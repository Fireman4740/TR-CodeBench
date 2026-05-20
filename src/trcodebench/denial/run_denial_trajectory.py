from __future__ import annotations

from pathlib import Path
from typing import Any

from ..evaluate import evaluate_candidate
from .build_denial_prompt import build_denial_prompt
from .denial_schema import DenialConstraint, DenialStepResult, DenialTrajectory
from .denial_scoring import compute_denial_metrics
from .select_next_constraint import select_next_constraint
from .verify_denial import verify_denial


def run_denial_trajectory(
    item: dict[str, Any],
    candidate_paths: list[str | Path],
    hidden_cases: int | None = None,
    pbt_cases: int = 25,
    timeout_seconds: float = 1.0,
) -> dict[str, Any]:
    item_id = item["id"]
    trajectory = DenialTrajectory(item_id=item_id)
    used_ids: list[str] = []

    for step_idx, cand_path in enumerate(candidate_paths):
        cand_path = Path(cand_path)
        if not cand_path.exists():
            trajectory.steps.append(DenialStepResult(
                step=step_idx,
                constraint=None if step_idx == 0 else trajectory.steps[-1].constraint if trajectory.steps else None,
                passed=False,
                constraint_satisfied=False,
                failure_reason="candidate file not found",
                candidate_path=str(cand_path),
            ))
            continue

        constraint: DenialConstraint | None = None
        if step_idx > 0:
            constraint = select_next_constraint(item, used_ids)
            if constraint is None:
                break
            used_ids.append(constraint.id)

        result = evaluate_candidate(
            item_id=item_id,
            candidate_path=cand_path,
            hidden_cases=hidden_cases,
            pbt_cases=pbt_cases,
            timeout_seconds=timeout_seconds,
        )

        passed = result["score"]["correctness_score"] == 1.0
        constraint_satisfied = True
        failure_reason = None

        if constraint is not None:
            source = cand_path.read_text(encoding="utf-8")
            constraint_satisfied, violation_msg = verify_denial(source, constraint)
            if not constraint_satisfied:
                failure_reason = violation_msg

        if not passed and failure_reason is None:
            failure_reason = "correctness failure"

        candidate_paradigms = result.get("pd_classification", {}).get("candidate_paradigms", [])
        paradigm = candidate_paradigms[0] if candidate_paradigms else None
        pd_score = result["score"].get("pd_score", 0.0)

        trajectory.steps.append(DenialStepResult(
            step=step_idx,
            constraint=constraint,
            passed=passed,
            constraint_satisfied=constraint_satisfied,
            paradigm=paradigm,
            pd_score=pd_score,
            failure_reason=failure_reason,
            candidate_path=str(cand_path),
        ))

    traj_dict = trajectory.to_dict()
    traj_dict["denial_metrics"] = compute_denial_metrics(traj_dict)
    return traj_dict


def build_prompts_for_item(
    item: dict[str, Any],
    max_steps: int = 3,
    previous_sources: list[str] | None = None,
) -> list[dict[str, Any]]:
    prompts: list[dict[str, Any]] = []
    used_ids: list[str] = []

    for step in range(max_steps):
        if step == 0:
            continue

        constraint = select_next_constraint(item, used_ids)
        if constraint is None:
            break
        used_ids.append(constraint.id)

        prev_code = previous_sources[step - 1] if previous_sources and step - 1 < len(previous_sources) else None
        prompt = build_denial_prompt(item, constraint, previous_code=prev_code)
        prompts.append({
            "step": step,
            "constraint": constraint.to_dict(),
            "prompt": prompt,
        })

    return prompts
