from __future__ import annotations

from typing import Any


PARADIGM_SIGNATURES: dict[str, dict[str, Any]] = {
    "patience_sorting": {"bisect": True, "recursion": False, "dict_memo": False},
    "prefix_sums_binary_search": {"bisect": True, "dict_memo": True},
    "balanced_tree_scheduler": {"bisect": True, "heapq": True},
    "fenwick_tree_coordinate_compression": {"fenwick": True, "coordinate_compression": True},
    "fenwick_tree": {"fenwick": True, "coordinate_compression": False},
    "segment_tree_dp": {"recursion": True, "nested_loops": 0, "dict_memo": True},
    "segment_tree": {"recursion": True, "nested_loops": 0, "dict_memo": False},
    "dfs_memoization": {"recursion": True, "dict_memo": True, "adjacency_list": True},
    "dijkstra_heap": {"heapq": True, "adjacency_list": True},
    "a_star_with_zero_heuristic": {"heapq": True, "adjacency_list": True},
    "sweep_line_variant": {"heapq": True, "adjacency_list": False, "recursion": False},
    "lazy_heap": {"heapq": True, "adjacency_list": False, "dict_memo": True},
    "greedy_heap": {"heapq": True, "adjacency_list": False, "dict_memo": False, "recursion": False},
    "event_sweep_with_priority_queue": {"heapq": True, "adjacency_list": False},
    "bucketed_dijkstra_for_small_weights": {"deque": True, "adjacency_list": True},
    "topological_dp": {"deque": True, "adjacency_list": True, "recursion": False},
    "relaxation_in_known_topological_order": {"deque": True, "adjacency_list": True},
    "offline_graph_traversal": {"deque": True, "union_find": False, "adjacency_list": True},
    "monotone_queue_generalization": {"deque": True, "adjacency_list": False},
    "monotonic_deque": {"deque": True, "adjacency_list": False},
    "greedy_by_finish_time": {"nested_loops": 0, "bisect": False, "recursion": False, "heapq": False},
    "two_pointers": {"nested_loops": 1, "heapq": False, "bisect": False},
    "block_prefix_suffix": {"nested_loops": 0, "deque": False, "heapq": False},
    "union_find": {"union_find": True},
    "component_labeling_after_build": {"dict_memo": True, "union_find": False, "adjacency_list": True},
    "dynamic_programming_with_sorting": {"dict_memo": True, "adjacency_list": False, "recursion": False},
    "kmp": {"kmp_prefix_table": True},
    "rolling_hash_with_verification": {"rolling_hash": True},
    "z_algorithm": {"z_algorithm": True},
    "sqrt_decomposition": {"nested_loops": 1},
}

_FEATURE_KEYS = [
    "recursion", "heapq", "bisect", "deque",
    "dict_memo", "union_find", "fenwick",
    "kmp_prefix_table", "rolling_hash", "z_algorithm",
    "adjacency_list", "coordinate_compression",
]


def _to_vector(features: dict[str, Any]) -> list[float]:
    vec = [float(bool(features.get(k, False))) for k in _FEATURE_KEYS]
    nested = min(int(features.get("nested_loops", 0)), 2) / 2.0
    vec.append(nested)
    return vec


def paradigm_distance(candidate_features: dict[str, Any], oracle_features: dict[str, Any]) -> float:
    va = _to_vector(candidate_features)
    vb = _to_vector(oracle_features)
    dot = sum(x * y for x, y in zip(va, vb))
    norm_a = sum(x * x for x in va) ** 0.5
    norm_b = sum(x * x for x in vb) ** 0.5
    if norm_a == 0 and norm_b == 0:
        return 0.0
    if norm_a == 0 or norm_b == 0:
        return 1.0
    cosine_sim = dot / (norm_a * norm_b)
    return round(1.0 - cosine_sim, 6)


def detect_paradigms(features: dict[str, Any], known_paradigms: list[str]) -> list[str]:
    matched: list[str] = []
    for paradigm in known_paradigms:
        signature = PARADIGM_SIGNATURES.get(paradigm)
        if signature is None:
            continue
        if _matches(features, signature):
            matched.append(paradigm)
    return matched


def _matches(features: dict[str, Any], signature: dict[str, Any]) -> bool:
    for key, required in signature.items():
        actual = features.get(key)
        if isinstance(required, bool):
            if bool(actual) != required:
                return False
        elif isinstance(required, int):
            if key == "nested_loops":
                actual_loops = int(actual or 0)
                if required == 0 and actual_loops > 0:
                    return False
                if required == 1 and actual_loops == 0:
                    return False
            elif int(actual or 0) != required:
                return False
        else:
            if actual != required:
                return False
    return True


def is_genuine_divergence(
    candidate_features: dict[str, Any],
    oracle_features: dict[str, Any],
    known_paradigms: list[str],
) -> tuple[bool, list[str], list[str]]:
    candidate_paradigms = detect_paradigms(candidate_features, known_paradigms)
    oracle_paradigms = detect_paradigms(oracle_features, known_paradigms)
    if not candidate_paradigms or not oracle_paradigms:
        return False, candidate_paradigms, oracle_paradigms
    overlap = set(candidate_paradigms) & set(oracle_paradigms)
    return len(overlap) == 0, candidate_paradigms, oracle_paradigms
