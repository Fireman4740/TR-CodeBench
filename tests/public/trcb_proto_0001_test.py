from oracles import trcb_proto_0001 as oracle
from tests.public._helpers import assert_public_cases


PUBLIC_CASES = [
    {"input": {"nums": []}, "expected": 0},
    {"input": {"nums": [10, 9, 2, 5, 3, 7, 101, 18]}, "expected": 4},
    {"input": {"nums": [2, 2, 2]}, "expected": 1},
    {"input": {"nums": [-1, 3, 4, -2, 0, 6, 2, 3]}, "expected": 4},
    {"input": {"nums": [1, 2, 3, 4]}, "expected": 4},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["nums"])
