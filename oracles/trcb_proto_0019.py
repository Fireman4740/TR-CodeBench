def solve(nums: list[int]) -> int:
    """Maximum sum of any contiguous subarray. Returns 0 for empty list."""
    if not nums:
        return 0

    max_sum = nums[0]
    current = nums[0]

    for i in range(1, len(nums)):
        current = max(nums[i], current + nums[i])
        if current > max_sum:
            max_sum = current

    return max_sum
