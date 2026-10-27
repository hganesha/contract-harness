"""Optional LLM adapter.

The harness is fully functional with the ``NullProvider``. When configured, an
OpenAI-compatible Chat Completions endpoint is used to enrich narrative
sections — this works with OpenAI, OpenRouter, Groq, a local Ollama server
(``http://localhost:11434/v1``), vLLM, LM Studio, etc. Only the stdlib is used
(``urllib``); no SDK is required.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


class NullProvider:
    enabled = False

    def complete(self, system: str, user: str) -> str:  # noqa: D401
        return ""


@dataclass
class OpenAICompatProvider:
    base_url: str
    api_key: str
    model: str
    timeout: int = 60
    enabled: bool = True

    def complete(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        req = urllib.request.Request(
            url=self.base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
        except (urllib.error.URLError, KeyError, TimeoutError, json.JSONDecodeError) as exc:
            # Fail open: deterministic content still gets produced.
            print(f"[harness] LLM call failed, falling back to deterministic output: {exc}")
            return ""


def build_provider(config: dict) -> NullProvider | OpenAICompatProvider:
    llm_cfg = (config or {}).get("llm", {})
    if not llm_cfg.get("enabled", False):
        return NullProvider()
    api_key = os.environ.get(llm_cfg.get("api_key_env", "OPENAI_API_KEY"), "")
    if not api_key:
        print("[harness] LLM enabled but no API key found in environment; using deterministic mode.")
        return NullProvider()
    return OpenAICompatProvider(
        base_url=llm_cfg.get("base_url", "https://api.openai.com/v1"),
        api_key=api_key,
        model=llm_cfg.get("model", "gpt-4o-mini"),
        timeout=int(llm_cfg.get("timeout", 60)),
    )
