from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


BANNED_MODULES = {
    "importlib",
    "inspect",
    "os",
    "pathlib",
    "pickle",
    "runpy",
    "shutil",
    "socket",
    "subprocess",
    "sys",
}

BANNED_CALLS = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "input",
    "open",
}


def _root_module(module_name: str | None) -> str:
    if not module_name:
        return ""
    return module_name.split(".", 1)[0]


def analyze_candidate(candidate_path: str | Path, item: dict[str, Any]) -> dict[str, Any]:
    path = Path(candidate_path)
    source = path.read_text(encoding="utf-8")
    allowed_imports = set(item["task"].get("allowed_imports", []))
    violations: list[str] = []
    imported_modules: list[str] = []
    suspicious_calls: list[str] = []

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return {
            "ok": False,
            "syntax_error": str(exc),
            "violations": [f"syntax_error:{exc.msg}"],
            "imported_modules": [],
            "suspicious_calls": [],
        }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = _root_module(alias.name)
                imported_modules.append(root)
                if root in BANNED_MODULES:
                    violations.append(f"banned_import:{root}")
                elif root not in allowed_imports:
                    violations.append(f"disallowed_import:{root}")
        elif isinstance(node, ast.ImportFrom):
            root = _root_module(node.module)
            imported_modules.append(root)
            if root in BANNED_MODULES:
                violations.append(f"banned_import:{root}")
            elif root not in allowed_imports:
                violations.append(f"disallowed_import:{root}")
        elif isinstance(node, ast.Call):
            call_name = ""
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            if call_name in BANNED_CALLS:
                suspicious_calls.append(call_name)
                violations.append(f"banned_call:{call_name}")

    return {
        "ok": not violations,
        "syntax_error": None,
        "violations": sorted(set(violations)),
        "imported_modules": sorted(set(module for module in imported_modules if module)),
        "suspicious_calls": sorted(set(suspicious_calls)),
    }
