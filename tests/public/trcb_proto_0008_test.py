from oracles import trcb_proto_0008 as oracle
from tests.public._helpers import assert_public_cases


PUBLIC_CASES = [
    {"input": {"n": 4, "edges": [(0, 1, 3), (0, 2, 2), (1, 3, 4), (2, 3, 10)]}, "expected": 12},
    {"input": {"n": 3, "edges": []}, "expected": 0},
    {"input": {"n": 5, "edges": [(0, 1, -5), (1, 2, 8), (3, 4, 2)]}, "expected": 8},
    {"input": {"n": 4, "edges": [(0, 1, 1), (1, 2, 1), (0, 2, 5), (2, 3, 1)]}, "expected": 6},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["n", "edges"])
