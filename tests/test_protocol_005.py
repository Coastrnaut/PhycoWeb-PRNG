"""Feature 005: the tests of its protocol machinery (tasks T006 to T009 and later).

The feature is a setting, PHYCOWEB_FEATURE (research R9; data-model section 1; contracts/cli.md,
"The feature setting"): feature 004 by default, feature 005's paths, model ID, candidate IDs,
development inputs and disclaimer under 005. Feature 004's records, logs and documents are never
written (spec FR-003). No test here makes a heavy run.

This file makes no security claim.
"""
import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from protocol import candidates, changelog, devinputs_v3, evidence, provenance
from protocol.disclaimer import DESIGN_DISCLAIMER, DESIGN_DISCLAIMER_005
from protocol.evidence import Refused
from tests.support_004 import TempRepo, write

ROOT = Path(__file__).resolve().parents[1]
PATHS_004 = {
    "REP_REL": "reports/004-crypto-architecture-v3",
    "FEATURE_REL": "specs/004-crypto-architecture-v3",
    "SPEC_REL": "specs/004-crypto-architecture-v3/spec.md",
    "RESEARCH_REL": "specs/004-crypto-architecture-v3/research.md",
    "DESIGN_REL": "specs/004-crypto-architecture-v3/design.md",
    "PROTOCOL_LOG_REL": "research/004/protocol-changes.jsonl",
    "CANDIDATE_LOG_REL": "research/004/candidates.jsonl",
    "PROVENANCE_LOG_REL": "reports/004-crypto-architecture-v3/provenance.jsonl",
    "DOWNLOADS_REL": "reports/004-crypto-architecture-v3/downloads.json",
    "SIDECAR_REL": "vectors/phyco-v3/MANIFEST.json",
    "SUPERSEDED_REL": "research/004/candidates/superseded.json",
    "REFUSED_LIST_REL": "research/004/refused-constants.json",
    "LOCAL_REL": "data/local/004",
}
PATHS_005 = {name: value.replace("004-crypto-architecture-v3", "005-crypto-architecture-v4")
             .replace("research/004", "research/005").replace("data/local/004", "data/local/005")
             .replace("phyco-v3", "phyco-v4") for name, value in PATHS_004.items()}
T132 = "reports/004-crypto-architecture-v3/rechecks/recheck-20261110T010625Z-454c1890.json"
T132_SHA256 = "d53424fb529ab2254825c107a2f066dab702f46e66c0ef176787b5d5f6526f21"


def setUpModule():
    evidence.set_feature("005")


def tearDownModule():
    evidence.set_feature(evidence.ENTRY_FEATURE)


def feature_004_status() -> str:
    """What git says of feature 004's paths: nothing while they are as committed."""
    done = subprocess.run(["git", "status", "--porcelain", "--", *evidence.feature_roots("004")[:4]],
                          cwd=ROOT, capture_output=True, text=True, check=True)
    return done.stdout


