from oracles import trcb_proto_0040 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"n": 0}, "expected": 0},
    {"input": {"n": 1}, "expected": 1},
    {"input": {"n": 10}, "expected": 55},
    {"input": {"n": 50}, "expected": 12586269025 % (10**9 + 7)},
    {"input": {"n": 1000000000000000000}, "expected": 209783453},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["n"])
