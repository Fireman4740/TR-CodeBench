from oracles import trcb_proto_0027 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"text": "", "patterns": ["ab"]}, "expected": []},
    {"input": {"text": "abcabc", "patterns": []}, "expected": []},
    {"input": {"text": "abcdefg", "patterns": ["abc", "efg"]}, "expected": [0, 4]},
    {"input": {"text": "aaaa", "patterns": ["aa"]}, "expected": [0, 1, 2]},
    {"input": {"text": "hello world", "patterns": ["xyz", "abc"]}, "expected": []},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["text", "patterns"])
