"""NIST harness isolates each test from in-place input mutation (FR-011; research R6, N2)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

try:
    import numpy
    import nistrng
except ImportError:  # pragma: no cover
    nistrng = None


@unittest.skipIf(nistrng is None, "numpy and nistrng are required")
class TestNistHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "scripts"))
        import nist_eval

        cls.nist_eval = nist_eval
        cls.bits = nist_eval.bits_msb_first("lut-v1", [1024, 2048, 4096, 8192], 32 * 2000)

    def test_bits_are_int64_msb_first(self):
        self.assertEqual(self.bits.dtype, numpy.int64)
        first = int("".join(str(b) for b in self.bits[:32]), 2)
        self.assertEqual(first, 0xD7EDF3D7)

    def test_every_test_reported_once_and_input_untouched(self):
        original = self.bits.copy()
        tests = self.nist_eval.evaluate(self.bits)
        self.assertTrue(numpy.array_equal(self.bits, original))
        self.assertEqual(sorted(t["name"] for t in tests), sorted(nistrng.SP800_22R1A_BATTERY))

    def test_results_match_isolated_runs(self):
        tests = {t["name"]: t for t in self.nist_eval.evaluate(self.bits)}
        for name in ("cumulative sums", "dft", "serial"):
            with self.subTest(name=name):
                result, _ = nistrng.SP800_22R1A_BATTERY[name].run(self.bits.copy())
                expected = [float(p) for p in numpy.atleast_1d(result._score_list)]
                self.assertEqual(tests[name]["p_values"], expected)
                self.assertEqual(tests[name]["p_value"], min(expected))
        # Cumulative Sums reports forward and backward p-values separately.
        self.assertEqual(len(tests["cumulative sums"]["p_values"]), 2)

    def test_reproducible(self):
        first = self.nist_eval.evaluate(self.bits)
        second = self.nist_eval.evaluate(self.bits)
        strip = lambda ts: [{k: v for k, v in t.items() if k != "elapsed_ms"} for t in ts]
        self.assertEqual(strip(first), strip(second))


if __name__ == "__main__":
    unittest.main()
