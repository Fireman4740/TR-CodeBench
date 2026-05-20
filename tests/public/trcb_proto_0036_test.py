from oracles import trcb_proto_0036 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"base": 2, "exponent": 10, "modulus": 1000}, "expected": 24},
    {"input": {"base": 3, "exponent": 0, "modulus": 7}, "expected": 1},
    {"input": {"base": 5, "exponent": 1, "modulus": 3}, "expected": 2},
    {"input": {"base": 0, "exponent": 5, "modulus": 13}, "expected": 0},
    {"input": {"base": 7, "exponent": 256, "modulus": 13}, "expected": 9},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["base", "exponent", "modulus"])
