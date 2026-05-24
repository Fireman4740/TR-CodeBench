from oracles import trcb_proto_0015 as oracle
from tests.public._helpers import assert_public_cases


PUBLIC_CASES = [
    {"input": {"lists": []}, "expected": []},
    {"input": {"lists": [[]]}, "expected": []},
    {"input": {"lists": [[1, 3, 5], [2, 4, 6]]}, "expected": [1, 2, 3, 4, 5, 6]},
    {"input": {"lists": [[1], [0], [2]]}, "expected": [0, 1, 2]},
    {"input": {"lists": [[-5, -3, -1], [-4, -2, 0], [-6, 1, 2]]}, "expected": [-6, -5, -4, -3, -2, -1, 0, 1, 2]},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["lists"])
