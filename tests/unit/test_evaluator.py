from __future__ import annotations

import pytest

from trcodebench.evaluate import (
    _bar,
    _classify_pbt_failures,
    _classify_suite_failures,
    _format_compact,
    _format_human,
    evaluate_candidate,
)
from trcodebench.load_items import load_item, resolve_repo_path


# ---------------------------------------------------------------------------
# Minimal sample result fixture (no real evaluation needed for formatter tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_result() -> dict:
    """Minimal result dict that satisfies all formatter helpers."""
    return {
        "item_id": "trcb-proto-0001",
        "candidate": "/tmp/example.py",
        "metrics": {
            "public_pass_rate": 1.0,
            "hidden_pass_rate": 1.0,
            "pbt_gate_passed": True,
            "pbt_group_pass_rate": 0.8,
            "static_violation": False,
            "crash": False,
            "timeout": False,
            "salieri_overlap": 0.12,
            "paradigm_distance": 0.75,
            "productivity_score": 0.80,
            "complexity_ratio_ok": True,
        },
        "metrics_profile": {
            "correctness": 1.0,
            "robustness": 0.8,
            "efficiency": 0.7,
            "divergence": 0.6,
            "safety": 1.0,
        },
        "score": {"score": 0.77, "correctness_score": 1.0, "pd_score": 0.5, "optimization_score": 0.7},
        "static_checks": {"ok": True, "violations": []},
        "paradigm_features": {},
        "oracle_features": {},
        "pd_classification": {
            "paradigm_distance": 0.75,
            "productivity_score": 0.80,
            "originality_score": 0.88,
            "pd_score": 0.5,
            "candidate_paradigms": ["fenwick_tree"],
            "oracle_paradigms": ["patience_sorting"],
            "is_genuine_divergence": True,
            "known_valid_paradigms": ["patience_sorting", "fenwick_tree"],
            "paradigm_evidence": {},
        },
        "complexity_profile": {
            "ratio": 12.0,
            "expected_ratio_max": 30.0,
            "small_median_seconds": 0.001,
            "large_median_seconds": 0.012,
            "small": {"valid_runs": 5, "failures": 0, "timeouts": 0},
            "large": {"valid_runs": 5, "failures": 0, "timeouts": 0},
        },
        "suites": {
            "public": {"total": 5, "passed": 5, "pass_rate": 1.0, "crash": False, "timeout": False, "failures": []},
            "hidden": {"total": 20, "passed": 18, "pass_rate": 0.9, "crash": False, "timeout": False, "failures": [
                {"suite": "hidden", "case_index": 3, "status": "ok", "input": {}, "expected": 3, "actual": 4, "error": None},
                {"suite": "hidden", "case_index": 7, "status": "timeout", "input": {}, "expected": 5, "actual": None, "error": "timed out"},
            ]},
            "pbt": {
                "pbt_gate_passed": True,
                "pbt_group_pass_rate": 0.8,
                "groups": {},
                "total": 25,
                "passed": 20,
                "pass_rate": 0.8,
                "crash": False,
                "timeout": False,
                "failures": [],
            },
        },
        "pbt_error": None,
        "failure_analysis": {
            "public": {"wrong_answer": 0, "crash": 0, "timeout": 0},
            "hidden": {"wrong_answer": 1, "crash": 0, "timeout": 1},
            "pbt": {"wrong_answer": 0, "crash": 0, "unsatisfiable": 0, "counterexample": None},
        },
        "execution_context": {
            "model": "multiprocessing.Process",
            "python_version": "3.11.0 (default, ...) [GCC]",
            "timeout_seconds": 1.0,
            "isolation": "process-level (no network/fs isolation; static AST checks gate dangerous imports before execution)",
            "packages_available": {"hypothesis": "6.100.0", "jsonschema": None, "requests": "2.31.0", "python-dotenv": "1.0.0"},
        },
    }


# ---------------------------------------------------------------------------
# _bar() unit tests
# ---------------------------------------------------------------------------

def test_bar_full():
    bar = _bar(1.0)
    assert len(bar) == 16
    # All filled characters (either █ or # depending on terminal)
    assert bar == bar[0] * 16


