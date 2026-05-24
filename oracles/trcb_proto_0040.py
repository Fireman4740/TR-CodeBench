def solve(n: int) -> int:
    """Matrix exponentiation for n-th Fibonacci number mod 10^9+7."""
    MOD = 10**9 + 7

    if n == 0:
        return 0
    if n == 1:
        return 1

    def mat_mult(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
        return [
            [
                (a[0][0] * b[0][0] + a[0][1] * b[1][0]) % MOD,
                (a[0][0] * b[0][1] + a[0][1] * b[1][1]) % MOD,
            ],
            [
                (a[1][0] * b[0][0] + a[1][1] * b[1][0]) % MOD,
                (a[1][0] * b[0][1] + a[1][1] * b[1][1]) % MOD,
            ],
        ]

    def mat_pow(mat: list[list[int]], power: int) -> list[list[int]]:
        result = [[1, 0], [0, 1]]  # identity
        base = mat
        while power > 0:
            if power % 2 == 1:
                result = mat_mult(result, base)
            base = mat_mult(base, base)
            power //= 2
        return result

    fib_matrix = [[1, 1], [1, 0]]
    result_matrix = mat_pow(fib_matrix, n)
    return result_matrix[0][1]
