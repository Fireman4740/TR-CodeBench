def solve(n: int, operations: list[tuple[str, int, int]]) -> list[int]:
    tree = [0] * (n + 1)

    def add(index: int, delta: int) -> None:
        index += 1
        while index <= n:
            tree[index] += delta
            index += index & -index

    def prefix_sum(index: int) -> int:
        total = 0
        while index > 0:
            total += tree[index]
            index -= index & -index
        return total

    answer: list[int] = []
    for operation, left, right in operations:
        if operation == "add":
            add(left, right)
        elif operation == "sum":
            answer.append(prefix_sum(right) - prefix_sum(left))
        else:
            raise ValueError(f"unknown operation {operation!r}")
    return answer
