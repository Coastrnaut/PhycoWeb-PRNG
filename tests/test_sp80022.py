"""Tests for the own SP 800-22 harness `sp80022` (feature 002, research R3, R6).

TestWorkedExamples (T010) and TestAppendixB (T011) hold values transcribed from NIST SP 800-22
Rev. 1a; they are added once the document has been read. The tests here need no external data.
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
