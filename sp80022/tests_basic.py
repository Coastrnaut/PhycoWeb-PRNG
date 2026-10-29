"""SP 800-22 sections 2.1-2.6: frequency, block frequency, runs, longest run, rank, DFT."""
import math

import numpy

from .special import TestResult, as_bits, erfc, igamc


def frequency(bits) -> TestResult:
    """2.1 Frequency (Monobit) Test."""
    x = as_bits(bits)
    n = x.size
    s_n = int(2 * x.sum() - n)
    s_obs = abs(s_n) / math.sqrt(n)
    return TestResult("frequency", True, [erfc(s_obs / math.sqrt(2))], {},
                      {"n": n, "S_n": s_n, "s_obs": s_obs})


def block_frequency(bits, M: int = 128) -> TestResult:
    """2.2 Frequency Test within a Block."""
    x = as_bits(bits)
    N = x.size // M
    if N < 1:
        return TestResult("block_frequency", False, [], {"M": M})
    pi = x[:N * M].reshape(N, M).sum(axis=1) / M
    chi2 = 4.0 * M * float(((pi - 0.5) ** 2).sum())
    return TestResult("block_frequency", True, [igamc(N / 2.0, chi2 / 2.0)], {"M": M},
                      {"N": N, "chi2": chi2})


def runs(bits) -> TestResult:
    """2.3 Runs Test. If the frequency prerequisite fails, p = 0.0 (section 2.3.4)."""
    x = as_bits(bits)
    n = x.size
    pi = float(x.sum()) / n
    tau = 2.0 / math.sqrt(n)
    if abs(pi - 0.5) >= tau:
        return TestResult("runs", True, [0.0], {}, {"pi": pi, "tau": tau, "prerequisite": False})
    v_obs = 1 + int((x[1:] != x[:-1]).sum())
    num = abs(v_obs - 2.0 * n * pi * (1 - pi))
    den = 2.0 * math.sqrt(2.0 * n) * pi * (1 - pi)
    return TestResult("runs", True, [erfc(num / den)], {},
                      {"pi": pi, "tau": tau, "V_obs": v_obs, "prerequisite": True})


# (M, class lower bound v_min, class upper bound v_max, pi) for the three SP 800-22 cases.
_LONGEST_RUN = [
    (8, 1, 4, [0.2148, 0.3672, 0.2305, 0.1875]),
    (128, 4, 9, [0.1174, 0.2430, 0.2493, 0.1752, 0.1027, 0.1124]),
    (10000, 10, 16, [0.0882, 0.2092, 0.2483, 0.1933, 0.1208, 0.0675, 0.0727]),
]


