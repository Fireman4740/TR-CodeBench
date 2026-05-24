def solve(text: str, patterns: list[str]) -> list[int]:
    """Multi-pattern search using rolling hash with set lookup."""
    if not patterns or not text:
        return []
    m = len(patterns[0])
    if m == 0 or m > len(text):
        return []
    # Validate all patterns have same length
    for p in patterns:
        if len(p) != m:
            return []

    MOD = (1 << 61) - 1
    BASE = 131

    def poly_hash(s: str) -> int:
        h = 0
        for ch in s:
            h = (h * BASE + ord(ch)) % MOD
        return h

    # Precompute BASE^m mod MOD
    base_pow = pow(BASE, m, MOD)

    # Hash all patterns into a set
    pattern_set = set()
    for p in patterns:
        pattern_set.add(poly_hash(p))

    # Also keep original patterns for collision verification
    pattern_str_set = set(patterns)

    # Rolling hash over text
    result = []
    h = poly_hash(text[:m])
    if h in pattern_set and text[:m] in pattern_str_set:
        result.append(0)

    for i in range(1, len(text) - m + 1):
        h = (h * BASE + ord(text[i + m - 1]) - ord(text[i - 1]) * base_pow) % MOD
        if h in pattern_set and text[i:i + m] in pattern_str_set:
            result.append(i)

    return result
