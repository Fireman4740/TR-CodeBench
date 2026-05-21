from __future__ import annotations

import importlib
import random
import warnings
from typing import Any


def _case(**inputs: Any) -> dict[str, Any]:
    return {"input": inputs}


def _gen_lis(rng: random.Random, n: int | None = None) -> dict[str, Any]:
    n = n if n is not None else rng.choice([0, 1, 2, rng.randint(3, 80), rng.randint(100, 500)])
    nums = [rng.randint(-100, 100) for _ in range(n)]
    if rng.random() < 0.1:
        nums = sorted(nums)
    if rng.random() < 0.1:
        nums = sorted(nums, reverse=True)
    return _case(nums=nums)


def _gen_shortest_path(rng: random.Random, n: int | None = None) -> dict[str, Any]:
    n = n if n is not None else rng.randint(1, 40)
    max_edges = n * max(1, n - 1)
    m = min(max_edges, rng.randint(max(0, n - 1), max(n, 4 * n))) if n > 40 else rng.randint(0, min(240, max_edges))
    edges: set[tuple[int, int, int]] = set()
    for _ in range(m):
        u = rng.randrange(n)
        v = rng.randrange(n)
        if u != v:
            edges.add((u, v, rng.randint(1, 30)))
    source = rng.randrange(n)
    target = rng.randrange(n)
    return _case(n=n, edges=sorted(edges), source=source, target=target)


def _gen_intervals(rng: random.Random, n: int | None = None) -> dict[str, Any]:
    intervals = []
    count = n if n is not None else rng.randint(0, 100)
    for _ in range(count):
        start = rng.randint(-20, max(120, count * 2))
        end = start + rng.randint(1, 30)
        intervals.append((start, end))
    return _case(intervals=intervals)


def _gen_subarray(rng: random.Random, n: int | None = None) -> dict[str, Any]:
    n = n if n is not None else rng.randint(0, 160)
    nums = [rng.randint(0, 30) for _ in range(n)]
    target = rng.randint(1, max(400, 30 * max(1, n // 10)))
    return _case(nums=nums, target=target)


def _gen_union_find(rng: random.Random, n: int | None = None) -> dict[str, Any]:
    n = n if n is not None else rng.randint(1, 80)
    union_count = 2 * n if n > 80 else rng.randint(0, 160)
    query_count = 2 * n if n > 80 else rng.randint(1, 160)
    unions = [(rng.randrange(n), rng.randrange(n)) for _ in range(union_count)]
    queries = [(rng.randrange(n), rng.randrange(n)) for _ in range(query_count)]
    return _case(n=n, unions=unions, queries=queries)


def _gen_kmp(rng: random.Random, n: int | None = None) -> dict[str, Any]:
    alphabet = "abca"
    text_len = n if n is not None else rng.randint(0, 120)
    pattern_len = rng.randint(0, 12) if n is None else max(1, min(128, n // 20))
    text = "".join(rng.choice(alphabet) for _ in range(text_len))
    pattern = "".join(rng.choice(alphabet) for _ in range(pattern_len))
    return _case(text=text, pattern=pattern)


def _gen_sliding_window(rng: random.Random, n: int | None = None) -> dict[str, Any]:
    n = n if n is not None else rng.randint(0, 160)
    nums = [rng.randint(-100, 100) for _ in range(n)]
    k = rng.randint(0, n + 3) if n <= 160 else max(1, n // 20)
    return _case(nums=nums, k=k)


def _gen_dag_dp(rng: random.Random, n: int | None = None) -> dict[str, Any]:
    n = n if n is not None else rng.randint(1, 60)
    edges = []
    if n > 60:
        for _ in range(4 * n):
            start = rng.randrange(n)
            end = rng.randrange(start, n)
            if start != end:
                edges.append((start, end, rng.randint(-10, 25)))
    else:
        for u in range(n):
            for v in range(u + 1, n):
                if rng.random() < min(0.12, 8 / max(1, n)):
                    edges.append((u, v, rng.randint(-10, 25)))
    return _case(n=n, edges=edges)


def _gen_fenwick(rng: random.Random, n: int | None = None) -> dict[str, Any]:
    n = n if n is not None else rng.randint(1, 120)
    if n > 120:
        operations = [("add", index, rng.randint(-50, 50)) for index in range(n)]
        operations.extend(("sum", 0, n) for _ in range(n))
        return _case(n=n, operations=operations)

    operations = []
    operation_count = rng.randint(1, 180)
    for _ in range(operation_count):
        if rng.random() < 0.6:
            operations.append(("add", rng.randrange(n), rng.randint(-50, 50)))
        else:
            left = rng.randrange(n)
            right = rng.randint(left, n)
            operations.append(("sum", left, right))
    return _case(n=n, operations=operations)


def _gen_heap_scheduling(rng: random.Random, n: int | None = None) -> dict[str, Any]:
    n = n if n is not None else rng.randint(0, 120)
    tasks = [(rng.randint(0, max(100, n)), rng.randint(1, 40)) for _ in range(n)]
    return _case(tasks=tasks)


GENERATORS = {
    "trcb-proto-0001": _gen_lis,
    "trcb-proto-0002": _gen_shortest_path,
    "trcb-proto-0003": _gen_intervals,
    "trcb-proto-0004": _gen_subarray,
    "trcb-proto-0005": _gen_union_find,
    "trcb-proto-0006": _gen_kmp,
    "trcb-proto-0007": _gen_sliding_window,
    "trcb-proto-0008": _gen_dag_dp,
    "trcb-proto-0009": _gen_fenwick,
    "trcb-proto-0010": _gen_heap_scheduling,
}


def _generate_from_strategy(item: dict[str, Any], n_cases: int) -> list[dict[str, Any]]:
    strategy_ref = item["tests"].get("hypothesis_strategy")
    if not strategy_ref:
        raise KeyError(f"No hidden generator registered for {item['id']}")

    mod_name, fn_name = strategy_ref.split(":", 1)
    factory = getattr(importlib.import_module(mod_name), fn_name)
    strategy = factory()

    cases: list[dict[str, Any]] = []
    seen: set[str] = set()
    attempts = max(n_cases * 5, 10)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for _ in range(attempts):
            case = strategy.example()
            key = repr(case)
            if key in seen:
                continue
            seen.add(key)
            cases.append(case)
            if len(cases) >= n_cases:
                break
    return cases


def generate_cases(
    item: dict[str, Any],
    limit: int | None = None,
    seed: int | None = None,
    size_override: int | None = None,
) -> list[dict[str, Any]]:
    item_id = item["id"]
    n_cases = limit if limit is not None else int(item["tests"].get("n_hidden_cases", 100))
    if item_id not in GENERATORS:
        return _generate_from_strategy(item, n_cases)
    rng = random.Random(seed if seed is not None else item_id)
    generator = GENERATORS[item_id]
    return [generator(rng, size_override) for _ in range(n_cases)]
