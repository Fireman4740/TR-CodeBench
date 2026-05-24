from oracles import trcb_proto_0032 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"arr": [1, 3, 2, 7, 9, 11], "queries": [(0, 2)]}, "expected": [1]},
    {"input": {"arr": [5, 2, 4, 3, 1], "queries": [(1, 3), (0, 4)]}, "expected": [2, 1]},
    {"input": {"arr": [10], "queries": [(0, 0)]}, "expected": [10]},
    {"input": {"arr": [7, 7, 7, 7], "queries": [(0, 3), (1, 2)]}, "expected": [7, 7]},
    {"input": {"arr": [5, 1, 4, 2, 8], "queries": [(0, 0), (2, 4), (0, 4)]}, "expected": [5, 2, 1]},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["arr", "queries"])
