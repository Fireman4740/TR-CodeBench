def solve(n: int, edges: list[tuple[int, int, int]]) -> int:
    """Return total weight of MST, or -1 if graph is not connected (Kruskal's)."""
    if n == 0:
        return 0

    parent = list(range(n))
    rank = [0] * n

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> bool:
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        if rank[ra] < rank[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1
        return True

    sorted_edges = sorted(edges, key=lambda e: e[2])
    total_weight = 0
    edges_used = 0

    for u, v, w in sorted_edges:
        if union(u, v):
            total_weight += w
            edges_used += 1
            if edges_used == n - 1:
                break

    if edges_used != n - 1:
        return -1
    return total_weight
