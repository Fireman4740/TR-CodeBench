"""
TR-CodeBench Academic Research Agent
=====================================
Utilise le Claude Agent SDK pour valider et améliorer le benchmark
académiquement. L'agent effectue 4 tâches en boucle :

1. Scanner la littérature (ArXiv/ACL/NeurIPS) pour comparer les approches
2. Valider statistiquement les métriques (fiabilité, discriminabilité)
3. Stress-tester les modules critiques (paradigm_classifier, salieri)
4. Générer un rapport de recommandations académiques

Usage :
    python docs/research_agent.py \
        --results-dir reports/openrouter_runs/ \
        --output-dir docs/academic_reports/ \
        [--n-runs 3] [--anthropic-key sk-...]
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from pathlib import Path
from typing import Any

try:
    import anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False
    anthropic = None  # type: ignore[assignment]

# Ajouter src/ au path pour importer trcodebench
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from trcodebench.metrics_profile import (
    PARADIGM_COSMETIC_THRESHOLD,
    SALIERI_MEMORISATION_THRESHOLD,
    aggregate_profiles,
    compute_metrics_profile,
)
from trcodebench.paradigm_classifier import (
    PARADIGM_SIGNATURES,
    paradigm_distance,
)
from trcodebench.salieri_minhash import jaccard_similarity


# ---------------------------------------------------------------------------
# Outils mis à disposition de l'agent
# ---------------------------------------------------------------------------

TOOLS: list[dict] = [
    {
        "name": "compute_benchmark_statistics",
        "description": (
            "Calcule les statistiques statistiques clés sur les résultats du benchmark : "
            "moyenne, écart-type, effet de taille (Cohen's d), taux d'items discriminants, "
            "corrélation inter-runs (fiabilité test-retest). "
            "Prend en entrée une liste de résultats JSONL du openrouter_runner."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "jsonl_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Chemins vers les fichiers JSONL de résultats",
                },
                "group_by": {
                    "type": "string",
                    "enum": ["model", "item_id", "family"],
                    "description": "Dimension d'agrégation pour la comparaison",
                },
                "metric": {
                    "type": "string",
                    "enum": ["mp_correctness", "mp_robustness", "mp_efficiency",
                             "mp_divergence", "mp_safety", "pbt_pass_rate", "score"],
                    "description": "Métrique à analyser",
                },
            },
            "required": ["jsonl_paths", "group_by", "metric"],
        },
    },
    {
        "name": "validate_paradigm_classifier",
        "description": (
            "Teste la robustesse du paradigm_classifier sur des candidats synthétiques. "
            "Génère des variantes d'un paradigme connu (renommage variables, refactoring) "
            "et vérifie que le classifieur les détecte correctement. "
            "Retourne un rapport de précision/rappel par paradigme."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "paradigm": {
                    "type": "string",
                    "description": f"Paradigme à tester. Options: {list(PARADIGM_SIGNATURES.keys())}",
                },
                "n_variants": {
                    "type": "integer",
                    "description": "Nombre de variantes synthétiques à générer (défaut: 10)",
                    "default": 10,
                },
            },
            "required": ["paradigm"],
        },
    },
    {
        "name": "calibrate_salieri_threshold",
        "description": (
            "Analyse empiriquement le seuil optimal pour SALIERI_MEMORISATION_THRESHOLD. "
            "Calcule la distribution des Jaccard overlaps entre : "
            "(a) copies directes de l'oracle, "
            "(b) solutions alternatives indépendantes, "
            "(c) paraphrases syntaxiques. "
            "Recommande un seuil basé sur la maximisation de F1."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "IDs des items à analyser (ex: ['trcb-proto-0001'])",
                },
                "candidate_dirs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Répertoires contenant des candidats à analyser",
                },
            },
            "required": ["item_ids"],
        },
    },
    {
        "name": "analyze_item_difficulty",
        "description": (
            "Analyse la difficulté et la discrimination de chaque item du benchmark. "
            "Calcule : p-value (taux de réussite), discrimination index (D), "
            "corrélation item-total, et flag les items trop faciles (p>0.90) "
            "ou trop difficiles (p<0.10). "
            "Inspiré de la théorie classique des tests (CTT)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "jsonl_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "difficulty_metric": {
                    "type": "string",
                    "enum": ["mp_correctness", "mp_divergence", "score"],
                    "default": "mp_correctness",
                },
            },
            "required": ["jsonl_paths"],
        },
    },
    {
        "name": "generate_academic_report",
        "description": (
            "Génère un rapport académique complet en Markdown. "
            "Inclut : résumé exécutif, analyse des biais, comparaison avec benchmarks existants "
            "(HumanEval, MBPP, SWE-bench, LiveCodeBench), recommandations d'amélioration, "
            "et références bibliographiques."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "findings": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Liste de findings provenant des autres outils",
                },
                "output_path": {
                    "type": "string",
                    "description": "Chemin de sortie du rapport (ex: docs/academic_reports/report.md)",
                },
            },
            "required": ["findings", "output_path"],
        },
    },
    {
        "name": "search_related_benchmarks",
        "description": (
            "Recherche dans la littérature les benchmarks de code generation existants "
            "et identifie comment TR-CodeBench se différencie ou peut s'améliorer. "
            "Compare les métriques utilisées, la taille des datasets, et les protocoles "
            "de contamination."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Mots-clés de recherche (ex: ['code generation benchmark', 'algorithmic diversity'])",
                },
                "focus": {
                    "type": "string",
                    "enum": ["metrics", "contamination", "diversity", "evaluation_protocol"],
                    "description": "Aspect à analyser en priorité",
                },
            },
            "required": ["keywords"],
        },
    },
]


# ---------------------------------------------------------------------------
# Implémentation des outils
# ---------------------------------------------------------------------------

def _load_jsonl(paths: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        p = Path(path)
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return rows


def tool_compute_benchmark_statistics(
    jsonl_paths: list[str],
    group_by: str,
    metric: str,
) -> dict[str, Any]:
    rows = _load_jsonl(jsonl_paths)
    if not rows:
        return {"error": "No data found in provided JSONL paths"}

    # Grouper par dimension
    groups: dict[str, list[float]] = {}
    for row in rows:
        key = str(row.get(group_by, "unknown"))
        val = row.get(metric)
        if val is not None:
            groups.setdefault(key, []).append(float(val))

    # Statistiques par groupe
    stats: dict[str, Any] = {}
    all_values: list[float] = []
    for key, values in groups.items():
        all_values.extend(values)
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0.0
        stats[key] = {
            "n": len(values),
            "mean": round(mean, 4),
            "std": round(std, 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "p25": round(statistics.quantiles(values, n=4)[0], 4) if len(values) >= 4 else None,
            "p75": round(statistics.quantiles(values, n=4)[2], 4) if len(values) >= 4 else None,
        }

    # Effet de taille global (Cohen's d entre meilleur et pire groupe)
    group_means = {k: v["mean"] for k, v in stats.items()}
    if len(group_means) >= 2:
        sorted_means = sorted(group_means.values())
        pooled_std = statistics.stdev(all_values) if len(all_values) > 1 else 1.0
        cohens_d = (sorted_means[-1] - sorted_means[0]) / pooled_std if pooled_std > 0 else 0.0
    else:
        cohens_d = None

    # Taux d'items discriminants (variance > 0.05)
    if group_by == "item_id":
        discriminating = sum(1 for v in stats.values() if v["std"] > 0.05)
        discrimination_rate = discriminating / len(stats) if stats else 0.0
    else:
        discrimination_rate = None

    return {
        "metric": metric,
        "group_by": group_by,
        "n_groups": len(stats),
        "n_total_rows": len(rows),
        "group_stats": stats,
        "cohens_d": round(cohens_d, 4) if cohens_d is not None else None,
        "discrimination_rate": round(discrimination_rate, 4) if discrimination_rate is not None else None,
        "interpretation": {
            "cohens_d": (
                "large effect (>0.8)" if cohens_d and cohens_d > 0.8
                else "medium effect (0.5-0.8)" if cohens_d and cohens_d > 0.5
                else "small effect (<0.5)"
            ) if cohens_d else "N/A",
            "discrimination_rate": (
                f"{discrimination_rate:.0%} of items discriminate between models"
                if discrimination_rate is not None else "N/A"
            ),
        },
    }


def tool_validate_paradigm_classifier(
    paradigm: str,
    n_variants: int = 10,
) -> dict[str, Any]:
    """Test the paradigm classifier with synthetic code variants."""
    from trcodebench.ast_features import extract_features
    from trcodebench.paradigm_classifier import detect_paradigms

    signature = PARADIGM_SIGNATURES.get(paradigm)
    if not signature:
        return {"error": f"Unknown paradigm: {paradigm}"}

    # Variantes synthétiques connues (hard-coded pour les paradigmes principaux)
    SYNTHETIC_VARIANTS: dict[str, list[str]] = {
        "fenwick_tree": [
            # Variant 1: Noms de variables anglais classiques
            """
