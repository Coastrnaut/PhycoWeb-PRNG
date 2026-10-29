"""Assessment rules of the pre-registered protocol (spec, incl. Amendment 1; research R4)."""
import importlib
import unittest
from fractions import Fraction

# The package exports the function `assess`, which hides the module of the same name.
assess = importlib.import_module("sp80022.assess")


class TestThresholds(unittest.TestCase):
    def test_proportion_bound_at_100(self):
        self.assertAlmostEqual(assess.proportion_bound(100), 0.96015, places=5)
        self.assertEqual(assess.min_pass_count(100), 97)

    def test_q_at_100(self):
        self.assertAlmostEqual(float(assess.q_fail(100)), 0.01837, places=5)
        self.assertIsInstance(assess.q_fail(100), Fraction)

    def test_k_max_table(self):
        for n_sub, expected in ((2, 1), (8, 1), (18, 2), (148, 7)):
            self.assertEqual(assess.k_max(n_sub, 100), expected, n_sub)

    def test_k_max_recomputed_for_smaller_m(self):
        for m in (80, 55):
            q = assess.q_fail(m)
            for n_sub in (2, 8, 18, 148):
                k = assess.k_max(n_sub, m)
                self.assertLessEqual(assess.binom_sf(n_sub, q, k), Fraction(1, 100))
                if k > 0:
                    self.assertGreater(assess.binom_sf(n_sub, q, k - 1), Fraction(1, 100))


class TestSubtest(unittest.TestCase):
    def uniform(self, m):
        return [(i + 0.5) / m for i in range(m)]

    def test_ideal_subtest_passes(self):
        r = assess.subtest(self.uniform(100))
        self.assertTrue(r["proportion_ok"] and r["uniformity_ok"] and r["ok"])
        self.assertEqual(r["m_prime"], 100)

    def test_proportion_failure(self):
        ps = self.uniform(100)
        for i in range(4):
            ps[i] = 0.001
        r = assess.subtest(ps)
        self.assertEqual(r["pass_count"], 96)
        self.assertFalse(r["proportion_ok"])
        self.assertFalse(r["ok"])

    def test_uniformity_failure_counts_as_failure(self):
        ps = [0.55] * 100
        r = assess.subtest(ps)
        self.assertTrue(r["proportion_ok"])
        self.assertFalse(r["uniformity_ok"])
        self.assertFalse(r["ok"])

    def test_too_few_eligible_fails_uniformity(self):
        r = assess.subtest(self.uniform(54))
        self.assertFalse(r["uniformity_ok"])
        r = assess.subtest(self.uniform(55))
        self.assertTrue(r["uniformity_ok"])

    def test_p_one_goes_in_last_bin(self):
        r = assess.subtest([1.0] * 10 + self.uniform(90))
        self.assertEqual(sum(r["histogram"]), 100)
        self.assertGreaterEqual(r["histogram"][9], 10)


class TestFamilyAndVerdict(unittest.TestCase):
    def test_family_counts_both_failure_kinds(self):
        ok = {"ok": True}
        bad = {"ok": False}
        self.assertTrue(assess.family([ok] * 141 + [bad] * 7, 100)["pass"])
        self.assertFalse(assess.family([ok] * 140 + [bad] * 8, 100)["pass"])
        self.assertFalse(assess.family([bad], 100)["pass"])
        self.assertTrue(assess.family([ok, bad], 100)["pass"])
        self.assertFalse(assess.family([bad, bad], 100)["pass"])

    def test_overall_verdict(self):
        self.assertEqual(assess.overall(True, False, True), "PASS")
        self.assertEqual(assess.overall(True, False, False), "FAIL")
        self.assertEqual(assess.overall(False, False, True), "INCONCLUSIVE")
        self.assertEqual(assess.overall(False, False, None), "INCONCLUSIVE")
        self.assertEqual(assess.overall(True, True, True), "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
