def solve(words: list[str], queries: list[str]) -> list[int]:
    """Trie with count annotation for O(prefix_len) prefix frequency queries."""
    root = {}

    for word in words:
        node = root
        for ch in word:
            if ch not in node:
                node[ch] = {"_count": 0}
            node[ch]["_count"] += 1
            node = node[ch]

    results = []
    for prefix in queries:
        node = root
        found = True
        for ch in prefix:
            if ch not in node:
                found = False
                break
            node = node[ch]
        if found and prefix:
            results.append(node["_count"])
        elif not prefix:
            results.append(len(words))
        else:
            results.append(0)

    return results
