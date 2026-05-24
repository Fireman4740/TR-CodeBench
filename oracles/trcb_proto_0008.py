from collections import deque


def solve(n: int, edges: list[tuple[int, int, int]]) -> int:
    graph: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    indegree = [0] * n
    for start, end, weight in edges:
        graph[start].append((end, weight))
        indegree[end] += 1

    queue = deque(node for node, degree in enumerate(indegree) if degree == 0)
    best = [0] * n

    while queue:
        node = queue.popleft()
        for neighbor, weight in graph[node]:
            best[neighbor] = max(best[neighbor], best[node] + weight)
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    return max(best, default=0)
