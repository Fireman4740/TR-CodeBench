from __future__ import annotations

import pytest

from trcodebench.scoring import _harmonic_mean_3, compute_score


# ---------------------------------------------------------------------------
# _harmonic_mean_3
# ---------------------------------------------------------------------------

def test_harmonic_mean_3_equal_values():
    assert _harmonic_mean_3(1.0, 1.0, 1.0) == 1.0


def test_harmonic_mean_3_zero_input_returns_zero():
    assert _harmonic_mean_3(0.0, 0.5, 0.8) == 0.0
    assert _harmonic_mean_3(0.5, 0.0, 0.8) == 0.0
    assert _harmonic_mean_3(0.5, 0.8, 0.0) == 0.0


def test_harmonic_mean_3_known_value():
    # HM(2, 3, 6) = 3 / (1/2 + 1/3 + 1/6) = 3 / 1 = 3.0
    assert _harmonic_mean_3(2.0, 3.0, 6.0) == 3.0


# ---------------------------------------------------------------------------
# compute_score parametrized
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("metrics, expected_pd_score_ge, expected_score_range", [
    # Correct + paradigm different + productive + original
    (
        {
            "public_pass_rate": 1.0,
            "hidden_pass_rate": 1.0,
            "pbt_gate_passed": True,
            "pbt_group_pass_rate": 1.0,
            "static_violation": False,
            "crash": False,
            "timeout": False,
            "salieri_overlap": 0.05,
            "paradigm_distance": 0.8,
            "productivity_score": 0.7,
            "complexity_ratio_ok": True,
        },
        0.5,
        (0.85, 1.0),
    ),
    # Cosmetic variation (distance < threshold) → pd_score = 0
    (
        {
            "public_pass_rate": 1.0,
            "hidden_pass_rate": 1.0,
            "pbt_gate_passed": True,
            "pbt_group_pass_rate": 1.0,
            "static_violation": False,
            "crash": False,
            "timeout": False,
            "salieri_overlap": 0.05,
            "paradigm_distance": 0.1,
            "productivity_score": 0.9,
            "complexity_ratio_ok": True,
        },
        0.0,
        (0.85, 0.86),
    ),
    # Memorisation (salieri > 0.7) → pd_score = 0
    (
        {
            "public_pass_rate": 1.0,
            "hidden_pass_rate": 1.0,
            "pbt_gate_passed": True,
            "pbt_group_pass_rate": 1.0,
            "static_violation": False,
            "crash": False,
            "timeout": False,
            "salieri_overlap": 0.85,
            "paradigm_distance": 0.8,
            "productivity_score": 0.8,
            "complexity_ratio_ok": True,
        },
        0.0,
        (0.85, 0.86),
    ),
    # Complexity regression → productivity=0 → pd_score = 0, optimization_failed caps at 0.60
    (
        {
            "public_pass_rate": 1.0,
            "hidden_pass_rate": 1.0,
            "pbt_gate_passed": True,
            "pbt_group_pass_rate": 1.0,
            "static_violation": False,
            "crash": False,
            "timeout": False,
            "salieri_overlap": 0.05,
            "paradigm_distance": 0.8,
            "productivity_score": 0.0,
            "complexity_ratio_ok": False,
        },
        0.0,
        (0.55, 0.61),
    ),
    # Hallucination penalises (hidden < 1.0 → correctness=0 → pd blocked)
    (
        {
            "public_pass_rate": 1.0,
            "hidden_pass_rate": 0.5,
            "pbt_gate_passed": False,
            "pbt_group_pass_rate": 0.0,
            "static_violation": False,
            "crash": False,
            "timeout": False,
            "salieri_overlap": 0.0,
            "paradigm_distance": 0.9,
            "productivity_score": 0.9,
            "complexity_ratio_ok": None,
        },
        0.0,
        (0.0, 0.26),
    ),
    # Incorrect candidate → score near 0
    (
        {
            "public_pass_rate": 0.0,
            "hidden_pass_rate": 0.0,
            "pbt_gate_passed": False,
            "pbt_group_pass_rate": 0.0,
            "static_violation": False,
            "crash": True,
            "timeout": False,
            "salieri_overlap": 0.0,
            "paradigm_distance": 1.0,
            "productivity_score": 1.0,
            "complexity_ratio_ok": None,
        },
        0.0,
        (0.0, 0.01),
    ),
])
def test_compute_score_parametrized(metrics, expected_pd_score_ge, expected_score_range):
    result = compute_score(metrics)
    assert result["pd_score"] >= expected_pd_score_ge
    lo, hi = expected_score_range
    assert lo <= result["score"] <= hi, f"score={result['score']} not in [{lo}, {hi}]"
    assert 0.0 <= result["score"] <= 1.0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_perfect_correct_no_pd_fields():
    """When paradigm_distance/productivity_score missing, pd_score stays 0."""
    metrics = {
        "public_pass_rate": 1.0,
        "hidden_pass_rate": 1.0,
        "pbt_gate_passed": True,
        "pbt_group_pass_rate": 1.0,
        "static_violation": False,
        "crash": False,
        "timeout": False,
        "complexity_ratio_ok": True,
    }
    result = compute_score(metrics)
    assert result["pd_score"] == 0.0
    assert result["correctness_score"] == 1.0
    assert result["score"] == 0.85  # 0.50 + 0.20 + 0.15


def test_score_clamps_to_zero():
    metrics = {
        "public_pass_rate": 0.0,
        "hidden_pass_rate": 0.0,
        "pbt_gate_passed": False,
        "pbt_group_pass_rate": 0.0,
        "static_violation": True,
        "crash": True,
        "timeout": True,
        "salieri_overlap": 1.0,
        "paradigm_distance": 0.0,
        "productivity_score": 0.0,
        "complexity_ratio_ok": False,
    }
    result = compute_score(metrics)
    assert result["score"] == 0.0


def test_score_clamps_to_one():
    metrics = {
        "public_pass_rate": 1.0,
        "hidden_pass_rate": 1.0,
        "pbt_gate_passed": True,
        "pbt_group_pass_rate": 1.0,
        "static_violation": False,
        "crash": False,
        "timeout": False,
        "salieri_overlap": 0.0,
        "paradigm_distance": 1.0,
        "productivity_score": 1.0,
        "complexity_ratio_ok": True,
    }
    result = compute_score(metrics)
    assert result["score"] <= 1.0
    assert result["score"] >= 0.95
