from oracles import trcb_proto_0038 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"perm": [1, 2, 3]}, "expected": 1},
    {"input": {"perm": [3, 2, 1]}, "expected": 6},
    {"input": {"perm": [1]}, "expected": 1},
    {"input": {"perm": [2, 1, 3]}, "expected": 3},
    {"input": {"perm": [1, 2, 4, 3]}, "expected": 2},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["perm"])
