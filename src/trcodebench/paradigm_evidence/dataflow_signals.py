from __future__ import annotations

import ast

from .schema import ParadigmSignal

_RANGE_PARAM_PAIRS = [
    frozenset({"lo", "hi"}),
    frozenset({"l", "r"}),
    frozenset({"left", "right"}),
    frozenset({"start", "end"}),
]


def segment_tree_dataflow(tree: ast.AST) -> list[ParadigmSignal]:
    """Function accepts range bounds (lo/hi, l/r) and makes ≥2 recursive calls."""
    signals: list[ParadigmSignal] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        param_names = frozenset(arg.arg.lower() for arg in node.args.args)
        matched_pair = next(
            (pair for pair in _RANGE_PARAM_PAIRS if pair <= param_names), None
        )
        if matched_pair is None:
            continue

        recursive_count = sum(
            1
            for n in ast.walk(node)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == node.name
        )
        if recursive_count >= 2:
            signals.append(ParadigmSignal(
                layer="dataflow",
                name="seg_tree_range_params",
                confidence=0.80,
                evidence=(
                    f"fn '{node.name}' params include {matched_pair} "
                    f"+ {recursive_count} recursive calls"
                ),
            ))
            break

    return signals


def rolling_hash_dataflow(tree: ast.AST) -> list[ParadigmSignal]:
    """Hash variable incrementally updated (+=/-=) inside a loop."""
    signals: list[ParadigmSignal] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.For, ast.While)):
            continue
        for subnode in ast.walk(node):
            if (
                isinstance(subnode, ast.AugAssign)
                and isinstance(subnode.op, (ast.Add, ast.Sub))
                and isinstance(subnode.target, ast.Name)
                and "hash" in subnode.target.id.lower()
            ):
                signals.append(ParadigmSignal(
                    layer="dataflow",
                    name="rolling_hash_loop_update",
                    confidence=0.75,
                    evidence="hash variable incrementally updated inside loop",
                ))
                return signals  # one signal is enough

    return signals


def dfs_memoization_dataflow(tree: ast.AST) -> list[ParadigmSignal]:
    """Detect cache-lookup-before-recursion and cache-write-before-return patterns."""
    signals: list[ParadigmSignal] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        fn_name = node.name

        # Check for self-recursion
        has_self_call = any(
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == fn_name
            for n in ast.walk(node)
        )
        if not has_self_call:
            continue

        # Check for cache decorator (@lru_cache, @cache, @functools.lru_cache)
        has_cache_decorator = False
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id in ("cache", "lru_cache"):
                has_cache_decorator = True
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id == "lru_cache":
                has_cache_decorator = True
            elif isinstance(dec, ast.Attribute) and dec.attr in ("cache", "lru_cache"):
                has_cache_decorator = True
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == "lru_cache":
                has_cache_decorator = True

        if has_cache_decorator:
            signals.append(ParadigmSignal(
                layer="dataflow",
                name="dfs_cache_decorator",
                confidence=0.85,
                evidence=f"fn '{fn_name}' has cache/lru_cache decorator + self-recursion",
            ))
            break

        # Check for manual memo dict: `if key in memo` before recursion, `memo[key] = result` before return
        body_src = ast.dump(node)
        has_memo_lookup = any(
            isinstance(n, ast.Compare)
            and any(isinstance(c, ast.In) for c in n.ops)
            for n in ast.walk(node)
            if isinstance(n, ast.Compare)
        )
        has_memo_write = any(
            isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Subscript) for t in n.targets)
            for n in ast.walk(node)
        )
        if has_memo_lookup and has_memo_write:
            signals.append(ParadigmSignal(
                layer="dataflow",
                name="dfs_manual_memoization",
                confidence=0.75,
                evidence=f"fn '{fn_name}' has memo lookup + memo write + self-recursion",
            ))
            break

    return signals
