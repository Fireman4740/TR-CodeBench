def solve(operations: list[tuple]) -> list[int | None]:
    """Min stack with auxiliary stack tracking minimums for O(1) get_min."""
    stack = []
    min_stack = []
    results = []

    for op in operations:
        if op[0] == "push":
            x = op[1]
            stack.append(x)
            if not min_stack or x <= min_stack[-1]:
                min_stack.append(x)
            else:
                min_stack.append(min_stack[-1])
        elif op[0] == "pop":
            if stack:
                stack.pop()
                min_stack.pop()
        elif op[0] == "get_min":
            if stack:
                results.append(min_stack[-1])
            else:
                results.append(None)

    return results