def test_bar_zero():
    bar = _bar(0.0)
    assert len(bar) == 16
    # All empty characters (either ░ or . depending on terminal)
    assert bar == bar[0] * 16
    # Must differ from full bar
    assert bar != _bar(1.0)


def test_bar_none():
    bar = _bar(None)
    assert len(bar) == 16
    assert bar == "─" * 16


def test_bar_half():
    bar = _bar(0.5)
    assert len(bar) == 16
    # Exactly 8 filled, 8 empty
    fill_char = bar[0]
    empty_char = bar[-1]
    assert fill_char != empty_char
    assert bar.count(fill_char) == 8
    assert bar.count(empty_char) == 8


def test_bar_custom_width():
    bar = _bar(0.75, width=8)
    assert len(bar) == 8


def test_bar_clamps_above_one():
    assert _bar(2.0) == _bar(1.0)


def test_bar_clamps_below_zero():
    assert _bar(-1.0) == _bar(0.0)


# ---------------------------------------------------------------------------
# _format_compact() unit tests
# ---------------------------------------------------------------------------

def test_format_compact_contains_axes(sample_result):
    out = _format_compact(sample_result)
    for ax in ["C=", "R=", "E=", "D=", "S="]:
        assert ax in out, f"axis prefix {ax!r} missing from compact output"


def test_format_compact_contains_item_id(sample_result):
    out = _format_compact(sample_result)
    assert "trcb-proto-0001" in out


def test_format_compact_contains_suite_counts(sample_result):
    out = _format_compact(sample_result)
    assert "pub=5/5" in out
    assert "hid=18/20" in out


def test_format_compact_pbt_ok(sample_result):
    out = _format_compact(sample_result)
    assert "pbt=OK" in out


def test_format_compact_pbt_fail(sample_result):
    sample_result["suites"]["pbt"]["pbt_gate_passed"] = False
    out = _format_compact(sample_result)
    assert "pbt=FAIL" in out


def test_format_compact_score(sample_result):
    out = _format_compact(sample_result)
    assert "score=0.77" in out


# ---------------------------------------------------------------------------
# _format_human() unit tests
# ---------------------------------------------------------------------------

def test_format_human_contains_axes(sample_result):
    out = _format_human(sample_result)
    for ax in ["Correctness", "Robustness", "Efficiency", "Divergence", "Safety"]:
        assert ax in out, f"axis {ax!r} missing from human output"


def test_format_human_contains_execution_model(sample_result):
    out = _format_human(sample_result)
    assert "multiprocessing.Process" in out


def test_format_human_contains_item_id(sample_result):
    out = _format_human(sample_result)
    assert "trcb-proto-0001" in out


def test_format_human_shows_failure_breakdown(sample_result):
    out = _format_human(sample_result)
    # Hidden suite has 1 wrong_answer + 1 timeout → Failures line appears
    assert "Failures:" in out
    assert "wa=1" in out
    assert "to=1" in out


def test_format_human_no_failure_section_when_all_pass(sample_result):
    # Make everything pass
    sample_result["suites"]["hidden"]["failures"] = []
    sample_result["failure_analysis"]["hidden"] = {"wrong_answer": 0, "crash": 0, "timeout": 0}
    out = _format_human(sample_result)
    assert "Failures:" not in out


def test_format_human_static_violations_shown(sample_result):
    sample_result["static_checks"]["ok"] = False
    sample_result["static_checks"]["violations"] = ["import os is forbidden"]
    out = _format_human(sample_result)
    assert "Static Check Violations" in out
    assert "import os is forbidden" in out


def test_format_human_no_static_section_when_ok(sample_result):
    out = _format_human(sample_result)
    assert "Static Check Violations" not in out


def test_format_human_shows_paradigm_section(sample_result):
    out = _format_human(sample_result)
    assert "Paradigm Detection" in out
    assert "fenwick_tree" in out


# ---------------------------------------------------------------------------
# _classify_suite_failures() unit tests
# ---------------------------------------------------------------------------

def test_classify_suite_failures_empty():
    result = _classify_suite_failures({"failures": []})
    assert result == {"wrong_answer": 0, "crash": 0, "timeout": 0}


def test_classify_suite_failures_wrong_answer():
    # status "ok" with wrong output → wrong_answer
    result = _classify_suite_failures({
        "failures": [
            {"status": "ok", "expected": 1, "actual": 2},
            {"status": "ok", "expected": 3, "actual": 4},
        ]
    })
    assert result == {"wrong_answer": 2, "crash": 0, "timeout": 0}


