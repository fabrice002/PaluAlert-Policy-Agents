"""Institutional agent.

An agent has a mandate, a jurisdictional view of the knowledge base, a rule
table and a private inbox. It knows only the events released to it, which is
how the simulation reproduces information that is incomplete, unevenly
distributed and received at different times.

Each step the agent:
  1. reads the events newly released to it, plus tool results;
  2. matches its rule table against the signals those events carry;
  3. retrieves evidence for every question the matched rules raise, restricted
     to its own scopes and domains;
  4. turns evidence into claims (best-matching sentence, or the LLM's proposal)
     and submits them to the verbatim evidence gate;
  5. proposes actions from the shared catalog, each with its rationale and the
     admitted claims behind it; high-impact actions are marked for a human;
  6. sends questions to other agents when its rules require consultation.

Every step of that reasoning is written to the trace and the audit log.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from palualert_agents.audit import AuditLog
from palualert_agents.catalog import ACTIONS
from palualert_agents.evidence import Claim, best_quote, normalise, quote_overlap, verify
from palualert_agents.kb.retriever import TfidfRetriever
from palualert_agents.llm import LLMBackend, prompt_fingerprint


@dataclass(frozen=True)
class Rule:
    signal: str
    actions: tuple[str, ...] = ()
    questions: tuple[str, ...] = ()
    rationale: str = ""
    requests: tuple[tuple[str, str], ...] = ()      # (agent id, question)
    probes: tuple[str, ...] = ()


@dataclass
class Event:
    id: str
    step: int
    type: str
    text: str
    signals: list[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)
    tool: dict | None = None
    source: str = "scenario"


@dataclass
class ProposedAction:
    code: str
    label: str
    owner: str | None
    high_impact: bool
    rationale: str
    claim_ids: list[int]
    proposed_by: str
    step: int


@dataclass
class Assessment:
    agent: str
    step: int
    known_events: list[str]
    new_events: list[str]
    signals: list[str]
    summary: str
    tool_results: list[dict]
    evidence: list[dict]
    claims: list[dict]
    rejected_claims: list[dict]
    actions: list[ProposedAction]
    requests: list[dict]
    probes: list[str]
    trace: list[str]
    llm: dict | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


class Agent:
    id = "agent"
    name = "Agent"
    institution = ""
    mandate = ""
    kb_filters: dict = {}
    rules: tuple[Rule, ...] = ()

    def __init__(self, kb: TfidfRetriever, llm: LLMBackend, audit: AuditLog):
        self.kb = kb
        self.llm = llm
        self.audit = audit
        self.inbox: list[Event] = []
        self.history: list[Assessment] = []
        self._quoted: set[str] = set()

    # ── information flow ──────────────────────────────────────────────────────
    def receive(self, event: Event) -> None:
        self.inbox.append(event)

    def known(self, up_to_step: int) -> list[Event]:
        return [e for e in self.inbox if e.step <= up_to_step]

    # ── tools (overridden by agents that have them) ───────────────────────────
    def run_tools(self, events: list[Event], step: int) -> list[dict]:
        return []

    # ── evidence ──────────────────────────────────────────────────────────────
    def retrieve(self, question: str, k: int = 2) -> list:
        return self.kb.search(question, k=k, **self.kb_filters)

    def claims_for(self, question: str, hits: list, min_overlap: float = 0.2) -> list[Claim]:
        """One claim per hit, keeping only quotes that share terms with the question."""
        out, seen_quotes = [], set()
        for h in hits:
            q = best_quote(h, question)
            key = normalise(q)
            if key in seen_quotes or key in self._quoted:
                continue                      # overlapping chunks repeat sentences
            seen_quotes.add(key)
            if quote_overlap(q, question) >= min_overlap:
                out.append(Claim(text=f"[{self.id}] on: {question}", quote=q,
                                 chunk_id=h.chunk_id, score=round(h.score, 4)))
        return out

    # ── one simulation step ───────────────────────────────────────────────────
    def assess(self, step: int) -> Assessment:
        new = [e for e in self.inbox if e.step == step]
        trace = [f"Known events up to step {step}: "
                 + (", ".join(e.id for e in self.known(step)) or "none")]
        if new:
            trace.append("New this step: " + "; ".join(f"{e.id} ({e.type})" for e in new))

        tool_results = self.run_tools(new, step)
        signals = sorted({s for e in new for s in e.signals}
                         | {s for t in tool_results for s in t.get("derived_signals", [])})
        trace.append("Signals: " + (", ".join(signals) or "none"))

        matched = [r for r in self.rules if r.signal in signals]
        for r in matched:
            trace.append(f"Rule '{r.signal}' matched -> actions {list(r.actions) or '-'}"
                         + (f", consult {[t for t, _ in r.requests]}" if r.requests else ""))

        self._quoted: set[str] = set()
        # Evidence per question; remember which claims back which rule.
        questions, seen, claims, rule_claims = [], set(), [], {}
        evidence = []
        for r in matched:
            for q in r.questions:
                hits = self.retrieve(q)
                trace.append(f"Retrieved {len(hits)} chunk(s) for: {q[:90]}")
                evidence += [{"question": q, "chunk_id": h.chunk_id, "citation": h.citation(),
                              "score": round(h.score, 4)} for h in hits]
                seen |= {h.chunk_id for h in hits}
                start = len(claims)
                new_claims = self.claims_for(q, hits)
                self._quoted |= {normalise(c.quote) for c in new_claims}
                claims += new_claims
                rule_claims.setdefault(r.signal, []).extend(range(start, len(claims)))
                questions.append(q)

        llm_meta = None
        proposed_codes = [(r, a) for r in matched for a in r.actions]
        if self.llm.enabled and matched:
            llm_meta, claims, proposed_codes = self._llm_refine(
                step, new, tool_results, evidence, claims, proposed_codes, seen)

        gate = verify(claims, self.kb, seen_chunk_ids=seen)
        admitted = [c.to_dict() for c in claims if c.verified]
        rejected = [c.to_dict() for c in claims if not c.verified]
        index_of = {i: n for n, i in enumerate(i for i, c in enumerate(claims) if c.verified)}
        trace.append(f"Evidence gate: {len(gate.accepted)} claim(s) admitted, "
                     f"{len(gate.rejected)} rejected")
        for c in gate.rejected:
            self.audit.record("claim_rejected", self.id, c.to_dict(), step)

        actions, done = [], set()
        for r, code in proposed_codes:
            if code in done or code not in ACTIONS:
                if code not in ACTIONS:
                    trace.append(f"Dropped action {code!r}: not in the catalog")
                continue
            done.add(code)
            a = ACTIONS[code]
            refs = [index_of[i] for i in rule_claims.get(r.signal if r else "", []) if i in index_of]
            actions.append(ProposedAction(code, a.label, a.owner, a.high_impact,
                                          (r.rationale if r else "") or a.label, refs,
                                          self.id, step))
        if any(a.high_impact for a in actions):
            trace.append("High-impact actions routed to human decision: "
                         + ", ".join(a.code for a in actions if a.high_impact))

        requests = [{"from": self.id, "to": t, "question": q, "step": step}
                    for r in matched for t, q in r.requests]
        probes = sorted({p for r in matched for p in r.probes})

        summary = self.summarise(new, signals, actions, tool_results)
        a = Assessment(self.id, step, [e.id for e in self.known(step)], [e.id for e in new],
                       signals, summary, tool_results, evidence, admitted, rejected, actions,
                       requests, probes, trace, llm_meta)
        self.history.append(a)
        self.audit.record("assessment", self.id, {
            "summary": summary, "signals": signals, "new_events": a.new_events,
            "actions": [asdict(x) for x in actions], "claims": admitted,
            "requests": requests, "probes": probes, "trace": trace,
            "tool_results": tool_results}, step)
        return a

    def summarise(self, new, signals, actions, tool_results) -> str:
        if not new:
            return f"{self.name}: no new information this step."
        acts = ", ".join(a.code for a in actions) or "no action"
        return f"{self.name}: {len(new)} new event(s); signals {', '.join(signals) or 'none'}; proposes {acts}."

    # ── answering another agent ───────────────────────────────────────────────
    def answer(self, question: str, asked_by: str, step: int) -> dict:
        """Reply with the agent's current position (what it has concluded from the
        events it holds) followed by the provisions within its mandate."""
        hits = self.kb.search(question, k=4, min_score=0.03, **self.kb_filters)
        claims = []
        for h in hits:
            q = best_quote(h, question)
            if quote_overlap(q, question) >= 0.3:
                claims.append(Claim(text=f"[{self.id}] answer to {asked_by}: {question}",
                                    quote=q, chunk_id=h.chunk_id, score=round(h.score, 4)))
        gate = verify(claims[:2], self.kb, seen_chunk_ids={h.chunk_id for h in hits})

        position = ""
        mine = [a for a in self.history if a.step <= step and a.actions]
        if mine:
            last = mine[-1]
            rationales = list(dict.fromkeys(x.rationale for x in last.actions))
            position = (f"Current position (step {last.step}): "
                        + ", ".join(x.code for x in last.actions) + ". "
                        + " ".join(rationales) + " ")
        if gate.accepted:
            body = position + " ".join(f"Under {c.citation}: “{c.quote}”"
                                       for c in gate.accepted)
        else:
            body = position + ("No provision on this point was found in the documents within "
                               "my mandate; I flag it as a possible gap.")
        reply = {"from": self.id, "to": asked_by, "question": question, "answer": body,
                 "claims": [c.to_dict() for c in gate.accepted], "step": step,
                 "found": bool(gate.accepted), "position": position}
        self.audit.record("message", self.id, reply, step)
        return reply

    # ── optional model refinement ─────────────────────────────────────────────
    def _llm_refine(self, step, new, tool_results, evidence, claims, proposed, seen):
        allowed = {c: ACTIONS[c].label for c in ACTIONS}
        ev_text = "\n\n".join(
            f"[{cid}] {self.kb.get(cid)['title']}: {self.kb.get(cid)['text'][:1500]}"
            for cid in sorted(seen))
        system = (
            f"You are the {self.name}, acting for: {self.institution}.\nMandate: {self.mandate}\n"
            "You assess an unfolding malaria early-warning incident. Use ONLY the evidence "
            "passages given. Every claim must quote a passage verbatim (copy the exact words) "
            "and give its chunk id; claims that are not verbatim are discarded by an automatic "
            "gate. Recommend actions only from the allowed list. Answer with one JSON object.")
        user = json.dumps({
            "step": step,
            "events_you_received": [{"id": e.id, "type": e.type, "text": e.text,
                                     "data": e.data} for e in new],
            "tool_results": tool_results,
            "draft_actions": [a for _, a in proposed],
            "allowed_actions": allowed,
            "output_format": {
                "assessment": "2-4 sentences",
                "claims": [{"text": "what you assert", "quote": "verbatim span",
                            "chunk_id": "id from evidence"}],
                "actions": [{"code": "ALLOWED_CODE", "rationale": "why, citing claims"}],
                "rationale_steps": ["short reasoning steps"]},
        }, ensure_ascii=False) + "\n\nEVIDENCE\n" + ev_text

        meta = {"backend": self.llm.name, "model": self.llm.model,
                "prompt_sha256": prompt_fingerprint(system, user)}
        try:
            res = self.llm.generate(system, user)
        except Exception as e:
            meta["error"] = f"{type(e).__name__}: {e}"[:300]
            self.audit.record("llm_call", self.id, meta, step)
            return meta, claims, proposed
        meta.update({"model": res.model, "reasoning_summary": res.reasoning_summary[:4000],
                     **res.meta})
        data = res.data or {}
        if not data:
            meta["error"] = "no JSON in model output; kept the rule-based draft"
            self.audit.record("llm_call", self.id, meta, step)
            return meta, claims, proposed

        llm_claims = [Claim(text=str(c.get("text", ""))[:500], quote=str(c.get("quote", "")),
                            chunk_id=str(c.get("chunk_id", "")))
                      for c in data.get("claims", []) if isinstance(c, dict)]
        llm_actions = [a.get("code") for a in data.get("actions", []) if isinstance(a, dict)]
        meta.update({"assessment": data.get("assessment", ""),
                     "rationale_steps": data.get("rationale_steps", []),
                     "proposed_actions": llm_actions,
                     "dropped_actions": [c for c in llm_actions if c not in ACTIONS]})
        self.audit.record("llm_call", self.id, meta, step)
        # The model may add claims and actions; the rule-based draft is kept as the floor.
        merged = proposed + [(None, c) for c in llm_actions
                             if c in ACTIONS and c not in {a for _, a in proposed}]
        return meta, claims + llm_claims, merged
