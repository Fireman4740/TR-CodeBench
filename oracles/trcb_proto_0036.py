def solve(base: int, exponent: int, modulus: int) -> int:
    """Iterative binary exponentiation (repeated squaring) for modular power."""
    if modulus == 1:
        return 0
    result = 1
    base = base % modulus
    exp = exponent
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % modulus
        exp = exp >> 1
        base = (base * base) % modulus
    return result
