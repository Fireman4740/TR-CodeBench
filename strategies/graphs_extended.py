from __future__ import annotations

from hypothesis import strategies as st


# ---------- trcb-proto-0021: Topological Sort ----------

@st.composite
def toposort_case_strategy(draw):
    n = draw(st.integers(1, 50))
    edges = []
    for u in range(n):
        for v in range(u + 1, n):
            if draw(st.integers(0, 5)) == 0:
                edges.append((u, v))
    return {"input": {"n": n, "edges": edges}}


@st.composite
def toposort_boundary_strategy(draw):
    kind = draw(st.sampled_from([
        "single_node", "no_edges", "linear_chain", "has_cycle", "diamond"
    ]))
    if kind == "single_node":
        return {"input": {"n": 1, "edges": []}}
    elif kind == "no_edges":
        n = draw(st.integers(2, 10))
        return {"input": {"n": n, "edges": []}}
    elif kind == "linear_chain":
        n = draw(st.integers(2, 10))
        edges = [(i, i + 1) for i in range(n - 1)]
        return {"input": {"n": n, "edges": edges}}
    elif kind == "has_cycle":
        n = draw(st.integers(3, 8))
        edges = [(i, (i + 1) % n) for i in range(n)]
        return {"input": {"n": n, "edges": edges}}
    else:
        n = 4
        edges = [(0, 1), (0, 2), (1, 3), (2, 3)]
        return {"input": {"n": n, "edges": edges}}


TOPOSORT_PBT_GROUPS = {
    "differential": toposort_case_strategy,
    "boundary": toposort_boundary_strategy,
}


# ---------- trcb-proto-0022: Strongly Connected Components ----------

@st.composite
def scc_case_strategy(draw):
    n = draw(st.integers(1, 40))
    edge_count = draw(st.integers(0, min(200, n * n)))
    edges = []
    for _ in range(edge_count):
        u = draw(st.integers(0, n - 1))
        v = draw(st.integers(0, n - 1))
        if u != v:
            edges.append((u, v))
    return {"input": {"n": n, "edges": edges}}


@st.composite
def scc_boundary_strategy(draw):
    kind = draw(st.sampled_from([
        "single_node", "no_edges", "full_cycle", "two_sccs", "self_loops_only"
    ]))
    if kind == "single_node":
        return {"input": {"n": 1, "edges": []}}
    elif kind == "no_edges":
        n = draw(st.integers(2, 10))
        return {"input": {"n": n, "edges": []}}
    elif kind == "full_cycle":
        n = draw(st.integers(2, 8))
        edges = [(i, (i + 1) % n) for i in range(n)]
        return {"input": {"n": n, "edges": edges}}
    elif kind == "two_sccs":
        n = draw(st.integers(4, 8))
        mid = n // 2
        edges = [(i, (i + 1) % mid) for i in range(mid)]
        edges += [(i, mid + ((i - mid + 1) % (n - mid))) for i in range(mid, n)]
        return {"input": {"n": n, "edges": edges}}
    else:
        n = draw(st.integers(2, 6))
        return {"input": {"n": n, "edges": []}}


SCC_PBT_GROUPS = {
    "differential": scc_case_strategy,
    "boundary": scc_boundary_strategy,
}


# ---------- trcb-proto-0023: Minimum Spanning Tree ----------

