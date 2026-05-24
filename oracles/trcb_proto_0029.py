def solve(words: list[str]) -> list[list[str]]:
    """Group anagrams using sorted character tuple as dictionary key."""
    groups: dict[str, list[str]] = {}
    for word in words:
        key = "".join(sorted(word))
        if key not in groups:
            groups[key] = []
        groups[key].append(word)
    result = []
    for group in groups.values():
        result.append(sorted(group))
    result.sort(key=lambda g: g[0])
    return result
