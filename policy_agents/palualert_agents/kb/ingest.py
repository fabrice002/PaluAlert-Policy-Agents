"""Parse, chunk and index the pinned sources.

    python -m palualert_agents.kb.ingest

Reads every pinned source (kb/manifest.lock.json), extracts text page by page
with PyMuPDF so each chunk keeps its page number, splits it into overlapping
word windows (the chunking unit of the ITU AI-RE toolkit), tags the legal
article numbers each chunk contains, and writes:

    kb/processed/chunks.jsonl      one JSON object per chunk: the exchange format,
                                   loadable into the ITU sandbox ChromaDB
    kb/processed/tfidf_index.pkl   the offline retrieval index
    kb/processed/ingest_report.json  per-document coverage
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

from palualert_agents.kb.fetch import load_lock, load_manifest, local_file
from palualert_agents.settings import settings

# "Article 12", "Art. 12", "ARTICLE 12" (French law) and "Section 12" (English law).
ARTICLE_RE = re.compile(
    r"\b(?:Art(?:icle)?\.?|ARTICLE|Section|SECTION)\s*(\d{1,3}(?:\s*(?:bis|ter))?)\b"
    r"(?=\s*(?:er\b|\(|:|\.|-|–|\u2014|\s+[A-ZÀ-Ý]))")
TESS_LANG = {"fr": "fra", "en": "eng"}
OCR_MIN_CHARS = 60          # a page with less text than this is treated as a scan


def clean(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("­", "")                       # soft hyphen
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)             # hyphenated line breaks
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def pages_of(path: Path, language: str = "en") -> tuple[list[tuple[int | None, str]], int]:
    """(page number, text) for a PDF; (None, section text) blocks for text files.

    Scanned pages are OCR'd with Tesseract when tessdata is available.
    Returns the pages and the number of pages that went through OCR."""
    if path.suffix.lower() == ".pdf":
        import fitz  # PyMuPDF
        from palualert_agents.kb.fetch import sha256_file
        cache = settings.chunks_file.parent / "ocr_cache" / f"{sha256_file(path)}.json"
        if cache.exists():                      # OCR is slow; reuse it for identical files
            d = json.loads(cache.read_text(encoding="utf-8"))
            return [tuple(p) for p in d["pages"]], d["n_ocr"]
        out, n_ocr = [], 0
        with fitz.open(path) as doc:
            for i, p in enumerate(doc):
                text = p.get_text()
                if len(text.strip()) < OCR_MIN_CHARS and settings.tessdata:
                    try:
                        tp = p.get_textpage_ocr(language=TESS_LANG.get(language, "eng"),
                                                dpi=250, full=True,
                                                tessdata=settings.tessdata)
                        text = p.get_text(textpage=tp)
                        n_ocr += 1
                    except Exception as e:      # OCR is best effort
                        print(f"     OCR failed on {path.name} p.{i + 1}: {e}")
                out.append((i + 1, clean(text)))
        if n_ocr:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps({"pages": out, "n_ocr": n_ocr}, ensure_ascii=False),
                             encoding="utf-8")
        return out, n_ocr
    text = clean(path.read_text(encoding="utf-8", errors="replace"))
    if path.suffix.lower() == ".md":
        # One block per heading so citations point to a section; flatten each
        # block to prose so quotes are readable sentences, not table syntax.
        blocks = re.split(r"\n(?=#{1,4} )", text)
        return [(None, markdown_to_prose(b)) for b in blocks if b.strip()], 0
    return [(None, text)], 0


BOX = re.compile(r"[─-╿▲-▼←-⇿]")


def markdown_to_prose(md: str) -> str:
    """Headings kept on the first line; tables become one sentence per row;
    code fences and box-drawing diagrams are dropped."""
    md = re.sub(r"```.*?```", " ", md, flags=re.S)
    out = []
    for line in md.splitlines():
        s = line.strip()
        if not s or BOX.search(s) or re.fullmatch(r"[|:\-\s]+", s) or s == "---":
            continue
        if s.startswith("#"):
            out.append(s)                       # heading line, read by chunk_pages
            continue
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|") if c.strip()]
            s = ", ".join(cells)
        s = re.sub(r"^(?:[>*\-+]|\d+\.)\s+", "", s)
        s = s.replace("**", "").replace("`", "").replace("> ", "")
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)        # links -> text
        if s and s[-1] not in ".;:!?":
            s += "."
        out.append(s)
    return "\n".join(out)


def chunk_pages(pages: list[tuple[int | None, str]], words_per_chunk: int,
                overlap: int) -> list[dict]:
    """Word-window chunks that never mix more than two consecutive pages."""
    tokens: list[tuple[str, int | None, str]] = []   # (word, page, heading)
    for page, text in pages:
        heading = ""
        if page is None:
            first = text.splitlines()[0] if text else ""
            heading = first.lstrip("# ").strip()[:120] if first.startswith("#") else ""
        tokens.extend((w, page, heading) for w in text.split())

    chunks, step = [], max(1, words_per_chunk - overlap)
    for start in range(0, len(tokens), step):
        window = tokens[start:start + words_per_chunk]
        if len(window) < 25 and chunks:
            break
        pages_in = sorted({p for _, p, _ in window if p is not None})
        text = " ".join(w for w, _, _ in window)
        chunks.append({
            "text": text,
            "page_start": pages_in[0] if pages_in else None,
            "page_end": pages_in[-1] if pages_in else None,
            "heading": window[0][2],
            "articles": sorted(set(m.strip() for m in ARTICLE_RE.findall(text)),
                               key=lambda a: int(re.match(r"\d+", a).group())),
        })
        if start + words_per_chunk >= len(tokens):
            break
    return chunks


def ingest() -> dict:
    rows = load_manifest()
    lock = load_lock()
    settings.chunks_file.parent.mkdir(parents=True, exist_ok=True)

    report, all_chunks = {}, []
    for row in rows:
        did = row["doc_id"]
        if lock.get(did, {}).get("status") != "ok":
            report[did] = {"status": "not_fetched"}
            continue
        path = local_file(row)
        print(f"  ...  {did}", flush=True)
        try:
            pages, n_ocr = pages_of(path, row["language"])
        except Exception as e:
            report[did] = {"status": "unreadable", "detail": f"{type(e).__name__}: {e}"[:200]}
            continue
        n_chars = sum(len(t) for _, t in pages)
        if not pages:
            report[did] = {"status": "unreadable", "detail": "PDF has no readable pages"}
            continue
        if n_chars < 500:
            report[did] = {"status": "no_text_layer", "pages": len(pages),
                           "detail": "scanned PDF; set AI4G_TESSDATA for OCR"}
            continue
        chunks = chunk_pages(pages, settings.chunk_words, settings.chunk_overlap)
        for i, c in enumerate(chunks):
            c.update({
                "chunk_id": f"{did}#c{i:04d}",
                "doc_id": did, "title": row["title"], "issuer": row["issuer"],
                "jurisdiction": row["jurisdiction"], "scope": row["scope"],
                "domains": row["domains"].split(";"), "doc_type": row["doc_type"],
                "language": row["language"], "year": int(row["year"]),
                "url": row["url"] or row["local_path"],
                "sha256": lock[did]["sha256"],
                "ocr": n_ocr > 0,
            })
        all_chunks.extend(chunks)
        report[did] = {"status": "ok", "pages": len(pages), "chars": n_chars,
                       "chunks": len(chunks), "ocr_pages": n_ocr,
                       "articles_tagged": sum(1 for c in chunks if c["articles"])}

    with open(settings.chunks_file, "w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    from palualert_agents.kb.retriever import TfidfRetriever
    TfidfRetriever.build(all_chunks).save(settings.index_file)

    (settings.chunks_file.parent / "ingest_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main() -> int:
    report = ingest()
    ok = {k: v for k, v in report.items() if v["status"] == "ok"}
    for did, r in report.items():
        if r["status"] == "ok":
            print(f"  ok   {did:<24} {r['pages']:>4} pages {r['chunks']:>5} chunks "
                  f"{r['articles_tagged']:>4} with articles"
                  + (f"  ({r['ocr_pages']} OCR)" if r["ocr_pages"] else ""))
        else:
            print(f"  --   {did:<24} {r['status']} {r.get('detail', '')}")
    print(f"\n{len(ok)} documents, {sum(r['chunks'] for r in ok.values())} chunks "
          f"-> {settings.chunks_file.relative_to(settings.kb_dir.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
