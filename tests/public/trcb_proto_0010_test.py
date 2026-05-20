from oracles import trcb_proto_0010 as oracle
from tests.public._helpers import assert_public_cases


PUBLIC_CASES = [
    {"input": {"tasks": [(1, 2), (2, 4), (3, 2), (4, 1)]}, "expected": [0, 2, 3, 1]},
    {"input": {"tasks": [(7, 10), (7, 12), (7, 5)]}, "expected": [2, 0, 1]},
    {"input": {"tasks": []}, "expected": []},
    {"input": {"tasks": [(5, 2), (0, 3), (1, 9), (6, 1)]}, "expected": [1, 2, 3, 0]},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["tasks"])