def longest_run(bits) -> TestResult:
    """2.4 Test for the Longest Run of Ones in a Block. M is chosen from n as in SP 800-22."""
    x = as_bits(bits)
    n = x.size
    if n < 128:
        return TestResult("longest_run", False, [], {})
    M, v_min, v_max, pi = _LONGEST_RUN[0 if n < 6272 else 1 if n < 750000 else 2]
    K = len(pi) - 1
    N = n // M
    blocks = numpy.concatenate([x[:N * M].reshape(N, M), numpy.zeros((N, 1), numpy.int64)], 1)
    flat = numpy.concatenate([[0], blocks.ravel()])
    d = numpy.diff(flat)
    starts = numpy.flatnonzero(d == 1)
    ends = numpy.flatnonzero(d == -1)
    longest = numpy.zeros(N, dtype=numpy.int64)
    numpy.maximum.at(longest, starts // (M + 1), ends - starts)
    nu = numpy.bincount(numpy.clip(longest, v_min, v_max) - v_min, minlength=K + 1)
    expected = N * numpy.array(pi)
    chi2 = float(((nu - expected) ** 2 / expected).sum())
    return TestResult("longest_run", True, [igamc(K / 2.0, chi2 / 2.0)], {"M": M, "K": K},
                      {"N": N, "nu": nu.tolist(), "chi2": chi2})


def _rank_probabilities(M: int = 32, Q: int = 32):
    """P(rank = r) for a random M x Q binary matrix, r = M, M-1, and the remainder."""
    def p(r):
        prod = 1.0
        for i in range(r):
            prod *= (1 - 2.0 ** (i - Q)) * (1 - 2.0 ** (i - M)) / (1 - 2.0 ** (i - r))
        return 2.0 ** (r * (Q + M - r) - M * Q) * prod
    pm, pm1 = p(M), p(M - 1)
    return pm, pm1, 1.0 - pm - pm1


def _gf2_ranks(rows: numpy.ndarray, ncols: int) -> numpy.ndarray:
    """Ranks over GF(2) of many matrices at once; rows[k, i] holds row i of matrix k as bits."""
    R = rows.copy()
    N, nrows = R.shape
    rank = numpy.zeros(N, dtype=numpy.int64)
    idx = numpy.arange(nrows)
    all_k = numpy.arange(N)
    for c in range(ncols):
        mask = numpy.uint64(1) << numpy.uint64(ncols - 1 - c)
        has = (R & mask) != 0
        valid = has & (idx[None, :] >= rank[:, None])
        found = valid.any(axis=1)
        piv = numpy.where(found, valid.argmax(axis=1), 0)
        tgt = numpy.minimum(rank, nrows - 1)
        k = all_k[found]
        a, b = R[k, tgt[found]].copy(), R[k, piv[found]].copy()
        R[k, tgt[found]], R[k, piv[found]] = b, a
        prow = R[all_k, tgt]
        has = (R & mask) != 0
        elim = has & (idx[None, :] != tgt[:, None]) & found[:, None]
        R ^= numpy.where(elim, prow[:, None], numpy.uint64(0))
        rank += found
    return rank


def rank(bits, M: int = 32, Q: int = 32) -> TestResult:
    """2.5 Binary Matrix Rank Test. Probabilities are those of 32 x 32 matrices (SP 800-22)."""
    x = as_bits(bits)
    N = x.size // (M * Q)
    if N < 1:
        return TestResult("rank", False, [], {"M": M, "Q": Q})
    m = x[:N * M * Q].reshape(N, M, Q).astype(numpy.uint64)
    weights = numpy.uint64(1) << numpy.arange(Q - 1, -1, -1, dtype=numpy.uint64)
    rows = (m * weights).sum(axis=2, dtype=numpy.uint64)
    ranks = _gf2_ranks(rows, Q)
    f_m = int((ranks == M).sum())
    f_m1 = int((ranks == M - 1).sum())
    rest = N - f_m - f_m1
    p_m, p_m1, p_rest = _rank_probabilities(32, 32)
    chi2 = ((f_m - p_m * N) ** 2 / (p_m * N) + (f_m1 - p_m1 * N) ** 2 / (p_m1 * N)
            + (rest - p_rest * N) ** 2 / (p_rest * N))
    return TestResult("rank", True, [math.exp(-chi2 / 2.0)], {"M": M, "Q": Q},
                      {"N": N, "F_M": f_m, "F_M-1": f_m1, "chi2": chi2})


def dft(bits) -> TestResult:
    """2.6 Discrete Fourier Transform (Spectral) Test, with the Rev. 1a N0 = 0.95 n / 2."""
    x = as_bits(bits)
    n = x.size
    s = numpy.fft.fft(2.0 * x - 1.0)
    mod = numpy.abs(s[: n // 2])
    T = math.sqrt(math.log(1 / 0.05) * n)
    n0 = 0.95 * n / 2.0
    n1 = int((mod < T).sum())
    d = (n1 - n0) / math.sqrt(n * 0.95 * 0.05 / 4.0)
    return TestResult("dft", True, [erfc(abs(d) / math.sqrt(2))], {},
                      {"T": T, "N0": n0, "N1": n1, "d": d})
