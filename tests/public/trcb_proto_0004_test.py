from oracles import trcb_proto_0004 as oracle
from tests.public._helpers import assert_public_cases


PUBLIC_CASES = [
    {"input": {"nums": [2, 3, 1, 2, 4, 3], "target": 7}, "expected": 2},
    {"input": {"nums": [1, 1, 1, 1], "target": 5}, "expected": 0},
    {"input": {"nums": [5], "target": 5}, "expected": 1},
    {"input": {"nums": [0, 0, 4, 0, 2], "target": 6}, "expected": 3},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["nums", "target"])
