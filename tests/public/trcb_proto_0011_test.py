from oracles import trcb_proto_0011 as oracle
from tests.public._helpers import assert_public_cases


PUBLIC_CASES = [
    {"input": {"nums": []}, "expected": 0},
    {"input": {"nums": [1]}, "expected": 0},
    {"input": {"nums": [2, 4, 1, 3, 5]}, "expected": 3},
    {"input": {"nums": [5, 4, 3, 2, 1]}, "expected": 10},
    {"input": {"nums": [1, 2, 3, 4, 5]}, "expected": 0},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["nums"])
