from __future__ import annotations

from hypothesis import strategies as st


@st.composite
def kmp_case_strategy(draw):
    alphabet = st.sampled_from(list("abca"))
    text = "".join(draw(st.lists(alphabet, max_size=120)))
    pattern = "".join(draw(st.lists(alphabet, max_size=12)))
    return {"input": {"text": text, "pattern": pattern}}


@st.composite
def kmp_boundary_strategy(draw):
    kind = draw(st.sampled_from(["empty_pattern", "empty_text", "pattern_equals_text",
                                  "pattern_longer", "all_same_chars", "no_match"]))
    alphabet = st.sampled_from(list("abca"))
    if kind == "empty_pattern":
        text = "".join(draw(st.lists(alphabet, max_size=30)))
        return {"input": {"text": text, "pattern": ""}}
    elif kind == "empty_text":
        pattern = "".join(draw(st.lists(alphabet, min_size=1, max_size=10)))
        return {"input": {"text": "", "pattern": pattern}}
    elif kind == "pattern_equals_text":
        s = "".join(draw(st.lists(alphabet, min_size=1, max_size=20)))
        return {"input": {"text": s, "pattern": s}}
    elif kind == "pattern_longer":
        text = "".join(draw(st.lists(alphabet, min_size=1, max_size=5)))
        pattern = text + "x"
        return {"input": {"text": text, "pattern": pattern}}
    elif kind == "all_same_chars":
        c = draw(st.sampled_from(["a", "b"]))
        n = draw(st.integers(1, 30))
        m = draw(st.integers(1, min(10, n)))
        return {"input": {"text": c * n, "pattern": c * m}}
    else:
        return {"input": {"text": "aaa", "pattern": "b"}}


KMP_PBT_GROUPS = {
    "differential": kmp_case_strategy,
    "boundary": kmp_boundary_strategy,
}
