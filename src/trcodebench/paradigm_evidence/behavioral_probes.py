from __future__ import annotations

import ast
import time
from pathlib import Path
from typing import Any, Callable

from .schema import ParadigmSignal


def _time_calls(
    func: Callable,
    cases: list[dict[str, Any]],
    argument_order: list[str],
    timeout: float = 2.0,
) -> list[float]:
    times: list[float] = []
    for case in cases:
        inputs = case["input"]
        args = [inputs[k] for k in argument_order]
        t0 = time.perf_counter()
        try:
            func(*args)
        except Exception:
            times.append(timeout)
            continue
        elapsed = time.perf_counter() - t0
        times.append(min(elapsed, timeout))
    return times


def _scaling_ratio(small_times: list[float], large_times: list[float]) -> float | None:
    s_med = sorted(small_times)[len(small_times) // 2] if small_times else None
    l_med = sorted(large_times)[len(large_times) // 2] if large_times else None
    if s_med is None or l_med is None or s_med < 1e-7:
        return None
    return l_med / s_med


def probe_segment_tree(
    func: Callable,
    argument_order: list[str],
    make_cases: Callable[[int], list[dict[str, Any]]],
) -> list[ParadigmSignal]:
    signals: list[ParadigmSignal] = []
    small = make_cases(500)
    large = make_cases(5000)
    s_times = _time_calls(func, small, argument_order)
    l_times = _time_calls(func, large, argument_order)
    ratio = _scaling_ratio(s_times, l_times)
    if ratio is not None and ratio < 35.0:
        signals.append(ParadigmSignal(
            layer="behavioral",
            name="seg_tree_log_scaling",
            confidence=0.70,
            evidence=f"scaling ratio {ratio:.1f} consistent with O(n log n)",
        ))
    return signals


def probe_rolling_hash(
    func: Callable,
    argument_order: list[str],
    make_cases: Callable[[int], list[dict[str, Any]]],
) -> list[ParadigmSignal]:
    signals: list[ParadigmSignal] = []
    small = make_cases(200)
    large = make_cases(2000)
    s_times = _time_calls(func, small, argument_order)
    l_times = _time_calls(func, large, argument_order)
    ratio = _scaling_ratio(s_times, l_times)
    if ratio is not None and ratio < 20.0:
        signals.append(ParadigmSignal(
            layer="behavioral",
            name="rolling_hash_linear_scaling",
            confidence=0.65,
            evidence=f"scaling ratio {ratio:.1f} consistent with O(n)",
        ))
    return signals


def probe_dfs_memoization(
    func: Callable,
    argument_order: list[str],
    make_small_dag: Callable[[], list[dict[str, Any]]],
    make_large_dag: Callable[[], list[dict[str, Any]]],
) -> list[ParadigmSignal]:
    signals: list[ParadigmSignal] = []
    small = make_small_dag()
    large = make_large_dag()
    s_times = _time_calls(func, small, argument_order)
    l_times = _time_calls(func, large, argument_order)
    ratio = _scaling_ratio(s_times, l_times)
    if ratio is not None and ratio < 50.0:
        signals.append(ParadigmSignal(
            layer="behavioral",
            name="dfs_memo_polynomial_scaling",
            confidence=0.60,
            evidence=f"scaling ratio {ratio:.1f} — not exponential, consistent with memoized DFS",
        ))
    return signals


def probe_z_algorithm(
    func: Callable,
    argument_order: list[str],
) -> list[ParadigmSignal]:
    signals: list[ParadigmSignal] = []
    adversarial_cases = [
        {"input": {argument_order[0]: "a" * 500, argument_order[1]: "a" * 10}} if len(argument_order) >= 2
        else {"input": {argument_order[0]: "a" * 500 + "$" + "a" * 10}},
        {"input": {argument_order[0]: "ab" * 250, argument_order[1]: "ab" * 5}} if len(argument_order) >= 2
        else {"input": {argument_order[0]: "ab" * 250 + "$" + "ab" * 5}},
    ]
    try:
        times = _time_calls(func, adversarial_cases, argument_order, timeout=1.0)
        if all(t < 0.1 for t in times):
            signals.append(ParadigmSignal(
                layer="behavioral",
                name="z_algo_adversarial_fast",
                confidence=0.60,
                evidence="fast on adversarial repeated-char strings",
            ))
    except Exception:
        pass
    return signals
