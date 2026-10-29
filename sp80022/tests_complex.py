"""SP 800-22 sections 2.9-2.12: universal, linear complexity, serial, approximate entropy."""
import math

import numpy

from .special import TestResult, as_bits, erfc, igamc, window_codes

# Section 2.9: (L, minimum n) and the expected value / variance of f_n for each L.
_UNIVERSAL_L = [(6, 387840), (7, 904960), (8, 2068480), (9, 4654080), (10, 10342400),
                (11, 22753280), (12, 49643520), (13, 107560960), (14, 231669760),
                (15, 496435200), (16, 1059061760)]
_UNIVERSAL_EV = {1: (0.7326495, 0.690), 2: (1.5374383, 1.338), 3: (2.4016068, 1.901),
                 4: (3.3112247, 2.358), 5: (4.2534266, 2.705), 6: (5.2177052, 2.954),
                 7: (6.1962507, 3.125), 8: (7.1836656, 3.238), 9: (8.1764248, 3.311),
                 10: (9.1723243, 3.356), 11: (10.170032, 3.384), 12: (11.168765, 3.401),
                 13: (12.168070, 3.410), 14: (13.167693, 3.416), 15: (14.167488, 3.419),
                 16: (15.167379, 3.421)}


def universal(bits, L: int = None, Q: int = None) -> TestResult:
    """2.9 Maurer's "Universal Statistical" Test.

    L and Q default to the SP 800-22 table for n (L = 8, Q = 2560 at n = 2**21). sigma uses
    the c(L, K) correction, as in the section 2.9.8 example (c = 0.591311).
    """
    x = as_bits(bits)
    n = x.size
    if L is None:
        eligible = [l for l, n_min in _UNIVERSAL_L if n >= n_min]
        if not eligible:
            return TestResult("universal", False, [], {})
        L = eligible[-1]
    if Q is None:
        Q = 10 * 2 ** L
    K = n // L - Q
    if K < 1:
        return TestResult("universal", False, [], {"L": L, "Q": Q})
    w = numpy.zeros(n // L, dtype=numpy.int64)
    for j in range(L):
        w = (w << 1) | x[j:(n // L) * L:L]
    last = numpy.zeros(2 ** L, dtype=numpy.int64)
    last[w[:Q]] = numpy.arange(1, Q + 1)
    # Repeated values need the previous occurrence, so the scan is sequential.
    total = 0.0
    log2 = math.log2
    last_l = last.tolist()
    for i, v in enumerate(w[Q:].tolist(), start=Q + 1):
        total += log2(i - last_l[v])
        last_l[v] = i
    fn = total / K
    expected, variance = _UNIVERSAL_EV[L]
    c = 0.7 - 0.8 / L + (4 + 32 / L) * K ** (-3 / L) / 15
    sigma = c * math.sqrt(variance / K)
    p = erfc(abs(fn - expected) / (math.sqrt(2) * sigma))
    return TestResult("universal", True, [p], {"L": L, "Q": Q, "K": K},
                      {"fn": fn, "expected": expected, "sigma": sigma})


def _berlekamp_massey_many(blocks: numpy.ndarray) -> numpy.ndarray:
    """Linear complexity of every row of a 0/1 matrix, all rows at once."""
    N, M = blocks.shape
    s = blocks.astype(numpy.uint8)
    C = numpy.zeros((N, M + 1), dtype=numpy.uint8)
    Bs = numpy.zeros((N, M + 1), dtype=numpy.uint8)
    C[:, 0] = 1
    Bs[:, 0] = 1                     # B = 1 with m = -1
    L = numpy.zeros(N, dtype=numpy.int64)
    for t in range(M):
        Bs[:, 1:] = Bs[:, :-1].copy()   # Bs holds x^(t - m) * B(x)
        Bs[:, 0] = 0
        if t:
            acc = (C[:, 1:t + 1] & s[:, t - 1::-1]).sum(axis=1, dtype=numpy.int64)
            d = (s[:, t] ^ (acc & 1).astype(numpy.uint8)).astype(bool)
        else:
            d = s[:, 0].astype(bool)
        if not d.any():
            continue
        T = C[d].copy()
        C[d] ^= Bs[d]
        grow = d & (2 * L <= t)
        if grow.any():
            # Rows that change length keep their old C as the new B (shifted next step).
            Bs[grow] = T[grow[d]]
            L[grow] = t + 1 - L[grow]
    return L


def linear_complexity(bits, M: int = 500) -> TestResult:
    """2.10 Linear Complexity Test (K = 6)."""
    x = as_bits(bits)
    N = x.size // M
    if N < 1:
        return TestResult("linear_complexity", False, [], {"M": M, "K": 6})
    Ls = _berlekamp_massey_many(x[:N * M].reshape(N, M))
    mu = M / 2.0 + (9 + (-1) ** (M + 1)) / 36.0 - (M / 3.0 + 2 / 9.0) / 2.0 ** M
    T = (-1) ** M * (Ls - mu) + 2 / 9.0
    edges = [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]
    nu = numpy.bincount(numpy.searchsorted(edges, T, side="left"), minlength=7)
    pi = numpy.array([0.010417, 0.03125, 0.125, 0.5, 0.25, 0.0625, 0.020833])
    chi2 = float(((nu - N * pi) ** 2 / (N * pi)).sum())
    return TestResult("linear_complexity", True, [igamc(3.0, chi2 / 2.0)], {"M": M, "K": 6},
                      {"N": N, "nu": nu.tolist(), "chi2": chi2})


def _psi2(x: numpy.ndarray, m: int) -> float:
    if m <= 0:
        return 0.0
    n = x.size
    counts = numpy.bincount(window_codes(x, m, True), minlength=2 ** m).astype(numpy.float64)
    return float((counts ** 2).sum()) * 2.0 ** m / n - n


def serial(bits, m: int = 16) -> TestResult:
    """2.11 Serial Test: two p-values (del psi^2 and del^2 psi^2)."""
    x = as_bits(bits)
    p0, p1, p2 = _psi2(x, m), _psi2(x, m - 1), _psi2(x, m - 2)
    d1 = p0 - p1
    d2 = p0 - 2 * p1 + p2
    return TestResult("serial", True,
                      [igamc(2.0 ** (m - 2), d1 / 2.0), igamc(2.0 ** (m - 3), d2 / 2.0)],
                      {"m": m}, {"psi2": [p0, p1, p2], "del1": d1, "del2": d2})


def _phi(x: numpy.ndarray, m: int) -> float:
    if m <= 0:
        return 0.0
    n = x.size
    c = numpy.bincount(window_codes(x, m, True), minlength=2 ** m)
    c = c[c > 0] / n
    return float((c * numpy.log(c)).sum())


def approximate_entropy(bits, m: int = 10) -> TestResult:
    """2.12 Approximate Entropy Test."""
    x = as_bits(bits)
    n = x.size
    ap_en = _phi(x, m) - _phi(x, m + 1)
    chi2 = 2.0 * n * (math.log(2) - ap_en)
    return TestResult("approximate_entropy", True, [igamc(2.0 ** (m - 1), chi2 / 2.0)],
                      {"m": m}, {"ApEn": ap_en, "chi2": chi2})
