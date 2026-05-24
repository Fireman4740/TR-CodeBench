def assert_public_cases(oracle_module, public_cases, argument_order):
    for case in public_cases:
        inputs = case["input"]
        actual = oracle_module.solve(*[inputs[name] for name in argument_order])
        assert actual == case["expected"]
