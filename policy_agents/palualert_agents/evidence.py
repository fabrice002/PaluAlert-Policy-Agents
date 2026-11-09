"""The evidence gate: no claim without a verbatim source.

Every claim an agent makes about law, policy or the system's own validity must
carry a quote and the id of the knowledge-base chunk it comes from. The gate
accepts a claim only if the quote, after whitespace/quote/dash normalisation,
is a literal substring of that chunk. This is deterministic code, not a model:
an LLM can propose a claim, only the gate can admit it.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field

from palualert_agents.kb.retriever import Hit, TfidfRetriever, expand_query, split_sentences

MIN_QUOTE_CHARS = 25
MAX_QUOTE_CHARS = 700

_TRANS = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"',
                        "«": '"', "»": '"', "–": "-", "\u2014": "-",
                        " ": " ", " ": " "})


def normalise(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).translate(_TRANS).lower()
    return re.sub(r"\s+", " ", s).strip()


@dataclass
class Claim:
    text: str                 # what the agent asserts
    quote: str                # verbatim span supporting it
    chunk_id: str             # where the span is
    citation: str = ""        # human-readable reference, filled by the gate
    verified: bool = False
    reason: str = ""          # why the gate accepted or rejected it
    source_scope: str = ""
    score: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GateResult:
    accepted: list[Claim] = field(default_factory=list)
    rejected: list[Claim] = field(default_factory=list)


def verify(claims: list[Claim], kb: TfidfRetriever,
           seen_chunk_ids: set[str] | None = None) -> GateResult:
    """Admit only claims whose quote is verbatim in the cited chunk.

    seen_chunk_ids: chunks actually shown to the agent; citing anything else is
    rejected, so an agent cannot cite a document it never retrieved."""
    out = GateResult()
    for c in claims:
        chunk = kb.get(c.chunk_id)
        q = normalise(c.quote or "")
        if chunk is None:
            c.reason = "unknown chunk id"
        elif seen_chunk_ids is not None and c.chunk_id not in seen_chunk_ids:
            c.reason = "chunk was not in the agent's retrieved evidence"
        elif len(q) < MIN_QUOTE_CHARS:
            c.reason = f"quote shorter than {MIN_QUOTE_CHARS} characters"
        elif len(q) > MAX_QUOTE_CHARS:
            c.reason = f"quote longer than {MAX_QUOTE_CHARS} characters"
        elif q not in normalise(chunk["text"]):
            c.reason = "quote is not verbatim in the cited chunk"
        else:
            c.verified = True
            c.reason = "verbatim match"
            c.citation = Hit(chunk, 0).citation()
            c.source_scope = chunk["scope"]
        (out.accepted if c.verified else out.rejected).append(c)
    return out


_STOP = {"dans", "pour", "avec", "sont", "être", "cette", "leur", "leurs", "which", "that",
          "with", "from", "this", "their", "shall", "should", "have", "into", "under", "after",
          "before", "toute", "tout", "tous", "elle", "elles", "mais", "plus", "also", "such"}


def _terms(text: str) -> set[str]:
    words = re.findall(r"[a-zà-ÿ]{4,}", normalise(expand_query(text)))
    return {w[:7] for w in words if w not in _STOP}   # crude stem shared by FR/EN plurals


def quote_overlap(quote: str, question: str) -> float:
    """Share of the question's terms that the quote contains (0..1)."""
    q = _terms(question)
    return len(q & _terms(quote)) / len(q) if q else 0.0


def best_quote(hit: Hit, question: str, max_chars: int = 420) -> str:
    """The sentence of a chunk that best answers a question (extractive mode):
    most question terms first, then the shorter of equally good sentences."""
    q = _terms(question)
    best, best_key = "", (-1, 0)
    for s in split_sentences(hit.chunk["text"]):
        if len(s) < 80:
            continue
        key = (len(q & _terms(s)), -len(s))
        if key > best_key:
            best, best_key = s, key
    if not best:
        best = hit.chunk["text"][:max_chars]
    if len(best) > max_chars:                # cut at a word boundary, still verbatim
        best = best[:max_chars].rsplit(" ", 1)[0]
    return best


def best_evidence(hits: list[Hit], question: str) -> tuple[Hit | None, str, float]:
    """Among several hits, the (hit, quote, overlap) whose best sentence covers the
    question best; retrieval score breaks ties."""
    best = (None, "", -1.0, -1.0)
    for h in hits:
        q = best_quote(h, question)
        ov = quote_overlap(q, question)
        if (ov, h.score) > (best[2], best[3]):
            best = (h, q, ov, h.score)
    return best[0], best[1], max(best[2], 0.0)
