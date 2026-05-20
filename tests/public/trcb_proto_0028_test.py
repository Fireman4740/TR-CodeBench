from oracles import trcb_proto_0028 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"s": ""}, "expected": 0},
    {"input": {"s": "a"}, "expected": 0},
    {"input": {"s": "abcabc"}, "expected": 3},
    {"input": {"s": "abcd"}, "expected": 0},
    {"input": {"s": "aabaa"}, "expected": 2},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["s"])
