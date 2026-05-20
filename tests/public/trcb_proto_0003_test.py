from oracles import trcb_proto_0003 as oracle
from tests.public._helpers import assert_public_cases


PUBLIC_CASES = [
    {"input": {"intervals": []}, "expected": 0},
    {"input": {"intervals": [(0, 3), (1, 2), (2, 4), (4, 7)]}, "expected": 3},
    {"input": {"intervals": [(1, 5), (2, 6), (3, 7)]}, "expected": 1},
    {"input": {"intervals": [(0, 1), (1, 2), (2, 3)]}, "expected": 3},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["intervals"])
