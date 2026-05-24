import heapq


def solve(tasks: list[tuple[int, int]]) -> list[int]:
    indexed = sorted((release, duration, index) for index, (release, duration) in enumerate(tasks))
    order: list[int] = []
    heap: list[tuple[int, int]] = []
    time = 0
    cursor = 0

    while cursor < len(indexed) or heap:
        if not heap and cursor < len(indexed) and time < indexed[cursor][0]:
            time = indexed[cursor][0]
        while cursor < len(indexed) and indexed[cursor][0] <= time:
            _, duration, index = indexed[cursor]
            heapq.heappush(heap, (duration, index))
            cursor += 1
        duration, index = heapq.heappop(heap)
        time += duration
        order.append(index)

    return order
