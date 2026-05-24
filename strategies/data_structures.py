from __future__ import annotations

from hypothesis import strategies as st


# --- trcb-proto-0031: Bounded Recency-Ordered Store Operations ---

@st.composite
def lru_cache_case_strategy(draw):
    capacity = draw(st.integers(1, 20))
    n_ops = draw(st.integers(1, 100))
    operations = []
    for _ in range(n_ops):
        op_type = draw(st.sampled_from(["get", "put"]))
        key = draw(st.integers(0, 30))
        if op_type == "get":
            operations.append(("get", key))
        else:
            value = draw(st.integers(-100, 100))
            operations.append(("put", key, value))
    return {"input": {"capacity": capacity, "operations": operations}}


@st.composite
def lru_cache_boundary_strategy(draw):
    kind = draw(st.sampled_from(["single_cap", "all_gets", "all_puts_overflow", "get_then_put", "update_existing"]))
    if kind == "single_cap":
        ops = [("put", 1, 10), ("put", 2, 20), ("get", 1)]
        return {"input": {"capacity": 1, "operations": ops}}
    elif kind == "all_gets":
        ops = [("get", i) for i in range(5)]
        return {"input": {"capacity": 3, "operations": ops}}
    elif kind == "all_puts_overflow":
        ops = [("put", i, i * 10) for i in range(10)]
        ops.append(("get", 0))
        return {"input": {"capacity": 3, "operations": ops}}
    elif kind == "get_then_put":
        ops = [("get", 1), ("put", 1, 100), ("get", 1)]
        return {"input": {"capacity": 2, "operations": ops}}
    else:
        ops = [("put", 1, 10), ("put", 1, 20), ("get", 1)]
        return {"input": {"capacity": 2, "operations": ops}}


LRU_CACHE_PBT_GROUPS = {
    "differential": lru_cache_case_strategy,
    "boundary": lru_cache_boundary_strategy,
}


# --- trcb-proto-0032: Interval Extremum Precomputation Queries ---

@st.composite
def range_min_query_case_strategy(draw):
    arr = draw(st.lists(st.integers(-1000, 1000), min_size=1, max_size=100))
    n = len(arr)
    n_queries = draw(st.integers(1, 50))
    queries = []
    for _ in range(n_queries):
        l = draw(st.integers(0, n - 1))
        r = draw(st.integers(l, n - 1))
        queries.append((l, r))
    return {"input": {"arr": arr, "queries": queries}}


@st.composite
def range_min_query_boundary_strategy(draw):
    kind = draw(st.sampled_from(["single_element", "full_range", "same_index", "two_elements", "all_same"]))
    if kind == "single_element":
        v = draw(st.integers(-1000, 1000))
        return {"input": {"arr": [v], "queries": [(0, 0)]}}
    elif kind == "full_range":
        arr = draw(st.lists(st.integers(-1000, 1000), min_size=2, max_size=30))
        return {"input": {"arr": arr, "queries": [(0, len(arr) - 1)]}}
    elif kind == "same_index":
        arr = draw(st.lists(st.integers(-1000, 1000), min_size=1, max_size=30))
        i = draw(st.integers(0, len(arr) - 1))
        return {"input": {"arr": arr, "queries": [(i, i)]}}
    elif kind == "two_elements":
        a = draw(st.integers(-1000, 1000))
        b = draw(st.integers(-1000, 1000))
        return {"input": {"arr": [a, b], "queries": [(0, 0), (1, 1), (0, 1)]}}
    else:
        v = draw(st.integers(-1000, 1000))
        n = draw(st.integers(2, 20))
        return {"input": {"arr": [v] * n, "queries": [(0, n - 1)]}}


RANGE_MIN_QUERY_PBT_GROUPS = {
    "differential": range_min_query_case_strategy,
    "boundary": range_min_query_boundary_strategy,
}


# --- trcb-proto-0033: Hierarchical Prefix Frequency Counter ---

@st.composite
def prefix_count_case_strategy(draw):
    alphabet = "abcdefghij"
    n_words = draw(st.integers(0, 80))
    words = []
    for _ in range(n_words):
        length = draw(st.integers(1, 15))
        word = draw(st.text(alphabet=alphabet, min_size=length, max_size=length))
        words.append(word)
    n_queries = draw(st.integers(1, 30))
    queries = []
    for _ in range(n_queries):
        length = draw(st.integers(0, 10))
        q = draw(st.text(alphabet=alphabet, min_size=length, max_size=length))
        queries.append(q)
    return {"input": {"words": words, "queries": queries}}


