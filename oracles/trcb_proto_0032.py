import math


def solve(arr: list[int], queries: list[tuple[int, int]]) -> list[int]:
    """Sparse table for O(1) range minimum queries after O(n log n) preprocessing."""
    n = len(arr)
    if n == 0:
        return [0] * len(queries)  # shouldn't happen with valid queries

    LOG = max(1, math.floor(math.log2(n)) + 1)
    sparse = [[0] * n for _ in range(LOG)]
    sparse[0] = arr[:]

    for j in range(1, LOG):
        for i in range(n - (1 << j) + 1):
            sparse[j][i] = min(sparse[j - 1][i], sparse[j - 1][i + (1 << (j - 1))])

    results = []
    for l, r in queries:
        length = r - l + 1
        k = math.floor(math.log2(length))
        results.append(min(sparse[k][l], sparse[k][r - (1 << k) + 1]))

    return results
