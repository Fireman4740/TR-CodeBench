def solve(nums: list[int], target: int) -> int:
    if target <= 0:
        return 0

    best = len(nums) + 1
    left = 0
    current_sum = 0
    for right, value in enumerate(nums):
        current_sum += value
        while current_sum >= target:
            best = min(best, right - left + 1)
            current_sum -= nums[left]
            left += 1
    return 0 if best == len(nums) + 1 else best