class TheSetting(unittest.TestCase):
    """Research R9: one setting selects the paths, the model ID, the candidate IDs, the development
    inputs and the disclaimer; feature 004 is its default and keeps every value it had."""

    def setUp(self):
        self.addCleanup(evidence.set_feature, evidence.FEATURE)

    def test_feature_004_keeps_its_values(self):
        evidence.set_feature("004")
        for name, value in PATHS_004.items():
            self.assertEqual(getattr(evidence, name), value, name)
        self.assertEqual(evidence.MODEL_ID, "phyco-v3")
        self.assertEqual(devinputs_v3.PREFIX, "phycoweb-004/")
        self.assertEqual(evidence.FEATURE_DISCLAIMER, DESIGN_DISCLAIMER)
        self.assertTrue(candidates.CANDIDATE_ID.fullmatch("cand-A1"))
        self.assertIsNone(candidates.CANDIDATE_ID.fullmatch("v4-A1"))
        self.assertEqual(candidates.LOG, PATHS_004["CANDIDATE_LOG_REL"])
        self.assertEqual(changelog.LOG, PATHS_004["PROTOCOL_LOG_REL"])
        self.assertEqual(changelog.PLACE_CHECK_REL, "research/004/place-check.json")
        self.assertEqual(provenance.LOG, PATHS_004["PROVENANCE_LOG_REL"])

    def test_feature_005_has_data_model_section_1s_values(self):
        evidence.set_feature("005")
        for name, value in PATHS_005.items():
            self.assertEqual(getattr(evidence, name), value, name)
        self.assertEqual(evidence.MODEL_ID, "phyco-v4")
        self.assertEqual(devinputs_v3.PREFIX, "phycoweb-005/")
        self.assertTrue(candidates.CANDIDATE_ID.fullmatch("v4-A1"))
        self.assertTrue(candidates.CANDIDATE_ID.fullmatch("v4-B3"))
        self.assertIsNone(candidates.CANDIDATE_ID.fullmatch("cand-A1"))
        self.assertIsNone(candidates.CANDIDATE_ID.fullmatch("v4-A4"))
        self.assertEqual(candidates.LOG, PATHS_005["CANDIDATE_LOG_REL"])
        self.assertEqual(candidates.CANDIDATES_REL, "research/005/candidates")
        self.assertEqual(changelog.LOG, PATHS_005["PROTOCOL_LOG_REL"])
        self.assertEqual(changelog.CHOICES_REL, "specs/005-crypto-architecture-v4/checklist-choices.md")
        self.assertEqual(changelog.PLACE_CHECK_REL, "research/005/place-check.json")
        self.assertEqual(changelog.PLACE_CHECK_SCRIPT, "research/005/place_check.py")
        self.assertEqual(provenance.LOG, PATHS_005["PROVENANCE_LOG_REL"])
        self.assertEqual(provenance.RATIONALE_REL, "specs/005-crypto-architecture-v4/rationale.md")

    def test_the_disclaimer_is_the_specs_word_for_word(self):
        """FR-026: the block that opens the spec, its lines joined by single spaces."""
        lines = (ROOT / PATHS_005["SPEC_REL"]).read_bytes().decode("utf-8").split("\n")
        first = next(i for i, line in enumerate(lines) if line.startswith(">"))
        block = []
        while lines[first].startswith(">"):
            block.append(lines[first][1:].strip())
            first += 1
        self.assertEqual(" ".join(block), DESIGN_DISCLAIMER_005)
        evidence.set_feature("005")
        self.assertEqual(evidence.FEATURE_DISCLAIMER, DESIGN_DISCLAIMER_005)
        self.assertIn("`phyco-v4`", DESIGN_DISCLAIMER_005)

    def test_the_locks_are_one_for_both_features(self):
        seen = set()
        for name in ("004", "005"):
            evidence.set_feature(name)
            seen.add((evidence.HEAVY_LOCK_REL, evidence.APPEND_LOCK_REL))
        self.assertEqual(seen, {("data/heavy-run.lock", "data/log-append.lock")})

    def test_another_value_is_refused(self):
        with self.assertRaises(Refused):
            evidence.set_feature("006")
        self.assertIn(evidence.FEATURE, ("004", "005"))

    def test_a_script_exits_2_on_another_value(self):
        env = dict(os.environ, PHYCOWEB_FEATURE="006")
        for script in ("scripts/candidate_log.py", "scripts/recheck_004.py"):
            done = subprocess.run([sys.executable, script, "--help"], cwd=ROOT, env=env,
                                  capture_output=True, text=True)
            self.assertEqual(done.returncode, 2, script)
            self.assertIn("names no known feature", done.stderr)

    def test_the_setting_is_read_from_the_environment(self):
        code = "from protocol import evidence as e; print(e.FEATURE, e.ENTRY_FEATURE, e.REP_REL)"
        for value, rep in (("005", PATHS_005["REP_REL"]), (None, PATHS_004["REP_REL"])):
            env = {k: v for k, v in os.environ.items() if k != "PHYCOWEB_FEATURE"}
            if value:
                env["PHYCOWEB_FEATURE"] = value
            done = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env,
                                  capture_output=True, text=True, check=True)
            self.assertEqual(done.stdout.split(), [value or "004", value or "004", rep])

    def test_no_path_of_another_feature_is_written(self):
        evidence.set_feature("005")
        for rel in ("reports/004-crypto-architecture-v3/x.json", "research/004/candidates.jsonl",
                    "specs/004-crypto-architecture-v3/design.md", "data/local/004/x",
                    "vectors/phyco-v3/MANIFEST.json"):
            with self.assertRaises(Refused, msg=rel):
                evidence.guard_feature_path(rel)
        for rel in ("reports/005-crypto-architecture-v4/x.json", "research/005/candidates.jsonl",
                    "protocol/claims.json", "data/heavy-run.lock"):
            evidence.guard_feature_path(rel)
        evidence.set_feature("004")
        with self.assertRaises(Refused):
            evidence.guard_feature_path("research/005/candidates.jsonl")
        evidence.guard_feature_path("research/004/candidates.jsonl")


