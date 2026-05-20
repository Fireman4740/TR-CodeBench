def solve(perm: list[int]) -> int:
    """Factorial number system with Fenwick tree for 1-based lexicographic rank."""
    n = len(perm)
    if n == 0:
        return 1

    # Precompute factorials
    fact = [1] * (n + 1)
    for i in range(1, n + 1):
        fact[i] = fact[i - 1] * i

    # Fenwick tree to count elements already placed
    tree = [0] * (n + 1)

    def update(idx: int) -> None:
        while idx <= n:
            tree[idx] += 1
            idx += idx & (-idx)

    def query(idx: int) -> int:
        s = 0
        while idx > 0:
            s += tree[idx]
            idx -= idx & (-idx)
        return s

    rank = 0
    for i in range(n):
        # Count how many elements smaller than perm[i] have NOT been used
        smaller_used = query(perm[i] - 1)
        smaller_available = (perm[i] - 1) - smaller_used
        rank += smaller_available * fact[n - 1 - i]
        update(perm[i])

    return rank + 1