def test_classify_suite_failures_crash():
    result = _classify_suite_failures({"failures": [{"status": "crash", "error": "ZeroDivisionError"}]})
    assert result == {"wrong_answer": 0, "crash": 1, "timeout": 0}


def test_classify_suite_failures_timeout():
    result = _classify_suite_failures({"failures": [{"status": "timeout"}]})
    assert result == {"wrong_answer": 0, "crash": 0, "timeout": 1}


def test_classify_suite_failures_mixed():
    result = _classify_suite_failures({
        "failures": [
            {"status": "ok"},        # wrong answer
            {"status": "crash"},
            {"status": "timeout"},
            {"status": "crash"},
        ]
    })
    assert result == {"wrong_answer": 1, "crash": 2, "timeout": 1}


# ---------------------------------------------------------------------------
# _classify_pbt_failures() unit tests
# ---------------------------------------------------------------------------

def test_classify_pbt_failures_empty():
    result = _classify_pbt_failures({"failures": []})
    assert result == {"wrong_answer": 0, "crash": 0, "unsatisfiable": 0, "counterexample": None}


def test_classify_pbt_failures_unsatisfiable():
    result = _classify_pbt_failures({"failures": [{"error": "Unsatisfiable: too many filters"}]})
    assert result["unsatisfiable"] == 1
    assert result["wrong_answer"] == 0
    assert result["crash"] == 0


def test_classify_pbt_failures_wrong_answer():
    result = _classify_pbt_failures({"failures": [{"error": "got 3, expected 4"}]})
    assert result["wrong_answer"] == 1
    assert result["counterexample"] == "got 3, expected 4"


def test_classify_pbt_failures_crash():
    result = _classify_pbt_failures({"failures": [{"error": "candidate crash: ZeroDivisionError"}]})
    assert result["crash"] == 1


def test_classify_pbt_counterexample_is_first():
    result = _classify_pbt_failures({
        "failures": [
            {"error": "first counterexample"},
            {"error": "second counterexample"},
        ]
    })
    assert result["counterexample"] == "first counterexample"
    assert result["wrong_answer"] == 2


# ---------------------------------------------------------------------------
# failure_analysis and execution_context in evaluate_candidate() output
# ---------------------------------------------------------------------------

def test_failure_analysis_present_in_output(sample_result):
    """failure_analysis must exist with all three suite keys."""
    assert "failure_analysis" in sample_result
    for suite in ("public", "hidden", "pbt"):
        assert suite in sample_result["failure_analysis"]


def test_execution_context_present_in_output(sample_result):
    """execution_context must contain model and isolation fields."""
    ctx = sample_result.get("execution_context", {})
    assert ctx.get("model") == "multiprocessing.Process"
    assert "isolation" in ctx
    assert "static AST checks" in ctx["isolation"]


def test_evaluator_accepts_reference_oracle_as_candidate():
    item = load_item("trcb-proto-0001")
    candidate = resolve_repo_path(item["oracle"]["reference_solution_path"])

    result = evaluate_candidate(
        "trcb-proto-0001",
        candidate,
        hidden_cases=5,
        pbt_cases=3,
        timeout_seconds=1.0,
    )

    assert result["score"]["correctness_score"] == 1.0
    assert result["metrics"]["hidden_pass_rate"] == 1.0
    assert result["metrics"]["pbt_gate_passed"] is True
    assert result["static_checks"]["ok"]


def test_reference_lis_is_not_productive_divergence():
    item = load_item("trcb-proto-0001")
    candidate = resolve_repo_path(item["oracle"]["reference_solution_path"])

    result = evaluate_candidate(
        "trcb-proto-0001",
        candidate,
        hidden_cases=3,
        pbt_cases=0,
        timeout_seconds=1.0,
    )

    assert result["score"]["correctness_score"] == 1.0
    assert result["score"]["pd_score"] == 0.0
    assert result["pd_classification"]["candidate_paradigms"] == ["patience_sorting"]
    assert result["pd_classification"]["oracle_paradigms"] == ["patience_sorting"]


