from oracles import trcb_proto_0005 as oracle
from tests.public._helpers import assert_public_cases


PUBLIC_CASES = [
    {
        "input": {"n": 5, "unions": [(0, 1), (1, 2), (3, 4)], "queries": [(0, 2), (0, 4), (3, 4)]},
        "expected": [True, False, True],
    },
    {"input": {"n": 3, "unions": [], "queries": [(0, 0), (0, 1)]}, "expected": [True, False]},
    {"input": {"n": 4, "unions": [(0, 1), (2, 3), (1, 3)], "queries": [(0, 3), (1, 2)]}, "expected": [True, True]},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["n", "unions", "queries"])
