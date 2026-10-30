"""Feature 003 US2: battery parsers, failure rules and verdict (T027; FR-011, FR-014, SC-004,
SC-006). Fixtures in tests/data/batteries/ are real outputs of PractRand 0.96 and TestU01 1.2.3
on development seeds and OS data (smoke runs, 2026-10-29).
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from protocol import batteries  # noqa: E402

DATA = ROOT / "tests" / "data" / "batteries"

PR_HEADER = ("RNG_test using PractRand version 0.96\n\nrng=RNG_stdin32, seed=unknown\n"
             "length= 128 megabytes (2^27 bytes), time= 5.5 seconds\n"
             "  Test Name                         Raw       Processed     Evaluation       \n")


class TestPractRand(unittest.TestCase):
    def test_os_fixture(self):
        run = batteries.load_run(DATA / "pr-os")
        self.assertEqual(run["length_log2"], 28)
        self.assertEqual(run["n_pvalues"], 937)
        self.assertTrue(run["complete"])
        self.assertEqual(run["rule2"], [])
        self.assertEqual({r["checkpoint"] for r in run["results"]}, {27, 28})
        self.assertFalse(batteries.run_fails(run, 0.005 / 100000)["fails"])

    def test_lut_v1_fixture_stops_early_and_fails(self):
        run = batteries.load_run(DATA / "pr-lut")
        self.assertFalse(run["complete"])
        self.assertTrue(run["stopped_early"])
        self.assertGreater(len(run["rule2"]), 0)
        self.assertTrue(batteries.run_fails(run, 1e-9)["fails"])

    def test_extreme_formats(self):
        text = PR_HEADER + (
            "  BCFN(2+0,13-3U)                   R=  +0.7  p = 0.378     normal           \n"
            "  Gap-16:C                          R=  +1.1  p~= 0.768     normal           \n"
            "  FPF/16:all                        R= +19.2  p =  2e-17    FAIL !           \n"
            "  DC6-9x1Bytes-1                    R=  -9.1  p =1-3.4e-7   very suspicious  \n"
            "  BRank(12):3K(1)                   R=+99999  p =  0        FAIL !!!!!!!!    \n"
            "  [Low4/32]TMFn(0+2):wl             \"fail\"        FAIL !!!!!!!!  \n")
        parsed = batteries.parse_practrand(text)
        got = {r["test"]: r for r in parsed["results"]}
        self.assertEqual(parsed["n_pvalues"], 5)                  # "fail" has no p-value
        self.assertAlmostEqual(got["BCFN(2+0,13-3U)"]["q"], 0.378)
        self.assertAlmostEqual(got["Gap-16:C"]["q"], 1 - 0.768)
        self.assertAlmostEqual(got["DC6-9x1Bytes-1"]["q"], 3.4e-7)
        self.assertAlmostEqual(got["DC6-9x1Bytes-1"]["p"], 1 - 3.4e-7)
        self.assertEqual(got["BRank(12):3K(1)"]["q"], 0.0)
        rules = batteries.threshold_rules(parsed, "practrand")
        self.assertEqual({r["test"] for r in rules["rule2"]},
                         {"FPF/16:all", "BRank(12):3K(1)", "[Low4/32]TMFn(0+2):wl"})
        self.assertEqual({r["test"] for r in batteries.rule1(parsed, 3.4e-7)},
                         {"FPF/16:all", "DC6-9x1Bytes-1", "BRank(12):3K(1)"})


class TestTestU01(unittest.TestCase):
    def test_passing_fixture(self):
        run = batteries.load_run(DATA / "sc-v2")
        self.assertEqual(run["n_pvalues"], 15)
        self.assertTrue(run["complete"])
        self.assertEqual(run["rule3"], [])

    def test_failing_fixture_eps_rows_only(self):
        run = batteries.load_run(DATA / "sc-lut")
        self.assertEqual(len(run["rule3"]), 14)                 # 13 eps + 1 "1 - eps1"
        self.assertFalse(any("means a value" in ln for ln in run["rule3"]))
        self.assertTrue(batteries.run_fails(run, 1e-9)["fails"])

    def test_legend_without_eps_rows_is_not_rule3(self):
        # A good generator often has a p-value outside [0.001, 0.999]; TestU01 then prints the
        # legend. Only table rows printed as eps / 1 - eps1 count.
        text = ("========= Summary results of SmallCrush =========\n"
                " The following tests gave p-values outside [0.001, 0.9990]:\n"
                " (eps  means a value < 1.0e-300):\n (eps1 means a value < 1.0e-15):\n\n"
                "       Test                          p-value\n"
                " ----------------------------------------------\n"
                "  8  MatrixRank                      0.9995 \n"
                " ----------------------------------------------\n")
        jsonl = json.dumps({"tests": [{"index": 7, "name": "MatrixRank", "p": 0.9995}]})
        parsed = batteries.parse_testu01(text, jsonl)
        self.assertEqual(parsed["eps_lines"], [])
        self.assertAlmostEqual(parsed["results"][0]["q"], 0.0005)

    def test_missing_summary_is_incomplete(self):
        parsed = batteries.parse_testu01("partial output\n", "")
        self.assertFalse(parsed["summary_found"])
        self.assertEqual(parsed["n_pvalues"], 0)


def run_of(n_pvalues, q=0.5, rule2=(), complete=True, stopped=False, name="r"):
    return {"run": name, "n_pvalues": n_pvalues, "results": [{"q": q}], "rule2": list(rule2),
            "rule3": [], "complete": complete, "stopped_early": stopped}


class TestRulesAndVerdict(unittest.TestCase):
    def test_threshold_boundary_is_inclusive(self):
        t = 0.005 / 1000
        self.assertTrue(batteries.run_fails(run_of(1, q=t), t)["fails"])
        self.assertFalse(batteries.run_fails(run_of(1, q=t * 1.0001), t)["fails"])

    def test_effective_threshold_uses_larger_count(self):
        self.assertEqual(batteries.effective_threshold(1000, [run_of(400), run_of(500)]), 0.005 / 1000)
        self.assertEqual(batteries.effective_threshold(1000, [run_of(700), run_of(500)]), 0.005 / 1200)

    def test_negative_stopped_early_on_failure_is_not_incomplete(self):
        out = batteries.role_outcome([run_of(10, rule2=[{}], complete=False, stopped=True)], 100)
        self.assertTrue(out["fails"])
        self.assertEqual(out["incomplete_runs"], [])
        out = batteries.role_outcome([run_of(10, complete=False, stopped=True)], 100)
        self.assertEqual(out["incomplete_runs"], ["r"])

    def test_verdict_table(self):
        ok = batteries.role_outcome([run_of(10)], 100)
        bad = batteries.role_outcome([run_of(10, rule2=[{}])], 100)
        inc = batteries.role_outcome([run_of(10, complete=False)], 100)
        v = batteries.verdict
        self.assertEqual(v(True, ok, bad, ok)[0], "PASS")
        self.assertEqual(v(True, ok, bad, bad)[0], "FAIL")
        self.assertEqual(v(True, bad, bad, None)[0], "INCONCLUSIVE")     # positive fails
        self.assertEqual(v(True, ok, ok, ok)[0], "INCONCLUSIVE")         # negative passes
        self.assertEqual(v(True, inc, bad, ok)[0], "INCONCLUSIVE")
        self.assertEqual(v(True, ok, bad, inc)[0], "INCONCLUSIVE")
        self.assertEqual(v(True, ok, inc, ok)[0], "INCONCLUSIVE")
        self.assertEqual(v(False, ok, bad, ok)[0], "INVALID")

    def test_practrand_args(self):
        self.assertIn("-tlmaxonly", batteries.practrand_args())
        self.assertIn("-tlfail", batteries.practrand_args(stop_on_fail=True))
        args = batteries.practrand_args()
        self.assertEqual(args[args.index("-tlmax") + 1], "40")
        self.assertEqual(args[args.index("-tlmin") + 1], "27")
        self.assertIn("-a", args)


if __name__ == "__main__":
    unittest.main()
