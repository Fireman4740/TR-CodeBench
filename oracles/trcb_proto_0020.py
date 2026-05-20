def solve(weights: list[int], values: list[int], capacity: int) -> int:
    """Maximum value achievable without exceeding capacity (0/1 selection)."""
    n = len(weights)
    dp = [0] * (capacity + 1)

    for i in range(n):
        for w in range(capacity, weights[i] - 1, -1):
            if dp[w - weights[i]] + values[i] > dp[w]:
                dp[w] = dp[w - weights[i]] + values[i]

    return dp[capacity]
