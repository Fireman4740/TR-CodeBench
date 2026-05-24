# TR-CodeBench

Executable prototype for a Python-only benchmark under a **T2 Truth Regime**: high strategy latitude, low factual-invention license, and strict executable oracles. The goal is to separate *memorisation* from *structural understanding* by measuring **Productive Divergence (PD)** — correct solutions that use an algorithmic paradigm genuinely distinct from the reference oracle, under an enforced complexity regime.

The dataset currently holds **40 parametric algorithmic items** (`trcb-proto-0001` … `trcb-proto-0040`), each with a sealed oracle, public + hidden tests, a Hypothesis strategy, declared valid paradigms, and **denial constraints** for multi-step paradigm elicitation.

> See [`docs/SPEC.md`](docs/SPEC.md) for the full technical specification, scoring formulas, run results, and roadmap.

## What Is Included

- **40 curated JSON items** in `datasets/curated/` (schema: `schemas/item.schema.json`)
- **40 reference oracles** in `oracles/`
- **40 public pytest suites** in `tests/public/` + unit tests in `tests/unit/`
- generated hidden tests in `src/trcodebench/hidden_tests.py`
- Hypothesis strategies in `strategies/` (per family)
- a local evaluation harness (`src/trcodebench/`) with: process timeout, static import/API checks, hidden pass rate, PBT pass rate, empirical complexity stress test, Salieri shingle overlap, AST paradigm features, a **multi-layer paradigm-evidence stack** (`paradigm_evidence/`), and a **5-axis metrics profile**
- a **denial-trajectory engine** (`src/trcodebench/denial/`) that re-prompts a model under successive forbidden-paradigm constraints to elicit multiple distinct valid solutions
- an OpenRouter runner (`openrouter_runner.py`) + notebooks for live model evaluation and analysis
- aggregation/annotation scripts in `scripts/`, prompt templates in `prompts/`, and a dataset quality report template in `reports/`

### Item families (40 items)

| Family                | Count | Example item                                      |
| --------------------- | ----- | ------------------------------------------------- |
| dynamic_programming   | 6     | `0001` LIS, `0016` edit distance, `0020` knapsack |
| graph (+ graph_dp)    | 7     | `0002` Dijkstra, `0021` topo-sort, `0023` MST     |
| sorting               | 5     | `0011` inversions, `0012` quickselect, `0015` k-merge |
| string (+ strings)    | 6     | `0006` KMP, `0026` longest palindrome, `0028` LRS |
| data_structure(s)     | 7     | `0005` union-find, `0009` Fenwick, `0031` LRU     |
| math                  | 5     | `0036` modpow, `0037` sieve, `0039` convex hull   |
| arrays / intervals / scheduling | 4 | `0004` min subarray, `0003` intervals, `0010` jobs |

The full per-item table (titles, target complexity, known valid paradigms) lives in [`docs/SPEC.md` §6](docs/SPEC.md). Item titles are paraphrased and identifiers obfuscated as a partial anti-contamination measure.

## Install

