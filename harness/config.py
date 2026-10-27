"""Configuration loading (JSON; deliberately simple and dependency-free)."""
from __future__ import annotations

import json
from pathlib import Path

DEFAULTS = {
    "app_path": "examples/lovable-app",
    "requirements": "examples/requirements.md",
    "rules": "examples/business-rules.md",
    "contracts": "examples/target-contracts.openapi.json",
    "output_dir": "outputs",
    "llm": {
        "enabled": False,
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "model": "gpt-4o-mini",
        "timeout": 60,
    },
}


def _resolve(base: Path, value: str) -> str:
    p = Path(value)
    return str(p if p.is_absolute() else (base / p).resolve())


def load_config(path: str | None, overrides: dict | None = None) -> dict:
    if path:
        cfg_path = Path(path).resolve()
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        base = cfg_path.parent
    else:
        cfg = dict(DEFAULTS)
        base = Path.cwd()

    for key in ("app_path", "requirements", "rules", "contracts", "output_dir"):
        cfg.setdefault(key, DEFAULTS[key])
        if key in cfg:
            cfg[key] = _resolve(base, str(cfg[key]))
    cfg.setdefault("llm", DEFAULTS["llm"])

    for key, value in (overrides or {}).items():
        if value:
            cfg[key] = str(Path(value).resolve())
    return cfg
