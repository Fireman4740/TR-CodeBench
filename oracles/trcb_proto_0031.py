def solve(capacity: int, operations: list[tuple]) -> list[int]:
    """Bounded recency-ordered store using OrderedDict for O(1) get/put."""
    from collections import OrderedDict

    cache = OrderedDict()
    results = []

    for op in operations:
        if op[0] == "get":
            key = op[1]
            if key in cache:
                cache.move_to_end(key)
                results.append(cache[key])
            else:
                results.append(-1)
        elif op[0] == "put":
            key, value = op[1], op[2]
            if key in cache:
                cache.move_to_end(key)
                cache[key] = value
            else:
                if len(cache) >= capacity:
                    cache.popitem(last=False)
                cache[key] = value

    return results
