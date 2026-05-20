from oracles import trcb_proto_0002 as oracle
from tests.public._helpers import assert_public_cases


PUBLIC_CASES = [
    {
        "input": {
            "n": 4,
            "edges": [(0, 1, 5), (0, 2, 1), (2, 1, 1), (1, 3, 2), (2, 3, 7)],
            "source": 0,
            "target": 3,
        },
        "expected": 4,
    },
    {"input": {"n": 3, "edges": [(0, 1, 4)], "source": 0, "target": 2}, "expected": -1},
    {"input": {"n": 1, "edges": [], "source": 0, "target": 0}, "expected": 0},
    {"input": {"n": 3, "edges": [(0, 1, 10), (0, 1, 2), (1, 2, 3)], "source": 0, "target": 2}, "expected": 5},
]


def test_oracle_public_cases():
    assert_public_cases(oracle, PUBLIC_CASES, ["n", "edges", "source", "target"])
