from oracles import trcb_proto_0031 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"capacity": 2, "operations": [("put", 1, 1), ("put", 2, 2), ("get", 1), ("put", 3, 3), ("get", 2), ("get", 3)]}, "expected": [1, -1, 3]},
    {"input": {"capacity": 1, "operations": [("put", 1, 10), ("put", 2, 20), ("get", 1), ("get", 2)]}, "expected": [-1, 20]},
    {"input": {"capacity": 2, "operations": [("get", 5)]}, "expected": [-1]},
    {"input": {"capacity": 3, "operations": [("put", 1, 1), ("put", 1, 10), ("get", 1)]}, "expected": [10]},
    {"input": {"capacity": 2, "operations": [("put", 1, 1), ("put", 2, 2), ("get", 1), ("put", 3, 3), ("get", 1), ("get", 2)]}, "expected": [1, 1, -1]},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["capacity", "operations"])
