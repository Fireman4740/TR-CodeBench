"""Naive O(n*m) brute-force pattern matching — should be REJECTED by complexity check."""


def solve(text: str, pattern: str) -> list[int]:
    if pattern == "":
        return list(range(len(text) + 1))

    matches: list[int] = []
    n = len(text)
    m = len(pattern)
    for i in range(n - m + 1):
        match = True
        for j in range(m):
            if text[i + j] != pattern[j]:
                match = False
                break
        if match:
            matches.append(i)
    return matches
