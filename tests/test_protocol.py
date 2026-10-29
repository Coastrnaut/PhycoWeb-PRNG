"""Protocol tests for feature 002: seed sets (FR-015, SC-006, data-model section 2)."""
import hashlib
import importlib
import json
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from protocol import freeze, seedsets

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

SPEC_TABLE = {
    "dev": ((56053, 7029, 30841, 11050),
            "7e7e33c75e9e58048a26c1926e6addd4dc3514502574ea6687ded889aa47950e"),
    "heldout-1": ((44401, 31074, 35395, 61291),
                  "84a30b2e037550d0c6b1cfba1444eb0447fbc15b5b7c631ad8fc8a577dfca23d"),
    "heldout-2": ((61805, 51202, 28895, 20558),
                  "13120fcb1c1a49f6e6109f059982909470da33784bd0490f1e0f10252e214ad4"),
    "heldout-3": ((5899, 31471, 52105, 42678),
                  "af3b9b8e62829ef732a5c2bb2963c7655c9b461635da0c40d960b4c7eaace88f"),
}


class TestSeedSets(unittest.TestCase):
    def test_sets_match_spec_table(self):
        for name, (first, digest) in SPEC_TABLE.items():
            seeds = seedsets.derive(name)
            self.assertEqual(len(seeds), 100, name)
            self.assertEqual(len(set(seeds)), 100, name)
            self.assertEqual(seeds[0], first, name)
            text = seedsets.canonical_text(seeds).encode("ascii")
            self.assertEqual(hashlib.sha256(text).hexdigest(), digest, name)
            self.assertEqual(seedsets.FINGERPRINTS[name], digest, name)

    def test_sets_are_disjoint(self):
        sets = [set(seedsets.derive(name)) for name in SPEC_TABLE]
        for i in range(len(sets)):
            for j in range(i + 1, len(sets)):
                self.assertFalse(sets[i] & sets[j])

    def test_seed_values_in_domain(self):
        for name in SPEC_TABLE:
            for seed in seedsets.derive(name):
                self.assertEqual(len(seed), 4)
                self.assertTrue(all(type(v) is int and 0 <= v <= 0xFFFF for v in seed))

    def test_tampered_fingerprint_rejected(self):
        bad = dict(seedsets.FINGERPRINTS, dev="0" * 64)
        with mock.patch.object(seedsets, "FINGERPRINTS", bad):
            with self.assertRaises(ValueError):
                seedsets.load("dev", allow={"dev"})

    def test_allow_list_blocks_heldout(self):
        for name in ("heldout-1", "heldout-2", "heldout-3"):
            with self.assertRaises(PermissionError):
                seedsets.load(name, allow={"dev"})
        self.assertEqual(len(seedsets.load("dev", allow={"dev"})), 100)

    def test_unknown_set_rejected(self):
        with self.assertRaises(ValueError):
            seedsets.load("heldout-4", allow={"heldout-4"})


