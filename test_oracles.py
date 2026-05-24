import sys
sys.path.insert(0, '.')

# Test 0016 - Edit Distance
from oracles import trcb_proto_0016
cases_16 = [
    (("", ""), 0),
    (("", "abc"), 3),
    (("horse", "ros"), 3),
    (("intention", "execution"), 5),
    (("abc", "abc"), 0),
]
for args, expected in cases_16:
    result = trcb_proto_0016.solve(*args)
    assert result == expected, f"0016 FAIL: solve{args} = {result}, expected {expected}"
print("0016 OK")

# Test 0017 - Coin Change
from oracles import trcb_proto_0017
cases_17 = [
    (([1, 2, 5], 0), 0),
    (([1, 2, 5], 11), 3),
    (([2], 3), -1),
    (([1], 1), 1),
    (([3, 7], 14), 2),
]
for args, expected in cases_17:
    result = trcb_proto_0017.solve(*args)
    assert result == expected, f"0017 FAIL: solve{args} = {result}, expected {expected}"
print("0017 OK")

# Test 0018 - LCS
from oracles import trcb_proto_0018
cases_18 = [
    (("", "abc"), 0),
    (("abcde", "ace"), 3),
    (("abc", "def"), 0),
    (("abcba", "abcbcba"), 5),
    (("a", "a"), 1),
]
for args, expected in cases_18:
    result = trcb_proto_0018.solve(*args)
    assert result == expected, f"0018 FAIL: solve{args} = {result}, expected {expected}"
print("0018 OK")

# Test 0019 - Max Subarray
from oracles import trcb_proto_0019
cases_19 = [
    (([], ), 0),
    (([-1], ), -1),
    (([-2, 1, -3, 4, -1, 2, 1, -5, 4], ), 6),
    (([5, 4, -1, 7, 8], ), 23),
    (([-3, -2, -1], ), -1),
]
for args, expected in cases_19:
    result = trcb_proto_0019.solve(*args)
    assert result == expected, f"0019 FAIL: solve{args} = {result}, expected {expected}"
print("0019 OK")

# Test 0020 - Knapsack
from oracles import trcb_proto_0020
cases_20 = [
    (([], [], 10), 0),
    (([5], [10], 4), 0),
    (([1, 2, 3], [6, 10, 12], 5), 22),
    (([2, 3, 4, 5], [3, 4, 5, 6], 9), 12),
    (([1, 1, 1], [1, 1, 1], 2), 2),
]
for args, expected in cases_20:
    result = trcb_proto_0020.solve(*args)
    assert result == expected, f"0020 FAIL: solve{args} = {result}, expected {expected}"
print("0020 OK")

print("\nALL TESTS PASSED")
