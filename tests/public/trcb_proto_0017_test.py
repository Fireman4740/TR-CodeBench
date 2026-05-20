from oracles import trcb_proto_0017 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"coins": [1, 2, 5], "amount": 0}, "expected": 0},
    {"input": {"coins": [1, 2, 5], "amount": 11}, "expected": 3},
    {"input": {"coins": [2], "amount": 3}, "expected": -1},
    {"input": {"coins": [1], "amount": 1}, "expected": 1},
    {"input": {"coins": [3, 7], "amount": 14}, "expected": 2},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["coins", "amount"])