@st.composite
def mst_case_strategy(draw):
    n = draw(st.integers(1, 40))
    edge_count = draw(st.integers(0, min(150, n * (n - 1) // 2)))
    edges = []
    for _ in range(edge_count):
        u = draw(st.integers(0, n - 1))
        v = draw(st.integers(0, n - 1))
        w = draw(st.integers(1, 100))
        if u != v:
            edges.append((u, v, w))
    return {"input": {"n": n, "edges": edges}}


@st.composite
def mst_boundary_strategy(draw):
    kind = draw(st.sampled_from([
        "single_node", "disconnected", "complete_small", "linear_chain", "duplicate_edges"
    ]))
    if kind == "single_node":
        return {"input": {"n": 1, "edges": []}}
    elif kind == "disconnected":
        n = draw(st.integers(3, 8))
        edges = [(0, 1, draw(st.integers(1, 10)))]
        return {"input": {"n": n, "edges": edges}}
    elif kind == "complete_small":
        n = draw(st.integers(3, 5))
        edges = []
        for u in range(n):
            for v in range(u + 1, n):
                edges.append((u, v, draw(st.integers(1, 20))))
        return {"input": {"n": n, "edges": edges}}
    elif kind == "linear_chain":
        n = draw(st.integers(2, 8))
        edges = [(i, i + 1, draw(st.integers(1, 10))) for i in range(n - 1)]
        return {"input": {"n": n, "edges": edges}}
    else:
        n = draw(st.integers(2, 5))
        w1 = draw(st.integers(1, 10))
        w2 = draw(st.integers(1, 10))
        edges = [(0, 1, w1), (0, 1, w2)]
        return {"input": {"n": n, "edges": edges}}


MST_PBT_GROUPS = {
    "differential": mst_case_strategy,
    "boundary": mst_boundary_strategy,
}


# ---------- trcb-proto-0024: Bipartite Check ----------

@st.composite
def bipartite_case_strategy(draw):
    n = draw(st.integers(1, 40))
    edge_count = draw(st.integers(0, min(120, n * (n - 1) // 2)))
    edges = []
    for _ in range(edge_count):
        u = draw(st.integers(0, n - 1))
        v = draw(st.integers(0, n - 1))
        if u != v:
            edges.append((u, v))
    return {"input": {"n": n, "edges": edges}}


@st.composite
def bipartite_boundary_strategy(draw):
    kind = draw(st.sampled_from([
        "single_node", "no_edges", "triangle", "even_cycle", "odd_cycle"
    ]))
    if kind == "single_node":
        return {"input": {"n": 1, "edges": []}}
    elif kind == "no_edges":
        n = draw(st.integers(2, 10))
        return {"input": {"n": n, "edges": []}}
    elif kind == "triangle":
        return {"input": {"n": 3, "edges": [(0, 1), (1, 2), (0, 2)]}}
    elif kind == "even_cycle":
        n = draw(st.sampled_from([4, 6, 8]))
        edges = [(i, (i + 1) % n) for i in range(n)]
        return {"input": {"n": n, "edges": edges}}
    else:
        n = draw(st.sampled_from([3, 5, 7]))
        edges = [(i, (i + 1) % n) for i in range(n)]
        return {"input": {"n": n, "edges": edges}}


BIPARTITE_PBT_GROUPS = {
    "differential": bipartite_case_strategy,
    "boundary": bipartite_boundary_strategy,
}


# ---------- trcb-proto-0025: Bridges in Graph ----------

@st.composite
def bridges_case_strategy(draw):
    n = draw(st.integers(2, 35))
    edge_count = draw(st.integers(n - 1, min(120, n * (n - 1) // 2)))
    edges = []
    # Ensure connected: build a spanning tree first
    perm = draw(st.permutations(list(range(n))))
    for i in range(n - 1):
        edges.append((perm[i], perm[i + 1]))
    # Add random extra edges
    for _ in range(edge_count - (n - 1)):
        u = draw(st.integers(0, n - 1))
        v = draw(st.integers(0, n - 1))
        if u != v:
            edges.append((u, v))
    return {"input": {"n": n, "edges": edges}}


@st.composite
def bridges_boundary_strategy(draw):
    kind = draw(st.sampled_from([
        "single_edge", "linear_chain", "cycle_no_bridges", "star_graph", "two_nodes"
    ]))
    if kind == "single_edge":
        return {"input": {"n": 2, "edges": [(0, 1)]}}
    elif kind == "linear_chain":
        n = draw(st.integers(3, 8))
        edges = [(i, i + 1) for i in range(n - 1)]
        return {"input": {"n": n, "edges": edges}}
    elif kind == "cycle_no_bridges":
        n = draw(st.integers(3, 8))
        edges = [(i, (i + 1) % n) for i in range(n)]
        return {"input": {"n": n, "edges": edges}}
    elif kind == "star_graph":
        n = draw(st.integers(3, 8))
        edges = [(0, i) for i in range(1, n)]
        return {"input": {"n": n, "edges": edges}}
    else:
        return {"input": {"n": 2, "edges": [(0, 1)]}}


BRIDGES_PBT_GROUPS = {
    "differential": bridges_case_strategy,
    "boundary": bridges_boundary_strategy,
}
