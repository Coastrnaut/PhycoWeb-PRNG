"""Proportion, uniformity and verdict rules of the pre-registered protocol (spec; research R4).

Spec Amendment 1: a sub-test fails if it fails proportion OR uniformity, and both kinds of
failure count toward k_max.
"""
import math
from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Optional

from .special import binom_sf, igamc

ALPHA = 0.01
UNIFORMITY_ALPHA = 0.0001
MIN_SEQUENCES = 55
FAMILY_ALPHA = Fraction(1, 100)


def proportion_bound(m: int) -> float:
    return 0.99 - 3.0 * math.sqrt(0.99 * 0.01 / m)


def min_pass_count(m: int) -> int:
    return math.ceil(proportion_bound(m) * m)


@lru_cache(maxsize=None)
def q_fail(m: int) -> Fraction:
    """Probability that an ideal sub-test fails the proportion criterion with m sequences."""
    return binom_sf(m, Fraction(1, 100), m - min_pass_count(m))


@lru_cache(maxsize=None)
def k_max(n_sub: int, m: int) -> int:
    q = q_fail(m)
    for k in range(n_sub + 1):
        if binom_sf(n_sub, q, k) <= FAMILY_ALPHA:
            return k
    return n_sub


def histogram(p_values: List[float]) -> List[int]:
    bins = [0] * 10
    for p in p_values:
        bins[min(int(math.floor(p * 10)), 9)] += 1
    return bins


def subtest(p_values: List[float]) -> Dict:
    m = len(p_values)
    hist = histogram(p_values)
    passed = sum(p >= ALPHA for p in p_values)
    if m:
        bound = proportion_bound(m)
        proportion_ok = passed >= bound * m
        expected = m / 10.0
        chi2 = sum((f - expected) ** 2 / expected for f in hist)
        p_t = igamc(4.5, chi2 / 2.0)
    else:
        bound, proportion_ok, p_t = None, False, None
    uniformity_ok = m >= MIN_SEQUENCES and p_t is not None and p_t >= UNIFORMITY_ALPHA
    return {"m_prime": m, "pass_count": passed, "proportion_bound": bound,
            "proportion_ok": proportion_ok, "histogram": hist, "p_value_t": p_t,
            "uniformity_ok": uniformity_ok, "ok": proportion_ok and uniformity_ok}


def family(subtests: List[Dict], m: int) -> Dict:
    n_sub = len(subtests)
    failed = sum(not s["ok"] for s in subtests)
    limit = 0 if n_sub == 1 or m == 0 else k_max(n_sub, m)
    # Fewer than 55 eligible sequences fails the test outright (spec Edge Cases).
    return {"n_sub": n_sub, "failed_sub": failed, "k_max": limit,
            "pass": failed <= limit and m >= MIN_SEQUENCES}


def assess(per_sequence) -> Dict:
    """Aggregate battery results of many sequences (list of lists of TestResult)."""
    names = [r.name for r in per_sequence[0]]
    subtests, families = {}, {}
    for t, name in enumerate(names):
        eligible = [seq[t] for seq in per_sequence if seq[t].eligible]
        m = len(eligible)
        n_sub = len(eligible[0].p_values) if eligible else 1
        subs = [subtest([r.p_values[j] for r in eligible]) for j in range(n_sub)]
        subtests[name] = subs
        families[name] = family(subs, m)
    return {"subtests": subtests, "families": families,
            "pass": all(f["pass"] for f in families.values())}


def overall(positive_pass: bool, negative_pass: Optional[bool], candidate_pass: Optional[bool]):
    """Spec overall verdict. A candidate that was not run (None) cannot pass."""
    if not positive_pass or negative_pass:
        return "INCONCLUSIVE"
    if candidate_pass is None:
        return "INCONCLUSIVE"
    return "PASS" if candidate_pass else "FAIL"
