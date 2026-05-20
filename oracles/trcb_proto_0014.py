import heapq


def solve(stream: list[int]) -> list[int]:
    """Running median using two heaps."""
    max_heap = []  # lower half (negated for max-heap behavior)
    min_heap = []  # upper half
    medians = []

    for num in stream:
        # Insert into appropriate heap
        if not max_heap or num <= -max_heap[0]:
            heapq.heappush(max_heap, -num)
        else:
            heapq.heappush(min_heap, num)

        # Balance heaps: max_heap can have at most 1 more element
        if len(max_heap) > len(min_heap) + 1:
            heapq.heappush(min_heap, -heapq.heappop(max_heap))
        elif len(min_heap) > len(max_heap):
            heapq.heappush(max_heap, -heapq.heappop(min_heap))

        # Median is always top of max_heap (lower of two middles if even)
        medians.append(-max_heap[0])

    return medians
