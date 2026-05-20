from oracles import trcb_proto_0007 as oracle
from tests.public._helpers import assert_public_cases


PUBLIC_CASES = [
    {"input": {"nums": [1, 3, -1, -3, 5, 3, 6, 7], "k": 3}, "expected": [3, 3, 5, 5, 6, 7]},
    {"input": {"nums": [4, 2, 12], "k": 1}, "expected": [4, 2, 12]},
    {"input": {"nums": [4, 2, 12], "k": 4}, "expected": []},
    {"input": {"nums": [], "k": 1}, "expected": []},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["nums", "k"])
