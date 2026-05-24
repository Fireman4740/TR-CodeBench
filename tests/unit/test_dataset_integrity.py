from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from trcodebench.hidden_tests import generate_cases
from trcodebench.load_items import list_item_ids, load_item, resolve_repo_path
from trcodebench.run_candidate import load_function_from_path


EXPECTED_COUNT = 40
EXPECTED_IDS = [f"trcb-proto-{i:04d}" for i in range(1, EXPECTED_COUNT + 1)]

# Canonical family values — all dataset items must use one of these
CANONICAL_FAMILIES = {
    "dynamic_programming",
    "graph",
    "sorting",
    "string",
    "data_structure",
    "math",
    "arrays",
    "intervals",
    "scheduling",
}

# Supported denial constraint types (mirrors verify_denial.py coverage)
DENIAL_CONSTRAINT_TYPES = {
    "forbidden_api",
    "forbidden_import",
    "forbidden_structure",
    "forbidden_paradigm",
    "forbidden_construct",
    "resource",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_schema() -> dict:
    schema_path = resolve_repo_path("schemas/item.schema.json")
    return json.loads(schema_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_expected_item_count_and_paths_exist():
    item_ids = list_item_ids()
    assert item_ids == EXPECTED_IDS, (
        f"Expected {EXPECTED_COUNT} items (0001–{EXPECTED_COUNT:04d}), got {len(item_ids)}.\n"
        f"Missing: {set(EXPECTED_IDS) - set(item_ids)}\n"
        f"Extra:   {set(item_ids) - set(EXPECTED_IDS)}"
    )
    for item_id in item_ids:
        item = load_item(item_id)
        assert item["language"] == "python", f"{item_id}: language must be 'python'"
        assert item["task"]["function_name"] == "solve", f"{item_id}: function_name must be 'solve'"
        oracle_path = resolve_repo_path(item["oracle"]["reference_solution_path"])
        assert oracle_path.exists(), f"{item_id}: oracle not found at {oracle_path}"
        for public_path in item["tests"]["public_tests"]:
            p = resolve_repo_path(public_path)
            assert p.exists(), f"{item_id}: public test not found at {p}"


def test_family_values_are_canonical():
    """All items must use a canonical family name (no data_structures/strings/graph_dp drift)."""
    bad = {}
    for item_id in list_item_ids():
        item = load_item(item_id)
        family = item.get("family", "")
        if family not in CANONICAL_FAMILIES:
            bad[item_id] = family
    assert not bad, (
        "Non-canonical family values found. Run the normalization fix.\n"
        + "\n".join(f"  {iid}: '{fam}'" for iid, fam in sorted(bad.items()))
    )


def test_denial_constraints_present_and_valid():
    """Every item must have at least one denial constraint with a supported type."""
    errors = []
    for item_id in list_item_ids():
        item = load_item(item_id)
        constraints = item.get("denial_constraints")
        if not constraints:
            errors.append(f"{item_id}: missing or empty denial_constraints")
            continue
        for c in constraints:
            ctype = c.get("type", "")
            if ctype not in DENIAL_CONSTRAINT_TYPES:
                errors.append(f"{item_id} constraint '{c.get('id')}': unsupported type '{ctype}'")
    assert not errors, "\n".join(errors)


def test_oracle_features_precomputed():
    """Every item must have oracle_ast_features pre-computed (avoids dynamic re-detection drift)."""
    missing = []
    for item_id in list_item_ids():
        item = load_item(item_id)
        features = item.get("oracle", {}).get("oracle_ast_features")
        if not features:
            missing.append(item_id)
    assert not missing, (
        "Items missing oracle_ast_features — run: python scripts/annotate_oracle_features.py\n"
        + "\n".join(f"  {iid}" for iid in missing)
    )


def test_json_schema_valid():
    """Every item JSON must validate against schemas/item.schema.json."""
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed — pip install trcodebench[dev]")

    schema = _load_schema()
    errors = []
    for item_id in list_item_ids():
        item = load_item(item_id)
        try:
            jsonschema.validate(item, schema)
        except jsonschema.ValidationError as exc:
            errors.append(f"{item_id}: {exc.message}")
    assert not errors, "\n".join(errors)


def test_public_case_count_is_visible_and_nontrivial():
    for item_id in list_item_ids():
        item = load_item(item_id)
        public_cases = []
        for public_path in item["tests"]["public_tests"]:
            module_name = ".".join(
                resolve_repo_path(public_path)
                .relative_to(resolve_repo_path("."))
                .with_suffix("")
                .parts
            )
            module = importlib.import_module(module_name)
            public_cases.extend(module.PUBLIC_CASES)
        assert len(public_cases) >= 3, f"{item_id}: expected ≥3 public cases, got {len(public_cases)}"


def test_hidden_generators_are_registered_and_oracle_callable():
    for item_id in list_item_ids():
        item = load_item(item_id)
        oracle = load_function_from_path(
            resolve_repo_path(item["oracle"]["reference_solution_path"]), "solve"
        )
        cases = generate_cases(item, limit=5)
        assert len(cases) == 5, f"{item_id}: expected 5 hidden cases, got {len(cases)}"
        for case in cases:
            inputs = case["input"]
            result = oracle(*[inputs[name] for name in item["task"]["arguments"]])
            assert result is not None, f"{item_id}: oracle returned None"
