"""Offline checks: no network, no model.

    python -m pytest tests -q        or        python tests/test_offline.py
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from palualert_agents.audit import AuditLog, verify_chain                    # noqa: E402
from palualert_agents.evidence import Claim, normalise, verify               # noqa: E402
from palualert_agents.kb.retriever import get_retriever                      # noqa: E402
from palualert_agents.mews_client import correct_siting_offset, dew_point    # noqa: E402


def test_gate_accepts_only_verbatim_quotes():
    kb = get_retriever()
    chunk = next(c for c in kb.chunks if c["doc_id"] == "CM-LAW-2024-017" and c["articles"])
    words = chunk["text"].split()
    good = " ".join(words[5:20])
    res = verify([Claim("ok", good, chunk["chunk_id"]),
                  Claim("paraphrase", good.replace(words[10], "XXXX"), chunk["chunk_id"]),
                  Claim("wrong chunk", good, "NOPE#c0000"),
                  Claim("too short", "loi", chunk["chunk_id"])], kb)
    assert [c.text for c in res.accepted] == ["ok"]
    assert {c.reason for c in res.rejected} == {"quote is not verbatim in the cited chunk",
                                                "unknown chunk id",
                                                "quote shorter than 25 characters"}


def test_gate_rejects_chunks_the_agent_never_saw():
    kb = get_retriever()
    c = kb.chunks[0]
    q = " ".join(c["text"].split()[:12])
    res = verify([Claim("x", q, c["chunk_id"])], kb, seen_chunk_ids=set())
    assert not res.accepted and "not in the agent's retrieved evidence" in res.rejected[0].reason


def test_audit_chain_detects_tampering():
    d = Path(tempfile.mkdtemp())
    log = AuditLog(d / "a.jsonl", "t")
    for i in range(5):
        log.record("x", "tester", {"i": i})
    assert verify_chain(d / "a.jsonl")[0]
    lines = (d / "a.jsonl").read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[2])
    rec["payload"]["i"] = 99
    lines[2] = json.dumps(rec)
    (d / "a.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok, n, msg = verify_chain(d / "a.jsonl")
    assert not ok and n == 3


def test_sensor_correction_keeps_moisture():
    t, rh = correct_siting_offset(30.73, 56.8, 7.27)
    assert abs(t - 23.46) < 1e-6
    assert abs(dew_point(t, rh) - dew_point(30.73, 56.8)) < 0.05
    assert abs(rh - 87.4) < 1.0            # the reanalysis value, recovered from moisture alone


def test_scenario_runs_end_to_end():
    from palualert_agents.llm import get_backend
    from palualert_agents.simulation import Simulation, load_scenario
    sim = Simulation(load_scenario("S1_sensor_siting"), llm=get_backend("extractive"),
                     out_dir=Path(tempfile.mkdtemp()) / "run")
    res = sim.run()
    kb = get_retriever()

    assert verify_chain(sim.out / "audit.jsonl")[0]
    assert res["evaluation"]["action_recall"] == 1.0
    # every admitted quote really is in its chunk
    for st in res["steps"]:
        for a in st["assessments"].values():
            for c in a["claims"]:
                assert normalise(c["quote"]) in normalise(kb.get(c["chunk_id"])["text"])
    # information asymmetry: at step 1 only the surveillance agent holds the IoT reading
    s1 = res["steps"][0]["assessments"]
    assert "E1.1" in s1["surveillance"]["known_events"]
    assert "E1.1" not in s1["telecom"]["known_events"]
    assert "E1.1" not in s1["ministry"]["known_events"]
    # the high-impact action went to a human
    assert any(d["action"] == "MAINTAIN_VECTOR_CONTROL" for d in res["decisions"])
    for f in ("run.json", "transcript.md", "report.html", "gaps.csv"):
        assert (sim.out / f).exists()


def test_chroma_records_are_scalar():
    from palualert_agents.kb.to_chroma import main
    assert main(["--dry-run"]) == 0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok  ", name)
