from oracles import trcb_proto_0013 as oracle
from tests.public._helpers import assert_public_cases


PUBLIC_CASES = [
    {"input": {"nums": []}, "expected": []},
    {"input": {"nums": [5]}, "expected": [-1]},
    {"input": {"nums": [1, 2, 1]}, "expected": [2, -1, 2]},
    {"input": {"nums": [2, 1, 2, 4, 3]}, "expected": [4, 2, 4, -1, 4]},
    {"input": {"nums": [3, 3, 3]}, "expected": [-1, -1, -1]},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["nums"])
