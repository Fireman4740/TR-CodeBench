from __future__ import annotations

from hypothesis import strategies as st


# ---------- trcb-proto-0026: Longest Palindromic Substring ----------

@st.composite
def palindrome_case_strategy(draw):
    alphabet = st.sampled_from(list("abcba"))
    s = "".join(draw(st.lists(alphabet, max_size=100)))
    return {"input": {"s": s}}


@st.composite
def palindrome_boundary_strategy(draw):
    kind = draw(st.sampled_from([
        "empty", "single_char", "all_same", "no_palindrome_gt1", "full_palindrome"
    ]))
    if kind == "empty":
        return {"input": {"s": ""}}
    elif kind == "single_char":
        c = draw(st.sampled_from(list("abcdef")))
        return {"input": {"s": c}}
    elif kind == "all_same":
        c = draw(st.sampled_from(list("ab")))
        n = draw(st.integers(2, 50))
        return {"input": {"s": c * n}}
    elif kind == "no_palindrome_gt1":
        n = draw(st.integers(2, 20))
        s = "".join(chr(ord("a") + i % 26) for i in range(n))
        return {"input": {"s": s}}
    else:
        half = "".join(draw(st.lists(st.sampled_from(list("abc")), min_size=1, max_size=20)))
        s = half + half[::-1]
        return {"input": {"s": s}}


PALINDROME_PBT_GROUPS = {
    "differential": palindrome_case_strategy,
    "boundary": palindrome_boundary_strategy,
}


# ---------- trcb-proto-0027: Multi-Pattern Search ----------

@st.composite
def multi_pattern_case_strategy(draw):
    alphabet = st.sampled_from(list("abcd"))
    text = "".join(draw(st.lists(alphabet, min_size=1, max_size=100)))
    m = draw(st.integers(1, min(5, len(text))))
    k = draw(st.integers(1, 8))
    patterns = []
    for _ in range(k):
        pat = "".join(draw(st.lists(alphabet, min_size=m, max_size=m)))
        patterns.append(pat)
    return {"input": {"text": text, "patterns": patterns}}


@st.composite
def multi_pattern_boundary_strategy(draw):
    kind = draw(st.sampled_from([
        "empty_text", "empty_patterns", "single_char_patterns",
        "pattern_longer_than_text", "all_same"
    ]))
    if kind == "empty_text":
        return {"input": {"text": "", "patterns": ["ab"]}}
    elif kind == "empty_patterns":
        return {"input": {"text": "abcdef", "patterns": []}}
    elif kind == "single_char_patterns":
        text = "".join(draw(st.lists(st.sampled_from(list("ab")), min_size=3, max_size=20)))
        patterns = [draw(st.sampled_from(list("ab")))]
        return {"input": {"text": text, "patterns": patterns}}
    elif kind == "pattern_longer_than_text":
        return {"input": {"text": "ab", "patterns": ["abcd"]}}
    else:
        n = draw(st.integers(3, 20))
        return {"input": {"text": "a" * n, "patterns": ["aa"]}}


MULTI_PATTERN_PBT_GROUPS = {
    "differential": multi_pattern_case_strategy,
    "boundary": multi_pattern_boundary_strategy,
}


# ---------- trcb-proto-0028: Longest Repeated Substring ----------

@st.composite
def repeated_substr_case_strategy(draw):
    alphabet = st.sampled_from(list("abca"))
    s = "".join(draw(st.lists(alphabet, min_size=1, max_size=80)))
    return {"input": {"s": s}}


@st.composite
def repeated_substr_boundary_strategy(draw):
    kind = draw(st.sampled_from([
        "empty", "single_char", "all_same", "no_repeat", "double_string"
    ]))
    if kind == "empty":
        return {"input": {"s": ""}}
    elif kind == "single_char":
        return {"input": {"s": draw(st.sampled_from(list("abcdef")))}}
    elif kind == "all_same":
        c = draw(st.sampled_from(list("ab")))
        n = draw(st.integers(2, 30))
        return {"input": {"s": c * n}}
    elif kind == "no_repeat":
        n = draw(st.integers(2, 15))
        s = "".join(chr(ord("a") + i % 26) for i in range(n))
        return {"input": {"s": s}}
    else:
        base = "".join(draw(st.lists(st.sampled_from(list("abc")), min_size=2, max_size=10)))
        return {"input": {"s": base + base}}


REPEATED_SUBSTR_PBT_GROUPS = {
    "differential": repeated_substr_case_strategy,
    "boundary": repeated_substr_boundary_strategy,
}


# ---------- trcb-proto-0029: Group Anagrams ----------

@st.composite
def anagram_group_case_strategy(draw):
    n = draw(st.integers(1, 30))
    words = []
    for _ in range(n):
        length = draw(st.integers(0, 8))
        word = "".join(draw(st.lists(st.sampled_from(list("abcde")), min_size=length, max_size=length)))
        words.append(word)
    return {"input": {"words": words}}


@st.composite
def anagram_group_boundary_strategy(draw):
    kind = draw(st.sampled_from([
        "empty_list", "single_word", "all_anagrams", "no_anagrams", "empty_strings"
    ]))
    if kind == "empty_list":
        return {"input": {"words": []}}
    elif kind == "single_word":
        word = "".join(draw(st.lists(st.sampled_from(list("abc")), min_size=1, max_size=5)))
        return {"input": {"words": [word]}}
    elif kind == "all_anagrams":
        base = list("abc")
        perms = draw(st.lists(st.permutations(base), min_size=2, max_size=6))
        words = ["".join(p) for p in perms]
        return {"input": {"words": words}}
    elif kind == "no_anagrams":
        words = ["a", "bb", "ccc", "dddd"]
        return {"input": {"words": words}}
    else:
        n = draw(st.integers(1, 5))
        return {"input": {"words": [""] * n}}


ANAGRAM_GROUP_PBT_GROUPS = {
    "differential": anagram_group_case_strategy,
    "boundary": anagram_group_boundary_strategy,
}


# ---------- trcb-proto-0030: Z-Function ----------

@st.composite
def z_function_case_strategy(draw):
    alphabet = st.sampled_from(list("abca"))
    s = "".join(draw(st.lists(alphabet, min_size=1, max_size=100)))
    return {"input": {"s": s}}


@st.composite
def z_function_boundary_strategy(draw):
    kind = draw(st.sampled_from([
        "empty", "single_char", "all_same", "no_prefix_match", "periodic"
    ]))
    if kind == "empty":
        return {"input": {"s": ""}}
    elif kind == "single_char":
        return {"input": {"s": draw(st.sampled_from(list("abcdef")))}}
    elif kind == "all_same":
        c = draw(st.sampled_from(list("ab")))
        n = draw(st.integers(2, 30))
        return {"input": {"s": c * n}}
    elif kind == "no_prefix_match":
        n = draw(st.integers(2, 15))
        s = "a" + "".join("b" for _ in range(n - 1))
        return {"input": {"s": s}}
    else:
        base = "".join(draw(st.lists(st.sampled_from(list("ab")), min_size=2, max_size=5)))
        reps = draw(st.integers(2, 6))
        return {"input": {"s": base * reps}}


Z_FUNCTION_PBT_GROUPS = {
    "differential": z_function_case_strategy,
    "boundary": z_function_boundary_strategy,
}
