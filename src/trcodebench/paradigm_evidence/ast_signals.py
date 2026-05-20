from __future__ import annotations

import ast

from .schema import ParadigmSignal


def segment_tree_signals(tree: ast.AST) -> list[ParadigmSignal]:
    signals: list[ParadigmSignal] = []

    # Structural: function with mid-split + ≥2 recursive calls
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        fn_name = node.name

        has_mid_split = any(
            isinstance(n, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id in ("mid", "m", "middle")
                for t in n.targets
            )
            and isinstance(n.value, ast.BinOp)
            and isinstance(n.value.op, ast.FloorDiv)
            for n in ast.walk(node)
        )
        if not has_mid_split:
            continue

        recursive_count = sum(
            1
            for n in ast.walk(node)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == fn_name
        )
        if recursive_count >= 2:
            signals.append(ParadigmSignal(
                layer="structural",
                name="seg_tree_divide_conquer",
                confidence=0.85,
                evidence=f"fn '{fn_name}': {recursive_count} recursive calls + mid-split",
            ))
            break

    # Structural: child-index arithmetic (2*i, 2*i+1 patterns)
    child_idx_count = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Mult)
        and (
            (isinstance(node.left, ast.Constant) and node.left.value == 2)
            or (isinstance(node.right, ast.Constant) and node.right.value == 2)
        )
    )
    if child_idx_count >= 2:
        signals.append(ParadigmSignal(
            layer="structural",
            name="seg_tree_child_indexing",
            confidence=0.65,
            evidence=f"child index pattern (2*node) found {child_idx_count} times",
        ))

    return signals


def z_algorithm_signals(source: str, tree: ast.AST) -> list[ParadigmSignal]:
    signals: list[ParadigmSignal] = []
    lowered = source.lower()

    # z-array initialization to zeros
    if "z = [0]" in lowered or "z=[0]" in lowered or "z = [0 " in lowered or "z=[0 " in lowered:
        signals.append(ParadigmSignal(
            layer="structural",
            name="z_array_init",
            confidence=0.80,
            evidence="z-array initialized to zeros",
        ))

    # l/r window pointer variables
    assigned = {
        n.id.lower()
        for n in ast.walk(tree)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
    }
    if {"l", "r"} <= assigned or {"left", "right"} <= assigned:
        signals.append(ParadigmSignal(
            layer="structural",
            name="z_window_pointers",
            confidence=0.60,
            evidence="l/r or left/right window pointers present",
        ))

    # z[i] index access
    if "z[i]" in lowered or "z_arr" in lowered or "zarr" in lowered:
        signals.append(ParadigmSignal(
            layer="structural",
            name="z_index_access",
            confidence=0.75,
            evidence="z[i] access pattern",
        ))

    return signals


def rolling_hash_signals(source: str) -> list[ParadigmSignal]:
    signals: list[ParadigmSignal] = []
    lowered = source.lower()

    # mod + base/prime together
    has_mod = "% mod" in lowered or "% p " in lowered or "% prime" in lowered
    has_base = "base" in lowered or "prime" in lowered
    if has_mod and has_base:
        signals.append(ParadigmSignal(
            layer="structural",
            name="rolling_hash_modular",
            confidence=0.75,
            evidence="modular arithmetic with base/prime constant",
        ))

    # power array or modular exponentiation
    if "power" in lowered or ("pow" in lowered and "mod" in lowered):
        signals.append(ParadigmSignal(
            layer="structural",
            name="rolling_hash_power",
            confidence=0.70,
            evidence="power array or modular exponentiation",
        ))

    # hash * base % mod window-slide update
    if "hash" in lowered and ("* base" in lowered or "* b" in lowered) and "mod" in lowered:
        signals.append(ParadigmSignal(
            layer="structural",
            name="rolling_hash_window_update",
            confidence=0.80,
            evidence="hash * base % mod window-slide pattern",
        ))

    return signals
