def solve(text: str, pattern: str) -> list[int]:
    if pattern == "":
        return list(range(len(text) + 1))

    prefix = [0] * len(pattern)
    border = 0
    for index in range(1, len(pattern)):
        while border and pattern[index] != pattern[border]:
            border = prefix[border - 1]
        if pattern[index] == pattern[border]:
            border += 1
        prefix[index] = border

    matches: list[int] = []
    border = 0
    for index, char in enumerate(text):
        while border and char != pattern[border]:
            border = prefix[border - 1]
        if char == pattern[border]:
            border += 1
        if border == len(pattern):
            matches.append(index - len(pattern) + 1)
            border = prefix[border - 1]
    return matches
