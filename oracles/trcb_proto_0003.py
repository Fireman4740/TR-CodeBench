def solve(intervals: list[tuple[int, int]]) -> int:
    chosen = 0
    current_end: int | None = None
    for start, end in sorted(intervals, key=lambda item: (item[1], item[0])):
        if current_end is None or start >= current_end:
            chosen += 1
            current_end = end
    return chosen
