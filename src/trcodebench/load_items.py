from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CURATED_DIR = ROOT / "datasets" / "curated"


def item_path(item_id: str) -> Path:
    return CURATED_DIR / f"{item_id}.json"


def load_item(item_id: str) -> dict[str, Any]:
    path = item_path(item_id)
    if not path.exists():
        raise FileNotFoundError(f"Unknown item id {item_id!r}: {path}")
    with path.open("r", encoding="utf-8") as handle:
        item = json.load(handle)
    if item.get("id") != item_id:
        raise ValueError(f"Item id mismatch in {path}: expected {item_id!r}, found {item.get('id')!r}")
    return item


def list_item_ids() -> list[str]:
    return sorted(path.stem for path in CURATED_DIR.glob("trcb-proto-*.json"))


def resolve_repo_path(relative_path: str) -> Path:
    return (ROOT / relative_path).resolve()
