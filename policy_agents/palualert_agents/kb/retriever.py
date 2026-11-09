"""Retrieval over the knowledge base.

The default retriever is TF-IDF (scikit-learn): it runs offline, is
deterministic and its scores are reproducible in an audit. The corpus is
bilingual: Cameroonian law and strategy are in French, global guidance in
English: so queries are expanded through a small EN<->FR policy glossary
before matching. On the ITU sandbox the same chunks.jsonl can be embedded into
ChromaDB instead (see to_chroma.py); the agents only depend on `search()`.
"""
from __future__ import annotations

import json
import pickle
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from palualert_agents.settings import settings

# Policy vocabulary that differs between the French national corpus and the
# English global one. Expansion is symmetric: either side adds the other.
GLOSSARY = {
    "personal data": "données à caractère personnel",
    "data protection": "protection des données",
    "health data": "données de santé",
    "sensitive data": "données sensibles",
    "consent": "consentement",
    "data controller": "responsable du traitement",
    "processing": "traitement",
    "cross-border transfer": "transfert vers un pays tiers",
    "transfer": "transfert",
    "supervisory authority": "autorité de protection",
    "authority": "autorité",
    "malaria": "paludisme",
    "surveillance": "surveillance épidémiologique",
    "epidemic": "épidémie",
    "outbreak": "flambée épidémique",
    "early warning": "alerte précoce",
    "alert": "alerte",
    "health district": "district de santé",
    "ministry of health": "ministère de la santé publique",
    "sensor": "capteur",
    "climate": "climat",
    "weather": "météorologie",
    "rainfall": "pluviométrie",
    "telecommunications": "communications électroniques",
    "radio frequency": "fréquences radioélectriques",
    "spectrum": "spectre des fréquences",
    "regulator": "régulation",
    "cybersecurity": "cybersécurité",
    "security incident": "incident de sécurité",
    "breach": "violation",
    "audit": "audit",
    "accountability": "responsabilité",
    "liability": "responsabilité",
    "automated decision": "décision automatisée",
    "profiling": "profilage",
    "artificial intelligence": "intelligence artificielle",
    "algorithm": "algorithme",
    "digital health": "santé numérique",
    "information system": "système d'information",
    "interoperability": "interopérabilité",
    "community health worker": "agent de santé communautaire",
    "funding": "financement",
    "coordination": "coordination",
    "governance": "gouvernance",
    "penalty": "sanction",
    "right of access": "droit d'accès",
    "data subject": "personne concernée",
    "retention": "conservation",
    "notification": "notification",
    "public health": "santé publique",
}
_PAIRS = [(en, fr) for en, fr in GLOSSARY.items()]


def expand_query(q: str) -> str:
    low = q.lower()
    extra = [fr for en, fr in _PAIRS if en in low] + [en for en, fr in _PAIRS if fr in low]
    return q + (" " + " ".join(extra) if extra else "")


@dataclass
class Hit:
    chunk: dict
    score: float

    @property
    def chunk_id(self) -> str:
        return self.chunk["chunk_id"]

    def citation(self) -> str:
        c = self.chunk
        where = []
        if c.get("articles"):
            where.append("art. " + ", ".join(c["articles"][:3]))
        if c.get("page_start"):
            where.append(f"p. {c['page_start']}" + (
                f"–{c['page_end']}" if c.get("page_end") != c["page_start"] else ""))
        if c.get("heading"):
            where.append(f"§ {c['heading']}")
        return f"{c['doc_id']} ({c['issuer']}, {c['year']})" + (
            ", " + ", ".join(where) if where else "")


class TfidfRetriever:
    def __init__(self, chunks: list[dict], vectorizer: TfidfVectorizer, matrix):
        self.chunks = chunks
        self.vectorizer = vectorizer
        self.matrix = matrix
        self._by_id = {c["chunk_id"]: c for c in chunks}

    @classmethod
    def build(cls, chunks: list[dict]) -> "TfidfRetriever":
        vec = TfidfVectorizer(strip_accents="unicode", lowercase=True, ngram_range=(1, 2),
                              sublinear_tf=True, min_df=1, max_df=0.6,
                              token_pattern=r"(?u)\b\w[\w'-]{1,}\b")
        matrix = vec.fit_transform([c["title"] + " " + c["text"] for c in chunks])
        return cls(chunks, vec, matrix)

    def save(self, path: Path) -> None:
        with open(path, "wb") as f:
            pickle.dump({"chunks": self.chunks, "vectorizer": self.vectorizer,
                         "matrix": self.matrix}, f)

    @classmethod
    def load(cls, path: Path = settings.index_file) -> "TfidfRetriever":
        if not path.exists():
            # A fresh clone ships chunks.jsonl but not the (regenerable) index.
            if settings.chunks_file.exists():
                r = cls.build(list(iter_chunks()))
                r.save(path)
                return r
            raise FileNotFoundError(
                f"{path} not found - run `python -m palualert_agents.kb.ingest` first")
        with open(path, "rb") as f:
            d = pickle.load(f)
        return cls(d["chunks"], d["vectorizer"], d["matrix"])

    def get(self, chunk_id: str) -> dict | None:
        return self._by_id.get(chunk_id)

    def search(self, query: str, k: int = settings.top_k, scopes: list[str] | None = None,
               domains: list[str] | None = None, jurisdictions: list[str] | None = None,
               doc_ids: list[str] | None = None, min_score: float = settings.min_score,
               max_per_doc: int = 2) -> list[Hit]:
        qv = self.vectorizer.transform([expand_query(query)])
        scores = (self.matrix @ qv.T).toarray().ravel()
        order = np.argsort(-scores)
        hits, per_doc = [], {}
        for i in order:
            s = float(scores[i])
            if s < min_score:
                break
            c = self.chunks[i]
            if scopes and c["scope"] not in scopes:
                continue
            if domains and not set(domains) & set(c["domains"]):
                continue
            if jurisdictions and c["jurisdiction"] not in jurisdictions:
                continue
            if doc_ids and c["doc_id"] not in doc_ids:
                continue
            if per_doc.get(c["doc_id"], 0) >= max_per_doc:
                continue
            per_doc[c["doc_id"]] = per_doc.get(c["doc_id"], 0) + 1
            hits.append(Hit(c, s))
            if len(hits) >= k:
                break
        return hits

    def coverage(self, query: str, **filters) -> tuple[float, Hit | None]:
        """Best score for a concept within a filtered scope: the basis of an
        'evidenced absence' finding. Low score = the corpus does not address it."""
        hits = self.search(query, k=1, min_score=0.0, **filters)
        return (hits[0].score, hits[0]) if hits else (0.0, None)


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.;:!?])\s+(?=[A-ZÀ-Ý0-9«\"(])", text)
    return [p.strip() for p in parts if 40 <= len(p.strip()) <= 600]


_retriever: TfidfRetriever | None = None


def get_retriever() -> TfidfRetriever:
    global _retriever
    if _retriever is None:
        _retriever = TfidfRetriever.load()
    return _retriever


def iter_chunks(path: Path = settings.chunks_file):
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)
