from __future__ import annotations

import ast
import re
from typing import Any

from .denial_schema import DenialConstraint


def _collect_imports(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module.split(".")[0])
    return modules


def _collect_names(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def _has_recursion(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn_name = node.name
            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Name)
                    and child.func.id == fn_name
                ):
                    return True
    return False


def _has_nested_loops(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While)):
            for child in ast.walk(node):
                if child is not node and isinstance(child, (ast.For, ast.While)):
                    return True
    return False


def _has_explicit_sort(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "sorted":
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr == "sort":
                return True
    return False


def _has_nested_for_loops(source: str) -> bool:
    """True if source contains nested `for` loops (for inside for, ignoring while)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            for child in ast.walk(node):
                if child is not node and isinstance(child, ast.For):
                    return True
    return False


def _has_nested_while_loops(source: str) -> bool:
    """True if source contains nested `while` loops."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            for child in ast.walk(node):
                if child is not node and isinstance(child, ast.While):
                    return True
    return False


def verify_denial(
    source: str,
    constraint: DenialConstraint,
) -> tuple[bool, str | None]:
    if constraint.constraint_type == "forbidden_api":
        names = _collect_names(source)
        violations = [f for f in constraint.forbidden if f in names]
        if violations:
            return False, f"Forbidden API used: {', '.join(violations)}"
        return True, None

    elif constraint.constraint_type == "forbidden_import":
        imports = _collect_imports(source)
        violations = [f for f in constraint.forbidden if f in imports]
        if violations:
            return False, f"Forbidden import: {', '.join(violations)}"
        names = _collect_names(source)
        violations = [f for f in constraint.forbidden if f in names]
        if violations:
            return False, f"Forbidden module reference: {', '.join(violations)}"
        return True, None

    elif constraint.constraint_type == "forbidden_structure":
        violations: list[str] = []
        for pattern in constraint.forbidden:
            normalized = pattern.lower().replace("_", " ").strip()
            if normalized == "recursion" and _has_recursion(source):
                violations.append("recursion")
            elif normalized in ("nested loop", "nested loops") and _has_nested_loops(source):
                violations.append("nested loops")
            elif normalized in ("explicit sort", "sort", "sorting") and _has_explicit_sort(source):
                violations.append("explicit sort")
        if violations:
            return False, f"Forbidden structure: {', '.join(violations)}"
        return True, None

    elif constraint.constraint_type == "forbidden_paradigm":
        # Paradigm constraints are soft — verified externally via paradigm evidence stack.
        # Here we only do a best-effort name check.
        lowered = source.lower()
        for pattern in constraint.forbidden:
            pattern_lower = pattern.lower().replace("_", " ")
            # Very conservative: only flag if explicit mention in comments
            comment_lines = [
                line.strip()
                for line in source.splitlines()
                if line.strip().startswith("#")
            ]
            for comment in comment_lines:
                if pattern_lower in comment.lower():
                    return False, f"Paradigm '{pattern}' mentioned in comments"
        return True, None

    elif constraint.constraint_type == "forbidden_construct":
        # General-purpose construct check: combines name, import, and structural pattern matching.
        violations: list[str] = []
        names = _collect_names(source)
        imports = _collect_imports(source)

        for pattern in constraint.forbidden:
            normalized = pattern.lower().replace("_", " ").strip()

            # Structural patterns — explicit keywords
            if normalized in ("nested for loops", "nested_for_loops"):
                if _has_nested_for_loops(source):
                    violations.append(pattern)
                continue
            if normalized in ("nested while loops", "nested_while_loops"):
                if _has_nested_while_loops(source):
                    violations.append(pattern)
                continue
            if normalized in ("nested loops", "nested loop"):
                if _has_nested_loops(source):
                    violations.append(pattern)
                continue
            if normalized in ("recursion", "recursive call", "recursive"):
                if _has_recursion(source):
                    violations.append(pattern)
                continue
            if normalized in ("explicit sort", "sort", "sorting"):
                if _has_explicit_sort(source):
                    violations.append(pattern)
                continue

            # Dotted reference (e.g., "collections.OrderedDict") → check import + attr
            if "." in pattern:
                parts = pattern.split(".")
                root, leaf = parts[0], parts[-1]
                if root in imports and leaf in names:
                    violations.append(pattern)
                continue

            # Underscore-suffixed hints (e.g., "OrderedDict_import_usage") → strip suffix
            bare = re.sub(r"_(import_usage|usage|api|call|reference)$", "", pattern, flags=re.I)

            # Plain name check
            if bare in names or bare in imports:
                violations.append(pattern)

        if violations:
            return False, f"Forbidden construct used: {', '.join(violations)}"
        return True, None

    elif constraint.constraint_type == "resource":
        # Resource constraints are verified via stress tests externally.
        return True, None

    # Unknown type: log and pass through (no false positives)
    return True, None
