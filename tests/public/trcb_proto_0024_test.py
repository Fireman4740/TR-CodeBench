from oracles import trcb_proto_0024 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"n": 4, "edges": [(0, 1), (1, 2), (2, 3)]}, "expected": True},
    {"input": {"n": 3, "edges": [(0, 1), (1, 2), (0, 2)]}, "expected": False},
    {"input": {"n": 1, "edges": []}, "expected": True},
    {"input": {"n": 4, "edges": []}, "expected": True},
    {"input": {"n": 5, "edges": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]}, "expected": False},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["n", "edges"])
