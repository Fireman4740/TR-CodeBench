from __future__ import annotations

from hypothesis import strategies as st


@st.composite
def lis_case_strategy(draw):
    nums = draw(st.lists(st.integers(-100, 100), max_size=120))
    return {"input": {"nums": nums}}


@st.composite
def lis_boundary_strategy(draw):
    kind = draw(st.sampled_from(["empty", "single", "all_same", "descending", "ascending", "two_elements"]))
    if kind == "empty":
        nums = []
    elif kind == "single":
        nums = [draw(st.integers(-100, 100))]
    elif kind == "all_same":
        v = draw(st.integers(-100, 100))
        nums = [v] * draw(st.integers(1, 30))
    elif kind == "descending":
        n = draw(st.integers(2, 30))
        nums = sorted(draw(st.lists(st.integers(-100, 100), min_size=n, max_size=n)), reverse=True)
    elif kind == "ascending":
        n = draw(st.integers(2, 30))
        nums = sorted(draw(st.lists(st.integers(-100, 100), min_size=n, max_size=n)))
    else:
        nums = [draw(st.integers(-100, 100)), draw(st.integers(-100, 100))]
    return {"input": {"nums": nums}}


LIS_PBT_GROUPS = {
    "differential": lis_case_strategy,
    "boundary": lis_boundary_strategy,
}


@st.composite
def subarray_case_strategy(draw):
    nums = draw(st.lists(st.integers(0, 40), max_size=120))
    target = draw(st.integers(1, 500))
    return {"input": {"nums": nums, "target": target}}


@st.composite
def subarray_boundary_strategy(draw):
    kind = draw(st.sampled_from(["empty", "target_exceeds_sum", "single_meets_target", "all_zeros"]))
    if kind == "empty":
        return {"input": {"nums": [], "target": draw(st.integers(1, 100))}}
    elif kind == "target_exceeds_sum":
        nums = draw(st.lists(st.integers(0, 10), min_size=1, max_size=20))
        target = sum(nums) + draw(st.integers(1, 100))
        return {"input": {"nums": nums, "target": target}}
    elif kind == "single_meets_target":
        target = draw(st.integers(1, 50))
        v = draw(st.integers(target, target + 20))
        return {"input": {"nums": [v], "target": target}}
    else:
        nums = [0] * draw(st.integers(1, 20))
        return {"input": {"nums": nums, "target": draw(st.integers(1, 10))}}


SUBARRAY_PBT_GROUPS = {
    "differential": subarray_case_strategy,
    "boundary": subarray_boundary_strategy,
}


@st.composite
def sliding_window_case_strategy(draw):
    nums = draw(st.lists(st.integers(-100, 100), max_size=120))
    k = draw(st.integers(0, len(nums) + 3))
    return {"input": {"nums": nums, "k": k}}


@st.composite
def sliding_window_boundary_strategy(draw):
    kind = draw(st.sampled_from(["empty", "k_zero", "k_exceeds_len", "single", "all_same"]))
    if kind == "empty":
        return {"input": {"nums": [], "k": draw(st.integers(0, 5))}}
    elif kind == "k_zero":
        nums = draw(st.lists(st.integers(-100, 100), min_size=1, max_size=20))
        return {"input": {"nums": nums, "k": 0}}
    elif kind == "k_exceeds_len":
        nums = draw(st.lists(st.integers(-100, 100), min_size=1, max_size=20))
        return {"input": {"nums": nums, "k": len(nums) + draw(st.integers(1, 10))}}
    elif kind == "single":
        return {"input": {"nums": [draw(st.integers(-100, 100))], "k": 1}}
    else:
        v = draw(st.integers(-100, 100))
        n = draw(st.integers(1, 20))
        k = draw(st.integers(1, n))
        return {"input": {"nums": [v] * n, "k": k}}


SLIDING_WINDOW_PBT_GROUPS = {
    "differential": sliding_window_case_strategy,
    "boundary": sliding_window_boundary_strategy,
}


@st.composite
def fenwick_case_strategy(draw):
    n = draw(st.integers(1, 80))
    operations = []
    count = draw(st.integers(1, 120))
    for _ in range(count):
        op = draw(st.sampled_from(["add", "sum"]))
        if op == "add":
            operations.append(("add", draw(st.integers(0, n - 1)), draw(st.integers(-100, 100))))
        else:
            left = draw(st.integers(0, n - 1))
            right = draw(st.integers(left, n))
            operations.append(("sum", left, right))
    return {"input": {"n": n, "operations": operations}}


@st.composite
def fenwick_boundary_strategy(draw):
    kind = draw(st.sampled_from(["no_ops", "only_sums", "single_add_full_query", "n_one"]))
    if kind == "no_ops":
        return {"input": {"n": draw(st.integers(1, 20)), "operations": []}}
    elif kind == "only_sums":
        n = draw(st.integers(1, 20))
        ops = [("sum", 0, n) for _ in range(draw(st.integers(1, 10)))]
        return {"input": {"n": n, "operations": ops}}
    elif kind == "single_add_full_query":
        n = draw(st.integers(1, 20))
        idx = draw(st.integers(0, n - 1))
        val = draw(st.integers(-100, 100))
        return {"input": {"n": n, "operations": [("add", idx, val), ("sum", 0, n)]}}
    else:
        val = draw(st.integers(-100, 100))
        return {"input": {"n": 1, "operations": [("add", 0, val), ("sum", 0, 1)]}}


FENWICK_PBT_GROUPS = {
    "differential": fenwick_case_strategy,
    "boundary": fenwick_boundary_strategy,
}


@st.composite
def heap_scheduling_case_strategy(draw):
    tasks = draw(
        st.lists(
            st.tuples(st.integers(0, 100), st.integers(1, 40)),
            max_size=100,
        )
    )
    return {"input": {"tasks": tasks}}


@st.composite
def heap_scheduling_boundary_strategy(draw):
    kind = draw(st.sampled_from(["empty", "single", "all_same_time", "all_profit_one"]))
    if kind == "empty":
        return {"input": {"tasks": []}}
    elif kind == "single":
        return {"input": {"tasks": [(draw(st.integers(0, 100)), draw(st.integers(1, 40)))]}}
    elif kind == "all_same_time":
        t = draw(st.integers(0, 50))
        tasks = [(t, draw(st.integers(1, 40))) for _ in range(draw(st.integers(1, 15)))]
        return {"input": {"tasks": tasks}}
    else:
        tasks = [(draw(st.integers(0, 100)), 1) for _ in range(draw(st.integers(1, 20)))]
        return {"input": {"tasks": tasks}}


HEAP_SCHEDULING_PBT_GROUPS = {
    "differential": heap_scheduling_case_strategy,
    "boundary": heap_scheduling_boundary_strategy,
}
