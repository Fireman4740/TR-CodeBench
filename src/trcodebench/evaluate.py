from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import time
import warnings
from pathlib import Path
from typing import Any

from hypothesis import HealthCheck, Phase, given, settings
from hypothesis.errors import Unsatisfiable

from .ast_features import extract_features
from .hidden_tests import generate_cases
from .load_items import ROOT, load_item, resolve_repo_path
from .paradigm_classifier import is_genuine_divergence, paradigm_distance as compute_paradigm_distance
from .paradigm_evidence import enhance_candidate_paradigms
from .run_candidate import load_function_from_path, normalize_value, run_one_case
from .salieri_minhash import file_similarity
from .metrics_profile import compute_metrics_profile
from .scoring import compute_score
from .static_checks import analyze_candidate


def _load_public_cases(item: dict[str, Any]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for test_path in item["tests"].get("public_tests", []):
        module_path = resolve_repo_path(test_path)
        spec_name = "_trcb_public_" + "_".join(module_path.relative_to(ROOT).with_suffix("").parts)
        spec = importlib.util.spec_from_file_location(spec_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot import public tests from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cases.extend(getattr(module, "PUBLIC_CASES"))
    return cases


def _expected_for_case(oracle_func, argument_order: list[str], case: dict[str, Any]) -> Any:
    if "expected" in case:
        return case["expected"]
    inputs = case["input"]
    return oracle_func(*[inputs[name] for name in argument_order])


def _run_one_pbt_group(
    group_name: str,
    strategy_factory,
    candidate_path: Path,
    oracle_func,
    function_name: str,
    argument_order: list[str],
    n_cases: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    failure_msg: list[str] = []
    error_str: str | None = None

    @settings(
        max_examples=n_cases,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
        database=None,
        phases=[Phase.explicit, Phase.reuse, Phase.generate],  # no shrink — benchmark needs detection, not minimal counterexample
    )
    @given(strategy_factory())
    def _check(case: dict) -> None:
        inputs = case["input"]
        expected = normalize_value(oracle_func(*[inputs[k] for k in argument_order]))
        outcome = run_one_case(candidate_path, function_name, argument_order, inputs, timeout_seconds)
        if outcome["status"] != "ok":
            raise AssertionError(f"candidate {outcome['status']}: {outcome.get('error', '')}")
        actual = normalize_value(outcome.get("output"))
        if actual != expected:
            raise AssertionError(f"got {actual!r}, expected {expected!r}")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _check()
    except AssertionError as exc:
        failure_msg.append(str(exc))
        error_str = str(exc)
    except Unsatisfiable as exc:
        error_str = f"Unsatisfiable: {exc}"
    except Exception as exc:
        error_str = f"{type(exc).__name__}: {exc}"

    return {
        "passed": len(failure_msg) == 0,
        "counterexample": failure_msg[0] if failure_msg else None,
        "error": error_str,
    }


def _run_pbt_groups(
    item: dict[str, Any],
    candidate_path: Path,
    oracle_func,
    function_name: str,
    argument_order: list[str],
    n_cases: int,
    timeout_seconds: float,
) -> tuple[dict[str, Any], str | None]:
    _no_pbt: dict[str, Any] = {
        "pbt_gate_passed": True,
        "pbt_group_pass_rate": 1.0,
        "groups": {},
        "total": 0,
        "passed": 0,
        "pass_rate": 1.0,
        "crash": False,
        "timeout": False,
        "failures": [],
    }
    if n_cases <= 0:
        return _no_pbt, None

    groups_ref = item["tests"].get("pbt_groups")
    strategy_ref = item["tests"].get("hypothesis_strategy")

    pbt_groups: dict[str, Any] = {}
    if groups_ref:
        try:
            mod_name, attr = groups_ref.split(":", 1)
            pbt_groups = getattr(importlib.import_module(mod_name), attr)
        except Exception as exc:
            return _no_pbt, f"PBT groups load error: {type(exc).__name__}: {exc}"
    elif strategy_ref:
        try:
            mod_name, fn_name = strategy_ref.split(":", 1)
            factory = getattr(importlib.import_module(mod_name), fn_name)
            pbt_groups = {"differential": factory}
        except Exception as exc:
            return _no_pbt, f"Strategy load error: {type(exc).__name__}: {exc}"
    else:
        return _no_pbt, None

    group_results: dict[str, dict[str, Any]] = {}
    cases_per_group = max(1, n_cases // len(pbt_groups))
    first_error: str | None = None

    for group_name, factory in pbt_groups.items():
        g = _run_one_pbt_group(
            group_name=group_name,
            strategy_factory=factory,
            candidate_path=candidate_path,
            oracle_func=oracle_func,
            function_name=function_name,
            argument_order=argument_order,
            n_cases=cases_per_group,
            timeout_seconds=timeout_seconds,
        )
        group_results[group_name] = g
        if not g["passed"] and first_error is None:
            first_error = g["counterexample"] or g["error"]

    total_groups = len(group_results)
    passed_groups = sum(1 for g in group_results.values() if g["passed"])
    pbt_gate_passed = passed_groups == total_groups
    pbt_group_pass_rate = passed_groups / total_groups if total_groups else 1.0

    result: dict[str, Any] = {
        "pbt_gate_passed": pbt_gate_passed,
        "pbt_group_pass_rate": round(pbt_group_pass_rate, 6),
        "groups": group_results,
        "total": cases_per_group * total_groups,
        "passed": cases_per_group * passed_groups,
        "pass_rate": pbt_group_pass_rate,
        "crash": False,
        "timeout": False,
        "failures": [{"error": first_error}] if first_error else [],
    }
    return result, first_error


def _run_suite(
    *,
    suite_name: str,
    candidate_path: Path,
    oracle_func,
    function_name: str,
    argument_order: list[str],
    cases: list[dict[str, Any]],
    timeout_seconds: float,
) -> dict[str, Any]:
    details: list[dict[str, Any]] = []
    passed = 0
    crashed = False
    timed_out = False

    for index, case in enumerate(cases):
        inputs = case["input"]
        expected = normalize_value(_expected_for_case(oracle_func, argument_order, case))
        outcome = run_one_case(candidate_path, function_name, argument_order, inputs, timeout_seconds)
        actual = normalize_value(outcome.get("output"))
        ok = outcome["status"] == "ok" and actual == expected
        passed += int(ok)
        crashed = crashed or outcome["status"] == "crash"
        timed_out = timed_out or outcome["status"] == "timeout"
        if not ok and len(details) < 8:
            details.append(
                {
                    "suite": suite_name,
                    "case_index": index,
                    "status": outcome["status"],
                    "input": normalize_value(inputs),
                    "expected": expected,
                    "actual": actual,
                    "error": outcome.get("error"),
                }
            )

    total = len(cases)
    return {
        "total": total,
        "passed": passed,
        "pass_rate": 1.0 if total == 0 else passed / total,
        "crash": crashed,
        "timeout": timed_out,
        "failures": details,
    }


def _get_stress_config(target_complexity: str) -> dict[str, Any] | None:
    normalized = " ".join(target_complexity.lower().split())
    configs: list[tuple[str, dict[str, Any]]] = [
        ("(n + m) log n", {"small_size": 500, "large_size": 5_000, "n_small": 3, "n_large": 3, "ratio_max": 35.0}),
        ("(u + q) log n", {"small_size": 1_000, "large_size": 10_000, "n_small": 3, "n_large": 3, "ratio_max": 35.0}),
        ("alpha(n)", {"small_size": 1_000, "large_size": 10_000, "n_small": 3, "n_large": 3, "ratio_max": 25.0}),
        ("n log n", {"small_size": 1_000, "large_size": 10_000, "n_small": 5, "n_large": 5, "ratio_max": 30.0}),
        ("n + m", {"small_size": 1_000, "large_size": 10_000, "n_small": 3, "n_large": 3, "ratio_max": 20.0}),
        ("o(n)", {"small_size": 1_000, "large_size": 10_000, "n_small": 5, "n_large": 5, "ratio_max": 15.0}),
        ("log n", {"small_size": 10_000, "large_size": 1_000_000, "n_small": 5, "n_large": 5, "ratio_max": 5.0}),
    ]
    for marker, config in configs:
        if marker in normalized:
            return config
    return None


def _complexity_ratio_ok(
    candidate_path: Path,
    function_name: str,
    argument_order: list[str],
    small_cases: list[dict[str, Any]],
    large_cases: list[dict[str, Any]],
    expected_ratio_max: float,
    timeout_seconds: float,
) -> tuple[bool | None, dict[str, Any]]:
    def median_time(cases: list[dict[str, Any]]) -> tuple[float | None, dict[str, Any]]:
        times: list[float] = []
        failures = 0
        timeouts = 0
        for case in cases[:5]:
            t0 = time.perf_counter()
            outcome = run_one_case(candidate_path, function_name, argument_order, case["input"], timeout_seconds)
            elapsed = time.perf_counter() - t0
            if outcome["status"] == "ok":
                times.append(elapsed)
            else:
                failures += 1
                timeouts += int(outcome["status"] == "timeout")
        if not times:
            return None, {"valid_runs": 0, "failures": failures, "timeouts": timeouts}
        return sorted(times)[len(times) // 2], {
            "valid_runs": len(times),
            "failures": failures,
            "timeouts": timeouts,
        }

    small_time, small_meta = median_time(small_cases)
    large_time, large_meta = median_time(large_cases)
    profile: dict[str, Any] = {
        "small_median_seconds": small_time,
        "large_median_seconds": large_time,
        "expected_ratio_max": expected_ratio_max,
        "small": small_meta,
        "large": large_meta,
    }

    if large_meta["timeouts"] or (large_time is None and large_meta["failures"]):
        profile["ratio"] = None
        return False, profile
    if small_time is None or large_time is None or small_time < 1e-6:
        profile["ratio"] = None
        return None, profile

    ratio = large_time / small_time
    profile["ratio"] = ratio
    if small_meta["valid_runs"] < 3 or large_meta["valid_runs"] < 3:
        return None, profile
    return ratio <= expected_ratio_max, profile


def _compute_productivity_score(
    complexity_ratio_ok: bool | None,
    complexity_profile: dict[str, Any] | None,
    pbt_pass_rate: float,
) -> float:
    if complexity_ratio_ok is None:
        efficiency = 0.5
    elif not complexity_ratio_ok:
        efficiency = 0.0
    else:
        ratio = complexity_profile.get("ratio") if complexity_profile else None
        ratio_max = complexity_profile.get("expected_ratio_max", 30.0) if complexity_profile else 30.0
        if ratio is None:
            efficiency = 0.5
        else:
            efficiency = max(0.1, 1.0 - ratio / ratio_max)

    robustness = pbt_pass_rate

    if efficiency == 0.0 or robustness == 0.0:
        return 0.0
    return round(2.0 / (1.0 / efficiency + 1.0 / robustness), 6)


def evaluate_candidate(
    item_id: str,
    candidate_path: str | Path,
    hidden_cases: int | None = None,
    pbt_cases: int = 25,
    timeout_seconds: float = 1.0,
) -> dict[str, Any]:
    item = load_item(item_id)
    candidate = Path(candidate_path).resolve()
    oracle_path = resolve_repo_path(item["oracle"]["reference_solution_path"])
    function_name = item["task"]["function_name"]
    argument_order = item["task"]["arguments"]

    static = analyze_candidate(candidate, item)
    oracle_func = load_function_from_path(oracle_path, function_name)
    public_cases = _load_public_cases(item)
    hidden = generate_cases(item, limit=hidden_cases)

    public_result = _run_suite(
        suite_name="public",
        candidate_path=candidate,
        oracle_func=oracle_func,
        function_name=function_name,
        argument_order=argument_order,
        cases=public_cases,
        timeout_seconds=timeout_seconds,
    )
    hidden_result = _run_suite(
        suite_name="hidden",
        candidate_path=candidate,
        oracle_func=oracle_func,
        function_name=function_name,
        argument_order=argument_order,
        cases=hidden,
        timeout_seconds=timeout_seconds,
    )
    pbt_result, pbt_error = _run_pbt_groups(
        item=item,
        candidate_path=candidate,
        oracle_func=oracle_func,
        function_name=function_name,
        argument_order=argument_order,
        n_cases=pbt_cases,
        timeout_seconds=timeout_seconds,
    )

    oracle_source = oracle_path.read_text(encoding="utf-8")
    candidate_source = candidate.read_text(encoding="utf-8")
    candidate_features = extract_features(candidate_source)
    stored_oracle_features = item.get("oracle", {}).get("oracle_ast_features")
    oracle_features = stored_oracle_features if stored_oracle_features else extract_features(oracle_source)
    known_paradigms = item["oracle"].get("known_valid_paradigms", [])
    genuine_divergence, candidate_paradigms, oracle_paradigms = is_genuine_divergence(
        candidate_features=candidate_features,
        oracle_features=oracle_features,
        known_paradigms=known_paradigms,
    )
    candidate_paradigms, paradigm_evidence = enhance_candidate_paradigms(
        features=candidate_features,
        source=candidate_source,
        base_paradigms=candidate_paradigms,
    )
    if set(candidate_paradigms) != set(oracle_paradigms):
        genuine_divergence = bool(candidate_paradigms and oracle_paradigms)

    complexity_ratio_ok = None
    complexity_profile = None
    stress_config = _get_stress_config(item["oracle"].get("reference_complexity", ""))
    if stress_config:
        small_cases = generate_cases(item, limit=stress_config["n_small"], size_override=stress_config["small_size"])
        large_cases = generate_cases(item, limit=stress_config["n_large"], size_override=stress_config["large_size"])
        complexity_ratio_ok, complexity_profile = _complexity_ratio_ok(
            candidate_path=candidate,
            function_name=function_name,
            argument_order=argument_order,
            small_cases=small_cases,
            large_cases=large_cases,
            expected_ratio_max=stress_config["ratio_max"],
            timeout_seconds=timeout_seconds * 3,
        )

    salieri_overlap = file_similarity(candidate, oracle_path)
    p_dist = compute_paradigm_distance(candidate_features, oracle_features)
    productivity = _compute_productivity_score(
        complexity_ratio_ok=complexity_ratio_ok,
        complexity_profile=complexity_profile,
        pbt_pass_rate=pbt_result["pbt_group_pass_rate"],
    )

    metrics = {
        "public_pass_rate": public_result["pass_rate"],
        "hidden_pass_rate": hidden_result["pass_rate"],
        "pbt_gate_passed": pbt_result["pbt_gate_passed"],
        "pbt_group_pass_rate": pbt_result["pbt_group_pass_rate"],
        "static_violation": not static["ok"],
        "crash": public_result["crash"] or hidden_result["crash"] or pbt_result["crash"],
        "timeout": public_result["timeout"] or hidden_result["timeout"] or pbt_result["timeout"],
        "salieri_overlap": salieri_overlap,
        "paradigm_distance": p_dist,
        "productivity_score": productivity,
        "complexity_ratio_ok": complexity_ratio_ok,
    }
    score = compute_score(metrics)

    # Compute independent metrics profile (5 axes)
    metrics_profile = compute_metrics_profile(
        metrics=metrics,
        complexity_profile=complexity_profile,
        is_genuine_divergence=genuine_divergence,
    )

    return {
        "item_id": item_id,
        "candidate": str(candidate),
        "metrics": metrics,
        "metrics_profile": metrics_profile,
        "score": score,
        "static_checks": static,
        "paradigm_features": candidate_features,
        "oracle_features": oracle_features,
        "pd_classification": {
            "paradigm_distance": p_dist,
            "productivity_score": productivity,
            "originality_score": round(1.0 - salieri_overlap, 6),
            "pd_score": score["pd_score"],
            "candidate_paradigms": candidate_paradigms,
            "oracle_paradigms": oracle_paradigms,
            "is_genuine_divergence": genuine_divergence,
            "known_valid_paradigms": known_paradigms,
            "paradigm_evidence": {
                p: {
                    "confidence": ev.confidence,
                    "decision": ev.decision,
                    "signals": [
                        {"layer": s.layer, "name": s.name, "confidence": s.confidence, "evidence": s.evidence}
                        for s in ev.signals
                    ],
                }
                for p, ev in paradigm_evidence.items()
            },
        },
        "complexity_profile": complexity_profile,
        "suites": {
            "public": public_result,
            "hidden": hidden_result,
            "pbt": pbt_result,
        },
        "pbt_error": pbt_error,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a Python candidate for one TR-CodeBench item.")
    parser.add_argument("--item", required=True, help="Item id, for example trcb-proto-0001.")
    parser.add_argument("--candidate", required=True, help="Path to a Python file exposing solve(...).")
    parser.add_argument("--hidden-cases", type=int, default=None, help="Override number of generated hidden cases.")
    parser.add_argument("--pbt-cases", type=int, default=25, help="Number of Hypothesis-generated examples.")
    parser.add_argument("--timeout", type=float, default=1.0, help="Timeout per test case in seconds.")
    parser.add_argument("--strict-exit", action="store_true", help="Exit non-zero when correctness_score is 0.")
    args = parser.parse_args(argv)

    result = evaluate_candidate(
        item_id=args.item,
        candidate_path=args.candidate,
        hidden_cases=args.hidden_cases,
        pbt_cases=args.pbt_cases,
        timeout_seconds=args.timeout,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.strict_exit and result["score"]["correctness_score"] < 1.0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
