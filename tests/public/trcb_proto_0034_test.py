from oracles import trcb_proto_0034 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"operations": [("push", 3), ("push", 5), ("get_min",), ("push", 1), ("get_min",), ("pop",), ("get_min",)]}, "expected": [3, 1, 3]},
    {"input": {"operations": [("get_min",)]}, "expected": [None]},
    {"input": {"operations": [("pop",), ("get_min",)]}, "expected": [None]},
    {"input": {"operations": [("push", 2), ("push", 2), ("pop",), ("get_min",)]}, "expected": [2]},
    {"input": {"operations": [("push", 10), ("push", 5), ("push", 7), ("pop",), ("get_min",), ("pop",), ("get_min",)]}, "expected": [5, 10]},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["operations"])