> ⚠️ **Known blocker:** `pyproject.toml` is currently empty (0 bytes). The editable install below will not declare dependencies or extras until it is populated — see [Status & Known Issues](#status--known-issues). Until then, install the runtime dependencies manually.

Intended install (once `pyproject.toml` is restored):

```bash
python3.11 -m pip install -e ".[dev]"
```

Manual fallback for now:

```bash
python3.11 -m pip install pytest hypothesis jsonschema requests psutil python-dotenv
# notebook extras: jupyterlab matplotlib pandas ipykernel nbconvert
```

The harness expects **Python 3.11**. Run the repository tests (set `PYTHONPATH=src` if not installed as a package):

```bash
PYTHONPATH=src python3.11 -m pytest
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

On WSL, run the setup commands from the repository root:

```bash
cd /mnt/f/IA/TR-CodeBench
sed -i 's/\r$//' scripts/run_openrouter_eval.sh
chmod +x scripts/run_openrouter_eval.sh
python3.11 -m pip install -e ".[notebook]"
cp -n .env.example .env
```

Then edit `.env`:

```bash
nano .env
```

Set `OPENROUTER_API_KEY` and keep `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`. Do not leave `OPENROUTER_BASE_URL` empty; the runner now falls back to the default, but the explicit value makes the configuration easier to audit.

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

To launch the shell evaluation script from WSL:

```bash
./scripts/run_openrouter_eval.sh \
  --max-items all \
  --n-runs 1 \
  --hidden-cases 30 \
  --pbt-cases 10 \
  --max-workers 10
```

For a quick one-item smoke test before the full run:

```bash
./scripts/run_openrouter_eval.sh \
  --max-items 1 \
  --max-workers 1
```

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

## Scoring — 5-axis metrics profile (primary)

Since v0.3 the evaluator reports **five independent axes** (`src/trcodebench/metrics_profile.py`) instead of a single composite score. Each axis is interpretable on its own and aggregated separately (means exclude `null`):

| Axis            | Scale            | Meaning                                              |
| --------------- | ---------------- | --------------------------------------------------- |
| `correctness`   | 0 / 1            | all public **and** hidden tests pass                |
| `robustness`    | [0, 1]           | `0.7·pbt_gate + 0.3·pbt_group_pass_rate`            |
| `efficiency`    | [0, 1] or `null` | complexity-regime compliance (continuous, from the empirical stress ratio); `null` if correctness fails |
| `divergence`    | [0, 1] or `null` | productive divergence vs oracle; `null` if correctness fails |
| `safety`        | 0 / 1            | no static violation, crash, or hidden-test failure  |

`divergence` is gated: it is `0` unless `salieri_overlap ≤ 0.70` **and** `paradigm_distance ≥ 0.20`; otherwise `HM(paradigm_distance, 1 − salieri_overlap)`, with a ×1.2 bonus (capped at 1.0) when the paradigm-evidence stack confirms genuine divergence. Thresholds: `SALIERI_MEMORISATION_THRESHOLD = 0.70`, `PARADIGM_COSMETIC_THRESHOLD = 0.20`.

### Composite score (DEPRECATED)

`compute_score()` in `scoring.py` still returns the legacy weighted composite for backward compatibility, flagged with `"score_deprecated": True`:

```text
score = 0.50 × correctness + 0.20 × robustness + 0.15 × optimization + 0.15 × pd_score
      − 0.25 × hallucination_flag        (clamped to [0,1], capped at 0.60 if complexity fails)
```

New analysis should use `metrics_profile`, not this composite. See [`docs/SPEC.md` §5](docs/SPEC.md) for the complete specification.

## Denial trajectories (multi-step PD)

Single-shot PD only measures divergence from *one* oracle. The denial engine (`src/trcodebench/denial/`) instead re-prompts a model on the same item under successive **forbidden-paradigm / forbidden-construct constraints** (declared per item in `denial_constraints`), then verifies each solution still passes correctness *and* honours the constraint. It reports `trajectory_depth`, `denial_pass_rate`, `unique_valid_paradigms`, `valid_strategy_switches`, and `pd_confirmed` (≥ 2 distinct valid paradigms). This probes the *solution space* a model can reach, not just its distance from the reference.

## Add An Item

1. Add `datasets/curated/trcb-proto-XXXX.json` matching `schemas/item.schema.json` — including `task` (title, statement, signature, allowed/forbidden imports, optimization constraints), `oracle` (path, complexities, `known_valid_paradigms`, `oracle_ast_features`), `tests`, `anti_contamination`, `scoring`, and `denial_constraints`.
2. Add an oracle in `oracles/trcb_proto_XXXX.py`.
3. Add public cases in `tests/public/trcb_proto_XXXX_test.py`.
4. Add or reuse a Hypothesis strategy in `strategies/` (wire it via `tests.hypothesis_strategy` and `tests.pbt_groups`).
5. Register a hidden-case generator / size profile in `src/trcodebench/hidden_tests.py`.
6. Pre-compute `oracle_ast_features` with `python scripts/annotate_oracle_features.py`.
7. Run `PYTHONPATH=src pytest` (the dataset-integrity test verifies counts, paths, and oracle callability).

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

- The process timeout is a reliability guard, not a secure sandbox (no network/fs isolation, no cgroups/seccomp).
- Hidden tests and oracles are stored in plaintext; separation from model-visible prompts relies on developer discipline.
- Static API checks are AST heuristics, not a full policy engine.
- Anti-contamination is partial: `salieri_overlap` detects oracle copying, not memorisation from the training corpus. There are no post-cutoff items yet.
- The complexity stress test has not yet been confronted with a real naive solution in a live run (`complexity_ratio_ok` was `True` for ~100% of measured runs) — naive baselines now exist in `candidates/` to validate the discriminant.

## Status & Known Issues

- **`pyproject.toml` is empty (0 bytes)** — the editable install and console entry points are broken until it is restored. The `egg-info` reports version `0.0.0`. This is the top-priority fix.
- **Docs lag the code** — this README and `docs/SPEC.md` are being realigned with the 40-item dataset and the `denial` / `paradigm_evidence` / `metrics_profile` modules.
- **Family names are inconsistent** in item JSON: `data_structure`/`data_structures`, `string`/`strings`, `graph`/`graph_dp` should be normalised.
- **Schema drift**: `schemas/item.schema.json` names `oracle_paradigm_features`, but items store `oracle_ast_features` + `oracle_detected_paradigms`.
- **`reports/.DS_Store`** is tracked and should be removed and git-ignored.
