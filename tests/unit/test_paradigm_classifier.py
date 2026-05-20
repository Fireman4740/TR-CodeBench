from __future__ import annotations

import pytest

from trcodebench.paradigm_classifier import (
    detect_paradigms,
    is_genuine_divergence,
    paradigm_distance,
)


_EMPTY_FEATURES: dict = {
    "syntax_error": False,
    "recursion": False,
    "heapq": False,
    "bisect": False,
    "deque": False,
    "dict_memo": False,
    "union_find": False,
    "fenwick": False,
    "kmp_prefix_table": False,
    "rolling_hash": False,
    "z_algorithm": False,
    "nested_loops": 0,
}


def _features(**kwargs) -> dict:
    return {**_EMPTY_FEATURES, **kwargs}


# ---------------------------------------------------------------------------
# is_genuine_divergence
# ---------------------------------------------------------------------------

def test_genuine_divergence_false_when_candidate_unclassified():
    diverge, cand_p, oracle_p = is_genuine_divergence(
        candidate_features=_features(),          # no paradigm matches
        oracle_features=_features(bisect=True),
        known_paradigms=["patience_sorting"],
    )
    assert diverge is False
    assert cand_p == []


def test_genuine_divergence_false_when_oracle_unclassified():
    """Bug fix: oracle empty must NOT grant PD to candidate."""
    diverge, cand_p, oracle_p = is_genuine_divergence(
        candidate_features=_features(fenwick=True),
        oracle_features=_features(),             # oracle matches nothing
        known_paradigms=["fenwick_tree"],
    )
    assert diverge is False
    assert oracle_p == []


def test_genuine_divergence_false_when_same_paradigm():
    diverge, cand_p, oracle_p = is_genuine_divergence(
        candidate_features=_features(bisect=True),
        oracle_features=_features(bisect=True),
        known_paradigms=["patience_sorting"],
    )
    assert diverge is False
    assert "patience_sorting" in cand_p
    assert "patience_sorting" in oracle_p


def test_genuine_divergence_true_when_different_paradigms():
    diverge, cand_p, oracle_p = is_genuine_divergence(
        candidate_features=_features(fenwick=True, coordinate_compression=True),
        oracle_features=_features(bisect=True),
        known_paradigms=["patience_sorting", "fenwick_tree_coordinate_compression"],
    )
    assert diverge is True
    assert "fenwick_tree_coordinate_compression" in cand_p
    assert "patience_sorting" in oracle_p


def test_genuine_divergence_false_when_partial_overlap():
    # candidate matches both patience_sorting and fenwick; oracle matches patience_sorting
    # overlap is non-empty → NOT genuine divergence
    diverge, cand_p, oracle_p = is_genuine_divergence(
        candidate_features=_features(bisect=True, fenwick=True),
        oracle_features=_features(bisect=True),
        known_paradigms=["patience_sorting", "fenwick_tree_coordinate_compression"],
    )
    assert diverge is False


# ---------------------------------------------------------------------------
# paradigm_distance
# ---------------------------------------------------------------------------

def test_paradigm_distance_zero_for_identical_features():
    f = _features(bisect=True, nested_loops=1)
    assert paradigm_distance(f, f) == 0.0


def test_paradigm_distance_zero_for_two_empty_feature_sets():
    assert paradigm_distance(_features(), _features()) == 0.0


def test_paradigm_distance_one_when_one_side_empty():
    assert paradigm_distance(_features(heapq=True), _features()) == 1.0
    assert paradigm_distance(_features(), _features(heapq=True)) == 1.0


def test_paradigm_distance_between_zero_and_one_for_partial_overlap():
    a = _features(bisect=True, heapq=False)
    b = _features(bisect=False, heapq=True)
    d = paradigm_distance(a, b)
    assert 0.0 < d <= 1.0


def test_paradigm_distance_less_for_similar_than_different():
    base = _features(bisect=True, heapq=True)
    similar = _features(bisect=True, heapq=False)
    different = _features(bisect=False, heapq=False, fenwick=True)
    assert paradigm_distance(base, similar) < paradigm_distance(base, different)


def test_paradigm_distance_is_symmetric():
    a = _features(bisect=True, recursion=True)
    b = _features(heapq=True, deque=True)
    assert paradigm_distance(a, b) == paradigm_distance(b, a)


# ---------------------------------------------------------------------------
# detect_paradigms
# ---------------------------------------------------------------------------

def test_detect_patience_sorting():
    features = _features(bisect=True)
    detected = detect_paradigms(features, ["patience_sorting"])
    assert "patience_sorting" in detected


def test_detect_kmp():
    features = _features(kmp_prefix_table=True)
    detected = detect_paradigms(features, ["kmp"])
    assert "kmp" in detected


def test_unknown_paradigm_skipped():
    features = _features(bisect=True)
    detected = detect_paradigms(features, ["nonexistent_paradigm"])
    assert detected == []


def test_detect_union_find():
    features = _features(union_find=True)
    detected = detect_paradigms(features, ["union_find"])
    assert "union_find" in detected


@pytest.mark.parametrize("paradigm,feature_key", [
    ("fenwick_tree", "fenwick"),
    ("rolling_hash_with_verification", "rolling_hash"),
    ("z_algorithm", "z_algorithm"),
    ("dfs_memoization", "recursion"),
])
def test_detect_various_paradigms(paradigm: str, feature_key: str):
    feat = _features(**{feature_key: True})
    if paradigm == "dfs_memoization":
            feat = _features(recursion=True, dict_memo=True, adjacency_list=True)
