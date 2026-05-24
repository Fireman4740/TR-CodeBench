from oracles import trcb_proto_0035 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"intervals": [(1, 3), (2, 6), (8, 10), (15, 18)]}, "expected": [(1, 6), (8, 10), (15, 18)]},
    {"input": {"intervals": [(1, 4), (4, 5)]}, "expected": [(1, 5)]},
    {"input": {"intervals": []}, "expected": []},
    {"input": {"intervals": [(5, 10)]}, "expected": [(5, 10)]},
    {"input": {"intervals": [(1, 10), (2, 3), (4, 5), (6, 7)]}, "expected": [(1, 10)]},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["intervals"])
