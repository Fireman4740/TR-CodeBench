def solve(n: int, edges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Find all bridges using Tarjan's DFS with discovery/low values."""
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    disc = [-1] * n
    low = [-1] * n
    bridges = []
    timer = 0

    def dfs(node: int, parent: int) -> None:
        nonlocal timer
        disc[node] = low[node] = timer
        timer += 1
        for neighbor in adj[node]:
            if disc[neighbor] == -1:
                dfs(neighbor, node)
                low[node] = min(low[node], low[neighbor])
                if low[neighbor] > disc[node]:
                    bridge = (min(node, neighbor), max(node, neighbor))
                    bridges.append(bridge)
            elif neighbor != parent:
                low[node] = min(low[node], disc[neighbor])

    for v in range(n):
        if disc[v] == -1:
            dfs(v, -1)

    bridges.sort()
    return bridges