class DevelopmentInputs(unittest.TestCase):
    """FR-028: feature 004's derivation under phycoweb-005/, and no other namespace."""

    def setUp(self):
        self.addCleanup(evidence.set_feature, evidence.FEATURE)

    def test_each_feature_derives_under_its_own_namespace(self):
        evidence.set_feature("005")
        key_005 = devinputs_v3.load("dev", "key", ("dev",), 2)[0]
        self.assertEqual(key_005, hashlib.sha256(b"phycoweb-005/dev/key/0").digest())
        states = devinputs_v3.load("control", "state", ("control",), 1, n=4, w=32)
        self.assertEqual(len(states[0]), 32)
        evidence.set_feature("004")
        key_004 = devinputs_v3.load("dev", "key", ("dev",), 2)[0]
        self.assertEqual(key_004, hashlib.sha256(b"phycoweb-004/dev/key/0").digest())
        self.assertNotEqual(key_004, key_005)

    def test_feature_005s_fingerprints_are_its_own(self):
        evidence.set_feature("005")
        self.assertIs(devinputs_v3.FINGERPRINTS, devinputs_v3.FINGERPRINTS_005)
        for n, w in devinputs_v3.PAIRS:
            self.assertEqual(devinputs_v3.fingerprint("dev", "state", n, w),
                             devinputs_v3.FINGERPRINTS_005["dev"]["state"][(n, w)])
            self.assertNotEqual(devinputs_v3.FINGERPRINTS_005["dev"]["state"][(n, w)],
                                devinputs_v3.FINGERPRINTS_BY_FEATURE["004"]["dev"]["state"][(n, w)])
        with self.assertRaises(devinputs_v3.InputRefused):
            devinputs_v3.load("control", "key", ("control",), 1)
        with self.assertRaises(devinputs_v3.InputRefused):
            devinputs_v3.load("dev", "key", ("control",), 1)


class TempRepo005(TempRepo):
    """A temporary repository built under feature 005's paths."""

    def setUp(self):
        self.addCleanup(evidence.set_feature, evidence.set_feature("005"))
        super().setUp()


class Records(TempRepo005):
    """Data-model section 1: every record of this feature holds `feature` and the setting it was
    written under, and none is written under another feature's paths."""

    def simple(self, **kwargs):
        return evidence.write_simple_record("lock-cleared", "locks", {"lock": "none"},
                                            writes_evidence=False, **kwargs)

    def test_a_record_holds_its_feature_and_the_setting(self):
        path = self.simple()
        record = json.loads(path.read_bytes().decode("utf-8"))
        self.assertEqual(record["feature"], "005")
        self.assertEqual(record["config"]["PHYCOWEB_FEATURE"], "005")
        self.assertEqual(record["disclaimer"], DESIGN_DISCLAIMER_005)
        self.assertTrue(evidence.rel_to_repo(path).startswith(PATHS_005["REP_REL"] + "/locks/"))
        self.assertTrue(evidence.check_record_id(record))

    def test_a_record_without_the_field_is_feature_004s(self):
        committed = sorted((ROOT / PATHS_004["REP_REL"] / "validation").glob("*.json"))[0]
        self.assertNotIn("feature", json.loads(committed.read_bytes().decode("utf-8")))
        evidence.set_feature("004")
        self.addCleanup(evidence.set_feature, "005")
        run = evidence.Run("lock-cleared", directory="locks", writes_evidence=False,
                           environment={"none": "none"})
        run.protocol = ("none", "none")
        run.start = {}
        self.assertNotIn("feature", run.common_fields())
        self.assertNotIn("PHYCOWEB_FEATURE", run.common_fields()["config"])

    def test_a_record_whose_feature_and_path_disagree_is_refused(self):
        run = evidence.Run("lock-cleared", directory="locks", writes_evidence=False)
        with run:
            record = run.prepare("pass", fields={"lock": "none"})
            record["feature"] = "004"
            with self.assertRaises(Refused):
                run.write(record)
            self.assertEqual(list((self.root / PATHS_005["REP_REL"]).rglob("lock-cleared-*.json")), [])
            run.finished = True

    def test_no_record_is_written_under_feature_004s_paths(self):
        run = evidence.Run("generator-run", directory="research/004/exploration", writes_evidence=False)
        with run:
            record = run.prepare("pass", fields={})
            with self.assertRaises(Refused):
                run.write(record)
            run.finished = True
        self.assertFalse((self.root / "research/004/exploration").exists())
        with self.assertRaises(Refused):
            evidence.append_entry(PATHS_004["CANDIDATE_LOG_REL"], {"event": "proposed"})
        self.assertFalse((self.root / PATHS_004["CANDIDATE_LOG_REL"]).exists())

    def test_a_cited_document_is_copied_under_this_features_paths(self):
        evidence.keep_version("spec-versions", b"a spec\n")
        digest = hashlib.sha256(b"a spec\n").hexdigest()
        self.assertTrue((self.root / PATHS_005["REP_REL"] / "spec-versions" / f"{digest}.md").exists())