class TestExploreGuard(unittest.TestCase):
    """explore.py refuses held-out seed sets and logs nothing (T032; SC-006)."""

    ROOT = Path(__file__).resolve().parents[1]
    RUNS = ROOT / "research" / "002" / "runs.jsonl"

    def _runs(self):
        return self.RUNS.read_bytes() if self.RUNS.exists() else None

    def test_heldout_refused(self):
        for name in ("heldout-1", "heldout-2", "heldout-3", "nonsense"):
            before = self._runs()
            proc = subprocess.run([sys.executable, str(self.ROOT / "research" / "002" / "explore.py"),
                                   "--variant", "any", "--set", name],
                                  capture_output=True, text=True, cwd=self.ROOT)
            self.assertEqual(proc.returncode, 2, name)
            self.assertEqual(self._runs(), before, name)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class _TempReports(unittest.TestCase):
    """Point protocol.freeze at an empty temporary reports directory."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        patcher = mock.patch.object(freeze, "REPORTS", self.tmp / "reports")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.dev = self.tmp / "dev-final.json"
        self.dev.write_text("{}", encoding="utf-8")

    def write_freeze(self, n, approved=True, **overrides):
        record = {"attempt": n, "seed_set": f"heldout-{n}", "status": "draft", "git_head": "x"}
        record.update(freeze.current())
        record["dev_evidence"] = str(self.dev)
        record["approved_by"] = "owner" if approved else ""
        record["approved_on"] = "2026-10-28" if approved else ""
        record.update(overrides)
        freeze.attempt_dir(n).mkdir(parents=True, exist_ok=True)
        freeze.freeze_path(n).write_text(json.dumps(record), encoding="utf-8")
        return record


class TestFreeze(_TempReports):
    """T046 (FR-016, data-model section 3)."""

    def create(self, n, status=""):
        return freeze.create(n, self.dev, status=lambda: status, head=lambda: "abc123")

    def test_draft_has_empty_approval_and_true_hashes(self):
        import sp80022
        record = self.create(1)
        on_disk = json.loads(freeze.freeze_path(1).read_text(encoding="utf-8"))
        self.assertEqual(record, on_disk)
        self.assertEqual(on_disk["approved_by"], "")
        self.assertEqual(on_disk["approved_on"], "")
        self.assertEqual(on_disk["seed_set"], "heldout-1")
        self.assertEqual(on_disk["model_sha256"], _sha256(ROOT / freeze.MODEL))
        self.assertEqual(on_disk["lut_sha256"], _sha256(ROOT / freeze.LUT))
        self.assertEqual(on_disk["design_sha256"], _sha256(ROOT / freeze.DESIGN))
        self.assertEqual(on_disk["harness_sha256"], sp80022.source_sha256())
        self.assertEqual(on_disk["harness_version"], sp80022.__version__)
        self.assertEqual(on_disk["design_version"], "1.0")
        self.assertEqual(on_disk["warmup"], 256)

    def test_refuses_attempt_that_is_not_next(self):
        for n in (0, 2, 3, 4):
            with self.assertRaises(freeze.FreezeError, msg=n):
                self.create(n)
        self.assertFalse(freeze.REPORTS.exists())

    def test_next_attempt_follows_attempt_records(self):
        freeze.attempt_dir(1).mkdir(parents=True)
        (freeze.attempt_dir(1) / "attempt.json").write_text("{}", encoding="utf-8")
        self.assertEqual(freeze.next_attempt(), 2)
        self.assertEqual(self.create(2)["seed_set"], "heldout-2")

    def test_refuses_existing_attempt_directory(self):
        freeze.attempt_dir(1).mkdir(parents=True)
        with self.assertRaises(freeze.FreezeError):
            self.create(1)
        self.assertFalse(freeze.freeze_path(1).exists())

    def test_refuses_uncommitted_changes(self):
        for dirty in (" M phycoweb/model_v2.py", " M specs/002-core-dynamics-redesign/design.md",
                      "?? sp80022/new.py"):
            with self.assertRaises(freeze.FreezeError, msg=dirty):
                self.create(1, status=dirty)
        self.assertFalse(freeze.attempt_dir(1).exists())

    def test_cli_refusal_exits_2(self):
        script = runpy.run_path(str(ROOT / "scripts" / "freeze.py"), run_name="freeze_cli")
        self.assertEqual(script["main"](["--attempt", "2", "--dev-evidence", str(self.dev)]), 2)


class TestAcceptanceGuard(_TempReports):
    """T047 (FR-016, FR-017, FR-018, SC-006). The evaluator is mocked: nothing is generated."""

    def setUp(self):
        super().setUp()
        self.acceptance = importlib.import_module("acceptance")
        self.calls = []
        self.verdicts = {"positive": "pass", "negative": "fail", "candidate": "pass"}

        def fake_evaluate(role, n, seeds, workers, command):
            self.calls.append(role)
            self.assertEqual(len(seeds), 100)
            return {"verdict": self.verdicts[role], "families_failed": []}

        for target, name, value in ((self.acceptance, "evaluate", fake_evaluate),
                                    (self.acceptance.evalcore, "write_record",
                                     lambda path, record: None)):
            patcher = mock.patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_attempt(self, n=1):
        return self.acceptance.main(["--attempt", str(n), "--workers", "1"])

    def assert_refused(self, n=1):
        self.assertEqual(self.run_attempt(n), 2)
        self.assertEqual(self.calls, [])

    def test_missing_freeze(self):
        self.assert_refused()

    def test_unapproved_freeze(self):
        self.write_freeze(1, approved=False)
        self.assert_refused()
        self.write_freeze(1, approved=True, approved_on=" ")
        self.assert_refused()

    def test_hash_mismatch(self):
        for field in ("model_sha256", "lut_sha256", "design_sha256", "harness_sha256",
                      "harness_version", "design_version", "warmup"):
            with self.subTest(field=field):
                self.write_freeze(1, **{field: "0"})
                self.assert_refused()

    def test_attempt_record_exists(self):
        self.write_freeze(1)
        (freeze.attempt_dir(1) / "attempt.json").write_text("{}", encoding="utf-8")
        self.assert_refused()

    def test_started_attempt_not_rerun(self):
        self.write_freeze(1)
        (freeze.attempt_dir(1) / "started.json").write_text("{}", encoding="utf-8")
        self.assert_refused()

    def test_attempt_beyond_three_or_not_next(self):
        self.write_freeze(4)
        self.assert_refused(4)
        self.write_freeze(2)
        self.assert_refused(2)

    def test_order_and_pass(self):
        from protocol.disclaimer import DISCLAIMER
        self.write_freeze(1)
        self.assertEqual(self.run_attempt(), 0)
        self.assertEqual(self.calls, ["positive", "negative", "candidate"])
        attempt = json.loads((freeze.attempt_dir(1) / "attempt.json").read_text(encoding="utf-8"))
        self.assertEqual(attempt["overall"], "PASS")
        self.assertEqual([o["role"] for o in attempt["order"]],
                         ["positive", "negative", "candidate"])
        self.assertEqual(attempt["freeze_sha256"], _sha256(freeze.freeze_path(1)))
        summary = (freeze.attempt_dir(1) / "summary.md").read_text(encoding="utf-8")
        self.assertIn(DISCLAIMER, summary)
        # The attempt is now used: running it again is refused.
        self.calls.clear()
        self.assert_refused()

    def test_positive_control_failure_skips_candidate(self):
        self.write_freeze(1)
        self.verdicts["positive"] = "fail"
        self.assertEqual(self.run_attempt(), 1)
        self.assertEqual(self.calls, ["positive", "negative"])
        attempt = json.loads((freeze.attempt_dir(1) / "attempt.json").read_text(encoding="utf-8"))
        self.assertEqual(attempt["overall"], "INCONCLUSIVE")
        self.assertEqual(attempt["candidate"], self.acceptance.NOT_RUN)
        self.assertEqual(freeze.next_attempt(), 2)

    def test_negative_control_pass_is_inconclusive(self):
        self.write_freeze(1)
        self.verdicts["negative"] = "pass"
        self.assertEqual(self.run_attempt(), 1)
        self.assertEqual(self.calls, ["positive", "negative", "candidate"])
        attempt = json.loads((freeze.attempt_dir(1) / "attempt.json").read_text(encoding="utf-8"))
        self.assertEqual(attempt["overall"], "INCONCLUSIVE")

    def test_candidate_fail(self):
        self.write_freeze(1)
        self.verdicts["candidate"] = "fail"
        self.assertEqual(self.run_attempt(), 1)
        attempt = json.loads((freeze.attempt_dir(1) / "attempt.json").read_text(encoding="utf-8"))
        self.assertEqual(attempt["overall"], "FAIL")


class TestRescoreAttempt(_TempReports):
    """T050: a re-score of an attempt reproduces its records, and detects a change (SC-004).

    Uses dev seeds and short sequences in a temporary directory; no held-out seed is used.
    """

    def setUp(self):
        super().setUp()
        self.rescore = importlib.import_module("rescore_attempt")
        self.evalcore = self.rescore.evalcore
        out = freeze.attempt_dir(1)
        out.mkdir(parents=True)
        n_bits = 2 ** 14
        seeds = [list(s) for s in seedsets.load("dev", allow={"dev"})[:2]]
        controls = self.tmp / "control.bin"
        controls.write_bytes(bytes(range(256)) * (2 * n_bits // 8 // 256))
        jobs = [(i, "model", ("phyco-v2", s), n_bits, 0) for i, s in enumerate(seeds)]
        cand = self.evalcore.build_record("phyco-v2", self.evalcore.run_jobs(jobs, 1),
                                          seed_set="dev", seeds=seeds, n_bits=n_bits,
                                          command="test", workers=1, started=0.0)
        raw = controls.read_bytes()
        jobs = [(i, "bytes", raw[i * n_bits // 8:(i + 1) * n_bits // 8], n_bits, 0)
                for i in range(2)]
        pos = self.evalcore.build_record("os-csprng", self.evalcore.run_jobs(jobs, 1),
                                         seed_set=None, seeds=None, n_bits=n_bits, command="test",
                                         workers=1, started=0.0,
                                         extra={"bytes_file": str(controls),
                                                "bytes_sha256": _sha256(controls)})
        for role, rec in (("positive", pos), ("candidate", cand)):
            (out / f"eval-{role}.json").write_text(json.dumps(rec), encoding="utf-8")
        attempt = {"positive": {"record": "eval-positive.json"}, "negative": "not run (test)",
                   "candidate": {"record": "eval-candidate.json"}}
        (out / "attempt.json").write_text(json.dumps(attempt), encoding="utf-8")
        self.out = out

    def test_identical(self):
        self.assertEqual(self.rescore.main(["--attempt", "1", "--workers", "1"]), 0)
        result = json.loads((self.out / "rescore.json").read_text(encoding="utf-8"))
        self.assertTrue(result["identical"])

    def test_detects_changed_record(self):
        path = self.out / "eval-candidate.json"
        rec = json.loads(path.read_text(encoding="utf-8"))
        rec["sequences"][0]["frequency"]["p_values"][0] += 1e-12
        path.write_text(json.dumps(rec), encoding="utf-8")
        self.assertEqual(self.rescore.main(["--attempt", "1", "--workers", "1"]), 1)

    def test_detects_changed_control_bytes(self):
        path = Path(json.loads((self.out / "eval-positive.json").read_text(
            encoding="utf-8"))["bytes_file"])
        raw = path.read_bytes()
        path.write_bytes(bytes([raw[0] ^ 0xFF]) + raw[1:])
        self.assertEqual(self.rescore.main(["--attempt", "1", "--workers", "1"]), 2)


if __name__ == "__main__":
    unittest.main()
