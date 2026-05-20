from oracles import trcb_proto_0020 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"weights": [], "values": [], "capacity": 10}, "expected": 0},
    {"input": {"weights": [5], "values": [10], "capacity": 4}, "expected": 0},
    {"input": {"weights": [1, 2, 3], "values": [6, 10, 12], "capacity": 5}, "expected": 22},
    {"input": {"weights": [2, 3, 4, 5], "values": [3, 4, 5, 6], "capacity": 9}, "expected": 12},
    {"input": {"weights": [1, 1, 1], "values": [1, 1, 1], "capacity": 2}, "expected": 2},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["weights", "values", "capacity"])
