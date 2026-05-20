from oracles import trcb_proto_0014 as oracle
from tests.public._helpers import assert_public_cases


PUBLIC_CASES = [
    {"input": {"stream": [5]}, "expected": [5]},
    {"input": {"stream": [2, 3]}, "expected": [2, 2]},
    {"input": {"stream": [5, 2, 3, 1, 4]}, "expected": [5, 2, 3, 2, 3]},
    {"input": {"stream": [1, 1, 1, 1]}, "expected": [1, 1, 1, 1]},
    {"input": {"stream": [10, 20, 30, 40]}, "expected": [10, 10, 20, 20]},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["stream"])
