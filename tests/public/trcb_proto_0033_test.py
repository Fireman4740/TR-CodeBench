from oracles import trcb_proto_0033 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"words": ["apple", "app", "apricot", "banana"], "queries": ["ap"]}, "expected": [3]},
    {"input": {"words": ["hello", "help", "hero"], "queries": ["he", "hel", "her"]}, "expected": [3, 2, 1]},
    {"input": {"words": ["a", "a", "a"], "queries": ["a", "b"]}, "expected": [3, 0]},
    {"input": {"words": [], "queries": ["any"]}, "expected": [0]},
    {"input": {"words": ["cat", "car", "card"], "queries": ["", "ca", "car"]}, "expected": [3, 3, 2]},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["words", "queries"])
