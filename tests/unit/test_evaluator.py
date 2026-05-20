from __future__ import annotations

from trcodebench.evaluate import evaluate_candidate
from trcodebench.load_items import load_item, resolve_repo_path


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
