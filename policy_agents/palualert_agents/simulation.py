"""Scenario engine and coordination protocol.

A scenario is a sequence of steps. Each step releases a chunk of events to
named recipients only; nobody sees the whole picture at once. Within a step the
coordinator runs a fixed three-phase protocol:

  A. independent assessment   every agent assesses what *it* knows, in isolation
  B. consultation             questions raised in A are delivered to the agent
                              whose mandate covers them, which answers from its
                              own documents (or reports that it cannot)
  C. coordination             the coordinator pools the proposals, detects
                              conflicting recommendations, actions with no
                              mandated owner and owners not engaged, and routes
                              every high-impact action to a human decision

At the end, every gap probe raised during the run is analysed against the
knowledge base (gaps.py). Everything is written to a hash-chained audit log.
"""
from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

from palualert_agents.agents.base import Event
from palualert_agents.agents.roster import ROSTER
from palualert_agents.audit import AuditLog
from palualert_agents.catalog import ACTIONS, INSTITUTIONS, conflicts_between
from palualert_agents.gaps import PROBES, analyse
from palualert_agents.kb.retriever import get_retriever
from palualert_agents.llm import LLMBackend, get_backend
from palualert_agents.settings import settings

# Actions nobody is mandated for point at the gap that explains why.
UNOWNED_TO_PROBE = {"APPROVE_MODEL_UPDATE": "G-MODEL-CHANGE",
                    "CERTIFY_SENSOR_SITING": "G-SENSOR-STANDARD"}


def load_scenario(path: Path | str) -> dict:
    path = Path(path)
    if not path.exists():
        path = settings.scenarios_dir / f"{path.name}.yaml"
    with open(path, encoding="utf-8") as f:
        sc = yaml.safe_load(f)
    sc["_file"] = str(path)
    return sc


