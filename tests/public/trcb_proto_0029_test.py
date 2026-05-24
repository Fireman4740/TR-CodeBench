from oracles import trcb_proto_0029 as oracle
from tests.public._helpers import assert_public_cases

PUBLIC_CASES = [
    {"input": {"words": []}, "expected": []},
    {"input": {"words": ["a"]}, "expected": [["a"]]},
    {"input": {"words": ["eat", "tea", "tan", "ate", "nat", "bat"]}, "expected": [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]},
    {"input": {"words": ["abc", "def", "ghi"]}, "expected": [["abc"], ["def"], ["ghi"]]},
    {"input": {"words": ["", ""]}, "expected": [["", ""]]},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["words"])
