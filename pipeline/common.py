"""Shared helpers for the WC 2026 pipeline."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "site" / "public" / "data"
IMG_DIR = ROOT / "site" / "public" / "img"
CACHE_DIR = ROOT / "pipeline" / "cache"
SEED_DIR = ROOT / "pipeline" / "data"

for d in (DATA_DIR, IMG_DIR, CACHE_DIR, SEED_DIR):
    d.mkdir(parents=True, exist_ok=True)

KNOCKOUT_STAGES = (
    "LAST_32",
    "LAST_16",
    "QUARTER_FINALS",
    "SEMI_FINALS",
    "THIRD_PLACE",
    "FINAL",
)

STAGE_LABEL = {
    "LAST_32": "Round of 32",
    "LAST_16": "Round of 16",
    "QUARTER_FINALS": "Quarter-finals",
    "SEMI_FINALS": "Semi-finals",
    "THIRD_PLACE": "Third place",
    "FINAL": "Final",
}

PINNED_DEFAULT_ID = 764  # Brazil (football-data.org team id)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def require_token() -> str:
    tok = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
    if not tok:
        raise SystemExit(
            "FOOTBALL_DATA_TOKEN not set. Export it locally or add it as an Actions secret."
        )
    return tok
