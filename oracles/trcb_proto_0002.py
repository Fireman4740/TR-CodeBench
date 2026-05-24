import heapq


def solve(n: int, edges: list[tuple[int, int, int]], source: int, target: int) -> int:
    graph: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for start, end, weight in edges:
        graph[start].append((end, weight))

    distances = [float("inf")] * n
    distances[source] = 0
    heap = [(0, source)]

    while heap:
        distance, node = heapq.heappop(heap)
        if node == target:
            return distance
        if distance != distances[node]:
            continue
        for neighbor, weight in graph[node]:
            new_distance = distance + weight
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                heapq.heappush(heap, (new_distance, neighbor))

    return -1
