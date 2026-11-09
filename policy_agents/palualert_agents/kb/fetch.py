"""Fetch and pin every knowledge-base source.

    python -m palualert_agents.kb.fetch            download what is missing
    python -m palualert_agents.kb.fetch --verify   re-hash local files against the lock

Each source is downloaded from its issuing body (or the stated mirror) into
kb/raw/<doc_id>.<ext>, and its SHA-256, size and fetch time are written to
kb/manifest.lock.json. The manifest stays human-curated; the lock is generated.
Project-evidence rows (local_path set) are hashed in place, never copied.

Some publishers block automated downloads. Save the file by hand as
kb/raw/<doc_id>.pdf and re-run: it is pinned with "obtained": "manual".
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from palualert_agents.settings import ROOT, settings

UA = "Mozilla/5.0 (PaluAlert-KB-fetch; ITU AI for Good hackathon research)"


def load_manifest(path: Path = settings.manifest) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_lock() -> dict:
    if settings.lock_file.exists():
        return json.loads(settings.lock_file.read_text(encoding="utf-8"))
    return {}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _kind(content: bytes, content_type: str) -> str | None:
    """Return 'pdf' or 'txt' for content we can parse, else None."""
    if content[:5] == b"%PDF-":
        return "pdf"
    ct = content_type.lower()
    if "text/plain" in ct or "markdown" in ct:
        return "txt"
    return None


def local_file(row: dict) -> Path | None:
    """Where a row's content lives on disk, if it has been obtained."""
    if row.get("local_path"):
        return (ROOT / row["local_path"]).resolve()
    for ext in ("pdf", "txt"):
        p = settings.raw_dir / f"{row['doc_id']}.{ext}"
        if p.exists():
            return p
    return None


def fetch_row(row: dict, timeout: int = 120) -> dict:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if row.get("local_path"):
        p = local_file(row)
        if not p or not p.exists():
            return {"status": "missing_local", "fetched_at": now}
        return {"status": "ok", "file": str(p.relative_to(ROOT.parent)).replace("\\", "/"),
                "sha256": sha256_file(p), "bytes": p.stat().st_size, "fetched_at": now}

    try:
        r = requests.get(row["url"], headers={"User-Agent": UA}, timeout=timeout,
                         allow_redirects=True)
    except requests.RequestException as e:
        return {"status": "error", "detail": f"{type(e).__name__}: {e}"[:300], "fetched_at": now}
    if r.status_code != 200:
        return {"status": "error", "detail": f"HTTP {r.status_code}", "fetched_at": now}
    kind = _kind(r.content, r.headers.get("content-type", ""))
    if kind is None:
        return {"status": "error", "fetched_at": now,
                "detail": f"not a PDF/text document ({r.headers.get('content-type')})"}

    settings.raw_dir.mkdir(parents=True, exist_ok=True)
    out = settings.raw_dir / f"{row['doc_id']}.{kind}"
    out.write_bytes(r.content)
    return {"status": "ok", "file": f"kb/raw/{out.name}", "sha256": sha256_file(out),
            "bytes": len(r.content), "final_url": r.url, "fetched_at": now}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verify", action="store_true", help="re-hash files against the lock")
    ap.add_argument("--force", action="store_true", help="re-download everything")
    ap.add_argument("--only", nargs="*", help="doc_ids to fetch")
    args = ap.parse_args(argv)

    rows = load_manifest()
    lock = load_lock()

    if args.verify:
        bad = 0
        for row in rows:
            entry = lock.get(row["doc_id"], {})
            p = local_file(row)
            if entry.get("status") != "ok" or not p:
                print(f"  --   {row['doc_id']:<24} not fetched")
                continue
            same = sha256_file(p) == entry["sha256"]
            bad += not same
            print(f"  {'ok' if same else 'DIFF':<4} {row['doc_id']}")
        return 1 if bad else 0

    for row in rows:
        did = row["doc_id"]
        if args.only and did not in args.only:
            continue
        p = local_file(row)
        if not args.force and lock.get(did, {}).get("status") == "ok" and p \
                and not row.get("local_path"):
            print(f"  skip {did:<24} already pinned")
            continue
        if p and not row.get("local_path") and not args.force:
            # Placed by hand (site blocks automated download): pin what is there.
            entry = {"status": "ok", "file": f"kb/raw/{p.name}", "sha256": sha256_file(p),
                     "bytes": p.stat().st_size, "obtained": "manual",
                     "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        else:
            entry = fetch_row(row)
        lock[did] = entry
        size = f"{entry.get('bytes', 0) / 1e6:6.2f} MB" if entry["status"] == "ok" else ""
        print(f"  {entry['status']:<5} {did:<24} {size} {entry.get('detail', '')}")
        settings.lock_file.write_text(json.dumps(lock, indent=2, ensure_ascii=False),
                                      encoding="utf-8")

    n_ok = sum(1 for r in rows if lock.get(r["doc_id"], {}).get("status") == "ok")
    print(f"\n{n_ok}/{len(rows)} sources pinned -> {settings.lock_file.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
