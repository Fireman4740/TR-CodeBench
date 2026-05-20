from oracles import trcb_proto_0016 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"word1": "", "word2": ""}, "expected": 0},
    {"input": {"word1": "", "word2": "abc"}, "expected": 3},
    {"input": {"word1": "horse", "word2": "ros"}, "expected": 3},
    {"input": {"word1": "intention", "word2": "execution"}, "expected": 5},
    {"input": {"word1": "abc", "word2": "abc"}, "expected": 0},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["word1", "word2"])
