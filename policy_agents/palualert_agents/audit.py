"""Tamper-evident audit log.

One JSON line per event: what was released to whom, what each agent
retrieved, every model call (prompt hash, model id, reasoning summary), every
claim admitted or rejected by the evidence gate, messages between agents,
conflicts, gaps and human decisions. Each record carries the SHA-256 of the
previous one, so editing or deleting a line breaks the chain:

    python -m palualert_agents.audit outputs/<run>/audit.jsonl
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

GENESIS = "0" * 64


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                      default=str)


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class AuditLog:
    def __init__(self, path: Path, run_id: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.seq = 0
        self.prev = GENESIS
        self.path.write_text("", encoding="utf-8")

    def record(self, kind: str, actor: str, payload: dict, step: int | None = None) -> dict:
        self.seq += 1
        body = {
            "seq": self.seq,
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "run_id": self.run_id,
            "step": step,
            "kind": kind,
            "actor": actor,
            "payload": payload,
            "prev_hash": self.prev,
        }
        body["hash"] = sha256_text(_canonical(body))
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(_canonical(body) + "\n")
        self.prev = body["hash"]
        return body


def verify_chain(path: Path) -> tuple[bool, int, str]:
    """(intact, records checked, message)."""
    prev = GENESIS
    n = 0
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            rec = json.loads(line)
            claimed = rec.pop("hash")
            if rec["prev_hash"] != prev:
                return False, n, f"record {n}: prev_hash does not match record {n - 1}"
            if sha256_text(_canonical(rec)) != claimed:
                return False, n, f"record {n}: content was modified"
            prev = claimed
    return True, n, f"{n} records, chain intact"


if __name__ == "__main__":
    ok, n, msg = verify_chain(Path(sys.argv[1]))
    print(("OK   " if ok else "FAIL ") + msg)
    sys.exit(0 if ok else 1)
