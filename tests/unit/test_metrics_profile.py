"""Tests for the independent metrics_profile module."""

from __future__ import annotations

import pytest

from trcodebench.metrics_profile import (
    aggregate_profiles,
    compute_correctness,
    compute_divergence,
    compute_efficiency,
    compute_metrics_profile,
    compute_robustness,
    compute_safety,
)


# ---------------------------------------------------------------------------
# Axis 1 — Correctness
# ---------------------------------------------------------------------------


def test_correctness_both_perfect():
    assert compute_correctness({"public_pass_rate": 1.0, "hidden_pass_rate": 1.0}) == 1.0


def test_correctness_public_fails():
    assert compute_correctness({"public_pass_rate": 0.8, "hidden_pass_rate": 1.0}) == 0.0


def test_correctness_hidden_fails():
    assert compute_correctness({"public_pass_rate": 1.0, "hidden_pass_rate": 0.9}) == 0.0


def test_correctness_both_fail():
    assert compute_correctness({"public_pass_rate": 0.0, "hidden_pass_rate": 0.0}) == 0.0


# ---------------------------------------------------------------------------
# Axis 2 — Robustness
# ---------------------------------------------------------------------------


def test_robustness_all_pass():
    assert compute_robustness({"pbt_gate_passed": True, "pbt_group_pass_rate": 1.0}) == 1.0


def test_robustness_gate_fails():
    score = compute_robustness({"pbt_gate_passed": False, "pbt_group_pass_rate": 0.5})
    assert score == pytest.approx(0.15, abs=0.001)


def test_robustness_partial():
    score = compute_robustness({"pbt_gate_passed": True, "pbt_group_pass_rate": 0.6})
    # 0.7 * 1.0 + 0.3 * 0.6 = 0.88
    assert score == pytest.approx(0.88, abs=0.001)


# ---------------------------------------------------------------------------
# Axis 3 — Efficiency
# ---------------------------------------------------------------------------


def test_efficiency_correctness_fails_returns_none():
    metrics = {"public_pass_rate": 0.5, "hidden_pass_rate": 1.0, "complexity_ratio_ok": True}
    assert compute_efficiency(metrics) is None


def test_efficiency_ratio_ok_none_returns_none():
    metrics = {"public_pass_rate": 1.0, "hidden_pass_rate": 1.0, "complexity_ratio_ok": None}
    assert compute_efficiency(metrics) is None


def test_efficiency_ratio_ok_false_returns_zero():
    metrics = {"public_pass_rate": 1.0, "hidden_pass_rate": 1.0, "complexity_ratio_ok": False}
    assert compute_efficiency(metrics) == 0.0


def test_efficiency_with_profile_perfect():
    metrics = {
        "public_pass_rate": 1.0,
        "hidden_pass_rate": 1.0,
        "complexity_ratio_ok": True,
        "complexity_profile": {"ratio": 0.0, "expected_ratio_max": 30.0},
    }
    assert compute_efficiency(metrics) == 1.0


def test_efficiency_with_profile_at_limit():
    metrics = {
        "public_pass_rate": 1.0,
        "hidden_pass_rate": 1.0,
        "complexity_ratio_ok": True,
        "complexity_profile": {"ratio": 30.0, "expected_ratio_max": 30.0},
    }
    assert compute_efficiency(metrics) == 0.0


def test_efficiency_with_profile_midpoint():
    metrics = {
        "public_pass_rate": 1.0,
        "hidden_pass_rate": 1.0,
        "complexity_ratio_ok": True,
        "complexity_profile": {"ratio": 15.0, "expected_ratio_max": 30.0},
    }
    assert compute_efficiency(metrics) == pytest.approx(0.5, abs=0.001)


def test_efficiency_no_profile_returns_one():
    metrics = {"public_pass_rate": 1.0, "hidden_pass_rate": 1.0, "complexity_ratio_ok": True}
    assert compute_efficiency(metrics) == 1.0


# ---------------------------------------------------------------------------
# Axis 4 — Divergence
# ---------------------------------------------------------------------------


def test_divergence_correctness_fails_returns_none():
    metrics = {
        "public_pass_rate": 0.5,
        "hidden_pass_rate": 1.0,
        "salieri_overlap": 0.1,
        "paradigm_distance": 0.8,
        "complexity_ratio_ok": True,
    }
    assert compute_divergence(metrics) is None


def test_divergence_optimization_failed_returns_zero():
    metrics = {
        "public_pass_rate": 1.0,
        "hidden_pass_rate": 1.0,
        "salieri_overlap": 0.1,
        "paradigm_distance": 0.8,
        "complexity_ratio_ok": False,
    }
    assert compute_divergence(metrics) == 0.0


def test_divergence_salieri_too_high_returns_zero():
    metrics = {
        "public_pass_rate": 1.0,
        "hidden_pass_rate": 1.0,
        "salieri_overlap": 0.85,
        "paradigm_distance": 0.8,
        "complexity_ratio_ok": True,
    }
    assert compute_divergence(metrics) == 0.0


def test_divergence_distance_too_low_returns_zero():
    metrics = {
        "public_pass_rate": 1.0,
        "hidden_pass_rate": 1.0,
        "salieri_overlap": 0.1,
        "paradigm_distance": 0.1,
        "complexity_ratio_ok": True,
    }
    assert compute_divergence(metrics) == 0.0


