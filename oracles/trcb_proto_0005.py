def solve(n: int, unions: list[tuple[int, int]], queries: list[tuple[int, int]]) -> list[bool]:
    parent = list(range(n))
    rank = [0] * n

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(left: int, right: int) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left == root_right:
            return
        if rank[root_left] < rank[root_right]:
            root_left, root_right = root_right, root_left
        parent[root_right] = root_left
        if rank[root_left] == rank[root_right]:
            rank[root_left] += 1

    for left, right in unions:
        union(left, right)

    return [find(left) == find(right) for left, right in queries]
