from __future__ import annotations

import textwrap

import pytest

from trcodebench.ast_features import extract_features


def dedent(src: str) -> str:
    return textwrap.dedent(src).strip()


# --- Fenwick ---

def test_fenwick_detected_via_keyword():
    features = extract_features(dedent("""
        def solve(n, ops):
            fenwick = [0] * (n + 1)
            def update(i, v):
                while i <= n:
                    fenwick[i] += v
                    i += i & -i
    """))
    assert features["fenwick"]


def test_fenwick_detected_via_bit_trick_pattern():
    features = extract_features(dedent("""
        def solve(n):
            i = 1
            while i <= n:
                i += i & -i
            return i
    """))
    assert features["fenwick"]


def test_bitmask_variable_bit_does_not_trigger_fenwick():
    features = extract_features(dedent("""
        def solve(nums):
            bit = 0
            for x in nums:
                bit |= x
            return bin(bit).count('1')
    """))
    assert not features["fenwick"]


def test_bitwise_op_without_bit_variable_does_not_trigger_fenwick():
    features = extract_features(dedent("""
        def solve(n):
            mask = (1 << n) - 1
            return mask & (mask - 1)
    """))
    assert not features["fenwick"]


# --- Rolling hash ---

def test_rolling_hash_detected_via_rolling_keyword():
    features = extract_features(dedent("""
        def solve(text, pattern):
            # rolling hash approach
            base = 31
            mod = 10**9 + 7
            rolling = 0
            for c in text:
                rolling = (rolling * base + ord(c)) % mod
            return rolling
    """))
    assert features["rolling_hash"]


def test_rolling_hash_detected_via_variable_naming():
    features = extract_features(dedent("""
        def solve(text, pattern):
            base = 31
            mod = 10**9 + 7
            hash = 0
            for c in text:
                hash = (hash * base + ord(c)) % mod
            return hash
    """))
    assert features["rolling_hash"]


def test_builtin_hash_with_mod_does_not_trigger_rolling_hash():
    features = extract_features(dedent("""
        def solve(x):
            mod = 10**9 + 7
            return hash(x) % mod
    """))
    assert not features["rolling_hash"]


def test_mod_without_hash_does_not_trigger_rolling_hash():
    features = extract_features(dedent("""
        def solve(nums):
            mod = 10**9 + 7
            total = 0
            for x in nums:
                total = (total + x) % mod
            return total
    """))
    assert not features["rolling_hash"]


# --- Recursion (including async) ---

def test_direct_recursion_detected():
    features = extract_features(dedent("""
        def solve(n):
            if n <= 0:
                return 0
            return solve(n - 1) + 1
    """))
    assert features["recursion"]


def test_async_recursion_detected():
    features = extract_features(dedent("""
        async def solve(n):
            if n <= 0:
                return 0
            return await solve(n - 1) + 1
    """))
    assert features["recursion"]


def test_no_recursion_in_iterative_function():
    features = extract_features(dedent("""
        def solve(n):
            result = 0
            for i in range(n):
                result += i
            return result
    """))
    assert not features["recursion"]


# --- Syntax error ---

def test_syntax_error_returns_safe_dict():
    features = extract_features("def (broken:")
    assert features.get("syntax_error") is True


# --- Basic feature detections ---

def test_heapq_detected_from_import():
    features = extract_features(dedent("""
        import heapq
        def solve(nums):
            heapq.heapify(nums)
            return heapq.heappop(nums)
    """))
    assert features["heapq"]


def test_bisect_detected_from_call():
    features = extract_features(dedent("""
        from bisect import bisect_left
        def solve(nums, target):
            return bisect_left(nums, target)
    """))
    assert features["bisect"]


def test_union_find_detected():
    features = extract_features(dedent("""
        def solve(n, edges):
            parent = list(range(n))
            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x
            def union(a, b):
                parent[find(a)] = find(b)
            for u, v in edges:
                union(u, v)
            return [find(i) for i in range(n)]
    """))
    assert features["union_find"]


@pytest.mark.parametrize("n_nested,expected_count", [
    (0, 0),
    (1, 1),
    (2, 3),  # outer loop contains 2 inner → 2 pairs at depth 1, plus 1 pair for the inner-inner
])
def test_nested_loop_count(n_nested: int, expected_count: int):
    if n_nested == 0:
        src = "def f(n):\n    for i in range(n): pass"
    elif n_nested == 1:
        src = "def f(n):\n    for i in range(n):\n        for j in range(n): pass"
    else:
        src = "def f(n):\n    for i in range(n):\n        for j in range(n):\n            for k in range(n): pass"
    features = extract_features(src)
    assert features["nested_loops"] == expected_count
