from oracles import trcb_proto_0026 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"s": ""}, "expected": 0},
    {"input": {"s": "a"}, "expected": 1},
    {"input": {"s": "babad"}, "expected": 3},
    {"input": {"s": "cbbd"}, "expected": 2},
    {"input": {"s": "abacdfgdcaba"}, "expected": 3},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["s"])
