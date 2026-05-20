"""Annotate each curated item JSON with oracle_ast_features from the reference solution.

Run from the repo root:
    python scripts/annotate_oracle_features.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from trcodebench.ast_features import extract_features  # noqa: E402
from trcodebench.paradigm_classifier import detect_paradigms  # noqa: E402

DATASETS = ROOT / "datasets" / "curated"


def annotate_item(item_path: Path) -> None:
    item = json.loads(item_path.read_text(encoding="utf-8"))
    oracle_rel = item["oracle"]["reference_solution_path"]
    oracle_path = ROOT / oracle_rel
    source = oracle_path.read_text(encoding="utf-8")
    features = extract_features(source)
    known = item["oracle"].get("known_valid_paradigms", [])
    detected = detect_paradigms(features, known)
    item["oracle"]["oracle_ast_features"] = features
    item["oracle"]["oracle_detected_paradigms"] = detected
    item_path.write_text(json.dumps(item, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{item['id']}: features={features}, paradigms={detected}")


def main() -> None:
    for item_path in sorted(DATASETS.glob("trcb-proto-*.json")):
        annotate_item(item_path)


if __name__ == "__main__":
    main()
