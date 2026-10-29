"""SP 800-22 sections 2.7-2.8: non-overlapping and overlapping template matching (R2, R6)."""
import math
from functools import lru_cache
from typing import List

import numpy
from scipy.special import gammaln

from .special import TestResult, as_bits, igamc, window_codes


@lru_cache(maxsize=None)
def _templates(m: int) -> tuple:
    out = []
    for v in range(2 ** m):
        b = format(v, f"0{m}b")
        if all(b[k:] != b[:m - k] for k in range(1, m)):
            out.append(b)
    return tuple(out)


def templates(m: int) -> List[str]:
    """Aperiodic m-bit templates in increasing numeric order (148 for m = 9)."""
    return list(_templates(m))


def non_overlapping_template(bits, m: int = 9, N: int = 8, template_list=None) -> TestResult:
    """2.7 Non-overlapping Template Matching Test, every aperiodic template a sub-test.

    Aperiodic templates cannot overlap themselves, so the non-overlapping count in a block
    equals the number of windows that match.
    """
    x = as_bits(bits)
    M = x.size // N
    tpl = list(template_list) if template_list is not None else templates(m)
    if M < m:
        return TestResult("non_overlapping_template", False, [], {"m": m, "N": N, "M": M})
    counts = numpy.stack([numpy.bincount(window_codes(x[j * M:(j + 1) * M], m, False),
                                         minlength=2 ** m) for j in range(N)])
    mu = (M - m + 1) / 2.0 ** m
    var = M * (1 / 2.0 ** m - (2 * m - 1) / 2.0 ** (2 * m))
    codes = [int(t, 2) for t in tpl]
    W = counts[:, codes]
    chi2 = ((W - mu) ** 2).sum(axis=0) / var
    p = [igamc(N / 2.0, c / 2.0) for c in chi2]
    return TestResult("non_overlapping_template", True, p,
                      {"m": m, "N": N, "M": M, "templates": len(tpl)},
                      {"mu": mu, "sigma2": var, "chi2": chi2.tolist()})


# SP 800-22 Rev. 1a corrected probabilities for m = 9, M = 1032, K = 5.
_OTM_PI_REV1A = [0.364091, 0.185659, 0.139381, 0.100571, 0.070432, 0.139865]


def _otm_pi(m: int, M: int, K: int) -> List[float]:
    """Section 3.8 probabilities for general parameters (used by the worked example)."""
    eta = (M - m + 1) / 2.0 ** m / 2.0

    def pr(u):
        if u == 0:
            return math.exp(-eta)
        return sum(math.exp(-eta - u * math.log(2) + l * math.log(eta) - gammaln(l + 1)
                            + gammaln(u) - gammaln(l) - gammaln(u - l + 1))
                   for l in range(1, u + 1))
    pi = [pr(u) for u in range(K)]
    return pi + [1.0 - sum(pi)]


def overlapping_template(bits, m: int = 9, M: int = 1032, K: int = 5) -> TestResult:
    """2.8 Overlapping Template Matching Test with the all-ones template of length m."""
    x = as_bits(bits)
    N = x.size // M
    if N < 1:
        return TestResult("overlapping_template", False, [], {"m": m, "M": M, "K": K})
    pi = _OTM_PI_REV1A if (m, M, K) == (9, 1032, 5) else _otm_pi(m, M, K)
    blocks = x[:N * M].reshape(N, M)
    hits = numpy.ones((N, M - m + 1), dtype=bool)
    for j in range(m):
        hits &= blocks[:, j:j + M - m + 1] == 1
    per_block = hits.sum(axis=1)
    nu = numpy.bincount(numpy.minimum(per_block, K), minlength=K + 1)
    expected = N * numpy.array(pi)
    chi2 = float(((nu - expected) ** 2 / expected).sum())
    return TestResult("overlapping_template", True, [igamc(K / 2.0, chi2 / 2.0)],
                      {"m": m, "M": M, "K": K, "pi": list(pi)},
                      {"N": N, "nu": nu.tolist(), "chi2": chi2})
