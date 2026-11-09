"""Command line.

    python -m palualert_agents fetch                  pin the knowledge-base sources
    python -m palualert_agents ingest                 parse, chunk, index
    python -m palualert_agents ask "question" [--scope national]
    python -m palualert_agents run S1_sensor_siting [--backend ollama] [--interactive]
    python -m palualert_agents run-all                every scenario in scenarios/
    python -m palualert_agents verify outputs/<run>/audit.jsonl
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _utf8_console() -> None:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass


def cmd_ask(args) -> int:
    from palualert_agents.evidence import best_quote
    from palualert_agents.kb.retriever import get_retriever
    kb = get_retriever()
    hits = kb.search(args.question, k=args.k, scopes=args.scope or None)
    for i, h in enumerate(hits, 1):
        print(f"[{i}] {h.score:.3f}  {h.citation()}\n     “{best_quote(h, args.question)}”\n")
    if not hits:
        print("No passage above the score floor.")
    return 0


def _run(name: str, args) -> dict:
    from palualert_agents.llm import get_backend
    from palualert_agents.simulation import Simulation, load_scenario
    sim = Simulation(load_scenario(name), llm=get_backend(args.backend),
                     human_mode="interactive" if args.interactive else "scripted")
    res = sim.run()
    ev = res["evaluation"]
    print(f"\n{res['scenario']['title']}")
    print(f"  output       {sim.out}")
    print(f"  actions      recall {ev['action_recall']}  missed {ev['expected_actions_missed']}")
    print(f"  gaps         {len(res['gaps'])} raised, recall {ev['gap_recall']}  "
          f"missed {ev['expected_gaps_missed']}")
    print(f"  evidence     {ev['claims_admitted']} claims admitted, {ev['claims_rejected']} rejected")
    print(f"  coordination {ev['conflicts']} conflict(s), {ev['human_decisions']} human decision(s)")
    from palualert_agents.audit import verify_chain
    ok, n, msg = verify_chain(sim.out / "audit.jsonl")
    print(f"  audit        {msg}")
    return res


def main(argv=None) -> int:
    _utf8_console()
    ap = argparse.ArgumentParser(prog="palualert_agents", description="PaluAlert policy agents")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch")
    sub.add_parser("ingest")
    a = sub.add_parser("ask")
    a.add_argument("question")
    a.add_argument("--scope", nargs="*")
    a.add_argument("-k", type=int, default=5)
    for name in ("run", "run-all"):
        r = sub.add_parser(name)
        if name == "run":
            r.add_argument("scenario")
        r.add_argument("--backend", default=None,
                       help="extractive | ollama | openai | anthropic (default: AI4G_LLM_BACKEND)")
        r.add_argument("--interactive", action="store_true",
                       help="take the human decisions at the terminal")
    v = sub.add_parser("verify")
    v.add_argument("audit_file")
    args = ap.parse_args(argv)

    if args.cmd == "fetch":
        from palualert_agents.kb.fetch import main as m
        return m([])
    if args.cmd == "ingest":
        from palualert_agents.kb.ingest import main as m
        return m()
    if args.cmd == "ask":
        return cmd_ask(args)
    if args.cmd == "run":
        _run(args.scenario, args)
        return 0
    if args.cmd == "run-all":
        from palualert_agents.settings import settings
        for p in sorted(settings.scenarios_dir.glob("*.yaml")):
            _run(str(p), args)
        return 0
    if args.cmd == "verify":
        from palualert_agents.audit import verify_chain
        ok, n, msg = verify_chain(Path(args.audit_file))
        print(("OK   " if ok else "FAIL ") + msg)
        return 0 if ok else 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
