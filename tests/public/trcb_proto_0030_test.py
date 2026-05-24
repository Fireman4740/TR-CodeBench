from oracles import trcb_proto_0030 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"s": ""}, "expected": []},
    {"input": {"s": "a"}, "expected": [0]},
    {"input": {"s": "aaaaaa"}, "expected": [0, 5, 4, 3, 2, 1]},
    {"input": {"s": "aabxaa"}, "expected": [0, 1, 0, 0, 2, 1]},
    {"input": {"s": "abcabc"}, "expected": [0, 0, 0, 3, 0, 0]},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["s"])
