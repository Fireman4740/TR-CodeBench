from __future__ import annotations

from hypothesis import strategies as st


@st.composite
def modexp_case_strategy(draw):
    base = draw(st.integers(0, 10**9))
    exponent = draw(st.integers(0, 10**6))
    modulus = draw(st.integers(1, 10**9))
    return {"input": {"base": base, "exponent": exponent, "modulus": modulus}}


@st.composite
def modexp_boundary_strategy(draw):
    kind = draw(st.sampled_from(["exp_zero", "mod_one", "base_zero", "base_one", "large_exp"]))
    if kind == "exp_zero":
        base = draw(st.integers(0, 10**9))
        modulus = draw(st.integers(1, 10**9))
        return {"input": {"base": base, "exponent": 0, "modulus": modulus}}
    elif kind == "mod_one":
        base = draw(st.integers(0, 10**9))
        exponent = draw(st.integers(0, 10**6))
        return {"input": {"base": base, "exponent": exponent, "modulus": 1}}
    elif kind == "base_zero":
        exponent = draw(st.integers(1, 10**6))
        modulus = draw(st.integers(2, 10**9))
        return {"input": {"base": 0, "exponent": exponent, "modulus": modulus}}
    elif kind == "base_one":
        exponent = draw(st.integers(0, 10**6))
        modulus = draw(st.integers(1, 10**9))
        return {"input": {"base": 1, "exponent": exponent, "modulus": modulus}}
    else:
        base = draw(st.integers(2, 100))
        exponent = draw(st.integers(10**5, 10**6))
        modulus = draw(st.integers(2, 10**9))
        return {"input": {"base": base, "exponent": exponent, "modulus": modulus}}


MODEXP_PBT_GROUPS = {
    "differential": modexp_case_strategy,
    "boundary": modexp_boundary_strategy,
}


@st.composite
def count_primes_case_strategy(draw):
    n = draw(st.integers(0, 10000))
    return {"input": {"n": n}}


@st.composite
def count_primes_boundary_strategy(draw):
    kind = draw(st.sampled_from(["zero", "one", "two", "three", "small_prime", "power_of_two"]))
    if kind == "zero":
        return {"input": {"n": 0}}
    elif kind == "one":
        return {"input": {"n": 1}}
    elif kind == "two":
        return {"input": {"n": 2}}
    elif kind == "three":
        return {"input": {"n": 3}}
    elif kind == "small_prime":
        return {"input": {"n": draw(st.sampled_from([5, 7, 11, 13, 17, 19, 23, 29]))}}
    else:
        return {"input": {"n": draw(st.sampled_from([4, 8, 16, 32, 64, 128, 256]))}}


COUNT_PRIMES_PBT_GROUPS = {
    "differential": count_primes_case_strategy,
    "boundary": count_primes_boundary_strategy,
}


@st.composite
def perm_rank_case_strategy(draw):
    n = draw(st.integers(1, 8))
    perm = draw(st.permutations(list(range(1, n + 1))))
    return {"input": {"perm": list(perm)}}


@st.composite
def perm_rank_boundary_strategy(draw):
    kind = draw(st.sampled_from(["single", "identity", "reversed", "two_elements"]))
    if kind == "single":
        return {"input": {"perm": [1]}}
    elif kind == "identity":
        n = draw(st.integers(2, 8))
        return {"input": {"perm": list(range(1, n + 1))}}
    elif kind == "reversed":
        n = draw(st.integers(2, 8))
        return {"input": {"perm": list(range(n, 0, -1))}}
    else:
        perm = draw(st.sampled_from([[1, 2], [2, 1]]))
        return {"input": {"perm": perm}}


PERM_RANK_PBT_GROUPS = {
    "differential": perm_rank_case_strategy,
    "boundary": perm_rank_boundary_strategy,
}


@st.composite
def convex_hull_case_strategy(draw):
    n = draw(st.integers(3, 50))
    points = draw(
        st.lists(
            st.tuples(st.integers(-1000, 1000), st.integers(-1000, 1000)),
            min_size=n,
            max_size=n,
        )
    )
    return {"input": {"points": points}}


@st.composite
def convex_hull_boundary_strategy(draw):
    kind = draw(st.sampled_from(["single", "two_points", "collinear", "triangle", "duplicates"]))
    if kind == "single":
        p = (draw(st.integers(-100, 100)), draw(st.integers(-100, 100)))
        return {"input": {"points": [p]}}
    elif kind == "two_points":
        p1 = (draw(st.integers(-100, 100)), draw(st.integers(-100, 100)))
        p2 = (draw(st.integers(-100, 100)), draw(st.integers(-100, 100)))
        return {"input": {"points": [p1, p2]}}
    elif kind == "collinear":
        n = draw(st.integers(3, 10))
        x_start = draw(st.integers(-100, 100))
        y_start = draw(st.integers(-100, 100))
        dx = draw(st.integers(-5, 5))
        dy = draw(st.integers(-5, 5))
        points = [(x_start + i * dx, y_start + i * dy) for i in range(n)]
        return {"input": {"points": points}}
    elif kind == "triangle":
        points = [
            (draw(st.integers(-100, 100)), draw(st.integers(-100, 100)))
            for _ in range(3)
        ]
        return {"input": {"points": points}}
    else:
        p = (draw(st.integers(-100, 100)), draw(st.integers(-100, 100)))
        return {"input": {"points": [p] * draw(st.integers(3, 10))}}


CONVEX_HULL_PBT_GROUPS = {
    "differential": convex_hull_case_strategy,
    "boundary": convex_hull_boundary_strategy,
}


@st.composite
def matrix_fib_case_strategy(draw):
    n = draw(st.integers(0, 10**15))
    return {"input": {"n": n}}


@st.composite
def matrix_fib_boundary_strategy(draw):
    kind = draw(st.sampled_from(["zero", "one", "two", "small", "large"]))
    if kind == "zero":
        return {"input": {"n": 0}}
    elif kind == "one":
        return {"input": {"n": 1}}
    elif kind == "two":
        return {"input": {"n": 2}}
    elif kind == "small":
        return {"input": {"n": draw(st.integers(3, 20))}}
    else:
        return {"input": {"n": draw(st.integers(10**12, 10**18))}}


MATRIX_FIB_PBT_GROUPS = {
    "differential": matrix_fib_case_strategy,
    "boundary": matrix_fib_boundary_strategy,
}
