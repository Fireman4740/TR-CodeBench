#!/usr/bin/env python3
"""Aggregate TR-CodeBench metrics profiles from a JSONL run file.

Reads a JSONL file where each line is a full evaluation result (from evaluate_candidate),
extracts metrics_profile from each, and produces per-model and per-item aggregation tables.

Usage:
    python scripts/aggregate_metrics.py reports/openrouter_runs/results.jsonl
    python scripts/aggregate_metrics.py results.jsonl --format csv
    python scripts/aggregate_metrics.py results.jsonl --format markdown
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from io import StringIO
from pathlib import Path
from typing import Any

# Allow running as script from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from trcodebench.metrics_profile import aggregate_profiles, compute_metrics_profile


AXES = ["correctness", "robustness", "efficiency", "divergence", "safety"]


def load_results(path: Path) -> list[dict[str, Any]]:
    """Load evaluation results from a JSONL file."""
    results = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            results.append(json.loads(line))
    return results


def extract_profiles(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract or recompute metrics_profile from each result."""
    profiles = []
    for r in results:
        if "metrics_profile" in r:
            profile = r["metrics_profile"]
        elif "metrics" in r:
            # Backward compat: recompute from raw metrics
            profile = compute_metrics_profile(
                metrics=r["metrics"],
                complexity_profile=r.get("complexity_profile"),
                is_genuine_divergence=r.get("pd_classification", {}).get("is_genuine_divergence", False),
            )
        else:
            continue
        profile["_model"] = r.get("model", r.get("model_id", "unknown"))
        profile["_item"] = r.get("item_id", "unknown")
        profiles.append(profile)
    return profiles


def aggregate_by_group(
    profiles: list[dict[str, Any]], group_key: str
) -> dict[str, dict[str, float | None]]:
    """Group profiles by a key and compute mean per axis."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in profiles:
        groups[p.get(group_key, "unknown")].append(p)

    return {name: aggregate_profiles(group) for name, group in sorted(groups.items())}


def format_markdown(
    aggregated: dict[str, dict[str, float | None]], group_label: str
) -> str:
    """Format aggregation as a markdown table."""
    lines = []
    header = f"| {group_label} | " + " | ".join(f"{a.capitalize()} ↑" for a in AXES) + " |"
    separator = "|" + "|".join(["---"] * (len(AXES) + 1)) + "|"
    lines.append(header)
    lines.append(separator)

    for name, agg in aggregated.items():
        cells = []
        for axis in AXES:
            val = agg.get(axis)
            cells.append(f"{val:.4f}" if val is not None else "N/A")
        lines.append(f"| {name} | " + " | ".join(cells) + " |")

    return "\n".join(lines)


def format_csv(
    aggregated: dict[str, dict[str, float | None]], group_label: str
) -> str:
    """Format aggregation as CSV."""
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow([group_label] + [a.capitalize() for a in AXES])
    for name, agg in aggregated.items():
        row = [name]
        for axis in AXES:
            val = agg.get(axis)
            row.append(f"{val:.4f}" if val is not None else "")
        writer.writerow(row)
    return buf.getvalue()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate TR-CodeBench metrics profiles.")
    parser.add_argument("input", type=Path, help="Path to a JSONL results file.")
    parser.add_argument("--format", choices=["markdown", "csv"], default="markdown", help="Output format.")
    parser.add_argument("--by", choices=["model", "item"], default="model", help="Aggregation dimension.")
    parser.add_argument("--output", type=Path, default=None, help="Output file (default: stdout).")
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"Error: {args.input} not found.", file=sys.stderr)
        return 1

    results = load_results(args.input)
    profiles = extract_profiles(results)

    if not profiles:
        print("No profiles found in input.", file=sys.stderr)
        return 1

    group_key = "_model" if args.by == "model" else "_item"
    group_label = "Model" if args.by == "model" else "Item"
    aggregated = aggregate_by_group(profiles, group_key)

    if args.format == "markdown":
        output = format_markdown(aggregated, group_label)
    else:
        output = format_csv(aggregated, group_label)

    if args.output:
        args.output.write_text(output, encoding="utf-8")
        print(f"Written to {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
