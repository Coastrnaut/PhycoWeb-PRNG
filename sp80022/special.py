"""Special functions and the common result type (research R4)."""
import math
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List

import numpy
from scipy.special import gammaincc


def igamc(a: float, x: float) -> float:
    """Regularized upper incomplete gamma function Q(a, x), as SP 800-22 uses it."""
    return float(gammaincc(a, x))


def erfc(x: float) -> float:
    return math.erfc(x)


def normal_cdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def binom_sf(n: int, p: Fraction, k: int) -> Fraction:
    """P(X > k) for X ~ Binomial(n, p), computed exactly."""
    p = Fraction(p)
    return sum((math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1, n + 1)),
               Fraction(0))


@dataclass
class TestResult:
    name: str
    eligible: bool
    p_values: List[float]
    params: Dict = field(default_factory=dict)
    stats: Dict = field(default_factory=dict)


def as_bits(bits) -> numpy.ndarray:
    """Read-only int64 view of a 0/1 sequence; never modifies the caller's array (N1, N2)."""
    arr = numpy.asarray(bits)
    if arr.ndim != 1:
        raise ValueError("bits must be a 1-D array")
    out = arr.astype(numpy.int64, copy=True)
    if out.size and (out.min() < 0 or out.max() > 1):
        raise ValueError("bits must contain only 0 and 1")
    out.flags.writeable = False
    return out


def window_codes(bits: numpy.ndarray, m: int, cyclic: bool) -> numpy.ndarray:
    """Integer code of every m-bit window, first bit most significant."""
    n = bits.size
    ext = numpy.concatenate([bits, bits[:m - 1]]) if cyclic else bits
    count = n if cyclic else n - m + 1
    codes = numpy.zeros(max(count, 0), dtype=numpy.int64)
    for j in range(m):
        codes = (codes << 1) | ext[j:j + count]
    return codes
