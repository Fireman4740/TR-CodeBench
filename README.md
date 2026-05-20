# TR-CodeBench-Proto-100

Executable prototype for a Python-only benchmark under a T2 Truth Regime: high strategy latitude, low factual-invention license, and strict executable oracles.

This v0.1 scaffold contains 10 end-to-end algorithmic items. It is designed to prove the pipeline before scaling to 100 tasks.

## What Is Included

- 10 curated JSON items in `datasets/curated/`
- 10 reference oracles in `oracles/`
- public pytest cases in `tests/public/`
- generated hidden tests in `src/trcodebench/hidden_tests.py`
- Hypothesis strategies in `strategies/`
- a local evaluation harness with timeout, static import checks, hidden pass rate, PBT pass rate, Salieri-style shingle overlap, AST features, and v0 scoring
- prompt templates and a dataset quality report template

Current items:

| ID                | Topic                    | Required shape       |
| ----------------- | ------------------------ | -------------------- |
| `trcb-proto-0001` | LIS                      | `O(n log n)`         |
| `trcb-proto-0002` | positive shortest path   | `O((n + m) log n)`   |
| `trcb-proto-0003` | interval scheduling      | `O(n log n)`         |
| `trcb-proto-0004` | shortest target subarray | `O(n)`               |
| `trcb-proto-0005` | union-find connectivity  | near-linear          |
| `trcb-proto-0006` | exact string matching    | `O(n + m)` preferred |
| `trcb-proto-0007` | sliding window maximum   | `O(n)`               |
| `trcb-proto-0008` | longest path in DAG      | `O(n + m)`           |
| `trcb-proto-0009` | point updates/range sums | `O(log n)` per op    |
| `trcb-proto-0010` | heap scheduling          | `O(n log n)`         |

## Install

```bash
python3.11 -m pip install -e ".[dev]"
```

Run the repository tests:

```bash
python3.11 -m pytest
```

## Evaluate A Candidate

Create a Python file exposing the required function, for example `candidates/example_lis.py`:

```python
from bisect import bisect_left


def solve(nums: list[int]) -> int:
    tails = []
    for value in nums:
        index = bisect_left(tails, value)
        if index == len(tails):
            tails.append(value)
        else:
            tails[index] = value
    return len(tails)
```

Evaluate it:

```bash
python3.11 -m trcodebench.evaluate --item trcb-proto-0001 --candidate candidates/example_lis.py
```

For faster smoke tests:

```bash
python3.11 -m trcodebench.evaluate --item trcb-proto-0001 --candidate candidates/example_lis.py --hidden-cases 10 --pbt-cases 5
```

## OpenRouter Notebook Smoke Test

For live model runs through OpenRouter, copy `.env.example` to `.env`, set `OPENROUTER_API_KEY`, and optionally edit `OPENROUTER_MODELS`.

Install notebook dependencies:

```bash
python3.11 -m pip install -e ".[notebook]"
python3.11 -m ipykernel install --user --name tr-codebench-py311 --display-name "TR-CodeBench Python 3.11"
```

Then open:

```bash
jupyter lab notebooks/openrouter_real_world_eval.ipynb
```

The notebook calls OpenRouter, writes temporary candidate files under `tmp/openrouter_candidates/`, evaluates them with the local harness, and saves run outputs under `reports/openrouter_runs/`.

For a non-interactive run, use the Python 3.11 nbconvert module directly:

```bash
python3.11 -m nbconvert --to notebook --execute notebooks/openrouter_real_world_eval.ipynb \
  --output openrouter_real_world_eval.executed.ipynb \
  --output-dir reports/openrouter_runs \
  --ExecutePreprocessor.kernel_name=tr-codebench-py311
```

To regenerate plots from an existing JSONL without new API calls:

```bash
OPENROUTER_SKIP_LIVE=1 \
OPENROUTER_RESULTS_JSONL=reports/openrouter_runs/openrouter_eval_YYYYMMDDTHHMMSSZ.jsonl \
python3.11 -m nbconvert --to notebook --execute notebooks/openrouter_real_world_eval.ipynb \
  --output openrouter_real_world_eval.analysis.ipynb \
  --output-dir reports/openrouter_runs \
  --ExecutePreprocessor.kernel_name=tr-codebench-py311
```

## Scoring V0.2

The evaluator reports:

- `correctness_score`: 1 only when all public and hidden tests pass
- `pbt_pass_rate`: pass rate from Hypothesis differential testing (candidate vs oracle via `@given`)
- `optimization_score`: 1 when complexity stress test passes (`complexity_ratio_ok = True`); 0 on failure or timeout
- `pd_score`: continuous productive-divergence score — see formula below
- `salieri_overlap`: normalized 5-token shingle Jaccard similarity with the oracle
- `paradigm_distance`: cosine distance between candidate and oracle AST feature vectors
- `hallucination_flag`: static violation, crash, or hidden-test failure

Score formula:

```text
pd_score = HM(paradigm_distance, productivity_score, 1 − salieri_overlap)
           if correctness_score = 1 AND optimization_score = 1
              AND salieri_overlap ≤ 0.70 AND paradigm_distance ≥ 0.20
           else 0

score = 0.50 × correctness_score
      + 0.20 × pbt_pass_rate
      + 0.15 × optimization_score
      + 0.15 × pd_score
      − 0.25 × hallucination_flag
      capped at 0.60 when complexity_ratio_ok = False (explicit constraint violation)
```

Thresholds: `SALIERI_MEMORISATION_THRESHOLD = 0.70`, `PARADIGM_COSMETIC_THRESHOLD = 0.20`.

## Add An Item

1. Add `datasets/curated/trcb-proto-XXXX.json` matching `schemas/item.schema.json`.
2. Add an oracle in `oracles/trcb_proto_XXXX.py`.
3. Add public cases in `tests/public/trcb_proto_XXXX_test.py`.
4. Add or reuse a Hypothesis strategy in `strategies/`.
5. Register a hidden-case generator in `src/trcodebench/hidden_tests.py`.
6. Run `pytest`.

## Scaling To 100 Items

Recommended expansion order:

1. harden the 10 parametric items and evaluation reports
2. add 30 more parametric algorithmic tasks
3. add 25 isolated functions from real Python repositories as standalone tasks
4. add 20 optimization/refactoring PR-derived tasks
5. add 10 recent/post-cutoff tasks
6. add 5 honeypots outside the main score

Keep oracle code, hidden tests, and source metadata separated from prompts shown to evaluated models.

## Limitations

- The process timeout is a reliability guard, not a secure sandbox.
- Hidden tests are generated locally and are not encrypted in this v0.1 scaffold.
- Static API checks are AST heuristics, not a full policy engine.
- Optimization scoring is binary in v0 and should be replaced by calibrated stress tests for v0.2.

V0.2
./scripts/run_openrouter_eval.sh \
 --max-items all \
 --n-runs 1 \
 --hidden-cases 30 \
 --pbt-cases 10 \
 --max-workers 10
