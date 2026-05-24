from oracles import trcb_proto_0019 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"nums": []}, "expected": 0},
    {"input": {"nums": [-1]}, "expected": -1},
    {"input": {"nums": [-2, 1, -3, 4, -1, 2, 1, -5, 4]}, "expected": 6},
    {"input": {"nums": [5, 4, -1, 7, 8]}, "expected": 23},
    {"input": {"nums": [-3, -2, -1]}, "expected": -1},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["nums"])
