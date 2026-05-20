from oracles import trcb_proto_0012 as oracle
from tests.public._helpers import assert_public_cases


PUBLIC_CASES = [
    {"input": {"nums": [3], "k": 1}, "expected": 3},
    {"input": {"nums": [3, 2, 1, 5, 6, 4], "k": 2}, "expected": 5},
    {"input": {"nums": [3, 2, 3, 1, 2, 4, 5, 5, 6], "k": 4}, "expected": 4},
    {"input": {"nums": [7, 7, 7, 7], "k": 3}, "expected": 7},
    {"input": {"nums": [-1, -2, -3, -4], "k": 1}, "expected": -1},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["nums", "k"])
