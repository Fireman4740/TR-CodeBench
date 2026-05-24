from __future__ import annotations

from typing import Any

from .denial_schema import DenialConstraint


def compute_denial_metrics(trajectory_dict: dict[str, Any]) -> dict[str, Any]:
    steps = trajectory_dict.get("trajectory", [])
    denial_steps = [s for s in steps if s.get("constraint") is not None]

    trajectory_depth = len(steps)
    denial_pass_count = sum(
        1 for s in denial_steps
        if s.get("passed") and s.get("constraint_satisfied")
    )
    denial_pass_rate = denial_pass_count / len(denial_steps) if denial_steps else 0.0

    constraint_satisfied_count = sum(1 for s in denial_steps if s.get("constraint_satisfied"))
    constraint_satisfaction_rate = (
        constraint_satisfied_count / len(denial_steps) if denial_steps else 0.0
    )

    paradigms: list[str] = []
    for s in steps:
        p = s.get("paradigm")
        if p and s.get("passed") and p not in paradigms:
            paradigms.append(p)

    valid_strategy_switches = 0
    prev_paradigm = None
    for s in steps:
        if s.get("passed") and s.get("paradigm"):
            if prev_paradigm and s["paradigm"] != prev_paradigm:
                valid_strategy_switches += 1
            prev_paradigm = s["paradigm"]

    pd_confirmed = (
        len(paradigms) >= 2
        and any(
            s.get("passed") and s.get("constraint_satisfied") and s.get("pd_score", 0) > 0
            for s in denial_steps
        )
    )

    return {
        "trajectory_depth": trajectory_depth,
        "denial_pass_rate": round(denial_pass_rate, 6),
        "constraint_satisfaction_rate": round(constraint_satisfaction_rate, 6),
        "unique_valid_paradigms": paradigms,
        "valid_strategy_switches": valid_strategy_switches,
        "pd_confirmed": pd_confirmed,
    }
