from oracles import trcb_proto_0037 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"n": 10}, "expected": 4},
    {"input": {"n": 0}, "expected": 0},
    {"input": {"n": 1}, "expected": 0},
    {"input": {"n": 2}, "expected": 0},
    {"input": {"n": 30}, "expected": 10},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["n"])
