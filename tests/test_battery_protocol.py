"""Feature 003 US2 protocol guards (T021; FR-010 to FR-015, SC-004, SC-005): battery seed sets,
battery freeze, scripts/battery_run.py guards, and scripts/battery_attempt.py order, halting and
verdicts with a fake runner that writes real tool outputs from tests/data/batteries/.
"""
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import battery_attempt  # noqa: E402
import battery_rescore  # noqa: E402
import battery_run  # noqa: E402
from protocol import battery_freeze, battery_seedsets, seedsets  # noqa: E402

DATA = ROOT / "tests" / "data" / "batteries"
DEV_SEED = ("56053", "7029", "30841", "11050")


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*args)


class TestBatterySeedSets(unittest.TestCase):
    def test_first_seeds_and_fingerprints_match_spec(self):
        self.assertEqual(battery_seedsets.derive("heldout-1")[0], (12132, 10603, 3424, 61301))
        self.assertEqual(battery_seedsets.derive("heldout-2")[0], (5338, 17654, 46179, 7977))
        for name in battery_seedsets.ORDER:
            seeds = battery_seedsets.load(name, allow={name})
            self.assertEqual(len(seeds), 10)

    def test_disjoint_from_all_earlier_sets(self):
        earlier = set(seedsets.FEATURE001_SEEDS)
        for name in seedsets.FINGERPRINTS:
            earlier |= set(seedsets.derive(name))
        new = set(battery_seedsets.derive("heldout-1")) | set(battery_seedsets.derive("heldout-2"))
        self.assertEqual(len(new), 20)
        self.assertFalse(new & earlier)

    def test_not_allowed_or_unknown_refused(self):
        with self.assertRaises(PermissionError):
            battery_seedsets.load("heldout-1", allow={"dev"})
        with self.assertRaises(ValueError):
            battery_seedsets.load("heldout-3", allow={"heldout-3"})

    def test_fingerprint_mismatch_refused(self):
        with mock.patch.dict(battery_seedsets.FINGERPRINTS, {"heldout-1": "0" * 64}):
            with self.assertRaises(ValueError):
                battery_seedsets.load("heldout-1", allow={"heldout-1"})


NOW = {"phyco_v2_model_sha256": "a" * 64, "stream_binary_sha256": "b" * 64,
       "tool_binaries": {"practrand:RNG_test": "c" * 64}}


class FreezeBase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p = mock.patch.object(battery_freeze, "REPORTS", Path(tmp.name))
        p.start()
        self.addCleanup(p.stop)

    def create(self, n=1, S=1000, now=None):
        return battery_freeze.create(n, S, {"practrand": "RNG_test stdin32"},
                                     head=lambda: "deadbeef", now=dict(now or NOW))

    def approve(self, n=1):
        rec = battery_freeze.load(n)
        rec.update(approved_by="owner", approved_on="2026-10-30")
        battery_freeze.freeze_path(n).write_text(json.dumps(rec), encoding="utf-8")
        return rec

    def finish(self, n, verdict):
        battery_freeze.attempt_dir(n).mkdir(parents=True, exist_ok=True)
        (battery_freeze.attempt_dir(n) / "attempt.json").write_text(
            json.dumps({"verdict": verdict}), encoding="utf-8")


class TestFreeze(FreezeBase):
    def test_draft_is_unapproved_and_records_S(self):
        rec = self.create()
        self.assertEqual((rec["seed_set"], rec["S"], rec["approved_by"]), ("heldout-1", 1000, ""))
        self.assertAlmostEqual(rec["threshold"], 5e-6)
        problems = battery_freeze.validate(battery_freeze.load(1), 1, now=dict(NOW))
        self.assertTrue(any("approved_by" in p for p in problems))

    def test_approved_freeze_validates(self):
        self.create()
        rec = self.approve()
        self.assertEqual(battery_freeze.validate(rec, 1, now=dict(NOW)), [])

    def test_hash_change_invalidates(self):
        self.create()
        rec = self.approve()
        changed = dict(NOW, stream_binary_sha256="d" * 64)
        self.assertTrue(any("stream_binary_sha256" in p
                            for p in battery_freeze.validate(rec, 1, now=changed)))

    def test_tool_binary_change_invalidates(self):
        self.create()
        rec = self.approve()
        changed = dict(NOW, tool_binaries={"practrand:RNG_test": "e" * 64})
        self.assertTrue(battery_freeze.validate(rec, 1, now=changed))

    def test_missing_binary_refused(self):
        with self.assertRaises(battery_freeze.FreezeError):
            self.create(now=dict(NOW, stream_binary_sha256=None))
        with self.assertRaises(battery_freeze.FreezeError):
            self.create(now=dict(NOW, tool_binaries={}))

    def test_bad_S_refused(self):
        for S in (0, -1, 2.5):
            with self.assertRaises(battery_freeze.FreezeError):
                self.create(S=S)

    def test_existing_freeze_refused(self):
        self.create()
        with self.assertRaises(battery_freeze.FreezeError):
            self.create()


