from collections import deque


def solve(n: int, edges: list[tuple[int, int]]) -> list[int]:
    """Return a valid topological ordering, or empty list if cycle exists."""
    adj = [[] for _ in range(n)]
    indegree = [0] * n

    for u, v in edges:
        adj[u].append(v)
        indegree[v] += 1

    queue = deque(v for v in range(n) if indegree[v] == 0)
    order = []

    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in adj[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != n:
        return []
    return order
