from bisect import bisect_left


def solve(nums: list[int]) -> int:
    tails: list[int] = []
    for value in nums:
        index = bisect_left(tails, value)
        if index == len(tails):
            tails.append(value)
        else:
            tails[index] = value
    return len(tails)
