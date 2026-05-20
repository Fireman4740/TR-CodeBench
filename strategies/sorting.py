from __future__ import annotations

from hypothesis import strategies as st


# --- trcb-proto-0011: Count Inversions ---

@st.composite
def inversions_case_strategy(draw):
    nums = draw(st.lists(st.integers(-100, 100), max_size=120))
    return {"input": {"nums": nums}}


@st.composite
def inversions_boundary_strategy(draw):
    kind = draw(st.sampled_from(["empty", "single", "sorted_asc", "sorted_desc", "all_same"]))
    if kind == "empty":
        nums = []
    elif kind == "single":
        nums = [draw(st.integers(-100, 100))]
    elif kind == "sorted_asc":
        n = draw(st.integers(2, 30))
        nums = sorted(draw(st.lists(st.integers(-100, 100), min_size=n, max_size=n)))
    elif kind == "sorted_desc":
        n = draw(st.integers(2, 30))
        nums = sorted(draw(st.lists(st.integers(-100, 100), min_size=n, max_size=n)), reverse=True)
    else:
        v = draw(st.integers(-100, 100))
        nums = [v] * draw(st.integers(1, 30))
    return {"input": {"nums": nums}}


INVERSIONS_PBT_GROUPS = {
    "differential": inversions_case_strategy,
    "boundary": inversions_boundary_strategy,
}


# --- trcb-proto-0012: Kth Largest Element ---

@st.composite
def kth_largest_case_strategy(draw):
    nums = draw(st.lists(st.integers(-100, 100), min_size=1, max_size=120))
    k = draw(st.integers(1, len(nums)))
    return {"input": {"nums": nums, "k": k}}


@st.composite
def kth_largest_boundary_strategy(draw):
    kind = draw(st.sampled_from(["single", "all_same", "k_is_one", "k_is_len", "two_elements"]))
    if kind == "single":
        return {"input": {"nums": [draw(st.integers(-100, 100))], "k": 1}}
    elif kind == "all_same":
        v = draw(st.integers(-100, 100))
        n = draw(st.integers(1, 30))
        k = draw(st.integers(1, n))
        return {"input": {"nums": [v] * n, "k": k}}
    elif kind == "k_is_one":
        nums = draw(st.lists(st.integers(-100, 100), min_size=1, max_size=30))
        return {"input": {"nums": nums, "k": 1}}
    elif kind == "k_is_len":
        nums = draw(st.lists(st.integers(-100, 100), min_size=1, max_size=30))
        return {"input": {"nums": nums, "k": len(nums)}}
    else:
        a = draw(st.integers(-100, 100))
        b = draw(st.integers(-100, 100))
        k = draw(st.integers(1, 2))
        return {"input": {"nums": [a, b], "k": k}}


KTH_LARGEST_PBT_GROUPS = {
    "differential": kth_largest_case_strategy,
    "boundary": kth_largest_boundary_strategy,
}


# --- trcb-proto-0013: Next Greater Element (Circular) ---

@st.composite
def next_greater_circular_case_strategy(draw):
    nums = draw(st.lists(st.integers(-100, 100), max_size=120))
    return {"input": {"nums": nums}}


@st.composite
def next_greater_circular_boundary_strategy(draw):
    kind = draw(st.sampled_from(["empty", "single", "all_same", "ascending", "descending"]))
    if kind == "empty":
        nums = []
    elif kind == "single":
        nums = [draw(st.integers(-100, 100))]
    elif kind == "all_same":
        v = draw(st.integers(-100, 100))
        nums = [v] * draw(st.integers(2, 30))
    elif kind == "ascending":
        n = draw(st.integers(2, 30))
        nums = sorted(draw(st.lists(st.integers(-100, 100), min_size=n, max_size=n)))
    else:
        n = draw(st.integers(2, 30))
        nums = sorted(draw(st.lists(st.integers(-100, 100), min_size=n, max_size=n)), reverse=True)
    return {"input": {"nums": nums}}


NEXT_GREATER_CIRCULAR_PBT_GROUPS = {
    "differential": next_greater_circular_case_strategy,
    "boundary": next_greater_circular_boundary_strategy,
}


# --- trcb-proto-0014: Running Median ---

@st.composite
def running_median_case_strategy(draw):
    stream = draw(st.lists(st.integers(-100, 100), min_size=1, max_size=120))
    return {"input": {"stream": stream}}


@st.composite
def running_median_boundary_strategy(draw):
    kind = draw(st.sampled_from(["single", "two_elements", "all_same", "ascending", "descending"]))
    if kind == "single":
        return {"input": {"stream": [draw(st.integers(-100, 100))]}}
    elif kind == "two_elements":
        a = draw(st.integers(-100, 100))
        b = draw(st.integers(-100, 100))
        return {"input": {"stream": [a, b]}}
    elif kind == "all_same":
        v = draw(st.integers(-100, 100))
        n = draw(st.integers(1, 30))
        return {"input": {"stream": [v] * n}}
    elif kind == "ascending":
        n = draw(st.integers(2, 30))
        return {"input": {"stream": sorted(draw(st.lists(st.integers(-100, 100), min_size=n, max_size=n)))}}
    else:
        n = draw(st.integers(2, 30))
        return {"input": {"stream": sorted(draw(st.lists(st.integers(-100, 100), min_size=n, max_size=n)), reverse=True)}}


RUNNING_MEDIAN_PBT_GROUPS = {
    "differential": running_median_case_strategy,
    "boundary": running_median_boundary_strategy,
}


# --- trcb-proto-0015: Merge K Sorted Lists ---

@st.composite
def merge_k_sorted_case_strategy(draw):
    k = draw(st.integers(0, 10))
    lists = []
    for _ in range(k):
        lst = sorted(draw(st.lists(st.integers(-100, 100), max_size=30)))
        lists.append(lst)
    return {"input": {"lists": lists}}


@st.composite
def merge_k_sorted_boundary_strategy(draw):
    kind = draw(st.sampled_from(["empty_outer", "empty_inner", "single_list", "single_elements", "all_same"]))
    if kind == "empty_outer":
        return {"input": {"lists": []}}
    elif kind == "empty_inner":
        k = draw(st.integers(1, 5))
        return {"input": {"lists": [[] for _ in range(k)]}}
    elif kind == "single_list":
        lst = sorted(draw(st.lists(st.integers(-100, 100), min_size=1, max_size=30)))
        return {"input": {"lists": [lst]}}
    elif kind == "single_elements":
        k = draw(st.integers(1, 10))
        return {"input": {"lists": [[draw(st.integers(-100, 100))] for _ in range(k)]}}
    else:
        v = draw(st.integers(-100, 100))
        k = draw(st.integers(1, 5))
        n = draw(st.integers(1, 10))
        return {"input": {"lists": [[v] * n for _ in range(k)]}}


MERGE_K_SORTED_PBT_GROUPS = {
    "differential": merge_k_sorted_case_strategy,
    "boundary": merge_k_sorted_boundary_strategy,
}
