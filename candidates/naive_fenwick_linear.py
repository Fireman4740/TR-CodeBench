"""Naive O(n) per query array solution for point update + range sum — should be REJECTED by complexity check."""


def solve(n: int, operations: list[tuple[str, int, int]]) -> list[int]:
    arr = [0] * n
    answer: list[int] = []

    for operation, left, right in operations:
        if operation == "add":
            arr[left] += right
        elif operation == "sum":
            answer.append(sum(arr[left:right]))
        else:
            raise ValueError(f"unknown operation {operation!r}")
    return answer
