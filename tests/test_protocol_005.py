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


if __name__ == "__main__":
    unittest.main()
