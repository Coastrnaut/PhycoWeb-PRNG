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
import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from protocol import candidates, changelog, devinputs_v3, evidence, oplist, provenance, trailcheck
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


SPEC_005 = """# Spec

## Review & Approval *(Constitution Principle VIII)*

| Gate | Reviewer | Date | Decision | Notes |
|------|----------|------|----------|-------|
{rows}
Notes under the table.

## Requirements

### Functional Requirements

- **FR-001**: {one}
- **FR-002**: {two}

### Pre-registered Design Protocol: the changed rules

- **A rule**: FR-001. *Stricter means*: no change.
"""
CHOICES_005 = """# Choices

## Round 1 (first run)

| Item | Question | A (recommended) | Alternatives | Where |
|------|----------|-----------------|--------------|-------|
| SEC-001 | A limit | The limit falls | B: no change | spec FR-001 |
| RAT-001 | A word | The word is defined | B: no change | spec FR-002 |

### Rows that change the protocol (round 1)
{pair}
| Row | Rule | Direction | Why |
|-----|------|-----------|-----|
| SEC-001 | A rule (FR-001) | {direction} | the limit only falls |
"""


class ChangeLog(TempRepo005):
    """Spec FR-031: feature 005's first entries, from its lists in their table form: the baseline,
    one entry per listed row and one that lists a round's clarifications."""

    def setUp(self):
        super().setUp()
        (self.root / evidence.PROTOCOL_LOG_REL).unlink()
        self.spec_rows = list(self.rows)
        write(self.root, "research/005/place_check.py",
              (ROOT / "research/005/place_check.py").read_bytes())
        write(self.root, evidence.REFUSED_LIST_REL, (ROOT / evidence.REFUSED_LIST_REL).read_bytes())
        self.write_spec_005("the limit is 8", "a word")
        self.base = self.commit("the plan approval")
        self.write_choices("", "stricter")
        self.choices = self.commit("choices")
        self.write_spec_005("the limit is 4", "a word, defined")
        self.applied = self.commit("applied")
        self.write_choices(f"\nThe round's two commits are {self.choices[:7]} (its choices) and "
                           f"{self.applied[:7]} (its changes applied).\n", "stricter")
        self.commit("the pair")
        original = changelog.place_check

        def module():
            found = original()
            found.PLAN_APPROVAL = self.base
            found.FILES = ()
            return found

        patcher = mock.patch.object(changelog, "place_check", module)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch.object(changelog, "BASELINE_005", ((self.base, evidence.SPEC_REL),))
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_spec_005(self, one: str, two: str) -> None:
        write(self.root, evidence.SPEC_REL,
              SPEC_005.format(rows="".join(line + "\n" for line in self.spec_rows), one=one, two=two))

    def write_choices(self, pair: str, direction: str) -> None:
        write(self.root, changelog.CHOICES_REL, CHOICES_005.format(pair=pair, direction=direction))

    def row(self, gate: str, decision: str, notes: str) -> None:
        self.spec_rows.append(f"| {gate} | owner | 2026-11-12 | {decision} | {notes} |")
        text = (self.root / evidence.SPEC_REL).read_bytes().decode("utf-8")
        one = text.split("**FR-001**: ")[1].split("\n")[0]
        two = text.split("**FR-002**: ")[1].split("\n")[0]
        self.write_spec_005(one, two)
        self.commit(f"row {gate}")

    def compare(self) -> dict:
        result = changelog.check()
        data = (json.dumps(result, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
        write(self.root, changelog.PLACE_CHECK_REL, data)
        self.commit("the comparison")
        self.row("Place check", "Approved", f"names it, {hashlib.sha256(data).hexdigest()}")
        self.row("Readings set aside", "Not needed", "none")
        return result

    def test_the_first_entries_follow_the_lists(self):
        result = self.compare()
        self.assertEqual(result["unmade"], [])
        entries = changelog.build_first_entries_005()
        self.assertEqual([e["granularity"] for e in entries], ["baseline", "round", "round"])
        self.assertEqual(entries[0]["baseline"][0]["path"], evidence.SPEC_REL)
        self.assertEqual(entries[0]["baseline"][0]["sha256_kind"], "raw")
        self.assertEqual(entries[0]["refused_list"]["path"], evidence.REFUSED_LIST_REL)
        rule = entries[1]["rules"][0]
        self.assertEqual((entries[1]["row"]["id"], rule["rule"], rule["direction"]),
                         ("SEC-001", "A rule", "stricter"))
        self.assertIn("the limit is 8", rule["old_text"]["FR-001"])
        self.assertIn("the limit is 4", rule["new_text"]["FR-001"])
        self.assertEqual(rule["commits"], [self.choices, self.applied])
        self.assertEqual(entries[2]["clarifications"], ["RAT-001"])
        self.assertEqual(entries[2]["rules"], [])

    def test_create_writes_the_log_on_the_owners_written_word(self):
        self.compare()
        written = evidence.written_approval("set the rows and commit")
        self.assertEqual(changelog.create(written), 0)
        entries = evidence.check_chain(evidence.PROTOCOL_LOG_REL)
        self.assertEqual(len(entries), 3)
        self.assertTrue(all(e["written_approval"]["entered_by"] == "agent" for e, _ in entries))
        self.commit("the log")
        self.assertEqual(evidence.guard_protocol_log("inverse")[0], 2)
        with self.assertRaises(Refused):
            changelog.create(written)

    def test_a_settled_row_holds_its_reading(self):
        self.write_choices(f"\nThe round's two commits are {self.choices[:7]} (its choices) and "
                           f"{self.applied[:7]} (its changes applied).\n", "settled")
        self.commit("settled")
        self.compare()
        rule = changelog.build_first_entries_005()[1]["rules"][0]
        self.assertEqual(rule["direction"], "settled")
        self.assertEqual(rule["readings"][0]["new_reading"], "The limit falls")

    def test_a_place_changed_after_the_comparison_is_refused(self):
        self.compare()
        self.write_spec_005("the limit is 2", "a word, defined")
        self.commit("a later edit")
        with self.assertRaises(Refused):
            changelog.build_first_entries_005()

    def test_an_undecided_gate_is_refused(self):
        result = changelog.check()
        data = (json.dumps(result, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
        write(self.root, changelog.PLACE_CHECK_REL, data)
        self.commit("the comparison")
        with self.assertRaises(Refused):
            changelog.build_first_entries_005()
        self.row("Place check", "Approved", f"names it, {hashlib.sha256(data).hexdigest()}")
        with self.assertRaises(Refused):
            changelog.build_first_entries_005()


# ------------------------------------------------------------- the re-check of sums and trails

W8 = 8
TRIPLES = ((0x01, 0x00, 0x01), (0x80, 0x80, 0x00), (0x03, 0x05, 0x06), (0x40, 0x40, 0x80),
           (0x11, 0x01, 0x30), (0x7f, 0x01, 0x80), (0x00, 0x00, 0x00), (0xff, 0xff, 0xfe))
CONSTANTS_W8 = (0x01, 0x5d, 0x80, 0xff, 0x00)
PAIRS = ((0x01, 0x01), (0x01, 0x03), (0x80, 0x80), (0x06, 0x1a), (0xff, 0x01), (0x00, 0x00))


def operate(sub: bool):
    return (lambda x, y: (x - y) & 0xff) if sub else (lambda x, y: (x + y) & 0xff)


def sign(*bits: int) -> int:
    return -1 if sum(trailcheck.parity(b) for b in bits) & 1 else 1


def best(key, fixed, free, output, weigh):
    """A chooser for a built characteristic: the first most likely transition, by exhaustive count
    over the outputs, the free input of a mask's addition taken equal to its fixed one."""
    inputs = list(fixed) + ([fixed[0]] if free and fixed else [0] * free)
    if output is not None:
        candidates = [(m, output) for m in range(1 << 4)] if free and not fixed else [(None, output)]
    else:
        candidates = [(None, o) for o in range(1 << W8)]
    found = None
    for free_value, out in candidates:
        trial = inputs if free_value is None else [free_value]
        try:
            weight = weigh(trial, out)
        except IndexError:
            continue
        if weight and (found is None or weight > found[0]):
            found = (weight, list(trial), out)
    if found is None:
        raise AssertionError(f"no transition of nonzero weight at {key}")
    return found[1], found[2]


class ExactWeights(unittest.TestCase):
    """Spec FR-020's exact weights, each equal to an exhaustive count at w = 8 over the stated
    inputs, outputs and constants."""

    def test_the_differential_probability_of_an_addition_and_a_subtraction(self):
        for sub in (False, True):
            op = operate(sub)
            for a, b, g in TRIPLES:
                count = sum(1 for x in range(256) for y in range(256) if op(x ^ a, y ^ b) == op(x, y) ^ g)
                self.assertEqual(trailcheck.add_count(W8, a, b, g, sub), count, (a, b, g, sub))

    def test_the_squared_correlation_of_an_addition_and_a_subtraction(self):
        for sub in (False, True):
            op = operate(sub)
            for u, v, t in TRIPLES:
                total = sum(sign(u & x, v & y, t & op(x, y)) for x in range(256) for y in range(256))
                self.assertEqual(trailcheck.add_sum(W8, u, v, t, sub), total, (u, v, t, sub))

    def test_an_addition_of_a_constant_by_the_carrys_automaton(self):
        for c in CONSTANTS_W8:
            for a, b in PAIRS:
                count = sum(1 for x in range(256) if ((x ^ a) + c) & 0xff == ((x + c) & 0xff) ^ b)
                self.assertEqual(trailcheck.add_constant_count(W8, c, a, b), count, (c, a, b))
                total = sum(sign(a & x, b & ((x + c) & 0xff)) for x in range(256))
                self.assertEqual(trailcheck.add_constant_sum(W8, c, a, b), total, (c, a, b))

    def test_every_transition_of_an_addition_at_w_4(self):
        for a in range(16):
            for b in range(16):
                row = [trailcheck.add_count(4, a, b, g) for g in range(16)]
                self.assertEqual(sum(row), 256)
                for g in range(16):
                    count = sum(1 for x in range(16) for y in range(16)
                                if ((x ^ a) + (y ^ b)) & 15 == ((x + y) & 15) ^ g)
                    self.assertEqual(row[g], count)

    def test_an_s_box_from_its_table(self):
        table = (0x9, 0xC, 0x3, 0x0, 0x2, 0x5, 0x4, 0x7, 0x6, 0x1, 0xA, 0xB, 0x8, 0xD, 0xE, 0xF)
        counts = [[trailcheck.table_count(table, a, b) for b in range(16)] for a in range(16)]
        self.assertEqual(counts[0][0], 16)
        self.assertTrue(all(sum(row) == 16 for row in counts))
        self.assertEqual(max(counts[a][b] for a in range(1, 16) for b in range(16)), 4)
        sums = [[trailcheck.table_sum(table, a, b) for b in range(16)] for a in range(16)]
        self.assertEqual(max(abs(sums[a][b]) for a in range(16) for b in range(1, 16)), 8)
        self.assertEqual(sum(v * v for v in sums[5]), 256)

    def test_the_class_by_the_threshold(self):
        from fractions import Fraction
        self.assertEqual(trailcheck.classify(Fraction(1, 1 << 127)), "confirmed vulnerability")
        self.assertEqual(trailcheck.classify(Fraction(1, 1 << 128)), evidence.NONE)
        self.assertEqual(trailcheck.classify(Fraction(1, 1 << 129)), evidence.NONE)


class TheReader(unittest.TestCase):
    """The standard-library reader of research/004/ir.py's forms: the reference designs' committed
    lists read by it equal `ir`'s, form for form and value for value."""

    SIZES = ((2, 8), (4, 16), (4, 32))

    def setUp(self):
        if str(ROOT / "research/004") not in sys.path:
            sys.path.insert(0, str(ROOT / "research/004"))
        import ir
        self.ir = ir
        evidence.set_feature("004")
        self.addCleanup(evidence.set_feature, "005")
        self.builds = ir.candidate_modules(ROOT / "research/004/candidates")

    def test_it_imports_the_standard_library_and_protocol_alone(self):
        for name in ("oplist", "trailcheck"):
            source = (ROOT / f"protocol/{name}.py").read_text(encoding="utf-8")
            imports = [line for line in source.split("\n") if line.startswith(("import ", "from "))]
            for line in imports:
                module = line.split()[1].split(".")[0]
                self.assertIn(module, ("__future__", "sys", "types", "json", "dataclasses", "fractions",
                                       "typing", "protocol"), line)

    def test_the_lists_and_their_values_equal_irs(self):
        state_seed = 0x9E3779B97F4A7C15
        for name in ("cand-A1", "cand-B1"):
            source = (ROOT / f"research/004/candidates/{name}.py").read_bytes()
            for n, w in self.SIZES:
                program, _ = oplist.read(source, name, n, w)
                theirs = self.builds[name](n, w)
                self.assertEqual(repr(program), repr(theirs), (name, n, w))
                values, x = [], state_seed
                for _ in range(2 * n * n + 3 * 3):
                    x = (x * 6364136223846793005 + 1442695040888963407) & (2 ** 64 - 1)
                    values.append((x >> 20) & ((1 << w) - 1))
                state, table = values[:2 * n * n], [values[2 * n * n + 3 * r:][:3] for r in range(3)]
                self.assertEqual(oplist.permute(program, state, table),
                                 self.ir.permute(self.ir.load(theirs), state, table), (name, n, w))

    def test_ir_stays_what_import_ir_finds_afterwards(self):
        source = (ROOT / "research/004/candidates/cand-A1.py").read_bytes()
        oplist.read(source, "cand-A1", 2, 8)
        self.assertIs(sys.modules["ir"], self.ir)

    def test_a_linear_steps_transpose(self):
        w = 8
        expr = oplist.Rotl(oplist.Xor(oplist.Lane(1), oplist.Shl(oplist.Lane(1), 3)), 5)
        for mask in (0x01, 0x80, 0x5a):
            into = {}
            oplist.transpose(expr, mask, into, w)
            for x in range(256):
                value = oplist.linear(expr, [0, x], w)
                self.assertEqual(trailcheck.parity(mask & value), trailcheck.parity(into[1] & x))


def one(update, w=W8):
    return oplist.Program("one", 1, w, (oplist.Phase(0, (update,)),))


class Trails(unittest.TestCase):
    """Data-model section 3: a characteristic with every nonlinear operation recorded re-checks to
    its weight, by exact arithmetic from the operation list; a changed transition is a disagreement."""

    def a1(self, kind="differential", rounds=2, lane=1, value=0x80):
        source = (ROOT / "research/004/candidates/cand-A1.py").read_bytes()
        program, _ = oplist.read(source, "cand-A1", 2, W8)
        state = [0] * 8
        state[lane] = value
        rows = [(0x12, 0x34, 0x56)] * rounds
        characteristic, weight = trailcheck.build(program, kind, state, rows, best)
        return program, rows, characteristic, weight

    def test_a_single_additions_trail_is_its_differential(self):
        from fractions import Fraction
        program = one(oplist.Mix(0, "add", oplist.Rotl(oplist.Lane(1), 3)))
        characteristic, weight = trailcheck.build(program, "differential", [0x05, 0x21], [()], best)
        after = trailcheck.state_of(characteristic[0]["state_out"], 2, W8)
        count = sum(1 for x in range(256) for y in range(256)
                    if oplist.permute(program, [x ^ 0x05, y ^ 0x21]) == [
                        a ^ b for a, b in zip(oplist.permute(program, [x, y]), after)])
        self.assertEqual(weight, Fraction(count, 65536))
        self.assertEqual(trailcheck.recompute(program, "differential", characteristic, [()]), weight)

    def test_a_single_additions_trail_is_its_squared_correlation(self):
        from fractions import Fraction
        for op in ("add", "sub"):
            program = one(oplist.Mix(0, op, oplist.Rotl(oplist.Lane(1), 3)))
            characteristic, weight = trailcheck.build(program, "linear", [0x06, 0x00], [()], best)
            before = trailcheck.state_of(characteristic[0]["state_in"], 2, W8)
            after = trailcheck.state_of(characteristic[0]["state_out"], 2, W8)
            total = 0
            for x in range(256):
                for y in range(256):
                    out = oplist.permute(program, [x, y])
                    total += sign(before[0] & x, before[1] & y, after[0] & out[0], after[1] & out[1])
            self.assertEqual(weight, Fraction(total * total, 1 << 32), op)
            self.assertEqual(trailcheck.recompute(program, "linear", characteristic, [()]), weight)

    def test_an_addition_of_a_committed_constant(self):
        from fractions import Fraction
        for op in ("add", "sub"):
            program = one(oplist.Mix(0, op, oplist.Constant(0)))
            rows = [(0x5d,)]
            characteristic, weight = trailcheck.build(program, "differential", [0x06, 0x00], rows, best)
            after = trailcheck.state_of(characteristic[0]["state_out"], 2, W8)
            count = sum(1 for x in range(256)
                        if oplist.permute(program, [x ^ 0x06, 0], rows)[0] == oplist.permute(program, [x, 0], rows)[0] ^ after[0])
            self.assertEqual(weight, Fraction(count, 256), op)
            self.assertEqual(trailcheck.recompute(program, "differential", characteristic, rows), weight)
            with self.assertRaises(Refused):
                trailcheck.recompute(program, "differential", characteristic, [()])
            self.assertNotEqual(trailcheck.recompute(program, "differential", characteristic, rows), 0)

    def test_a_function_of_one_update_is_its_truth_table(self):
        from fractions import Fraction
        program = one(oplist.Mix(0, "xor", oplist.And(oplist.Lane(1), oplist.Rotl(oplist.Lane(1), 1))))
        characteristic, weight = trailcheck.build(program, "differential", [0x00, 0x01], [()], best)
        after = trailcheck.state_of(characteristic[0]["state_out"], 2, W8)
        count = sum(1 for x in range(256) for y in range(256)
                    if oplist.permute(program, [x, y ^ 0x01]) == [
                        a ^ b for a, b in zip(oplist.permute(program, [x, y]), after)])
        self.assertEqual(weight, Fraction(count, 65536))
        self.assertEqual(trailcheck.recompute(program, "differential", characteristic, [()]), weight)

    def test_a_reference_designs_trail_rechecks_to_its_weight(self):
        for kind in trailcheck.KINDS:
            program, rows, characteristic, weight = self.a1(kind)
            self.assertLess(weight, 1)
            self.assertGreater(sum(len(r["operations"]) for r in characteristic), 2)
            self.assertEqual(trailcheck.recompute(program, kind, characteristic, rows), weight)

    def test_a_changed_output_is_a_disagreement(self):
        program, rows, characteristic, _ = self.a1()
        operation = characteristic[0]["operations"][0]
        operation["output"] = trailcheck.hexadecimal(trailcheck.number(operation["output"]) ^ 0x02)
        with self.assertRaises(trailcheck.Disagreement):
            trailcheck.recompute(program, "differential", characteristic, rows)

    def test_a_changed_weight_input_or_state_is_a_disagreement(self):
        for change in ("weight", "inputs", "state_out", "dropped", "added", "round"):
            program, rows, characteristic, _ = self.a1()
            operations = characteristic[1]["operations"]
            if change == "weight":
                operations[0]["weight"] = "1/3"
            elif change == "inputs":
                operations[0]["inputs"][0] = trailcheck.hexadecimal(trailcheck.number(operations[0]["inputs"][0]) ^ 1)
            elif change == "state_out":
                characteristic[1]["state_out"] = characteristic[1]["state_in"]
            elif change == "dropped":
                del operations[0]
            elif change == "added":
                operations.append({"op_index": 9999, "position": evidence.NONE, "inputs": ["0x0", "0x0"],
                                   "output": "0x0", "weight": "1"})
            else:
                characteristic[1]["round"] = 3
            with self.assertRaises(trailcheck.Disagreement, msg=change):
                trailcheck.recompute(program, "differential", characteristic, rows)

    def test_updates_in_turn_form_one_s_box_per_bit_position(self):
        source = (ROOT / "research/004/candidates/cand-B1.py").read_bytes()
        program, module = oplist.read(source, "cand-B1", 4, W8)
        walk = trailcheck.Walk(program, "differential", 4)
        table = walk.network_table(walk.member_of[(1, 0)], ())
        mine = lambda x: (x & 1) | ((x >> 3) & 1) << 1 | ((x >> 2) & 1) << 2 | ((x >> 1) & 1) << 3
        self.assertEqual([table[mine(x)] for x in range(16)], [mine(y) for y in module.SBOX])
        for kind in trailcheck.KINDS:
            state = [0] * 32
            state[2] = 0x10
            characteristic, weight = trailcheck.build(program, kind, state, [()], best, 4)
            self.assertLess(weight, 1)
            self.assertEqual(trailcheck.recompute(program, kind, characteristic, [()], 4), weight)
            operation = characteristic[0]["operations"][-1]
            operation["output"] = trailcheck.hexadecimal(trailcheck.number(operation["output"]) ^ 0x0f)
            with self.assertRaises(trailcheck.Disagreement):
                trailcheck.recompute(program, kind, characteristic, [()], 4)

    def test_a_record_is_read_with_its_product_its_log_and_its_class(self):
        program, rows, characteristic, weight = self.a1(rounds=1)
        source = (ROOT / "research/004/candidates/cand-A1.py").read_bytes()
        record = {"candidate": "cand-A1", "size": 2, "width": W8, "rounds": 1, "trail_kind": "differential",
                  "characteristic": characteristic, "weight": str(weight),
                  "weight_log2": evidence.trail_weight_log2(str(weight)),
                  "classification": "confirmed vulnerability"}
        found = trailcheck.trail_found(record, source, lambda rounds: rows[:rounds], evidence.trail_weight_log2)
        self.assertEqual(found, {key: record[key] for key in ("weight", "weight_log2", "classification")})
        characteristic[0]["operations"][0]["weight"] = "1/7"
        found = trailcheck.trail_found(record, source, lambda rounds: rows[:rounds], evidence.trail_weight_log2)
        self.assertIn("differs from", found["transitions"])
        self.assertIn("not committed", trailcheck.trail_found(record, None, lambda rounds: rows, None)["transitions"])


def bound_record(name, rounds, bound, **fields):
    record = dict({"record_id": name, "kind": "bound", "candidate": "v4-A1", "bound_kind": "linear", "size": 16,
                   "width": 32, "rounds": rounds, "status": "pass", "method": "searched", "bound": bound,
                   "created_utc": "2026-12-01T00:00:00Z"}, **fields)
    return (json.dumps(record, sort_keys=True) + "\n").encode("utf-8"), record


class Splits(unittest.TestCase):
    """Data-model section 2: a `split` bound again from its two parts' committed bytes."""

    def setUp(self):
        self.records = {name: bound_record(name, rounds, bound)
                        for name, rounds, bound in (("b1", 1, "8"), ("b2", 2, "81/2"), ("b3", 3, "70"))}
        self.defects = set()

    def split(self, first="b2", second="b3", **fields):
        parts = [{"record_id": name, "sha256": hashlib.sha256(self.records[name][0]).hexdigest(),
                  "sha256_kind": "raw", "rounds": self.records[name][1]["rounds"],
                  "bound": self.records[name][1]["bound"]} for name in (first, second)]
        record = dict({"record_id": "s5", "kind": "bound", "candidate": "v4-A1", "bound_kind": "linear", "size": 16,
                       "width": 32, "rounds": 5, "method": "split", "parts": parts, "bound": "221/2",
                       "alternatives": 1, "searched": evidence.NONE, "status": "pass",
                       "classification": "no weakness identified within the analysis performed",
                       "created_utc": "2026-12-02T00:00:00Z"}, **fields)
        return record

    def found(self, record):
        return trailcheck.split_found(record, self.records, lambda blob: hashlib.sha256(blob).hexdigest(),
                                      lambda other: other["bound"], lambda name: name in self.defects)

    def differs(self, record):
        found = self.found(record)
        return {key: value for key, value in found.items() if record.get(key) != value}

    def test_the_exact_rational_sum(self):
        self.assertEqual(self.differs(self.split()), {})

    def test_another_sum_is_a_difference(self):
        self.assertEqual(self.differs(self.split(bound="111")), {"bound": "221/2"})

    def test_a_part_whose_sha256_differs(self):
        record = self.split()
        record["parts"][0]["sha256"] = "0" * 64
        self.assertIn("another SHA-256", self.differs(record)["sum"])

    def test_a_part_that_is_not_established(self):
        for change in ({"status": "inconclusive"}, {"capped": True}, {"status": "fail"}):
            blob, _ = bound_record("b2", 2, "81/2", **change)
            self.records["b2"] = (blob, json.loads(blob))
            self.assertIn("not an established bound", self.differs(self.split())["sum"], change)

    def test_a_part_of_another_candidate_kind_size_or_width(self):
        for change in ({"candidate": "v4-B1"}, {"bound_kind": "differential"}, {"size": 8}, {"width": 16}):
            blob, _ = bound_record("b3", 3, "70", **change)
            self.records["b3"] = (blob, json.loads(blob))
            self.assertIn("another candidate, kind, size or width", self.differs(self.split())["sum"])

    def test_the_parts_cover_the_rounds(self):
        self.assertIn("cover 4 rounds", self.differs(self.split("b1", "b3"))["sum"])

    def test_a_part_with_a_defect_no_longer_stands(self):
        self.defects.add("b3")
        self.assertIn("no longer stands", self.differs(self.split())["sum"])

    def test_a_sum_of_a_sum_stands_while_its_parts_do(self):
        inner = self.split(record_id="s5")
        self.records["s5"] = ((json.dumps(inner, sort_keys=True) + "\n").encode("utf-8"), inner)
        outer = self.split("s5", "b2", record_id="s7", rounds=7, bound="151", alternatives=1,
                           created_utc="2026-12-03T00:00:00Z")
        self.assertEqual(self.differs(outer), {})
        self.defects.add("b3")
        self.assertIn("no longer stands", self.differs(outer)["sum"])

    def test_the_alternatives_and_the_largest_sum(self):
        blob, record = bound_record("b4", 4, "110")
        self.records["b4"] = (blob, record)
        self.assertEqual(self.differs(self.split()), {"alternatives": 2,
                                                      "sum": "the largest sum of two established bounds is 118"})
        self.assertEqual(self.differs(self.split("b1", "b4", bound="118", alternatives=2)), {})

    def test_a_later_record_is_not_compared(self):
        blob, record = bound_record("b4", 4, "110", created_utc="2026-12-05T00:00:00Z")
        self.records["b4"] = (blob, record)
        self.assertEqual(self.differs(self.split()), {})

    def test_the_searched_bound_is_shown_and_must_be_smaller(self):
        blob, record = bound_record("b5", 5, "100")
        self.records["b5"] = (blob, record)
        self.assertEqual(self.differs(self.split()), {"searched": "100"})
        self.assertEqual(self.differs(self.split(searched="100")), {})
        blob, record = bound_record("b5", 5, "111")
        self.records["b5"] = (blob, record)
        self.assertIn("no smaller than the sum", self.differs(self.split(searched="111"))["sum"])


class TheRecheckOfThisFeature(TempRepo005):
    """scripts/recheck_004.py under 005: a `split` bound and a trail are read from the committed
    records and the candidate's committed operation list."""

    def setUp(self):
        super().setUp()
        from scripts import recheck_004
        self.recheck = recheck_004

    def test_a_split_bound_and_its_parts(self):
        base = f"{evidence.REP_REL}/candidates/v4-A1"
        blobs = {}
        for name, rounds, bound in (("bound-1", 2, "40"), ("bound-2", 3, "70")):
            blob, _ = bound_record(name, rounds, bound, method="active-box count",
                                   counts={str(rounds): {"count": int(bound), "status": 0, "sum_of": [1, 1]}})
            blobs[name] = blob
            write(self.root, f"{base}/{name}.json", blob)
        self.commit("the parts")
        parts = [{"record_id": name, "sha256": hashlib.sha256(blob).hexdigest(), "sha256_kind": "raw",
                  "rounds": json.loads(blob)["rounds"], "bound": json.loads(blob)["bound"]}
                 for name, blob in blobs.items()]
        record = {"record_id": "bound-3", "kind": "bound", "candidate": "v4-A1", "bound_kind": "linear", "size": 16,
                  "width": 32, "rounds": 5, "method": "split", "parts": parts, "bound": "110", "alternatives": 1,
                  "searched": evidence.NONE, "status": "pass", "created_utc": "2026-12-02T00:00:00Z",
                  "classification": "no weakness identified within the analysis performed"}
        self.assertEqual(self.recheck.differences(record, self.recheck.check_bound(record, evidence)), [])
        write(self.root, f"{evidence.RESEARCH_REL.replace(evidence.FEATURE_REL, 'research/005').rsplit('/', 1)[0]}"
                         "/validation/defects/bound-2.json", "{}\n")
        found = self.recheck.differences(record, self.recheck.check_bound(record, evidence))
        self.assertEqual([item["field"] for item in found], ["sum"])
        self.assertIn("no longer stands", found[0]["recomputed"])

    def test_a_trail_from_the_committed_operation_list(self):
        source = (ROOT / "research/004/candidates/cand-A1.py").read_bytes()
        write(self.root, "research/005/candidates/v4-A1.py", source)
        table = {"table": [["0x12", "0x34", "0x56"], ["0x9a", "0xbc", "0xde"]]}
        blob = (json.dumps(table) + "\n").encode("utf-8")
        write(self.root, "research/005/candidates/v4-A1/constants/t.json", blob)
        self.commit("the candidate")
        program, _ = oplist.read(source, "v4-A1", 2, W8)
        state = [0] * 8
        state[1] = 0x80
        rows = [(0x9a, 0xbc, 0xde)]
        characteristic, weight = trailcheck.build(program, "differential", state, rows, best)
        record = {"record_id": "trail-1", "candidate": "v4-A1", "size": 2, "width": W8, "rounds": 1,
                  "first_round": 2, "trail_kind": "differential", "characteristic": characteristic,
                  "weight": str(weight), "weight_log2": evidence.trail_weight_log2(str(weight)),
                  "classification": "confirmed vulnerability",
                  "constants": {"path": "research/005/candidates/v4-A1/constants/t.json",
                                "sha256": hashlib.sha256(blob).hexdigest()}}
        self.assertEqual(self.recheck.differences(record, self.recheck.check_trail(record, evidence)), [])
        record["constants"]["sha256"] = "0" * 64
        found = self.recheck.differences(record, self.recheck.check_trail(record, evidence))
        self.assertIn("another SHA-256", found[0]["recomputed"])
        record["candidate"] = "v4-A9"
        found = self.recheck.differences(record, self.recheck.check_trail(record, evidence))
        self.assertIn("not committed", found[0]["recomputed"])


# ----------------------------------------------------------- the probes and the projection table

CAPS = {16: 48.0, 8: 24.0, 4: 8.0}
REFERENCE_DESIGNS = ("cand-A1", "cand-B1")


def plan_fixture() -> dict:
    """A small plan-projections.json of the committed one's form: both reference designs, each size
    and kind, with searches that feature 004 made (a source), projected (none) or left to the cap."""
    climbs, trails = {}, {}
    for design in REFERENCE_DESIGNS:
        trails[design] = 0.0
        for size, cap in CAPS.items():
            for kind in ("linear", "differential"):
                if design == "cand-A1":
                    searches = [{"r": 1, "need_h": 0.5, "source": "bound-a"}, {"r": 2, "need_h": 1.0, "source": "bound-b"}]
                    if size == 16 and kind == "differential":
                        searches.append({"r": 3, "need_h": cap, "note": "reaches this cap"})
                elif size == 16:
                    searches = [{"r": 1, "need_h": cap, "note": "reaches this cap"}]
                elif size == 8:
                    searches = [{"r": 1, "need_h": 6.0, "note": "projected"}, {"r": 2, "need_h": cap, "note": "reaches this cap"}]
                else:
                    searches = [{"r": 1, "need_h": 0.1, "note": "projected"}]
                need = sum(row["need_h"] for row in searches)
                trails[design] += need
                climbs[f"{design} {size}x{size} {kind}"] = {"cap_h": cap, "need_h": round(need, 4), "searches": searches}
    rows = {family: {"trails_need_h": round(trails[design], 3), "structural_need_h": 12.0, "bias_need_h": 24.0,
                     "row_h": round(2 * (trails[design] + 36.0), 1)}
            for design, family in (("cand-A1", "ARX"), ("cand-B1", "Boolean"))}
    option = {"caps_h": {f"{n}x{n}": cap for n, cap in CAPS.items()}, "candidates_per_family": 3, "ceiling_h": 2200.0,
              "provisional_needs_h": {"structural": 12.0, "bias": 24.0},
              "feature_wide_needs_h": {"probes": 40.0, "two whole-suite runs per platform": 2.0, "reproductions and re-checks": 9.0},
              "feature_wide_row_h": 102.0, "rows": rows, "climbs": climbs,
              "sum_of_rows_h": round(3 * sum(row["row_h"] for row in rows.values()) + 102.0, 1)}
    return {"approved_option": "E", "margin": 2, "options": {"E": option}}


def chain(entries) -> bytes:
    lines, previous = b"", evidence.ZERO_HASH
    for seq, entry in enumerate(entries):
        raw = json.dumps(dict(entry, seq=seq, prev_sha256=previous, date_utc="2026-11-12T00:00:00Z"),
                         sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n"
        lines += raw
        previous = evidence.sha256(raw)
    return lines


class PlannedRepo(TempRepo005):
    """A repository with the plan's projections, the reference designs and feature 004's log of them."""

    def setUp(self):
        super().setUp()
        from scripts import evidence_v3, projection_table
        self.ev, self.table = evidence_v3, projection_table
        write(self.root, evidence.PLAN_PROJECTIONS_REL, json.dumps(plan_fixture(), indent=1, sort_keys=True) + "\n")
        write(self.root, evidence.REFUSED_LIST_REL, (ROOT / evidence.REFUSED_LIST_REL).read_bytes())
        entries = []
        for design in REFERENCE_DESIGNS:
            source = (ROOT / f"research/004/candidates/{design}.py").read_bytes()
            write(self.root, f"research/004/candidates/{design}.py", source)
            entries.append({"event": "proposed", "candidate_id": design, "oplist_sha256": evidence.sha256(source)})
        write(self.root, "research/004/candidates.jsonl", chain(entries))
        for name in ("bound-a", "bound-b"):
            write(self.root, f"reports/004-crypto-architecture-v3/candidates/cand-A1/{name}.json",
                  json.dumps({"record_id": name}) + "\n")
        for rel in ("research/004/tools/trails/long_trail.py", "research/004/tools/trails/active_sbox.py"):
            write(self.root, rel, (ROOT / rel).read_bytes())
        self.commit("the plan and the reference designs")
        for target, name, value in ((projection_table, "BASELINE", "HEAD"), (evidence_v3, "CODE", [])):
            patcher = mock.patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.real_plan_check = projection_table.guard_plan_check
        patcher = mock.patch.object(projection_table, "guard_plan_check")
        self.plan_check = patcher.start()
        self.addCleanup(patcher.stop)

    def probe_record(self, design, kind, size, result="finished", hours=1.0, bound_kind=evidence.NONE, rounds=66):
        extra = {"table_probe": {"design": design, "family": "ARX" if design == "cand-A1" else "Boolean", "kind": kind,
                                 "size": size, "width": 32, "rounds": rounds, "bound_kind": bound_kind,
                                 "method": evidence.NONE}, "result": result, "limit_hours": 4.0}
        if result == "finished":
            extra["probe_hours"] = hours
        return evidence.write_projection(run="probe", row=evidence.FEATURE_ROW, inputs="none", measured_speed={},
                                         projected_hours=4.0, time_hours=0.0 if result == "refused" else hours, extra=extra)

    def every_probe(self, **override):
        """One record per listed probe, each finished in an hour unless `override` names it."""
        listed = [(design, kind, size, evidence.NONE, 66) for design in REFERENCE_DESIGNS
                  for kind in ("structural", "bias") for size in (4, 8, 16)]
        listed += [("cand-A1", "bound", 16, "differential", 3)]
        listed += [("cand-B1", "bound", size, kind, r) for size, last in ((16, 1), (8, 2))
                   for kind in ("linear", "differential") for r in range(1, last + 1)]
        for design, kind, size, bound_kind, rounds in listed:
            name = f"{design} {kind} {size} {bound_kind} {rounds}"
            result, hours = override.get(name, ("finished", 1.0))
            if result is not None:
                self.probe_record(design, kind, size, result, hours, bound_kind, rounds)
        self.commit("the probes")

    def propose(self):
        write(self.root, evidence.CANDIDATE_LOG_REL, chain([{"event": "proposed", "candidate_id": "v4-A1", "family": "ARX"}]))
        self.commit("a candidate")


class Probes(PlannedRepo):
    """contracts/cli.md, "`scripts/evidence_v3.py … --probe`"; research R5; spec FR-005."""

    def run_probe(self, *arguments, finishes=True):
        calls = []

        def limited(function, job, seconds):
            calls.append(job)
            return 1.0 if finishes is True or len(calls) <= finishes else None

        with mock.patch.object(self.ev, "limited", limited), mock.patch("builtins.print"):
            code = self.ev.main(["--probe", "--candidate", "cand-A1", *arguments])
        records = sorted(((self.root / evidence.REP_REL / "projections").glob("projection-*.json")),
                         key=lambda path: path.stat().st_mtime_ns)
        return code, calls, [json.loads(path.read_bytes().decode("utf-8")) for path in records]

    def test_a_probe_is_a_projection_record_of_the_feature_wide_row(self):
        code, calls, records = self.run_probe("--kind", "structural", "--size", "4")
        self.assertEqual(code, 0)
        record = records[-1]
        self.assertEqual((record["kind"], record["row"], record["result"]), ("projection", "feature-wide", "finished"))
        self.assertEqual(record["table_probe"], {"design": "cand-A1", "family": "ARX", "kind": "structural", "size": 4,
                                                 "width": 32, "rounds": 66, "bound_kind": "none", "method": "none"})
        self.assertEqual(sorted(record["hours_by_kind"]), sorted(["inverse", "dependency", "symmetry", "invariant", "degree"]))
        self.assertEqual([job[1] for job in calls], ["inverse", "dependency", "symmetry", "invariant", "degree"])
        self.assertEqual(record["parallelism"], {"threads": 1, "workers": 1})
        self.assertEqual(record["limit_hours"], 4.0)
        self.assertIn("discarded unread", record["outputs_statement"])
        self.assertEqual(record["probe_hours"], record["time_hours"])
        self.assertEqual(record["design"]["sha256"],
                         evidence.sha256((ROOT / "research/004/candidates/cand-A1.py").read_bytes()))
        self.assertEqual(record["feature"], "005")
        self.assertFalse((self.root / "data/heavy-run.lock").exists())

    def test_a_bias_probe_runs_at_66_rounds_and_one_thread(self):
        code, calls, records = self.run_probe("--kind", "bias", "--size", "8")
        self.assertEqual(code, 0)
        self.assertEqual([(job[1], job[2], job[3]) for job in calls], [("frequency", 8, 66), ("avalanche", 8, 66)])
        self.assertEqual(records[-1]["parallelism"]["threads"], 1)
        self.assertEqual(self.run_probe("--kind", "bias", "--size", "8", "--rounds", "12")[0], evidence.EXIT_REFUSED)

    def test_a_probe_that_does_not_finish_reached_the_probe_limit(self):
        code, calls, records = self.run_probe("--kind", "structural", "--size", "16", finishes=2)
        self.assertEqual(code, 0)
        self.assertEqual(records[-1]["result"], "reached the probe limit")
        self.assertNotIn("probe_hours", records[-1])
        self.assertEqual(sorted(records[-1]["hours_by_kind"]), ["dependency", "inverse"])
        self.assertEqual(len(calls), 3)

    def test_a_search_probe_names_its_kind_and_r_and_is_projected_at_the_plans_need(self):
        code, calls, records = self.run_probe("--kind", "bound", "--size", "16", "--bound-kind", "differential", "--rounds", "2")
        self.assertEqual(code, 0)
        self.assertEqual(records[-1]["projected_hours"], 1.0)
        self.assertEqual(records[-1]["table_probe"]["method"], "active-box count")
        self.assertEqual([job[1:5] for job in calls], [("bound", 16, 2, "differential")])
        code, _, records = self.run_probe("--kind", "bound", "--size", "16", "--bound-kind", "differential", "--rounds", "3")
        self.assertEqual(records[-1]["projected_hours"], 4.0)
        self.assertEqual(self.run_probe("--kind", "bound", "--size", "16")[0], evidence.EXIT_REFUSED)
        self.assertEqual(self.run_probe("--kind", "bound", "--size", "16", "--bound-kind", "linear", "--rounds", "9")[0],
                         evidence.EXIT_REFUSED)

    def test_it_exits_2_once_a_proposed_entry_exists(self):
        self.propose()
        code, calls, records = self.run_probe("--kind", "structural", "--size", "4")
        self.assertEqual((code, calls, records), (evidence.EXIT_REFUSED, [], []))

    def test_a_probe_past_the_40_h_share_is_refused_and_keeps_the_plans_projection(self):
        self.assertEqual(self.ev.probes_share(), 40.0)
        for _ in range(4):
            self.probe_record("cand-B1", "bias", 4, hours=9.5)
        self.assertEqual(self.ev.probes_used(), 38.0)
        code, calls, records = self.run_probe("--kind", "structural", "--size", "4")
        self.assertEqual((code, calls), (evidence.EXIT_REFUSED, []))
        refused = [record for record in records if record["result"] == "refused"]
        self.assertEqual([(record["time_hours"], record["table_probe"]["kind"]) for record in refused], [(0.0, "structural")])
        code, _, records = self.run_probe("--kind", "bound", "--size", "16", "--bound-kind", "differential", "--rounds", "2")
        self.assertEqual(code, 0)
        self.assertEqual(len([record for record in records if record["table_probe"]["kind"] == "bound"]), 1)

    def test_the_share_is_the_tables_once_it_exists(self):
        write(self.root, f"{evidence.REP_REL}/projection-table.json",
              json.dumps({"feature_wide_row": {"holds_h": 102.0, "probes_share_h": 30.0}}))
        self.assertEqual(self.ev.probes_share(), 30.0)

    def test_only_a_reference_design_as_feature_004s_log_holds_it(self):
        with mock.patch("builtins.print"):
            self.assertEqual(self.ev.main(["--probe", "--candidate", "v4-A1", "--kind", "bias", "--size", "4"]),
                             evidence.EXIT_REFUSED)
        write(self.root, "research/004/candidates/cand-A1.py", "import ir\n")
        self.assertEqual(self.run_probe("--kind", "bias", "--size", "4")[0], evidence.EXIT_REFUSED)
        self.commit("another list")
        self.assertEqual(self.run_probe("--kind", "bias", "--size", "4")[0], evidence.EXIT_REFUSED)

    def test_it_runs_under_005_alone_and_at_a_claimable_size(self):
        self.assertEqual(self.run_probe("--kind", "bias", "--size", "2")[0], evidence.EXIT_REFUSED)
        self.assertEqual(self.run_probe("--kind", "inverse", "--size", "4")[0], evidence.EXIT_REFUSED)
        evidence.set_feature("004")
        self.addCleanup(evidence.set_feature, "005")
        with mock.patch("builtins.print"):
            self.assertEqual(self.ev.main(["--probe", "--candidate", "cand-A1", "--kind", "bias", "--size", "4"]),
                             evidence.EXIT_REFUSED)


class TheProjectionTable(PlannedRepo):
    """contracts/cli.md, "`scripts/projection_table.py [--check]`"; data-model section 4."""

    def main(self, *arguments):
        with mock.patch("builtins.print") as printed:
            code = self.table.main(list(arguments))
        return code, " ".join(str(call.args[0]) for call in printed.call_args_list if call.args)

    def test_each_value_is_the_smaller_of_the_plans_and_the_probes(self):
        self.every_probe()
        table = self.table.compute()
        plan = plan_fixture()["options"]["E"]
        for family in ("ARX", "Boolean"):
            row = table["rows"][family]
            self.assertEqual(row["structural"], {"plan_h": 24.0, "need_h": 3.0, "holds_h": 6.0})
            self.assertEqual(row["bias"], {"plan_h": 48.0, "need_h": 3.0, "holds_h": 6.0})
            self.assertLessEqual(row["trails"]["holds_h"], row["trails"]["plan_h"])
            self.assertEqual(row["row"]["plan_h"], plan["rows"][family]["row_h"])
            self.assertLessEqual(row["row"]["holds_h"], row["row"]["plan_h"])
        search = table["families"]["ARX"]["climbs"]["16x16"]["differential"]["runs"][2]
        self.assertEqual((search["plan_need_h"], search["need_h"], search["probe_result"]), (48.0, 1.0, "finished"))
        self.assertEqual(table["rows"]["ARX"]["trails"]["need_h"], 9.0 + 1.0)
        self.assertEqual(table["caps_h"]["16x16"], {"plan_h": 48.0, "holds_h": 48.0})
        self.assertEqual(table["feature_wide_row"]["holds_h"], 102.0)
        self.assertLessEqual(table["sum_of_rows_h"], table["plan_sum_of_rows_h"])
        self.assertTrue(table["fits_ceiling"])
        self.assertEqual(table["above_row"], [])

    def test_no_value_is_raised(self):
        self.every_probe(**{"cand-B1 bound 8 linear 1": ("finished", 20.0), "cand-A1 structural 4 none 66": ("finished", 30.0)})
        table = self.table.compute()
        run = table["families"]["Boolean"]["climbs"]["8x8"]["linear"]["runs"][0]
        self.assertEqual((run["plan_need_h"], run["need_h"]), (6.0, 6.0))
        self.assertEqual(table["rows"]["ARX"]["structural"]["need_h"], 12.0)
        self.assertEqual(table["rows"]["ARX"]["structural"]["holds_h"], 24.0)

    def test_a_search_probe_at_the_limit_reads_as_its_search_at_the_cap(self):
        self.every_probe(**{"cand-B1 bound 8 linear 1": ("reached the probe limit", 4.0),
                            "cand-B1 bound 8 linear 2": (None, 0.0)})
        climb = self.table.compute()["families"]["Boolean"]["climbs"]["8x8"]["linear"]
        self.assertEqual(len(climb["runs"]), 1)
        self.assertEqual((climb["runs"][0]["need_h"], climb["runs"][0]["reaches_cap"]), (24.0, True))
        self.assertEqual((climb["plan_need_h"], climb["need_h"]), (30.0, 24.0))

    def test_a_probe_that_did_not_finish_keeps_its_sizes_share(self):
        self.every_probe(**{"cand-A1 bias 16 none 66": ("reached the probe limit", 4.0),
                            "cand-A1 structural 8 none 66": ("refused", 0.0)})
        rows = self.table.compute()["rows"]["ARX"]
        self.assertEqual(rows["bias"]["need_h"], 1.0 + 1.0 + 8.0)
        self.assertEqual(rows["structural"]["need_h"], 1.0 + 4.0 + 1.0)

    def test_a_need_shown_above_its_row_is_recorded_and_printed(self):
        self.every_probe(**{f"cand-A1 structural {size} none 66": ("finished", 9.0) for size in (4, 8, 16)})
        table = self.table.compute()
        self.assertEqual(table["rows"]["ARX"]["structural"]["holds_h"], 24.0)
        self.assertEqual(len(table["above_row"]), 1)
        self.assertEqual((table["above_row"][0]["family"], table["above_row"][0]["row"], table["above_row"][0]["shown_at_least_h"]),
                         ("ARX", "structural", 27.0))
        code, printed = self.main()
        self.assertEqual(code, 0)
        self.assertIn("above its row: ARX structural", printed)

    def test_a_listed_probe_missing_or_not_committed_is_refused(self):
        self.every_probe(**{"cand-B1 bound 16 linear 1": (None, 0.0)})
        self.assertEqual(self.main()[0], evidence.EXIT_REFUSED)
        self.probe_record("cand-B1", "bound", 16, bound_kind="linear", rounds=1)
        self.assertEqual(self.main()[0], evidence.EXIT_REFUSED)
        self.commit("the last probe")
        self.assertEqual(self.main()[0], 0)

    def test_it_exits_2_once_a_proposed_entry_exists_or_the_plan_fails_its_check(self):
        self.every_probe()
        self.plan_check.side_effect = Refused("plan-projections.json fails its --check")
        self.assertEqual(self.main()[0], evidence.EXIT_REFUSED)
        self.plan_check.side_effect = None
        self.propose()
        self.assertEqual(self.main()[0], evidence.EXIT_REFUSED)
        self.assertFalse((self.root / evidence.REP_REL / "projection-table.json").exists())

    def test_the_plans_check_is_the_plan_scripts(self):
        with mock.patch.object(self.table.subprocess, "run", return_value=mock.Mock(returncode=1, stdout="differs", stderr="")):
            with self.assertRaises(Refused):
                self.real_plan_check()
        with mock.patch.object(self.table.subprocess, "run", return_value=mock.Mock(returncode=0, stdout="matches", stderr="")):
            self.real_plan_check()

    def test_the_table_is_written_checked_and_read(self):
        self.every_probe()
        code, printed = self.main()
        self.assertEqual(code, 0)
        path = self.root / evidence.REP_REL / "projection-table.json"
        table = json.loads(path.read_bytes().decode("utf-8"))
        self.assertEqual((table["kind"], table["feature"], table["classification"]), ("projection-table", "005", "none"))
        blob = (self.root / evidence.PLAN_PROJECTIONS_REL).read_bytes()
        self.assertEqual((table["plan_projections_sha256"], table["plan_projections_sha256_kind"]),
                         (hashlib.sha256(blob).hexdigest(), "raw"))
        self.assertEqual(self.main("--check")[0], 0)
        self.assertEqual(evidence.row_hours("v4-A1", "trails"), table["rows"]["ARX"]["trails"]["holds_h"])
        self.assertEqual(evidence.row_hours("v4-B2", "statistics"), table["rows"]["Boolean"]["bias"]["holds_h"])
        self.assertEqual(evidence.feature_row_hours(), 102.0)
        table["rows"]["ARX"]["trails"]["holds_h"] += 1.0
        path.write_bytes(evidence.pretty(table))
        self.assertEqual(self.main("--check")[0], evidence.EXIT_VERDICT)

    def test_it_holds_numbers_record_ids_and_fixed_names_and_no_prose(self):
        self.every_probe(**{"cand-B1 bound 8 linear 1": ("reached the probe limit", 4.0),
                            "cand-B1 bound 8 linear 2": (None, 0.0)})
        allowed = {"projection-table", "005", "none", "raw", "E", "cap", "plan", "finished", "reached the probe limit",
                   "refused", "cand-A1", "cand-B1", "ARX", "Boolean"}

        def texts(value):
            if isinstance(value, dict):
                for item in value.values():
                    yield from texts(item)
            elif isinstance(value, list):
                for item in value:
                    yield from texts(item)
            elif isinstance(value, str):
                yield value

        for text in texts(self.table.compute()):
            if text in allowed or re.fullmatch(r"[0-9a-f]{64}", text):
                continue
            self.assertRegex(text, r"^(projection-\d{8}T\d{6}Z-[0-9a-f]{8}|bound-[a-z]|reports/00[45]-[\w./-]+\.json)$")

    def test_a_source_is_named_by_record_id_path_and_sha256(self):
        self.every_probe()
        table = self.table.compute()
        made = table["families"]["ARX"]["climbs"]["4x4"]["linear"]["runs"][0]["source"]
        rel = "reports/004-crypto-architecture-v3/candidates/cand-A1/bound-a.json"
        self.assertEqual(made, {"record_id": "bound-a", "path": rel, "sha256_kind": "raw",
                                "sha256": hashlib.sha256((self.root / rel).read_bytes()).hexdigest()})
        probed = table["families"]["Boolean"]["climbs"]["16x16"]["linear"]["runs"][0]["source"]
        self.assertEqual(hashlib.sha256((self.root / probed["path"]).read_bytes()).hexdigest(), probed["sha256"])
        self.assertEqual(table["families"]["Boolean"]["climbs"]["4x4"]["linear"]["runs"][0]["source"], "plan")


# ----------------------------------------------------------------------------- the candidate log

DOCUMENT = """# {title}

> {disclaimer}

Version: 0.5

## Security target

The target{change}.

## Mode

The mode.

## Next

Not drafted yet.
"""


class TheCandidateLog(TempRepo005):
    """Data-model section 5; contracts/cli.md, "`scripts/candidate_log.py propose …`"; quickstart V4."""

    DESIGN = "specs/005-crypto-architecture-v4/design.md"
    RATIONALE = "specs/005-crypto-architecture-v4/rationale.md"
    LIST_004 = "research/004/candidates/cand-A1.py"

    def setUp(self):
        super().setUp()
        from scripts import candidate_log
        self.script = candidate_log
        self.documents()
        self.source = (ROOT / self.LIST_004).read_bytes()
        write(self.root, self.LIST_004, self.source)
        for name in ("v4-A1", "v4-A2", "v4-A3", "v4-B1"):
            write(self.root, f"research/005/candidates/{name}.py", f"import ir  # {name}\n")
        write(self.root, evidence.PLAN_PROJECTIONS_REL,
              json.dumps({"approved_option": "E", "options": {"E": {"candidates_per_family": 3}}}) + "\n")
        self.commit("documents and lists")

    def documents(self, change: str = "") -> None:
        for rel, title in ((self.DESIGN, "design document"), (self.RATIONALE, "design rationale")):
            write(self.root, rel, DOCUMENT.format(title=title, disclaimer=DESIGN_DISCLAIMER_005, change=change))

    def review(self, name: str = "Security-target review", decision: str = "Approved") -> None:
        notes = []
        for rel in (self.DESIGN, self.RATIONALE):
            for chapter in ("Security target", "Mode"):
                digest = evidence.sha256(evidence.section_bytes((self.root / rel).read_bytes(), chapter))
                notes.append(f"`{rel}`, chapter \"{chapter}\", {digest}")
        self.add_row(name, decision, "Version 0.5; " + "; ".join(notes))

    def table(self, per_family: int = 3) -> None:
        write(self.root, f"{evidence.REP_REL}/projection-table.json",
              json.dumps({"candidates_per_family": per_family, "feature_wide_row": {"holds_h": 102.0}}) + "\n")
        self.commit("the projection table")

    def fields(self, candidate: str = "v4-A1", **more) -> dict:
        digest = evidence.sha256((self.root / f"research/005/candidates/{candidate}.py").read_bytes())
        return dict({"candidate_id": candidate, "oplist_sha256": digest,
                     "parameters": {name: "stated" for name in candidates.PARAMETERS}}, **more)

    def command(self, *arguments, candidate: str = "v4-A1", **more) -> int:
        write(self.root, "entry.json", json.dumps(self.fields(candidate, **more)))
        with mock.patch("builtins.print"):
            return self.script.main(["propose", str(self.root / "entry.json"), *arguments])

    def log(self) -> list:
        path = self.root / evidence.CANDIDATE_LOG_REL
        return [json.loads(line) for line in path.read_bytes().decode("utf-8").splitlines()] if path.exists() else []

    def test_no_candidate_before_the_review_reads_approved(self):
        self.table()
        self.assertEqual(self.command(), evidence.EXIT_REFUSED)
        self.review(decision="Declined")
        self.assertEqual(self.command(), evidence.EXIT_REFUSED)
        self.assertEqual(self.log(), [])

    def test_no_candidate_before_the_projection_table_exists(self):
        self.review()
        self.assertEqual(self.command(), evidence.EXIT_REFUSED)
        self.assertEqual(self.log(), [])
        self.table()
        self.assertEqual(self.command(), 0)

    def test_once_both_hold_the_entry_is_appended_with_derived_from_none(self):
        self.review()
        self.table()
        self.assertEqual(self.command(), 0)
        entry = self.log()[0]
        self.assertEqual((entry["event"], entry["candidate_id"], entry["family"], entry["derived_from"]),
                         ("proposed", "v4-A1", "ARX", "none"))

    def test_a_reviewed_chapter_changed_at_head_refuses_every_proposed_entry(self):
        self.review()
        self.table()
        self.documents(change=", changed")
        self.commit("a chapter changed")
        self.assertEqual(self.command(), evidence.EXIT_REFUSED)
        self.assertEqual(self.command(candidate="v4-B1"), evidence.EXIT_REFUSED)
        self.review("Security-target review 2")
        self.assertEqual(self.command(), 0)

    def test_the_row_names_each_of_the_four_chapters(self):
        digest = evidence.sha256(evidence.section_bytes((self.root / self.DESIGN).read_bytes(), "Mode"))
        self.add_row("Security-target review", "Approved", f"`{self.DESIGN}`, chapter \"Mode\", {digest}")
        self.table()
        self.assertEqual(self.command(), evidence.EXIT_REFUSED)

    def test_derived_from_names_the_feature_004_design(self):
        self.review()
        self.table()
        digest = evidence.sha256(self.source)
        self.assertEqual(self.command("--derived-from", f"{self.LIST_004}:{digest}", "--relation", "derived"), 0)
        self.assertEqual(self.log()[0]["derived_from"],
                         {"feature": "004", "candidate": "cand-A1", "oplist_path": self.LIST_004,
                          "oplist_sha256": digest, "relation": "derived", "changes": "none"})
        self.assertEqual(self.command("--derived-from", f"{self.LIST_004}:{digest}", "--relation", "starting-point",
                                      "--changes", "a fifth step in the box", candidate="v4-A2"), 0)
        self.assertEqual((self.log()[1]["derived_from"]["relation"], self.log()[1]["derived_from"]["changes"]),
                         ("starting-point", "a fifth step in the box"))

    def test_a_derived_from_that_does_not_hold_is_refused(self):
        self.review()
        self.table()
        digest = evidence.sha256(self.source)
        for arguments in (("--derived-from", f"{self.LIST_004}:{'0' * 64}", "--relation", "derived"),
                          ("--derived-from", f"{self.LIST_004}:{digest}"),
                          ("--relation", "derived"),
                          ("--derived-from", f"{self.LIST_004}:{digest}", "--relation", "derived", "--changes", "a change"),
                          ("--derived-from", f"{self.LIST_004}:{digest}", "--relation", "starting-point"),
                          ("--derived-from", f"research/005/candidates/v4-A2.py:{digest}", "--relation", "derived")):
            self.assertEqual(self.command(*arguments), evidence.EXIT_REFUSED, arguments)
        self.assertEqual(self.log(), [])

    def test_the_limit_per_family_is_the_plan_approvals(self):
        self.review()
        self.table(per_family=2)
        self.assertEqual(candidates.most_per_family(), 2)
        self.assertEqual(self.command(candidate="v4-A1"), 0)
        self.assertEqual(self.command(candidate="v4-A2"), 0)
        self.assertEqual(self.command(candidate="v4-A3"), evidence.EXIT_REFUSED)
        self.assertEqual(self.command(candidate="v4-B1"), 0)
        (self.root / evidence.REP_REL / "projection-table.json").unlink()
        self.assertEqual(candidates.most_per_family(), 3)

    def test_feature_004s_log_keeps_its_rule(self):
        evidence.set_feature("004")
        self.addCleanup(evidence.set_feature, "005")
        self.assertEqual(candidates.most_per_family(), 3)
        write(self.root, "entry.json", json.dumps({"candidate_id": "cand-A1"}))
        with mock.patch("builtins.print"):
            self.assertEqual(self.script.main(["propose", str(self.root / "entry.json"), "--relation", "derived"]),
                             evidence.EXIT_REFUSED)


# ---------------------------------------------------------------------------- the security target

import tests.test_records_004 as records_004  # noqa: E402

DESIGN_005 = ROOT / "specs/005-crypto-architecture-v4/design.md"
RATIONALE_005 = ROOT / "specs/005-crypto-architecture-v4/rationale.md"
LIMITS_005 = ROOT / "reports/005-crypto-architecture-v4/security-target/limits.json"
PROFILE_005 = ROOT / "reports/005-crypto-architecture-v4/security-target/parameters.json"
PLACEHOLDERS = ("<R4>", "<R8>", "<R16>")


class ThisFeaturesFiles:
    """Feature 004's tests of its chapters and security-target files, run with this feature as their
    parameter: its documents, its two files and its disclaimer (T030)."""

    def setUp(self):
        for name, value in (("DESIGN_FILE", DESIGN_005), ("RATIONALE_FILE", RATIONALE_005), ("LIMITS_FILE", LIMITS_005),
                            ("PROFILE_FILE", PROFILE_005), ("DESIGN_DISCLAIMER", DESIGN_DISCLAIMER_005)):
            patcher = mock.patch.object(records_004, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        super().setUp()


class TheChapters(ThisFeaturesFiles, records_004.Chapters):
    """Inherited FR-034's chapters and header, for `phyco-v4`, Version 0.5 (spec FR-010, FR-026)."""

    def test_the_drafts_tables_hold_at_the_limits_they_state(self):
        """Under 005 the parameter table gives the variant rows while "Permutation" is not drafted."""
        tool = records_004.limits_script()
        if tool.variant_table_drafted(self.design):
            self.skipTest("the variant table is drafted: the file's own run takes over")
        out = tool.compute(self.design, [], ROOT)
        self.assertTrue(out["held"], out["assertions"])
        claimable = [row for row in out["parameters"]["rows"] if row["status"] == "claimable"]
        self.assertEqual([row["bound_bits"] for row in claimable], [128, 128, 128])
        self.assertEqual([row["R"] for row in claimable], list(PLACEHOLDERS))

    def test_the_version_is_0_5_until_a_later_change(self):
        self.assertRegex(records_004.header_of(self.design)[-1], r"^Version: 0\.([5-9]|\d\d+)$")
        self.assertEqual(records_004.header_of(self.design)[0], "# phyco-v4: design document")
        self.assertEqual(records_004.header_of(self.rationale)[0], "# phyco-v4: design rationale")

    def test_the_chapters_after_mode_read_not_drafted_yet_until_phase_6(self):
        if len(records_004.drafted(self.design)) > 2:
            self.skipTest("the later chapters are drafted from plan phase 6 on")
        self.assertEqual(records_004.drafted(self.design), ["Security target", "Mode"])
        self.assertEqual(records_004.drafted(self.rationale), ["Security target", "Mode"])

    def test_the_open_items_stand_under_a_heading_of_their_own(self):
        tool = records_004.limits_script()
        lines = tool.section_lines(self.design, "Security target", "Open items")
        text = " ".join(lines)
        for words in ("<R4>", "<R8>", "<R16>", "margin of instantiation's diffusion", "related-key and related-nonce",
                      "functionality class"):
            self.assertIn(words, text)

    def test_the_rationale_lists_the_changes_from_version_0_4_in_both_chapters(self):
        tool = records_004.limits_script()
        lines = self.rationale.split("\n")
        heads = tool.headings(lines)
        for chapter in ("Security target", "Mode"):
            first, last = tool.span(heads, 2, chapter, 0, len(lines))
            start, end = tool.span(heads, 3, "Changes from Version 0.4", first, last)
            entries = [line for line in lines[start:end] if line.startswith("- **")]
            self.assertGreaterEqual(len(entries), 5, chapter)
            block = "\n".join(lines[start:end])
            self.assertEqual(block.count("Reason:"), len(entries), chapter)

    def test_the_copied_chapters_cite_feature_004s_documents_by_name(self):
        tool = records_004.limits_script()
        lines = self.design.split("\n")
        heads = tool.headings(lines)
        first, _ = tool.span(heads, 2, "Security target", 0, len(lines))
        _, last = tool.span(heads, 2, "Mode", 0, len(lines))
        text = " ".join("\n".join(lines[first:last]).split())
        bare = re.findall(r"(?<!feature 004's )(?<!feature 005's )\bFR-\d{3}\b", text)
        self.assertEqual(bare, [])
        self.assertNotIn("phyco-v3", self.design)
        self.assertNotIn("feature 008", text)
        self.assertNotIn("for feature 005", text)


class TheSecurityTargetFiles(ThisFeaturesFiles, records_004.SecurityTargetFiles):
    """The two files with feature 004's fields, R a placeholder until the selection (spec FR-011)."""

    def test_each_row_holds_section_10s_fields(self):
        names = ("n", "w", "lanes_per_node", "b", "c", "r", "variant_id", "R", "key_entropy_bits", "nonce_bits",
                 "keyed_variants", "reachable_secret_state_bits", "bound_bits", "bound_terms", "status", "checks")
        for row in self.profile["rows"]:
            for name in names:
                self.assertIn(name, row, row["variant_id"])
            if row["status"] == "claimable":
                for name in ("throughput_implied", "throughput_goal", "rate_before_forget"):
                    self.assertIn(name, row, row["variant_id"])
                if row["R"] in PLACEHOLDERS:
                    self.assertEqual((row["throughput_implied"], row["rate_before_forget"]), (row["R"], row["R"]))

    def test_a_placeholder_r_is_read_as_not_yet_known_and_every_other_figure_checked(self):
        open_rows = [row for row in self.profile["rows"] if row["R"] in PLACEHOLDERS]
        if not open_rows:
            self.skipTest("every R is written")
        for row in open_rows:
            self.assertIn(f"-R{row['R']}-", row["variant_id"])
            self.assertEqual(row["R"], f"<R{row['n']}>")
            self.assertEqual((row["bound_bits"], row["key_entropy_bits"], row["c"], row["violations"]), (128, 256, 384, []))
        tool = records_004.limits_script()
        with tool_feature("005"):
            for old, new in (("| 4 | 32 | 1024 | 384 | 640 | <R4> | 256 | 384 | 128 |", "| 4 | 32 | 1024 | 384 | 640 | <R4> | 256 | 384 | 127 |"),
                             ("| 4 | 32 | 1024 | 384 | 640 | <R4> |", "| 4 | 32 | 1024 | 384 | 640 | <R8> |"),
                             ("| 8 | 32 | 4096 | 384 | 3712 | <R8> |", "| 8 | 32 | 4096 | 384 | 3713 | <R8> |")):
                self.assertIn(old, self.design)
                with self.assertRaises(Refused, msg=new):
                    tool.compute(self.design.replace(old, new), [], ROOT)

    def test_the_files_are_this_features_and_name_its_model(self):
        for record in (self.limits, self.profile):
            self.assertEqual((record["kind"], record["feature"]), ("security-target", "005"))
        self.assertTrue(all(row["variant_id"].startswith("phyco-v4/") for row in self.profile["rows"]))
        self.assertEqual([entry["status"] for entry in self.limits["theorems"]], ["unverified", "unverified"])

    def test_the_register_holds_the_profiles_bound_by_variant_and_names_both_files(self):
        register = json.loads((ROOT / "protocol/claims.json").read_bytes().decode("utf-8"))["models"]["phyco-v4"]
        self.assertEqual(register["bound"]["sizes"],
                         {row["variant_id"]: f"at most {row['bound_bits']} bits" for row in self.profile["rows"]
                          if row["status"] == "claimable"})
        self.assertEqual(register["bound"]["sha256"], hashlib.sha256(PROFILE_005.read_bytes()).hexdigest())
        named = {item["path"]: item["sha256"] for item in register["evidence"]}
        for path in (PROFILE_005, LIMITS_005):
            rel = path.relative_to(ROOT).as_posix()
            self.assertEqual(named.get(rel), hashlib.sha256(path.read_bytes()).hexdigest(), rel)


class TheRationalesValues(ThisFeaturesFiles, records_004.RationaleValues):
    """The rationale restates no value of either file, its sections of changes included (inherited FR-034)."""


class tool_feature:
    """The limits script reads the setting when it computes: a block under one feature."""

    def __init__(self, name: str):
        self.name = name

    def __enter__(self):
        self.previous = evidence.set_feature(self.name)

    def __exit__(self, *exc):
        evidence.set_feature(self.previous)


class TheLimitsScriptUnderBothFeatures(unittest.TestCase):
    """Research R8: under 005 the variant rows come from the parameter table until "Permutation" holds its
    variant table; feature 004's mode is unchanged."""

    PARAMETERS = """### Parameter table

| Variant | n | w | b | c | r | R | Key entropy | Reachable secret state | Bound | Status |
|---------|---|---|---|---|---|---|-------------|------------------------|-------|--------|
| phyco-v4/n4-w32-R<R4>-c384 | 4 | 32 | 1024 | 384 | 640 | <R4> | 256 | 384 | 128 | claimable |
| phyco-v4/n8-w32-R<R8>-c384 | 8 | 32 | 4096 | 384 | 3712 | <R8> | 256 | 384 | 128 | claimable |
| phyco-v4/n16-w32-R<R16>-c384 | 16 | 32 | 16384 | 384 | 16000 | <R16> | 256 | 384 | 128 | claimable |
| phyco-v4/n2-w16-R8-c64 | 2 | 16 | 128 | 64 | 64 | 8 | 64 | 64 | 32 | research |
"""

    def design(self, permutation: str = "Not drafted yet.\n") -> str:
        body = records_004.stated_design().split("## Permutation")[0].split("## Mode", 1)[1]
        return (f"# phyco-v4\n\nVersion: 0.5\n\n## Security target\n\n{self.PARAMETERS}\n## Mode{body}"
                f"## Permutation\n\n{permutation}")

    def test_under_005_the_parameter_table_gives_the_rows(self):
        tool = records_004.limits_script()
        with tool_feature("005"):
            out = tool.compute(self.design(), [], ROOT)
        rows = out["parameters"]["rows"]
        self.assertEqual([row["R"] for row in rows], ["<R4>", "<R8>", "<R16>", 8])
        self.assertEqual([row["bound_bits"] for row in rows], [128, 128, 128, 32])
        self.assertTrue(out["held"])
        self.assertEqual(rows[0]["throughput_implied"], "<R4>")
        self.assertNotIn("throughput_implied", rows[3])
        self.assertEqual(sorted(out["limits"]["per_request"]), sorted(row["variant_id"] for row in rows[:3]))

    def test_once_the_variant_table_stands_it_gives_the_rows(self):
        tool = records_004.limits_script()
        table = records_004.STATED_VARIANTS.replace("phyco-v3", "phyco-v4")
        with tool_feature("005"):
            with self.assertRaises(Refused):
                tool.compute(self.design(f"### Variant table\n\n{table}\n"), [], ROOT)
            stated = self.PARAMETERS
            for size, rounds in ((4, 20), (8, 24), (16, 32)):
                stated = stated.replace(f"<R{size}>", str(rounds))
            text = self.design(f"### Variant table\n\n{table}\n").replace(self.PARAMETERS, stated)
            lines = [line for line in text.split("\n") if "n2-w4-R8-c16" not in line]
            out = tool.compute("\n".join(lines), [], ROOT)
        self.assertEqual([row["R"] for row in out["parameters"]["rows"]], [20, 24, 32, 8])

    def test_feature_004_reads_its_variant_table_alone(self):
        tool = records_004.limits_script()
        with tool_feature("004"):
            with self.assertRaises(Refused):
                tool.compute(self.design(), [], ROOT)
            out = tool.compute(records_004.stated_design(), [], ROOT)
        self.assertNotIn("throughput_implied", out["parameters"]["rows"][0])


# -------------------------------------------------------------------- the selection-bias statement

def selection_bias():
    import importlib.util
    spec = importlib.util.spec_from_file_location("selection_bias", ROOT / "research/005/selection_bias.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TheSelectionBiasStatement(unittest.TestCase):
    """Data-model section 6; research R11; quickstart V9: every design of both features, from their logs."""

    def setUp(self):
        import tempfile
        self.tool = selection_bias()
        self.tmp = Path(tempfile.mkdtemp(prefix="phyco005-"))
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)

    def log_005(self, entries) -> None:
        write(self.tmp, "research/005/candidates.jsonl",
              "".join(json.dumps(dict(entry, seq=seq), sort_keys=True) + "\n" for seq, entry in enumerate(entries)))
        write(self.tmp, "research/004/candidates.jsonl", (ROOT / "research/004/candidates.jsonl").read_bytes())

    def test_feature_004s_designs_and_their_decisions(self):
        text = self.tool.statement()
        for line in ("| 004 | `cand-A1` | ARX | ineligible | feature 004, seq 107 | none |",
                     "| 004 | `cand-B1` | Boolean | ineligible | feature 004, seq 47 | none |",
                     "| 004 | `cand-B2` | Boolean | proposed and declined | feature 004, seq 49 | none |",
                     "| 004 | `cand-A2` | ARX | proposed and declined | feature 004, seq 109 | none |"):
            self.assertIn(line, text)

    def test_feature_004s_d4_and_selection_records_by_path_and_sha256(self):
        text = self.tool.statement()
        for rel, record in (("reports/004-crypto-architecture-v3/d4/choice.json", "d4-choice-20261108T110819Z-b980295b"),
                            ("reports/004-crypto-architecture-v3/freeze/selection.json", "selection-20261109T122326Z-254be6df")):
            digest = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
            self.assertIn(f"`{rel}`, record `{record}`, SHA-256 `{digest}` (raw)", text)
        self.assertIn("Feature 004 ran no bias test at w = 32.", text)

    def test_this_features_designs_with_what_they_derive_from(self):
        derived = {"feature": "004", "candidate": "cand-A1", "oplist_path": "x", "oplist_sha256": "y",
                   "relation": "derived", "changes": "none"}
        self.log_005([
            {"event": "proposed", "candidate_id": "v4-A1", "family": "ARX", "derived_from": derived},
            {"event": "proposed", "candidate_id": "v4-B1", "family": "Boolean", "derived_from": "none"},
            {"event": "proposed", "candidate_id": "v4-A2", "family": "ARX", "derived_from": "none"},
            {"event": "decision", "candidate_id": "v4-B1", "decision": "ineligible"},
            {"event": "decision", "candidate_id": "v4-A1", "decision": "eligible"},
            {"event": "decision", "candidate_id": "v4-A2", "decision": "eligible"},
            {"event": "replacement", "candidate_id": "v4-B1", "family": "Boolean", "reason": self.tool.DECLINED},
        ])
        write(self.tmp, "reports/005-crypto-architecture-v4/freeze/selection.json",
              json.dumps({"created_utc": "2026-12-01T00:00:00Z", "selected": "v4-A2"}))
        text = self.tool.statement(self.tmp)
        for line in ("| 005 | `v4-A1` | ARX | not selected | feature 005, seq 4 | feature 004, cand-A1, derived |",
                     "| 005 | `v4-B1` | Boolean | ineligible | feature 005, seq 3 | none |",
                     "| 005 | `v4-A2` | ARX | selected | feature 005, seq 5 | none |",
                     "| 005 | `v4-B2` | Boolean | proposed and declined | feature 005, seq 6 | none |",
                     "| 004 | `cand-A1` | ARX | ineligible | feature 004, seq 107 | none |"):
            self.assertIn(line, text)

    def test_the_family_wise_rate_over_this_features_tests(self):
        self.log_005([])
        base = "reports/005-crypto-architecture-v4/candidates/v4-A1"
        write(self.tmp, f"{base}/frequency-1.json", json.dumps({"status": "pass", "config": {"size": 4, "rounds": 10}}))
        write(self.tmp, f"{base}/avalanche-1.json", json.dumps({"status": "pass", "config": {"size": 4, "rounds": 10}}))
        write(self.tmp, f"{base}/avalanche-2.json", json.dumps({"status": "inconclusive", "config": {"size": 8, "rounds": 10}}))
        self.assertEqual(self.tool.bias_tests("reports/005-crypto-architecture-v4", self.tmp), (5, [2.0]))
        self.assertAlmostEqual(self.tool.rate(5, [2.0]), 1 - 0.995 ** 5 * 0.99, places=12)
        self.assertIn("5 pairs of a size and a round count and 1 avalanche sizes: 0.0345.", self.tool.statement(self.tmp))

    def test_check_compares_the_statement_a_file_holds(self):
        held = self.tmp / "report.md"
        held.write_text("# Report\n\n" + self.tool.statement() + "\nMore.\n", encoding="utf-8", newline="\r\n")
        with mock.patch("builtins.print"):
            self.assertEqual(self.tool.main(["--check", str(held)]), 0)
            held.write_text(self.tool.statement().replace("seq 107", "seq 106"), encoding="utf-8")
            self.assertEqual(self.tool.main(["--check", str(held)]), 1)

    def test_no_line_of_it_is_flagged_by_the_claim_test(self):
        from scripts import check_claims
        lines = self.tool.statement().split("\n")
        register = json.loads((ROOT / "protocol/claims.json").read_bytes().decode("utf-8"))
        found = check_claims.scan_lines("specs/005-crypto-architecture-v4/rationale.md", list(range(len(lines))), lines,
                                        dict(register, allow_list={"phrases": [], "lines": []}))
        self.assertEqual([(f.rule, f.text) for f in found], [])

    def test_it_reads_both_logs_and_writes_neither(self):
        source = (ROOT / "research/005/selection_bias.py").read_text(encoding="utf-8")
        self.assertNotIn("write_bytes", source)
        self.assertNotIn("write_text", source)
        self.assertNotIn('open(', source)


if __name__ == "__main__":
    unittest.main()
