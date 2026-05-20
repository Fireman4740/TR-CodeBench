from __future__ import annotations

import ast
from typing import Any

from .ast_signals import rolling_hash_signals, segment_tree_signals, z_algorithm_signals
from .dataflow_signals import dfs_memoization_dataflow, rolling_hash_dataflow, segment_tree_dataflow
from .schema import (
    ACCEPT_THRESHOLD,
    JUDGE_THRESHOLD,
    ParadigmEvidence,
    ParadigmSignal,
)

# Paradigms where heuristic signature matching is fragile; evidence stack takes precedence.
EVIDENCE_PARADIGMS: frozenset[str] = frozenset([
    "segment_tree",
    "z_algorithm",
    "rolling_hash_with_verification",
    "dfs_memoization",
])

_LAYER_WEIGHTS: dict[str, float] = {
    "ast_feature": 0.30,
    "structural": 0.50,
    "dataflow": 0.20,
    "behavioral": 0.25,
}


def _fuse(signals: list[ParadigmSignal]) -> float:
    if not signals:
        return 0.0
    total_weight = sum(_LAYER_WEIGHTS.get(s.layer, 0.25) for s in signals)
    weighted_sum = sum(s.confidence * _LAYER_WEIGHTS.get(s.layer, 0.25) for s in signals)
    return round(weighted_sum / total_weight, 6) if total_weight else 0.0


def _ast_feature_signals(paradigm: str, features: dict[str, Any]) -> list[ParadigmSignal]:
    signals: list[ParadigmSignal] = []

    if paradigm == "segment_tree":
        if features.get("recursion"):
            signals.append(ParadigmSignal(
                layer="ast_feature", name="recursion_present",
                confidence=0.50, evidence="recursion detected",
            ))
        if not features.get("heapq") and not features.get("bisect"):
            signals.append(ParadigmSignal(
                layer="ast_feature", name="no_heapq_bisect",
                confidence=0.40, evidence="no heapq or bisect (consistent with seg-tree)",
            ))

    elif paradigm == "z_algorithm":
        if features.get("z_algorithm"):
            signals.append(ParadigmSignal(
                layer="ast_feature", name="z_var_detected",
                confidence=0.70, evidence="z variable + l/r pointers detected by ast_features",
            ))

    elif paradigm == "rolling_hash_with_verification":
        if features.get("rolling_hash"):
            signals.append(ParadigmSignal(
                layer="ast_feature", name="rolling_hash_vars",
                confidence=0.60, evidence="hash + base + mod variables detected",
            ))

    elif paradigm == "dfs_memoization":
        if (
            features.get("recursion")
            and features.get("dict_memo")
            and features.get("adjacency_list")
        ):
            signals.append(ParadigmSignal(
                layer="ast_feature", name="dfs_memo_combo",
                confidence=0.75, evidence="recursion + memo + adjacency_list all present",
            ))

    return signals


def assess_paradigm(
    paradigm: str,
    source: str,
    existing_features: dict[str, Any],
) -> ParadigmEvidence:
    """Run multi-layer evidence assessment for a single fragile paradigm."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ParadigmEvidence(paradigm=paradigm)

    signals: list[ParadigmSignal] = []
    signals.extend(_ast_feature_signals(paradigm, existing_features))

    if paradigm == "segment_tree":
        signals.extend(segment_tree_signals(tree))
        signals.extend(segment_tree_dataflow(tree))
    elif paradigm == "z_algorithm":
        signals.extend(z_algorithm_signals(source, tree))
    elif paradigm == "rolling_hash_with_verification":
        signals.extend(rolling_hash_signals(source))
        signals.extend(rolling_hash_dataflow(tree))
    elif paradigm == "dfs_memoization":
        signals.extend(dfs_memoization_dataflow(tree))

    confidence = _fuse(signals)
    if confidence >= ACCEPT_THRESHOLD:
        decision = "accept"
    elif confidence >= JUDGE_THRESHOLD:
        decision = "judge"
    else:
        decision = "abstain"

    return ParadigmEvidence(
        paradigm=paradigm,
        signals=signals,
        confidence=confidence,
        decision=decision,
    )


def enhance_candidate_paradigms(
    features: dict[str, Any],
    source: str,
    base_paradigms: list[str],
) -> tuple[list[str], dict[str, ParadigmEvidence]]:
    """
    Augment paradigm list with evidence-stack corrections for fragile paradigms.

    - If a fragile paradigm was matched by signatures but evidence abstains → remove it.
    - If a fragile paradigm was not matched but evidence accepts → add it.

    Returns (enhanced_list, evidence_by_paradigm).
    """
    evidence_map: dict[str, ParadigmEvidence] = {}
    enhanced = list(base_paradigms)

    for paradigm in EVIDENCE_PARADIGMS:
        ev = assess_paradigm(paradigm, source, features)
        evidence_map[paradigm] = ev

        if paradigm in enhanced:
            if ev.decision == "abstain":
                enhanced = [p for p in enhanced if p != paradigm]
        else:
            if ev.decision == "accept":
                enhanced.append(paradigm)

    return enhanced, evidence_map
