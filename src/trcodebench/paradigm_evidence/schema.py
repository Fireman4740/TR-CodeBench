from __future__ import annotations

from dataclasses import dataclass, field

ACCEPT_THRESHOLD = 0.80
JUDGE_THRESHOLD = 0.50


@dataclass(frozen=True)
class ParadigmSignal:
    layer: str      # "ast_feature" | "structural" | "dataflow"
    name: str
    confidence: float
    evidence: str


@dataclass
class ParadigmEvidence:
    paradigm: str
    signals: list[ParadigmSignal] = field(default_factory=list)
    confidence: float = 0.0
    decision: str = "abstain"   # "accept" | "judge" | "abstain"
