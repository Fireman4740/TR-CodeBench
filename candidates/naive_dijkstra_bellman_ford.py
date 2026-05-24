"""Naive O(V*E) Bellman-Ford solution for shortest path — should be REJECTED by complexity check."""


def solve(n: int, edges: list[tuple[int, int, int]], source: int, target: int) -> int:
    INF = float("inf")
    dist = [INF] * n
    dist[source] = 0

    for _ in range(n - 1):
        for u, v, w in edges:
            if dist[u] != INF and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w

    return -1 if dist[target] == INF else int(dist[target])
