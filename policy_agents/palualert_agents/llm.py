"""Pluggable language-model backends.

    AI4G_LLM_BACKEND=extractive   default. No model: agents quote the best
                                  matching sentences and apply their rule
                                  tables. Offline, deterministic, reproducible.
    AI4G_LLM_BACKEND=ollama       local model (the ITU AI-RE toolkit default,
                                  qwen2.5:14b) at AI4G_OLLAMA_URL
    AI4G_LLM_BACKEND=openai       any OpenAI-compatible endpoint, e.g. the
                                  ITU sandbox or vLLM: AI4G_OPENAI_BASE_URL
    AI4G_LLM_BACKEND=anthropic    Claude via the Anthropic SDK

Whatever the backend, the model only *proposes*: its claims go through the
verbatim evidence gate and its actions are restricted to the agent's catalog.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

from palualert_agents.audit import sha256_text
from palualert_agents.settings import settings


@dataclass
class LLMResult:
    text: str
    data: dict | None
    model: str
    reasoning_summary: str = ""
    meta: dict = field(default_factory=dict)


def parse_json(text: str) -> dict | None:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


class LLMBackend:
    name = "base"

    def __init__(self, model: str = ""):
        self.model = model

    @property
    def enabled(self) -> bool:
        return True

    def generate(self, system: str, user: str) -> LLMResult:
        raise NotImplementedError

    def describe(self) -> dict:
        return {"backend": self.name, "model": self.model}


class ExtractiveBackend(LLMBackend):
    name = "extractive"

    @property
    def enabled(self) -> bool:
        return False

    def generate(self, system: str, user: str) -> LLMResult:   # pragma: no cover
        raise RuntimeError("the extractive backend does not call a model")


class OllamaBackend(LLMBackend):
    name = "ollama"

    def generate(self, system: str, user: str) -> LLMResult:
        import httpx
        r = httpx.post(f"{settings.ollama_url}/api/chat", timeout=600, json={
            "model": self.model, "stream": False, "format": "json",
            "options": {"temperature": settings.llm_temperature},
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
        })
        r.raise_for_status()
        text = r.json()["message"]["content"]
        return LLMResult(text, parse_json(text), self.model)


class OpenAICompatibleBackend(LLMBackend):
    name = "openai"

    def generate(self, system: str, user: str) -> LLMResult:
        from openai import OpenAI
        client = OpenAI(base_url=settings.openai_base_url or None,
                        api_key=os.environ.get("OPENAI_API_KEY", "not-needed"))
        resp = client.chat.completions.create(
            model=self.model, temperature=settings.llm_temperature,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}])
        text = resp.choices[0].message.content or ""
        return LLMResult(text, parse_json(text), self.model)


class AnthropicBackend(LLMBackend):
    """Claude. Server-side refusal fallback is enabled ("default" routing), and
    the summarised reasoning is kept for the audit log."""
    name = "anthropic"

    def generate(self, system: str, user: str) -> LLMResult:
        import anthropic
        client = anthropic.Anthropic()
        resp = client.beta.messages.create(
            model=self.model,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            thinking={"type": "adaptive", "display": "summarized"},
            output_config={"effort": "medium"},
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if resp.stop_reason == "refusal":
            detail = getattr(resp, "stop_details", None)
            return LLMResult("", None, resp.model,
                             meta={"refusal": str(getattr(detail, "category", None))})
        text = "".join(b.text for b in resp.content if b.type == "text")
        reasoning = "\n".join(b.thinking for b in resp.content
                              if b.type == "thinking" and b.thinking)
        return LLMResult(text, parse_json(text), resp.model, reasoning,
                         meta={"request_id": resp._request_id,
                               "input_tokens": resp.usage.input_tokens,
                               "output_tokens": resp.usage.output_tokens})


_BACKENDS = {b.name: b for b in (ExtractiveBackend, OllamaBackend,
                                 OpenAICompatibleBackend, AnthropicBackend)}


def get_backend(name: str | None = None) -> LLMBackend:
    name = name or settings.llm_backend
    if name not in _BACKENDS:
        raise ValueError(f"unknown LLM backend {name!r}; choose from {sorted(_BACKENDS)}")
    model = settings.llm_model or settings.default_models.get(name, "")
    return _BACKENDS[name](model)


def prompt_fingerprint(system: str, user: str) -> str:
    return sha256_text(system + "\n\x1e\n" + user)
