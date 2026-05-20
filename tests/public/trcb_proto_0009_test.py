from oracles import trcb_proto_0009 as oracle
from tests.public._helpers import assert_public_cases


PUBLIC_CASES = [
    {"input": {"n": 5, "operations": [("add", 0, 3), ("add", 3, 7), ("sum", 0, 4)]}, "expected": [10]},
    {
        "input": {"n": 4, "operations": [("sum", 0, 4), ("add", 2, -5), ("sum", 2, 3), ("sum", 3, 4)]},
        "expected": [0, -5, 0],
    },
    {"input": {"n": 1, "operations": [("add", 0, 9), ("sum", 0, 1)]}, "expected": [9]},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["n", "operations"])