class Feature004Read(TempRepo005):
    """What this feature reads of feature 004's, under the setting 005: its validation records
    (research R14), its downloads manifest (FR-001) and its FUT-SEC-8 review and demonstration
    (FR-030)."""

    def validation(self, outcome="re-found", created="2026-11-04T00:00:00Z"):
        record = {"kind": "validation", "tool": "fake tool", "tool_sha256": "ab" * 32,
                  "outcome": outcome, "validated_kind": "bound", "created_utc": created,
                  "code_sha256": {}}
        record["record_id"] = evidence.record_id_for(record)
        write(self.root, f"{PATHS_004['REP_REL']}/validation/{record['record_id']}.json",
              evidence.pretty(record))
        return record

    def test_feature_004s_validation_stays_in_force(self):
        self.assertIsNone(evidence.validation_record("fake tool", "ab" * 32))
        record = self.validation()
        found = evidence.validation_record("fake tool", "ab" * 32)
        self.assertEqual(found["record_id"], record["record_id"])
        self.assertIsNone(evidence.validation_record("fake tool", "cd" * 32))
        self.commit("a validation of feature 004")
        cited = evidence.validation_citation("fake tool", "ab" * 32)
        self.assertEqual(cited["record_id"], record["record_id"])

    def test_under_feature_004_only_its_own_are_read(self):
        record = {"kind": "validation", "tool": "fake tool", "tool_sha256": "ab" * 32,
                  "outcome": "re-found", "created_utc": "2026-11-04T00:00:00Z", "code_sha256": {}}
        record["record_id"] = evidence.record_id_for(record)
        write(self.root, f"{PATHS_005['REP_REL']}/validation/{record['record_id']}.json",
              evidence.pretty(record))
        self.assertIsNotNone(evidence.validation_record("fake tool", "ab" * 32))
        evidence.set_feature("004")
        self.addCleanup(evidence.set_feature, "005")
        self.assertIsNone(evidence.validation_record("fake tool", "ab" * 32))

    def test_feature_004s_downloads_manifest_is_read_as_its_own(self):
        write(self.root, PATHS_004["DOWNLOADS_REL"],
              evidence.pretty({"entries": [{"name": "Daemen.pdf", "state": "fetched", "sha256": "0" * 64}]}))
        self.assertEqual(evidence.read_manifest(), [])
        self.assertEqual(evidence.read_manifest("004")[0]["name"], "Daemen.pdf")

    def test_the_instantiation_guard_reads_feature_004s_row_and_record(self):
        with self.assertRaises(Refused):
            evidence.guard_order_of_us1()
        record = {"kind": "demonstration", "created_utc": "2026-11-04T16:56:04Z", "status": "pass"}
        record["record_id"] = evidence.record_id_for(record)
        rel = f"fut-sec-8/{record['record_id']}.json"
        path = write(self.root, f"{PATHS_004['REP_REL']}/{rel}", evidence.pretty(record))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        head = "# Spec\n\n## Review & Approval\n\n| Gate | Reviewer | Date | Decision | Notes |\n|---|---|---|---|---|\n"
        write(self.root, PATHS_004["SPEC_REL"],
              head + f"| FUT-SEC-8 result review | owner | 2026-11-04 | Approved | {rel} {digest} |\n\n## Next\n")
        self.commit("feature 004's review and demonstration")
        evidence.guard_order_of_us1()
        self.assertEqual(evidence.latest_demonstration()[1]["record_id"], record["record_id"])


