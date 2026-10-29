"""Exact binary expansions of pi, e, sqrt(2) and sqrt(3) for harness validation (T011, R3b).

Each expansion includes its integer-part bits (pi = 11.0010..., as in SP 800-22 section 2.1.8).
Values are computed with integer arithmetic plus GUARD extra bits, and cached as packed bytes in
tests/data/expansions/. The cache files are checked against fixed SHA-256 values in the tests.
"""
import math
from pathlib import Path

import numpy

DATA = Path(__file__).resolve().parent / "data" / "expansions"
GUARD = 64


def _e_fixed(frac_bits: int) -> int:
    """floor(e * 2**frac_bits) via binary splitting of sum 1/k!."""
    K = 2
    while math.lgamma(K + 1) / math.log(2) < frac_bits + 8:
        K *= 2

    def split(a, b):
        if b - a == 1:
            return 1, b
        m = (a + b) // 2
        p1, q1 = split(a, m)
        p2, q2 = split(m, b)
        return p1 * q2 + p2, q1 * q2
    p, q = split(0, K)
    return (1 << frac_bits) + (p << frac_bits) // q


def _pi_fixed(frac_bits: int) -> int:
    """floor(pi * 2**frac_bits) via the Chudnovsky series with binary splitting."""
    C3_24 = 640320 ** 3 // 24

    def split(a, b):
        if b - a == 1:
            if a == 0:
                p = q = 1
            else:
                p = (6 * a - 5) * (2 * a - 1) * (6 * a - 1)
                q = a * a * a * C3_24
            t = p * (13591409 + 545140134 * a)
            return p, q, -t if a & 1 else t
        m = (a + b) // 2
        p1, q1, t1 = split(a, m)
        p2, q2, t2 = split(m, b)
        return p1 * p2, q1 * q2, q2 * t1 + p1 * t2
    terms = frac_bits // 47 + 4
    _, q, t = split(0, terms)
    return 426880 * math.isqrt(10005 << (2 * frac_bits)) * q // t


def _sqrt_fixed(k: int, frac_bits: int) -> int:
    return math.isqrt(k << (2 * frac_bits))


FIXED = {"pi": (_pi_fixed, 2), "e": (_e_fixed, 2), "sqrt2": (lambda f: _sqrt_fixed(2, f), 1),
         "sqrt3": (lambda f: _sqrt_fixed(3, f), 1)}


def compute(name: str, n_bits: int) -> numpy.ndarray:
    func, int_bits = FIXED[name]
    value = func(n_bits - int_bits + GUARD) >> GUARD
    text = bin(value)[2:]
    assert len(text) == n_bits, (name, len(text))
    return numpy.frombuffer(text.encode("ascii"), dtype=numpy.uint8) - ord("0")


def load(name: str, n_bits: int = 1_000_000) -> numpy.ndarray:
    path = DATA / f"{name}_{n_bits}.bin"
    if not path.exists():
        DATA.mkdir(parents=True, exist_ok=True)
        path.write_bytes(numpy.packbits(compute(name, n_bits)).tobytes())
    raw = numpy.frombuffer(path.read_bytes(), dtype=numpy.uint8)
    return numpy.unpackbits(raw)[:n_bits]


def naive(name: str, n_bits: int) -> numpy.ndarray:
    """Independent slow method for the first bits: plain series / Machin / bisection."""
    frac = n_bits + GUARD
    one = 1 << frac
    if name == "e":
        total, term, k = 0, one, 0
        while term:
            total += term
            k += 1
            term //= k
        value, int_bits = total, 2
    elif name == "pi":
        def arctan_inv(x):
            total, power, k, sign = 0, one // x, 1, 1
            while power:
                total += sign * (power // k)
                power //= x * x
                k += 2
                sign = -sign
            return total
        value, int_bits = 16 * arctan_inv(5) - 4 * arctan_inv(239), 2
    else:
        target = (2 if name == "sqrt2" else 3) << (2 * frac)
        lo, hi = 0, 2 << frac
        while hi - lo > 1:
            mid = (lo + hi) // 2
            lo, hi = (mid, hi) if mid * mid <= target else (lo, mid)
        value, int_bits = lo, 1
    text = bin(value >> GUARD)[2:]
    bits = numpy.frombuffer(text.encode("ascii"), dtype=numpy.uint8) - ord("0")
    return bits[:n_bits]