def test_reference_kmp_is_classified_and_not_partial_pd():
    item = load_item("trcb-proto-0006")
    candidate = resolve_repo_path(item["oracle"]["reference_solution_path"])

    result = evaluate_candidate(
        "trcb-proto-0006",
        candidate,
        hidden_cases=3,
        pbt_cases=0,
        timeout_seconds=1.0,
    )

    assert result["score"]["correctness_score"] == 1.0
    assert result["score"]["pd_score"] == 0.0
    assert result["pd_classification"]["candidate_paradigms"] == ["kmp"]
    assert result["pd_classification"]["oracle_paradigms"] == ["kmp"]


def test_fenwick_lis_is_productive_divergence(tmp_path):
    candidate = tmp_path / "fenwick_lis.py"
    candidate.write_text(
        """
def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    values = {value: index + 1 for index, value in enumerate(sorted(set(nums)))}
    bit = [0] * (len(values) + 1)

    def update(index: int, value: int) -> None:
        while index < len(bit):
            if value > bit[index]:
                bit[index] = value
            index += index & -index

    def query(index: int) -> int:
        best = 0
        while index > 0:
            if bit[index] > best:
                best = bit[index]
            index -= index & -index
        return best

    answer = 0
    for number in nums:
        rank = values[number]
        current = query(rank - 1) + 1
        update(rank, current)
        if current > answer:
            answer = current
    return answer
""".strip()
    )

    result = evaluate_candidate(
        "trcb-proto-0001",
        candidate,
        hidden_cases=3,
        pbt_cases=0,
        timeout_seconds=1.0,
    )

    assert result["score"]["correctness_score"] == 1.0
    assert result["score"]["pd_score"] > 0.0
    assert result["pd_classification"]["candidate_paradigms"] == ["fenwick_tree_coordinate_compression"]


def test_quadratic_lis_fails_complexity_profile(tmp_path):
    candidate = tmp_path / "quadratic_lis.py"
    candidate.write_text(
        """
def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    dp = [1] * len(nums)
    for right in range(len(nums)):
        for left in range(right):
            if nums[left] < nums[right] and dp[left] + 1 > dp[right]:
                dp[right] = dp[left] + 1
    return max(dp)
""".strip()
    )

    result = evaluate_candidate(
        "trcb-proto-0001",
        candidate,
        hidden_cases=2,
        pbt_cases=0,
        timeout_seconds=0.2,
    )

    assert result["score"]["correctness_score"] == 1.0
    assert result["metrics"]["complexity_ratio_ok"] is False
    assert result["score"]["optimization_score"] == 0.0
    assert result["score"]["score"] <= 0.60
    assert result["score"]["pd_score"] == 0.0


def test_reference_fenwick_item_is_not_productive_divergence():
    item = load_item("trcb-proto-0009")
    candidate = resolve_repo_path(item["oracle"]["reference_solution_path"])

    result = evaluate_candidate(
        "trcb-proto-0009",
        candidate,
        hidden_cases=3,
        pbt_cases=0,
        timeout_seconds=1.0,
    )

    assert result["score"]["correctness_score"] == 1.0
    assert result["score"]["pd_score"] == 0.0
    assert result["pd_classification"]["candidate_paradigms"] == ["fenwick_tree"]
    assert result["pd_classification"]["oracle_paradigms"] == ["fenwick_tree"]


def test_naive_range_sum_fails_fenwick_complexity_profile(tmp_path):
    candidate = tmp_path / "naive_range_sum.py"
    candidate.write_text(
        """
def solve(n: int, operations: list[tuple[str, int, int]]) -> list[int]:
    values = [0] * n
    answer = []
    for operation, left, right in operations:
        if operation == "add":
            values[left] += right
        elif operation == "sum":
            answer.append(sum(values[left:right]))
        else:
            raise ValueError(f"unknown operation {operation!r}")
    return answer
""".strip()
    )

    result = evaluate_candidate(
        "trcb-proto-0009",
        candidate,
        hidden_cases=2,
        pbt_cases=0,
        timeout_seconds=0.2,
    )

    assert result["score"]["correctness_score"] == 1.0
    assert result["metrics"]["complexity_ratio_ok"] is False
    assert result["score"]["optimization_score"] == 0.0
    assert result["score"]["score"] <= 0.60
    assert result["score"]["pd_score"] == 0.0
