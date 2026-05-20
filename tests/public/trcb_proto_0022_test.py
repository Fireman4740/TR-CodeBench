from oracles import trcb_proto_0022 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"n": 5, "edges": [(0, 1), (1, 2), (2, 0), (3, 4)]}, "expected": 3},
    {"input": {"n": 1, "edges": []}, "expected": 1},
    {"input": {"n": 4, "edges": [(0, 1), (1, 2), (2, 3), (3, 0)]}, "expected": 1},
    {"input": {"n": 3, "edges": []}, "expected": 3},
    {"input": {"n": 4, "edges": [(0, 1), (1, 0), (2, 3), (3, 2)]}, "expected": 2},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["n", "edges"])
