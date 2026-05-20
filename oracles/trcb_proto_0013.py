def solve(nums: list[int]) -> list[int]:
    """Next greater element in circular array using monotonic stack."""
    n = len(nums)
    if n == 0:
        return []
    result = [-1] * n
    stack = []
    for i in range(2 * n - 1, -1, -1):
        idx = i % n
        while stack and stack[-1] <= nums[idx]:
            stack.pop()
        if i < n:
            result[idx] = stack[-1] if stack else -1
        stack.append(nums[idx])
    return result
