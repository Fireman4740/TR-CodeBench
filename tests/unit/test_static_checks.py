from __future__ import annotations

from trcodebench.load_items import load_item
from trcodebench.static_checks import analyze_candidate


def test_static_checks_reject_forbidden_import(tmp_path):
    candidate = tmp_path / "bad_candidate.py"
    candidate.write_text("import os\n\ndef solve(nums):\n    return len(nums)\n", encoding="utf-8")

    result = analyze_candidate(candidate, load_item("trcb-proto-0001"))

    assert not result["ok"]
    assert "banned_import:os" in result["violations"]


def test_static_checks_allow_declared_import(tmp_path):
    candidate = tmp_path / "good_candidate.py"
    candidate.write_text("from bisect import bisect_left\n\ndef solve(nums):\n    return 0\n", encoding="utf-8")

    result = analyze_candidate(candidate, load_item("trcb-proto-0001"))

    assert result["ok"]