def test_divergence_genuine_case():
    metrics = {
        "public_pass_rate": 1.0,
        "hidden_pass_rate": 1.0,
        "salieri_overlap": 0.1,
        "paradigm_distance": 0.8,
        "complexity_ratio_ok": True,
        "is_genuine_divergence": False,
    }
    score = compute_divergence(metrics)
    assert score is not None
    assert score > 0.0
    assert score <= 1.0


def test_divergence_genuine_bonus():
    metrics_base = {
        "public_pass_rate": 1.0,
        "hidden_pass_rate": 1.0,
        "salieri_overlap": 0.1,
        "paradigm_distance": 0.8,
        "complexity_ratio_ok": True,
        "is_genuine_divergence": False,
    }
    metrics_genuine = {**metrics_base, "is_genuine_divergence": True}

    base_score = compute_divergence(metrics_base)
    genuine_score = compute_divergence(metrics_genuine)
    assert genuine_score > base_score


# ---------------------------------------------------------------------------
# Axis 5 — Safety
# ---------------------------------------------------------------------------


def test_safety_all_clean():
    metrics = {"static_violation": False, "crash": False, "hidden_pass_rate": 1.0}
    assert compute_safety(metrics) == 1.0


def test_safety_static_violation():
    metrics = {"static_violation": True, "crash": False, "hidden_pass_rate": 1.0}
    assert compute_safety(metrics) == 0.0


def test_safety_crash():
    metrics = {"static_violation": False, "crash": True, "hidden_pass_rate": 1.0}
    assert compute_safety(metrics) == 0.0


def test_safety_hidden_incomplete():
    metrics = {"static_violation": False, "crash": False, "hidden_pass_rate": 0.9}
    assert compute_safety(metrics) == 0.0


# ---------------------------------------------------------------------------
# Full profile
# ---------------------------------------------------------------------------


def test_full_profile_perfect_candidate():
    metrics = {
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
    }
    profile = compute_metrics_profile(
        metrics=metrics,
        complexity_profile={"ratio": 5.0, "expected_ratio_max": 30.0},
        is_genuine_divergence=True,
    )
    assert profile["correctness"] == 1.0
    assert profile["robustness"] == 1.0
    assert profile["efficiency"] == pytest.approx(0.8333, abs=0.01)
    assert profile["divergence"] > 0.5
    assert profile["safety"] == 1.0


def test_full_profile_incorrect_candidate():
    metrics = {
        "public_pass_rate": 0.5,
        "hidden_pass_rate": 0.0,
        "pbt_gate_passed": False,
        "pbt_group_pass_rate": 0.0,
        "static_violation": True,
        "crash": True,
        "timeout": False,
        "salieri_overlap": 0.0,
        "paradigm_distance": 1.0,
        "productivity_score": 1.0,
        "complexity_ratio_ok": None,
    }
    profile = compute_metrics_profile(metrics=metrics)
    assert profile["correctness"] == 0.0
    assert profile["robustness"] == 0.0
    assert profile["efficiency"] is None
    assert profile["divergence"] is None
    assert profile["safety"] == 0.0


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def test_aggregate_profiles_basic():
    profiles = [
        {"correctness": 1.0, "robustness": 0.8, "efficiency": 0.5, "divergence": 0.3, "safety": 1.0},
        {"correctness": 1.0, "robustness": 0.6, "efficiency": 0.7, "divergence": None, "safety": 1.0},
    ]
    agg = aggregate_profiles(profiles)
    assert agg["correctness"] == 1.0
    assert agg["robustness"] == pytest.approx(0.7, abs=0.001)
    assert agg["efficiency"] == pytest.approx(0.6, abs=0.001)
    assert agg["divergence"] == pytest.approx(0.3, abs=0.001)  # Only one value
    assert agg["safety"] == 1.0


def test_aggregate_profiles_all_none():
    profiles = [
        {"correctness": 0.0, "robustness": 0.0, "efficiency": None, "divergence": None, "safety": 0.0},
        {"correctness": 0.0, "robustness": 0.0, "efficiency": None, "divergence": None, "safety": 0.0},
    ]
    agg = aggregate_profiles(profiles)
    assert agg["efficiency"] is None
    assert agg["divergence"] is None


# ---------------------------------------------------------------------------
# Independence: axes don't interfere with each other
# ---------------------------------------------------------------------------


def test_axes_independence_safety_vs_correctness():
    """A candidate can be safe (no crash/violation) but still incorrect."""
    metrics = {
        "public_pass_rate": 0.0,
        "hidden_pass_rate": 1.0,
        "pbt_gate_passed": True,
        "pbt_group_pass_rate": 1.0,
        "static_violation": False,
        "crash": False,
        "timeout": False,
        "salieri_overlap": 0.0,
        "paradigm_distance": 0.0,
        "complexity_ratio_ok": None,
    }
    profile = compute_metrics_profile(metrics=metrics)
    assert profile["correctness"] == 0.0
    assert profile["safety"] == 1.0  # Safety is independent


def test_axes_independence_robustness_vs_efficiency():
    """Robustness can be low while efficiency is high."""
    metrics = {
        "public_pass_rate": 1.0,
        "hidden_pass_rate": 1.0,
        "pbt_gate_passed": False,
        "pbt_group_pass_rate": 0.3,
        "static_violation": False,
        "crash": False,
        "timeout": False,
        "salieri_overlap": 0.5,
        "paradigm_distance": 0.1,
        "complexity_ratio_ok": True,
    }
    profile = compute_metrics_profile(
        metrics=metrics,
        complexity_profile={"ratio": 2.0, "expected_ratio_max": 30.0},
    )
    assert profile["robustness"] < 0.5
    assert profile["efficiency"] > 0.9
