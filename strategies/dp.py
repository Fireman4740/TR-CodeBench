from __future__ import annotations

from hypothesis import strategies as st


# --- trcb-proto-0016: Edit Distance ---

@st.composite
def edit_distance_case_strategy(draw):
    alphabet = st.sampled_from("abcdefghijklmnopqrstuvwxyz")
    word1 = draw(st.text(alphabet, min_size=0, max_size=40))
    word2 = draw(st.text(alphabet, min_size=0, max_size=40))
    return {"input": {"word1": word1, "word2": word2}}


@st.composite
def edit_distance_boundary_strategy(draw):
    kind = draw(st.sampled_from(["both_empty", "one_empty", "identical", "single_char", "all_different"]))
    alphabet = st.sampled_from("abcdefgh")
    if kind == "both_empty":
        return {"input": {"word1": "", "word2": ""}}
    elif kind == "one_empty":
        word = draw(st.text(alphabet, min_size=1, max_size=10))
        if draw(st.booleans()):
            return {"input": {"word1": word, "word2": ""}}
        return {"input": {"word1": "", "word2": word}}
    elif kind == "identical":
        word = draw(st.text(alphabet, min_size=1, max_size=15))
        return {"input": {"word1": word, "word2": word}}
    elif kind == "single_char":
        c1 = draw(alphabet)
        c2 = draw(alphabet)
        return {"input": {"word1": c1, "word2": c2}}
    else:
        n = draw(st.integers(1, 10))
        word1 = draw(st.text(st.sampled_from("abc"), min_size=n, max_size=n))
        word2 = draw(st.text(st.sampled_from("xyz"), min_size=n, max_size=n))
        return {"input": {"word1": word1, "word2": word2}}


EDIT_DISTANCE_PBT_GROUPS = {
    "differential": edit_distance_case_strategy,
    "boundary": edit_distance_boundary_strategy,
}


# --- trcb-proto-0017: Coin Change ---

@st.composite
def coin_change_case_strategy(draw):
    n_coins = draw(st.integers(1, 8))
    coins = sorted(draw(st.lists(st.integers(1, 50), min_size=n_coins, max_size=n_coins, unique=True)))
    amount = draw(st.integers(0, 200))
    return {"input": {"coins": coins, "amount": amount}}


@st.composite
def coin_change_boundary_strategy(draw):
    kind = draw(st.sampled_from(["zero_amount", "single_coin", "impossible", "exact_coin", "large_amount"]))
    if kind == "zero_amount":
        coins = draw(st.lists(st.integers(1, 20), min_size=1, max_size=5, unique=True))
        return {"input": {"coins": sorted(coins), "amount": 0}}
    elif kind == "single_coin":
        coin = draw(st.integers(1, 10))
        mult = draw(st.integers(1, 10))
        return {"input": {"coins": [coin], "amount": coin * mult}}
    elif kind == "impossible":
        return {"input": {"coins": [2], "amount": draw(st.sampled_from([1, 3, 5, 7]))}}
    elif kind == "exact_coin":
        coins = sorted(draw(st.lists(st.integers(1, 30), min_size=1, max_size=5, unique=True)))
        return {"input": {"coins": coins, "amount": coins[0]}}
    else:
        coins = sorted(draw(st.lists(st.integers(1, 20), min_size=2, max_size=5, unique=True)))
        amount = draw(st.integers(100, 300))
        return {"input": {"coins": coins, "amount": amount}}


COIN_CHANGE_PBT_GROUPS = {
    "differential": coin_change_case_strategy,
    "boundary": coin_change_boundary_strategy,
}


# --- trcb-proto-0018: Longest Common Subsequence ---

@st.composite
def lcs_case_strategy(draw):
    alphabet = st.sampled_from("abcdefghijklmnop")
    text1 = draw(st.text(alphabet, min_size=0, max_size=40))
    text2 = draw(st.text(alphabet, min_size=0, max_size=40))
    return {"input": {"text1": text1, "text2": text2}}


