from __future__ import annotations

import argparse
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

try:
    import requests
except ImportError as exc:  # pragma: no cover - exercised by local environment only
    raise SystemExit("Missing dependency: requests. Run: python3.11 -m pip install -e '.[notebook]'") from exc

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is optional when env is already exported
    load_dotenv = None

from .evaluate import _load_public_cases, evaluate_candidate
from .load_items import ROOT, list_item_ids, load_item


FENCE_RE = re.compile(r"```(?:python|py)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
PLAIN_TRAILER_RE = re.compile(r"^\s*(COMPLEXITY|PARADIGM)\s*:", re.IGNORECASE)


def _split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def safe_slug(value: str, max_len: int = 80) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")
    return slug[:max_len] or "value"


def extract_python_code(text: str) -> str:
    blocks = FENCE_RE.findall(text)
    if blocks:
        code_text = max(blocks, key=len).strip()
    else:
        code_text = text.strip()
        markers = [pos for marker in ("def solve", "from ", "import ") if (pos := code_text.find(marker)) >= 0]
        if markers:
            code_text = code_text[min(markers) :]
        kept_lines = []
        for line in code_text.splitlines():
            if PLAIN_TRAILER_RE.match(line):
                break
            kept_lines.append(line)
        code_text = "\n".join(kept_lines).strip()
    return code_text + "\n"


def compact_public_cases(item: dict[str, Any], max_cases: int = 5) -> str:
    cases = _load_public_cases(item)[:max_cases]
    lines: list[str] = []
    for idx, case in enumerate(cases, start=1):
        lines.append(f"Case {idx}:")
        lines.append("input = " + json.dumps(case["input"], ensure_ascii=True))
        lines.append("expected = " + json.dumps(case["expected"], ensure_ascii=True))
    return "\n".join(lines)


def build_t2_prompt(item: dict[str, Any]) -> str:
    task = item["task"]
    constraints = task.get("optimization_constraints", {})
    public_cases = compact_public_cases(item)
    return f"""
You are solving one Python 3.11 coding benchmark item under a T2 truth regime.

ORACLE
- Your code will be executed against public tests, hidden tests, property-based tests, and static import checks.
- Hidden tests and the reference oracle are not shown.

STYLE LATITUDE
- Any correct algorithmic paradigm is allowed if it respects the signature and constraints.

INVENTION LICENSE
- Do not invent APIs, packages, files, network calls, stdin, stdout, or external state.
- Use only the allowed imports.

TASK
Title: {task["title"]}
Statement: {task["statement"]}
Signature: {task["signature"]}
Allowed imports: {task.get("allowed_imports", [])}
Forbidden imports: {task.get("forbidden_imports", [])}
Optimization constraints: {json.dumps(constraints, ensure_ascii=True)}
Known valid paradigms, not exhaustive: {item["oracle"].get("known_valid_paradigms", [])}

PUBLIC TESTS
{public_cases}

OUTPUT RULES
- Return only Python code.
- Define exactly the requested function name: {task["function_name"]}.
- Do not include markdown fences unless you put all code inside one Python fence.
- You may include final Python comments named COMPLEXITY and PARADIGM.
""".strip()


class OpenRouterRunner:
    def __init__(self, args: argparse.Namespace) -> None:
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.http_referer = os.getenv("OPENROUTER_HTTP_REFERER", "").strip()
        self.app_title = os.getenv("OPENROUTER_APP_TITLE", "TR-CodeBench-Proto-100").strip()
        self.models = _split_csv(args.models or os.getenv("OPENROUTER_MODELS", "")) or ["openai/gpt-4o-mini"]
        self.item_ids = self._resolve_item_ids(args.items or os.getenv("OPENROUTER_ITEM_IDS", ""), args.max_items)
        self.n_runs = args.n_runs if args.n_runs is not None else _env_int("OPENROUTER_N_RUNS", 1)
        self.hidden_cases = args.hidden_cases if args.hidden_cases is not None else _env_int("OPENROUTER_HIDDEN_CASES", 30)
        self.pbt_cases = args.pbt_cases if args.pbt_cases is not None else _env_int("OPENROUTER_PBT_CASES", 10)
        self.max_tokens = args.max_tokens if args.max_tokens is not None else _env_int("OPENROUTER_MAX_TOKENS", 1200)
        self.temperature = args.temperature if args.temperature is not None else _env_float("OPENROUTER_TEMPERATURE", 0.2)
        self.request_timeout = args.request_timeout if args.request_timeout is not None else _env_float("OPENROUTER_REQUEST_TIMEOUT", 120.0)
        self.rate_limit_sleep = _env_float("OPENROUTER_RATE_LIMIT_SLEEP", 0.0)
        self.max_workers = args.max_workers if args.max_workers is not None else _env_int("OPENROUTER_MAX_WORKERS", 4)
        self.retries = args.retries if args.retries is not None else _env_int("OPENROUTER_RETRIES", 2)
        self.candidate_timeout = args.candidate_timeout if args.candidate_timeout is not None else _env_float("TRCB_CANDIDATE_TIMEOUT", 1.0)
        self.run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.output_dir = (ROOT / args.output_dir).resolve() if args.output_dir else ROOT / "reports" / "openrouter_runs"
        self.candidate_dir = ROOT / "tmp" / "openrouter_candidates" / self.run_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.candidate_dir.mkdir(parents=True, exist_ok=True)
        self.results_jsonl = self.output_dir / f"openrouter_eval_{self.run_id}.jsonl"
        self.results_csv = self.output_dir / f"openrouter_eval_{self.run_id}.csv"

    def _resolve_item_ids(self, item_ids_raw: str, max_items_arg: str | None) -> list[str]:
        all_item_ids = list_item_ids()
        configured = _split_csv(item_ids_raw)
        if configured:
            item_ids = configured
        else:
            max_items = (max_items_arg or os.getenv("OPENROUTER_MAX_ITEMS", "all")).strip().lower()
            item_ids = all_item_ids if max_items in {"", "all", "*"} else all_item_ids[: int(max_items)]
        unknown = sorted(set(item_ids) - set(all_item_ids))
        if unknown:
            raise ValueError(f"Unknown item ids: {unknown}")
        return item_ids

    def headers(self) -> dict[str, str]:
        if not self.api_key or self.api_key == "sk-or-v1-replace-me":
            raise RuntimeError("Set OPENROUTER_API_KEY in .env before running evaluation.")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.http_referer:
            headers["HTTP-Referer"] = self.http_referer
        if self.app_title:
            headers["X-Title"] = self.app_title
        return headers

    def call_openrouter(self, model: str, prompt: str) -> tuple[str, dict[str, Any], float]:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You return concise, executable Python code for benchmark tasks. No prose outside code.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        start = time.perf_counter()
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers(),
                    json=payload,
                    timeout=self.request_timeout,
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"].get("content") or ""
                return content, data, time.perf_counter() - start
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                last_error = exc
                if status not in {408, 409, 425, 429, 500, 502, 503, 504} or attempt >= self.retries:
                    raise
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_error = exc
                if attempt >= self.retries:
                    raise
            time.sleep(min(2**attempt, 8))
        raise RuntimeError(f"OpenRouter request failed after retries: {last_error}")

    def write_candidate(self, model: str, item_id: str, run_index: int, response_text: str, response_json: dict[str, Any]) -> Path:
        base = f"{safe_slug(model)}__{item_id}__run{run_index}"
        candidate_path = self.candidate_dir / f"{base}.py"
        response_path = self.candidate_dir / f"{base}.response.txt"
        metadata_path = self.candidate_dir / f"{base}.api.json"
        candidate_path.write_text(extract_python_code(response_text), encoding="utf-8")
        response_path.write_text(response_text, encoding="utf-8")
        metadata_path.write_text(json.dumps(response_json, indent=2, sort_keys=True), encoding="utf-8")
        return candidate_path

    def flatten_eval_result(
        self,
        *,
        model: str,
        item_id: str,
        run_index: int,
        candidate_path: Path | None,
        response_json: dict[str, Any] | None,
        latency_seconds: float | None,
        eval_result: dict[str, Any] | None,
        error: str | None,
    ) -> dict[str, Any]:
        usage = (response_json or {}).get("usage") or {}
        score = (eval_result or {}).get("score") or {}
        metrics = (eval_result or {}).get("metrics") or {}
        suites = (eval_result or {}).get("suites") or {}
        public_suite = suites.get("public") or {}
        hidden_suite = suites.get("hidden") or {}
        pbt_suite = suites.get("pbt") or {}
        static_checks = (eval_result or {}).get("static_checks") or {}
        paradigm = (eval_result or {}).get("pd_classification") or {}
        complexity = (eval_result or {}).get("complexity_profile") or {}
        return {
            "run_id": self.run_id,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "item_id": item_id,
            "run_index": run_index,
            "candidate_path": str(candidate_path) if candidate_path else None,
            "api_error": error,
            "latency_seconds": latency_seconds,
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "score": score.get("score"),
            "correctness_score": score.get("correctness_score"),
            "optimization_score": score.get("optimization_score"),
            "pd_score": score.get("pd_score"),
            "paradigm_distance": paradigm.get("paradigm_distance"),
            "productivity_score": paradigm.get("productivity_score"),
            "originality_score": paradigm.get("originality_score"),
            "hallucination_flag": score.get("hallucination_flag"),
            "public_pass_rate": metrics.get("public_pass_rate"),
            "hidden_pass_rate": metrics.get("hidden_pass_rate"),
            "pbt_pass_rate": metrics.get("pbt_pass_rate"),
            "salieri_overlap": metrics.get("salieri_overlap"),
            "genuine_divergence": paradigm.get("is_genuine_divergence"),
            "complexity_ratio_ok": metrics.get("complexity_ratio_ok"),
            "complexity_ratio": complexity.get("ratio"),
            "static_violation": metrics.get("static_violation"),
            "crash": metrics.get("crash"),
            "timeout": metrics.get("timeout"),
            "public_passed": public_suite.get("passed"),
            "public_total": public_suite.get("total"),
            "hidden_passed": hidden_suite.get("passed"),
            "hidden_total": hidden_suite.get("total"),
            "pbt_passed": pbt_suite.get("passed"),
            "pbt_total": pbt_suite.get("total"),
            "pbt_error": (eval_result or {}).get("pbt_error"),
            "candidate_paradigms": ",".join(paradigm.get("candidate_paradigms") or []),
            "oracle_paradigms": ",".join(paradigm.get("oracle_paradigms") or []),
            "static_violations": ";".join(static_checks.get("violations") or []),
        }

    def run_one_experiment(self, job: tuple[str, str, int]) -> dict[str, Any]:
        model, item_id, run_index = job
        candidate_path = None
        response_json = None
        latency_seconds = None
        eval_result = None
        error = None
        try:
            if self.rate_limit_sleep > 0:
                time.sleep(self.rate_limit_sleep)
            prompt = build_t2_prompt(load_item(item_id))
            response_text, response_json, latency_seconds = self.call_openrouter(model, prompt)
            candidate_path = self.write_candidate(model, item_id, run_index, response_text, response_json)
            eval_result = evaluate_candidate(
                item_id=item_id,
                candidate_path=candidate_path,
                hidden_cases=self.hidden_cases,
                pbt_cases=self.pbt_cases,
                timeout_seconds=self.candidate_timeout,
            )
        except Exception as exc:  # keep partial runs analyzable
            error = f"{type(exc).__name__}: {exc}"

        return self.flatten_eval_result(
            model=model,
            item_id=item_id,
            run_index=run_index,
            candidate_path=candidate_path,
            response_json=response_json,
            latency_seconds=latency_seconds,
            eval_result=eval_result,
            error=error,
        )

    def run(self) -> list[dict[str, Any]]:
        jobs = [(model, item_id, run_index) for model in self.models for item_id in self.item_ids for run_index in range(self.n_runs)]
        print(f"Project root: {ROOT}")
        print(f"Run id: {self.run_id}")
        print(f"Models: {', '.join(self.models)}")
        print(f"Items: {', '.join(self.item_ids)}")
        print(f"Planned requests: {len(jobs)}; max_workers={self.max_workers}; retries={self.retries}")
        print(f"JSONL output: {self.results_jsonl}")

        rows: list[dict[str, Any]] = []
        write_lock = Lock()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_job = {executor.submit(self.run_one_experiment, job): job for job in jobs}
            for completed, future in enumerate(as_completed(future_to_job), start=1):
                model, item_id, run_index = future_to_job[future]
                try:
                    row = future.result()
                except Exception as exc:
                    row = self.flatten_eval_result(
                        model=model,
                        item_id=item_id,
                        run_index=run_index,
                        candidate_path=None,
                        response_json=None,
                        latency_seconds=None,
                        eval_result=None,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                rows.append(row)
                with write_lock:
                    with self.results_jsonl.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps(row, sort_keys=True) + "\n")
                status = "ERROR" if row.get("api_error") else f"score={row.get('score')}"
                print(f"[{completed}/{len(jobs)}] {model} {item_id} run={run_index}: {status}", flush=True)

        self._write_csv(rows)
        print(f"CSV output:   {self.results_csv}")
        return rows

    def _write_csv(self, rows: list[dict[str, Any]]) -> None:
        import csv

        if not rows:
            return
        fieldnames = list(rows[0].keys())
        with self.results_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TR-CodeBench OpenRouter evaluation and write JSONL/CSV results.")
    parser.add_argument("--models", help="Comma-separated OpenRouter model ids. Defaults to OPENROUTER_MODELS.")
    parser.add_argument("--items", help="Comma-separated TR-CodeBench item ids. Defaults to OPENROUTER_ITEM_IDS or max-items.")
    parser.add_argument("--max-items", help="Use first N items, or 'all'. Defaults to OPENROUTER_MAX_ITEMS.")
    parser.add_argument("--n-runs", type=int, help="Repeated attempts per model and item.")
    parser.add_argument("--hidden-cases", type=int, help="Generated hidden cases per item.")
    parser.add_argument("--pbt-cases", type=int, help="Hypothesis examples per item.")
    parser.add_argument("--candidate-timeout", type=float, help="Timeout per candidate test case.")
    parser.add_argument("--max-tokens", type=int, help="OpenRouter max_tokens.")
    parser.add_argument("--temperature", type=float, help="OpenRouter temperature.")
    parser.add_argument("--request-timeout", type=float, help="OpenRouter request timeout in seconds.")
    parser.add_argument("--max-workers", type=int, help="Parallel OpenRouter workers.")
    parser.add_argument("--retries", type=int, help="Retries for transient OpenRouter/network failures.")
    parser.add_argument("--run-id", help="Override output run id.")
    parser.add_argument("--output-dir", help="Output directory, relative to repo root or absolute.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if load_dotenv is not None:
        load_dotenv(ROOT / ".env")
    runner = OpenRouterRunner(parse_args(argv))
    runner.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
