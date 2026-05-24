from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DenialConstraint:
    id: str
    constraint_type: str          # "forbidden_api" | "forbidden_import" | "forbidden_structure" | "forbidden_paradigm" | "resource"
    forbidden: list[str]          # tokens / modules / patterns to ban
    reason: str
    expected_alternatives: list[str] = field(default_factory=list)
    is_feasible: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.constraint_type,
            "forbidden": self.forbidden,
            "reason": self.reason,
            "expected_alternatives": self.expected_alternatives,
            "is_feasible": self.is_feasible,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DenialConstraint:
        return cls(
            id=data["id"],
            constraint_type=data["type"],
            forbidden=data.get("forbidden", []),
            reason=data.get("reason", ""),
            expected_alternatives=data.get("expected_alternatives", []),
            is_feasible=data.get("is_feasible", True),
        )


@dataclass
class DenialStepResult:
    step: int
    constraint: DenialConstraint | None
    passed: bool
    constraint_satisfied: bool
    paradigm: str | None = None
    pd_score: float = 0.0
    failure_reason: str | None = None
    candidate_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "step": self.step,
            "constraint": self.constraint.to_dict() if self.constraint else None,
            "passed": self.passed,
            "constraint_satisfied": self.constraint_satisfied,
        }
        if self.paradigm is not None:
            d["paradigm"] = self.paradigm
        d["pd_score"] = self.pd_score
        if self.failure_reason:
            d["failure_reason"] = self.failure_reason
        if self.candidate_path:
            d["candidate_path"] = self.candidate_path
        return d


@dataclass
class DenialTrajectory:
    item_id: str
    steps: list[DenialStepResult] = field(default_factory=list)

    @property
    def trajectory_depth(self) -> int:
        return len(self.steps)

    @property
    def denial_pass_rate(self) -> float:
        denial_steps = [s for s in self.steps if s.constraint is not None]
        if not denial_steps:
            return 0.0
        passed = sum(1 for s in denial_steps if s.passed and s.constraint_satisfied)
        return passed / len(denial_steps)

    @property
    def unique_valid_paradigms(self) -> list[str]:
        seen: list[str] = []
        for s in self.steps:
            if s.passed and s.paradigm and s.paradigm not in seen:
                seen.append(s.paradigm)
        return seen

    @property
    def constraint_satisfaction_rate(self) -> float:
        denial_steps = [s for s in self.steps if s.constraint is not None]
        if not denial_steps:
            return 0.0
        satisfied = sum(1 for s in denial_steps if s.constraint_satisfied)
        return satisfied / len(denial_steps)

    @property
    def pd_confirmed(self) -> bool:
        if len(self.unique_valid_paradigms) < 2:
            return False
        return any(
            s.passed and s.constraint_satisfied and s.pd_score > 0
            for s in self.steps
            if s.constraint is not None
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "trajectory_depth": self.trajectory_depth,
            "denial_pass_rate": round(self.denial_pass_rate, 6),
            "unique_valid_paradigms": self.unique_valid_paradigms,
            "constraint_satisfaction_rate": round(self.constraint_satisfaction_rate, 6),
            "pd_confirmed": self.pd_confirmed,
            "trajectory": [s.to_dict() for s in self.steps],
        }
