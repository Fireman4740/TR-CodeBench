from collections import deque


def solve(n: int, edges: list[tuple[int, int]]) -> int:
    """Return the number of strongly connected components (Kosaraju's)."""
    adj = [[] for _ in range(n)]
    radj = [[] for _ in range(n)]

    for u, v in edges:
        adj[u].append(v)
        radj[v].append(u)

    # First pass: compute finish order using iterative DFS
    visited = [False] * n
    finish_order = []
    for start in range(n):
        if visited[start]:
            continue
        stack = [(start, 0)]
        visited[start] = True
        while stack:
            node, idx = stack.pop()
            if idx < len(adj[node]):
                stack.append((node, idx + 1))
                neighbor = adj[node][idx]
                if not visited[neighbor]:
                    visited[neighbor] = True
                    stack.append((neighbor, 0))
            else:
                finish_order.append(node)

    # Second pass: DFS on reverse graph in reverse finish order
    visited = [False] * n
    scc_count = 0
    for start in reversed(finish_order):
        if visited[start]:
            continue
        scc_count += 1
        queue = deque([start])
        visited[start] = True
        while queue:
            node = queue.popleft()
            for neighbor in radj[node]:
                if not visited[neighbor]:
                    visited[neighbor] = True
                    queue.append(neighbor)

    return scc_count