class TestAttemptOrder(FreezeBase):
    def test_attempt_2_not_before_1(self):
        with self.assertRaises(battery_freeze.FreezeError):
            self.create(n=2)

    def test_attempt_2_only_after_inconclusive_or_invalid(self):
        for verdict, allowed in (("INCONCLUSIVE", True), ("INVALID", True),
                                 ("FAIL", False), ("PASS", False)):
            with self.subTest(verdict=verdict):
                self.setUp()
                self.finish(1, verdict)
                if allowed:
                    self.assertEqual(self.create(n=2)["seed_set"], "heldout-2")
                else:
                    with self.assertRaises(battery_freeze.FreezeError):
                        self.create(n=2)

    def test_no_third_attempt(self):
        self.finish(1, "INCONCLUSIVE")
        self.finish(2, "INVALID")
        with self.assertRaises(battery_freeze.FreezeError):
            battery_freeze.next_attempt()
        with self.assertRaises(battery_freeze.FreezeError):
            self.create(n=3)

    def test_started_without_record_blocks(self):
        battery_freeze.attempt_dir(1).mkdir(parents=True)
        (battery_freeze.attempt_dir(1) / "started.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(battery_freeze.FreezeError):
            battery_freeze.next_attempt()


class TestBatteryRunGuards(FreezeBase):
    def run_main(self, *args):
        return quiet(battery_run.main, [*args, "--out", str(battery_freeze.REPORTS / "x")])

    def test_dev_mode_refuses_heldout_seed(self):
        seed = [str(v) for v in battery_seedsets.derive("heldout-1")[0]]
        self.assertEqual(self.run_main("--set", "dev", "--role", "candidate", "--battery",
                                       "smallcrush", "--orientation", "fwd", "--seed", *seed), 2)

    def test_stop_on_fail_only_for_negative(self):
        self.assertEqual(self.run_main("--set", "dev", "--role", "candidate", "--battery",
                                       "practrand", "--orientation", "fwd", "--stop-on-fail",
                                       "--seed", *DEV_SEED), 2)

    def test_role_and_seed_must_match(self):
        self.assertEqual(self.run_main("--set", "dev", "--role", "positive", "--battery",
                                       "smallcrush", "--orientation", "fwd", "--seed", *DEV_SEED), 2)
        self.assertEqual(self.run_main("--set", "dev", "--role", "candidate", "--battery",
                                       "smallcrush", "--orientation", "fwd", "--os"), 2)

    def test_practrand_has_no_rev(self):
        self.assertEqual(self.run_main("--set", "dev", "--role", "positive", "--os", "--battery",
                                       "practrand", "--orientation", "rev"), 2)

    def test_attempt_mode_needs_approved_freeze(self):
        args = ["--role", "positive", "--os", "--battery", "smallcrush", "--orientation", "fwd"]
        self.assertEqual(self.run_main("--attempt", "1", *args), 2)            # no freeze
        with mock.patch.object(battery_freeze, "current", lambda: dict(NOW)):
            self.create()
            self.assertEqual(self.run_main("--attempt", "1", *args), 2)        # not approved
            self.approve()
            self.assertEqual(self.run_main("--attempt", "1", "--practrand-tlmax", "30", *args), 2)

    def test_attempt_mode_refuses_seed_outside_set(self):
        with mock.patch.object(battery_freeze, "current", lambda: dict(NOW)):
            self.create()
            self.approve()
            self.assertEqual(self.run_main("--attempt", "1", "--role", "candidate", "--battery",
                                           "smallcrush", "--orientation", "fwd",
                                           "--seed", *DEV_SEED), 2)


def fake_launcher(calls, bad_roles=(), incomplete=()):
    """Write a real fixture per run: good outputs, or failing ones for bad_roles."""
    def launch(spec, attempt, out):
        calls.append((spec["role"], spec["name"]))
        bad = spec["role"] in bad_roles
        if spec["battery"] == "practrand":
            src = "pr-lut" if bad else "pr-os"
        else:
            src = "sc-lut" if bad else "sc-v2"
        shutil.copytree(DATA / src, out)
        if (spec["role"], spec["name"]) in incomplete:
            meta = json.loads((out / "run.json").read_text(encoding="utf-8"))
            meta["exit_status"] = 3
            (out / "run.json").write_text(json.dumps(meta), encoding="utf-8")
        return 0
    return launch


def all_match(seeds, workers):
    return {"all_match": True, "rows": []}


class TestAttempt(FreezeBase):
    def setUp(self):
        super().setUp()
        for target, name, value in ((battery_freeze, "current", lambda: dict(NOW)),
                                    (battery_freeze, "git_head", lambda: "deadbeef"),
                                    (battery_attempt, "equivalence", all_match)):
            p = mock.patch.object(target, name, value)
            p.start()
            self.addCleanup(p.stop)
        self.calls = []

    def ready(self):
        self.create(S=100000)
        self.approve()

    def attempt(self, launcher=None, n=1):
        with mock.patch.object(battery_attempt, "launch", launcher or fake_launcher(self.calls)):
            return quiet(battery_attempt.main, ["--attempt", str(n), "--slots", "8"])

    def record(self, n=1):
        return json.loads((battery_freeze.attempt_dir(n) / "attempt.json").read_text(encoding="utf-8"))

    def test_refused_without_freeze_or_approval(self):
        self.assertEqual(self.attempt(), 2)
        self.create(S=100000)
        self.assertEqual(self.attempt(), 2)
        self.assertEqual(self.calls, [])

    def test_pass_in_order_and_rescore_identical(self):
        self.ready()
        self.assertEqual(self.attempt(fake_launcher(self.calls, bad_roles=("negative",))), 0)
        rec = self.record()
        self.assertEqual(rec["verdict"], "PASS")
        roles = [r for r, _ in self.calls]
        self.assertEqual(roles, sorted(roles, key=["positive", "negative", "candidate"].index))
        self.assertEqual(len(self.calls), 3 * 70)
        self.assertIn("not be used to generate secrets", rec["disclaimer"])
        self.assertEqual(quiet(battery_rescore.main, ["--attempt", "1"]), 0)
        self.assertEqual(self.attempt(), 2)                                    # never twice

    def test_positive_failure_halts_candidate_but_runs_negative(self):
        self.ready()
        self.assertEqual(self.attempt(fake_launcher(self.calls, bad_roles=("positive", "negative"))), 1)
        rec = self.record()
        self.assertEqual(rec["verdict"], "INCONCLUSIVE")
        self.assertEqual(rec["roles"]["candidate"]["status"], "not_run")
        self.assertEqual(rec["roles"]["negative"]["status"], "run")
        self.assertNotIn("candidate", {r for r, _ in self.calls})

    def test_candidate_failure_is_fail_and_final(self):
        self.ready()
        self.assertEqual(self.attempt(fake_launcher(self.calls, bad_roles=("negative", "candidate"))), 1)
        self.assertEqual(self.record()["verdict"], "FAIL")
        with self.assertRaises(battery_freeze.FreezeError):
            self.create(n=2)

    def test_negative_not_failing_is_inconclusive(self):
        self.ready()
        self.assertEqual(self.attempt(fake_launcher(self.calls)), 1)
        self.assertEqual(self.record()["verdict"], "INCONCLUSIVE")

    def test_incomplete_candidate_run_is_inconclusive(self):
        self.ready()
        launcher = fake_launcher(self.calls, bad_roles=("negative",),
                                 incomplete={("candidate", "bigcrush-rev-seed3")})
        self.assertEqual(self.attempt(launcher), 1)
        rec = self.record()
        self.assertEqual(rec["verdict"], "INCONCLUSIVE")
        self.assertEqual(rec["roles"]["candidate"]["outcome"]["incomplete_runs"],
                         ["bigcrush-rev-seed3"])

    def test_equivalence_mismatch_is_invalid(self):
        self.ready()
        mismatch = {"all_match": False,
                    "rows": [{"model": "phyco-v2", "seed": [1, 2, 3, 4], "mismatches": 1}]}
        with mock.patch.object(battery_attempt, "equivalence", lambda seeds, workers: mismatch):
            self.assertEqual(self.attempt(), 1)
        self.assertEqual(self.record()["verdict"], "INVALID")
        self.assertEqual(self.calls, [])
        self.assertEqual(self.create(n=2)["seed_set"], "heldout-2")            # INVALID allows 2


if __name__ == "__main__":
    unittest.main()
