"""Load the knowledge base into ChromaDB, in the layout of the ITU AI-RE toolkit.

    python -m palualert_agents.kb.to_chroma --dry-run          validate and write records only
    python -m palualert_agents.kb.to_chroma --persist DIR      embed and load (needs chromadb + Ollama)

The ITU toolkit (CrashingGuru/ITUAIReadiness, simulation/server/knowledge)
stores chunks in a persistent ChromaDB collection `kb_main`, cosine space,
embedded with Ollama `nomic-embed-text`. This script writes the same
collection from kb/processed/chunks.jsonl, so the knowledge base built here can
be hosted in the AI for Good Lab sandbox next to the toolkit's own corpus.
ChromaDB metadata must be scalar, so list fields are joined with ';'.

The --dry-run path is tested; the embedding path needs chromadb and a running
Ollama, which the sandbox provides.
"""
from __future__ import annotations

import argparse
import json
import sys

from palualert_agents.kb.retriever import iter_chunks
from palualert_agents.settings import settings

META_KEYS = ("doc_id", "title", "issuer", "jurisdiction", "scope", "doc_type", "language",
             "year", "url", "sha256", "page_start", "page_end", "heading", "ocr")


def to_record(c: dict) -> dict:
    meta = {k: c[k] for k in META_KEYS if c.get(k) is not None}
    meta["domains"] = ";".join(c["domains"])
    meta["articles"] = ";".join(c["articles"])
    meta["source_type"] = {"law": "policy_document", "treaty": "policy_document",
                           "strategy": "national_strategy", "standard": "standards_document",
                           "project_evidence": "use_case"}.get(c["doc_type"],
                                                               "international_org_report")
    meta["country"] = c["jurisdiction"]
    return {"id": c["chunk_id"], "document": c["text"], "metadata": meta}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--persist", default="")
    ap.add_argument("--collection", default="kb_main")
    ap.add_argument("--embed-model", default="nomic-embed-text")
    args = ap.parse_args(argv)

    records = [to_record(c) for c in iter_chunks()]
    for r in records:
        assert all(isinstance(v, (str, int, float, bool)) for v in r["metadata"].values()), r["id"]
    out = settings.chunks_file.parent / "chroma_records.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(records)} records validated -> {out.name}")
    if args.dry_run:
        return 0

    import chromadb
    import httpx
    client = chromadb.PersistentClient(path=args.persist or str(settings.kb_dir / "chromadb"))
    col = client.get_or_create_collection(args.collection, metadata={"hnsw:space": "cosine"})
    for i in range(0, len(records), 64):
        batch = records[i:i + 64]
        emb = httpx.post(f"{settings.ollama_url}/api/embed", timeout=600,
                         json={"model": args.embed_model,
                               "input": [r["document"] for r in batch]}).json()["embeddings"]
        col.upsert(ids=[r["id"] for r in batch], documents=[r["document"] for r in batch],
                   metadatas=[r["metadata"] for r in batch], embeddings=emb)
        print(f"  {i + len(batch)}/{len(records)}", end="\r")
    print(f"\nloaded into collection '{args.collection}' ({col.count()} items)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
