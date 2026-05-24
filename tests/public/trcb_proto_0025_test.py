from oracles import trcb_proto_0025 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"n": 4, "edges": [(0, 1), (1, 2), (2, 3)]}, "expected": [(0, 1), (1, 2), (2, 3)]},
    {"input": {"n": 4, "edges": [(0, 1), (1, 2), (2, 0), (1, 3)]}, "expected": [(1, 3)]},
    {"input": {"n": 2, "edges": [(0, 1)]}, "expected": [(0, 1)]},
    {"input": {"n": 3, "edges": [(0, 1), (1, 2), (0, 2)]}, "expected": []},
    {"input": {"n": 5, "edges": [(0, 1), (1, 2), (2, 0), (1, 3), (3, 4), (4, 1)]}, "expected": []},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["n", "edges"])
