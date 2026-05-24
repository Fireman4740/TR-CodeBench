"""Unit tests for openrouter_runner.flatten_eval_result().

We call the method via a SimpleNamespace stub that only provides the
attributes accessed by the method (just `run_id`), avoiding the need to
spin up a full OpenRouterRunner with filesystem side-effects.
"""
from __future__ import annotations

import types
from typing import Any

import pytest

from trcodebench.openrouter_runner import OpenRouterRunner


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_runner() -> Any:
    """Return a minimal object that satisfies flatten_eval_result's attribute access."""
    return types.SimpleNamespace(run_id="test-run-0001")


def _minimal_eval_result(*, pbt_pass_rate: float = 0.8, pbt_gate: bool = True) -> dict[str, Any]:
    """Minimal eval_result dict shaped like evaluate_candidate() output."""
    return {
        "score": {
            "score": 0.75,
            "correctness_score": 1.0,
            "optimization_score": 0.7,
            "pd_score": 0.3,
            "hallucination_flag": False,
        },
        "metrics": {
            "public_pass_rate": 1.0,
            "hidden_pass_rate": 0.9,
            "pbt_gate_passed": pbt_gate,
            "pbt_group_pass_rate": pbt_pass_rate,
            "static_violation": False,
            "crash": False,
            "timeout": False,
            "salieri_overlap": 0.10,
            "paradigm_distance": 0.6,
            "productivity_score": 0.75,
            "complexity_ratio_ok": True,
        },
        "metrics_profile": {
            "correctness": 1.0,
            "robustness": 0.8,
            "efficiency": 0.7,
            "divergence": 0.6,
            "safety": 1.0,
        },
        "suites": {
            "public": {"total": 5, "passed": 5, "pass_rate": 1.0, "crash": False, "timeout": False, "failures": []},
            "hidden": {"total": 20, "passed": 18, "pass_rate": 0.9, "crash": False, "timeout": False, "failures": [
                {"suite": "hidden", "case_index": 2, "status": "ok", "input": {}, "expected": 1, "actual": 2, "error": None},
            ]},
            "pbt": {
                "pbt_gate_passed": pbt_gate,
                "pbt_group_pass_rate": pbt_pass_rate,
                "groups": {},
                "total": 25,
                "passed": int(pbt_pass_rate * 25),
                "pass_rate": pbt_pass_rate,
                "crash": False,
                "timeout": False,
                "failures": [],
            },
        },
        "pbt_error": None,
        "static_checks": {"ok": True, "violations": []},
        "pd_classification": {
            "paradigm_distance": 0.6,
            "productivity_score": 0.75,
            "originality_score": 0.90,
            "pd_score": 0.3,
            "candidate_paradigms": ["fenwick_tree"],
            "oracle_paradigms": ["patience_sorting"],
            "is_genuine_divergence": True,
            "known_valid_paradigms": ["patience_sorting"],
            "paradigm_evidence": {},
        },
        "complexity_profile": {
            "ratio": 10.0,
            "expected_ratio_max": 30.0,
            "small_median_seconds": 0.001,
            "large_median_seconds": 0.010,
            "small": {"valid_runs": 5, "failures": 0, "timeouts": 0},
            "large": {"valid_runs": 5, "failures": 0, "timeouts": 0},
        },
        "failure_analysis": {
            "public": {"wrong_answer": 0, "crash": 0, "timeout": 0},
            "hidden": {"wrong_answer": 1, "crash": 0, "timeout": 0},
            "pbt": {"wrong_answer": 0, "crash": 0, "unsatisfiable": 0, "counterexample": None},
        },
        "execution_context": {
            "model": "multiprocessing.Process",
            "python_version": "3.11.0",
            "timeout_seconds": 1.0,
            "isolation": "process-level",
            "packages_available": {},
        },
    }