@st.composite
def prefix_count_boundary_strategy(draw):
    kind = draw(st.sampled_from(["empty_words", "empty_query", "single_char_words", "no_match", "exact_match"]))
    if kind == "empty_words":
        return {"input": {"words": [], "queries": ["abc"]}}
    elif kind == "empty_query":
        words = draw(st.lists(st.text(alphabet="abc", min_size=1, max_size=5), min_size=1, max_size=10))
        return {"input": {"words": words, "queries": [""]}}
    elif kind == "single_char_words":
        words = ["a"] * draw(st.integers(1, 10))
        return {"input": {"words": words, "queries": ["a", "b"]}}
    elif kind == "no_match":
        return {"input": {"words": ["abc", "abd"], "queries": ["z", "x"]}}
    else:
        return {"input": {"words": ["hello", "help"], "queries": ["hello"]}}


PREFIX_COUNT_PBT_GROUPS = {
    "differential": prefix_count_case_strategy,
    "boundary": prefix_count_boundary_strategy,
}


# --- trcb-proto-0034: Layered Collection with Instant Floor Query ---

@st.composite
def min_stack_case_strategy(draw):
    n_ops = draw(st.integers(1, 100))
    operations = []
    stack_size = 0
    for _ in range(n_ops):
        if stack_size == 0:
            op_type = draw(st.sampled_from(["push", "get_min"]))
        else:
            op_type = draw(st.sampled_from(["push", "pop", "get_min"]))
        if op_type == "push":
            x = draw(st.integers(-100, 100))
            operations.append(("push", x))
            stack_size += 1
        elif op_type == "pop":
            operations.append(("pop",))
            stack_size -= 1
        else:
            operations.append(("get_min",))
    return {"input": {"operations": operations}}


@st.composite
def min_stack_boundary_strategy(draw):
    kind = draw(st.sampled_from(["empty_get_min", "pop_empty", "all_same_push", "ascending_push", "descending_push"]))
    if kind == "empty_get_min":
        return {"input": {"operations": [("get_min",)]}}
    elif kind == "pop_empty":
        return {"input": {"operations": [("pop",), ("get_min",)]}}
    elif kind == "all_same_push":
        v = draw(st.integers(-100, 100))
        n = draw(st.integers(1, 10))
        ops = [("push", v) for _ in range(n)]
        ops.append(("get_min",))
        return {"input": {"operations": ops}}
    elif kind == "ascending_push":
        ops = [("push", i) for i in range(1, 6)]
        ops.append(("get_min",))
        return {"input": {"operations": ops}}
    else:
        ops = [("push", i) for i in range(5, 0, -1)]
        ops.append(("get_min",))
        return {"input": {"operations": ops}}


MIN_STACK_PBT_GROUPS = {
    "differential": min_stack_case_strategy,
    "boundary": min_stack_boundary_strategy,
}


# --- trcb-proto-0035: Contiguous Region Consolidation ---

@st.composite
def merge_intervals_case_strategy(draw):
    n = draw(st.integers(0, 80))
    intervals = []
    for _ in range(n):
        start = draw(st.integers(-200, 200))
        end = draw(st.integers(start, start + 50))
        intervals.append((start, end))
    return {"input": {"intervals": intervals}}


@st.composite
def merge_intervals_boundary_strategy(draw):
    kind = draw(st.sampled_from(["empty", "single", "no_overlap", "all_overlap", "touching"]))
    if kind == "empty":
        return {"input": {"intervals": []}}
    elif kind == "single":
        s = draw(st.integers(-100, 100))
        e = draw(st.integers(s, s + 50))
        return {"input": {"intervals": [(s, e)]}}
    elif kind == "no_overlap":
        n = draw(st.integers(2, 8))
        intervals = [(i * 20, i * 20 + 5) for i in range(n)]
        return {"input": {"intervals": intervals}}
    elif kind == "all_overlap":
        n = draw(st.integers(2, 8))
        intervals = [(0, draw(st.integers(10, 50))) for _ in range(n)]
        return {"input": {"intervals": intervals}}
    else:
        n = draw(st.integers(2, 6))
        intervals = [(i * 5, (i + 1) * 5) for i in range(n)]
        return {"input": {"intervals": intervals}}


MERGE_INTERVALS_PBT_GROUPS = {
    "differential": merge_intervals_case_strategy,
    "boundary": merge_intervals_boundary_strategy,
}