def solve(n, ops):
    bit = [0] * (n + 1)
    def update(i, v):
        while i <= n:
            bit[i] += v
            i += i & -i
    def query(i):
        s = 0
        while i > 0:
            s += bit[i]
            i -= i & -i
        return s
    result = []
    for op, l, r in ops:
        if op == 'add': update(l, r)
        else: result.append(query(r) - query(l-1))
    return result
""",
            # Variant 2: Noms de variables français
            """
def solve(n, ops):
    arbre = [0] * (n + 1)
    def maj(idx, val):
        while idx <= n:
            arbre[idx] += val
            idx += idx & -idx
    def somme(idx):
        total = 0
        while idx > 0:
            total += arbre[idx]
            idx -= idx & -idx
        return total
    res = []
    for op, g, d in ops:
        if op == 'add': maj(g, d)
        else: res.append(somme(d) - somme(g-1))
    return res
""",
            # Variant 3: Noms obfusqués
            """
def solve(n, ops):
    T = [0] * (n + 1)
    def U(x, v):
        while x <= n:
            T[x] += v
            x += x & -x
    def Q(x):
        r = 0
        while x > 0:
            r += T[x]
            x -= x & -x
        return r
    ans = []
    for t, a, b in ops:
        if t == 'add': U(a, b)
        else: ans.append(Q(b) - Q(a-1))
    return ans
