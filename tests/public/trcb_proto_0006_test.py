from oracles import trcb_proto_0006 as oracle
from tests.public._helpers import assert_public_cases


PUBLIC_CASES = [
    {"input": {"text": "ababa", "pattern": "aba"}, "expected": [0, 2]},
    {"input": {"text": "aaaa", "pattern": "aa"}, "expected": [0, 1, 2]},
    {"input": {"text": "abc", "pattern": "d"}, "expected": []},
    {"input": {"text": "abc", "pattern": ""}, "expected": [0, 1, 2, 3]},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["text", "pattern"])
