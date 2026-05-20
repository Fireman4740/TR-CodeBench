from oracles import trcb_proto_0023 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"n": 4, "edges": [(0, 1, 10), (0, 2, 6), (0, 3, 5), (1, 3, 15), (2, 3, 4)]}, "expected": 19},
    {"input": {"n": 1, "edges": []}, "expected": 0},
    {"input": {"n": 3, "edges": [(0, 1, 1)]}, "expected": -1},
    {"input": {"n": 3, "edges": [(0, 1, 2), (1, 2, 3), (0, 2, 4)]}, "expected": 5},
    {"input": {"n": 2, "edges": [(0, 1, 7), (0, 1, 3)]}, "expected": 3},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["n", "edges"])
