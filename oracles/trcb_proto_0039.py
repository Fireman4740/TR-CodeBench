def solve(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Andrew's monotone chain algorithm for convex hull in CCW order."""
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts

    def cross(o: tuple[int, int], a: tuple[int, int], b: tuple[int, int]) -> int:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    # Build lower hull
    lower: list[tuple[int, int]] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    # Build upper hull
    upper: list[tuple[int, int]] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    # Concatenate, removing last point of each half (it's repeated)
    hull = lower[:-1] + upper[:-1]

    # Rotate so bottom-most (then left-most) point is first
    bottom_idx = 0
    for i in range(1, len(hull)):
        if hull[i][1] < hull[bottom_idx][1] or (
            hull[i][1] == hull[bottom_idx][1] and hull[i][0] < hull[bottom_idx][0]
        ):
            bottom_idx = i
    hull = hull[bottom_idx:] + hull[:bottom_idx]

    return hull
