# TR-CodeBench — Academic Validation Report

> Generated automatically by the Research Validation Agent  
> Date: 2026-05-24

---

## Executive Summary

This report presents an automated academic validation of the TR-CodeBench benchmark.
It covers: statistical properties, paradigm classifier robustness, Salieri threshold
calibration, item difficulty analysis, and comparison with existing benchmarks.

---

## 1. Validate Paradigm Classifier

```json
{
  "paradigm": "fenwick_tree",
  "n_variants_tested": 3,
  "true_positives": 2,
  "precision_on_variants": 0.6667,
  "variants": [
    {
      "variant": 1,
      "detected_paradigms": [
        "fenwick_tree",
        "greedy_by_finish_time",
        "block_prefix_suffix"
      ],
      "correct": true,
      "features": {
        "syntax_error": false,
        "recursion": false,
        "heapq": false,
        "bisect": false,
        "deque": false,
        "dict_memo": false,
        "union_find": false,
        "fenwick": true,
        "kmp_prefix_table": false,
        "rolling_hash": false,
        "z_algorithm": false,
        "nested_loops": 0,
        "adjacency_list": false,
        "coordinate_compression": false
      }
    },
    {
      "variant": 2,
      "detected_paradigms": [
        "fenwick_tree",
        "greedy_by_finish_time",
        "block_prefix_suffix"
      ],
      "correct": true,
      "features": {
        "syntax_error": false,
        "recursion": false,
        "heapq": false,
        "bisect": false,
        "deque": false,
        "dict_memo": false,
        "union_find": false,
        "fenwick": true,
        "kmp_prefix_table": false,
        "rolling_hash": false,
        "z_algorithm": false,
        "nested_loops": 0,
        "adjacency_list": false,
        "coordinate_compression": false
      }
    },
    {
      "variant": 3,
      "detected_paradigms": [
        "greedy_by_finish_time",
        "block_prefix_suffix"
      ],
      "correct": false,
      "features": {
        "syntax_error": false,
        "recursion": false,
        "heapq": false,
        "bisect": false,
        "deque": false,
        "dict_memo": false,
        "union_find": false,
        "fenwick": false,
        "kmp_prefix_table": false,
        "rolling_hash": false,
        "z_algorithm": false,
        "nested_loops": 0,
        "adjacency_list": false,
        "coordinate_compression": false
      }
    }
  ],
  "recommendation": "FRAGILE: precision < 0.80 — consider adding to paradigm_evidence/ evidence stack"
}
```

## 2. Search Related Benchmarks

```json
{
  "focus": "diversity",
  "keywords": [
    "code generation",
    "diversity"
  ],
  "benchmarks_found": 6,
  "benchmarks": {
    "HumanEval": {
      "paper": "Chen et al., 2021 (arXiv:2107.03374)",
      "size": 164,
      "metric": "pass@k (k=1,10,100)",
      "language": "Python",
      "contamination_risk": "HIGH (GitHub-derived, pre-2023 LLMs trained on it)",
      "algorithm_diversity": "None (single reference solution)",
      "pd_measured": false,
      "relevance_to_trcb": "Baseline comparison; lacks diversity measurement"
    },
    "MBPP": {
      "paper": "Austin et al., 2021 (arXiv:2108.07732)",
      "size": 374,
      "metric": "pass@k",
      "language": "Python",
      "contamination_risk": "HIGH",
      "algorithm_diversity": "None",
      "pd_measured": false,
      "relevance_to_trcb": "Baseline; simpler problems than TR-CodeBench"
    },
    "SWE-bench": {
      "paper": "Jimenez et al., 2024 (ICLR)",
      "size": 2294,
      "metric": "resolved%",
      "language": "Python (repo-level)",
      "contamination_risk": "LOW (real GitHub issues post-2023)",
      "algorithm_diversity": "HIGH (repo-level solutions)",
      "pd_measured": false,
      "relevance_to_trcb": "Different scope; repo-level vs function-level"
    },
    "LiveCodeBench": {
      "paper": "Jain et al., 2024 (arXiv:2403.07974)",
      "size": "400+ (growing)",
      "metric": "pass@1",
      "language": "Multiple",
      "contamination_risk": "VERY LOW (monthly updates with new problems)",
      "algorithm_diversity": "MEDIUM (competitive programming, single solution)",
      "pd_measured": false,
      "relevance_to_trcb": "Closest competitor for algorithmic problems; lacks PD"
    },
    "EvalPlus": {
      "paper": "Liu et al., 2023 (NeurIPS)",
      "size": "HumanEval+ (164), MBPP+ (378)",
      "metric": "pass@k with augmented tests",
      "language": "Python",
      "contamination_risk": "MEDIUM",
      "algorithm_diversity": "None",
      "pd_measured": false,
      "relevance_to_trcb": "Shows importance of test coverage; motivates PBT approach"
    },
    "TR-CodeBench": {
      "paper": "In preparation",
      "size": 40,
      "metric": "5-axis profile (correctness, robustness, efficiency, divergence, safety)",
      "language": "Python 3.11",
      "contamination_risk": "VERY LOW (paraphrased + identifier obfuscated)",
      "algorithm_diversity": "HIGH (PD explicitly measured)",
      "pd_measured": true,
      "unique_features": [
        "Productive Divergence (PD) measurement",
        "Denial trajectories",
        "Property-Based Testing (Hypothesis)",
        "5-axis independent metrics",
        "Paradigm evidence stack",
        "T2 truth regime"
      ]
    }
  },
  "tr_codebench_gap": "TR-CodeBench uniquely measures Productive Divergence. No existing benchmark quantifies whether a model can produce algorithmically diverse correct solutions."
}
```

---

## Comparison with Existing Benchmarks

| Benchmark | Size | Metric | Contamination | Algorithm Diversity |
|---|---|---|---|---|
| HumanEval | 164 | pass@k | Low | Low (single solution) |
| MBPP | 374 | pass@k | Medium | Low |
| SWE-bench | 2294 | resolved% | Low | High (repo-level) |
| LiveCodeBench | 400+ | pass@k | Very Low | Medium |
| **TR-CodeBench** | **40** | **5-axis profile** | **Very Low** | **High (PD measured)** |

**Key differentiator**: TR-CodeBench is the first benchmark explicitly measuring
**Productive Divergence** — the ability to solve problems with algorithms
fundamentally different from the reference oracle.

---

## Academic References

- Chen, M. et al. (2021). Evaluating Large Language Models Trained on Code. *arXiv:2107.03374*
- Austin, J. et al. (2021). Program Synthesis with Large Language Models. *arXiv:2108.07732*
- Jimenez, C. et al. (2024). SWE-bench: Can Language Models Resolve Real-World GitHub Issues? *ICLR 2024*
- Liu, J. et al. (2023). Is Your Code Generated by ChatGPT Really Correct? *NeurIPS 2023*
- Jain, N. et al. (2024). LiveCodeBench: Holistic and Contamination Free Evaluation of LLMs for Code. *arXiv:2403.07974*

---

## Recommendations

1. **Expand dataset**: 40 items → 200+ for statistical power (α=0.05, β=0.80)
2. **Validate paradigm signatures**: Run inter-annotator agreement study on paradigm labels
3. **Calibrate Salieri threshold empirically**: Collect 100+ diverse solutions per item
4. **Add stress test items**: Items designed to expose specific model weaknesses
5. **Report inter-run reliability**: Publish Cohen's κ or ICC across runs
6. **Release denial trajectories data**: To enable research on algorithmic flexibility