from __future__ import annotations

import importlib.util
import io
import multiprocessing as mp
import pickle
import traceback
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any


def normalize_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [normalize_value(item) for item in value]
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize_value(value[key]) for key in sorted(value)}
    return value


def load_function_from_path(module_path: str | Path, function_name: str):
    path = Path(module_path).resolve()
    spec = importlib.util.spec_from_file_location(f"_trcb_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    func = getattr(module, function_name, None)
    if not callable(func):
        raise AttributeError(f"Candidate must define callable {function_name}()")
    return func


def _safe_for_queue(value: Any) -> Any:
    value = normalize_value(value)
    try:
        pickle.dumps(value)
    except Exception:
        return {"__unserializable__": repr(value)}
    return value


def _child_run(
    queue: mp.Queue,
    candidate_path: str,
    function_name: str,
    argument_order: list[str],
    inputs: dict[str, Any],
) -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            func = load_function_from_path(candidate_path, function_name)
            args = [inputs[name] for name in argument_order]
            output = func(*args)
        queue.put(
            {
                "status": "ok",
                "output": _safe_for_queue(output),
                "stdout": stdout.getvalue(),
                "stderr": stderr.getvalue(),
            }
        )
    except BaseException as exc:
        queue.put(
            {
                "status": "crash",
                "output": None,
                "stdout": stdout.getvalue(),
                "stderr": stderr.getvalue(),
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(limit=6),
            }
        )


def run_one_case(
    candidate_path: str | Path,
    function_name: str,
    argument_order: list[str],
    inputs: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    queue: mp.Queue = mp.Queue()
    process = mp.Process(
        target=_child_run,
        args=(queue, str(candidate_path), function_name, argument_order, inputs),
    )
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join(0.2)
        return {
            "status": "timeout",
            "output": None,
            "stdout": "",
            "stderr": "",
            "error": f"timeout after {timeout_seconds:.3f}s",
        }
    if queue.empty():
        return {
            "status": "crash",
            "output": None,
            "stdout": "",
            "stderr": "",
            "error": "candidate process exited without a result",
        }
    return queue.get()
