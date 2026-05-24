from __future__ import annotations

from hypothesis import strategies as st


@st.composite
def interval_scheduling_case_strategy(draw):
    intervals = []
    count = draw(st.integers(0, 100))
    for _ in range(count):
        start = draw(st.integers(-50, 150))
        length = draw(st.integers(1, 40))
        intervals.append((start, start + length))
    return {"input": {"intervals": intervals}}


@st.composite
def interval_scheduling_boundary_strategy(draw):
    kind = draw(st.sampled_from(["empty", "single", "no_overlap", "all_overlap_same_point", "two_equal"]))
    if kind == "empty":
        return {"input": {"intervals": []}}
    elif kind == "single":
        s = draw(st.integers(-50, 150))
        return {"input": {"intervals": [(s, s + draw(st.integers(1, 40)))]}}
    elif kind == "no_overlap":
        n = draw(st.integers(2, 10))
        intervals = [(i * 10, i * 10 + 5) for i in range(n)]
        return {"input": {"intervals": intervals}}
    elif kind == "all_overlap_same_point":
        n = draw(st.integers(2, 8))
        intervals = [(0, draw(st.integers(5, 20))) for _ in range(n)]
        return {"input": {"intervals": intervals}}
    else:
        s = draw(st.integers(-50, 150))
        e = s + draw(st.integers(1, 40))
        return {"input": {"intervals": [(s, e), (s, e)]}}


INTERVAL_SCHEDULING_PBT_GROUPS = {
    "differential": interval_scheduling_case_strategy,
    "boundary": interval_scheduling_boundary_strategy,
}
