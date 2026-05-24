from oracles import trcb_proto_0018 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"text1": "", "text2": "abc"}, "expected": 0},
    {"input": {"text1": "abcde", "text2": "ace"}, "expected": 3},
    {"input": {"text1": "abc", "text2": "def"}, "expected": 0},
    {"input": {"text1": "abcba", "text2": "abcbcba"}, "expected": 5},
    {"input": {"text1": "a", "text2": "a"}, "expected": 1},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["text1", "text2"])
