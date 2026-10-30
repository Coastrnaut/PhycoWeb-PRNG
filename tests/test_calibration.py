"""Feature 003 US1: calibration runner guards, record shape and statistics (T004).

The SP 800-22 evaluation is replaced by a synthetic one so the tests run in seconds; the real
path is the unchanged feature-002 worker (scripts/evalcore.py).
"""
import contextlib
import gzip
import io
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import calibrate  # noqa: E402
import calibration_report  # noqa: E402
import sp80022  # noqa: E402


def fake_score(pool, sequences, n_bits, seed=0):
    rng = random.Random(seed + len(sequences))
    return [[sp80022.TestResult("frequency", True, [rng.random()], {}, {}),
             sp80022.TestResult("cumulative_sums", True, [rng.random(), rng.random()], {}, {})]
            for _ in sequences]


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*args)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        patches = [mock.patch.object(calibrate, "score", fake_score),
                   mock.patch.object(calibrate, "N_BITS", 64)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def run_cli(self, *args):
        return quiet(calibrate.main, ["--workers", "1", "--out-dir", str(self.dir), *args])


class TestRunnerGuards(Base):
    def test_wrong_harness_hash_refused(self):
        with mock.patch.object(calibrate, "HARNESS_SHA256", "0" * 64):
            self.assertEqual(self.run_cli("--runs", "0-1"), 2)
        self.assertEqual(list(self.dir.iterdir()), [])

    def test_range_outside_protocol_refused(self):
        self.assertEqual(self.run_cli("--runs", "999-1000"), 2)

    def test_existing_run_refused_without_resume(self):
        self.assertEqual(self.run_cli("--runs", "0-1"), 0)
        before = calibrate.run_path(self.dir, 0).read_bytes()
        self.assertEqual(self.run_cli("--runs", "0-2"), 2)
        self.assertEqual(calibrate.run_path(self.dir, 0).read_bytes(), before)
        self.assertFalse(calibrate.run_path(self.dir, 2).exists())

    def test_resume_starts_at_first_missing(self):
        self.assertEqual(self.run_cli("--runs", "0-1"), 0)
        before = calibrate.run_path(self.dir, 1).read_bytes()
        self.assertEqual(self.run_cli("--runs", "0-3", "--resume"), 0)
        self.assertEqual(calibrate.run_path(self.dir, 1).read_bytes(), before)
        self.assertTrue(calibrate.run_path(self.dir, 3).exists())

    def test_resume_refuses_gap(self):
        self.assertEqual(self.run_cli("--runs", "2-2"), 0)
        self.assertEqual(self.run_cli("--runs", "0-3", "--resume"), 2)


class TestRecord(Base):
    def test_shape_and_no_bytes_written(self):
        self.assertEqual(self.run_cli("--runs", "0-0"), 0)
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), ["run-0000.json.gz"])
        with gzip.open(calibrate.run_path(self.dir, 0), "rt", encoding="utf-8") as fh:
            rec = json.load(fh)
        self.assertEqual(rec["run"], 0)
        self.assertEqual(rec["n_sequences"], 100)
        self.assertEqual(len(rec["sequences"]), 100)
        self.assertEqual(len(rec["input_sha256"]), 64)
        self.assertEqual(rec["harness_sha256"], calibrate.HARNESS_SHA256)
        self.assertIn(rec["verdict"], ("pass", "fail"))
        self.assertEqual(set(rec["families"]), {"frequency", "cumulative_sums"})
        self.assertIn("not be used to generate secrets", rec["disclaimer"])

    def test_input_hash_is_hash_of_concatenation(self):
        chunks = [b"\x01" * 8, b"\x02" * 8]
        it = iter(chunks)
        _, digest = calibrate.draw_sequences(2, 64, rand=lambda n: next(it))
        import hashlib
        self.assertEqual(digest, hashlib.sha256(b"".join(chunks)).hexdigest())


