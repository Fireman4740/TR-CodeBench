from __future__ import annotations

from typing import Any

from .denial_schema import DenialConstraint


def select_next_constraint(
    item: dict[str, Any],
    used_constraint_ids: list[str],
    previous_source: str | None = None,
) -> DenialConstraint | None:
    raw_constraints = item.get("denial_constraints", [])
    if not raw_constraints:
        return None

    constraints = [DenialConstraint.from_dict(c) for c in raw_constraints]

    for constraint in constraints:
        if constraint.id not in used_constraint_ids and constraint.is_feasible:
            return constraint

    return None
