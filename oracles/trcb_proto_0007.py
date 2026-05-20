from collections import deque


def solve(nums: list[int], k: int) -> list[int]:
    if k <= 0 or k > len(nums):
        return []

    window: deque[int] = deque()
    answer: list[int] = []
    for index, value in enumerate(nums):
        while window and window[0] <= index - k:
            window.popleft()
        while window and nums[window[-1]] <= value:
            window.pop()
        window.append(index)
        if index >= k - 1:
            answer.append(nums[window[0]])
    return answer