class Simulation:
    def __init__(self, scenario: dict, llm: LLMBackend | None = None,
                 human_mode: str = "scripted", out_dir: Path | None = None,
                 mews_client=None):
        self.sc = scenario
        self.kb = get_retriever()
        self.llm = llm or get_backend()
        self.human_mode = human_mode
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.run_id = f"{scenario['id']}_{stamp}"
        self.out = Path(out_dir or settings.outputs_dir / self.run_id)
        self.out.mkdir(parents=True, exist_ok=True)
        self.audit = AuditLog(self.out / "audit.jsonl", self.run_id)

        ids = scenario.get("agents", list(ROSTER))
        self.agents = {}
        for aid in ids:
            kw = {"client": mews_client} if aid == "surveillance" and mews_client else {}
            self.agents[aid] = ROSTER[aid](self.kb, self.llm, self.audit, **kw)

        self.steps: list[dict] = []
        self.probe_triggers: dict[str, list[dict]] = {}
        self.decisions: list[dict] = []

    # ── protocol ──────────────────────────────────────────────────────────────
    def run(self) -> dict:
        self.audit.record("run_start", "coordinator", {
            "scenario": self.sc["id"], "title": self.sc["title"],
            "agents": {a: INSTITUTIONS.get(a, a) for a in self.agents},
            "llm": self.llm.describe(), "kb_chunks": len(self.kb.chunks),
            "kb_documents": len({c["doc_id"] for c in self.kb.chunks}),
            "human_mode": self.human_mode})

        for st in self.sc["steps"]:
            self.steps.append(self._run_step(st))

        gaps = []
        for pid, triggers in self.probe_triggers.items():
            g = analyse(PROBES[pid], self.kb, triggers)
            gaps.append(g)
            self.audit.record("gap", "advisor", g.to_dict())
        order = {"absent": 0, "weak": 1, "addressed": 2}
        gaps.sort(key=lambda g: (order[g.status], g.category, g.probe_id))

        result = {
            "run_id": self.run_id, "scenario": {k: v for k, v in self.sc.items()
                                                if not k.startswith("_")},
            "llm": self.llm.describe(), "mews": getattr(
                self.agents.get("surveillance"), "client", None) and
            self.agents["surveillance"].client.mode,
            "steps": self.steps, "decisions": self.decisions,
            "gaps": [g.to_dict() for g in gaps],
            "evaluation": self._evaluate(gaps),
        }
        self.audit.record("run_end", "coordinator", {"evaluation": result["evaluation"],
                                                    "n_gaps": len(gaps)})
        self._write(result)
        return result

    def _run_step(self, st: dict) -> dict:
        n = st["step"]
        self.audit.record("step_start", "coordinator", {"title": st.get("title", "")}, n)

        # Release: each event goes to its recipients only.
        released = []
        for item in st.get("release", []):
            to = list(self.agents) if item["to"] == "all" else item["to"]
            ev = item["event"]
            event = Event(id=ev["id"], step=n, type=ev.get("type", "info"), text=ev["text"],
                          signals=ev.get("signals", []), data=ev.get("data", {}),
                          tool=ev.get("tool"))
            for aid in to:
                if aid in self.agents:
                    self.agents[aid].receive(event)
            released.append({"event": event.id, "to": to, "type": event.type,
                             "text": event.text, "signals": event.signals})
            self.audit.record("event_release", "scenario", {
                "event": asdict(event), "recipients": to,
                "withheld_from": [a for a in self.agents if a not in to]}, n)

        # A. independent assessment
        assessments = {aid: ag.assess(n) for aid, ag in self.agents.items()}

        # B. consultation
        messages = []
        for a in assessments.values():
            for req in a.requests:
                self.audit.record("request", req["from"], req, n)
                target = self.agents.get(req["to"])
                if target is None:
                    reply = {"from": req["to"], "to": req["from"], "question": req["question"],
                             "answer": "Institution not represented in this exercise.",
                             "found": False, "claims": [], "step": n}
                else:
                    reply = target.answer(req["question"], req["from"], n)
                messages.append({"request": req, "reply": reply})
                if not reply["found"]:
                    self._trigger("G-ALERT-AUTHORITY" if req["to"] == "ministry"
                                  else "G-DATA-SHARING", req["to"], n,
                                  f"unanswered consultation from {req['from']}")

        for a in assessments.values():
            for pid in a.probes:
                self._trigger(pid, a.agent, n, ",".join(a.signals))

        # C. coordination
        coordination = self._coordinate(n, assessments, st.get("human", {}))
        return {"step": n, "title": st.get("title", ""), "released": released,
                "assessments": {k: v.to_dict() for k, v in assessments.items()},
                "messages": messages, "coordination": coordination}

    def _trigger(self, probe: str, agent: str, step: int, why: str) -> None:
        if probe in PROBES:
            self.probe_triggers.setdefault(probe, []).append(
                {"agent": agent, "step": step, "why": why})

    def _coordinate(self, n: int, assessments: dict, human_script: dict) -> dict:
        proposals: dict[str, list[str]] = {}
        for a in assessments.values():
            for act in a.actions:
                proposals.setdefault(act.code, []).append(a.agent)

        conflicts = []
        for x, y, what in conflicts_between(set(proposals)):
            conflicts.append({"between": [x, y], "issue": what,
                              "proposed_by": {x: proposals[x], y: proposals[y]}})

        ownership = []
        for code, by in proposals.items():
            owner = ACTIONS[code].owner
            if owner is None:
                ownership.append({"action": code, "issue": "no institution is mandated",
                                  "proposed_by": by})
                if code in UNOWNED_TO_PROBE:
                    self._trigger(UNOWNED_TO_PROBE[code], "coordinator", n, f"unowned {code}")
            elif owner not in by:
                state = ("owner agent did not propose it" if owner in self.agents
                         else "owner institution not represented")
                ownership.append({"action": code, "issue": state, "owner": owner,
                                  "proposed_by": by})

        decisions = []
        for code in sorted(c for c in proposals if ACTIONS[c].high_impact):
            d = self._decide(code, n, proposals[code], human_script.get(code))
            decisions.append(d)

        for c in conflicts:
            sides = {d["action"]: d["decision"] for d in decisions}
            approved = [s for s in c["between"] if sides.get(s) == "approve"]
            rejected = [s for s in c["between"] if sides.get(s) == "reject"]
            if len(approved) == 1:
                c["resolution"] = f"resolved by human decision: {approved[0]} approved"
            elif len(rejected) == 1:
                c["resolution"] = f"resolved by human decision: {rejected[0]} rejected"
            else:
                c["resolution"] = "escalated: needs a joint decision"

        record = {"proposals": proposals, "conflicts": conflicts, "ownership": ownership,
                  "decisions": decisions}
        self.audit.record("coordination", "coordinator", record, n)
        return record

    def _decide(self, code: str, n: int, proposed_by: list[str], scripted: dict | None) -> dict:
        if self.human_mode == "interactive":
            print(f"\n[step {n}] {ACTIONS[code].label}  (proposed by {', '.join(proposed_by)})")
            ans = input("  approve / reject / defer [defer]: ").strip().lower() or "defer"
            decision, note = (ans if ans in {"approve", "reject", "defer"} else "defer"), \
                input("  note: ").strip()
            who = "human (interactive)"
        elif scripted:
            decision, note, who = scripted["decision"], scripted.get("note", ""), \
                scripted.get("by", "human (scripted exercise director)")
        else:
            decision, note, who = "defer", "no human decision recorded; action not executed", \
                "default"
        d = {"step": n, "action": code, "label": ACTIONS[code].label,
             "proposed_by": proposed_by, "decision": decision, "note": note, "by": who}
        self.decisions.append(d)
        self.audit.record("human_decision", who, d, n)
        return d

    # ── evaluation against the scenario's expectations ────────────────────────
    def _evaluate(self, gaps) -> dict:
        exp = self.sc.get("expected", {})
        proposed = {a["code"] for s in self.steps for ag in s["assessments"].values()
                    for a in ag["actions"]}
        found_gaps = {g.probe_id for g in gaps}
        n_claims = sum(len(ag["claims"]) for s in self.steps for ag in s["assessments"].values())
        n_rej = sum(len(ag["rejected_claims"]) for s in self.steps
                    for ag in s["assessments"].values())
        ev_actions = exp.get("actions", [])
        ev_gaps = exp.get("gaps", [])
        return {
            "expected_actions_found": sorted(set(ev_actions) & proposed),
            "expected_actions_missed": sorted(set(ev_actions) - proposed),
            "action_recall": round(len(set(ev_actions) & proposed) / len(ev_actions), 3)
            if ev_actions else None,
            "expected_gaps_found": sorted(set(ev_gaps) & found_gaps),
            "expected_gaps_missed": sorted(set(ev_gaps) - found_gaps),
            "gap_recall": round(len(set(ev_gaps) & found_gaps) / len(ev_gaps), 3)
            if ev_gaps else None,
            "conflicts": sum(len(s["coordination"]["conflicts"]) for s in self.steps),
            "claims_admitted": n_claims, "claims_rejected": n_rej,
            "human_decisions": len(self.decisions),
        }

    # ── outputs ───────────────────────────────────────────────────────────────
    def _write(self, result: dict) -> None:
        (self.out / "run.json").write_text(json.dumps(result, indent=2, ensure_ascii=False,
                                                      default=str), encoding="utf-8")
        with open(self.out / "gaps.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["probe_id", "category", "title", "status", "national_score",
                        "national_evidence", "practice_examples", "recommendation", "y3172",
                        "ai_readiness", "missing_sources"])
            for g in result["gaps"]:
                w.writerow([g["probe_id"], g["category_label"], g["title"], g["status"],
                            g["national_best_score"],
                            " | ".join(e["citation"] for e in g["national_evidence"]),
                            " | ".join(e["citation"] for e in g["practice_examples"]),
                            g["recommendation"], " ".join(g["y3172"]),
                            "; ".join(g["readiness"]), " ".join(g["missing_sources"])])
        from palualert_agents.report import write_reports
        write_reports(result, self.out)
