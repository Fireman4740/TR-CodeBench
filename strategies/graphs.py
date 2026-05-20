from __future__ import annotations

from hypothesis import strategies as st


@st.composite
def shortest_path_case_strategy(draw):
    n = draw(st.integers(1, 30))
    edge_count = draw(st.integers(0, min(180, n * max(1, n - 1))))
    edges = []
    for _ in range(edge_count):
        start = draw(st.integers(0, n - 1))
        end = draw(st.integers(0, n - 1))
        weight = draw(st.integers(1, 50))
        if start != end:
            edges.append((start, end, weight))
    source = draw(st.integers(0, n - 1))
    target = draw(st.integers(0, n - 1))
    return {"input": {"n": n, "edges": edges, "source": source, "target": target}}


@st.composite
def shortest_path_boundary_strategy(draw):
    kind = draw(st.sampled_from(["source_equals_target", "no_edges", "direct_edge", "n_one", "no_path"]))
    if kind == "source_equals_target":
        n = draw(st.integers(1, 10))
        s = draw(st.integers(0, n - 1))
        edges = [(draw(st.integers(0, n - 1)), draw(st.integers(0, n - 1)), draw(st.integers(1, 50)))
                 for _ in range(draw(st.integers(0, 5)))]
        return {"input": {"n": n, "edges": edges, "source": s, "target": s}}
    elif kind == "no_edges":
        n = draw(st.integers(2, 10))
        s, t = draw(st.integers(0, n - 1)), draw(st.integers(0, n - 1))
        return {"input": {"n": n, "edges": [], "source": s, "target": t}}
    elif kind == "direct_edge":
        n = draw(st.integers(2, 10))
        s = draw(st.integers(0, n - 1))
        t = draw(st.sampled_from([i for i in range(n) if i != s]))
        w = draw(st.integers(1, 50))
        return {"input": {"n": n, "edges": [(s, t, w)], "source": s, "target": t}}
    elif kind == "n_one":
        return {"input": {"n": 1, "edges": [], "source": 0, "target": 0}}
    else:
        n = draw(st.integers(3, 8))
        s = 0
        t = n - 1
        return {"input": {"n": n, "edges": [(i, i + 1, 1) for i in range(n - 2)], "source": s, "target": t}}


SHORTEST_PATH_PBT_GROUPS = {
    "differential": shortest_path_case_strategy,
    "boundary": shortest_path_boundary_strategy,
}


@st.composite
def union_find_case_strategy(draw):
    n = draw(st.integers(1, 60))
    unions = draw(st.lists(st.tuples(st.integers(0, n - 1), st.integers(0, n - 1)), max_size=120))
    queries = draw(st.lists(st.tuples(st.integers(0, n - 1), st.integers(0, n - 1)), min_size=1, max_size=120))
    return {"input": {"n": n, "unions": unions, "queries": queries}}


@st.composite
def union_find_boundary_strategy(draw):
    kind = draw(st.sampled_from(["no_unions", "n_one", "self_queries", "chain_unions"]))
    if kind == "no_unions":
        n = draw(st.integers(2, 10))
        queries = [(draw(st.integers(0, n - 1)), draw(st.integers(0, n - 1)))
                   for _ in range(draw(st.integers(1, 10)))]
        return {"input": {"n": n, "unions": [], "queries": queries}}
    elif kind == "n_one":
        return {"input": {"n": 1, "unions": [(0, 0)], "queries": [(0, 0)]}}
    elif kind == "self_queries":
        n = draw(st.integers(1, 10))
        queries = [(i, i) for i in range(n)]
        return {"input": {"n": n, "unions": [], "queries": queries}}
    else:
        n = draw(st.integers(3, 10))
        unions = [(i, i + 1) for i in range(n - 1)]
        queries = [(0, n - 1)]
        return {"input": {"n": n, "unions": unions, "queries": queries}}


UNION_FIND_PBT_GROUPS = {
    "differential": union_find_case_strategy,
    "boundary": union_find_boundary_strategy,
}


@st.composite
def dag_longest_path_case_strategy(draw):
    n = draw(st.integers(1, 45))
    edges = []
    for start in range(n):
        for end in range(start + 1, n):
            include = draw(st.booleans())
            if include and draw(st.integers(0, 7)) == 0:
                edges.append((start, end, draw(st.integers(-10, 25))))
    return {"input": {"n": n, "edges": edges}}


@st.composite
def dag_longest_path_boundary_strategy(draw):
    kind = draw(st.sampled_from(["n_one", "no_edges", "linear_chain_positive", "linear_chain_negative"]))
    if kind == "n_one":
        return {"input": {"n": 1, "edges": []}}
    elif kind == "no_edges":
        return {"input": {"n": draw(st.integers(1, 10)), "edges": []}}
    elif kind == "linear_chain_positive":
        n = draw(st.integers(2, 8))
        edges = [(i, i + 1, draw(st.integers(1, 10))) for i in range(n - 1)]
        return {"input": {"n": n, "edges": edges}}
    else:
        n = draw(st.integers(2, 8))
        edges = [(i, i + 1, draw(st.integers(-10, -1))) for i in range(n - 1)]
        return {"input": {"n": n, "edges": edges}}


DAG_LONGEST_PATH_PBT_GROUPS = {
    "differential": dag_longest_path_case_strategy,
    "boundary": dag_longest_path_boundary_strategy,
}
