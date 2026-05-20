"""Metrics profile — independent evaluation axes for TR-CodeBench.

Each axis is computed independently and reported separately.
The composite score is retained for backward compatibility but marked deprecated.
"""

from __future__ import annotations

from typing import Any


SALIERI_MEMORISATION_THRESHOLD = 0.70
PARADIGM_COSMETIC_THRESHOLD = 0.20


def _harmonic_mean_2(a: float, b: float) -> float:
    if a <= 0.0 or b <= 0.0:
        return 0.0
    return round(2.0 / (1.0 / a + 1.0 / b), 6)


def compute_correctness(metrics: dict[str, Any]) -> float:
    """Axis 1 — Binary gate: all tests pass or not."""
    public_ok = metrics.get("public_pass_rate", 0.0) == 1.0
    hidden_ok = metrics.get("hidden_pass_rate", 0.0) == 1.0
    return 1.0 if (public_ok and hidden_ok) else 0.0


def compute_robustness(metrics: dict[str, Any]) -> float:
    """Axis 2 — PBT-based robustness score [0, 1]."""
    pbt_gate = float(metrics.get("pbt_gate_passed", True))
    pbt_rate = float(metrics.get("pbt_group_pass_rate", 1.0))
    return round(0.7 * pbt_gate + 0.3 * pbt_rate, 6)


def compute_efficiency(metrics: dict[str, Any]) -> float | None:
    """Axis 3 — Complexity regime compliance [0, 1] or None if not measurable.

    Returns None when correctness fails or measurement is indeterminate.
    Uses the continuous ratio value for granularity (not just the boolean).
    """
    correctness = compute_correctness(metrics)
    if correctness < 1.0:
        return None

    complexity_ratio_ok = metrics.get("complexity_ratio_ok")
    if complexity_ratio_ok is None:
        return None
    if complexity_ratio_ok is False:
        return 0.0

    # Use the raw ratio for a continuous score
    complexity_profile = metrics.get("complexity_profile")
    if complexity_profile is None:
        return 1.0

    ratio = complexity_profile.get("ratio")
    ratio_max = complexity_profile.get("expected_ratio_max", 30.0)
    if ratio is None or ratio_max <= 0:
        return 1.0

    # Linear scale: perfect (0 ratio) = 1.0, at ratio_max = 0.0
    score = max(0.0, min(1.0, 1.0 - ratio / ratio_max))
    return round(score, 6)


def compute_divergence(metrics: dict[str, Any]) -> float | None:
    """Axis 4 — Productive divergence from oracle [0, 1] or None.

    Returns None if correctness fails. Returns 0.0 if gates not passed.
    """
    correctness = compute_correctness(metrics)
    if correctness < 1.0:
        return None

    # Gate: optimization must not have failed
    if metrics.get("complexity_ratio_ok") is False:
        return 0.0

    salieri = float(metrics.get("salieri_overlap", 1.0))
    p_dist = float(metrics.get("paradigm_distance", 0.0))

    # Gates
    if salieri > SALIERI_MEMORISATION_THRESHOLD:
        return 0.0
    if p_dist < PARADIGM_COSMETIC_THRESHOLD:
        return 0.0

    originality = 1.0 - salieri
    base_score = _harmonic_mean_2(p_dist, originality)

    # Bonus for genuine divergence
    if metrics.get("is_genuine_divergence", False):
        base_score = min(1.0, round(base_score * 1.2, 6))

    return round(base_score, 6)


def compute_safety(metrics: dict[str, Any]) -> float:
    """Axis 5 — No hallucinations, crashes, or static violations (binary)."""
    has_violation = bool(
        metrics.get("static_violation", False)
        or metrics.get("crash", False)
        or metrics.get("hidden_pass_rate", 1.0) < 1.0
    )
    return 0.0 if has_violation else 1.0


def compute_metrics_profile(
    metrics: dict[str, Any],
    complexity_profile: dict[str, Any] | None = None,
    is_genuine_divergence: bool = False,
) -> dict[str, Any]:
    """Compute the 5-axis metrics profile.

    Parameters
    ----------
    metrics : dict
        Raw evaluation metrics (public_pass_rate, hidden_pass_rate, etc.)
    complexity_profile : dict or None
        Complexity profiling data (ratio, expected_ratio_max) for efficiency axis.
    is_genuine_divergence : bool
        Whether paradigm classifier confirmed genuine divergence.

    Returns
    -------
    dict with keys: correctness, robustness, efficiency, divergence, safety
    """
    # Enrich metrics with extra context for axis computations
    enriched = {**metrics}
    if complexity_profile is not None:
        enriched["complexity_profile"] = complexity_profile
    enriched["is_genuine_divergence"] = is_genuine_divergence

    correctness = compute_correctness(enriched)
    robustness = compute_robustness(enriched)
    efficiency = compute_efficiency(enriched)
    divergence = compute_divergence(enriched)
    safety = compute_safety(enriched)

    return {
        "correctness": correctness,
        "robustness": robustness,
        "efficiency": efficiency,
        "divergence": divergence,
        "safety": safety,
    }


def aggregate_profiles(
    profiles: list[dict[str, Any]],
) -> dict[str, float | None]:
    """Aggregate multiple profiles into mean per axis.

    None values are excluded from the mean (axis not applicable for that run).
    """
    axes = ["correctness", "robustness", "efficiency", "divergence", "safety"]
    result: dict[str, float | None] = {}
    for axis in axes:
        values = [p[axis] for p in profiles if p.get(axis) is not None]
        result[axis] = round(sum(values) / len(values), 4) if values else None
    return result
