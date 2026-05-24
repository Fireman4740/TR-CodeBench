from __future__ import annotations

import ast
from typing import Any


class _RecursionVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.function_stack: list[str] = []
        self.found = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call) -> None:
        if self.function_stack and isinstance(node.func, ast.Name) and node.func.id == self.function_stack[-1]:
            self.found = True
        self.generic_visit(node)


def extract_features(source: str) -> dict[str, Any]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"syntax_error": True}

    imports: set[str] = set()
    call_names: set[str] = set()
    assigned_names: set[str] = set()
    nested_loop_pairs = 0
    recursion_visitor = _RecursionVisitor()
    recursion_visitor.visit(tree)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            assigned_names.add(node.id.lower())
        elif isinstance(node, (ast.For, ast.While)):
            nested_loop_pairs += sum(isinstance(child, (ast.For, ast.While)) for child in ast.walk(node) if child is not node)

    lowered = source.lower()
    union_find = bool({"parent", "parents", "rank", "find", "union"} & assigned_names) and "find" in lowered
    fenwick = (
        "fenwick" in lowered
        or " i & -i" in lowered
        or "idx & -idx" in lowered
        or "index & -index" in lowered
        or ("bit" in assigned_names and " & -" in lowered)
    )
    kmp_prefix_table = bool({"prefix", "lps", "pi", "border", "failure"} & assigned_names)
    rolling_hash = (
        "rolling" in lowered
        or (
            "hash" in assigned_names
            and "base" in assigned_names
            and "mod" in assigned_names
        )
    )
    z_algorithm = "z_algorithm" in lowered or ("z" in assigned_names and {"left", "right"} <= assigned_names)
    adjacency_list = bool({"graph", "adj", "neighbors", "adjacency"} & assigned_names)
    coordinate_compression = (
        "sorted(set(" in source
        or ("rank" in assigned_names and "values" in assigned_names)
    )

    return {
        "syntax_error": False,
        "recursion": recursion_visitor.found,
        "heapq": "heapq" in imports or "heappush" in call_names or "heappop" in call_names,
        "bisect": "bisect" in imports or "bisect_left" in call_names or "bisect_right" in call_names,
        "deque": "collections" in imports and ("deque" in call_names or "deque" in lowered),
        "dict_memo": "memo" in assigned_names or "cache" in assigned_names or "lru_cache" in lowered,
        "union_find": union_find,
        "fenwick": fenwick,
        "kmp_prefix_table": kmp_prefix_table,
        "rolling_hash": rolling_hash,
        "z_algorithm": z_algorithm,
        "nested_loops": nested_loop_pairs,
        "adjacency_list": adjacency_list,
        "coordinate_compression": coordinate_compression,
    }
