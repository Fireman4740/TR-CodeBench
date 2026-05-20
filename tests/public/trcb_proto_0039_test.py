from oracles import trcb_proto_0039 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"points": [(0, 0), (1, 1), (2, 0), (1, -1)]}, "expected": [(1, -1), (2, 0), (1, 1), (0, 0)]},
    {"input": {"points": [(0, 0), (1, 0), (0, 1)]}, "expected": [(0, 0), (1, 0), (0, 1)]},
    {"input": {"points": [(0, 0), (1, 0)]}, "expected": [(0, 0), (1, 0)]},
    {"input": {"points": [(0, 0)]}, "expected": [(0, 0)]},
    {"input": {"points": [(0, 0), (1, 0), (2, 0), (0, 1), (2, 1)]}, "expected": [(0, 0), (2, 0), (2, 1), (0, 1)]},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["points"])