class TestStatistics(unittest.TestCase):
    def test_clopper_pearson_known_values(self):
        lo, hi = calibration_report.clopper_pearson(5, 10)
        self.assertAlmostEqual(lo, 0.187086, places=5)
        self.assertAlmostEqual(hi, 0.812914, places=5)
        lo, hi = calibration_report.clopper_pearson(0, 10)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.308497, places=5)

    def test_expected_single_family_rate(self):
        # Feature-002 spec: q = 0.01837 at m' = 100, plus the 1e-4 uniformity term.
        self.assertAlmostEqual(calibration_report.family_fail_probability(1, 100),
                               0.01837 + 0.0001, places=4)
        self.assertEqual(calibration_report.family_fail_probability(8, 54), 1.0)

    def test_expected_multi_family_rate_within_k_max_design(self):
        # k_max was chosen so the proportion-only family failure is <= 1%.
        for n_sub in (2, 8, 18, 148):
            p = calibration_report.family_fail_probability(n_sub, 100)
            self.assertLess(p, 0.0125)
            self.assertGreater(p, 0.0)


def synthetic_records(n, fail_pattern):
    recs = []
    for i in range(n):
        fa, fb = fail_pattern(i)
        sub = {"m_prime": 100, "ok": True, "proportion_ok": True, "uniformity_ok": True}
        recs.append({
            "families": {"frequency": {"pass": not fa, "n_sub": 1},
                         "runs": {"pass": not fb, "n_sub": 1}},
            "subtests": {"frequency": [dict(sub, ok=not fa, proportion_ok=not fa)],
                         "runs": [dict(sub, ok=not fb, uniformity_ok=not fb)]},
            "verdict": "fail" if (fa or fb) else "pass",
        })
    return recs


class TestSummary(unittest.TestCase):
    def test_counts_cofailure_and_implied_pass(self):
        # Runs 0-9 fail both families, 10-19 only frequency, rest pass.
        recs = synthetic_records(100, lambda i: (i < 20, i < 10))
        s = calibration_report.summarize(recs)
        self.assertEqual(s["overall"]["failures"], 20)
        self.assertEqual(s["per_family"]["frequency"]["failures"], 20)
        self.assertEqual(s["per_family"]["runs"]["failures"], 10)
        self.assertEqual(s["failing_family_count"], [80, 10, 10])
        pair = s["co_failure"][0]
        self.assertEqual((pair["a"], pair["b"], pair["both"]), ("frequency", "runs", 10))
        self.assertAlmostEqual(pair["expected_independent"], 2.0)
        self.assertLess(pair["fisher_p"], 1e-6)
        self.assertAlmostEqual(s["implied_pass_probability"]["value"], 0.64)
        self.assertEqual(s["per_subtest"]["runs[0]"]["uniformity"]["failures"], 10)
        self.assertEqual(s["per_subtest"]["frequency[0]"]["proportion"]["failures"], 20)
        self.assertFalse(s["per_family"]["frequency"]["consistent"])

    def test_report_requires_all_runs_and_is_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(calibrate, "RUNS", 3), \
                mock.patch.object(calibrate, "score", fake_score), \
                mock.patch.object(calibrate, "N_BITS", 64):
            runs, out = Path(tmp) / "runs", Path(tmp) / "summary.json"
            self.assertEqual(quiet(calibrate.main, ["--workers", "1", "--out-dir", str(runs),
                                                    "--runs", "0-1"]), 0)
            argv = ["--runs-dir", str(runs), "--out", str(out)]
            self.assertEqual(quiet(calibration_report.main, argv), 2)
            self.assertFalse(out.exists())
            self.assertEqual(quiet(calibrate.main, ["--workers", "1", "--out-dir", str(runs),
                                                    "--runs", "0-2", "--resume"]), 0)
            with mock.patch.object(calibrate, "N_BITS", 64):
                self.assertEqual(quiet(calibration_report.main, argv), 0)
            first = out.read_bytes()
            self.assertEqual(quiet(calibration_report.main, argv), 0)
            self.assertEqual(out.read_bytes(), first)
            self.assertTrue((runs / "SHA256SUMS").exists())
            self.assertTrue(out.with_suffix(".md").exists())


if __name__ == "__main__":
    unittest.main()
