from __future__ import annotations

from typing import Any

from .denial_schema import DenialConstraint


def build_denial_prompt(
    item: dict[str, Any],
    constraint: DenialConstraint,
    previous_code: str | None = None,
) -> str:
    task = item["task"]
    statement = task["statement"]
    signature = task["signature"]
    allowed = task.get("allowed_imports", [])
    forbidden_imports = task.get("forbidden_imports", [])
    opt = task.get("optimization_constraints", {})
    time_complexity = opt.get("time_complexity", "")

    forbidden_str = ", ".join(f"`{f}`" for f in constraint.forbidden)

    parts: list[str] = []

    parts.append(f"## Task\n\n{statement}\n")
    parts.append(f"### Signature\n\n```python\n{signature}\n```\n")

    if time_complexity:
        parts.append(f"### Complexity requirement\n\nYour solution must run in {time_complexity} time.\n")

    if allowed:
        parts.append(f"### Allowed imports\n\n{', '.join(f'`{m}`' for m in allowed)}\n")

    if forbidden_imports:
        parts.append(f"### Forbidden imports\n\n{', '.join(f'`{m}`' for m in forbidden_imports)}\n")

    parts.append(f"### Denial constraint\n\n**{constraint.reason}**\n")
    parts.append(f"You MUST NOT use any of the following: {forbidden_str}.\n")

    if constraint.constraint_type == "forbidden_api":
        parts.append("Do not call, reference, or import any of these APIs.\n")
    elif constraint.constraint_type == "forbidden_import":
        parts.append("Do not import these modules or use any function from them.\n")
    elif constraint.constraint_type == "forbidden_structure":
        parts.append("Do not use these structural patterns in your solution.\n")
    elif constraint.constraint_type == "forbidden_paradigm":
        parts.append(
            "Do not implement the listed algorithmic approach. "
            "Find a fundamentally different strategy.\n"
        )
    elif constraint.constraint_type == "resource":
        parts.append("Your solution must satisfy the listed resource constraints.\n")

    if constraint.expected_alternatives:
        alts = ", ".join(constraint.expected_alternatives)
        parts.append(f"\n*Hint: Consider approaches such as {alts}.*\n")

    if previous_code:
        parts.append(
            "\n### Previous solution (for reference only — do NOT reuse its approach)\n\n"
            f"```python\n{previous_code}\n```\n"
        )

    parts.append(
        "\n### Output format\n\n"
        "Return ONLY a Python function matching the signature above. "
        "No explanation, no tests, no markdown fences.\n"
    )

    return "\n".join(parts)
