"""Settings for the PaluAlert policy-agent layer.

Every value can be overridden with an environment variable prefixed `AI4G_`,
so the same code runs offline on a laptop, against a local Ollama, or on the
ITU AI for Good sandbox without edits.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # .../policy_agents
PACKAGE = ROOT.parent                                   # repository root
APP_DIR = PACKAGE / "palualert_app"


def _env(name: str, default: str) -> str:
    return os.environ.get(f"AI4G_{name}", default)


@dataclass(frozen=True)
class Settings:
    # Paths
    kb_dir: Path = ROOT / "kb"
    manifest: Path = ROOT / "kb" / "manifest.csv"
    lock_file: Path = ROOT / "kb" / "manifest.lock.json"
    raw_dir: Path = ROOT / "kb" / "raw"
    chunks_file: Path = ROOT / "kb" / "processed" / "chunks.jsonl"
    index_file: Path = ROOT / "kb" / "processed" / "tfidf_index.pkl"
    scenarios_dir: Path = ROOT / "scenarios"
    outputs_dir: Path = Path(_env("OUTPUTS_DIR", str(ROOT / "outputs")))

    # Tesseract language data for scanned PDFs (fra + eng). Empty disables OCR.
    tessdata: str = _env("TESSDATA", os.environ.get("TESSDATA_PREFIX", "")
                         or ("D:/ECOLE/ENSPY/Projet/tessdata"
                             if Path("D:/ECOLE/ENSPY/Projet/tessdata").exists() else ""))

    # Chunking: words per chunk, words of overlap (same unit as the ITU toolkit)
    chunk_words: int = int(_env("CHUNK_WORDS", "180"))
    chunk_overlap: int = int(_env("CHUNK_OVERLAP", "30"))

    # Retrieval
    top_k: int = int(_env("TOP_K", "6"))
    min_score: float = float(_env("MIN_SCORE", "0.06"))
    # Below this best score, a concept counts as "not found" in a scope.
    absence_score: float = float(_env("ABSENCE_SCORE", "0.10"))

    # LLM backend: extractive (offline, deterministic) | ollama | openai | anthropic
    llm_backend: str = _env("LLM_BACKEND", "extractive")
    llm_model: str = _env("LLM_MODEL", "")
    ollama_url: str = _env("OLLAMA_URL", "http://localhost:11434")
    openai_base_url: str = _env("OPENAI_BASE_URL", "")
    llm_temperature: float = float(_env("LLM_TEMPERATURE", "0"))

    # Domain application (palualert_app). Empty => run it in-process.
    mews_api_url: str = _env("MEWS_API_URL", "")

    default_models: dict = field(default_factory=lambda: {
        "ollama": "qwen2.5:14b",          # same default as the ITU AI-RE toolkit
        "openai": "gpt-4o-mini",
        "anthropic": "claude-opus-5-5",
    })

    def model_name(self) -> str:
        return self.llm_model or self.default_models.get(self.llm_backend, "")


settings = Settings()
