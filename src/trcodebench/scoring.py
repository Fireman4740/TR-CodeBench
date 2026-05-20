from __future__ import annotations

from typing import Any

SALIERI_MEMORISATION_THRESHOLD = 0.70
PARADIGM_COSMETIC_THRESHOLD = 0.20


def _harmonic_mean_3(a: float, b: float, c: float) -> float:
    if a <= 0.0 or b <= 0.0 or c <= 0.0:
        return 0.0
    return round(3.0 / (1.0 / a + 1.0 / b + 1.0 / c), 6)


def compute_score(metrics: dict[str, Any]) -> dict[str, Any]:
    pbt_gate_passed = bool(metrics.get("pbt_gate_passed", True))
    pbt_group_pass_rate = float(metrics.get("pbt_group_pass_rate", 1.0))
    robustness_score = round(0.7 * float(pbt_gate_passed) + 0.3 * pbt_group_pass_rate, 6)

    correctness_score = 1.0 if metrics["public_pass_rate"] == 1.0 and metrics["hidden_pass_rate"] == 1.0 else 0.0
    # Gate: PBT failure caps correctness contribution
    effective_correctness = min(correctness_score, 0.65) if not pbt_gate_passed else correctness_score

    complexity_ok = metrics.get("complexity_ratio_ok")
    if complexity_ok is None:
        optimization_score = 1.0 if correctness_score and not metrics.get("timeout", False) else 0.0
    else:
        optimization_score = 1.0 if correctness_score and complexity_ok else 0.0

    optimization_failed = metrics.get("complexity_ratio_ok") is False

    pd_score = 0.0
    if correctness_score and not optimization_failed:
        salieri = float(metrics.get("salieri_overlap", 1.0))
        p_dist = float(metrics.get("paradigm_distance", 0.0))
        prod_score = float(metrics.get("productivity_score", 0.0))

        if salieri <= SALIERI_MEMORISATION_THRESHOLD and p_dist >= PARADIGM_COSMETIC_THRESHOLD:
            originality = 1.0 - salieri
            pd_score = _harmonic_mean_3(p_dist, prod_score, originality)

    hallucination_flag = bool(
        metrics.get("static_violation", False)
        or metrics.get("crash", False)
        or metrics["hidden_pass_rate"] < 1.0
    )

    raw_score = (
        0.50 * effective_correctness
        + 0.20 * robustness_score
        + 0.15 * optimization_score
        + 0.15 * pd_score
        - 0.25 * float(hallucination_flag)
    )

    final = max(0.0, min(1.0, round(raw_score, 6)))
    if optimization_failed:
        final = min(final, 0.60)

    return {
        "score": final,
        "correctness_score": correctness_score,
        "optimization_score": optimization_score,
        "pd_score": pd_score,
        "hallucination_flag": hallucination_flag,
        "pbt_gate_passed": pbt_gate_passed,
        "robustness_score": robustness_score,
    }
