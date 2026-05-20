from oracles import trcb_proto_0021 as oracle

PUBLIC_CASES = [
    {"input": {"n": 4, "edges": [(0, 1), (0, 2), (1, 3), (2, 3)]}, "expected": [0, 1, 2, 3]},
    {"input": {"n": 3, "edges": [(0, 1), (1, 2), (2, 0)]}, "expected": []},
    {"input": {"n": 1, "edges": []}, "expected": [0]},
    {"input": {"n": 4, "edges": []}, "expected": [0, 1, 2, 3]},
    {"input": {"n": 3, "edges": [(2, 1), (2, 0), (1, 0)]}, "expected": [2, 1, 0]},
]


def test_oracle_public_cases():
    for case in PUBLIC_CASES:
        inputs = case["input"]
        result = oracle.solve(inputs["n"], inputs["edges"])
        expected = case["expected"]
        if expected == []:
            assert result == []
        else:
            # Validate it's a valid topological ordering
            n = inputs["n"]
            edges = inputs["edges"]
            assert sorted(result) == list(range(n))
            pos = {v: i for i, v in enumerate(result)}
            for u, v in edges:
                assert pos[u] < pos[v]
