def solve(s: str) -> int:
    """Longest repeated substring via binary search on length + rolling hash."""
    if len(s) <= 1:
        return 0

    MOD = (1 << 61) - 1
    BASE = 131

    def has_repeat(length: int) -> bool:
        """Check if any substring of given length appears at least twice."""
        if length == 0:
            return True
        base_pow = pow(BASE, length, MOD)
        h = 0
        for i in range(length):
            h = (h * BASE + ord(s[i])) % MOD
        seen = {h}
        for i in range(1, len(s) - length + 1):
            h = (h * BASE + ord(s[i + length - 1]) - ord(s[i - 1]) * base_pow) % MOD
            if h in seen:
                # Verify to handle hash collisions
                candidate = s[i:i + length]
                for j in range(i):
                    if s[j:j + length] == candidate:
                        return True
                seen.add(h)
            else:
                seen.add(h)
        return False

    lo, hi = 0, len(s) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if has_repeat(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo
