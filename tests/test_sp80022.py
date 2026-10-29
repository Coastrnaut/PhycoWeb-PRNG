"""Tests for the own SP 800-22 harness `sp80022` (feature 002, research R3, R6).

TestWorkedExamples (T010) and TestAppendixB (T011) hold values transcribed from NIST SP 800-22
Rev. 1a (cited below). The binary expansions they use are computed exactly (tests/expansions.py).
"""
import hashlib
import os
import random
import sys
import unittest
from pathlib import Path

import numpy

import sp80022

ROOT = Path(__file__).resolve().parents[1]
N_BITS = 2 ** 21
ORDER = ["frequency", "block_frequency", "runs", "longest_run", "rank", "dft",
         "non_overlapping_template", "overlapping_template", "universal", "linear_complexity",
         "serial", "approximate_entropy", "cumulative_sums", "random_excursions",
         "random_excursions_variant"]
COUNTS = [1, 1, 1, 1, 1, 1, 148, 1, 1, 1, 2, 1, 2, 8, 18]


def urandom_bits(n_bits=N_BITS, seed=20261028):
    rng = numpy.random.Generator(numpy.random.PCG64(seed))
    return rng.integers(0, 2, n_bits, dtype=numpy.uint8)


_CACHE = {}


def battery_of(key, bits):
    if key not in _CACHE:
        _CACHE[key] = sp80022.battery(bits)
    return _CACHE[key]


def failing(results):
    return {r.name for r in results if r.eligible and min(r.p_values) < 0.01}


class TestTemplates(unittest.TestCase):
    def test_counts(self):
        self.assertEqual([len(sp80022.templates(m)) for m in range(2, 11)],
                         [2, 4, 6, 12, 20, 40, 74, 148, 284])

    def test_order_and_ends(self):
        t = sp80022.templates(9)
        self.assertEqual(t[0], "000000001")
        self.assertEqual(t[-1], "111111110")
        self.assertEqual(t, sorted(t, key=lambda b: int(b, 2)))


class TestHarnessContract(unittest.TestCase):
    """contracts/sp80022-api.md; a fixed numpy PCG64 stream stands in for an ideal source."""

    @classmethod
    def setUpClass(cls):
        cls.bits = urandom_bits()
        cls.digest = hashlib.sha256(cls.bits.tobytes()).hexdigest()
        cls.results = battery_of("ideal", cls.bits)

    def test_input_not_modified(self):
        self.assertEqual(hashlib.sha256(self.bits.tobytes()).hexdigest(), self.digest)

    def test_order_and_p_value_counts(self):
        self.assertEqual([r.name for r in self.results], ORDER)
        self.assertEqual([len(r.p_values) for r in self.results if r.eligible],
                         [c for r, c in zip(self.results, COUNTS) if r.eligible])
        for r, c in zip(self.results, COUNTS):
            if r.name not in ("random_excursions", "random_excursions_variant"):
                self.assertTrue(r.eligible, r.name)
                self.assertEqual(len(r.p_values), c, r.name)

    def test_p_values_in_unit_interval(self):
        for r in self.results:
            for p in r.p_values:
                self.assertTrue(0.0 <= p <= 1.0, (r.name, p))

    def test_deterministic(self):
        again = sp80022.battery(self.bits)
        self.assertEqual([r.p_values for r in again], [r.p_values for r in self.results])

    def test_int8_input_matches(self):
        """N1 (feature 001): narrow input dtypes must not overflow any count."""
        again = sp80022.battery(self.bits.astype(numpy.int8))
        self.assertEqual([r.p_values for r in again], [r.p_values for r in self.results])

    def test_params_recorded(self):
        by = {r.name: r for r in self.results}
        self.assertEqual(by["block_frequency"].params["M"], 128)
        self.assertEqual(by["non_overlapping_template"].params["m"], 9)
        self.assertEqual(by["universal"].params["L"], 8)
        self.assertEqual(by["linear_complexity"].params["M"], 500)
        self.assertEqual(by["serial"].params["m"], 16)
        self.assertEqual(by["approximate_entropy"].params["m"], 10)

    def test_excursions_ineligible_when_few_cycles(self):
        bits = numpy.ones(N_BITS, dtype=numpy.uint8)
        bits[:900] = numpy.tile([0, 1], 450)   # 450 returns to zero, then a rising walk: J = 451
        for name in ("random_excursions", "random_excursions_variant"):
            r = getattr(sp80022.tests, name)(bits)
            self.assertFalse(r.eligible)
            self.assertEqual(r.p_values, [])

    def test_ideal_source_passes_most(self):
        # One sequence of an ideal source fails a given p >= 0.01 check about 1% of the time;
        # with 187 p-values a handful of failures is normal, a whole test failing is not.
        fails = sum(p < 0.01 for r in self.results for p in r.p_values)
        self.assertLessEqual(fails, 8)


# --- Values transcribed from NIST SP 800-22 Rev. 1a (April 2010), file
# nistspecialpublication800-22r1a.pdf (SHA-256 38aba1b34a7fa52c440790d6e0cabf498e4b525177b3b6ce
# bb399ab8ccf031d2), downloaded from nvlpubs.nist.gov on 2026-10-28. Section numbers as cited.

EPS100 = ("11001001000011111101101010100010001000010110100011"
          "00001000110100110001001100011001100010100010111000")       # sections 2.1.8 ff.
EPS128 = ("11001100000101010110110001001100111000000000001001"
          "00110101010001000100111101011010000000110101111100"
          "1100111001101101100010110010")                              # section 2.4.8

# The probabilities NIST STS used to produce the published section 2.8.8 / 2.10.8 and
# Appendix B values. They are NOT the harness defaults (research R11):
#  - Overlapping Template: the pre-Rev. 1a Poisson approximation, rejected by 4 million
#    urandom blocks (chi2 = 337, p ~ 1e-70); the harness uses the Rev. 1a values.
#  - Linear Complexity: pi0 = 0.01047 is a typo for 0.010417 (= 1/96; the 7 values would sum
#    to 1.000053); the harness uses the documented 0.010417.
STS_LC_PI = [0.01047, 0.03125, 0.125, 0.5, 0.25, 0.0625, 0.020833]


def bits_of(text):
    return numpy.array([int(c) for c in text], dtype=numpy.uint8)


def chi2_p(nu, N, pi, dof):
    from scipy.special import gammaincc
    nu, pi = numpy.array(nu), numpy.array(pi)
    chi2 = float(((nu - N * pi) ** 2 / (N * pi)).sum())
    return chi2, float(gammaincc(dof / 2.0, chi2 / 2.0))


class TestWorkedExamples(unittest.TestCase):
    """T010: section 2.x.8 examples (R3a)."""

    @classmethod
    def setUpClass(cls):
        from tests import expansions
        cls.e = expansions.load("e")

    def p(self, actual, expected, places=6):
        self.assertAlmostEqual(actual, expected, places=places)

    def test_2_1_frequency(self):
        r = sp80022.tests.frequency(bits_of(EPS100))
        self.assertEqual(r.stats["S_n"], -16)
        self.p(r.stats["s_obs"], 1.6)
        self.p(r.p_values[0], 0.109599)

    def test_2_2_block_frequency(self):
        r = sp80022.tests.block_frequency(bits_of(EPS100), M=10)
        self.assertEqual(r.stats["N"], 10)
        self.p(r.stats["chi2"], 7.2)
        self.p(r.p_values[0], 0.706438)

    def test_2_3_runs(self):
        r = sp80022.tests.runs(bits_of(EPS100))
        self.p(r.stats["pi"], 0.42)
        self.assertEqual(r.stats["V_obs"], 52)
        self.p(r.p_values[0], 0.500798)

    def test_2_4_longest_run(self):
        r = sp80022.tests.longest_run(bits_of(EPS128))
        self.assertEqual(r.params, {"M": 8, "K": 3})
        self.assertEqual(r.stats["nu"], [4, 9, 3, 0])
        self.p(r.stats["chi2"], 4.882457)
        self.p(r.p_values[0], 0.180609)

    def test_2_5_rank(self):
        r = sp80022.tests.rank(self.e[:100000])
        self.assertEqual((r.stats["N"], r.stats["F_M"], r.stats["F_M-1"]), (97, 23, 60))
        self.p(r.stats["chi2"], 1.2619656, places=7)
        self.p(r.p_values[0], 0.532069)

    @unittest.skip("Document inconsistency: section 2.6.8 states N1 = 46 for EPS100; this "
                   "harness counts 48. The DFT matches all four Appendix B values at n = 10**6 "
                   "(TestAppendixB) and is compared with NIST STS in T028.")
    def test_2_6_dft(self):
        r = sp80022.tests.dft(bits_of(EPS100))
        self.assertEqual(r.stats["N1"], 46)

    @unittest.skip("Input not reproducible: 2**20 bits of the FIPS 186-2 G-SHA-1 generator.")
    def test_2_7_non_overlapping_template(self):
        pass

    def test_2_8_overlapping_template_counts(self):
        r = sp80022.tests.overlapping_template(self.e)
        self.assertEqual(r.stats["N"], 968)
        self.assertEqual(r.stats["nu"], [329, 164, 150, 111, 78, 136])
        from sp80022.tests_template import _otm_pi
        chi2, p = chi2_p(r.stats["nu"], 968, _otm_pi(9, 1032, 5), 5)
        self.p(chi2, 8.965859)
        self.p(p, 0.110434)

    @unittest.skip("Input not reproducible: 2**20 bits of the FIPS 186-2 G-SHA-1 generator.")
    def test_2_9_universal(self):
        pass

    def test_2_10_linear_complexity_counts(self):
        r = sp80022.tests.linear_complexity(self.e, M=1000)
        self.assertEqual(r.stats["nu"], [11, 31, 116, 501, 258, 57, 26])
        chi2, p = chi2_p(r.stats["nu"], 1000, STS_LC_PI, 6)
        self.p(chi2, 2.700348)
        self.p(p, 0.845406)

    def test_2_11_serial(self):
        r = sp80022.tests.serial(self.e, m=2)
        for got, want in zip(r.stats["psi2"], [0.343128, 0.003364, 0.0]):
            self.p(got, want)
        self.p(r.stats["del1"], 0.339764)
        self.p(r.stats["del2"], 0.336400)
        self.p(r.p_values[0], 0.843764)
        self.p(r.p_values[1], 0.561915)

    def test_2_12_approximate_entropy(self):
        r = sp80022.tests.approximate_entropy(bits_of(EPS100), m=2)
        self.p(r.stats["ApEn"], 0.665393)
        self.p(r.stats["chi2"], 5.550792)
        self.p(r.p_values[0], 0.235301)

    def test_2_13_cumulative_sums(self):
        r = sp80022.tests.cumulative_sums(bits_of(EPS100))
        self.assertEqual((r.stats["z_forward"], r.stats["z_reverse"]), (16, 19))
        self.p(r.p_values[0], 0.219194)
        self.p(r.p_values[1], 0.114866)

    def test_2_14_random_excursions(self):
        # States -4..-1 as in the section 2.14.8 table. For +1 the table (0.778616) contradicts
        # Appendix B for the same input (0.786868, asserted in TestAppendixB); +2..+4 are
        # compared with NIST STS in T028.
        r = sp80022.tests.random_excursions(self.e)
        self.assertEqual(r.stats["J"], 1490)
        for got, want in zip(r.p_values[:4], [0.573306, 0.197996, 0.164011, 0.007779]):
            self.p(got, want)

    def test_2_15_random_excursions_variant(self):
        r = sp80022.tests.random_excursions_variant(self.e)
        self.assertEqual(r.stats["J"], 1490)
        counts = [1450, 1435, 1380, 1366, 1412, 1475, 1480, 1468, 1502,
                  1409, 1369, 1396, 1479, 1599, 1628, 1619, 1620, 1610]
        pvals = [0.858946, 0.794755, 0.576249, 0.493417, 0.633873, 0.917283, 0.934708, 0.816012,
                 0.826009, 0.137861, 0.200642, 0.441254, 0.939291, 0.505683, 0.445935, 0.512207,
                 0.538635, 0.593930]
        from sp80022.tests_walk import REV_STATES
        self.assertEqual([r.stats["xi"][x] for x in REV_STATES], counts)
        for got, want in zip(r.p_values, pvals):
            self.p(got, want)


# Appendix B, pages B-1 to B-3: 1,000,000 bits each, rows in the table's order.
APPENDIX_B_ROWS = ["frequency", "block_frequency", "cusum_forward", "cusum_reverse", "runs",
                   "longest_run", "rank", "dft", "non_overlapping_template",
                   "overlapping_template", "universal", "approximate_entropy",
                   "random_excursions", "random_excursions_variant", "linear_complexity",
                   "serial"]
APPENDIX_B = {
    "pi": [0.578211, 0.380615, 0.628308, 0.663369, 0.419268, 0.024390, 0.083553, 0.010186,
           0.165757, 0.296897, 0.669012, 0.361595, 0.844143, 0.760966, 0.255475, 0.143005],
    "e": [0.953749, 0.211072, 0.669887, 0.724266, 0.561917, 0.718945, 0.306156, 0.847187,
          0.078790, 0.110434, 0.282568, 0.700073, 0.786868, 0.826009, 0.826335, 0.766182],
    "sqrt2": [0.811881, 0.833222, 0.879009, 0.957206, 0.313427, 0.012117, 0.823810, 0.581909,
              0.569461, 0.791982, 0.130805, 0.884740, 0.216235, 0.566118, 0.317127, 0.861925],
    "sqrt3": [0.610051, 0.473961, 0.917121, 0.689519, 0.261123, 0.446726, 0.314498, 0.776046,
              0.532235, 0.082716, 0.165981, 0.180481, 0.783283, 0.155066, 0.346469, 0.157500],
}
EXPANSION_SHA256 = {
    "pi": "e31af8c5229974786fbac6931fb44f8596d4466eaa853f40df458fd352453155",
    "e": "7ae61691f949a9a92d5ed8b65722bfcf0179964064d5f2c7e2a971b32ac97d49",
    "sqrt2": "5de671f07b9fefe7c0ff7d9ca2146944157c17aa6032c3338d1b9c2ae8658a87",
    "sqrt3": "4c75e3c54dd821f70215e1e016744a74bd8cfb76cbd9be35a37964ae57443cf2",
}


class TestAppendixB(unittest.TestCase):
    """T011: Appendix B p-values for pi, e, sqrt(2), sqrt(3) (R3b)."""

    def test_expansions(self):
        from tests import expansions
        for name, digest in EXPANSION_SHA256.items():
            bits = expansions.load(name)
            self.assertEqual(hashlib.sha256(numpy.packbits(bits).tobytes()).hexdigest(), digest)
            self.assertTrue((expansions.naive(name, 10000) == bits[:10000]).all(), name)
        self.assertEqual("".join(map(str, expansions.load("pi")[:100])), EPS100)

    def ours(self, bits):
        from sp80022.tests_template import _otm_pi
        t = sp80022.tests
        cs = t.cumulative_sums(bits).p_values
        lc = t.linear_complexity(bits)
        otm = t.overlapping_template(bits)
        return {
            "frequency": t.frequency(bits).p_values[0],
            "block_frequency": t.block_frequency(bits).p_values[0],
            "cusum_forward": cs[0], "cusum_reverse": cs[1],
            "runs": t.runs(bits).p_values[0],
            "longest_run": t.longest_run(bits).p_values[0],
            "rank": t.rank(bits).p_values[0],
            "dft": t.dft(bits).p_values[0],
            "non_overlapping_template": t.non_overlapping_template(bits).p_values[0],
            # Published with the constants STS used (STS_LC_PI, _otm_pi; R11); counts are ours.
            "overlapping_template": chi2_p(otm.stats["nu"], otm.stats["N"],
                                           _otm_pi(9, 1032, 5), 5)[1],
            "universal": t.universal(bits).p_values[0],
            "approximate_entropy": t.approximate_entropy(bits).p_values[0],
            "random_excursions": t.random_excursions(bits).p_values[4],          # x = +1
            "random_excursions_variant": t.random_excursions_variant(bits).p_values[8],  # x = -1
            "linear_complexity": chi2_p(lc.stats["nu"], lc.stats["N"], STS_LC_PI, 6)[1],
            "serial": t.serial(bits).p_values[0],
        }

    def test_appendix_b(self):
        from tests import expansions
        for name, values in APPENDIX_B.items():
            ours = self.ours(expansions.load(name))
            for row, want in zip(APPENDIX_B_ROWS, values):
                with self.subTest(expansion=name, test=row):
                    # +-1 in the 6th printed decimal (R3d): STS's own normal-CDF routine
                    # differs from erfc by up to 7e-7 (cusum, e).
                    self.assertAlmostEqual(ours[row], want, delta=1e-6)

    def test_harness_defaults_differ_only_by_constants(self):
        """With its own documented constants, the harness gives other OTM and LC p-values."""
        from tests import expansions
        e = expansions.load("e")
        self.assertAlmostEqual(sp80022.tests.overlapping_template(e).p_values[0], 0.159027, 6)
        self.assertAlmostEqual(sp80022.tests.linear_complexity(e).p_values[0], 0.826194, 6)


class TestKnownBad(unittest.TestCase):
    """R3e: the harness must be able to fail. Expected failures follow from the definitions."""

    def test_all_zeros(self):
        r = battery_of("zeros", numpy.zeros(N_BITS, dtype=numpy.uint8))
        by = {x.name: x for x in r}
        self.assertFalse(by["random_excursions"].eligible)
        self.assertFalse(by["random_excursions_variant"].eligible)
        eligible = {x.name for x in r if x.eligible}
        self.assertEqual(failing(r), eligible)

    def test_alternating(self):
        r = battery_of("alt", numpy.tile(numpy.array([0, 1], dtype=numpy.uint8), N_BITS // 2))
        by = {x.name: x for x in r}
        # Exactly balanced: frequency and block frequency have S = 0, so p = 1.
        self.assertEqual(by["frequency"].p_values, [1.0])
        self.assertEqual(by["block_frequency"].p_values, [1.0])
        for name in ("runs", "longest_run", "rank", "dft", "non_overlapping_template",
                     "overlapping_template", "universal", "linear_complexity", "serial",
                     "approximate_entropy", "random_excursions", "random_excursions_variant"):
            self.assertIn(name, failing(r), name)

    def test_biased_source(self):
        rng = random.Random(2026)
        bits = numpy.fromiter((rng.random() < 0.51 for _ in range(N_BITS)), dtype=numpy.uint8,
                              count=N_BITS)
        r = battery_of("biased", bits)
        for name in ("frequency", "block_frequency", "runs", "cumulative_sums"):
            self.assertIn(name, failing(r), name)

    def test_lut_v1(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from gen_vectors import generate
        words = numpy.fromiter(generate("lut-v1", [1024, 2048, 4096, 8192], N_BITS // 32),
                               dtype=">u4", count=N_BITS // 32)
        bits = numpy.unpackbits(words.view(numpy.uint8))
        self.assertGreaterEqual(len(failing(battery_of("lut-v1", bits))), 1)


if __name__ == "__main__":
    unittest.main()
