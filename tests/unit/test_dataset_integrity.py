from __future__ import annotations

import importlib

from trcodebench.hidden_tests import generate_cases
from trcodebench.load_items import list_item_ids, load_item, resolve_repo_path
from trcodebench.run_candidate import load_function_from_path


def test_expected_item_count_and_paths_exist():
    item_ids = list_item_ids()
    assert item_ids == [f"trcb-proto-{index:04d}" for index in range(1, 11)]

    for item_id in item_ids:
        item = load_item(item_id)
        assert item["language"] == "python"
        assert item["task"]["function_name"] == "solve"
        assert resolve_repo_path(item["oracle"]["reference_solution_path"]).exists()
        for public_path in item["tests"]["public_tests"]:
            assert resolve_repo_path(public_path).exists()


def test_public_case_count_is_visible_and_nontrivial():
    for item_id in list_item_ids():
        item = load_item(item_id)
        public_cases = []
        for public_path in item["tests"]["public_tests"]:
            module_name = ".".join(resolve_repo_path(public_path).relative_to(resolve_repo_path(".")).with_suffix("").parts)
            module = importlib.import_module(module_name)
            public_cases.extend(module.PUBLIC_CASES)
        assert len(public_cases) >= 3


def test_hidden_generators_are_registered_and_oracle_callable():
    for item_id in list_item_ids():
        item = load_item(item_id)
        oracle = load_function_from_path(resolve_repo_path(item["oracle"]["reference_solution_path"]), "solve")
        cases = generate_cases(item, limit=5)
        assert len(cases) == 5
        for case in cases:
            inputs = case["input"]
            result = oracle(*[inputs[name] for name in item["task"]["arguments"]])
            assert result is not None