def _flatten(eval_result: dict[str, Any], **kwargs) -> dict[str, Any]:
    """Helper: call flatten_eval_result with sensible defaults."""
    runner = _make_runner()
    return OpenRouterRunner.flatten_eval_result(
        runner,
        model=kwargs.get("model", "openai/gpt-4o-mini"),
        item_id=kwargs.get("item_id", "trcb-proto-0001"),
        run_index=kwargs.get("run_index", 0),
        candidate_path=None,
        response_json=None,
        latency_seconds=1.23,
        eval_result=eval_result,
        error=None,
    )


# ---------------------------------------------------------------------------
# pbt_pass_rate fix (was always None before fix)
# ---------------------------------------------------------------------------

def test_pbt_pass_rate_not_null():
    """pbt_pass_rate must come from suites.pbt.pass_rate, not metrics."""
    row = _flatten(_minimal_eval_result(pbt_pass_rate=0.8))
    assert row["pbt_pass_rate"] == pytest.approx(0.8), (
        "pbt_pass_rate was None before fix — should now reflect suites['pbt']['pass_rate']"
    )


def test_pbt_pass_rate_is_zero_when_all_fail():
    row = _flatten(_minimal_eval_result(pbt_pass_rate=0.0, pbt_gate=False))
    assert row["pbt_pass_rate"] == pytest.approx(0.0)


def test_pbt_pass_rate_is_one_when_all_pass():
    row = _flatten(_minimal_eval_result(pbt_pass_rate=1.0, pbt_gate=True))
    assert row["pbt_pass_rate"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# pbt_gate_passed exported
# ---------------------------------------------------------------------------

def test_pbt_gate_passed_exported_true():
    row = _flatten(_minimal_eval_result(pbt_gate=True))
    assert row["pbt_gate_passed"] is True


def test_pbt_gate_passed_exported_false():
    row = _flatten(_minimal_eval_result(pbt_gate=False))
    assert row["pbt_gate_passed"] is False


def test_pbt_gate_passed_not_missing():
    row = _flatten(_minimal_eval_result())
    assert "pbt_gate_passed" in row


# ---------------------------------------------------------------------------
# execution_model column
# ---------------------------------------------------------------------------

def test_execution_model_column():
    row = _flatten(_minimal_eval_result())
    assert row["execution_model"] == "multiprocessing.Process"


# ---------------------------------------------------------------------------
# Failure count columns
# ---------------------------------------------------------------------------

def test_public_failures_zero_when_no_failures():
    row = _flatten(_minimal_eval_result())
    assert row["public_failures"] == 0


def test_hidden_failures_counted():
    """hidden suite has 1 failure in _minimal_eval_result."""
    row = _flatten(_minimal_eval_result())
    assert row["hidden_failures"] == 1


def test_pbt_failures_zero_when_no_failures():
    row = _flatten(_minimal_eval_result())
    assert row["pbt_failures"] == 0


def test_pbt_failures_counted():
    er = _minimal_eval_result()
    er["suites"]["pbt"]["failures"] = [{"error": "got 3, expected 4"}]
    row = _flatten(er)
    assert row["pbt_failures"] == 1


# ---------------------------------------------------------------------------
# None-safe: graceful degradation when eval_result is None
# ---------------------------------------------------------------------------

def test_flatten_handles_none_eval_result():
    runner = _make_runner()
    row = OpenRouterRunner.flatten_eval_result(
        runner,
        model="openai/gpt-4o-mini",
        item_id="trcb-proto-0001",
        run_index=0,
        candidate_path=None,
        response_json=None,
        latency_seconds=None,
        eval_result=None,
        error="api error",
    )
    assert row["api_error"] == "api error"
    assert row["pbt_pass_rate"] is None
    assert row["pbt_gate_passed"] is None
    assert row["execution_model"] == "multiprocessing.Process"


# ---------------------------------------------------------------------------
# 5-axis metrics profile columns present
# ---------------------------------------------------------------------------

def test_metrics_profile_columns_present():
    row = _flatten(_minimal_eval_result())
    for col in ("mp_correctness", "mp_robustness", "mp_efficiency", "mp_divergence", "mp_safety"):
        assert col in row, f"column {col!r} missing from JSONL row"
        assert row[col] is not None