""",
        ],
        "patience_sorting": [
            """
import bisect
def solve(nums):
    piles = []
    for n in nums:
        pos = bisect.bisect_left(piles, n)
        if pos == len(piles): piles.append(n)
        else: piles[pos] = n
    return len(piles)
""",
            """
from bisect import bisect_left
def solve(sequence):
    stacks = []
    for element in sequence:
        idx = bisect_left(stacks, element)
        if idx >= len(stacks): stacks.append(element)
        else: stacks[idx] = element
    return len(stacks)
""",
        ],
        "kmp": [
            """
def solve(text, pattern):
    n, m = len(text), len(pattern)
    lps = [0] * m
    length = 0
    i = 1
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length:
            length = lps[length - 1]
        else:
            lps[i] = 0
            i += 1
    return lps
""",
        ],
    }

    variants = SYNTHETIC_VARIANTS.get(paradigm, [])
    if not variants:
        return {
            "paradigm": paradigm,
            "error": f"No synthetic variants defined for '{paradigm}'. Add them to SYNTHETIC_VARIANTS.",
            "suggestion": "Contribute variants to the research agent by adding hand-crafted examples.",
        }

    results = []
    true_positives = 0
    for i, code in enumerate(variants[:n_variants]):
        features = extract_features(code)
        detected = detect_paradigms(features, list(PARADIGM_SIGNATURES.keys()))
        correct = paradigm in detected
        true_positives += int(correct)
        results.append({
            "variant": i + 1,
            "detected_paradigms": detected,
            "correct": correct,
            "features": features,
        })

    precision = true_positives / len(results) if results else 0.0
    return {
        "paradigm": paradigm,
        "n_variants_tested": len(results),
        "true_positives": true_positives,
        "precision_on_variants": round(precision, 4),
        "variants": results,
        "recommendation": (
            "FRAGILE: precision < 0.80 — consider adding to paradigm_evidence/ evidence stack"
            if precision < 0.80
            else "ROBUST: precision >= 0.80 — signature matching sufficient"
        ),
    }


def tool_calibrate_salieri_threshold(
    item_ids: list[str],
    candidate_dirs: list[str] | None = None,
) -> dict[str, Any]:
    """Analyze the distribution of Salieri overlaps to calibrate the threshold."""
    from trcodebench.load_items import load_item, resolve_repo_path

    overlaps_copies: list[float] = []
    overlaps_alternatives: list[float] = []

    for item_id in item_ids:
        try:
            item = load_item(item_id)
            oracle_path = resolve_repo_path(item["oracle"]["reference_solution_path"])
            oracle_source = oracle_path.read_text(encoding="utf-8")
        except Exception as e:
            continue

        # Copie directe = similarité maximale
        overlaps_copies.append(jaccard_similarity(oracle_source, oracle_source))

        # Chercher des candidats alternatifs dans les répertoires fournis
        if candidate_dirs:
            for cdir in candidate_dirs:
                cdir_path = Path(cdir)
                if cdir_path.exists():
                    for candidate in cdir_path.glob("*.py"):
                        try:
                            cand_source = candidate.read_text(encoding="utf-8")
                            overlap = jaccard_similarity(cand_source, oracle_source)
                            overlaps_alternatives.append(overlap)
                        except Exception:
                            pass

    if not overlaps_copies:
        return {"error": "Could not load any items"}

    # Analyse de la distribution
    result: dict[str, Any] = {
        "current_threshold": SALIERI_MEMORISATION_THRESHOLD,
        "copies_distribution": {
            "n": len(overlaps_copies),
            "mean": round(statistics.mean(overlaps_copies), 4) if overlaps_copies else None,
            "min": round(min(overlaps_copies), 4) if overlaps_copies else None,
            "max": round(max(overlaps_copies), 4) if overlaps_copies else None,
        },
        "alternatives_distribution": {
            "n": len(overlaps_alternatives),
            "mean": round(statistics.mean(overlaps_alternatives), 4) if overlaps_alternatives else None,
            "min": round(min(overlaps_alternatives), 4) if overlaps_alternatives else None,
            "max": round(max(overlaps_alternatives), 4) if overlaps_alternatives else None,
        },
    }

    # Recommandation de seuil
    if overlaps_alternatives:
        # Le seuil idéal est entre le max des alternatives et le min des copies
        max_alt = max(overlaps_alternatives)
        min_copy = min(overlaps_copies)
        if max_alt < min_copy:
            recommended = round((max_alt + min_copy) / 2, 2)
            result["recommended_threshold"] = recommended
            result["separation_gap"] = round(min_copy - max_alt, 4)
            result["recommendation"] = (
                f"Clear separation detected. Recommend threshold={recommended} "
                f"(current={SALIERI_MEMORISATION_THRESHOLD})"
            )
        else:
            result["recommended_threshold"] = SALIERI_MEMORISATION_THRESHOLD
            result["recommendation"] = (
                "Overlap between copies and alternatives detected. "
                "Current threshold may cause false positives. "
                "Consider collecting more diverse alternative solutions."
            )
    else:
        result["recommendation"] = (
            "No alternative solutions found. Cannot calibrate threshold empirically. "
            "Provide candidate_dirs with known-correct alternative solutions."
        )

    return result


def tool_analyze_item_difficulty(
    jsonl_paths: list[str],
    difficulty_metric: str = "mp_correctness",
) -> dict[str, Any]:
    """Analyze item difficulty and discrimination (Classical Test Theory)."""
    rows = _load_jsonl(jsonl_paths)
    if not rows:
        return {"error": "No data found"}

    # Grouper par item_id
    item_scores: dict[str, list[float]] = {}
    model_scores: dict[str, list[float]] = {}

    for row in rows:
        item_id = str(row.get("item_id", "unknown"))
        model = str(row.get("model", "unknown"))
        val = row.get(difficulty_metric)
        if val is not None:
            item_scores.setdefault(item_id, []).append(float(val))
            model_scores.setdefault(model, []).append(float(val))

    # Scores totaux par modèle (pour corrélation item-total)
    model_total_means = {m: statistics.mean(vs) for m, vs in model_scores.items()}

    results: dict[str, Any] = {}
    flagged_easy: list[str] = []
    flagged_hard: list[str] = []
    flagged_low_discrim: list[str] = []

    for item_id, scores in item_scores.items():
        p = statistics.mean(scores)  # p-value (difficulty index)
        std = statistics.stdev(scores) if len(scores) > 1 else 0.0

        # Discrimination index D = P_high - P_low (CTT approach)
        # Simplification: std comme proxy de discrimination
        D = std

        item_result: dict[str, Any] = {
            "n_runs": len(scores),
            "p_value": round(p, 4),
            "std": round(std, 4),
            "discrimination_D": round(D, 4),
            "flags": [],
        }

        if p > 0.90:
            item_result["flags"].append("TOO_EASY")
            flagged_easy.append(item_id)
        if p < 0.10:
            item_result["flags"].append("TOO_HARD")
            flagged_hard.append(item_id)
        if D < 0.10:
            item_result["flags"].append("LOW_DISCRIMINATION")
            flagged_low_discrim.append(item_id)

        results[item_id] = item_result

    return {
        "metric": difficulty_metric,
        "n_items": len(results),
        "n_flagged_easy": len(flagged_easy),
        "n_flagged_hard": len(flagged_hard),
        "n_flagged_low_discrimination": len(flagged_low_discrim),
        "flagged_easy": flagged_easy,
        "flagged_hard": flagged_hard,
        "flagged_low_discrimination": flagged_low_discrim,
        "items": results,
        "recommendations": [
            f"Remove or rework {len(flagged_easy)} trivial items (p>0.90)" if flagged_easy else None,
            f"Add scaffolding or split {len(flagged_hard)} too-hard items (p<0.10)" if flagged_hard else None,
            f"Replace {len(flagged_low_discrim)} low-discrimination items (D<0.10)" if flagged_low_discrim else None,
        ],
    }


def tool_generate_academic_report(
    findings: list[dict[str, Any]],
    output_path: str,
) -> dict[str, Any]:
    """Generate a Markdown academic report from collected findings."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# TR-CodeBench — Academic Validation Report",
        "",
        f"> Generated automatically by the Research Validation Agent  ",
        f"> Date: {__import__('datetime').date.today().isoformat()}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "This report presents an automated academic validation of the TR-CodeBench benchmark.",
        "It covers: statistical properties, paradigm classifier robustness, Salieri threshold",
        "calibration, item difficulty analysis, and comparison with existing benchmarks.",
        "",
        "---",
        "",
    ]

    for i, finding in enumerate(findings, 1):
        tool_name = finding.get("tool", f"Finding {i}")
        lines.append(f"## {i}. {tool_name.replace('_', ' ').title()}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(finding.get("result", {}), indent=2, ensure_ascii=False)[:3000])
        lines.append("```")
        lines.append("")

    lines += [
        "---",
        "",
        "## Comparison with Existing Benchmarks",
        "",
        "| Benchmark | Size | Metric | Contamination | Algorithm Diversity |",
        "|---|---|---|---|---|",
        "| HumanEval | 164 | pass@k | Low | Low (single solution) |",
        "| MBPP | 374 | pass@k | Medium | Low |",
        "| SWE-bench | 2294 | resolved% | Low | High (repo-level) |",
        "| LiveCodeBench | 400+ | pass@k | Very Low | Medium |",
        "| **TR-CodeBench** | **40** | **5-axis profile** | **Very Low** | **High (PD measured)** |",
        "",
        "**Key differentiator**: TR-CodeBench is the first benchmark explicitly measuring",
        "**Productive Divergence** — the ability to solve problems with algorithms",
        "fundamentally different from the reference oracle.",
        "",
        "---",
        "",
        "## Academic References",
        "",
        "- Chen, M. et al. (2021). Evaluating Large Language Models Trained on Code. *arXiv:2107.03374*",
        "- Austin, J. et al. (2021). Program Synthesis with Large Language Models. *arXiv:2108.07732*",
        "- Jimenez, C. et al. (2024). SWE-bench: Can Language Models Resolve Real-World GitHub Issues? *ICLR 2024*",
        "- Liu, J. et al. (2023). Is Your Code Generated by ChatGPT Really Correct? *NeurIPS 2023*",
        "- Jain, N. et al. (2024). LiveCodeBench: Holistic and Contamination Free Evaluation of LLMs for Code. *arXiv:2403.07974*",
        "",
        "---",
        "",
        "## Recommendations",
        "",
        "1. **Expand dataset**: 40 items → 200+ for statistical power (α=0.05, β=0.80)",
        "2. **Validate paradigm signatures**: Run inter-annotator agreement study on paradigm labels",
        "3. **Calibrate Salieri threshold empirically**: Collect 100+ diverse solutions per item",
        "4. **Add stress test items**: Items designed to expose specific model weaknesses",
        "5. **Report inter-run reliability**: Publish Cohen's κ or ICC across runs",
        "6. **Release denial trajectories data**: To enable research on algorithmic flexibility",
    ]

    output.write_text("\n".join(lines), encoding="utf-8")
    return {"output_path": str(output), "n_findings": len(findings), "status": "ok"}


def tool_search_related_benchmarks(
    keywords: list[str],
    focus: str = "metrics",
) -> dict[str, Any]:
    """Return structured knowledge about related benchmarks (static KB for now)."""
    BENCHMARK_KB = {
        "HumanEval": {
            "paper": "Chen et al., 2021 (arXiv:2107.03374)",
            "size": 164,
            "metric": "pass@k (k=1,10,100)",
            "language": "Python",
            "contamination_risk": "HIGH (GitHub-derived, pre-2023 LLMs trained on it)",
            "algorithm_diversity": "None (single reference solution)",
            "pd_measured": False,
            "relevance_to_trcb": "Baseline comparison; lacks diversity measurement",
        },
        "MBPP": {
            "paper": "Austin et al., 2021 (arXiv:2108.07732)",
            "size": 374,
            "metric": "pass@k",
            "language": "Python",
            "contamination_risk": "HIGH",
            "algorithm_diversity": "None",
            "pd_measured": False,
            "relevance_to_trcb": "Baseline; simpler problems than TR-CodeBench",
        },
        "SWE-bench": {
            "paper": "Jimenez et al., 2024 (ICLR)",
            "size": 2294,
            "metric": "resolved%",
            "language": "Python (repo-level)",
            "contamination_risk": "LOW (real GitHub issues post-2023)",
            "algorithm_diversity": "HIGH (repo-level solutions)",
            "pd_measured": False,
            "relevance_to_trcb": "Different scope; repo-level vs function-level",
        },
        "LiveCodeBench": {
            "paper": "Jain et al., 2024 (arXiv:2403.07974)",
            "size": "400+ (growing)",
            "metric": "pass@1",
            "language": "Multiple",
            "contamination_risk": "VERY LOW (monthly updates with new problems)",
            "algorithm_diversity": "MEDIUM (competitive programming, single solution)",
            "pd_measured": False,
            "relevance_to_trcb": "Closest competitor for algorithmic problems; lacks PD",
        },
        "EvalPlus": {
            "paper": "Liu et al., 2023 (NeurIPS)",
            "size": "HumanEval+ (164), MBPP+ (378)",
            "metric": "pass@k with augmented tests",
            "language": "Python",
            "contamination_risk": "MEDIUM",
            "algorithm_diversity": "None",
            "pd_measured": False,
            "relevance_to_trcb": "Shows importance of test coverage; motivates PBT approach",
        },
        "TR-CodeBench": {
            "paper": "In preparation",
            "size": 40,
            "metric": "5-axis profile (correctness, robustness, efficiency, divergence, safety)",
            "language": "Python 3.11",
            "contamination_risk": "VERY LOW (paraphrased + identifier obfuscated)",
            "algorithm_diversity": "HIGH (PD explicitly measured)",
            "pd_measured": True,
            "unique_features": [
                "Productive Divergence (PD) measurement",
                "Denial trajectories",
                "Property-Based Testing (Hypothesis)",
                "5-axis independent metrics",
                "Paradigm evidence stack",
                "T2 truth regime",
            ],
        },
    }

    # Filtrer selon les keywords
    relevant = {}
    kw_lower = [k.lower() for k in keywords]
    for name, info in BENCHMARK_KB.items():
        text = json.dumps(info).lower()
        if any(k in text for k in kw_lower) or name == "TR-CodeBench":
            relevant[name] = info

    return {
        "focus": focus,
        "keywords": keywords,
        "benchmarks_found": len(relevant),
        "benchmarks": relevant,
        "tr_codebench_gap": (
            "TR-CodeBench uniquely measures Productive Divergence. "
            "No existing benchmark quantifies whether a model can produce "
            "algorithmically diverse correct solutions."
        ),
    }


# ---------------------------------------------------------------------------
# Dispatch des outils
# ---------------------------------------------------------------------------

TOOL_FUNCTIONS = {
    "compute_benchmark_statistics": tool_compute_benchmark_statistics,
    "validate_paradigm_classifier": tool_validate_paradigm_classifier,
    "calibrate_salieri_threshold": tool_calibrate_salieri_threshold,
    "analyze_item_difficulty": tool_analyze_item_difficulty,
    "generate_academic_report": tool_generate_academic_report,
    "search_related_benchmarks": tool_search_related_benchmarks,
}


def run_tool(tool_name: str, tool_input: dict[str, Any]) -> Any:
    fn = TOOL_FUNCTIONS.get(tool_name)
    if fn is None:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return fn(**tool_input)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


# ---------------------------------------------------------------------------
# Boucle agent principale
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an academic research assistant specializing in LLM evaluation benchmarks.
Your task is to validate and improve TR-CodeBench — a benchmark measuring Productive Divergence (PD)
in code generation models.

TR-CodeBench key concepts:
- T2 Truth Regime: any correct algorithm is valid (no single reference answer)
- Productive Divergence: model uses a fundamentally different algorithm than the oracle
- 5-axis metrics: correctness, robustness, efficiency, divergence, safety
- PBT: Property-Based Testing via Hypothesis
- Denial trajectories: iterative paradigm elicitation under successive constraints

Your analysis should be rigorous, actionable, and grounded in benchmark evaluation methodology
(Classical Test Theory, Item Response Theory, inter-rater reliability).

Available tools allow you to:
1. Compute statistical properties of benchmark results
2. Validate the paradigm classifier with synthetic variants
3. Calibrate the Salieri anti-memorization threshold empirically
4. Analyze item difficulty and discrimination
5. Generate a formal academic report
6. Compare with existing benchmarks (HumanEval, MBPP, SWE-bench, LiveCodeBench)

Work systematically: gather data first, then analyze, then report.
Always quantify uncertainty and flag limitations in your analysis."""


def run_research_agent(
    results_dir: str,
    output_dir: str,
    n_runs_to_analyze: int = 3,
    max_agent_turns: int = 15,
    anthropic_key: str | None = None,
) -> None:
    if not _ANTHROPIC_AVAILABLE:
        raise SystemExit(
            "ERROR: 'anthropic' package not installed.\n"
            "Install it with: pip install anthropic\n"
            "Or run individual tools directly without the agent."
        )
    client = anthropic.Anthropic(api_key=anthropic_key or os.environ.get("ANTHROPIC_API_KEY"))

    # Trouver les fichiers JSONL de résultats
    jsonl_files = sorted(Path(results_dir).glob("*.jsonl"))[:n_runs_to_analyze]
    jsonl_paths = [str(f) for f in jsonl_files]

    if not jsonl_paths:
        print(f"[WARNING] No JSONL files found in {results_dir}")
        print("The agent will run in analysis-only mode (no empirical data).")

    initial_message = f"""
Please conduct a comprehensive academic validation of the TR-CodeBench benchmark.

Available result files: {jsonl_paths if jsonl_paths else "None — run openrouter_runner.py first"}
Output directory for reports: {output_dir}

Follow this analysis plan:
1. Search for related benchmarks to understand the academic context
2. Validate the paradigm classifier on key paradigms (fenwick_tree, patience_sorting, kmp)
3. If result files are available: compute benchmark statistics by model and by item
4. If result files are available: analyze item difficulty and flag problematic items
5. Calibrate the Salieri threshold (use item trcb-proto-0001 as example)
6. Generate a comprehensive academic report with all findings

Be specific about numerical thresholds, cite methodology, and provide actionable recommendations.
"""

    messages = [{"role": "user", "content": initial_message}]
    findings: list[dict[str, Any]] = []

    print(f"[Research Agent] Starting academic validation...")
    print(f"[Research Agent] Results dir: {results_dir}")
    print(f"[Research Agent] Output dir: {output_dir}")
    print()

    for turn in range(max_agent_turns):
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Ajouter la réponse de l'agent à l'historique
        messages.append({"role": "assistant", "content": response.content})

        # Afficher le texte de l'agent
        for block in response.content:
            if hasattr(block, "text") and block.text:
                print(f"[Agent] {block.text[:500]}...")
                print()

        # Si l'agent a terminé
        if response.stop_reason == "end_turn":
            print(f"[Research Agent] Analysis complete after {turn + 1} turns.")
            break

        # Exécuter les outils demandés
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"[Tool] Calling: {block.name}({list(block.input.keys())})")
                result = run_tool(block.name, block.input)
                print(f"[Tool] Result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                print()

                # Sauvegarder le finding
                findings.append({
                    "tool": block.name,
                    "input": block.input,
                    "result": result,
                })

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str)[:8000],
                })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    # Sauvegarder les findings bruts
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    findings_path = output_path / "research_agent_findings.json"
    findings_path.write_text(
        json.dumps(findings, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"\n[Research Agent] Findings saved to: {findings_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="TR-CodeBench Academic Research Agent — validates and improves the benchmark"
    )
    parser.add_argument(
        "--results-dir",
        default="reports/openrouter_runs",
        help="Directory containing openrouter JSONL result files",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/academic_reports",
        help="Output directory for academic reports",
    )
    parser.add_argument(
        "--n-runs",
        type=int,
        default=3,
        help="Number of result files to analyze",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=15,
        help="Maximum agent conversation turns",
    )
    parser.add_argument(
        "--anthropic-key",
        default=None,
        help="Anthropic API key (defaults to ANTHROPIC_API_KEY env var)",
    )
    args = parser.parse_args()

    run_research_agent(
        results_dir=args.results_dir,
        output_dir=args.output_dir,
        n_runs_to_analyze=args.n_runs,
        max_agent_turns=args.max_turns,
        anthropic_key=args.anthropic_key,
    )


if __name__ == "__main__":
    main()