class Rows(TempRepo005):
    """Feature 005's rows: a candidate's by its family from the projection table, the feature-wide
    row from that table or, before it exists, from the approved option of plan-projections.json;
    feature 004's constants stay its own."""

    OPTION = {"approved_option": "E", "options": {"E": {"feature_wide_row_h": 102.0}}}
    TABLE = {"rows": {"ARX": {"trails": {"plan_h": 195.5, "holds_h": 190.0},
                              "structural": {"plan_h": 24.0, "holds_h": 24.0},
                              "bias": {"plan_h": 48.0, "holds_h": 40.0}},
                      "Boolean": {"trails": {"plan_h": 353.3, "holds_h": 353.3},
                                  "structural": {"plan_h": 24.0, "holds_h": 24.0},
                                  "bias": {"plan_h": 48.0, "holds_h": 48.0}}},
             "feature_wide_row": {"plan_h": 102.0, "holds_h": 96.0}}

    def test_the_feature_wide_row_before_and_after_the_table(self):
        with self.assertRaises(Refused):
            evidence.feature_row_hours()
        write(self.root, evidence.PLAN_PROJECTIONS_REL, json.dumps(self.OPTION))
        self.assertEqual(evidence.feature_row_hours(), 102.0)
        write(self.root, f"{PATHS_005['REP_REL']}/projection-table.json", json.dumps(self.TABLE))
        self.assertEqual(evidence.feature_row_hours(), 96.0)

    def test_a_candidates_rows_come_by_family_from_the_table(self):
        with self.assertRaises(Refused):
            evidence.row_hours("v4-A1", "trails")
        write(self.root, f"{PATHS_005['REP_REL']}/projection-table.json", json.dumps(self.TABLE))
        self.assertEqual(evidence.row_hours("v4-A1", "trails"), 190.0)
        self.assertEqual(evidence.row_hours("v4-A2", "statistics"), 40.0)
        self.assertEqual(evidence.row_hours("v4-B1", "trails"), 353.3)
        self.assertEqual(evidence.row_hours("v4-B3", "structural"), 24.0)
        self.assertEqual(candidates.left_in_row("v4-B1", "trails"), 353.3)
        with self.assertRaises(Refused):
            evidence.row_hours("cand-A1", "trails")
        with self.assertRaises(Refused):
            evidence.guard_candidate_row("v4-A1", "trails", 200.0)
        evidence.guard_candidate_row("v4-A1", "trails", 100.0, 80.0)

    def test_feature_004_keeps_its_constants(self):
        evidence.set_feature("004")
        self.addCleanup(evidence.set_feature, "005")
        self.assertEqual(evidence.row_hours("cand-A1", "trails"), 48.0)
        self.assertEqual(evidence.row_hours("cand-B1", "statistics"), 12.0)
        self.assertEqual(evidence.feature_row_hours(), 66.0)

    def test_the_candidate_log_takes_this_features_ids_only(self):
        self.assertEqual(candidates.guard_candidate({"candidate_id": "v4-B2"}), ("v4-B2", "Boolean"))
        with self.assertRaises(Refused):
            candidates.guard_candidate({"candidate_id": "cand-A1"})


class Feature004Untouched(unittest.TestCase):
    """FR-003: the setting leaves feature 004's verdicts as they were, and no run of this feature
    writes under feature 004's paths. These tests run feature 004's own re-check, which takes
    minutes and writes nothing."""

    def test_the_recheck_gives_t132s_result_and_writes_nothing(self):
        record = (ROOT / T132).read_bytes()
        self.assertEqual(hashlib.sha256(record).hexdigest(), T132_SHA256)
        before = json.loads(record.decode("utf-8"))
        status = feature_004_status()
        env = {k: v for k, v in os.environ.items() if k != "PHYCOWEB_FEATURE"}
        done = subprocess.run([sys.executable, "-X", "utf8", "scripts/recheck_004.py", "--no-record"],
                              cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(done.returncode, 0, done.stderr[-400:])
        after = json.loads(done.stdout.split("\n")[0])
        self.assertEqual(after["results"], before["results"])
        self.assertEqual(after["disagreements"], before["disagreements"])
        self.assertEqual(after["decisions_checked"], before["decisions_checked"])
        self.assertEqual(sum(row["checked"] for row in after["results"].values()), 160)
        self.assertEqual(after["disagreements"], [])
        self.assertEqual(feature_004_status(), status)

    def test_feature_004s_tests_run_under_005_and_write_nothing_of_its_paths(self):
        status = feature_004_status()
        env = dict(os.environ, PHYCOWEB_FEATURE="005")
        done = subprocess.run([sys.executable, "-X", "utf8", "-W", "ignore", "-m", "unittest",
                               "tests.test_refused_sources", "tests.test_devinputs_v3", "tests.test_ir",
                               "tests.test_records_004.RecordIds", "tests.test_records_004.Disclaimers"],
                              cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(done.returncode, 0, done.stderr[-600:])
        self.assertEqual(feature_004_status(), status)


if __name__ == "__main__":
    unittest.main()
