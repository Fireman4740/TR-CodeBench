import random


def solve(nums: list[int], k: int) -> int:
    """Find kth largest using randomized quickselect."""
    arr = nums[:]
    target = len(arr) - k  # convert to 0-based index for kth smallest

    def quickselect(lo, hi):
        if lo == hi:
            return arr[lo]
        pivot_idx = random.randint(lo, hi)
        arr[pivot_idx], arr[hi] = arr[hi], arr[pivot_idx]
        pivot = arr[hi]
        store = lo
        for i in range(lo, hi):
            if arr[i] < pivot:
                arr[store], arr[i] = arr[i], arr[store]
                store += 1
        arr[store], arr[hi] = arr[hi], arr[store]
        if store == target:
            return arr[store]
        elif store < target:
            return quickselect(store + 1, hi)
        else:
            return quickselect(lo, store - 1)

    return quickselect(0, len(arr) - 1)