@st.composite
def lcs_boundary_strategy(draw):
    kind = draw(st.sampled_from(["one_empty", "identical", "no_common", "single_char", "prefix_suffix"]))
    alphabet = st.sampled_from("abcdef")
    if kind == "one_empty":
        text = draw(st.text(alphabet, min_size=1, max_size=10))
        if draw(st.booleans()):
            return {"input": {"text1": text, "text2": ""}}
        return {"input": {"text1": "", "text2": text}}
    elif kind == "identical":
        text = draw(st.text(alphabet, min_size=1, max_size=15))
        return {"input": {"text1": text, "text2": text}}
    elif kind == "no_common":
        n = draw(st.integers(1, 8))
        text1 = draw(st.text(st.sampled_from("abc"), min_size=n, max_size=n))
        text2 = draw(st.text(st.sampled_from("xyz"), min_size=n, max_size=n))
        return {"input": {"text1": text1, "text2": text2}}
    elif kind == "single_char":
        c1 = draw(alphabet)
        c2 = draw(alphabet)
        return {"input": {"text1": c1, "text2": c2}}
    else:
        base = draw(st.text(alphabet, min_size=2, max_size=8))
        prefix = draw(st.text(alphabet, min_size=0, max_size=3))
        suffix = draw(st.text(alphabet, min_size=0, max_size=3))
        return {"input": {"text1": base, "text2": prefix + base + suffix}}


LCS_PBT_GROUPS = {
    "differential": lcs_case_strategy,
    "boundary": lcs_boundary_strategy,
}


# --- trcb-proto-0019: Maximum Subarray Sum ---

@st.composite
def max_subarray_case_strategy(draw):
    n = draw(st.integers(0, 80))
    nums = draw(st.lists(st.integers(-100, 100), min_size=n, max_size=n))
    return {"input": {"nums": nums}}


@st.composite
def max_subarray_boundary_strategy(draw):
    kind = draw(st.sampled_from(["empty", "single_positive", "single_negative", "all_negative", "all_positive"]))
    if kind == "empty":
        return {"input": {"nums": []}}
    elif kind == "single_positive":
        return {"input": {"nums": [draw(st.integers(1, 100))]}}
    elif kind == "single_negative":
        return {"input": {"nums": [draw(st.integers(-100, -1))]}}
    elif kind == "all_negative":
        n = draw(st.integers(2, 15))
        nums = draw(st.lists(st.integers(-100, -1), min_size=n, max_size=n))
        return {"input": {"nums": nums}}
    else:
        n = draw(st.integers(2, 15))
        nums = draw(st.lists(st.integers(1, 100), min_size=n, max_size=n))
        return {"input": {"nums": nums}}


MAX_SUBARRAY_PBT_GROUPS = {
    "differential": max_subarray_case_strategy,
    "boundary": max_subarray_boundary_strategy,
}


# --- trcb-proto-0020: 0/1 Knapsack ---

@st.composite
def knapsack_case_strategy(draw):
    n = draw(st.integers(0, 20))
    weights = draw(st.lists(st.integers(1, 30), min_size=n, max_size=n))
    values = draw(st.lists(st.integers(1, 50), min_size=n, max_size=n))
    capacity = draw(st.integers(0, 100))
    return {"input": {"weights": weights, "values": values, "capacity": capacity}}


@st.composite
def knapsack_boundary_strategy(draw):
    kind = draw(st.sampled_from(["no_items", "zero_capacity", "all_fit", "none_fit", "single_item"]))
    if kind == "no_items":
        return {"input": {"weights": [], "values": [], "capacity": draw(st.integers(0, 50))}}
    elif kind == "zero_capacity":
        n = draw(st.integers(1, 5))
        weights = draw(st.lists(st.integers(1, 10), min_size=n, max_size=n))
        values = draw(st.lists(st.integers(1, 10), min_size=n, max_size=n))
        return {"input": {"weights": weights, "values": values, "capacity": 0}}
    elif kind == "all_fit":
        n = draw(st.integers(1, 8))
        weights = draw(st.lists(st.integers(1, 5), min_size=n, max_size=n))
        values = draw(st.lists(st.integers(1, 20), min_size=n, max_size=n))
        capacity = sum(weights) + draw(st.integers(0, 10))
        return {"input": {"weights": weights, "values": values, "capacity": capacity}}
    elif kind == "none_fit":
        n = draw(st.integers(1, 5))
        weights = draw(st.lists(st.integers(20, 50), min_size=n, max_size=n))
        values = draw(st.lists(st.integers(1, 30), min_size=n, max_size=n))
        return {"input": {"weights": weights, "values": values, "capacity": draw(st.integers(1, 19))}}
    else:
        w = draw(st.integers(1, 20))
        v = draw(st.integers(1, 50))
        capacity = draw(st.integers(0, 30))
        return {"input": {"weights": [w], "values": [v], "capacity": capacity}}


KNAPSACK_PBT_GROUPS = {
    "differential": knapsack_case_strategy,
    "boundary": knapsack_boundary_strategy,
}
