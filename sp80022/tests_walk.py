"""SP 800-22 sections 2.13-2.15: cumulative sums, random excursions and its variant."""
import math

import numpy

from .special import TestResult, as_bits, erfc, igamc, normal_cdf

RE_STATES = [-4, -3, -2, -1, 1, 2, 3, 4]
REV_STATES = [-9, -8, -7, -6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def _cdiv(a: int, b: int) -> int:
    """C integer division (truncation toward zero), as NIST STS computes the sum bounds."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def _cusum_p(n: int, z: int) -> float:
    sq = math.sqrt(n)
    s1 = 0.0
    for k in range(_cdiv(_cdiv(-n, z) + 1, 4), _cdiv(_cdiv(n, z) - 1, 4) + 1):
        s1 += normal_cdf((4 * k + 1) * z / sq) - normal_cdf((4 * k - 1) * z / sq)
    s2 = 0.0
    for k in range(_cdiv(_cdiv(-n, z) - 3, 4), _cdiv(_cdiv(n, z) - 1, 4) + 1):
        s2 += normal_cdf((4 * k + 3) * z / sq) - normal_cdf((4 * k + 1) * z / sq)
    return min(max(1.0 - s1 + s2, 0.0), 1.0)


def cumulative_sums(bits) -> TestResult:
    """2.13 Cumulative Sums Test: forward then reverse p-value."""
    x = as_bits(bits)
    n = x.size
    steps = 2 * x - 1
    z_fwd = int(numpy.abs(numpy.cumsum(steps)).max())
    z_rev = int(numpy.abs(numpy.cumsum(steps[::-1])).max())
    return TestResult("cumulative_sums", True, [_cusum_p(n, z_fwd), _cusum_p(n, z_rev)], {},
                      {"z_forward": z_fwd, "z_reverse": z_rev})


def _walk(x: numpy.ndarray):
    s = numpy.cumsum(2 * x - 1)
    zeros = s == 0
    J = int(zeros.sum()) + (1 if s[-1] != 0 else 0)
    # Cycle of position i = number of returns to zero strictly before i.
    cycle = numpy.concatenate([[0], numpy.cumsum(zeros)[:-1]])
    return s, J, cycle


def _min_cycles(n: int) -> float:
    return max(0.005 * math.sqrt(n), 500)


def random_excursions(bits, min_cycles: float = None) -> TestResult:
    """2.14 Random Excursions Test: 8 p-values for x = -4..-1, +1..+4."""
    x = as_bits(bits)
    n = x.size
    s, J, cycle = _walk(x)
    limit = _min_cycles(n) if min_cycles is None else min_cycles
    if J < limit:
        return TestResult("random_excursions", False, [], {"min_cycles": limit}, {"J": J})
    p_values, nus = [], {}
    for state in RE_STATES:
        per_cycle = numpy.bincount(cycle[s == state], minlength=J)[:J]
        nu = numpy.bincount(numpy.minimum(per_cycle, 5), minlength=6)
        a = abs(state)
        pi = [1 - 1 / (2 * a)] + [1 / (4 * a * a) * (1 - 1 / (2 * a)) ** (k - 1) for k in
                                 range(1, 5)] + [1 / (2 * a) * (1 - 1 / (2 * a)) ** 4]
        expected = J * numpy.array(pi)
        chi2 = float(((nu - expected) ** 2 / expected).sum())
        p_values.append(igamc(2.5, chi2 / 2.0))
        nus[state] = nu.tolist()
    return TestResult("random_excursions", True, p_values, {"min_cycles": limit},
                      {"J": J, "nu": nus})


def random_excursions_variant(bits, min_cycles: float = None) -> TestResult:
    """2.15 Random Excursions Variant Test: 18 p-values for x = -9..-1, +1..+9."""
    x = as_bits(bits)
    n = x.size
    s, J, _ = _walk(x)
    limit = _min_cycles(n) if min_cycles is None else min_cycles
    if J < limit:
        return TestResult("random_excursions_variant", False, [], {"min_cycles": limit},
                          {"J": J})
    counts = {state: int((s == state).sum()) for state in REV_STATES}
    p_values = [erfc(abs(counts[v] - J) / math.sqrt(2.0 * J * (4 * abs(v) - 2)))
                for v in REV_STATES]
    return TestResult("random_excursions_variant", True, p_values, {"min_cycles": limit},
                      {"J": J, "xi": counts})
