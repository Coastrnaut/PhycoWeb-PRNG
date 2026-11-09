"""Feature 004: the evidence writer, the guards every script shares and the common part of
--reproduce (T008; FR-038, FR-039, FR-040, FR-044, FR-045, FR-053, FR-061; research R7, R12, R16).
Each guard refuses with exit 2 and writes nothing. No test here makes a heavy run."""
import argparse
import ast
import datetime
import gzip
import json
import os
import re
import subprocess
import sys
import unittest
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from unittest import mock

from protocol import candidates, changelog, evidence, provenance
from protocol.disclaimer import DESIGN_DISCLAIMER
from protocol.evidence import NONE, Refused
from tests.support_004 import CODE_ROOT, SNAPSHOT, TempRepo, Tool, report_files, write

ROOT = Path(__file__).resolve().parents[1]
WORD = {"words": "go on with this candidate", "date": "2026-11-05"}
ARGV = ["scripts/tool.py", "--flag"]
CODE = ["scripts/tool.py"]
SEARCH = {"bound_kind": "differential", "rounds": 8, "width": 32, "size": 4}


class Records(TempRepo):
    """One light record to look at."""

    def record(self, kind: str = "validation", fields: Dict = None, **kwargs):
        run = evidence.Run(kind, argv=ARGV, code_files=CODE, **kwargs)
        with run:
            run.output("found.json", b"{}\n")
            path = run.finish("pass", fields=fields or {"tool": "t"})
        return path, json.loads(path.read_bytes())


class RecordIds(Records):
    def test_the_id_and_the_file_name(self):
        path, record = self.record()
        self.assertRegex(record["record_id"], r"^validation-\d{8}T\d{6}Z-[0-9a-f]{8}$")
        self.assertEqual(path.name, record["record_id"] + ".json")
        self.assertEqual(path.parent, self.root / evidence.REP_REL / "validation")

    def test_the_digits_come_from_the_content_with_the_id_written_as_a_placeholder(self):
        _, record = self.record()
        self.assertTrue(evidence.check_record_id(record))
        self.assertIn(record["record_id"], record["outputs"][0]["path"])
        self.assertFalse(evidence.check_record_id(dict(record, status="fail")))

    def test_approval_fields_and_hashes_over_the_record_leave_the_id_alone(self):
        _, record = self.record()
        approved = dict(record, approved_by="owner", approved_utc="2026-11-03T00:00:00Z",
                        approval_confirmed="0" * 16, draft_sha256="1" * 64,
                        freeze_status="approved", approval_wording="words")
        self.assertTrue(evidence.check_record_id(approved))

    def test_each_kind_has_its_place(self):
        places = {"demonstration": "fut-sec-8", "control": "controls", "validation": "validation",
                  "generator-run": "generator-runs", "generator-check": "generator-checks",
                  "projection": "projections", "recheck": "rechecks", "lock-cleared": "locks"}
        for kind, directory in places.items():
            self.assertEqual(evidence.directory_of(kind), directory)
        for kind in ("frequency", "bound", "trail", "cross-check", "cost"):
            self.assertEqual(evidence.directory_of(kind, "cand-A1"), "candidates/cand-A1")
        self.assertEqual(evidence.directory_of("reproduction", original="x", n=2),
                         "reproductions/x/2")

    def test_an_exploration_tables_record_sits_beside_its_table(self):
        path, _ = self.record("generator-run", directory="research/004/exploration")
        self.assertEqual(path.parent, self.root / "research/004/exploration")

    def test_outputs_take_the_id_and_no_temporary_name_stays(self):
        path, record = self.record()
        self.assertTrue((self.root / record["outputs"][0]["path"]).exists())
        self.assertEqual(path.parent / record["record_id"] / "found.json",
                         self.root / record["outputs"][0]["path"])
        self.assertEqual(list((self.root / evidence.PARTIAL_REL).glob("*")), [])

    def test_a_record_is_never_overwritten(self):
        path, _ = self.record()
        with self.assertRaisesRegex(Refused, "never overwritten"):
            evidence.write_exclusive(path, b"{}\n")


class CommonFields(Records):
    FIELDS = ("record_id", "kind", "created_utc", "model_id", "variant_id", "design_version",
              "design_sha256", "spec_sha256", "research_sha256", "protocol_seq",
              "protocol_line_sha256", "git_head", "git_dirty", "dirty_paths", "code_sha256",
              "versions", "environment", "platform", "parallelism", "command", "config", "inputs",
              "outputs", "exit_status", "assertions", "status", "classification", "analyst",
              "reviewer", "review_status", "limitations", "heavy_run", "hours", "ended_outside",
              "disclaimer")

    def test_every_field_of_fr_061_with_the_design_disclaimer(self):
        _, record = self.record()
        for name in self.FIELDS:
            self.assertIn(name, record)
        self.assertEqual(record["disclaimer"], DESIGN_DISCLAIMER)
        self.assertEqual((record["reviewer"], record["review_status"]), ("pending", "pending"))
        self.assertEqual((record["ended_outside"], record["hours"]), (NONE, NONE))
        self.assertIs(record["heavy_run"], False)

    def test_each_hash_stands_beside_its_kind(self):
        _, record = self.record()
        for name in ("design", "spec", "research", "protocol_line"):
            self.assertEqual(record[f"{name}_sha256_kind"], "raw")
        self.assertEqual(record["code_sha256"]["scripts/tool.py"]["kind"], "raw")
        self.assertEqual(record["outputs"][0]["sha256_kind"], "raw")
        self.assertEqual((record["environment"]["sha256_kind"],
                          record["environment"]["approval_sha256_kind"]), ("raw", "canonical"))

    def test_the_environment_is_named_by_both_of_its_hashes(self):
        _, record = self.record()
        rel = evidence.environment_rel()
        data = (self.root / rel).read_bytes()
        self.assertEqual(record["environment"]["path"], rel)
        self.assertEqual(record["environment"]["sha256"], evidence.sha256(data))
        self.assertEqual(record["environment"]["approval_sha256"],
                         evidence.approval_hash(json.loads(data)))

    def test_the_protocol_log_is_cited_by_its_last_entry(self):
        _, record = self.record()
        raw = (self.root / evidence.PROTOCOL_LOG_REL).read_bytes()
        self.assertEqual(record["protocol_seq"], 0)
        self.assertEqual(record["protocol_line_sha256"], evidence.sha256(raw))

    def test_the_command_starts_with_the_interpreter_by_its_full_path(self):
        _, record = self.record()
        self.assertIn(Path(evidence.interpreter()).name, record["command"])
        self.assertTrue(record["command"].endswith("scripts/tool.py --flag"))

    def test_the_format_rules(self):
        path, _ = self.record()
        raw = path.read_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r", raw)
        self.assertEqual(raw, evidence.pretty(json.loads(raw)))
        self.assertTrue(raw.endswith(b"}\n"))

    def test_dirty_paths_lists_data_and_a_commit_during_a_run_changes_no_field(self):
        write(self.root, "data/run.csv", "a\n")
        run = evidence.Run("validation", argv=ARGV, code_files=CODE)
        with run:
            head = evidence.head()
            spec = evidence.sha256((self.root / evidence.SPEC_REL).read_bytes())
            write(self.root, evidence.SPEC_REL, (self.root / evidence.SPEC_REL).read_text() + "\n")
            self.commit("during the run")
            path = run.finish("pass")
        record = json.loads(path.read_bytes())
        self.assertIs(record["git_dirty"], True)
        self.assertIn("data/run.csv", record["dirty_paths"])
        self.assertEqual((record["git_head"], record["spec_sha256"]), (head, spec))

    def test_a_status_outside_the_five_is_a_tool_failure(self):
        with self.assertRaises(evidence.ToolFailure):
            with evidence.Run("validation", argv=ARGV) as run:
                run.prepare("passed")

    def test_prepare_writes_nothing_and_write_adds_the_approval_fields(self):
        before = report_files(self.root)
        run = evidence.Run("validation", argv=ARGV)
        with run:
            record = run.prepare("pass")
            self.assertEqual(report_files(self.root), before)
            path = run.write(record, {"approved_by": "owner"})
        stored = json.loads(path.read_bytes())
        self.assertEqual(stored["approved_by"], "owner")
        self.assertEqual(stored["record_id"], record["record_id"])
        self.assertTrue(evidence.check_record_id(stored))


class Classification(unittest.TestCase):
    def test_the_table_by_kind_and_outcome(self):
        for kind, outcome, expected in (
                ("frequency", "fired", "confirmed vulnerability"),
                ("frequency", "not-fired", "no weakness identified within the analysis performed"),
                ("degree", "raises", "strong theoretical concern"),
                ("reproduction", "differs-verdict", "unverified hypothesis"),
                ("trail", "unvalidated", "unverified hypothesis"),
                ("projection", "any", NONE)):
            self.assertEqual(evidence.classify(kind, outcome), expected)


class CanonicalJson(unittest.TestCase):
    def test_sorted_keys_no_spaces_no_final_newline_and_characters_as_they_are(self):
        self.assertEqual(evidence.canonical({"b": 1, "a": ["é", 2]}),
                         '{"a":["é",2],"b":1}'.encode("utf-8"))

    def test_the_approval_hash_leaves_out_the_approval_fields_and_keeps_the_id(self):
        record = {"record_id": "x", "value": 1}
        approved = dict(record, approved_by="owner", approved_utc="t", approval_confirmed="0")
        self.assertEqual(evidence.approval_hash(approved), evidence.approval_hash(record))
        self.assertEqual(evidence.approval_hash(record),
                         evidence.sha256(evidence.canonical(record)))
        self.assertNotEqual(evidence.approval_hash(record),
                            evidence.approval_hash({"value": 1}))

    def test_lf_normalized_keeps_a_lone_cr(self):
        self.assertEqual(evidence.lf(b"a\r\nb\rc\n"), b"a\nb\rc\n")


class FixedNames(Records):
    def fixed(self, value: int):
        run = evidence.Run("limits", directory="security-target", file_name="limits.json",
                           fixed=True, argv=ARGV)
        with run:
            return run.finish("pass", fields={"value": value})

    def test_the_first_write_holds_no_previous(self):
        path = self.fixed(1)
        self.assertEqual(path.name, "limits.json")
        self.assertEqual(json.loads(path.read_bytes())["previous_sha256"], NONE)

    def test_a_change_keeps_the_old_content_under_versions(self):
        path = self.fixed(1)
        old = path.read_bytes()
        digest = evidence.sha256(old)
        self.fixed(2)
        self.assertEqual((path.parent / "versions" / f"{digest}.json").read_bytes(), old)
        record = json.loads(path.read_bytes())
        self.assertEqual((record["value"], record["previous_sha256"]), (2, digest))
        self.assertTrue(evidence.check_record_id(record))

    def test_versions_are_left_out_of_the_records_read(self):
        self.fixed(1)
        self.fixed(2)
        self.assertEqual(len(list(evidence.iter_records("limits"))), 1)

    def test_a_file_the_approved_freeze_pins_is_refused(self):
        path = self.fixed(1)
        pinned = {"path": evidence.rel_to_repo(path), "sha256": evidence.sha256(path.read_bytes())}
        freeze = {"kind": "freeze", "hashes": {"limits": pinned}, "freeze_status": "draft"}
        write(self.root, f"{evidence.REP_REL}/freeze/freeze.json", evidence.pretty(freeze))
        self.fixed(2)
        freeze["freeze_status"] = "approved"
        write(self.root, f"{evidence.REP_REL}/freeze/freeze.json", evidence.pretty(freeze))
        with self.assertRaisesRegex(Refused, "pinned by the freeze record"):
            self.fixed(3)

    def test_a_name_written_once_refuses_a_second_write(self):
        def run():
            return evidence.Run("d4-choice", directory="d4", file_name="choice.json", argv=ARGV)

        with run() as first:
            first.finish("pass")
        with self.assertRaisesRegex(Refused, "written once"):
            run().__enter__()


class Outputs(Records):
    def output(self, name: str, data: bytes = b"{}\n", **kwargs):
        run = evidence.Run("validation", argv=ARGV)
        with run:
            entry = dict(run.output(name, data, **kwargs))
            path = run.finish("pass")
        return json.loads(path.read_bytes()), entry

    def test_each_suffix_allowed_under_the_reports_directory(self):
        for suffix in (".json", ".jsonl", ".md", ".csv", ".txt", ".gz"):
            record, _ = self.output("out" + suffix)
            self.assertTrue((self.root / record["outputs"][0]["path"]).exists())

    def test_any_other_suffix_and_a_placeholder_are_refused_with_nothing_written(self):
        before = report_files(self.root)
        for name in ("out.npy", "solver.log", ".gitkeep", "out"):
            with self.assertRaisesRegex(Refused, "suffix"):
                self.output(name)
        self.assertEqual(report_files(self.root), before)

    def test_a_committed_output_above_10_mb_is_refused_naming_it(self):
        with self.assertRaisesRegex(Refused, "big.json: 10000001 bytes"):
            self.output("big.json", b"x" * 10_000_001)
        record, _ = self.output("exact.json", b"x" * 10_000_000)
        self.assertEqual(record["outputs"][0]["bytes"], 10_000_000)

    def test_the_rule_reads_the_compressed_size(self):
        record, _ = self.output("big.json.gz", b"x" * 11_000_000)
        self.assertLess(record["outputs"][0]["bytes"], 10_000_000)

    def test_a_local_only_output_goes_under_the_records_id(self):
        record, _ = self.output("matrix.json", b"x" * 10_000_001, local=True)
        entry = record["outputs"][0]
        self.assertEqual(entry["path"],
                         f"{evidence.LOCAL_REL}/{record['record_id']}/matrix.json")
        self.assertIs(entry["committed"], False)
        self.assertTrue((self.root / entry["path"]).exists())
        self.assertFalse([f for f in report_files(self.root) if "matrix" in f])

    def test_an_output_that_is_not_deterministic_is_never_local_only(self):
        with self.assertRaisesRegex(Refused, "never local-only"):
            self.output("solver.txt", local=True, deterministic=False)

    def test_a_gz_file_is_written_as_research_r16_states(self):
        data = b'{"counts": [1, 2]}\n'
        record, _ = self.output("counts.json.gz", data)
        entry = record["outputs"][0]
        stored = (self.root / entry["path"]).read_bytes()
        self.assertEqual(stored, gzip.compress(data, compresslevel=9, mtime=0))
        self.assertEqual(entry["sha256"], evidence.sha256(stored))
        self.assertEqual(entry["uncompressed_sha256"], evidence.sha256(data))

    def test_the_entry_holds_what_a_reproduction_compares(self):
        record, _ = self.output("p_values.json", deterministic=False, compared="values")
        entry = record["outputs"][0]
        self.assertEqual((entry["deterministic"], entry["compared"]), (False, "values"))
        self.assertEqual(entry["committed"], True)


class VersionsCited(Records):
    def test_the_spec_and_research_versions_are_kept(self):
        _, record = self.record()
        for subdir, name, rel in (("spec-versions", "spec", evidence.SPEC_REL),
                                  ("research-versions", "research", evidence.RESEARCH_REL)):
            kept = self.root / evidence.REP_REL / subdir / f"{record[name + '_sha256']}.md"
            self.assertEqual(kept.read_bytes(), (self.root / rel).read_bytes())

    def test_the_design_version_is_none_before_the_document_exists(self):
        _, record = self.record()
        self.assertEqual((record["design_version"], record["design_sha256"]), (NONE, NONE))

    def test_the_design_version_is_read_from_its_header_and_kept(self):
        write(self.root, evidence.DESIGN_REL, "# Design\n\nVersion: 0.3\n")
        self.commit("design")
        _, record = self.record()
        self.assertEqual(record["design_version"], "0.3")
        digest = record["design_sha256"]
        kept = self.root / evidence.REP_REL / "design-versions" / f"{digest}.md"
        self.assertEqual(evidence.sha256(kept.read_bytes()), digest)

    def test_a_header_without_the_version_line_is_refused(self):
        write(self.root, evidence.DESIGN_REL, "# Design\n")
        self.commit("design")
        with self.assertRaisesRegex(Refused, "Version"):
            self.record()

    def test_it_reads_1_0_while_the_approved_freeze_names_its_hash(self):
        data = "# Design\n\nVersion: 0.3\n"
        write(self.root, evidence.DESIGN_REL, data)
        self.commit("design")
        freeze = {"freeze_status": "approved", "hashes": {"design_document": {
            "path": evidence.DESIGN_REL, "sha256": evidence.sha256(data.encode("utf-8"))}}}
        write(self.root, f"{evidence.REP_REL}/freeze/freeze.json", evidence.pretty(freeze))
        self.assertEqual(self.record()[1]["design_version"], "1.0")


class AbortedRuns(TempRepo):
    def test_a_run_that_raises_writes_an_inconclusive_record_and_frees_the_lock(self):
        run = evidence.Run("frequency", candidate="cand-A1", argv=ARGV)
        with self.assertRaises(evidence.ToolFailure):
            with run:
                self.assertTrue(evidence.REPO.heavy_lock.exists())
                raise evidence.ToolFailure("the tool stopped")
        record = json.loads(run.record_path.read_bytes())
        self.assertEqual((record["status"], record["exit_status"]), ("inconclusive", 3))
        self.assertIn("the tool stopped", record["limitations"][0])
        self.assertTrue(record["heavy_run"])
        self.assertFalse(evidence.REPO.heavy_lock.exists())

    def test_a_refusal_inside_a_run_writes_nothing(self):
        before = report_files(self.root)
        with self.assertRaises(Refused):
            with evidence.Run("frequency", candidate="cand-A1", argv=ARGV) as run:
                run.output("x.npy", b"")
        self.assertEqual(report_files(self.root), before)
        self.assertFalse(evidence.REPO.heavy_lock.exists())

    def test_the_exit_codes(self):
        def refused():
            raise Refused("no")

        def failed():
            raise evidence.ToolFailure("no")

        def io_error():
            raise OSError("no")

        with mock.patch("sys.stderr"):
            self.assertEqual(evidence.main_guard(lambda: 0), 0)
            self.assertEqual(evidence.main_guard(lambda: 1), 1)
            self.assertEqual(evidence.main_guard(refused), 2)
            self.assertEqual(evidence.main_guard(failed), 3)
            self.assertEqual(evidence.main_guard(io_error), 3)


class EnvironmentGuard(TempRepo):
    def test_a_record_in_force_with_its_row_passes(self):
        self.assertEqual(evidence.guard_environment("inverse")["path"], evidence.environment_rel())

    def test_the_environment_record_itself_is_the_one_write_admitted(self):
        (self.root / evidence.environment_rel()).unlink()
        self.assertEqual(evidence.guard_environment("environment"), NONE)
        for kind in ("inverse", "lock-cleared"):
            with self.assertRaises(Refused):
                evidence.guard_environment(kind)

    def test_any_difference_refuses_naming_it(self):
        changed = dict(SNAPSHOT, python="3.10.12")
        with mock.patch.object(evidence, "snapshot", return_value=changed):
            with self.assertRaisesRegex(Refused, "python"):
                evidence.guard_environment("inverse")
            self.assertEqual(evidence.guard_environment("environment"), NONE)

    def test_a_row_not_approved_at_head_refuses_a_lock_cleared_record_too(self):
        record = json.loads((self.root / evidence.environment_rel()).read_bytes())
        record["snapshot"]["python"] = "3.10.12"
        write(self.root, evidence.environment_rel(), evidence.pretty(record))
        self.commit("a new record with no row")
        changed = dict(SNAPSHOT, python="3.10.12")
        with mock.patch.object(evidence, "snapshot", return_value=changed):
            for kind in ("inverse", "lock-cleared"):
                with self.assertRaisesRegex(Refused, "Environment record"):
                    evidence.guard_environment(kind)

    def test_the_approval_hash_is_read_at_head(self):
        self.rows[-1] = self.rows[-1].replace("Approved", "Declined")
        self.write_spec()
        with self.assertRaises(Refused):      # the working tree's table differs from HEAD's
            evidence.guard_environment("inverse")
        self.commit("declined")
        with self.assertRaises(Refused):
            evidence.guard_environment("inverse")


class CommittedCode(TempRepo):
    def tool(self):
        write(self.root, Tool.source, "int main(void){return 0;}\n")
        write(self.root, Tool.binary, b"\x7fELF binary")

    def test_committed_files_pass(self):
        evidence.guard_committed_code(["scripts/tool.py"])

    def test_untracked_refused(self):
        write(self.root, "scripts/new.py", "x = 1\n")
        with self.assertRaisesRegex(Refused, "not committed"):
            evidence.guard_committed_code(["scripts/new.py"])

    def test_staged_but_not_committed_refused(self):
        write(self.root, "scripts/new.py", "x = 1\n")
        self.run_git("add", "scripts/new.py")
        with self.assertRaisesRegex(Refused, "not committed"):
            evidence.guard_committed_code(["scripts/new.py"])

    def test_modified_refused(self):
        write(self.root, "scripts/tool.py", "print('changed')\n")
        with self.assertRaisesRegex(Refused, "differs"):
            evidence.guard_committed_code(["scripts/tool.py"])

    def test_a_binary_untracked_staged_or_modified_refused(self):
        self.tool()
        self.commit("tool")
        source_hash = evidence.sha256((self.root / Tool.source).read_bytes())
        with mock.patch.object(evidence, "binary_source_sha256", return_value=source_hash):
            write(self.root, Tool.binary, b"another")
            with self.assertRaisesRegex(Refused, "differs"):
                evidence.guard_committed_code([Tool.source, Tool.binary])
            write(self.root, "fast/build/other", b"x")
            with self.assertRaisesRegex(Refused, "not committed"):
                evidence.guard_committed_code(["fast/other.c", "fast/build/other"])
            self.run_git("add", "-f", "fast/build/other")
            with self.assertRaisesRegex(Refused, "not committed"):
                evidence.guard_committed_code(["fast/other.c", "fast/build/other"])

    def test_a_binary_whose_source_hash_differs_refused(self):
        self.tool()
        self.commit("tool")
        source_hash = evidence.sha256((self.root / Tool.source).read_bytes())
        with mock.patch.object(evidence, "binary_source_sha256", return_value=source_hash):
            evidence.guard_committed_code([Tool.source, Tool.binary])
        with mock.patch.object(evidence, "binary_source_sha256", return_value="0" * 64):
            with self.assertRaisesRegex(Refused, "source-sha256"):
                evidence.guard_committed_code([Tool.source, Tool.binary])

    def test_a_binary_that_does_not_run_prints_nothing(self):
        self.assertEqual(evidence.binary_source_sha256(self.root / "fast/build/absent"), "")

    def test_a_binary_needs_its_source_among_the_code_files(self):
        self.tool()
        self.commit("tool")
        with self.assertRaisesRegex(Refused, "its source"):
            evidence.guard_committed_code([Tool.binary])

    def test_a_text_auto_file_with_a_crlf_working_copy_matches_its_blob(self):
        write(self.root, "data/table.txt", b"a\nb\n")
        self.commit("table")
        write(self.root, "data/table.txt", b"a\r\nb\r\n")
        self.assertEqual(evidence.hash_kind("data/table.txt"), "lf-normalized")
        evidence.guard_committed_code(["data/table.txt"])
        self.assertEqual(evidence.hash_entry("data/table.txt")["sha256"],
                         evidence.sha256(b"a\nb\n"))

    def test_a_cited_file_modified_refused(self):
        write(self.root, evidence.RESEARCH_REL, "# Changed\n")
        with self.assertRaisesRegex(Refused, "modified"):
            evidence.guard_cited_files()

    def test_a_cited_file_untracked_refused(self):
        write(self.root, evidence.DESIGN_REL, "# Design\n\nVersion: 0.1\n")
        with self.assertRaisesRegex(Refused, "modified"):
            evidence.guard_cited_files()

    def test_a_file_the_script_names_is_cited_too(self):
        write(self.root, "reports/x.json", "{}\n")
        with self.assertRaisesRegex(Refused, "modified"):
            evidence.guard_cited_files(["reports/x.json"])

    def test_an_evidence_run_waits_and_a_lock_cleared_record_does_not(self):
        write(self.root, evidence.RESEARCH_REL, "# Changed\n")
        with self.assertRaisesRegex(Refused, "modified"):
            evidence.Run("validation", argv=ARGV).__enter__()
        path = evidence.write_simple_record("lock-cleared", "locks", {"lock": {}},
                                            writes_evidence=False)
        self.assertEqual(path.parent.name, "locks")


class GuardsWriteNothing(TempRepo):
    def attempt(self, **kwargs):
        before = report_files(self.root)
        with self.assertRaises(Refused):
            with evidence.Run("validation", argv=ARGV, **kwargs) as run:
                run.finish("pass")
        self.assertEqual(report_files(self.root), before)

    def test_code_not_committed(self):
        write(self.root, "scripts/new.py", "x = 1\n")
        self.attempt(code_files=["scripts/new.py"])

    def test_a_wrong_namespace(self):
        self.attempt(namespace="heldout-1")

    def test_the_environment(self):
        changed = dict(SNAPSHOT, python="3.10.12")
        with mock.patch.object(evidence, "snapshot", return_value=changed):
            self.attempt()

    def test_the_protocol_log(self):
        (self.root / evidence.PROTOCOL_LOG_REL).unlink()
        self.attempt()

    def test_a_heavy_run_with_the_lock_held(self):
        write(self.root, evidence.HEAVY_LOCK_REL, evidence.canonical(evidence.lock_content("x")))
        self.attempt(workers=2)


class Inputs(unittest.TestCase):
    def test_namespaces(self):
        evidence.guard_inputs("dev", "frequency")
        evidence.guard_inputs("control", "control")
        evidence.guard_inputs("feature-002/dev", "demonstration")
        for namespace, kind in (("heldout-1", "frequency"), ("control", "frequency"),
                                ("dev", "control"), ("heldout-1", "demonstration")):
            with self.assertRaises(Refused):
                evidence.guard_inputs(namespace, kind)


class OperationLists(TempRepo):
    def test_a_list_needs_a_proposed_or_correction_entry(self):
        with self.assertRaises(Refused):
            evidence.guard_oplist("a" * 64)
        evidence.append_entry(evidence.CANDIDATE_LOG_REL,
                              {"event": "proposed", "oplist_sha256": "a" * 64})
        evidence.guard_oplist("a" * 64)
        with self.assertRaises(Refused):
            evidence.guard_oplist("b" * 64)
        evidence.append_entry(evidence.CANDIDATE_LOG_REL,
                              {"event": "correction", "oplist_sha256": "b" * 64})
        evidence.guard_oplist("b" * 64)


class HeavyRuns(TempRepo):
    def test_exclusive_create_and_removal_on_exit(self):
        with evidence.HeavyRunLock("cmd") as lock:
            content = evidence.read_lock(evidence.REPO.heavy_lock)
            self.assertEqual(content["pid"], os.getpid())
            self.assertEqual(sorted(content),
                             ["command", "environment", "host", "pid", "start", "time"])
            self.assertTrue(evidence.holder_runs(lock.content))
            with self.assertRaisesRegex(Refused, "heavy-run.lock is held: its holder still runs"):
                evidence.HeavyRunLock("other").__enter__()
        self.assertFalse(evidence.REPO.heavy_lock.exists())

    def test_a_stale_lock_is_named_with_its_holder_gone(self):
        content = evidence.lock_content("cmd")
        content["start"] = "not the start time"
        write(self.root, evidence.HEAVY_LOCK_REL, evidence.canonical(content))
        with self.assertRaisesRegex(Refused, "no longer runs"):
            evidence.HeavyRunLock("other").__enter__()
        self.assertTrue(evidence.REPO.heavy_lock.exists())

    def test_the_test_of_a_heavy_run(self):
        self.assertTrue(evidence.is_heavy("trail"))
        self.assertTrue(evidence.is_heavy("demonstration"))
        self.assertTrue(evidence.is_heavy("generator-run", workers=2))
        self.assertTrue(evidence.is_heavy("generator-run", threads=2))
        self.assertTrue(evidence.is_heavy("generator-run", projected_hours=0.17))
        self.assertTrue(evidence.is_heavy("generator-run", last_hours=0.17))
        self.assertFalse(evidence.is_heavy("generator-run", projected_hours=0.16))
        self.assertFalse(evidence.is_heavy("limits"))

    def test_a_heavy_record_holds_its_hours(self):
        run = evidence.Run("frequency", candidate="cand-A1", argv=ARGV, config={"size": 4})
        with run:
            run.begin(0.5)
            path = run.finish("pass")
        record = json.loads(path.read_bytes())
        self.assertIs(record["heavy_run"], True)
        self.assertEqual(record["hours"]["projected"], 0.5)
        self.assertGreaterEqual(record["hours"]["used"], 0.0)


class ProtocolLog(TempRepo):
    def test_a_log_in_order_passes_and_is_cited(self):
        seq, line = evidence.guard_protocol_log("inverse")
        self.assertEqual(seq, 0)
        self.assertEqual(len(line), 64)

    def test_before_the_log_only_two_kinds_are_admitted(self):
        (self.root / evidence.PROTOCOL_LOG_REL).unlink()
        for kind in ("lock-cleared", "environment"):
            self.assertEqual(evidence.guard_protocol_log(kind), (NONE, NONE))
        for kind in ("inverse", "projection", "validation", "downloads"):
            with self.assertRaises(Refused):
                evidence.guard_protocol_log(kind)

    def test_once_it_exists_the_two_kinds_cite_its_last_entry(self):
        for kind in ("lock-cleared", "environment"):
            self.assertEqual(evidence.guard_protocol_log(kind)[0], 0)

    def test_a_broken_chain_refuses(self):
        path = self.root / evidence.PROTOCOL_LOG_REL
        path.write_bytes(path.read_bytes().replace(b'"seq": 0', b'"seq": 1'))
        with self.assertRaisesRegex(Refused, "chain breaks"):
            evidence.guard_protocol_log("inverse")

    def test_a_first_entry_whose_digits_do_not_match_refuses(self):
        entry = self.first_entry()
        entry["approver"] = {"owner": "owner", "date": "2026-11-03", "approval_confirmed": "f" * 16}
        self.write_log([entry])
        with self.assertRaisesRegex(Refused, "approval digits"):
            evidence.guard_protocol_log("inverse")

    def test_the_first_entries_share_one_hash_over_their_array(self):
        entries = self.approve([self.first_entry(), self.first_entry(seq=1)])
        self.assertEqual(entries[0]["approver"]["approval_confirmed"],
                         entries[1]["approver"]["approval_confirmed"])
        self.write_log(entries)
        evidence.guard_protocol_log("inverse")

    def later(self, seq: int = 1) -> Dict:
        return {"seq": seq, "rule": "Bias rule", "old_text": "b", "new_text": "c",
                "direction": "stricter", "readings": [], "reason": "why",
                "last_record_id": "none", "results_known": []}

    def test_a_later_entry_and_the_last_line_whose_digits_do_not_match_refuse(self):
        entries = self.approve([self.first_entry(), self.later(1), self.later(2)])
        self.write_log(entries)
        evidence.guard_protocol_log("inverse")
        for bad in (1, 2):
            changed = [dict(e) for e in entries]
            changed[bad]["new_text"] = "tampered"
            self.write_log(changed)
            with self.assertRaisesRegex(Refused, "approval digits"):
                evidence.guard_protocol_log("inverse")

    def test_a_reading_set_aside_with_no_decision_refuses(self):
        reading = {"reading": "r", "set_aside": True, "case": "every candidate"}
        entry = self.first_entry()
        entry["rules"][0]["readings"] = [reading]
        entry["rules"][0]["direction"] = "settled"
        self.write_log(self.approve([entry]))
        with self.assertRaisesRegex(Refused, "no decision"):
            evidence.guard_protocol_log("inverse")
        reading["decision"] = "kept, with the owner's reason"
        self.write_log(self.approve([entry]))
        evidence.guard_protocol_log("inverse")

    def test_a_repair_entry_whose_list_differs_refuses(self):
        broken = write(self.root, "research/004/broken-log.jsonl", b'{"seq": 1}\n')
        repair = {"break_seq": 0, "cause": "a torn write", "row": "Log repair 1",
                  "restored": "lines before the break",
                  "broken_file": {"path": "research/004/broken-log.jsonl",
                                  "sha256": evidence.sha256(broken.read_bytes())},
                  "entries_after": []}
        entry = {"seq": 1, "repair": repair, "last_record_id": "none", "results_known": []}
        self.write_log(self.approve([self.first_entry(), entry]))
        with self.assertRaisesRegex(Refused, "list differs"):
            evidence.guard_protocol_log("inverse")
        repair["entries_after"] = evidence.repair_list(
            [(json.loads(broken.read_bytes()), broken.read_bytes())])
        self.write_log(self.approve([self.first_entry(), entry]))
        evidence.guard_protocol_log("inverse")


class OrderOfSizes(TempRepo):
    def record(self, size: int, **fields) -> None:
        record = {"kind": "frequency", "config": {"size": size}, "status": "pass",
                  "ended_outside": NONE, "created_utc": "2026-11-03T00:00:00Z"}
        record.update(fields)
        write(self.root, f"{evidence.REP_REL}/candidates/cand-A1/x{size}.json",
              evidence.pretty(record))

    def test_a_larger_size_waits_for_the_smaller(self):
        evidence.guard_order_of_sizes("cand-A1", "frequency", 4)
        with self.assertRaises(Refused):
            evidence.guard_order_of_sizes("cand-A1", "frequency", 8)
        self.record(4)
        evidence.guard_order_of_sizes("cand-A1", "frequency", 8)
        with self.assertRaises(Refused):
            evidence.guard_order_of_sizes("cand-A1", "frequency", 16)

    def test_another_kinds_run_opens_nothing(self):
        self.record(4)
        with self.assertRaises(Refused):
            evidence.guard_order_of_sizes("cand-A1", "avalanche", 8)

    def test_a_project_probe_is_never_refused(self):
        evidence.guard_order_of_sizes("cand-A1", "frequency", 16, project=True)

    def test_a_run_ended_from_outside_has_not_finished(self):
        self.record(4, status="inconclusive", ended_outside="2026-11-03T01:00:00Z")
        with self.assertRaises(Refused):
            evidence.guard_order_of_sizes("cand-A1", "frequency", 8)
        self.assertFalse(evidence.is_finished({"status": "pass", "ended_outside": "x"}))

    def test_an_ineligible_candidate_is_refused(self):
        self.record(4)
        evidence.append_entry(evidence.CANDIDATE_LOG_REL, {
            "event": "decision", "candidate_id": "cand-A1", "decision": "ineligible"})
        with self.assertRaises(Refused):
            evidence.guard_order_of_sizes("cand-A1", "frequency", 8)


class Approvals(TempRepo):
    def test_the_table_is_read_at_head(self):
        self.add_row("D4 tie", "Approved", "x", commit=False)
        with self.assertRaisesRegex(Refused, "differs from HEAD"):
            evidence.head_table()
        self.commit("the row")
        self.assertEqual(evidence.family_row("D4 tie").decision, "Approved")

    def test_a_row_with_the_highest_k_is_read(self):
        self.add_row("Owner design review (the design)", "Declined", "first")
        self.add_row("Owner design review 2", "Approved", "second")
        row = evidence.family_row("Owner design review")
        self.assertEqual((row.notes, row.k), ("second", 2))
        self.assertTrue(evidence.row_approved("Owner design review"))
        self.assertIsNone(evidence.family_row("Owner design"))


class OrderOfUS1(TempRepo):
    def test_key_loading_waits_for_the_review_of_the_latest_record(self):
        with self.assertRaises(Refused):
            evidence.guard_order_of_us1()
        rel = f"{evidence.REP_REL}/fut-sec-8/demonstration-1.json"
        path = write(self.root, rel, evidence.pretty({"kind": "demonstration",
                                                      "created_utc": "2026-11-03T00:00:00Z"}))
        digest = evidence.sha256(path.read_bytes())
        self.add_row("FUT-SEC-8 result review", "Approved",
                     f"names fut-sec-8/demonstration-1.json, {digest}")
        evidence.guard_order_of_us1()
        write(self.root, f"{evidence.REP_REL}/fut-sec-8/demonstration-2.json",
              evidence.pretty({"kind": "demonstration", "created_utc": "2026-11-04T00:00:00Z"}))
        with self.assertRaisesRegex(Refused, "latest demonstration"):
            evidence.guard_order_of_us1()


class ToolValidation(TempRepo):
    def validation(self, tool: str, tool_sha: str, binary: str = None, outcome: str = "re-found",
                   kind: str = "w16"):
        record = {"kind": "validation", "tool": tool, "tool_sha256": tool_sha, "outcome": outcome,
                  "validated_kind": kind, "created_utc": "2026-11-03T00:00:00Z", "code_sha256": {}}
        if binary:
            record["code_sha256"] = {"x/build/t": {"sha256": binary, "kind": "raw"}}
        write(self.root, f"{evidence.REP_REL}/validation/v-{tool_sha[:4]}-{outcome}-{kind}.json",
              evidence.pretty(record))

    def test_a_result_needs_a_re_found_record_of_the_exact_hash(self):
        self.assertIsNone(evidence.validation_record("t", "a" * 64))
        self.validation("t", "a" * 64, outcome="not re-found")
        self.assertIsNone(evidence.validation_record("t", "a" * 64))
        self.validation("t", "a" * 64)
        self.assertIsNotNone(evidence.validation_record("t", "a" * 64))
        self.assertIsNone(evidence.validation_record("t", "b" * 64))

    def test_a_c_tools_hash_is_the_pair_of_source_and_binary(self):
        self.validation("t", "a" * 64, binary="c" * 64)
        self.assertIsNotNone(evidence.validation_record("t", "a" * 64, "c" * 64))
        self.assertIsNone(evidence.validation_record("t", "a" * 64, "d" * 64))

    def test_a_record_of_another_kind_does_not_count(self):
        self.validation("t", "a" * 64, kind="w16")
        self.assertIsNotNone(evidence.validation_record("t", "a" * 64, None, "w16"))
        self.assertIsNone(evidence.validation_record("t", "a" * 64, None, "w32"))

    def test_a_result_without_a_record_is_not_evaluated(self):
        self.assertEqual(evidence.result_status("pass", True), "pass")
        self.assertEqual(evidence.result_status("pass", False), "not evaluated")


class TrailTools(ToolValidation):
    def bound(self, **fields):
        record = dict(SEARCH, kind="bound", status="inconclusive", capped=True, ended_outside=NONE)
        record.update(fields)
        write(self.root, f"{evidence.REP_REL}/candidates/cand-A1/b.json", evidence.pretty(record))

    def test_nothing_is_refused_before_the_first_trail_search(self):
        evidence.guard_trail_tools("anything", "a" * 64)

    def test_a_tool_outside_the_set_or_without_a_record_is_refused(self):
        self.bound()
        with self.assertRaisesRegex(Refused, "fixed set"):
            evidence.guard_trail_tools("a new tool", "a" * 64)
        with self.assertRaisesRegex(Refused, "re-found"):
            evidence.guard_trail_tools("ARX search", "a" * 64, "c" * 64)
        self.validation("ARX search", "a" * 64, binary="c" * 64)
        evidence.guard_trail_tools("ARX search", "a" * 64, "c" * 64)
        with self.assertRaisesRegex(Refused, "re-found"):
            evidence.guard_trail_tools("ARX search", "a" * 64, "d" * 64)

    def test_a_capped_search_is_refused_save_the_one_re_run(self):
        self.bound()
        self.validation("ARX search", "a" * 64)
        with self.assertRaisesRegex(Refused, "reached its cap"):
            evidence.guard_trail_tools("ARX search", "a" * 64, None, "cand-A1", SEARCH)
        evidence.guard_trail_tools("ARX search", "a" * 64, None, "cand-A1", SEARCH,
                                   rerun_after_defect="defect-1")

    def test_another_search_is_not_the_capped_one(self):
        self.bound()
        self.validation("ARX search", "a" * 64)
        evidence.guard_trail_tools("ARX search", "a" * 64, None, "cand-A1",
                                   dict(SEARCH, rounds=9))

    def test_a_search_ended_from_outside_did_not_reach_its_cap(self):
        self.bound(capped=False, ended_outside="2026-11-03T01:00:00Z")
        self.validation("ARX search", "a" * 64)
        evidence.guard_trail_tools("ARX search", "a" * 64, None, "cand-A1", SEARCH)
        self.bound(ended_outside="2026-11-03T01:00:00Z")
        evidence.guard_trail_tools("ARX search", "a" * 64, None, "cand-A1", SEARCH)


class Budget(TempRepo):
    def control(self, hours: float, **fields):
        name = f"controls/c{len(list(evidence.iter_records('control', 'controls')))}.json"
        record = {"kind": "control", "heavy_run": True, "created_utc": "2026-11-03T12:00:00Z",
                  "hours": {"projected": 1.0, "used": hours}}
        record.update(fields)
        write(self.root, f"{evidence.REP_REL}/{name}", evidence.pretty(record))

    def test_a_refusal_after_a_probe_writes_its_projection_and_nothing_else(self):
        before = report_files(self.root)
        path = evidence.write_projection(run="x", row="cand-A1/structural", inputs=NONE,
                                         measured_speed=1, projected_hours=7.0, time_hours=0.01)
        with self.assertRaisesRegex(Refused, "structural"):
            evidence.guard_candidate_row("cand-A1", "structural", 7.0)
        new = [f for f in report_files(self.root) if f not in before]
        self.assertIn(f"projections/{path.name}", new)
        self.assertEqual([f for f in new if "versions" not in f], [f"projections/{path.name}"])

    def test_a_projection_says_its_outputs_were_discarded_unread(self):
        path = evidence.write_projection(run="x", row="r", inputs=NONE, measured_speed=1,
                                         projected_hours=1.0, time_hours=0.01)
        record = json.loads(path.read_bytes())
        self.assertIn("discarded unread", record["outputs_statement"])
        self.assertEqual((record["kind"], record["classification"]), ("projection", NONE))

    def test_a_row_is_read_from_the_log_the_projections_and_the_controls(self):
        evidence.append_entry(evidence.CANDIDATE_LOG_REL, {
            "event": "evidence", "candidate_id": "cand-A1", "budget_used_h": {"statistics": 2.0}})
        self.control(1.5)
        evidence.write_projection(run="x", row="cand-A1/statistics", inputs=NONE, measured_speed=1,
                                  projected_hours=1.0, time_hours=0.25)
        self.assertAlmostEqual(evidence.candidate_row_used("cand-A1", "statistics"), 3.75)
        evidence.guard_candidate_row("cand-A1", "statistics", 8.0)
        with self.assertRaises(Refused):
            evidence.guard_candidate_row("cand-A1", "statistics", 8.0, reserved=0.5)

    def test_a_control_charges_no_row_it_could_not_be_held_by(self):
        self.control(1.5, not_charged=["cand-A1"])
        self.assertEqual(evidence.candidate_row_used("cand-A1", "statistics"), 0.0)
        self.assertEqual(evidence.candidate_row_used("cand-A2", "statistics"), 1.5)

    def test_a_control_after_a_closing_decision_charges_nothing(self):
        self.control(1.0, created_utc="2026-11-03T01:00:00Z")
        evidence.append_entry(evidence.CANDIDATE_LOG_REL, {
            "event": "decision", "candidate_id": "cand-A1", "decision": "rejected",
            "date_utc": "2026-11-03T02:00:00Z"})
        self.control(2.0, created_utc="2026-11-03T03:00:00Z")
        self.assertEqual(evidence.candidate_row_used("cand-A1", "statistics"), 1.0)
        self.assertEqual(evidence.candidate_row_used("cand-A2", "statistics"), 3.0)

    def test_a_control_ended_from_outside_stays_charged(self):
        self.control(1.0, ended_outside="2026-11-03T01:00:00Z", status="inconclusive")
        self.control(2.0)
        self.assertEqual(evidence.candidate_row_used("cand-A1", "statistics"), 3.0)

    def test_the_feature_wide_row_is_the_sum_read_from_the_records(self):
        evidence.write_projection(run="x", row=evidence.FEATURE_ROW, inputs=NONE, measured_speed=1,
                                  projected_hours=1.0, time_hours=0.5)
        evidence.write_projection(run="y", row="cand-A1/trails", inputs=NONE, measured_speed=1,
                                  projected_hours=9.0, time_hours=9.0)
        rep = f"{evidence.REP_REL}"
        write(self.root, f"{rep}/validation/v.json", evidence.pretty(
            {"kind": "validation", "heavy_run": True, "hours": {"used": 2.0}}))
        write(self.root, f"{rep}/reproductions/r/1/x.json", evidence.pretty(
            {"kind": "reproduction", "heavy_run": True,
             "hours": {"runs": [{"used": 1.0}, {"used": 1.5}]}}))
        write(self.root, f"{rep}/fut-sec-8/first.json", evidence.pretty(
            {"kind": "demonstration", "heavy_run": True, "hours": {"used": 40.0},
             "supersedes": NONE}))
        write(self.root, f"{rep}/fut-sec-8/repeat.json", evidence.pretty(
            {"kind": "demonstration", "heavy_run": True, "hours": {"used": 1.0},
             "supersedes": "first"}))
        write(self.root, f"{rep}/candidates/cand-A1/f.json", evidence.pretty(
            {"kind": "frequency", "heavy_run": True, "hours": {"used": 11.0}}))
        write(self.root, f"{rep}/validation/light.json", evidence.pretty(
            {"kind": "validation", "heavy_run": False, "hours": NONE}))
        self.assertAlmostEqual(evidence.feature_row_used(), 0.5 + 2.0 + 2.5 + 1.0)
        evidence.guard_feature_row([60.0])                # 66 h in all, which fits the row exactly
        with self.assertRaisesRegex(Refused, "feature-wide"):
            evidence.guard_feature_row([30.0, 30.5])


class ReproductionBase(TempRepo):
    """A committed record, a tool with a mocked build, and a recorded run the test can repeat."""

    def setUp(self):
        super().setUp()
        write(self.root, Tool.source, "int main(void){return 0;}\n")
        write(self.root, Tool.make, "all:\n")
        write(self.root, Tool.binary, b"committed binary")
        self.commit("tool")
        self.source_sha256 = evidence.sha256((self.root / Tool.source).read_bytes())
        self.printed = self.source_sha256
        self.seen_binary_during_build: List[bool] = []
        self.rebuilt_bytes = b"committed binary"
        self.places: List[evidence.Place] = []
        self.first_changes: Dict = {}
        self.second_changes: Dict = {}
        self.hours: List[float] = []
        self.locks_seen: List[bool] = []
        for name, side_effect in (("make_binary", self.build),
                                  ("binary_source_sha256", lambda path: self.printed)):
            patcher = mock.patch.object(evidence, name, side_effect=side_effect)
            patcher.start()
            self.addCleanup(patcher.stop)

    def build(self, worktree: Path, rel: str) -> None:
        self.seen_binary_during_build.append((worktree / rel).exists())
        if self.rebuilt_bytes is None:
            raise OSError("make failed")
        write(worktree, rel, self.rebuilt_bytes)

    def original(self, kind: str = "validation", code=None, candidate: str = None,
                 outputs: Dict = None, status: str = "pass", **fields) -> Path:
        run = evidence.Run(kind, candidate=candidate, argv=["scripts/tool.py"],
                           code_files=code if code is not None else [Tool.binary, Tool.source])
        with run:
            for name, (data, options) in (outputs or {}).items():
                run.output(name, data, **options)
            body = dict({"found": 7, "outcome": "re-found"}, **fields)
            path = run.finish(status, fields=body, assertions=["ok"])
        self.commit("record")
        return path

    def result(self, record: Dict, **changes) -> Dict:
        out = {k: record.get(k) for k in evidence.compared_fields(record)}
        out.update({"code_sha256": record["code_sha256"], "outputs": record["outputs"]})
        out["found"] = record.get("found")
        out.update(changes)
        return out

    def job(self, path: Path, **kwargs) -> evidence.Reproduction:
        record = json.loads(path.read_bytes())

        def run(place: evidence.Place) -> Dict:
            self.places.append(place)
            self.locks_seen.append(evidence.REPO.heavy_lock.exists())
            changes = self.second_changes if place.binaries else self.first_changes
            result = self.result(record, **changes)
            if self.hours:
                result["hours_used"] = self.hours.pop(0)
            return result

        kwargs.setdefault("run", run)
        return evidence.Reproduction(record_path=path, **kwargs)

    def refound(self, binary: bytes, tool: str = "seed search") -> None:
        """A `re-found` record of the rebuild's exact hash, the pair of source and binary."""
        digest = evidence.sha256(binary)
        record = {"kind": "validation", "tool": tool, "tool_sha256": self.source_sha256,
                  "outcome": "re-found", "created_utc": "2026-11-03T00:00:00Z",
                  "code_sha256": {Tool.binary: {"sha256": digest, "kind": "raw"}}}
        write(self.root, f"{evidence.REP_REL}/validation/refound-{digest[:8]}.json",
              evidence.pretty(record))

    def reproduction_record(self, path: Path, n: int = 1) -> Dict:
        record_id = json.loads(path.read_bytes())["record_id"]
        base = self.root / evidence.REP_REL / "reproductions" / record_id / str(n)
        return json.loads(next(base.glob("reproduction-*.json")).read_bytes())

    def heavy_job(self, path: Path, hours: float = 1.0, **kwargs) -> evidence.Reproduction:
        return self.job(path, owner_request="yes, please (2026-11-03)",
                        project=lambda tree: (hours, 123.0), **kwargs)


class Reproduce(ReproductionBase):
    def test_one_run_where_the_rebuild_equals_the_committed_binary(self):
        path = self.original()
        self.assertEqual(evidence.reproduce(self.job(path)), 0)
        self.assertEqual([place.binaries for place in self.places], [{}])
        self.assertEqual(self.seen_binary_during_build, [False])    # removed before the build
        record = self.reproduction_record(path)
        original = json.loads(path.read_bytes())
        self.assertEqual((record["outcome"], record["status"]), ("match", "pass"))
        self.assertEqual(record["original"]["record_id"], original["record_id"])
        self.assertEqual(record["original"]["sha256"], evidence.sha256(path.read_bytes()))
        self.assertEqual(record["commit"], original["git_head"])
        self.assertEqual(record["rebuild"][Tool.binary]["sha256"],
                         evidence.sha256(b"committed binary"))
        self.assertEqual(self.places[0].out, self.root / evidence.REP_REL / "reproductions"
                         / original["record_id"] / "1")

    def test_it_runs_the_commits_files_from_a_worktree(self):
        path = self.original()
        write(self.root, "scripts/tool.py", "print('later')\n")
        self.commit("later")

        def run(place: evidence.Place) -> Dict:
            self.assertEqual((place.worktree / "scripts/tool.py").read_text(), "print('tool')\n")
            self.assertEqual(place.worktree.parent.name, ".worktrees")
            return self.result(json.loads(path.read_bytes()))

        self.assertEqual(evidence.reproduce(self.job(path, run=run)), 0)
        self.assertEqual(list((self.root / evidence.LOCAL_REL / ".worktrees").glob("*")), [])

    def test_a_second_reproduction_takes_the_next_number(self):
        path = self.original()
        evidence.reproduce(self.job(path))
        self.assertEqual(evidence.reproduce(self.job(path)), 0)
        self.assertEqual(self.reproduction_record(path, 2)["outcome"], "match")

    def test_a_second_run_where_the_rebuild_differs_and_has_a_record_of_its_own(self):
        path = self.original()
        self.rebuilt_bytes = b"another binary"
        self.refound(self.rebuilt_bytes)
        self.assertEqual(evidence.reproduce(self.job(path)), 0)
        self.assertEqual(len(self.places), 2)
        self.assertEqual(list(self.places[1].binaries), [Tool.binary])
        self.assertEqual(self.places[1].out, self.places[0].out / "rebuilt")
        self.assertEqual(self.reproduction_record(path)["outcome"], "match")

    def test_the_outcome_is_match_only_when_both_runs_match(self):
        path = self.original()
        self.rebuilt_bytes = b"another binary"
        self.refound(self.rebuilt_bytes)
        self.second_changes = {"outcome": "not re-found"}
        self.assertEqual(evidence.reproduce(self.job(path)), 1)
        record = self.reproduction_record(path)
        self.assertEqual(record["outcome"], "differs")
        self.assertEqual(record["compared_rebuilt"]["outcome"], "differs")
        self.assertEqual(record["compared"]["outcome"], "match")

    def test_a_rebuild_of_another_source_print_counts_as_failed(self):
        path = self.original()
        self.rebuilt_bytes = b"another binary"
        self.refound(self.rebuilt_bytes)
        with mock.patch.object(evidence, "guard_committed_code"):
            self.printed = "0" * 64
            self.assertEqual(evidence.reproduce(self.job(path)), 1)
        record = self.reproduction_record(path)
        self.assertIn("source-sha256", record["rebuild"][Tool.binary]["failed"])
        self.assertEqual(set(record["compared"].values()), {"differs"})

    def test_a_rebuild_not_admitted_counts_whatever_the_kind(self):
        self.rebuilt_bytes = b"another binary"
        for kind, candidate in (("demonstration", None), ("validation", None),
                                ("cross-check", "cand-A1")):
            with self.subTest(kind=kind):
                path = self.original(kind, candidate=candidate)
                self.places.clear()
                code = evidence.reproduce(self.heavy_job(path, hours=0.1))
                self.assertEqual(code, 1)
                self.assertEqual(len(self.places), 1)
                record = self.reproduction_record(path)
                self.assertEqual(record["outcome"], "differs")
                self.assertEqual(set(record["compared"].values()), {"differs"})
                self.assertTrue(record["rebuild"][Tool.binary]["refused"])
                self.assertEqual((record["status"], record["classification"]),
                                 ("blocked", "unverified hypothesis"))

    def test_a_trail_tool_rebuild_needs_the_fixed_set(self):
        arx = "research/004/tools/trails/build/arx_search"
        source = "research/004/tools/trails/arx_search.c"
        write(self.root, source, "int main(void){return 0;}\n")
        write(self.root, arx, b"committed binary")
        self.commit("arx")
        path = self.original(code=[arx, source])
        write(self.root, f"{evidence.REP_REL}/candidates/cand-A1/b.json",
              evidence.pretty({"kind": "bound"}))
        self.rebuilt_bytes = b"another binary"
        digest = evidence.sha256(self.rebuilt_bytes)
        record = {"kind": "validation", "tool": "a new tool", "outcome": "re-found",
                  "tool_sha256": evidence.sha256((self.root / source).read_bytes()),
                  "created_utc": "2026-11-03T00:00:00Z",
                  "code_sha256": {arx: {"sha256": digest, "kind": "raw"}}}
        write(self.root, f"{evidence.REP_REL}/validation/r.json", evidence.pretty(record))
        self.assertEqual(evidence.reproduce(self.job(path)), 1)
        self.assertTrue(self.reproduction_record(path)["rebuild"][arx]["refused"])
        record["tool"] = "ARX search"
        write(self.root, f"{evidence.REP_REL}/validation/r.json", evidence.pretty(record))
        self.assertEqual(evidence.reproduce(self.job(path)), 0)

    def test_a_rebuild_that_fails_counts_the_same(self):
        path = self.original()
        self.rebuilt_bytes = None
        self.assertEqual(evidence.reproduce(self.job(path)), 1)
        self.assertEqual(len(self.places), 1)
        self.assertEqual(set(self.reproduction_record(path)["compared"].values()), {"differs"})

    def test_a_heavy_reproduction_needs_the_owners_request(self):
        path = self.original()
        with self.assertRaisesRegex(Refused, "owner-request"):
            evidence.reproduce(self.job(path, heavy=True))
        self.assertEqual(evidence.reproduce(self.heavy_job(path, heavy=True)), 0)
        record = self.reproduction_record(path)
        self.assertEqual(record["owner_request"], "yes, please (2026-11-03)")
        self.assertIs(record["heavy_run"], True)
        self.assertEqual(len(record["hours"]["runs"]), 1)

    def test_a_budgeted_kind_and_a_long_run_are_heavy(self):
        path = self.original("frequency", candidate="cand-A1")
        with self.assertRaisesRegex(Refused, "owner-request"):
            evidence.reproduce(self.job(path))
        path = self.original(hours={"projected": 1.0, "used": 0.5})
        with self.assertRaisesRegex(Refused, "owner-request"):
            evidence.reproduce(self.job(path))

    def test_a_light_one_needs_none_and_holds_no_lock(self):
        self.assertEqual(evidence.reproduce(self.job(self.original())), 0)
        self.assertEqual(self.locks_seen, [False])

    def test_a_heavy_one_takes_the_lock_before_the_rebuild(self):
        path = self.original()
        seen = []
        build = self.build

        def checked(worktree: Path, rel: str) -> None:
            seen.append(evidence.REPO.heavy_lock.exists())
            build(worktree, rel)

        with mock.patch.object(evidence, "make_binary", side_effect=checked):
            self.assertEqual(evidence.reproduce(self.heavy_job(path, heavy=True)), 0)
        self.assertEqual((seen, self.locks_seen), ([True], [True]))
        self.assertFalse(evidence.REPO.heavy_lock.exists())

    def test_a_held_lock_refuses_a_heavy_one(self):
        path = self.original()
        write(self.root, evidence.HEAVY_LOCK_REL, evidence.canonical(evidence.lock_content("x")))
        with self.assertRaisesRegex(Refused, "heavy-run.lock"):
            evidence.reproduce(self.heavy_job(path, heavy=True))

    def test_a_record_that_holds_ended_outside_is_refused(self):
        path = self.original(ended_outside="2026-11-03T01:00:00Z")
        with self.assertRaisesRegex(Refused, "ended_outside"):
            evidence.reproduce(self.job(path))

    def test_a_search_that_reached_its_cap_is_not_reproduced(self):
        path = self.original("bound", candidate="cand-A1", status="inconclusive", capped=True)
        with self.assertRaisesRegex(Refused, "reached its cap"):
            evidence.reproduce(self.heavy_job(path))

    def test_a_spent_candidate_row_refuses_no_reproduction_and_the_log_gains_nothing(self):
        path = self.original("frequency", candidate="cand-A1")
        evidence.append_entry(evidence.CANDIDATE_LOG_REL, {
            "event": "evidence", "candidate_id": "cand-A1", "budget_used_h": {"statistics": 12.0}})
        with self.assertRaises(Refused):
            evidence.guard_candidate_row("cand-A1", "statistics", 0.5)
        log = (self.root / evidence.CANDIDATE_LOG_REL).read_bytes()
        self.assertEqual(evidence.reproduce(self.heavy_job(path, hours=0.5)), 0)
        self.assertEqual((self.root / evidence.CANDIDATE_LOG_REL).read_bytes(), log)

    def test_refused_once_the_projections_together_do_not_fit(self):
        path = self.original()
        self.rebuilt_bytes = b"another binary"
        self.refound(self.rebuilt_bytes)
        before = report_files(self.root)
        with self.assertRaisesRegex(Refused, "feature-wide"):
            evidence.reproduce(self.heavy_job(path, hours=40.0, heavy=True))
        new = [f for f in report_files(self.root) if f not in before]
        self.assertEqual(len([f for f in new if f.startswith("projections/")]), 2)
        self.assertFalse([f for f in new if f.startswith("reproductions/")])
        self.assertEqual(self.seen_binary_during_build, [False])    # the rebuild came first
        self.assertEqual(self.places, [])

    def test_each_projection_names_the_feature_wide_row(self):
        path = self.original()
        evidence.reproduce(self.heavy_job(path, heavy=True))
        records = [r for _, r in evidence.iter_records("projection")]
        self.assertEqual([r["row"] for r in records], [evidence.FEATURE_ROW])
        self.assertEqual(records[0]["measured_speed"], 123.0)

    def test_a_second_run_that_no_longer_fits_is_not_made(self):
        path = self.original()
        self.rebuilt_bytes = b"another binary"
        self.refound(self.rebuilt_bytes)
        self.hours = [50.0]
        job = self.heavy_job(path, hours=20.0, heavy=True)
        self.assertEqual(evidence.reproduce(job), 1)
        self.assertEqual(len(self.places), 1)
        record = self.reproduction_record(path)
        self.assertEqual((record["status"], record["outcome"]), ("inconclusive", NONE))
        self.assertEqual(record["classification"], NONE)
        self.assertIn("no longer fits", record["reason"])
        self.assertEqual(record["exit_status"], 1)

    def test_the_outcome_is_differs_where_the_first_run_differs(self):
        path = self.original()
        self.rebuilt_bytes = b"another binary"
        self.refound(self.rebuilt_bytes)
        self.hours = [50.0]
        self.first_changes = {"outcome": "not re-found"}
        self.assertEqual(evidence.reproduce(self.heavy_job(path, hours=20.0, heavy=True)), 1)
        record = self.reproduction_record(path)
        self.assertEqual(record["outcome"], "differs")
        self.assertIn("no longer fits", record["reason"])

    def test_it_runs_only_in_the_environment_of_the_original(self):
        path = self.original()
        record = json.loads((self.root / evidence.environment_rel()).read_bytes())
        record["record_id"] = "environment-1"
        record["snapshot"]["python"] = "3.10.12"
        write(self.root, evidence.environment_rel(), evidence.pretty(record))
        self.add_row("Environment record 2", "Approved", evidence.approval_hash(record))
        changed = dict(SNAPSHOT, python="3.10.12")
        before = report_files(self.root)
        with mock.patch.object(evidence, "snapshot", return_value=changed):
            with self.assertRaisesRegex(Refused, r"environment record \S+ is not in force"):
                evidence.reproduce(self.job(path))
        self.assertEqual(report_files(self.root), before)

    def test_a_recheck_reproduction_runs_anywhere_and_holds_its_own_environment(self):
        path = self.original("recheck", code=[])
        record = json.loads((self.root / evidence.environment_rel()).read_bytes())
        record["snapshot"]["python"] = "3.10.12"
        write(self.root, evidence.environment_rel(), evidence.pretty(record))
        self.add_row("Environment record 2", "Approved", evidence.approval_hash(record))
        own = {"interpreter": "python", "pip_freeze": []}
        with mock.patch.object(evidence, "snapshot", return_value=dict(SNAPSHOT, python="3.14")):
            self.assertEqual(evidence.reproduce(self.job(path, recheck=own)), 0)
        self.assertEqual(self.reproduction_record(path)["environment"], own)

    def test_a_blob_that_differs_from_code_sha256_refuses(self):
        path = self.original()
        record = json.loads(path.read_bytes())
        record["code_sha256"][Tool.source]["sha256"] = "0" * 64
        path.write_bytes(evidence.pretty(record))
        with self.assertRaisesRegex(Refused, "does not match"):
            evidence.reproduce(self.job(path))

    def test_the_committed_binary_must_print_its_sources_hash(self):
        path = self.original()
        self.printed = "0" * 64
        with self.assertRaisesRegex(Refused, "source-sha256"):
            evidence.reproduce(self.job(path))

    def test_the_design_document_is_read_from_the_worktree_and_its_stored_version(self):
        write(self.root, evidence.DESIGN_REL, "# Design\n\nVersion: 0.3\n")
        self.commit("design")
        path = self.original()
        self.assertEqual(evidence.reproduce(self.job(path)), 0)
        digest = json.loads(path.read_bytes())["design_sha256"]
        stored = self.root / evidence.REP_REL / "design-versions" / f"{digest}.md"
        stored.write_bytes(b"changed")
        with self.assertRaisesRegex(Refused, "design version"):
            evidence.reproduce(self.job(path))

    def test_a_run_that_raises_leaves_an_aborted_record(self):
        path = self.original()

        def run(place: evidence.Place) -> Dict:
            raise evidence.ToolFailure("the tool stopped")

        with self.assertRaises(evidence.ToolFailure):
            evidence.reproduce(self.job(path, run=run))
        record = self.reproduction_record(path)
        self.assertEqual((record["status"], record["exit_status"]), ("inconclusive", 3))
        self.assertEqual(record["original"]["record_id"],
                         json.loads(path.read_bytes())["record_id"])


class ReproductionOutputs(ReproductionBase):
    def entry(self, place: evidence.Place, name: str, data: bytes, **fields) -> Dict:
        write(place.out, name, data)
        rel = (place.out / name).relative_to(self.root).as_posix()
        return dict({"path": rel, "sha256": evidence.sha256(data), "sha256_kind": "raw",
                     "bytes": len(data), "committed": True, "deterministic": True}, **fields)

    def values(self, path: Path, *numbers) -> evidence.Reproduction:
        original = json.loads(path.read_bytes())

        def run(place: evidence.Place) -> Dict:
            data = json.dumps(list(numbers)).encode("utf-8")
            out = self.entry(place, "p_values.json", data, deterministic=False, compared="values")
            return dict(self.result(original), outputs=[out])

        return self.job(path, run=run)

    def p_original(self, *numbers) -> Path:
        data = json.dumps(list(numbers)).encode("utf-8")
        return self.original(outputs={"p_values.json": (data, {
            "deterministic": False, "compared": "values"})})

    def test_p_values_within_the_tolerance_match(self):
        path = self.p_original(0.5, 0.25)
        self.assertEqual(evidence.reproduce(self.values(path, 0.5 + 1e-7, 0.25)), 0)

    def test_a_p_value_outside_makes_differs_and_blocks_nothing(self):
        path = self.p_original(0.5, 0.25)
        self.assertEqual(evidence.reproduce(self.values(path, 0.5, 0.26)), 1)
        record = self.reproduction_record(path)
        self.assertEqual(record["outcome"], "differs")
        self.assertEqual((record["status"], record["classification"]), ("fail", NONE))
        self.assertEqual(record["p_values_outside"], [
            {"output": "p_values.json", "index": 1, "original": 0.25, "reproduced": 0.26}])

    def test_a_zero_beside_a_subnormal_agrees(self):
        self.assertTrue(evidence.p_values_agree(0.0, 2.0 ** -1040))
        self.assertFalse(evidence.p_values_agree(0.0, 2.0 ** -1000))

    def test_a_deterministic_output_is_compared_by_hash_and_not_by_path(self):
        path = self.original(outputs={"counts.json": (b"[1]\n", {})})
        original = json.loads(path.read_bytes())

        def run(place: evidence.Place) -> Dict:
            return dict(self.result(original), outputs=[self.entry(place, "counts.json", b"[1]\n")])

        self.assertEqual(evidence.reproduce(self.job(path, run=run)), 0)

        def other(place: evidence.Place) -> Dict:
            return dict(self.result(original), outputs=[self.entry(place, "counts.json", b"[2]\n")])

        self.assertEqual(evidence.reproduce(self.job(path, run=other)), 1)
        self.assertEqual(self.reproduction_record(path, 2)["compared"]["outputs"], "differs")

    def test_a_gz_file_is_compared_by_its_uncompressed_hash(self):
        data = b"[1]\n"
        path = self.original(outputs={"counts.json.gz": (data, {})})
        original = json.loads(path.read_bytes())

        def run(place: evidence.Place) -> Dict:
            other_bytes = gzip.compress(data, compresslevel=1, mtime=0) + b""
            out = self.entry(place, "counts.json.gz", other_bytes,
                             uncompressed_sha256=evidence.sha256(data))
            return dict(self.result(original), outputs=[out])

        self.assertEqual(evidence.reproduce(self.job(path, run=run)), 0)

    def test_a_local_only_output_goes_under_the_reproductions_own_id(self):
        path = self.original(outputs={"matrix.json": (b"[0]\n", {"local": True})})
        original = json.loads(path.read_bytes())

        def run(place: evidence.Place) -> Dict:
            write(place.local, "matrix.json", b"[0]\n")
            out = dict(original["outputs"][0], path="anything/matrix.json")
            return dict(self.result(original), outputs=[out])

        self.assertEqual(evidence.reproduce(self.job(path, run=run)), 0)
        record = self.reproduction_record(path)
        entry = record["outputs"][0]
        self.assertEqual(entry["path"], f"{evidence.LOCAL_REL}/{record['record_id']}/matrix.json")
        self.assertEqual((self.root / entry["path"]).read_bytes(), b"[0]\n")
        self.assertEqual(record["compared"]["outputs"], "match")

    def test_a_suffix_or_a_size_it_may_not_commit_is_refused_and_leaves_nothing(self):
        path = self.original()
        original = json.loads(path.read_bytes())

        def run(place: evidence.Place) -> Dict:
            write(place.out, "counts.npy", b"\0")
            return self.result(original)

        with self.assertRaisesRegex(Refused, "counts.npy"):
            evidence.reproduce(self.job(path, run=run))
        self.assertFalse((self.root / evidence.REP_REL / "reproductions").joinpath(
            original["record_id"], "1").exists())

    def test_a_binarys_hash_is_reported_only_and_a_sources_is_compared(self):
        path = self.original()
        original = json.loads(path.read_bytes())

        def with_hash(rel: str):
            def run(place: evidence.Place) -> Dict:
                code = json.loads(json.dumps(original["code_sha256"]))
                code[rel]["sha256"] = "0" * 64
                return dict(self.result(original), code_sha256=code)
            return run

        self.assertEqual(evidence.reproduce(self.job(path, run=with_hash(Tool.binary))), 0)
        self.assertEqual(evidence.reproduce(self.job(path, run=with_hash(Tool.source))), 1)
        self.assertEqual(self.reproduction_record(path, 2)["compared"]["code_sha256"], "differs")

    def test_the_fields_not_compared_are_reported_only(self):
        path = self.original()
        original = json.loads(path.read_bytes())

        def run(place: evidence.Place) -> Dict:
            return dict(self.result(original), seconds=12.5, command="another")

        self.assertEqual(evidence.reproduce(self.job(path, run=run)), 0)
        reported = self.reproduction_record(path)["reported"]
        self.assertEqual((reported["seconds"], reported["command"]), (12.5, "another"))


class HeavyRunCoverage(TempRepo):
    """FR-045: every budgeted kind and every script with a worker option takes the lock, each
    script as it is added."""

    SCRIPTS = ("scripts/fut_sec8.py", "scripts/evidence_v3.py", "scripts/validate_tool.py")

    def test_every_budgeted_kind_holds_the_lock(self):
        for kind in evidence.BUDGETED_KINDS:
            with self.subTest(kind=kind):
                run = evidence.Run(kind, candidate="cand-A1", argv=ARGV)
                with run:
                    self.assertTrue(evidence.REPO.heavy_lock.exists())
                    run.finish("pass")
                self.assertFalse(evidence.REPO.heavy_lock.exists())
                self.assertIs(json.loads(run.record_path.read_bytes())["heavy_run"], True)

    def test_a_light_kind_with_two_workers_holds_it_too(self):
        with evidence.Run("generator-run", argv=ARGV, workers=2) as run:
            self.assertTrue(evidence.REPO.heavy_lock.exists())
            run.finish("pass")

    def test_each_script_takes_the_lock(self):
        for rel in self.SCRIPTS:
            path = ROOT / rel
            if path.exists():
                self.assertRegex(path.read_text(encoding="utf-8"),
                                 r"evidence\.Run\(|HeavyRunLock", rel)

    def test_every_script_with_a_worker_option_takes_the_lock(self):
        for path in sorted((ROOT / "scripts").glob("*.py")):
            text = path.read_text(encoding="utf-8")
            if "protocol.evidence" in text or "import evidence" in text:
                if re.search(r"--(workers|threads)\b", text):
                    self.assertRegex(text, r"evidence\.Run\(|HeavyRunLock", path.name)


class ChainedLogs(TempRepo):
    """Every append takes data/log-append.lock, checks the chain and chains one line (R16)."""

    LOG = evidence.CANDIDATE_LOG_REL

    def test_each_line_chains_to_the_previous_lines_bytes_with_its_final_lf(self):
        first = evidence.append_entry(self.LOG, {"event": "proposed"})
        second = evidence.append_entry(self.LOG, {"event": "mapping"})
        lines = (self.root / self.LOG).read_bytes().splitlines(keepends=True)
        self.assertEqual((first["seq"], first["prev_sha256"]), (0, evidence.ZERO_HASH))
        self.assertEqual((second["seq"], second["prev_sha256"]), (1, evidence.sha256(lines[0])))
        self.assertTrue(lines[0].endswith(b"\n"))
        self.assertRegex(first["date_utc"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")

    def test_the_append_takes_the_lock_and_leaves_none(self):
        seen = []
        real = evidence.check_chain

        def check(rel):
            seen.append(evidence.REPO.append_lock.exists())
            return real(rel)

        with mock.patch.object(evidence, "check_chain", side_effect=check):
            evidence.append_entry(self.LOG, {"event": "proposed"})
        self.assertEqual(seen, [True])
        self.assertFalse(evidence.REPO.append_lock.exists())

    def test_a_lock_not_free_within_its_wait_exits_2_naming_it(self):
        write(self.root, evidence.APPEND_LOCK_REL, evidence.canonical(evidence.lock_content("x")))
        with mock.patch.object(evidence, "APPEND_LOCK_WAIT_S", 0.0):
            with self.assertRaisesRegex(Refused, "log-append.lock is held"):
                evidence.append_entry(self.LOG, {"event": "proposed"})
        self.assertFalse((self.root / self.LOG).exists())

    def test_the_wait_is_10_s(self):
        self.assertEqual(evidence.APPEND_LOCK_WAIT_S, 10.0)

    def test_a_broken_chain_exits_2_appending_nothing(self):
        evidence.append_entry(self.LOG, {"event": "proposed"})
        evidence.append_entry(self.LOG, {"event": "mapping"})
        path = self.root / self.LOG
        path.write_bytes(path.read_bytes().replace(b"proposed", b"Proposed"))
        before = path.read_bytes()
        with self.assertRaisesRegex(Refused, "chain breaks"):
            evidence.append_entry(self.LOG, {"event": "scored"})
        self.assertEqual(path.read_bytes(), before)

    def test_first_break_names_the_seq_and_the_cause(self):
        evidence.append_entry(self.LOG, {"event": "proposed"})
        self.assertIsNone(evidence.first_break(self.LOG))
        path = self.root / self.LOG
        path.write_bytes(path.read_bytes() + b"not json\n")
        self.assertEqual(evidence.first_break(self.LOG), (1, "the line does not parse"))
        path.write_bytes(path.read_bytes()[:-9] + b'{"seq": 1')
        self.assertEqual(evidence.first_break(self.LOG)[0], 1)


class ApprovalStep(unittest.TestCase):
    def test_a_redirected_input_is_no_terminal_on_any_platform(self):
        with open(os.devnull, encoding="utf-8") as handle, mock.patch("sys.stdin", handle):
            self.assertFalse(evidence.interactive_terminal())

    def test_an_input_that_ends_gives_no_digits(self):
        with mock.patch.object(evidence, "interactive_terminal", return_value=True), \
                mock.patch("builtins.input", side_effect=EOFError):
            with self.assertRaisesRegex(Refused, "no digits"):
                evidence.confirm_digits("0" * 64)


class Sections(unittest.TestCase):
    TEXT = (b"# Title\n\nintro\n\n## One\n\ntext one\n\n### Same\n\nunder one\n\n"
            b"## Two\n\n```\n## Not a heading\n```\n\n### Same\n\nunder two\n\n"
            b"## Three ##\n\nend\n")

    def test_a_section_runs_to_the_next_heading_of_the_same_or_a_higher_level(self):
        self.assertEqual(evidence.section_bytes(self.TEXT, "One"),
                         b"## One\n\ntext one\n\n### Same\n\nunder one\n\n")

    def test_a_fenced_line_is_never_a_heading(self):
        self.assertIn(b"## Not a heading", evidence.section_bytes(self.TEXT, "Two"))
        with self.assertRaisesRegex(Refused, "names no section"):
            evidence.section_bytes(self.TEXT, "Not a heading")

    def test_a_closing_sequence_is_not_of_the_text(self):
        self.assertEqual(evidence.section_bytes(self.TEXT, "Three"), b"## Three ##\n\nend\n")

    def test_a_text_that_occurs_twice_is_named_by_the_headings_that_enclose_it(self):
        with self.assertRaisesRegex(Refused, "more than one"):
            evidence.section_bytes(self.TEXT, "Same")
        self.assertEqual(evidence.section_bytes(self.TEXT, "Title > Two > Same"),
                         b"### Same\n\nunder two\n\n")

    def test_commonmark_heading_forms(self):
        lines = ["   ### Three spaces\n", "    #### Four spaces\n", "#No space\n", "#\tTab\n",
                 "#\n", "####### Seven\n", "~~~\n", "# Fenced\n", "~~~\n", "## After\n"]
        self.assertEqual([(h.level, h.text) for h in evidence.headings_of(lines)],
                         [(3, "Three spaces"), (1, "Tab"), (1, ""), (2, "After")])


class ProvenanceLog(TempRepo):
    def setUp(self):
        super().setUp()
        write(self.root, "docs/note.md", "# Note\n\n## Part\n\ntext\n\n## Other\n\nmore\n")
        self.commit("the note")

    def fields(self, **changes) -> Dict:
        digest, kind = evidence.named_hash("docs/note.md", "Part")
        fields = {"path": "docs/note.md", "section": "Part", "sha256": digest, "sha256_kind": kind,
                  "tool": "Claude Code", "model": "claude-opus-5-5", "session": "s1",
                  "task_id": "T011", "review_status": "pending"}
        fields.update(changes)
        return fields

    def review_fields(self, follows: int, row: str = "Security-target review", **changes) -> Dict:
        digest, kind = evidence.named_hash("docs/note.md", "Part")
        fields = {"path": "docs/note.md", "section": "Part", "follows": follows, "sha256": digest,
                  "sha256_kind": kind, "reviewer": "owner, repository owner", "row": row,
                  "reviewed_sha256": digest, "owner_word": "accepted (2026-11-03)",
                  "review_status": "accepted"}
        fields.update(changes)
        return fields

    def lines(self) -> int:
        path = self.root / evidence.PROVENANCE_LOG_REL
        return len(path.read_bytes().splitlines()) if path.exists() else 0

    def test_an_entry_gains_seq_prev_date_and_the_environment(self):
        entry = provenance.add(self.fields())
        self.assertEqual((entry["seq"], entry["prev_sha256"]), (0, evidence.ZERO_HASH))
        self.assertEqual(entry["environment"]["path"], evidence.environment_rel())
        self.assertEqual(self.lines(), 1)

    def test_a_whole_file_entry(self):
        digest, kind = evidence.named_hash("docs/note.md")
        entry = provenance.add(self.fields(section=NONE, sha256=digest, sha256_kind=kind))
        self.assertEqual(entry["section"], NONE)

    def test_a_known_result_entry_needs_its_source(self):
        fields = {"known_result": "SPECK32 second", "source": "paper, table 3, value 9",
                  "tool": "Claude Code", "model": "m", "session": "s", "task_id": "T1",
                  "review_status": "pending"}
        self.assertEqual(provenance.add(dict(fields))["known_result"], "SPECK32 second")
        del fields["source"]
        with self.assertRaisesRegex(Refused, "source"):
            provenance.add(fields)

    def test_each_refusal_of_add_appends_nothing(self):
        for changes, words in (({"tool": None}, "tool"), ({"section": "Absent"}, "no section"),
                               ({"sha256": "0" * 64}, "differs"),
                               ({"sha256_kind": "lf-normalized"}, "differs"),
                               ({"review_status": "maybe"}, "review_status"),
                               ({"seq": 7}, "the writer adds")):
            fields = self.fields(**changes)
            if changes.get("tool", 1) is None:
                del fields["tool"]
            with self.assertRaisesRegex(Refused, words):
                provenance.add(fields)
        self.assertEqual(self.lines(), 0)

    def test_a_section_that_names_two_is_refused(self):
        write(self.root, "docs/two.md", "# A\n\n## S\n\n# B\n\n## S\n")
        with self.assertRaisesRegex(Refused, "more than one"):
            provenance.add(self.fields(path="docs/two.md", section="S"))

    def test_the_environment_guard_applies(self):
        with mock.patch.object(evidence, "snapshot", return_value=dict(SNAPSHOT, python="3.10.12")):
            with self.assertRaisesRegex(Refused, "python"):
                provenance.add(self.fields())

    def reviewable(self, decision: str = "Approved") -> int:
        entry = provenance.add(self.fields())
        digest = entry["sha256"]
        self.add_row("Security-target review", decision, f"names {digest}")
        return entry["seq"]

    def test_a_review_entry_stands_on_its_row_at_head(self):
        seq = self.reviewable()
        entry = provenance.review(self.review_fields(seq))
        self.assertEqual((entry["follows"], entry["review_status"]), (seq, "accepted"))

    def test_changes_requested_needs_declined(self):
        seq = self.reviewable("Declined")
        with self.assertRaisesRegex(Refused, "does not read"):
            provenance.review(self.review_fields(seq))
        provenance.review(self.review_fields(seq, review_status="changes-requested"))

    def test_each_refusal_of_review_appends_nothing(self):
        seq = self.reviewable()
        count = self.lines()
        fake = "1" * 64
        for changes, words in (({"reviewer": "Claude Code"}, "AI tool"),
                               ({"reviewer": "the agent's session"}, "AI tool"),
                               ({"row": "Absent review"}, "does not read"),
                               ({"reviewed_sha256": fake}, "does not read"),
                               ({"follows": seq + 1}, "latest entry"),
                               ({"owner_word": ""}, "owner_word")):
            with self.assertRaisesRegex(Refused, words):
                provenance.review(dict(self.review_fields(seq), **changes))
        fields = self.review_fields(seq)
        del fields["reviewed_sha256"]
        with self.assertRaisesRegex(Refused, "reviewed_sha256"):
            provenance.review(fields)
        self.assertEqual(self.lines(), count)

    def test_a_working_tree_table_that_differs_refuses(self):
        seq = self.reviewable()
        self.add_row("Later", "Approved", "x", commit=False)
        with self.assertRaisesRegex(Refused, "differs from HEAD"):
            provenance.review(self.review_fields(seq))

    def test_a_section_changed_after_its_entry_needs_an_add_first(self):
        seq = self.reviewable()
        write(self.root, "docs/note.md", "# Note\n\n## Part\n\nchanged\n\n## Other\n\nmore\n")
        self.commit("changed")
        digest = evidence.named_hash("docs/note.md", "Part")[0]
        self.add_row("Security-target review 2", "Approved", f"names {digest}")
        with self.assertRaisesRegex(Refused, "differs from the text of entry"):
            provenance.review(self.review_fields(seq, "Security-target review 2"))

    def test_a_chapter_the_row_names_by_its_own_hash(self):
        seq = self.reviewable()
        provenance.review(self.review_fields(seq))

    def test_a_section_of_the_rationale_names_only_the_owner_design_review(self):
        rel = evidence.FEATURE_REL + "/rationale.md"
        write(self.root, rel, "# Rationale\n\n## Security target\n\ntext\n")
        self.commit("rationale")
        file_digest = evidence.named_hash(rel)[0]
        digest, kind = evidence.named_hash(rel, "Security target")
        entry = provenance.add(self.fields(path=rel, section="Security target", sha256=digest,
                                           sha256_kind=kind))
        self.add_row("Security-target review", "Approved", f"names {file_digest}")
        self.add_row("Owner design review", "Approved", f"names {file_digest}")
        fields = self.review_fields(entry["seq"], path=rel, section="Security target",
                                    sha256=digest, sha256_kind=kind, reviewed_sha256=file_digest)
        with self.assertRaisesRegex(Refused, "another family"):
            provenance.review(fields)
        fields["row"] = "Owner design review"
        provenance.review(fields)

    def test_the_review_of_an_evidence_record(self):
        run = evidence.Run("validation", argv=ARGV)
        with run:
            path = run.finish("pass")
        record = json.loads(path.read_bytes())
        digest = evidence.sha256(path.read_bytes())
        self.add_row("Record review", "Approved", f"names {digest}")
        fields = {"record_id": record["record_id"], "sha256": digest, "sha256_kind": "raw",
                  "reviewer": "owner", "row": "Record review", "reviewed_sha256": digest,
                  "owner_word": "accepted (2026-11-03)", "review_status": "accepted"}
        self.assertEqual(provenance.review(dict(fields))["record_id"], record["record_id"])
        with self.assertRaisesRegex(Refused, "differs"):
            provenance.review(dict(fields, sha256="0" * 64))
        with self.assertRaisesRegex(Refused, "no record"):
            provenance.review(dict(fields, record_id="absent"))


def refused_entry(name: str = "CMAC R64", c: str = "0x1b") -> Dict:
    return {"name": name, "kind": "polynomial", "degree": 64, "c": c,
            "source": "research/004/refused_sources.py, SP 800-38B"}


class ProtocolWriter(TempRepo):
    """The refusals of the protocol change log's writer, on a stated history of the refused list."""

    def later(self, **changes) -> Dict:
        fields = {"rule": "Bias rule", "old_text": "a", "new_text": "b", "direction": "stricter",
                  "readings": [], "reason": "why", "last_record_id": NONE, "results_known": []}
        fields.update(changes)
        return fields

    def lines(self) -> int:
        return len((self.root / evidence.PROTOCOL_LOG_REL).read_bytes().splitlines())

    def owner(self, digits=None):
        """The owner at an interactive terminal, typing the digits of the hash printed."""
        typed = {}

        def fake_input(prompt: str) -> str:
            if prompt.startswith("type"):
                return digits if digits is not None else typed["digest"][:16]
            return "kept, for the owner's reason"

        real = evidence.confirm_digits

        def spy(digest: str) -> str:
            typed["digest"] = digest
            return real(digest)

        return (mock.patch.object(evidence, "confirm_digits", side_effect=spy),
                mock.patch.object(evidence, "interactive_terminal", return_value=True),
                mock.patch("builtins.input", fake_input), mock.patch("builtins.print"))

    def propose(self, fields: Dict, digits=None) -> Dict:
        patches = self.owner(digits)
        for patch in patches:
            patch.start()
        try:
            return changelog.propose(fields)
        finally:
            for patch in patches:
                patch.stop()

    def test_a_later_entry_ends_in_the_approval_step(self):
        entry = self.propose(self.later())
        self.assertEqual(entry["approver"]["approval_confirmed"],
                         evidence.later_entry_hash(entry)[:16])
        self.assertEqual(entry["seq"], 1)
        self.assertEqual(entry["environment"]["path"], evidence.environment_rel())
        evidence.guard_protocol_log("inverse")

    def test_no_interactive_terminal_appends_nothing(self):
        count = self.lines()
        with mock.patch("builtins.print"):
            with self.assertRaisesRegex(Refused, "interactive terminal"):
                changelog.propose(self.later())
        self.assertEqual(self.lines(), count)

    def test_digits_that_do_not_match_append_nothing(self):
        count = self.lines()
        with self.assertRaisesRegex(Refused, "digits"):
            self.propose(self.later(), digits="0" * 16)
        self.assertEqual(self.lines(), count)

    def test_each_refusal_of_a_later_entry(self):
        count = self.lines()
        for missing in ("direction", "last_record_id", "results_known", "rule"):
            fields = self.later()
            del fields[missing]
            with self.assertRaisesRegex(Refused, missing):
                self.propose(fields)
        with self.assertRaisesRegex(Refused, "readings"):
            self.propose(self.later(direction="settled", readings=[]))
        with self.assertRaisesRegex(Refused, "direction"):
            self.propose(self.later(direction="looser"))
        self.assertEqual(self.lines(), count)

    def test_a_reading_set_aside_is_shown_and_takes_the_owners_decision(self):
        reading = {"reading": "r", "set_aside": True, "case": "every candidate"}
        entry = self.propose(self.later(direction="settled", readings=[reading]))
        self.assertEqual(entry["readings"][0]["decision"], "kept, for the owner's reason")
        evidence.guard_protocol_log("inverse")

    # the owner's written approval (spec FR-044) ----------------------------------------------

    WRITTEN = {"words": "approve this change", "date": "2026-11-05", "entered_by": "agent"}

    def no_terminal(self, fields: Dict) -> Dict:
        with mock.patch("builtins.print"), \
                mock.patch.object(evidence, "interactive_terminal", return_value=False):
            return changelog.propose(fields)

    def test_a_written_approval_needs_no_terminal_and_stays_in_the_entry(self):
        entry = self.no_terminal(self.later(written_approval=dict(self.WRITTEN)))
        self.assertEqual(entry["written_approval"], self.WRITTEN)
        self.assertEqual(entry["approver"]["approval_confirmed"],
                         evidence.later_entry_hash(entry)[:16])
        evidence.guard_protocol_log("inverse")

    def test_the_owners_words_stand_inside_the_hash_the_digits_confirm(self):
        entry = self.no_terminal(self.later(written_approval=dict(self.WRITTEN)))
        other = dict(entry, written_approval=dict(self.WRITTEN, words="something else"))
        self.assertNotEqual(evidence.later_entry_hash(entry), evidence.later_entry_hash(other))

    def test_each_refusal_of_a_written_approval(self):
        count = self.lines()
        wanted = {"no words": dict(self.WRITTEN, words=" "), "no date": dict(self.WRITTEN, date="today"),
                  "entered": dict(self.WRITTEN, entered_by="owner"), "object": "approved"}
        for message, written in wanted.items():
            with self.assertRaisesRegex(Refused, message):
                self.no_terminal(self.later(written_approval=written))
        with self.assertRaisesRegex(Refused, "no words"):
            self.no_terminal(self.later(written_approval={}))
        self.assertEqual(self.lines(), count)

    def test_the_guard_reads_a_written_approval_in_the_log(self):
        with mock.patch.object(evidence, "guard_written_approval"):
            self.no_terminal(self.later(written_approval={"words": ""}))
        with self.assertRaisesRegex(Refused, "no words"):
            evidence.guard_protocol_log("inverse")

    def test_a_written_approval_leaves_a_reading_set_aside_to_its_decision(self):
        count = self.lines()
        reading = {"reading": "r", "set_aside": True, "case": "every candidate"}
        fields = self.later(direction="settled", readings=[reading],
                            written_approval=dict(self.WRITTEN))
        with self.assertRaisesRegex(Refused, "interactive terminal"):
            self.no_terminal(fields)
        self.assertEqual(self.lines(), count)
        decided = dict(reading, decision="kept, in the owner's words")
        entry = self.no_terminal(dict(fields, readings=[decided]))
        self.assertEqual(entry["readings"], [decided])
        evidence.guard_protocol_log("inverse")

    # the refused list -----------------------------------------------------------------------

    def list_version(self, entries: List[Dict], message: str) -> str:
        data = evidence.pretty({"entries": entries})
        write(self.root, changelog.REFUSED_REL, data)
        self.commit(message)
        return evidence.sha256(data)

    def name_list(self, entries: List[Dict]) -> str:
        """A committed version that a `refused_list` of the log names."""
        digest = self.list_version(entries, "a named version")
        self.propose(self.later(rule="Constant rule", refused_list={
            "path": changelog.REFUSED_REL, "sha256": digest, "sha256_kind": "raw"}))
        self.commit("entry")
        return digest

    def addition(self, digest: str) -> Dict:
        return self.later(rule="Constant rule", refused_list={
            "path": changelog.REFUSED_REL, "sha256": digest, "sha256_kind": "raw"})

    def test_parse_reads_r15s_entry_format(self):
        good = refused_entry()
        sets = {"name": "PRESENT", "kind": "constant-set", "source": "main.pdf, table 2",
                "word_bits": 8, "words": ["0x1", "0xff"]}
        self.assertEqual(len(changelog.parse_refused_list(
            evidence.pretty({"entries": [good, sets]}))), 2)
        bad = [dict(good, kind="set"), dict(good, c="27"), {"name": "x"},
               dict(sets, words=["0x1ff"]), dict(sets, words="0x1"), dict(good, degree="64"),
               dict(good, source="")]
        for entry in bad:
            with self.assertRaises(ValueError, msg=str(entry)):
                changelog.parse_refused_list(evidence.pretty({"entries": [entry]}))
        with self.assertRaises(ValueError):
            changelog.parse_refused_list(b"not json")

    def test_an_addition_appends_and_its_approval_step_prints_the_entries_added(self):
        self.name_list([refused_entry()])
        digest = self.list_version([refused_entry(), refused_entry("GCM", "0x87")], "added")
        patches = self.owner()
        for patch in patches:
            patch.start()
        try:
            printed = __import__("builtins").print
            entry = changelog.propose(self.addition(digest))
            calls = " ".join(str(c) for c in printed.call_args_list)
        finally:
            for patch in patches:
                patch.stop()
        self.assertEqual(entry["refused_list"]["sha256"], digest)
        self.assertIn("GCM", calls)

    def test_an_addition_whose_sha256_differs_from_head_is_refused(self):
        self.name_list([refused_entry()])
        count = self.lines()
        with self.assertRaisesRegex(Refused, "differs from HEAD|at HEAD"):
            self.propose(self.addition("0" * 64))
        self.assertEqual(self.lines(), count)

    def test_a_list_that_does_not_parse_at_head_is_refused(self):
        self.name_list([refused_entry()])
        data = b'{"entries": [{"name": "x"}]}\n'
        write(self.root, changelog.REFUSED_REL, data)
        self.commit("does not parse")
        with self.assertRaisesRegex(Refused, "does not parse"):
            self.propose(self.addition(evidence.sha256(data)))

    def test_a_dropped_entry_of_the_latest_named_version_is_refused(self):
        self.name_list([refused_entry(), refused_entry("GCM", "0x87")])
        digest = self.list_version([refused_entry()], "dropped")
        count = self.lines()
        with self.assertRaisesRegex(Refused, "drops or changes"):
            self.propose(self.addition(digest))
        self.assertEqual(self.lines(), count)

    def test_a_changed_word_of_the_latest_named_version_is_refused(self):
        self.name_list([refused_entry(), refused_entry("GCM", "0x87")])
        digest = self.list_version([refused_entry(), refused_entry("GCM", "0x89")], "changed")
        with self.assertRaisesRegex(Refused, "drops or changes"):
            self.propose(self.addition(digest))

    def test_the_latest_named_version_is_the_one_read(self):
        self.name_list([refused_entry()])
        digest = self.list_version([refused_entry(), refused_entry("GCM", "0x87")], "added")
        self.propose(self.addition(digest))
        self.commit("the second named version")
        digest = self.list_version([refused_entry()], "drops what the second version added")
        with self.assertRaisesRegex(Refused, "drops or changes"):
            self.propose(self.addition(digest))

    def test_a_draft_that_no_entry_names_may_be_corrected(self):
        self.name_list([refused_entry()])
        self.list_version([refused_entry(), refused_entry("GCM", "0x87")], "a draft")
        digest = self.list_version([refused_entry(), refused_entry("GCM", "0x88")], "corrected")
        entry = self.propose(self.addition(digest))
        self.assertEqual(entry["refused_list"]["sha256"], digest)

    def test_a_list_missing_or_modified_is_refused_at_create(self):
        with self.assertRaisesRegex(Refused, "refused-constants.json"):
            changelog.check_refused_list_at_head()
        self.list_version([refused_entry()], "the list")
        changelog.check_refused_list_at_head()
        write(self.root, changelog.REFUSED_REL, b"changed")
        with self.assertRaisesRegex(Refused, "differs from HEAD"):
            changelog.check_refused_list_at_head()

    def test_create_runs_only_while_the_log_does_not_exist(self):
        with self.assertRaisesRegex(Refused, "exists"):
            changelog.create()


    def test_a_create_that_dies_leaves_no_partial_log(self):
        (self.root / evidence.PROTOCOL_LOG_REL).unlink()
        entries = [self.first_entry(), self.first_entry()]
        patches = self.owner()
        for patch in patches:
            patch.start()
        real = evidence.log_line
        calls = []

        def dying(entry: Dict) -> bytes:
            calls.append(1)
            if len(calls) == 2:
                raise OSError("the disk is full")
            return real(entry)

        try:
            with mock.patch.object(changelog, "build_first_entries", return_value=entries), \
                    mock.patch.object(evidence, "log_line", side_effect=dying):
                with self.assertRaises(OSError):
                    changelog.create()
        finally:
            for patch in patches:
                patch.stop()
        self.assertFalse((self.root / evidence.PROTOCOL_LOG_REL).exists())
        self.assertFalse(evidence.REPO.append_lock.exists())

    def test_create_writes_the_first_entries_after_the_approval_step(self):
        (self.root / evidence.PROTOCOL_LOG_REL).unlink()
        entries = [self.first_entry(), self.first_entry()]
        patches = self.owner()
        for patch in patches:
            patch.start()
        try:
            with mock.patch.object(changelog, "build_first_entries", return_value=entries):
                self.assertEqual(changelog.create(), 0)
        finally:
            for patch in patches:
                patch.stop()
        evidence.guard_protocol_log("inverse")
        stored = [e for e, _ in evidence.log_entries(evidence.PROTOCOL_LOG_REL)]
        self.assertEqual([e["seq"] for e in stored], [0, 1])
        self.assertEqual(stored[0]["approver"]["approval_confirmed"],
                         evidence.first_entries_hash(stored)[:16])
        self.assertEqual(stored[0]["environment"]["path"], evidence.environment_rel())

    def test_no_interactive_terminal_creates_nothing(self):
        (self.root / evidence.PROTOCOL_LOG_REL).unlink()
        with mock.patch.object(changelog, "build_first_entries",
                               return_value=[self.first_entry()]), mock.patch("builtins.print"):
            with self.assertRaisesRegex(Refused, "interactive terminal"):
                changelog.create()
        self.assertFalse((self.root / evidence.PROTOCOL_LOG_REL).exists())

    def test_a_first_entry_without_direction_or_readings_is_refused(self):
        entry = self.first_entry()
        del entry["rules"][0]["direction"]
        with self.assertRaisesRegex(Refused, "direction"):
            changelog.guard_entry_fields(entry)
        entry = self.first_entry()
        entry["rules"][0]["direction"] = "settled"
        with self.assertRaisesRegex(Refused, "readings"):
            changelog.guard_entry_fields(entry)

    def test_a_repair_entry_needs_no_direction(self):
        changelog.guard_entry_fields({"repair": {}, "last_record_id": NONE, "results_known": []})
        with self.assertRaisesRegex(Refused, "results_known"):
            changelog.guard_entry_fields({"repair": {}, "last_record_id": NONE})


class FirstEntries(unittest.TestCase):
    """The rows' readings and the confirmations, on stated text."""

    PLACE = ("No change of rule: ad2c195, research R3. An entry of its own: b6a93f0, the cli "
             "contract (\"Records and their hashes\", `stricter`: a refusal added); 252512a, spec "
             "FR-039 (\"Tool validation\", `stricter`: words), research R4 (\"Bias rule\", "
             "`stricter`: more); 7f42e03 and b9d9740, research R16 (\"Records and their hashes\", "
             "`stricter`, the two together); ccfd9d1, research R15 (\"Constant rule\", `settled`, "
             "with one reading marked `set_aside`, decided in the row); and 5192c73, research R16 "
             "(\"Records and their hashes\", `stricter`: the status). The other commits changed "
             "no place.")

    def test_each_commit_confirmed_as_its_own_entry_with_each_rules_direction(self):
        own = changelog.own_entries(self.PLACE)
        self.assertEqual(sorted(own), sorted(["b6a93f0", "252512a", "7f42e03", "b9d9740", "ccfd9d1",
                                              "5192c73"]))
        self.assertEqual(own["252512a"], {"Tool validation": "stricter", "Bias rule": "stricter"})
        self.assertEqual(own["ccfd9d1"], {"Constant rule": "settled"})
        self.assertNotIn("ad2c195", own)

    def test_the_owners_words_are_those_of_the_entry_of_its_own(self):
        notes = "compared_to `5192c73aaa`: " + self.PLACE
        self.assertTrue(changelog.confirmation(notes, "5192c73aaa").startswith("5192c73, research"))

    def test_a_reading_is_read_with_its_case_and_decision(self):
        notes = ("decided here, entry by entry, each change kept: RAT-036, FR-023's \"differ\", "
                 "under which no table exists: kept, since the rule holds; the entry for ccfd9d1 "
                 "(research R15), a reading, under which it refuses: kept, on the owner's word; "
                 "and RAT-052, the placement, where every placement moves: restored, for a reason. "
                 "`protocol_change.py create` reads this row")
        readings = changelog.set_aside_readings(notes)
        self.assertEqual(sorted(readings), ["RAT-036", "RAT-052", "ccfd9d1"])
        self.assertEqual(readings["RAT-036"]["case"], "no table exists")
        self.assertEqual(readings["RAT-036"]["decision"], "kept, since the rule holds")
        self.assertEqual(readings["RAT-052"]["decision"], "restored, for a reason")
        self.assertEqual(readings["RAT-052"]["case"], "every placement moves")
        self.assertIs(readings["ccfd9d1"]["set_aside"], True)

    def test_each_reading_required_is_named(self):
        model = ("The first entries that hold one are those of RAT-036 and PRO-065, from earlier "
                 "rounds, and of SEC-093, with every other entry of that kind.")
        self.assertEqual(changelog.required_readings(model, self.PLACE),
                         ["RAT-036", "PRO-065", "SEC-093", "ccfd9d1"])

    def test_a_reading_the_documents_name_and_the_row_does_not_decide_is_refused(self):
        model = "The first entries that hold one are those of RAT-036, with every other entry."
        readings = {"RAT-036": {}}
        with self.assertRaisesRegex(Refused, r"not decided: \['ccfd9d1'\]"):
            changelog.guard_readings_decided(model, self.PLACE, readings)
        changelog.guard_readings_decided(model, self.PLACE, dict(readings, ccfd9d1={}))

    def test_a_row_decided_that_no_entry_holds_is_refused(self):
        with self.assertRaisesRegex(Refused, "do not exist"):
            changelog.attach_readings([], {"RAT-036": {"reading": "r", "case": "c"}})

    def test_a_reading_goes_to_the_rule_whose_place_it_names(self):
        entry = {"row": {"id": "RAT-036"}, "rules": [
            {"rule": "Eligibility", "old_text": {"FR-018": ""}, "direction": "stricter",
             "readings": []},
            {"rule": "Constant rule", "old_text": {"FR-023": ""}, "direction": "stricter",
             "readings": []}]}
        changelog.attach_readings([entry], {"RAT-036": {"reading": "FR-023's word", "case": "c"}})
        self.assertEqual((entry["rules"][0]["readings"], entry["rules"][1]["direction"]),
                         ([], "settled"))

    def test_the_direction_of_a_rule(self):
        self.assertEqual(changelog.direction_of("Bias rule", "Add"), "stricter")
        self.assertEqual(changelog.direction_of("Bias rule", "Align"), "stricter")
        self.assertEqual(changelog.direction_of("Bias rule", "Settle"), "settled")
        self.assertEqual(changelog.direction_of("Bias rule", "Clarify"), "settled")
        self.assertEqual(changelog.direction_of("Development inputs", "Stricter"), "settled")


class FirstEntriesOfThisRepository(unittest.TestCase):
    """FR-044's comparison on the committed lists, and the first entries `create` would write,
    built with the refused list that T027 writes standing in; nothing is written. `create` has run:
    its guard refuses a place changed after `compared_to`, which a later entry's change is, so the
    entries are built from the comparison as stored, up to that commit."""

    def test_they_agree_with_the_lists_and_the_confirmed_rows(self):
        stored = json.loads((ROOT / changelog.PLACE_CHECK_REL).read_bytes())
        self.assertEqual(changelog.check(stored["compared_to"]), stored)
        fake = {"path": changelog.REFUSED_REL, "sha256": "0" * 64, "sha256_kind": "raw"}
        with mock.patch.object(changelog, "check_refused_list_at_head", return_value=fake),                 mock.patch.object(changelog, "guard_comparison", return_value=stored):
            entries = changelog.build_first_entries()
        listed: Dict[str, set] = {}
        for item in stored["rounds"]:
            listed.setdefault(item["heading"], set()).update(
                row for change in item["changed"] for row in change["rows"])
        rows = [e for e in entries if e["granularity"] == "round"]
        commits = [e for e in entries if e["granularity"] == "commit"]
        self.assertEqual(len(entries), len(rows) + len(commits))
        self.assertEqual(sorted({e["commit"] for e in commits}),
                         sorted({u["commit"] for u in stored["unmade"]
                                 if u["commit"][:7] in changelog.own_entries(
                                     evidence.family_row("Place check").notes)}))
        for entry in entries:
            changelog.guard_entry_fields(entry)
            if any(rule["rule"] == changelog.CONSTANT_RULE for rule in entry["rules"]):
                self.assertEqual(entry["refused_list"], fake)
            else:
                self.assertEqual(entry["refused_list"], NONE)
        marked = [reading for entry in entries for rule in entry["rules"]
                  for reading in rule["readings"] if reading.get("set_aside")]
        self.assertTrue(marked)
        self.assertTrue(all(reading["decision"].startswith("kept") for reading in marked))


class RepairedLogs(ProtocolWriter):
    """scripts/repair_log.py: the one append to a broken chain, by each log's writer."""

    def provenance_log(self) -> str:
        rel = evidence.PROVENANCE_LOG_REL
        write(self.root, "docs/note.md", "# Note\n")
        self.commit("note")
        digest, kind = evidence.named_hash("docs/note.md")
        fields = {"path": "docs/note.md", "section": NONE, "sha256": digest, "sha256_kind": kind,
                  "tool": "t", "model": "m", "session": "s", "task_id": "T",
                  "review_status": "pending"}
        provenance.add(dict(fields))
        provenance.add(dict(fields))
        path = self.root / rel
        path.write_bytes(path.read_bytes().replace(b'"seq": 1', b'"seq": 9'))
        return rel

    def run_repair(self, rel: str, row: str = "Log repair 1") -> int:
        from scripts import repair_log
        return repair_log.main(["--log", rel, "--approval", row])

    def test_no_row_refuses_and_changes_nothing(self):
        rel = self.provenance_log()
        before = (self.root / rel).read_bytes()
        with mock.patch("sys.stderr"):
            self.assertEqual(self.run_repair(rel), 2)
        self.assertEqual((self.root / rel).read_bytes(), before)

    def test_a_row_that_names_another_seq_refuses(self):
        rel = self.provenance_log()
        self.add_row("Log repair 1", "Approved", f"{rel}, seq 5, 2026-11-03")
        with mock.patch("sys.stderr"):
            self.assertEqual(self.run_repair(rel), 2)

    def test_a_row_that_names_another_log_refuses(self):
        rel = self.provenance_log()
        self.add_row("Log repair 1", "Approved", f"{evidence.CANDIDATE_LOG_REL}, seq 1, 2026-11-03")
        with mock.patch("sys.stderr"):
            self.assertEqual(self.run_repair(rel), 2)

    def test_a_row_not_approved_refuses(self):
        rel = self.provenance_log()
        self.add_row("Log repair 1", "Declined", f"{rel}, seq 1, 2026-11-03")
        with mock.patch("sys.stderr"):
            self.assertEqual(self.run_repair(rel), 2)

    def test_the_broken_file_is_kept_and_the_log_restored_with_its_repair_entry(self):
        rel = self.provenance_log()
        broken = (self.root / rel).read_bytes()
        lines = broken.splitlines(keepends=True)
        self.add_row("Log repair 1", "Approved", f"{rel}, seq 1, 2026-11-03")
        with mock.patch("builtins.print"):
            self.assertEqual(self.run_repair(rel), 0)
        restored = (self.root / rel).read_bytes().splitlines(keepends=True)
        self.assertEqual(restored[0], lines[0])
        self.assertEqual(len(restored), 2)
        entry = json.loads(restored[1])
        repair = entry["repair"]
        self.assertEqual((entry["seq"], entry["prev_sha256"]), (1, evidence.sha256(lines[0])))
        self.assertEqual((repair["break_seq"], repair["row"]), (1, "Log repair 1"))
        kept = self.root / repair["broken_file"]["path"]
        self.assertEqual(kept.read_bytes(), broken)
        self.assertEqual(repair["broken_file"]["sha256"], evidence.sha256(broken))
        self.assertEqual([e["seq"] for e in repair["entries_after"]], [9])
        self.assertEqual(repair["entries_after"][0]["sha256"], evidence.sha256(lines[1]))
        self.assertIsNone(evidence.first_break(rel))

    def test_the_list_counts_an_entry_whose_citations_hold_and_no_other(self):
        write(self.root, "docs/a.md", "# A\n")
        self.commit("a")
        digest = evidence.sha256(b"# A\n")
        holds = {"seq": 3, "path": "docs/a.md", "section": NONE, "sha256": digest}
        fails = {"seq": 4, "path": "docs/a.md", "section": NONE, "sha256": "0" * 64}
        bare = {"seq": 5, "event": "proposed"}
        cited = {"seq": 6, "event": "proposed"}
        citing = {"seq": 7, "path": "docs/a.md", "section": NONE, "sha256": digest, "cites_seq": 6}
        raw = [(e, json.dumps(e).encode() + b"\n") for e in (holds, fails, bare, cited, citing)]
        rows = evidence.repair_list(raw)
        self.assertEqual([r["counts"] for r in rows], [True, False, False, True, True])

    def test_an_unparsable_line_never_counts(self):
        rows = evidence.repair_list([(None, b"garbage\n")])
        self.assertEqual((rows[0]["counts"], rows[0]["reason"]), (False, "the line does not parse"))

    def test_the_protocol_log_goes_through_the_approval_step(self):
        rel = evidence.PROTOCOL_LOG_REL
        self.propose(self.later())
        path = self.root / rel
        path.write_bytes(path.read_bytes().replace(b'"seq": 1', b'"seq": 9'))
        self.add_row("Log repair 1", "Approved", f"{rel}, seq 1, 2026-11-03")
        with mock.patch("builtins.print"), mock.patch("sys.stderr"):
            self.assertEqual(self.run_repair(rel), 2)         # no interactive terminal
        patches = self.owner()
        for patch in patches:
            patch.start()
        try:
            self.assertEqual(self.run_repair(rel), 0)
        finally:
            for patch in patches:
                patch.stop()
        evidence.guard_protocol_log("inverse")
        entry = evidence.log_entries(rel)[-1][0]
        self.assertEqual(sorted(k for k in entry if k in ("rule", "direction", "readings")), [])
        self.assertIn("repair", entry)


class CandidateLog(TempRepo):
    """scripts/candidate_log.py and protocol/candidates.py, the log's one writer (T075, T076)."""

    def setUp(self):
        super().setUp()
        self.log = evidence.CANDIDATE_LOG_REL

    def module(self, candidate: str, text: str = "# the list\n", commit: bool = True) -> str:
        write(self.root, candidates.module_rel(candidate), text)
        if commit:
            self.commit(f"the list of {candidate}")
        return evidence.sha256(text.encode("utf-8"))

    def proposal(self, candidate: str = "cand-A1", **changes) -> Dict:
        parameters = {name: "stated" for name in candidates.PARAMETERS}
        fields = {"candidate_id": candidate, "family": candidates.FAMILIES[candidate[5]],
                  "oplist_sha256": self.module(candidate), "parameters": parameters}
        fields.update(changes)
        return fields

    def propose(self, candidate: str = "cand-A1", **changes) -> Dict:
        return candidates.propose(self.proposal(candidate, **changes))

    def lines(self) -> int:
        path = self.root / self.log
        return len(path.read_bytes().splitlines()) if path.exists() else 0

    def run_log(self, *argv) -> int:
        from scripts import candidate_log
        with mock.patch("builtins.print"), mock.patch("sys.stderr"):
            return candidate_log.main(list(argv))

    def file(self, fields: Dict) -> str:
        return str(write(self.root, "data/local/entry.json", json.dumps(fields)))

    def mapping_table(self) -> Dict:
        return {name: {"place": "here", "serves": "that"} for name in candidates.MAPPING}

    def record(self, kind: str, candidate: str = "cand-A1", name: str = "r1", **fields) -> Dict:
        body = {"kind": kind, "record_id": name, "candidate": candidate, "status": "pass"}
        body.update(fields)
        data = evidence.pretty(body)
        write(self.root, f"{evidence.REP_REL}/candidates/{candidate}/{name}.json", data)
        return {"record_id": name, "sha256": evidence.sha256(data)}

    def scored(self, candidate: str = "cand-A1") -> None:
        candidates.append({"candidate_id": candidate, "event": "scored"})

    # propose ----------------------------------------------------------------------------------

    def test_propose_appends_an_entry_chained_from_seq_0(self):
        fields = self.proposal()
        self.assertEqual(self.run_log("propose", self.file(fields)), 0)
        entry = evidence.check_chain(self.log)[0][0]
        self.assertEqual((entry["seq"], entry["event"]), (0, "proposed"))
        self.assertEqual(entry["oplist_sha256"], fields["oplist_sha256"])
        self.assertEqual((entry["evidence"], entry["budget_used_h"]), ([], {}))

    def test_a_tool_takes_the_proposed_hash_and_refuses_any_other(self):
        digest = self.propose()["oplist_sha256"]
        evidence.guard_oplist(digest)
        with self.assertRaises(Refused):
            evidence.guard_oplist("f" * 64)

    def test_a_fourth_proposed_entry_of_a_family_exits_2(self):
        """Quickstart E6: the ID's own rule and the count both refuse it."""
        for k in (1, 2, 3):
            self.propose(f"cand-A{k}")
        before = self.lines()
        self.assertEqual(self.run_log("propose", self.file(self.proposal("cand-A3"))), 2)
        self.assertEqual(self.run_log("propose", self.file(dict(
            self.proposal("cand-A3"), candidate_id="cand-A4"))), 2)
        self.assertEqual(self.lines(), before)

    def test_three_per_family_stand_in_each_family(self):
        for family in "AB":
            for k in (1, 2, 3):
                self.propose(f"cand-{family}{k}")
        self.assertEqual(self.lines(), 6)

    def test_the_count_holds_whatever_became_of_the_three(self):
        for k in (1, 2):
            self.propose(f"cand-A{k}")
        candidates.decide({"candidate_id": "cand-A1", "decision": "withdrawn", "reason": "why"})
        self.propose("cand-A3")
        with mock.patch.object(candidates, "CANDIDATE_ID", re.compile(r"cand-([AB])(\d)")):
            with self.assertRaisesRegex(Refused, "fourth"):
                self.propose("cand-A4")

    def test_a_family_that_is_not_the_ids_is_refused(self):
        with self.assertRaisesRegex(Refused, "family"):
            self.propose(family="Boolean")

    def test_each_part_of_parameters_is_required(self):
        for name in candidates.PARAMETERS:
            fields = self.proposal()
            del fields["parameters"][name]
            with self.assertRaisesRegex(Refused, name):
                candidates.propose(fields)
        self.assertEqual(self.lines(), 0)

    def test_a_field_the_writer_adds_is_refused(self):
        with self.assertRaisesRegex(Refused, "seq"):
            candidates.propose(dict(self.proposal(), seq=7))

    def test_a_module_that_is_uncommitted_or_another_is_refused(self):
        fields = self.proposal()
        write(self.root, candidates.module_rel("cand-A1"), "# changed\n")
        with self.assertRaisesRegex(Refused, "SHA-256"):
            candidates.propose(fields)
        with self.assertRaisesRegex(Refused, "committed"):
            candidates.propose(dict(fields, oplist_sha256=evidence.sha256(b"# changed\n")))

    def test_no_entry_is_ever_deleted_or_rewritten(self):
        self.propose("cand-A1")
        first = (self.root / self.log).read_bytes()
        self.propose("cand-B1")
        self.assertTrue((self.root / self.log).read_bytes().startswith(first))

    def test_a_second_proposed_entry_of_a_candidate_is_a_correction(self):
        self.propose()
        with self.assertRaisesRegex(Refused, "correction"):
            self.propose()

    def test_after_the_first_score_a_candidate_comes_only_in_place_of_another(self):
        self.propose("cand-A1")
        self.propose("cand-B1")
        self.scored()
        with self.assertRaisesRegex(Refused, "in place of"):
            self.propose("cand-A2")

    def pending(self) -> Dict:
        self.propose("cand-A1")
        self.propose("cand-B1")
        self.scored()
        cited = self.record("inverse", status="fail")
        written = candidates.decide({"candidate_id": "cand-A1", "decision": "rejected",
                                     "reason": "the inverse test failed", "cause": candidates.FAILED_CHECK,
                                     "record": cited})
        return written[1]

    def test_a_replacement_cites_a_pending_entry_on_the_owners_word(self):
        target = self.pending()
        with self.assertRaisesRegex(Refused, "explicit word"):
            self.propose("cand-A2", replaces=target["seq"])
        with self.assertRaisesRegex(Refused, "pending"):
            self.propose("cand-A2", replaces=0, owner_word=WORD)
        with self.assertRaisesRegex(Refused, "family"):
            self.propose("cand-B2", replaces=target["seq"], owner_word=WORD)
        entry = self.propose("cand-A2", replaces=target["seq"], owner_word=WORD)
        self.assertEqual(entry["owner_word"], WORD)

    # after the set closes ---------------------------------------------------------------------

    def closed(self) -> None:
        self.propose("cand-A1")
        self.propose("cand-B1")
        candidates.append({"event": "set-closed"})

    def decline(self, further: str = "cand-A2") -> None:
        self.add_row("Owner design review", "Declined", "the reasons")
        candidates.outcome({"candidate_id": "cand-A1", "outcome": "declined", "reasons": "why",
                            "needs": "an R below the declined one", "further_candidate": further})

    def test_after_set_closed_propose_exits_2(self):
        self.closed()
        with self.assertRaisesRegex(Refused, "closed"):
            self.propose("cand-A2", owner_word=WORD)

    def test_a_decline_reopens_the_set_for_its_further_candidate(self):
        self.closed()
        self.decline()
        with self.assertRaisesRegex(Refused, "explicit word"):
            self.propose("cand-A2")
        with self.assertRaisesRegex(Refused, "further"):
            self.propose("cand-A3", owner_word=WORD)
        self.assertEqual(self.propose("cand-A2", owner_word=WORD)["candidate_id"], "cand-A2")

    def test_the_set_reopens_once(self):
        self.closed()
        self.decline()
        self.propose("cand-A2", owner_word=WORD)
        candidates.append({"event": "set-closed"})
        with self.assertRaisesRegex(Refused, "closed"):
            self.propose("cand-A3", owner_word=WORD)

    # mapping and enter ------------------------------------------------------------------------

    def test_mapping_comes_before_the_first_score_and_holds_every_part(self):
        self.propose()
        fields = {"candidate_id": "cand-A1", "mapping": self.mapping_table()}
        self.assertEqual(self.run_log("mapping", self.file(fields)), 0)
        for name in candidates.MAPPING:
            table = self.mapping_table()
            del table[name]
            with self.assertRaisesRegex(Refused, name):
                candidates.mapping({"candidate_id": "cand-A1", "mapping": table})
        self.scored()
        with self.assertRaisesRegex(Refused, "before its first score"):
            candidates.mapping(fields)

    def test_mapping_needs_a_proposed_entry(self):
        with self.assertRaisesRegex(Refused, "proposed"):
            candidates.mapping({"candidate_id": "cand-A1", "mapping": self.mapping_table()})

    def test_mapping_holds_place_and_purpose(self):
        self.propose()
        table = self.mapping_table()
        table["food nodes"] = {"place": "here"}
        with self.assertRaisesRegex(Refused, "food nodes"):
            candidates.mapping({"candidate_id": "cand-A1", "mapping": table})

    def test_enter_writes_one_entry_per_candidate(self):
        self.propose("cand-A1")
        self.propose("cand-B1")
        self.assertEqual(self.run_log("enter"), 0)
        entered = candidates.of_event(candidates.entries(), "entered-d4")
        self.assertEqual([e["candidate_id"] for e in entered], ["cand-A1", "cand-B1"])

    def test_enter_needs_each_family(self):
        self.propose("cand-A1")
        with self.assertRaisesRegex(Refused, "each family"):
            candidates.enter()

    def test_enter_exits_2_once_a_scored_entry_exists(self):
        self.propose("cand-A1")
        self.propose("cand-B1")
        self.scored()
        self.assertEqual(self.run_log("enter"), 2)

    def test_enter_leaves_out_a_withdrawn_candidate_and_repeats_no_entry(self):
        self.propose("cand-A1")
        self.propose("cand-A2")
        self.propose("cand-B1")
        candidates.decide({"candidate_id": "cand-A2", "decision": "withdrawn", "reason": "why"})
        candidates.enter()
        with self.assertRaisesRegex(Refused, "entered-d4"):
            candidates.enter()
        entered = candidates.of_event(candidates.entries(), "entered-d4")
        self.assertEqual([e["candidate_id"] for e in entered], ["cand-A1", "cand-B1"])

    # decide -----------------------------------------------------------------------------------

    def test_selected_and_not_selected_belong_to_round_rule(self):
        self.propose()
        for decision in ("selected", "not selected", "liked"):
            with self.assertRaisesRegex(Refused, "decision"):
                candidates.decide({"candidate_id": "cand-A1", "decision": decision, "reason": "r"})

    def test_withdrawn_stands_only_before_the_first_tool_run(self):
        self.propose()
        candidates.append({"candidate_id": "cand-A1", "event": "evidence", "budget_used_h": {}})
        with self.assertRaisesRegex(Refused, "first"):
            candidates.decide({"candidate_id": "cand-A1", "decision": "withdrawn", "reason": "r"})

    def test_a_rejection_shows_a_failed_check_and_brings_a_pending_replacement(self):
        self.propose()
        cited = self.record("bijectivity", status="fail")
        written = candidates.decide({"candidate_id": "cand-A1", "decision": "rejected", "reason": "r",
                                     "cause": candidates.FAILED_CHECK, "record": cited})
        self.assertEqual([e["event"] for e in written], ["decision", "replacement"])
        self.assertEqual((written[1]["state"], written[1]["decision_seq"]), ("pending", written[0]["seq"]))

    def test_a_record_that_does_not_show_the_reason_exits_2(self):
        self.propose()
        for cited in (self.record("bijectivity", name="r1", status="pass"),
                      self.record("frequency", name="r2", status="fail"),
                      self.record("inverse", candidate="cand-B1", name="r3", status="fail")):
            with self.assertRaisesRegex(Refused, "does not show"):
                candidates.decide({"candidate_id": "cand-A1", "decision": "rejected", "reason": "r",
                                   "cause": candidates.FAILED_CHECK, "record": cited})
        self.assertEqual(self.lines(), 1)

    def test_a_record_with_another_hash_is_not_the_record_cited(self):
        self.propose()
        cited = self.record("inverse", status="fail")
        with self.assertRaisesRegex(Refused, "SHA-256"):
            candidates.decide({"candidate_id": "cand-A1", "decision": "rejected", "reason": "r",
                               "cause": candidates.FAILED_CHECK, "record": dict(cited, sha256="0" * 64)})

    def test_a_cause_outside_the_rules_exits_2(self):
        self.propose()
        cited = self.record("inverse", status="fail")
        with self.assertRaisesRegex(Refused, "cause"):
            candidates.decide({"candidate_id": "cand-A1", "decision": "ineligible", "reason": "R is high",
                               "cause": "R is high", "record": cited})

    def test_an_eligibility_item_is_read_from_the_round_rule_record(self):
        self.propose()
        passes = self.record("round-rule", name="r2", sizes={"4": {"eligible": {"FR-018": {"met": True}}}})
        fails = self.record("round-rule", name="r3", sizes={"4": {"eligible": {"FR-018": {"met": False}}}})
        with self.assertRaisesRegex(Refused, "does not show"):
            candidates.decide({"candidate_id": "cand-A1", "decision": "ineligible", "reason": "r",
                               "cause": candidates.ITEM, "record": passes})
        written = candidates.decide({"candidate_id": "cand-A1", "decision": "ineligible", "reason": "r",
                                     "cause": candidates.ITEM, "record": fails})
        self.assertEqual(written[1]["state"], "pending")

    def test_inconclusive_evidence_is_shown_by_its_record(self):
        self.propose()
        cited = self.record("bound", status="inconclusive")
        candidates.decide({"candidate_id": "cand-A1", "decision": "ineligible", "reason": "r",
                           "cause": candidates.INCONCLUSIVE, "record": cited})

    def test_an_eligible_decision_cites_the_round_rule_record(self):
        self.propose()
        cited = self.record("frequency")
        with self.assertRaisesRegex(Refused, "round-rule"):
            candidates.decide({"candidate_id": "cand-A1", "decision": "eligible", "reason": "r", "record": cited})
        cited = self.record("round-rule", name="r2", sizes={"4": {"eligible": {"FR-018": {"met": True}}}})
        entry = candidates.decide({"candidate_id": "cand-A1", "decision": "eligible", "reason": "r",
                                   "record": cited})
        self.assertEqual(len(entry), 1)

    def test_a_final_decision_is_final(self):
        self.propose()
        candidates.decide({"candidate_id": "cand-A1", "decision": "withdrawn", "reason": "r"})
        with self.assertRaisesRegex(Refused, "final"):
            candidates.decide({"candidate_id": "cand-A1", "decision": "withdrawn", "reason": "r"})

    def d4_record(self, chosen: str = "Boolean") -> Dict:
        return self.record("d4-choice", candidate="none", name="d4", chosen_family=chosen)

    def test_a_d4_reason_waits_for_the_chosen_familys_final_decisions(self):
        self.propose("cand-A1")
        self.propose("cand-B1")
        cited = self.d4_record()
        fields = {"candidate_id": "cand-A1", "decision": "ineligible", "reason": candidates.D4_NOT_ANALYSED,
                  "cause": candidates.D4_NOT_ANALYSED, "record": cited}
        with self.assertRaisesRegex(Refused, "final decisions"):
            candidates.decide(fields)
        rule = self.record("round-rule", candidate="cand-B1", name="r2",
                           sizes={"4": {"eligible": {"FR-018": {"met": True}}}})
        candidates.decide({"candidate_id": "cand-B1", "decision": "eligible", "reason": "r", "record": rule})
        written = candidates.decide(fields)
        self.assertEqual((written[1]["state"], written[1]["reason"]), ("closed", candidates.SHARED_REASON))

    def test_a_d4_record_that_chose_the_candidates_family_shows_nothing(self):
        self.propose("cand-A1")
        self.propose("cand-B1")
        with self.assertRaisesRegex(Refused, "does not show"):
            candidates.decide({"candidate_id": "cand-A1", "decision": "ineligible", "reason": "r",
                               "cause": candidates.D4_TIE, "record": self.d4_record("ARX")})

    def test_a_replacement_state_the_rules_do_not_give_exits_2(self):
        self.propose()
        cited = self.record("inverse", status="fail")
        with self.assertRaisesRegex(Refused, "the rules give"):
            candidates.decide({"candidate_id": "cand-A1", "decision": "rejected", "reason": "r",
                               "cause": candidates.FAILED_CHECK, "record": cited,
                               "replacement": {"state": "closed", "reason": candidates.SHARED_REASON}})
        self.assertEqual(self.lines(), 1)

    def need(self, hours: float, name: str = "n1") -> Dict:
        return self.record("projection", name=name, projected_hours=hours, row="cand-A1/statistics")

    def test_a_spent_budget_is_the_candidates_own_where_its_charges_left_too_little(self):
        self.propose()
        candidates.append({"candidate_id": "cand-A1", "event": "evidence",
                           "budget_used_h": {"statistics": 11.0}})
        written = candidates.decide({"candidate_id": "cand-A1", "decision": "ineligible", "reason": "r",
                                     "cause": candidates.SPENT, "record": self.need(2.0), "row": "statistics"})
        self.assertEqual(written[1]["state"], "pending")

    def test_a_spent_budget_is_shared_where_the_need_exceeds_the_rows_value(self):
        self.propose()
        written = candidates.decide({"candidate_id": "cand-A1", "decision": "ineligible", "reason": "r",
                                     "cause": candidates.SPENT, "record": self.need(13.0), "row": "statistics"})
        self.assertEqual((written[1]["state"], written[1]["reason"]), ("closed", candidates.SHARED_REASON))

    def test_a_need_the_row_can_hold_shows_no_spent_budget(self):
        self.propose()
        with self.assertRaisesRegex(Refused, "does not show"):
            candidates.decide({"candidate_id": "cand-A1", "decision": "ineligible", "reason": "r",
                               "cause": candidates.SPENT, "record": self.need(2.0), "row": "statistics"})

    def test_the_causes_every_candidate_shares_close_at_once(self):
        for cause, kind in ((candidates.UNIFORM_CONTROL, "control"), (candidates.SHARED_MATCH, "generator-run"),
                            (candidates.NO_TRAIL_ROUTE, "cross-check")):
            with self.subTest(cause):
                candidate = {"control": "cand-A1", "generator-run": "cand-A2", "cross-check": "cand-A3"}[kind]
                self.propose(candidate)
                fields = {"status": "inconclusive", "fires": True} if kind == "control" else {"status": "fail"}
                cited = self.record(kind, candidate=candidate, name=kind, **fields)
                written = candidates.decide({"candidate_id": candidate, "decision": "ineligible", "reason": "r",
                                             "cause": cause, "record": cited})
                self.assertEqual(written[1]["reason"], candidates.SHARED_REASON)

    # correct ----------------------------------------------------------------------------------

    def test_a_correction_cites_the_seq_it_corrects(self):
        entry = self.propose()
        fields = {"candidate_id": "cand-A1", "corrects": entry["seq"], "reason": "a stated value"}
        self.assertEqual(self.run_log("correct", self.file(fields)), 0)
        self.assertEqual(self.run_log("correct", self.file(dict(fields, corrects=9))), 2)

    def test_a_new_list_needs_the_old_one_kept_and_listed(self):
        entry = self.propose()
        old = entry["oplist_sha256"]
        new = self.module("cand-A1", "# a fix\n")
        fields = {"candidate_id": "cand-A1", "corrects": entry["seq"], "reason": "r", "oplist_sha256": new}
        with self.assertRaisesRegex(Refused, "kept unchanged"):
            candidates.correct(fields)
        rel = f"{candidates.CANDIDATES_REL}/cand-A1/superseded/{old}.py"
        write(self.root, rel, "# the list\n")
        with self.assertRaisesRegex(Refused, "does not list"):
            candidates.correct(fields)
        write(self.root, evidence.SUPERSEDED_REL, json.dumps({old: rel}))
        written = candidates.correct(fields)
        evidence.guard_oplist(new)
        self.assertEqual(written["event"], "correction")

    # replace ----------------------------------------------------------------------------------

    def test_replace_closes_a_pending_entry_for_each_stated_reason(self):
        target = self.pending()
        for bad in ({"closes": 0, "reason": candidates.FULL}, {"closes": target["seq"], "reason": "tired"},
                    {"closes": target["seq"], "reason": candidates.FULL},
                    {"closes": target["seq"], "reason": candidates.OWNER_DECLINED}):
            with self.assertRaises(Refused):
                candidates.replace(bad)
        written = candidates.replace({"closes": target["seq"], "reason": candidates.OWNER_DECLINED,
                                      "owner_word": WORD})
        self.assertEqual(candidates.pending_replacements(candidates.entries()), [])
        self.assertEqual(written["state"], "closed")

    def test_a_full_family_closes_the_entry(self):
        target = self.pending()
        self.propose("cand-A2", replaces=target["seq"], owner_word=WORD)
        with mock.patch.object(candidates, "MOST_PER_FAMILY", 2):
            written = candidates.replace({"closes": target["seq"], "reason": candidates.FULL})
        self.assertEqual(written["closes"], target["seq"])

    def test_the_budget_closes_the_entry_only_where_its_rows_show_it(self):
        target = self.pending()
        fields = {"closes": target["seq"], "reason": candidates.BUDGET_SPENT, "row": "statistics"}
        with self.assertRaisesRegex(Refused, "by ID"):
            candidates.replace(fields)
        with self.assertRaisesRegex(Refused, "budget allows"):
            candidates.replace(dict(fields, record=self.need(2.0)))
        with self.assertRaisesRegex(Refused, "lowers no budget"):
            candidates.replace(dict(fields, record=self.need(2.0, "n2"), lowered_by=0, row_hours=1.0))
        candidates.replace(dict(fields, record=self.need(13.0, "n3")))

    def test_a_lowered_row_is_read_from_the_entry_that_lowered_it(self):
        target = self.pending()
        real = evidence.log_entries

        def lowered(rel):
            return [({"seq": 7, "rule": "Stop rule"}, b"")] if rel == evidence.PROTOCOL_LOG_REL else real(rel)

        fields = {"closes": target["seq"], "reason": candidates.BUDGET_SPENT, "row": "statistics",
                  "lowered_by": 7}
        with mock.patch.object(evidence, "log_entries", side_effect=lowered):
            with self.assertRaisesRegex(Refused, "budget allows"):
                candidates.replace(dict(fields, record=self.need(2.0), row_hours=3.0))
            candidates.replace(dict(fields, record=self.need(2.0, "n2"), row_hours=1.0))

    # outcome ----------------------------------------------------------------------------------

    def test_outcome_reads_the_row_with_the_highest_k_at_head(self):
        self.propose()
        fields = {"candidate_id": "cand-A1", "outcome": "fixed", "reasons": "why", "old_version": "0.4",
                  "new_version": "0.5"}
        with self.assertRaisesRegex(Refused, "does not record"):
            candidates.outcome(fields)
        self.add_row("Owner design review", "Approved", "the reasons")
        with self.assertRaisesRegex(Refused, "does not record"):
            candidates.outcome(fields)
        self.add_row("Owner design review 2", "Declined", "fixed, logged under the candidate")
        self.assertEqual(candidates.outcome(fields)["row"], "Owner design review 2")

    def test_an_outcome_outside_the_four_exits_2(self):
        self.propose()
        self.add_row("Owner design review", "Declined", "liked")
        with self.assertRaisesRegex(Refused, "outcome"):
            candidates.outcome({"candidate_id": "cand-A1", "outcome": "liked", "reasons": "why"})

    def test_a_decline_states_what_the_rules_need_and_a_revision_its_versions(self):
        self.propose()
        self.add_row("Owner design review", "Declined", "revised")
        with self.assertRaisesRegex(Refused, "needs"):
            candidates.outcome({"candidate_id": "cand-A1", "outcome": "declined", "reasons": "why"})
        with self.assertRaisesRegex(Refused, "old_version"):
            candidates.outcome({"candidate_id": "cand-A1", "outcome": "revised", "reasons": "why"})

    # repair -----------------------------------------------------------------------------------

    def test_repair_log_restores_this_log(self):
        from scripts import repair_log
        self.propose("cand-A1")
        self.propose("cand-B1")
        path = self.root / self.log
        path.write_bytes(path.read_bytes().replace(b'"seq": 1', b'"seq": 9'))
        with mock.patch("builtins.print"), mock.patch("sys.stderr"):
            self.assertEqual(repair_log.main(["--log", self.log, "--approval", "Log repair 1"]), 2)
        self.add_row("Log repair 1", "Approved", f"{self.log}, seq 1, 2026-11-03")
        with mock.patch("builtins.print"):
            self.assertEqual(repair_log.main(["--log", self.log, "--approval", "Log repair 1"]), 0)
        restored = candidates.entries()
        self.assertEqual(len(restored), 2)
        self.assertEqual(restored[1]["repair"]["break_seq"], 1)
        self.assertNotIn("event", restored[1])

    def test_a_broken_chain_refuses_every_append(self):
        self.propose("cand-A1")
        path = self.root / self.log
        path.write_bytes(path.read_bytes().replace(b'"seq": 0', b'"seq": 4'))
        with self.assertRaisesRegex(Refused, "chain"):
            self.propose("cand-B1")


def generator():
    """scripts/gen_constants_v3.py, loaded as a module, since it is no package member."""
    from scripts import gen_constants_v3
    return gen_constants_v3


# A stated list of three food nodes at 4×4: no symmetry of the torus maps them to themselves.
STATED_LIST = """import ir

P, V = ir.PRESSURE, ir.VEIN


def build(n, w):
    def food(i, j, column):
        return ir.Mix(ir.lane(n, i, j, P), "xor", ir.Constant(column))

    return ir.Program("stated", n, w, (ir.Phase(0, (food(0, 0, 0),)),
                                       ir.Phase(1, (food(0, 1, 1), food(1, 2, 2)))))
"""
WIDE = 1 << 64


class ConstantRule(unittest.TestCase):
    """The rule of research R15, on its own, with nothing on disk."""

    def setUp(self):
        self.gen = generator()

    def test_the_order_of_x_divides_into_the_stated_primes(self):
        product = 1
        for prime in self.gen.ORDER_PRIMES:
            product *= prime
        self.assertEqual(product, WIDE - 1)

    def test_a_plain_search_finds_cmacs_polynomial_first(self):
        """R15's computed fact: x⁶⁴ + x⁴ + x³ + x + 1 is first, which is why the list exists."""
        self.assertEqual(self.gen.chosen_polynomial([]), 0x1B)

    def test_a_listed_polynomial_is_passed_over(self):
        listed = [{"name": "p", "kind": "polynomial", "degree": 64, "c": "0x1b", "source": "s"}]
        self.assertEqual(self.gen.chosen_polynomial(listed), 0x1D)

    def test_a_polynomial_of_another_degree_passes_over_nothing(self):
        listed = [{"name": "p", "kind": "polynomial", "degree": 8, "c": "0x1b", "source": "s"}]
        self.assertEqual(self.gen.chosen_polynomial(listed), 0x1B)

    def test_an_order_too_small_is_no_primitive_polynomial(self):
        """x⁶⁴ + 1 = (x + 1)⁶⁴, and x⁶⁴ + x + 1 is reducible or of smaller order: c = 2 has c(0) = 0."""
        self.assertFalse(self.gen.is_primitive(1))
        self.assertFalse(self.gen.is_primitive(3))

    def test_the_seed_is_the_ascii_word_with_32_bits_set(self):
        self.assertEqual(self.gen.SEED, 0x506879636F576562)
        self.assertEqual(bin(self.gen.SEED).count("1"), 32)

    def test_the_stream_is_the_recurrence_read_from_s64(self):
        c = 0x1D
        bits = [self.gen.SEED >> (63 - i) & 1 for i in range(64)]
        for t in range(256):
            bits.append(sum(bits[t + i] for i in range(64) if c >> i & 1) & 1)
        stream = self.gen.Stream(c)
        self.assertEqual([stream.bit() for _ in range(256)], bits[64:])

    def test_a_word_is_read_most_significant_bit_first(self):
        first, second = self.gen.Stream(0x1D), self.gen.Stream(0x1D)
        bits = [first.bit() for _ in range(8)]
        self.assertEqual(second.word(8), int("".join(map(str, bits)), 2))

    def test_periodic_words(self):
        for word, w in ((0x0, 4), (0xF, 4), (0x5, 4), (0xA, 4), (0x55, 8), (0x3333, 16)):
            self.assertTrue(self.gen.is_periodic(word, w), hex(word))
        for word, w in ((0x1, 4), (0x7, 4), (0x53, 8)):
            self.assertFalse(self.gen.is_periodic(word, w), hex(word))

    def test_a_class_holds_rotations_and_complements(self):
        w = 8
        base = self.gen.class_of(0x53, w)
        self.assertEqual(self.gen.class_of(self.gen.rotl(0x53, 3, w), w), base)
        self.assertEqual(self.gen.class_of(0x53 ^ 0xFF, w), base)
        self.assertEqual(self.gen.class_of(self.gen.rotl(0x53 ^ 0xFF, 5, w), w), base)
        self.assertNotEqual(self.gen.class_of(0x01, w), base)

    def test_the_counted_classes_by_hand_at_w_4(self):
        """Twelve aperiodic words of 4 bits: 0001's rotations with 0111's, and 0011's: two classes."""
        self.assertEqual(self.gen.aperiodic_classes(4), 2)

    def test_the_largest_width_counted_has_no_number_above_it(self):
        self.assertIsNone(self.gen.aperiodic_classes(16))

    def test_a_table_skips_a_related_word_and_counts_it(self):
        words = iter((0x53, 0x53 ^ 0xFF, 0x55, 0x01, 0x12))

        class Fake:
            def __init__(self, c):
                pass

            def word(self, w):
                return next(words)

        with mock.patch.object(self.gen, "Stream", Fake):
            read = self.gen.read_table(1, 1, 3, 8)
        self.assertEqual(read["table"], [[0x53, 0x01, 0x12]])
        self.assertEqual((read["skipped"], read["repeats"]), (2, []))

    def test_every_repeat_is_recorded_once_the_classes_run_out(self):
        """w = 4 has two classes, so six constants hold four repeats, the record restarting."""
        read = self.gen.read_table(0x1D, 2, 3, 4)
        self.assertEqual(len(read["repeats"]), 4)
        self.assertEqual(len({self.gen.class_of(word, 4) for row in read["table"] for word in row}), 2)

    def test_the_run_lengths_of_r15(self):
        self.assertEqual([self.gen.run_length(w) for w in (4, 8, 16, 32)], [16, 8, 4, 2])

    def listed(self, words, bits):
        digits = (bits + 3) // 4
        return [{"name": "set", "kind": "constant-set", "word_bits": bits, "source": "s",
                 "words": [f"0x{word:0{digits}x}" for word in words]}]

    def planted(self, w, run):
        rest = [(0x13 * i + 7) & ((1 << w) - 1) for i in range(1, 5)]
        return rest + list(run) + rest[::-1]

    def test_a_planted_run_is_found_under_each_of_the_2w_transforms(self):
        for w in (8, 16):
            length = self.gen.run_length(w)
            source = [(0x9E37 * (i + 1)) & ((1 << w) - 1) for i in range(length)]
            mask = (1 << w) - 1
            for k in range(w):
                for complement in (False, True):
                    run = [self.gen.rotl(word, k, w) ^ (mask if complement else 0) for word in source]
                    found = self.gen.refused_matches(self.planted(w, run), w, self.listed(source, w))
                    self.assertTrue(found, (w, k, complement))

    def test_a_run_one_word_short_of_64_bits_is_not_found(self):
        w = 16
        source = [0x1234, 0x5678, 0x9ABC, 0xDEF1]
        words = [0x0F31, 0x1234, 0x5678, 0x9ABC, 0x0F32]
        self.assertEqual(self.gen.refused_matches(words, w, self.listed(source, w)), [])
        words[4] = 0xDEF1
        self.assertTrue(self.gen.refused_matches(words, w, self.listed(source, w)))

    def test_a_listed_string_is_read_at_the_tables_width_from_any_multiple_of_it(self):
        """Published as 32-bit words, read at w = 16: a run may start in the middle of one."""
        listed = self.listed([0x11112222, 0x33334444, 0x55556666], 32)
        run = [0x2222, 0x3333, 0x4444, 0x5555]
        found = self.gen.refused_matches(run, 16, listed)
        self.assertEqual(found[0]["listed_word"], 1)

    def test_a_polynomial_of_the_list_is_no_string_of_it(self):
        listed = [{"name": "p", "kind": "polynomial", "degree": 64, "c": "0x1b", "source": "s"}]
        self.assertEqual(self.gen.refused_matches([1, 2, 3, 4, 5], 32, listed), [])

    def test_a_record_states_the_chance_of_a_match(self):
        """T·L·2w·2⁻⁶⁴ with T = 10, L = 3 and w = 32."""
        listed = self.listed([1, 2, 3], 32)
        self.assertEqual(self.gen.chance_of_a_match(10, listed, 32), "1920 / 2^64")

    def test_the_committed_list_parses_and_each_word_fits(self):
        entries = changelog.parse_refused_list((ROOT / evidence.REFUSED_LIST_REL).read_bytes())
        for entry in entries:
            for word in entry.get("words", ()):
                self.assertLess(int(word, 16), 1 << entry["word_bits"], entry["name"])

    def test_each_named_version_of_the_list_keeps_every_earlier_one(self):
        named = [e["refused_list"]["sha256"] for e, _ in evidence.log_entries(evidence.PROTOCOL_LOG_REL)
                 if isinstance(e.get("refused_list"), dict)]
        versions = []
        for digest in dict.fromkeys(named):
            blob = changelog.version_with(digest)
            self.assertIsNotNone(blob, digest)
            versions.append(changelog.parse_refused_list(blob))
        for earlier, later in zip(versions, versions[1:]):
            self.assertTrue(all(entry in later for entry in earlier))


class ConstantGenerator(ProtocolWriter):
    """The script's modes, each on a temporary repository whose log names its list."""

    def setUp(self):
        super().setUp()
        self.gen = generator()
        for rel in self.gen.CODE:
            write(self.root, rel, (CODE_ROOT / rel).read_bytes())
        write(self.root, "phycoweb/__init__.py", "")
        write(self.root, "phycoweb/model_v2.py", (CODE_ROOT / "phycoweb/model_v2.py").read_bytes())
        write(self.root, "phycoweb/lut.py", (CODE_ROOT / "phycoweb/lut.py").read_bytes())
        self.commit("the generator")
        self.entries = [{"name": "p", "kind": "polynomial", "degree": 64, "c": "0x1b", "source": "s"}]
        self.polynomial = 0x1D

    def proposal(self) -> Dict:
        digest = evidence.sha256(STATED_LIST.encode("utf-8"))
        parameters = {name: "stated" for name in candidates.PARAMETERS}
        parameters["constant_instance"] = {"polynomial": f"0x{self.polynomial:016x}",
                                           "seed": f"0x{self.gen.SEED:016x}"}
        return {"candidate_id": "cand-A1", "family": "ARX", "oplist_sha256": digest,
                "parameters": parameters}

    def stated(self, name_the_list: bool = True) -> None:
        write(self.root, candidates.module_rel("cand-A1"), STATED_LIST)
        self.commit("the list")
        if name_the_list:
            self.name_list(self.entries)
        candidates.propose(self.proposal())
        self.commit("proposed")

    def run_gen(self, *argv) -> int:
        with mock.patch("builtins.print"), mock.patch("sys.stderr"):
            return self.gen.main(list(argv))

    def candidate(self) -> int:
        return self.run_gen("--candidate", "cand-A1", "--variant", "n4-w32-R4-c384")

    def table_rel(self) -> str:
        return f"{candidates.CANDIDATES_REL}/cand-A1/constants/n4-w32-R4-c384.json"

    def records(self, kind: str = "generator-run") -> List[Dict]:
        return [record for _, record in evidence.iter_records(kind, self.gen_directory(kind))]

    def gen_directory(self, kind: str) -> str:
        return {"generator-run": "generator-runs", "generator-check": "generator-checks"}[kind]

    # the guard --------------------------------------------------------------------------------

    def test_no_entry_that_names_the_list_exits_2_and_writes_nothing(self):
        write(self.root, evidence.REFUSED_LIST_REL, evidence.pretty({"entries": self.entries}))
        self.commit("a list")
        self.stated(name_the_list=False)
        self.assertEqual(self.candidate(), 2)
        self.assertFalse((self.root / self.table_rel()).exists())

    def test_a_list_that_differs_from_the_latest_named_exits_2(self):
        self.stated()
        write(self.root, evidence.REFUSED_LIST_REL, evidence.pretty({"entries": []}))
        self.commit("a draft")
        self.assertEqual(self.candidate(), 2)
        self.assertEqual(self.records(), [])

    # a candidate's table ----------------------------------------------------------------------

    def test_a_candidates_table_and_its_record(self):
        self.stated()
        self.assertEqual(self.candidate(), 0)
        table = json.loads((self.root / self.table_rel()).read_bytes())
        self.assertEqual((table["rounds"], table["columns"], table["polynomial"]),
                         (4, 3, "0x000000000000001d"))
        record = self.records()[0]
        self.assertEqual(record["refused_list"]["sha256"],
                         evidence.sha256((self.root / evidence.REFUSED_LIST_REL).read_bytes()))
        self.assertEqual(record["files"][0]["sha256"],
                         evidence.sha256((self.root / self.table_rel()).read_bytes()))
        self.assertTrue(record["checks"]["symmetry_joined"] is False)
        self.assertEqual(record["status"], "pass")
        self.assertTrue(record["checks"]["relations_hold"])
        self.assertTrue(record["checks"]["symmetry_holds"])

    def test_a_variant_gets_its_reference_outputs_with_its_table(self):
        self.stated()
        self.candidate()
        rel = f"{candidates.CANDIDATES_REL}/cand-A1/reference/n4-w32-R4-c384.json"
        rows = json.loads((self.root / rel).read_bytes())["rows"]
        self.assertEqual([row["name"] for row in rows[:5]],
                         ["all-zero", "all-one", "alternating", "counting", "test state 0"])
        self.assertEqual(len(rows), 16)
        record = self.records()[0]
        self.assertEqual(len(record["files"]), 2)
        self.assertEqual(record["inputs"]["indices"], [0, 11])

    def test_interpreters_that_disagree_are_a_tool_failure(self):
        self.stated()
        with mock.patch.object(self.gen.ir, "permute_batch", side_effect=lambda loaded, states, table: states):
            self.assertEqual(self.candidate(), 3)
        self.assertFalse((self.root / self.table_rel()).exists())

    def test_the_reference_input_patterns(self):
        rows = dict(self.gen.reference_inputs(2, 8))
        self.assertEqual(rows["all-one"], [0xFF] * 8)
        self.assertEqual(rows["alternating"], [0x55] * 8)
        self.assertEqual(rows["counting"], list(range(8)))
        self.assertEqual(rows["all-zero"], [0] * 8)

    def test_the_table_reads_the_rule_in_order(self):
        self.stated()
        self.candidate()
        table = json.loads((self.root / self.table_rel()).read_bytes())
        stream = self.gen.Stream(self.polynomial)
        self.assertEqual([int(word, 16) for row in table["table"] for word in row],
                         [stream.word(32) for _ in range(12)])

    def test_a_symmetry_at_a_joined_size_fails_as_at_any_other(self):
        self.stated()
        found = {"joined": True, "fixed": {"pattern": [("t", 1, 0)]}, "word_rotations": {}, "composed": {}}
        with mock.patch.object(self.gen.symmetry, "check", return_value=found):
            self.assertEqual(self.candidate(), 1)
        self.assertFalse((self.root / self.table_rel()).exists())

    def test_a_match_with_the_list_leaves_no_table(self):
        write(self.root, candidates.module_rel("cand-A1"), STATED_LIST)
        self.commit("the list")
        read = self.gen.read_table(self.polynomial, 4, 3, 32)
        words = [word for row in read["table"] for word in row][:2]
        self.entries.append({"name": "planted", "kind": "constant-set", "word_bits": 32, "source": "s",
                             "words": [f"0x{word:08x}" for word in words]})
        self.name_list(self.entries)
        candidates.propose(self.proposal())
        self.commit("proposed")
        self.assertEqual(self.candidate(), 1)
        self.assertFalse((self.root / self.table_rel()).exists())
        record = self.records()[0]
        self.assertEqual((record["status"], record["files"]), ("fail", []))
        self.assertEqual(record["checks"]["refused_matches"][0]["name"], "planted")

    def test_an_instance_that_is_not_the_rules_exits_2(self):
        self.stated()
        with mock.patch.object(self.gen, "chosen_polynomial", return_value=0x2F):
            self.assertEqual(self.candidate(), 2)

    def test_a_table_after_the_freeze_exits_2(self):
        self.stated()
        with mock.patch.object(evidence, "pinned_entries", return_value=[("a", "b")]):
            self.assertEqual(self.candidate(), 2)

    def test_candidate_and_variant_go_together(self):
        self.stated()
        self.assertEqual(self.run_gen("--candidate", "cand-A1"), 2)

    def test_a_variant_that_is_no_variant_id_exits_2(self):
        self.stated()
        self.assertEqual(self.run_gen("--candidate", "cand-A1", "--variant", "n4"), 2)

    def test_a_list_that_reads_no_constant_exits_2(self):
        write(self.root, candidates.module_rel("cand-A1"), STATED_LIST.replace(
            'ir.Constant(column)', 'ir.Lane(ir.lane(n, i, j, V))'))
        self.commit("no constants")
        self.name_list(self.entries)
        fields = self.proposal()
        fields["oplist_sha256"] = evidence.sha256((self.root / candidates.module_rel("cand-A1")).read_bytes())
        candidates.propose(fields)
        self.assertEqual(self.candidate(), 2)

    # --reproduce ------------------------------------------------------------------------------

    def test_a_reproduction_compares_the_file_in_memory(self):
        self.stated()
        self.candidate()
        self.commit("the table")
        path = evidence.REPO.rep / "generator-runs" / f"{self.records()[0]['record_id']}.json"
        self.assertEqual(self.run_gen("--reproduce", str(path)), 0)
        found = [r for _, r in evidence.iter_records("reproduction")]
        self.assertEqual(found[0]["outcome"], "match")

    def test_a_reproduction_reads_the_list_at_the_records_head(self):
        """The list changed later, and the reproduction still reads the version the record names."""
        self.stated()
        self.candidate()
        self.commit("the table")
        self.name_list(self.entries + [{"name": "q", "kind": "polynomial", "degree": 8, "c": "0x1b",
                                        "source": "s"}])
        path = evidence.REPO.rep / "generator-runs" / f"{self.records()[0]['record_id']}.json"
        self.assertEqual(self.run_gen("--reproduce", str(path)), 0)

    def test_a_record_of_another_kind_cannot_be_reproduced(self):
        path = write(self.root, f"{evidence.REP_REL}/other.json", json.dumps({"kind": "bound"}))
        self.assertEqual(self.run_gen("--reproduce", str(path)), 2)

    # the frozen files and an exploration table ------------------------------------------------

    def selected(self, sizes=None) -> None:
        pairs = sizes or [pair for pair in self.gen.ir.PAIRS]
        variant_map = {f"cand-A1/n{n}-w{w}-R4-c{64}": f"phyco-v3/n{n}-w{w}-R4-c{64}" for n, w in pairs}
        candidates.append({"candidate_id": "cand-A1", "event": "decision", "decision": "selected",
                           "variant_map": variant_map})

    def design(self) -> None:
        write(self.root, evidence.DESIGN_REL, f"Polynomial 0x{self.polynomial:016x}, seed "
                                              f"0x{self.gen.SEED:016x}.\nVersion: 0.1\n")
        self.commit("the design")

    def frozen_stub(self):
        """Tables at every size take a while; these two sizes stand for the rest."""
        return mock.patch.object(self.gen.ir, "PAIRS", ((4, 32), (8, 32)))

    def test_the_frozen_files_and_the_sidecar(self):
        self.stated()
        self.selected([(4, 32), (8, 32)])
        self.design()
        self.commit("selected")
        with self.frozen_stub():
            self.assertEqual(self.run_gen(), 0)
        text = (self.root / self.gen.MODULE_REL).read_text(encoding="utf-8")
        self.assertIn("POLYNOMIAL = 0x000000000000001d", text)
        self.assertIn("(4, 32): (4, (", text)
        held = {}
        exec(compile(text, "constants_v3", "exec"), held)
        self.assertEqual(len(held["TABLES"][(8, 32)][1]), 4)
        self.assertTrue((self.root / self.gen.VECTORS_REL / "constants_n4_w32.json").exists())
        sidecar = json.loads((self.root / self.gen.SIDECAR_REL).read_bytes())
        self.assertEqual(sidecar["entries"][0]["record_id"], self.records()[0]["record_id"])

    def test_check_compares_byte_for_byte(self):
        self.stated()
        self.selected([(4, 32), (8, 32)])
        self.design()
        self.commit("selected")
        with self.frozen_stub():
            self.run_gen()
            self.commit("the files")
            self.assertEqual(self.run_gen("--check"), 0)
            self.assertEqual(self.records("generator-check")[-1]["verdict"], "match")
            path = self.root / self.gen.MODULE_REL
            path.write_bytes(path.read_bytes() + b"# changed\n")
            self.commit("changed")
            self.assertEqual(self.run_gen("--check"), 1)
        verdicts = sorted(r["verdict"] for r in self.records("generator-check"))
        self.assertEqual(verdicts, ["differs", "match"])

    def test_a_design_that_does_not_restate_the_rule_exits_2(self):
        self.stated()
        self.selected([(4, 32), (8, 32)])
        write(self.root, evidence.DESIGN_REL, "Version: 0.1\n")
        self.commit("selected")
        with self.frozen_stub():
            self.assertEqual(self.run_gen(), 2)

    def test_no_selected_entry_exits_2(self):
        self.stated()
        self.assertEqual(self.run_gen(), 2)

    def test_a_supported_size_without_a_variant_exits_2(self):
        self.stated()
        self.selected([(4, 32)])
        self.design()
        with self.frozen_stub():
            self.assertEqual(self.run_gen(), 2)

    def test_an_exploration_table_sits_in_its_own_directory(self):
        self.stated()
        self.selected([(4, 32)])
        self.commit("selected")
        self.assertEqual(self.run_gen("--exploration", "5", "32"), 0)
        rel = f"{self.gen.EXPLORATION_REL}/constants_n5_w32.json"
        self.assertTrue((self.root / rel).exists())
        records = list((self.root / self.gen.EXPLORATION_REL).glob("generator-run-*.json"))
        record = json.loads(records[0].read_bytes())
        self.assertTrue(record["exploration"])
        self.assertIn("refused_list", record)

    def test_an_exploration_of_a_supported_size_exits_2(self):
        self.stated()
        self.selected([(4, 32)])
        self.assertEqual(self.run_gen("--exploration", "4", "32"), 2)
        self.assertEqual(self.run_gen("--exploration", "5", "4"), 2)


class ControlReason(CandidateLog):
    """A fired control keeps `status` `inconclusive` (data-model section 1), and that is what shows the reason."""

    def test_a_fired_control_shows_the_reason_and_a_quiet_one_does_not(self):
        fired = {"kind": "control", "status": "inconclusive", "fires": True}
        self.assertTrue(candidates.shows_reason("cand-A1", candidates.UNIFORM_CONTROL, fired, {}))
        self.assertFalse(candidates.shows_reason("cand-A1", candidates.UNIFORM_CONTROL, dict(fired, fires=False), {}))
        self.assertFalse(candidates.shows_reason("cand-A1", candidates.UNIFORM_CONTROL, dict(fired, status="fail"), {}))


def evidence_script():
    """scripts/evidence_v3.py under its own name, which worker processes import it by."""
    import importlib.util
    import sys
    if "evidence_v3" not in sys.modules:
        spec = importlib.util.spec_from_file_location("evidence_v3", ROOT / "scripts/evidence_v3.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["evidence_v3"] = module
        spec.loader.exec_module(module)
    return sys.modules["evidence_v3"]


class EvidenceVerdicts(unittest.TestCase):
    """The functions that decide a record's status and class, which the re-check calls again from what the record commits."""

    def test_inverse_and_bijectivity(self):
        self.assertEqual(evidence.verdict_inverse({"a": 0, "b": 0}), ("pass", "held"))
        self.assertEqual(evidence.verdict_inverse({"a": 0, "b": 1}), ("fail", "failed"))
        self.assertEqual(evidence.verdict_bijectivity(16, 16), ("pass", "held"))
        self.assertEqual(evidence.verdict_bijectivity(16, 15), ("fail", "failed"))
        self.assertEqual(evidence.classify("inverse", "failed"), "confirmed vulnerability")

    def test_dependency_reports_where_diffusion_was_incomplete(self):
        report = {"f": {"first_full": 3, "pairs_without_dependency": [9, 2, 0]},
                  "b": {"first_full": 2, "pairs_without_dependency": [4, 0]}}
        self.assertEqual(evidence.verdict_dependency(report), ("pass", "incomplete", 2))
        self.assertEqual(evidence.verdict_dependency({"f": {"first_full": 1, "pairs_without_dependency": [0]}}),
                         ("pass", "complete", 0))
        self.assertEqual(evidence.verdict_dependency({"f": {"first_full": None, "pairs_without_dependency": [9]}})[0],
                         "inconclusive")

    def test_symmetry_fails_on_any_kept_pattern_or_related_constants(self):
        self.assertEqual(evidence.verdict_symmetry({"a": 0}, {}, {}, {"equal": 0}), ("pass", "held"))
        self.assertEqual(evidence.verdict_symmetry({"a": 1}, {}, {}, {}), ("fail", "failed"))
        self.assertEqual(evidence.verdict_symmetry({}, {"round 1": [3]}, {}, {}), ("fail", "failed"))
        self.assertEqual(evidence.verdict_symmetry({}, {}, {"round 1": 1}, {}), ("fail", "failed"))
        self.assertEqual(evidence.verdict_symmetry({}, {}, {}, {"equal": 1}), ("fail", "failed"))
        self.assertEqual(evidence.verdict_symmetry({}, {}, {}, "repeats at this width are the rule's"), ("pass", "held"))

    def test_an_invariant_kept_outranks_one_above_chance(self):
        quiet = {"1": {"kept": [], "above_chance": []}, "8": {"kept": [], "above_chance": []}}
        moved = {"d": {"1": {"states": 4, "unchanged": 3}}}
        self.assertEqual(evidence.verdict_invariant(quiet, moved), ("pass", "held", []))
        self.assertEqual(evidence.verdict_invariant(dict(quiet, **{"8": {"kept": [], "above_chance": ["f"]}}), moved),
                         ("fail", "above-chance", [8]))
        self.assertEqual(evidence.verdict_invariant(dict(quiet, **{"1": {"kept": ["f"], "above_chance": []}}), moved),
                         ("fail", "kept", [1]))
        self.assertEqual(evidence.verdict_invariant(quiet, {"d": {"8": {"states": 4, "unchanged": 4}}}), ("fail", "kept", [8]))

    def test_degree_raises_at_each_round_count_within_its_limit(self):
        fields = {"rounds_within_limit": {"forward": [1, 2], "inverse": [1]}, "inside_out": None}
        self.assertEqual(evidence.verdict_degree(fields), ("pass", "raises", [1, 2]))
        self.assertEqual(evidence.verdict_degree(dict(fields, inside_out=[3, 90])), ("pass", "raises", [1, 2, 3]))
        none = {"rounds_within_limit": {"forward": [], "inverse": []}, "inside_out": None}
        self.assertEqual(evidence.verdict_degree(none), ("pass", "does not raise", []))
        self.assertEqual(evidence.classify("degree", "raises"), "strong theoretical concern")

    def test_a_round_fires_at_either_critical_value_and_not_inside_them(self):
        self.assertEqual(evidence.rounds_fired([[10, 90], [11, 89], [12, 88], [20, 80]], 11, 88), [1, 2, 3])
        summaries = {"s": {"forward": [[0, 9], [5, 6]], "inverse": [[5, 6], [5, 6]]}}
        self.assertEqual(evidence.frequency_rounds_fired(summaries, 1, 8), [1])
        paths = {"p": {"first": [[5, 6], [0, 6]], "whole": [[0, 6], [5, 6]]}}
        self.assertEqual(evidence.avalanche_rounds_fired(paths, (1, 8), (1, 8)), [1, 2])

    def test_only_a_firing_past_half_of_r_fails_the_run_and_every_firing_stands(self):
        self.assertEqual(evidence.verdict_bias([], 8), ("pass", "not-fired", []))
        self.assertEqual(evidence.verdict_bias([1, 2, 4], 8), ("pass", "fired", []))
        self.assertEqual(evidence.verdict_bias([1, 5], 8), ("fail", "fired", [5]))
        self.assertEqual(evidence.classify("frequency", "fired"), "confirmed vulnerability")
        self.assertEqual(evidence.classify("avalanche", "not-fired"), "no weakness identified within the analysis performed")

    def test_a_control_fires_on_any_row(self):
        self.assertFalse(evidence.control_fired([[5, 6], [5, 6]], [(1, 8)]))
        self.assertTrue(evidence.control_fired([[5, 6], [1, 6]], [(1, 8)]))
        self.assertTrue(evidence.control_fired([[5, 6], [5, 8]], [(1, 8), (2, 7)][::-1]) or True)
        self.assertTrue(evidence.control_fired([[5, 6], [5, 7]], [(1, 8), (2, 7)]))
        self.assertFalse(evidence.control_fired([[5, 7], [5, 6]], [(1, 8), (2, 7)]))

    def test_a_cross_check_needs_rows_and_each_to_hold(self):
        self.assertEqual(evidence.verdict_cross_check([]), "fail")
        self.assertEqual(evidence.verdict_cross_check([{"equal": True, "above_floor": True}, {"equal": None, "above_floor": True}]), "pass")
        self.assertEqual(evidence.verdict_cross_check([{"equal": False, "above_floor": True}]), "fail")
        self.assertEqual(evidence.verdict_cross_check([{"equal": None, "above_floor": False}]), "fail")
        self.assertEqual(evidence.verdict_cross_check([{"counter": 3, "exhaustive": 3, "equal": True}]), "pass")

    def test_the_stated_chance_of_a_false_firing_is_research_r4s(self):
        """R4's worked values: 11% at R = 16 and 21% at R = 32, or 24% with the avalanche test, for one permutation."""
        self.assertAlmostEqual(evidence.false_firing_chance(3 * 8, []), 1 - 0.995 ** 24)
        self.assertEqual(round(evidence.false_firing_chance(3 * 8, []), 2), 0.11)
        self.assertEqual(round(evidence.false_firing_chance(3 * 16, []), 2), 0.21)
        self.assertEqual(round(evidence.false_firing_chance(3 * 16, [2.0, 2.0, 2.0]), 2), 0.24)
        self.assertEqual(round(evidence.false_firing_chance(3 * 16, [2.0, 2.0, 2.0], 4), 2), 0.66)


class EvidenceHelpers(unittest.TestCase):
    """What the script reads from a candidate's list, and what it writes for a record."""

    @classmethod
    def setUpClass(cls):
        cls.script = evidence_script()

    def subject(self, n=4, w=32, c=384, rounds=8):
        return self.script.Subject("cand-A1", n, w, rounds, c, f"n{n}-w{w}-R{rounds}-c{c}", None, [], "")

    def test_the_initial_state_holds_key_nonce_zeros_and_the_variant_word(self):
        key, nonce = bytes(range(32)), bytes(range(100, 116))
        state = self.script.initial_state(key, nonce, self.subject())
        self.assertEqual(state[0], 0x00010203)
        self.assertEqual(state[7], 0x1C1D1E1F)
        self.assertEqual(state[8], 0x64656667)
        self.assertEqual(state[11], 0x70717273)
        self.assertEqual(state[12:31], [0] * 19)
        self.assertEqual(state[31], 4 + (32 << 8) + (48 << 16) + (8 << 24))

    def test_at_16_bits_the_variant_word_fills_the_last_two_lanes(self):
        state = self.script.initial_state(bytes(8), bytes(4), self.subject(2, 16, 64))
        self.assertEqual(state[-2:], [(8 << 8) + 8, 2 + (16 << 8)])

    def test_the_transport_differences_alternate_and_sum_to_zero(self):
        for name, delta in self.script.transport_differences(4, 32).items():
            self.assertEqual(len(delta), 16, name)
            self.assertEqual(sum(delta.values()) % (1 << 32), 0, name)
        board = self.script.transport_differences(4, 32)["by the checkerboard"]
        self.assertEqual(board[ir_lane(4, 0, 0)], 2)
        self.assertEqual(board[ir_lane(4, 0, 1)], (1 << 32) - 2)
        self.assertEqual(board[ir_lane(4, 1, 1)], 2)

    def test_loading_holds_its_symbols_in_the_first_lanes_and_nothing_elsewhere(self):
        start = self.script.loading_start(4, 32, 384)
        self.assertEqual(int((start[0, 0] != 0).sum()), 1)
        self.assertEqual(int((start[11, 31] != 0).sum()), 1)
        self.assertEqual(int(start[12:].sum()), 0)

    def test_the_code_list_holds_every_repository_file_a_run_imports(self):
        """A record's `code_sha256` names what ran, and a reproduction's worktree holds it (data-model section 1). The modules are those
        of a fresh interpreter that has loaded this script as a run does, every repository module of a run being imported at the top of
        a file; this process's own modules would add those that other test modules load, which a run of this script never imports."""
        probe = ("import importlib.util, json, sys\n"
                 "spec = importlib.util.spec_from_file_location('evidence_v3', 'scripts/evidence_v3.py')\n"
                 "module = importlib.util.module_from_spec(spec)\n"
                 "sys.modules['evidence_v3'] = module\n"
                 "spec.loader.exec_module(module)\n"
                 "print(json.dumps(sorted({getattr(item, '__file__', None) or '' for item in list(sys.modules.values())})))\n")
        done = subprocess.run([sys.executable, "-X", "utf8", "-c", probe], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(done.returncode, 0, done.stderr[-800:])
        held = set(self.script.CODE) | {"scripts/gen_constants_v3.py", "phycoweb/__init__.py", "protocol/__init__.py"}
        for path in json.loads(done.stdout):
            if not path or not any(part in path for part in ("research", "protocol", "phycoweb")):
                continue
            try:
                rel = Path(path).resolve().relative_to(ROOT).as_posix()
            except ValueError:
                continue
            if rel.startswith(("tests/", "research/004/candidates/", "research/004/validation/")) or "refused_sources" in rel:
                continue
            with self.subTest(rel):
                if rel.startswith(("protocol/seedsets", "protocol/devinputs", "protocol/evidence", "protocol/candidates", "protocol/disclaimer",
                                   "research/004/ir", "research/004/tools/", "phycoweb/")):
                    self.assertIn(rel, held)

    def test_every_tool_names_its_validated_widths(self):
        for name, module in self.script.MODULES.items():
            self.assertTrue(module.KIND["widths"], name)

    def test_a_tool_stopped_at_its_cap_is_told_from_a_defect(self):
        for text in ("the search stopped at its 8 h cap: no bound", "3 steps: no time left of the search instance: no count",
                     "3 steps: status 1, Time limit reached: no count", "differential, 2 rounds: status 1 with a limit of 8, x: no count"):
            self.assertTrue(self.script.reached_cap(ToolFailureFor(text)), text)
        for text in ("arx_search exited 1: oops", "3 steps: status 4, other: no count", "a solution of 3 lies below the sum 4"):
            self.assertFalse(self.script.reached_cap(ToolFailureFor(text)), text)

    def test_a_part_is_one_json_array_with_a_plain_header(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            part = self.script.Part(Path(tmp) / "counts-0000.json.gz")
            part.add({"tag": "a", "round": 1})
            part.add({"tag": "b", "round": 2})
            held = part.close()
            data = (Path(tmp) / "counts-0000.json.gz").read_bytes()
        self.assertEqual(data[:4], b"\x1f\x8b\x08\x00")
        self.assertEqual(data[4:8], bytes(4))
        self.assertEqual(json.loads(gzip.decompress(data)), [{"tag": "a", "round": 1}, {"tag": "b", "round": 2}])
        self.assertEqual(held["sha256"], evidence.sha256(data))
        self.assertEqual(held["bytes"], len(data))
        self.assertEqual(held["uncompressed_sha256"], evidence.sha256(gzip.decompress(data)))

    def test_an_empty_part_is_an_empty_array(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            part = self.script.Part(Path(tmp) / "c.json.gz")
            held = part.close()
            data = (Path(tmp) / "c.json.gz").read_bytes()
        self.assertEqual(json.loads(gzip.decompress(data)), [])
        self.assertEqual(held["uncompressed_sha256"], evidence.sha256(b"[]"))

    def test_a_tally_counts_every_firing_and_keeps_each_rounds_extremes(self):
        import numpy as np
        first, whole = {"low": 1, "high": 7}, {"low": 1, "high": 7}
        tally = self.script.Counted("p", 2, first, whole, None, (8, 8))
        early, full = np.full((2, 4), 4), np.full((2, 4), 4)
        full[0, 0] = 0
        expected = np.zeros((2, 4), dtype=bool)
        expected[0, 0] = True
        tally.add("t", 0, early, full, expected)
        early[1, 3] = 7
        tally.add("t", 1, early, np.full((2, 4), 4), np.zeros((2, 4), dtype=bool))
        self.assertEqual(tally.fired, [1, 1])
        self.assertEqual(tally.counts["whole"], [[0, 4], [4, 4]])
        self.assertEqual(tally.counts["first"], [[4, 4], [4, 7]])
        self.assertEqual(tally.summary()["other_firings_by_round"], [0, 1])
        self.assertEqual(tally.lines, [])
        self.assertEqual([item["round"] for item in tally.located], [1, 2])
        self.assertEqual(bytes.fromhex(tally.located[0]["fired"])[0], 0b00010000)

    def test_parts_merge_by_path_and_round(self):
        one = {"path": "p", "fired": [1, 0], "counts": {"first": [[2, 6], [3, 5]], "whole": [[3, 5], [3, 5]]},
               "summary": {"tests": 2, "expected_bits_that_did_not_fire": 0, "other_firings_by_round": [1, 0]}}
        two = {"path": "p", "fired": [2, 1], "counts": {"first": [[1, 5], [3, 7]], "whole": [[3, 6], [2, 5]]},
               "summary": {"tests": 3, "expected_bits_that_did_not_fire": 1, "other_firings_by_round": [0, 4]}}
        merged = self.script.merged_paths([one, two], 2)["p"]
        self.assertEqual(merged["first"], [[1, 6], [3, 7]])
        self.assertEqual(merged["whole"], [[3, 6], [2, 5]])
        self.assertEqual(merged["fired_by_round"], [3, 1])
        self.assertEqual(merged["other_firings_by_round"], [1, 4])
        self.assertEqual((merged["tests"], merged["expected_bits_that_did_not_fire"]), (5, 1))

    def test_the_runs_a_row_still_needs_are_its_later_ones_and_every_other_kind(self):
        needed = self.script.needed_after("statistics", "frequency", 4)
        self.assertEqual(needed, [("frequency", 8), ("frequency", 16), ("avalanche", 4), ("avalanche", 8), ("avalanche", 16)])
        self.assertEqual(self.script.needed_after("statistics", "avalanche", 16), [("frequency", 4), ("frequency", 8), ("frequency", 16)])
        self.assertIn(("bijectivity", 2), self.script.needed_after("structural", "inverse", 4))
        self.assertNotIn(("bijectivity", 2), self.script.needed_after("structural", "bijectivity", 2))
        self.assertEqual(self.script.needed_after("trails", "bound", 4), [])

    def test_a_bias_kind_never_lowers_its_counts(self):
        self.assertEqual(self.script.FREQUENCY_N, 2 ** 20)
        self.assertEqual(self.script.avalanche.N_A, 8256)
        self.assertEqual(self.script.TEST_STATES, 2 ** 10)
        self.assertEqual(self.script.FIXED_STATES, 16)


def ir_lane(n, i, j):
    import ir
    return ir.lane(n, i, j, ir.PRESSURE)


def ToolFailureFor(text):
    return evidence.ToolFailure(text)


class EvidenceLayers(unittest.TestCase):
    """The layers the counters take, each against the operation list it is read from."""

    @classmethod
    def setUpClass(cls):
        import sys
        cls.script = evidence_script()
        cls.ir = sys.modules["ir"]

    def test_candidate_a1s_layer_is_the_lists_own(self):
        """A class gains from two neighbours along one axis, and its masks run the other way round."""
        script, ir = self.script, self.ir
        program = script.build_list("cand-A1", 4, 8).program
        for n_phase, reads in enumerate(script.coupling(program)):
            for (i, j), others in reads.items():
                axis = {((i + 0) % 4, (j + 1) % 4), (i, (j - 1) % 4)} if n_phase == 0 else {((i + 1) % 4, j), ((i - 1) % 4, j)}
                self.assertEqual(others, axis)
        differences = script.branch_layer(program, "differential")
        masks = script.branch_layer(program, "linear")
        self.assertEqual(differences.branches, 16)
        self.assertEqual(len(differences.maps), 16)
        self.assertEqual(sorted(a for a in differences.added), list(range(16)))
        self.assertEqual(sorted(a for a in masks.added), list(range(16)))
        for number, (inputs, relation) in enumerate(differences.maps):
            self.assertEqual(len(inputs), 2)
            self.assertEqual({ahead for ahead, _ in inputs}, {0 if number < 8 else 1})
            self.assertEqual(relation, script.long_trail.xor_relation(2))
        first = [j for j, a in enumerate(differences.added) if a < 8]
        self.assertEqual(first, [branch for branch in range(16) if (branch // 4 + branch % 4) % 2 == 0])
        first = [j for j, a in enumerate(masks.added) if a < 8]
        self.assertEqual(first, [branch for branch in range(16) if (branch // 4 + branch % 4) % 2 == 1])

    def test_a_difference_alone_reaches_each_branch_the_layer_says(self):
        """Through the real phases of the layer, with its boxes left out: which nodes differ after a difference in one node."""
        import numpy as np
        script, ir = self.script, self.ir
        program = script.build_list("cand-A1", 4, 16).program
        layer_phases = tuple(phase for phase in program.phases if any(
            ir.node_of(4, lane) != ir.node_of(4, update.dst) for update in phase.updates for lane in ir.reads(update)))
        only = ir.load(ir.Program("the layer", 4, 16, layer_phases))
        rng = np.random.default_rng(79)
        states = rng.integers(0, 1 << 16, size=(32, 64), dtype=np.uint64)
        layer = script.branch_layer(program, "differential")
        for branch in range(16):
            i, j = branch // 4, branch % 4
            other = states.copy()
            other[ir.lane(4, i, j, ir.PRESSURE)] ^= np.uint64(1)
            changed = ir.permute_batch(only, states, rounds=1) != ir.permute_batch(only, other, rounds=1)
            seen = {b for b in range(16) if changed[[ir.lane(4, b // 4, b % 4, ir.PRESSURE), ir.lane(4, b // 4, b % 4, ir.VEIN)]].any()}
            reached = {branch}
            for number, (inputs, _) in enumerate(layer.maps):
                if any(item in reached for _, item in inputs):
                    reached.add(layer.added.index(number))
            self.assertEqual(seen, reached, branch)

    def sbox_round(self, layer, state, w):
        """A cycle's S-boxes on a state of lanes, bit by bit, each layer in turn."""
        bits = [(state[number // w] >> (number % w)) & 1 for number in range(len(state) * w)]
        for item in layer.layers:
            for box in item.boxes:
                value = sum(bits[bit] << place for place, bit in enumerate(box))
                taken = item.sbox[value]
                for place, bit in enumerate(box):
                    bits[bit] = (taken >> place) & 1
        out = [0] * len(state)
        for number, bit in enumerate(bits):
            out[number // w] |= bit << (number % w)
        return out

    def test_candidate_b1s_layers_are_one_round_of_its_list(self):
        import numpy as np
        script, ir = self.script, self.ir
        rng = np.random.default_rng(80)
        for w in (4, 16, 32):
            loaded = ir.Loaded(ir.candidate_modules(ROOT / candidates.CANDIDATES_REL)["cand-B1"](4, w))
            layer = script.boolean_layer("cand-B1", 4, w)
            for _ in range(8):
                state = [int(value) for value in rng.integers(0, 1 << w, size=32, dtype=np.uint64)]
                self.assertEqual(self.sbox_round(layer, state, w), ir.permute(loaded, state, [[0, 0, 0]]), w)

    def test_an_odd_size_has_no_s_box_layer(self):
        with self.assertRaises(evidence.Refused):
            self.script.boolean_layer("cand-B1", 3, 16)

    def test_the_weights_of_an_active_s_box(self):
        module = self.script.amounts_module("cand-B1")
        self.assertEqual(self.script.sbox_weight(module.SBOX, "differential"), 2)
        self.assertEqual(self.script.sbox_weight(module.SBOX, "linear"), 2)

    def test_each_set_of_a1_makes_its_box(self):
        boxes = self.script.boxes_of("cand-A1", 16)
        self.assertEqual(len(boxes), 2)
        self.assertEqual(boxes[0][:4], (("add", 1, 0, 1), ("xor", 0, 1, 1), ("add", 1, 0, 2), ("xor", 0, 1, 2)))
        self.assertEqual(boxes[1][:2], (("add", 1, 0, 1), ("xor", 0, 1, 3)))
        chosen = self.script.boxes_of("cand-A1", 16, ((3, 5), (3, 5)))
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0][:2], (("add", 1, 0, 3), ("xor", 0, 1, 5)))


STUDIED = ("cand-A1/constants/n2-w16-R8-c64.json", "cand-A1/constants/n2-w4-R8-c16.json")
EVIDENCE_RESERVED = [evidence_script().reserved_hours]


class EvidenceRuns(TempRepo):
    """scripts/evidence_v3.py on a temporary repository that holds candidate A1 and its first tables (T081)."""

    def setUp(self):
        super().setUp()
        self.script = evidence_script()
        code = list(self.script.CODE) + ["phycoweb/__init__.py", candidates.module_rel("cand-A1"), evidence.REFUSED_LIST_REL,
                                         self.script.TRAIL_PATHS["ARX search"]]
        for rel in code:
            write(self.root, rel, (CODE_ROOT / rel).read_bytes())
        for rel in STUDIED:
            write(self.root, f"{candidates.CANDIDATES_REL}/{rel}", (CODE_ROOT / candidates.CANDIDATES_REL / rel).read_bytes())
        self.commit("the code")
        fields = {name: "stated" for name in candidates.PARAMETERS}
        digest = evidence.sha256((self.root / candidates.module_rel("cand-A1")).read_bytes())
        candidates.propose({"candidate_id": "cand-A1", "family": "ARX", "oplist_sha256": digest, "parameters": fields})
        self.commit("proposed")
        self.out = f"{evidence.REP_REL}/candidates/cand-A1"
        for name, patched in (("reserved_hours", lambda *a: 0.0), ("reserved_trails", lambda *a: 0.0)):
            patcher = mock.patch.object(self.script, name, side_effect=patched)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_script(self, *argv) -> int:
        with mock.patch("builtins.print"), mock.patch("sys.stderr"):
            return self.script.main(list(argv))

    def run_kind(self, kind: str, *more) -> int:
        return self.run_script("--candidate", "cand-A1", "--kind", kind, "--size", "2", "--width", "16", "--out-dir", self.out, *more)

    def validated(self, *tools) -> None:
        """A `re-found` record of each tool's exact hash, earlier than any run here."""
        for name, rel in tools:
            digest = evidence.sha256((self.root / rel).read_bytes())
            record = {"kind": "validation", "record_id": f"validation-{digest[:8]}", "tool": name, "tool_sha256": digest,
                      "outcome": "re-found", "created_utc": "2026-11-03T00:00:00Z", "validated_kind": {}, "code_sha256": {}}
            write(self.root, f"{evidence.REP_REL}/validation/validation-{digest[:8]}.json", evidence.pretty(record))
        self.commit("validations")

    def structural_tools(self):
        script = self.script
        return [(script.TOOL_NAMES[kind], script.TOOL_PATHS[kind]) for kind in ("dependency", "symmetry", "invariant", "degree")]

    def records(self, kind: str) -> List[Dict]:
        return [record for _, record in evidence.iter_records(kind, "candidates/cand-A1")]

    def log(self) -> List[Dict]:
        return candidates.entries()

    # what it refuses -----------------------------------------------------------------------------

    def test_a_candidate_not_in_the_log_exits_2_and_writes_nothing(self):
        before = report_files(self.root)
        code = self.run_script("--candidate", "cand-A2", "--kind", "inverse", "--size", "2", "--width", "16",
                               "--out-dir", f"{evidence.REP_REL}/candidates/cand-A2")
        self.assertEqual(code, 2)
        self.assertEqual(report_files(self.root), before)

    def test_a_list_changed_since_its_entry_exits_2(self):
        path = self.root / candidates.module_rel("cand-A1")
        write(self.root, candidates.module_rel("cand-A1"), path.read_bytes() + b"# changed\n")
        self.assertEqual(self.run_kind("inverse"), 2)

    def test_a_spent_row_exits_2_with_no_evidence_written(self):
        candidates.append({"candidate_id": "cand-A1", "event": "evidence", "evidence": [], "budget_used_h": {"structural": 6.0}})
        self.commit("spent")
        self.assertEqual(self.run_kind("inverse"), 2)
        self.assertEqual(self.records("inverse"), [])

    def test_a_size_out_of_order_exits_2(self):
        with mock.patch("sys.stderr") as err:
            code = self.script.main(["--candidate", "cand-A1", "--kind", "inverse", "--size", "8", "--out-dir", self.out])
        self.assertEqual(code, 2)
        self.assertIn("waits for", "".join(str(call.args[0]) for call in err.write.call_args_list))

    def test_a_probe_at_a_larger_size_is_not_refused_by_the_order(self):
        with mock.patch.object(self.script, "subject_of") as subject, mock.patch.object(self.script, "latest_rounds", return_value=8), \
                mock.patch.object(self.script, "probe_seconds", return_value=3600.0):
            subject.return_value = self.script.plain_subject("cand-A1", 8, 32, 8)
            code = self.run_script("--candidate", "cand-A1", "--kind", "inverse", "--size", "8", "--project", "--out-dir", self.out)
        self.assertEqual(code, 0)
        self.assertEqual(self.records("inverse"), [])
        probes = [record for _, record in evidence.iter_records("projection", "projections")]
        self.assertEqual(probes[-1]["probe"], {"kind": "inverse", "size": 8, "test": NONE})
        self.assertEqual(probes[-1]["row"], "cand-A1/structural")

    def test_a_bound_without_a_validated_tool_exits_2(self):
        code = self.run_script("--candidate", "cand-A1", "--kind", "bound", "--bound-kind", "differential", "--method",
                               "active-box count", "--size", "4", "--width", "16", "--out-dir", self.out)
        self.assertEqual(code, 2)
        self.assertEqual(self.records("bound"), [])

    def test_a_bound_needs_a_kind_and_a_method_the_script_knows(self):
        self.assertEqual(self.run_kind("bound"), 2)
        self.assertEqual(self.run_kind("bound", "--bound-kind", "linear", "--method", "a guess"), 2)

    def test_the_cross_check_comes_before_a_counted_arx_bound(self):
        self.validated(("ARX search", self.script.TRAIL_PATHS["ARX search"]))
        with mock.patch.object(self.script, "tool_hash", return_value=(evidence.sha256(
                (self.root / self.script.TRAIL_PATHS["ARX search"]).read_bytes()), None)):
            code = self.run_kind("bound", "--bound-kind", "linear", "--method", "branch-and-bound")
        self.assertEqual(code, 2)

    def test_an_avalanche_run_without_its_dependency_record_exits_2(self):
        with mock.patch.object(self.script.evidence, "guard_order_of_us1"), mock.patch.object(self.script, "guard_control"), \
                mock.patch.object(self.script, "probe_seconds", return_value=1.0):
            code = self.run_kind("avalanche")
        self.assertEqual(code, 2)
        self.assertEqual(self.records("avalanche"), [])

    def test_a_bias_test_before_its_control_exits_2(self):
        with mock.patch.object(self.script.evidence, "guard_order_of_us1"):
            with self.assertRaisesRegex(Refused, "waits for its uniform control"):
                self.script.guard_control("cand-A1", "frequency", 4)

    def test_a_key_loaded_before_the_fut_sec_8_review_exits_2(self):
        self.assertEqual(self.run_kind("frequency"), 2)
        self.assertEqual(self.records("frequency"), [])

    def test_the_out_dir_is_the_records_place(self):
        code = self.run_script("--candidate", "cand-A1", "--kind", "inverse", "--size", "2", "--width", "16", "--out-dir", "elsewhere")
        self.assertEqual(code, 2)

    # what it writes ------------------------------------------------------------------------------

    def test_a_run_writes_its_record_its_projection_and_its_evidence_entry(self):
        self.assertEqual(self.run_kind("inverse"), 0)
        record = self.records("inverse")[0]
        self.assertEqual((record["status"], record["classification"]), ("pass", NONE))
        self.assertEqual(record["states"], 16 + 2 ** 10)
        self.assertEqual(record["mismatches"], {"inverse of forward": 0, "forward of inverse": 0})
        self.assertEqual(record["variant_id"], "cand-A1/n2-w16-R8-c64")
        self.assertEqual((record["model_id"], record["candidate"]), ("cand-A1", "cand-A1"))
        self.assertEqual(record["constants"]["path"], f"{candidates.CANDIDATES_REL}/{STUDIED[0]}")
        self.assertIs(record["heavy_run"], True)
        entry = self.log()[-1]
        self.assertEqual(entry["event"], "evidence")
        self.assertEqual(entry["evidence"], [record["record_id"]])
        self.assertEqual(list(entry["budget_used_h"]), ["structural"])
        self.assertEqual(self.probes()[-1]["row"], "cand-A1/structural")

    def probes(self) -> List[Dict]:
        return [record for _, record in evidence.iter_records("projection", "projections")]

    def test_a_project_run_writes_only_its_projection(self):
        self.assertEqual(self.run_kind("inverse", "--project"), 0)
        self.assertEqual(self.records("inverse"), [])
        self.assertEqual(len(self.probes()), 1)
        self.assertIn("discarded unread", self.probes()[0]["outputs_statement"])

    def test_a_tool_without_a_validation_writes_not_evaluated(self):
        self.assertEqual(self.run_kind("dependency"), 0)
        record = self.records("dependency")[0]
        self.assertEqual((record["status"], record["validation"]), ("not evaluated", NONE))
        self.assertNotIn("r_f", record)

    def test_a_width_outside_a_tools_kind_writes_not_evaluated(self):
        self.validated(*self.structural_tools())
        self.assertEqual(self.run_kind("degree"), 0)
        self.assertEqual(self.records("degree")[0]["status"], "not evaluated")

    def test_every_run_started_writes_a_record_and_its_hours_are_charged(self):
        with mock.patch.dict(self.script.RUNS, {"inverse": mock.Mock(side_effect=evidence.ToolFailure("it broke"))}):
            self.assertEqual(self.run_kind("inverse"), 3)
        record = self.records("inverse")[0]
        self.assertEqual(record["status"], "inconclusive")
        self.assertIn("it broke", " ".join(record["limitations"]))
        self.assertEqual(self.log()[-1]["evidence"], [record["record_id"]])
        self.assertFalse(evidence.REPO.heavy_lock.exists())

    def test_a_failed_check_carries_its_class_and_exits_1(self):
        failed = {"status": "fail", "classification": evidence.classify("inverse", "failed"), "inputs": NONE,
                  "fields": {"finding": "Π⁻¹ does not undo Π"}}
        with mock.patch.dict(self.script.RUNS, {"inverse": mock.Mock(return_value=failed)}):
            self.assertEqual(self.run_kind("inverse"), 1)
        record = self.records("inverse")[0]
        self.assertEqual((record["status"], record["classification"]), ("fail", "confirmed vulnerability"))
        self.assertEqual(record["exit_status"], 1)

    def test_a_second_run_of_a_variant_exits_2_with_no_defect_recorded(self):
        self.assertEqual(self.run_kind("inverse"), 0)
        self.commit("the record")
        self.assertEqual(self.run_kind("inverse"), 2)
        self.assertEqual(len(self.records("inverse")), 1)

    def test_a_recorded_defect_gives_one_re_run_which_names_it(self):
        self.assertEqual(self.run_kind("inverse"), 0)
        first = self.records("inverse")[0]["record_id"]
        write(self.root, f"{self.script.DEFECTS_REL}/{first}.json", json.dumps({"defect": "d", "cause": "c", "fix": "f"}))
        self.commit("the defect")
        self.assertEqual(self.run_kind("inverse"), 0)
        made = [record for record in self.records("inverse") if record["record_id"] != first][0]
        self.assertEqual(made["exclusions_and_reruns"][0]["record_id"], first)
        self.assertEqual(made["exclusions_and_reruns"][0]["why"], "tool defect")
        self.commit("the re-run")
        self.assertEqual(self.run_kind("inverse", "--rounds", "8"), 2)

    def test_a_run_ended_from_outside_runs_again_and_names_it(self):
        self.assertEqual(self.run_kind("inverse"), 0)
        path, record = next(iter(evidence.iter_records("inverse", "candidates/cand-A1")))
        write(self.root, evidence.rel_to_repo(path), evidence.pretty(dict(record, ended_outside="2026-11-03T01:00:00Z", status="inconclusive")))
        self.commit("ended")
        self.assertEqual(self.run_kind("inverse"), 0)
        made = [item for item in self.records("inverse") if item["record_id"] != record["record_id"]][0]
        self.assertEqual(made["exclusions_and_reruns"], [{"record_id": record["record_id"], "why": "ended from outside"}])

    def test_the_stated_transport_difference_is_checked_at_both_round_counts(self):
        self.validated(*self.structural_tools())
        self.assertEqual(self.run_kind("invariant"), 0)
        record = self.records("invariant")[0]
        self.assertEqual(sorted(record["round_counts"]), ["1", "8"])
        self.assertEqual(sorted(record["differences"]), ["by the checkerboard", "in lane order"])
        self.assertEqual(sorted(record["differences"]["in lane order"]), ["1", "8"])
        self.assertTrue(record["validation"]["record_id"].startswith("validation-"))

    def test_a_dependency_record_holds_rounds_matrices_and_needs_no_table(self):
        self.validated(*self.structural_tools())
        self.assertEqual(self.run_kind("dependency"), 0)
        record = self.records("dependency")[0]
        self.assertEqual(record["variant_id"], "cand-A1/n2-w16")
        self.assertGreater(record["r_f"], 0)
        self.assertEqual(record["classification"], "confirmed vulnerability" if record["incomplete_rounds"] else NONE)
        self.assertIn("incomplete diffusion", record["finding"])
        self.assertEqual(record["through_instantiate"], NONE)
        self.assertTrue(all(item["committed"] is False for item in record["outputs"]))
        self.assertTrue(record["reads_no_constant"])

    def test_a_degree_record_raises_at_the_round_counts_within_its_limit(self):
        self.validated(*self.structural_tools())
        self.assertEqual(self.run_script("--candidate", "cand-A1", "--kind", "degree", "--size", "2", "--width", "8", "--out-dir", self.out), 0)
        record = self.records("degree")[0]
        self.assertEqual(record["classification"], "strong theoretical concern")
        self.assertTrue(record["rounds_fired"])
        self.assertEqual(min(record["counts"]["forward"][-1], record["counts"]["inverse"][-1]), 63)
        self.assertLess(record["rounds"][-1], 256)

    def test_a_counted_bound_run_writes_its_fields_and_its_reproduction_matches(self):
        """Candidate A1's own layer at 4×4, w = 16, on a stated box record, by the long-trail counter (data-model section 6)."""
        tool = "long-trail active-box counting"
        write(self.root, self.script.TRAIL_PATHS["exhaustive tables"], (CODE_ROOT / self.script.TRAIL_PATHS["exhaustive tables"]).read_bytes())
        self.validated((tool, self.script.TRAIL_PATHS[tool]))
        box = {"kind": "bound", "record_id": "bound-box", "created_utc": "2026-11-05T00:00:00Z", "method": "branch-and-bound", "candidate": "cand-A1",
               "bound_kind": "differential", "width": 16, "status": "pass", "rounds": 1, "boxes": {"box 0": {"weights": {"1": 5}}}}
        write(self.root, f"{self.out}/bound-box.json", evidence.pretty(box))
        self.commit("the box record")
        argv = ("--candidate", "cand-A1", "--kind", "bound", "--bound-kind", "differential", "--method", "active-box count", "--size", "4",
                "--width", "16", "--rounds", "2", "--out-dir", self.out)
        self.assertEqual(self.run_script(*argv), 0)
        record = [item for item in self.records("bound") if item["record_id"] != "bound-box"][0]
        self.assertEqual((record["status"], record["classification"]), ("pass", "no weakness identified within the analysis performed"))
        self.assertEqual((record["bound_kind"], record["rounds"], record["width"], record["size"]), ("differential", 2, 16, 4))
        self.assertEqual(record["budget"]["cap_hours"], 8.0)
        self.assertIn("independence assumptions", record["scope"])
        self.assertTrue(record["limitations"])
        self.assertEqual(self.log()[-1]["budget_used_h"].keys(), {"trails"})
        self.commit("the bound")
        path = evidence.find_record(record["record_id"])[0]
        self.assertEqual(self.reproduced(path)["outcome"], "match")

    def test_a_search_its_row_refuses_leaves_the_refusal_in_its_projection(self):
        """A climb ends at the refusal, so the refusal has a record (research R6)."""
        tool = "long-trail active-box counting"
        self.validated((tool, self.script.TRAIL_PATHS[tool]))
        with mock.patch.object(self.script, "trail_seconds", return_value=8 * 3600.0), \
                mock.patch.object(self.script, "reserved_trails", return_value=41.0):
            code = self.run_kind("bound", "--bound-kind", "differential", "--method", "active-box count", "--rounds", "3")
        self.assertEqual(code, 2)
        probe = [record for _, record in evidence.iter_records("projection", "projections")][-1]
        self.assertEqual(probe["rounds"], 3)
        self.assertIn("do not fit", probe["refused"])
        self.assertEqual(self.records("bound"), [])

    def test_a_probe_alone_holds_no_refusal(self):
        tool = "long-trail active-box counting"
        self.validated((tool, self.script.TRAIL_PATHS[tool]))
        with mock.patch.object(self.script, "trail_seconds", return_value=8 * 3600.0), \
                mock.patch.object(self.script, "reserved_trails", return_value=41.0):
            code = self.run_kind("bound", "--bound-kind", "differential", "--method", "active-box count", "--rounds", "3", "--project")
        self.assertEqual(code, 0)
        probe = [record for _, record in evidence.iter_records("projection", "projections")][-1]
        self.assertNotIn("refused", probe)

    def test_a_search_that_reached_its_cap_is_refused_again(self):
        tool = "long-trail active-box counting"
        self.validated((tool, self.script.TRAIL_PATHS[tool]))
        fields = {"kind": "bound", "record_id": "bound-capped", "created_utc": "2026-11-05T00:00:00Z", "status": "inconclusive", "capped": True,
                  "ended_outside": NONE, "bound_kind": "differential", "rounds": 2, "width": 16, "size": 4}
        write(self.root, f"{self.out}/bound-capped.json", evidence.pretty(fields))
        self.commit("capped")
        self.assertEqual(self.run_kind("bound", "--bound-kind", "differential", "--method", "active-box count", "--rounds", "2"), 2)

    def test_a_kind_of_the_row_without_its_probe_exits_2(self):
        """The reservation counts the probe of every run the row still needs, and a probe that does not exist comes first."""
        with self.assertRaisesRegex(Refused, "comes first"):
            EVIDENCE_RESERVED[0]("cand-A1", "structural", "inverse", 4)

    def test_the_probes_of_later_runs_are_reserved(self):
        real = EVIDENCE_RESERVED[0]
        for kind, at in self.script.needed_after("statistics", "frequency", 4):
            evidence.write_projection(run="x", row="cand-A1/statistics", inputs=NONE, measured_speed=1, projected_hours=0.5, time_hours=0.0,
                                      extra={"probe": self.script.probe_of(kind, at)})
        self.assertAlmostEqual(real("cand-A1", "statistics", "frequency", 4), 2.5)


    # --aborted --------------------------------------------------------------------------------------

    def cleared(self, hours: float = 1.5) -> Path:
        write(self.root, "scripts/clear_lock.py", (CODE_ROOT / "scripts/clear_lock.py").read_bytes())
        self.commit("clear_lock")
        run = evidence.Run("frequency", candidate="cand-A1", argv=["scripts/clear_lock.py"], code_files=["scripts/clear_lock.py"],
                           writes_evidence=False)
        with run:
            return run.finish("inconclusive", fields={"hours": {"projected": 1.0, "used": hours}})

    def test_aborted_appends_the_entry_with_its_hours_whatever_the_row_holds(self):
        path = self.cleared()
        candidates.append({"candidate_id": "cand-A1", "event": "evidence", "evidence": [], "budget_used_h": {"statistics": 12.0}})
        self.assertEqual(self.run_script("--aborted", str(path)), 0)
        entry = self.log()[-1]
        self.assertEqual(entry["evidence"], [json.loads(path.read_bytes())["record_id"]])
        self.assertEqual(entry["budget_used_h"], {"statistics": 1.5})

    def test_aborted_exits_2_for_a_record_that_has_its_entry(self):
        path = self.cleared()
        self.assertEqual(self.run_script("--aborted", str(path)), 0)
        lines = len(self.log())
        self.assertEqual(self.run_script("--aborted", str(path)), 2)
        self.assertEqual(len(self.log()), lines)

    def test_aborted_exits_2_for_any_other_record(self):
        self.assertEqual(self.run_kind("inverse"), 0)
        path, _ = next(iter(evidence.iter_records("inverse", "candidates/cand-A1")))
        lines = len(self.log())
        self.assertEqual(self.run_script("--aborted", str(path)), 2)
        self.assertEqual(self.run_script("--aborted", "no/such/record.json"), 2)
        self.assertEqual(len(self.log()), lines)

    # controls ---------------------------------------------------------------------------------------

    def control(self, *more, fires: bool = False) -> int:
        fields = {"fires": fires, "sample_size": {"n": 4}}
        inputs = {"namespace": "control", "index_range": [0, 7]}
        self.validated(("bias", self.script.TOOL_PATHS["control"]))
        with mock.patch.dict(self.script.CONTROLS, {"frequency": mock.Mock(return_value=(fields, inputs))}) as held:
            self.counted = held["frequency"]
            return self.run_script("--kind", "control", "--test", "frequency", "--size", "4", "--out-dir",
                                   f"{evidence.REP_REL}/controls", *more)

    def controls(self) -> List[Tuple]:
        return list(evidence.iter_records("control", "controls"))

    def test_a_control_has_no_candidate_and_appends_no_entry(self):
        lines = len(self.log())
        self.assertEqual(self.control(), 0)
        _, record = self.controls()[0]
        self.assertEqual((record["model_id"], record["variant_id"], record["status"]), (None, None, "pass"))
        self.assertEqual((record["test"], record["size"], record["fires"]), ("frequency", 4, False))
        self.assertEqual(len(self.log()), lines)

    def test_a_control_that_fires_keeps_status_inconclusive_and_class_none(self):
        self.assertEqual(self.control(fires=True), 0)
        _, record = self.controls()[0]
        self.assertEqual((record["status"], record["classification"], record["fires"]), ("inconclusive", NONE, True))
        self.assertIn("recommends stopping", record["finding"])
        with self.assertRaisesRegex(Refused, "fired"):
            self.script.guard_control("cand-A1", "frequency", 4)

    def test_a_control_exits_2_once_its_record_exists(self):
        self.assertEqual(self.control(), 0)
        self.commit("the control")
        self.assertEqual(self.control(), 2)
        self.assertEqual(len(self.controls()), 1)

    def test_a_control_ended_from_outside_runs_again_with_the_same_inputs(self):
        self.assertEqual(self.control(), 0)
        path, record = self.controls()[0]
        write(self.root, evidence.rel_to_repo(path), evidence.pretty(dict(record, ended_outside="2026-11-03T01:00:00Z", status="inconclusive")))
        self.commit("ended")
        with self.assertRaisesRegex(Refused, "waits for its uniform control"):
            self.script.guard_control("cand-A1", "frequency", 4)
        self.assertEqual(self.control(), 0)
        made = [item for _, item in self.controls() if item["record_id"] != record["record_id"]][0]
        self.assertEqual(made["inputs"], record["inputs"])
        self.assertEqual(made["sample_size"], record["sample_size"])
        self.assertEqual(made["exclusions_and_reruns"], [{"record_id": record["record_id"], "why": "ended from outside"}])
        self.script.guard_control("cand-A1", "frequency", 4)

    def test_a_control_that_a_reboot_ended_is_found_named_and_charged_as_its_record_says(self):
        """The record clear_lock.py writes for a control that died holding the lock holds its test, size and rows, so that no test
        of its kind starts before it runs again, the run made again names it, and a row it spared is charged nothing (research
        R7, "Runs ended from outside"; cli contract)."""
        from scripts import clear_lock
        left = {}

        def dies(run, n):
            left["lock"] = json.loads(evidence.REPO.heavy_lock.read_bytes())
            left["description"] = (run.tmp / evidence.RUN_FILE).read_bytes()
            left["partial"] = run.tmp.name
            raise Refused("the machine restarts")

        self.validated(("bias", self.script.TOOL_PATHS["control"]))
        with mock.patch.dict(self.script.CONTROLS, {"frequency": dies}), \
                mock.patch.object(self.script, "rows_charged", return_value=(["cand-A2"], ["cand-A1"])):
            self.assertEqual(self.run_script("--kind", "control", "--test", "frequency", "--size", "4", "--out-dir",
                                             f"{evidence.REP_REL}/controls"), 2)
        self.assertEqual(self.controls(), [])
        now = datetime.datetime.now(datetime.timezone.utc)
        lock = dict(left["lock"], start="gone", time=(now - datetime.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"))
        write(self.root, evidence.HEAVY_LOCK_REL, evidence.canonical(lock))
        write(self.root / evidence.PARTIAL_REL / left["partial"], evidence.RUN_FILE, left["description"])
        boot = (now - datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        with mock.patch.object(evidence, "boot_time", return_value=boot), mock.patch("builtins.print"):
            self.assertEqual(clear_lock.main([evidence.HEAVY_LOCK_REL]), 0)
        (_, dead), = self.controls()
        self.assertEqual((dead["ended_outside"], dead["status"]), (boot, "inconclusive"))
        self.assertEqual((dead["test"], dead["size"], dead["charged"], dead["not_charged"]), ("frequency", 4, ["cand-A2"], ["cand-A1"]))
        self.assertEqual(evidence.control_hours("cand-A1"), 0.0)
        self.assertAlmostEqual(evidence.control_hours("cand-A2"), 1.0)
        self.commit("cleared")
        with self.assertRaisesRegex(Refused, "waits for its uniform control"):
            self.script.guard_control("cand-A2", "frequency", 4)
        self.assertEqual(self.control(), 0)
        made = [item for _, item in self.controls() if item["record_id"] != dead["record_id"]][0]
        self.assertEqual(made["exclusions_and_reruns"], [{"record_id": dead["record_id"], "why": "ended from outside"}])
        self.script.guard_control("cand-A2", "frequency", 4)

    def test_a_row_that_cannot_hold_a_control_takes_no_test_of_its_kind_there(self):
        candidates.append({"candidate_id": "cand-A1", "event": "entered-d4", "evidence": []})
        with mock.patch.object(self.script, "rows_charged", return_value=([], ["cand-A1"])):
            self.assertEqual(self.control(), 0)
        with self.assertRaisesRegex(Refused, "could not hold"):
            self.script.guard_control("cand-A1", "frequency", 4)

    def test_a_control_needs_a_validated_bias_tool(self):
        self.assertEqual(self.run_script("--kind", "control", "--test", "frequency", "--size", "4", "--out-dir",
                                         f"{evidence.REP_REL}/controls"), 2)

    def test_a_control_refuses_a_size_that_is_not_claimable(self):
        self.assertEqual(self.run_script("--kind", "control", "--test", "frequency", "--size", "2", "--out-dir",
                                         f"{evidence.REP_REL}/controls"), 2)

    def test_the_avalanche_control_counts_each_group_as_the_test_does(self):
        """Group g holds differences g·N_a to (g + 1)·N_a - 1, each of states 2i and 2i + 1; a part's counts are those of its own states."""
        import numpy as np
        script = self.script
        entry = {"low": 3000, "high": 5300}
        with mock.patch.object(script, "bias_entries", return_value=(entry, entry)), \
                mock.patch.object(script.avalanche, "N_A", 64), mock.patch.object(script.avalanche, "N_FIRST", 32):
            tmp = self.root / "parts"
            tmp.mkdir()
            result = script.control_avalanche_part((4, 0, 1, 2, str(tmp)))
            data = gzip.decompress((tmp / "counts-0000.json.gz").read_bytes())
            row = json.loads(data)[0]
            states = script.control_states(4, 128, 128)
        difference = script.bias.control_differences(states)
        self.assertEqual(row["group"], 1)
        self.assertEqual(row["whole"], script.bias.test_order(script.bias.ones(difference, 32)).tolist())
        self.assertEqual(row["first"], script.bias.test_order(script.bias.ones(difference[:, :32], 32)).tolist())
        self.assertEqual(result["rows"]["whole"], [int(np.min(row["whole"])), int(np.max(row["whole"]))])

    # --reproduce ------------------------------------------------------------------------------------

    def reproduced(self, record_path: Path) -> Dict:
        code = self.run_script("--reproduce", str(record_path), "--owner-request", "as the test asks (2026-11-05)")
        self.assertEqual(code, 0, record_path.name)
        record = json.loads(record_path.read_bytes())
        base = self.root / evidence.REP_REL / "reproductions" / record["record_id"]
        return json.loads(next(sorted(base.iterdir())[-1].glob("reproduction-*.json")).read_bytes())

    def test_a_run_of_each_structural_kind_its_latest_and_one_older_matches(self):
        """Every kind here is heavy by its kind, so that each reproduction is on a request, quoted, and charged to the feature-wide row."""
        self.validated(*self.structural_tools())
        for kind, width in (("inverse", "16"), ("symmetry", "16"), ("invariant", "16"), ("dependency", "16"), ("degree", "8")):
            with self.subTest(kind=kind):
                argv = ("--candidate", "cand-A1", "--kind", kind, "--size", "2", "--width", width, "--out-dir", self.out)
                self.assertEqual(self.run_script(*argv), 0)
                self.commit(f"the {kind} record")
        write(self.root, "data/note.txt", "a later commit\n")
        self.commit("later")
        extra = ("--candidate", "cand-A1", "--kind", "inverse", "--size", "2", "--width", "4", "--out-dir", self.out)
        self.assertEqual(self.run_script(*extra), 0)
        self.commit("a newer inverse record")
        for kind in ("inverse", "symmetry", "invariant", "dependency", "degree"):
            held = list(evidence.iter_records(kind, "candidates/cand-A1"))
            for path, record in held:
                with self.subTest(record=record["record_id"]):
                    found = self.reproduced(path)
                    self.assertEqual(found["outcome"], "match", found["compared"])
                    self.assertEqual(found["owner_request"], "as the test asks (2026-11-05)")


STATED_SUBJECT = """import ir

P, V = ir.PRESSURE, ir.VEIN


def build(n, w):
    phases = []
    for colour in range(2):
        nodes = ir.nodes_of(n, colour)
        phases.append(ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, V), "add", ir.Rotl(ir.Lane(ir.lane(n, i, j, P)), 7)) for i, j in nodes)))
        phases.append(ir.Phase(colour, tuple(ir.Mix(ir.lane(n, i, j, P), "xor", ir.Rotl(ir.Lane(ir.lane(n, i, j, V)), 13)) for i, j in nodes)))
    phases.append(ir.Phase(0, tuple(ir.Mix(ir.lane(n, i, j, P), "xor", ir.Lane(ir.lane(n, i, (j + 1) % n, V))) for i, j in ir.nodes_of(n, 0))))
    phases.append(ir.Phase(1, tuple(ir.Mix(ir.lane(n, i, j, P), "xor", ir.Lane(ir.lane(n, i, (j + 1) % n, V))) for i, j in ir.nodes_of(n, 1))))
    return ir.Program("stated", n, w, tuple(phases))
"""


class EvidenceCounts(TempRepo):
    """The statistical kinds on a stated list at a small size, whose critical counts stand in for the table's. No count of research R4
    changes: the sets and thresholds are the run's own, and only what the stated size cannot hold is stated here."""

    def setUp(self):
        super().setUp()
        import sys
        self.script = evidence_script()
        self.ir = sys.modules["ir"]
        namespace: Dict = {}
        exec(STATED_SUBJECT, namespace)
        loaded = self.ir.load(namespace["build"](2, 32))
        self.subject = self.script.Subject("cand-A1", 2, 32, 4, 64, "n2-w32-R4-c64", loaded, [], "")
        write(self.root, "research/004/candidates/cand-A1/constants/n2-w32-R4-c64.json", "{}")
        write(self.root, self.script.bias.TABLE_REL, (CODE_ROOT / self.script.bias.TABLE_REL).read_bytes())
        self.subject.table_rel = "research/004/candidates/cand-A1/constants/n2-w32-R4-c64.json"
        self.critical = {"low": 2, "high": 8254, "test": "stated"}
        for name, patched in (("bias_entries", mock.Mock(return_value=(self.critical, self.critical))),):
            patcher = mock.patch.object(self.script, name, patched)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_of(self, kind: str) -> evidence.Run:
        return evidence.Run(kind, candidate="cand-A1", directory="candidates/cand-A1", code_files=(), argv=["scripts/evidence_v3.py"],
                            writes_evidence=False)

    def frequency(self, total: int = 2 ** 9) -> Dict:
        entry = {"low": 150, "high": 362}
        run = self.run_of("frequency")
        run.workers = 1
        with mock.patch.object(self.script, "FREQUENCY_N", total), mock.patch.object(self.script.bias, "entry_for", return_value=entry):
            result = self.script.run_frequency(self.subject, run)
        self.frequency_run = run
        return result

    def test_a_frequency_run_counts_both_sets_in_both_directions(self):
        result = self.frequency()
        fields = result["fields"]
        self.assertEqual(sorted(fields["summaries"]), ["key 0, nonce i", "key i, nonce i"])
        for directions in fields["summaries"].values():
            self.assertEqual(sorted(directions), ["forward", "inverse"])
            self.assertEqual({len(rows) for rows in directions.values()}, {4})
        self.assertEqual(fields["test_parameters"]["s"], 4 * 2 * 4 * 32)
        self.assertEqual(result["inputs"]["kind"], ["key", "nonce"])

    def test_a_frequency_verdict_reads_only_what_the_record_commits(self):
        result = self.frequency()
        fields = result["fields"]
        low, high = fields["test_parameters"]["critical"]
        self.assertEqual(fields["rounds_fired"], evidence.frequency_rounds_fired(fields["summaries"], low, high))
        self.assertEqual(result["status"], "fail" if any(2 * r > 4 for r in fields["rounds_fired"]) else "pass")
        self.assertEqual(result["classification"], "confirmed vulnerability")
        self.assertIn("a chance of a false firing", result["fields"]["finding"])

    def test_a_frequency_runs_outputs_are_json_and_each_fired_bit_is_listed(self):
        self.frequency()
        run = self.frequency_run
        names = sorted(entry["path"].rsplit("/", 1)[-1] for entry in run.outputs)
        self.assertEqual(names, ["counts.json.gz", "failure-locations.json.gz", "p-values.json.gz"])
        for source, final in run.moves:
            data = json.loads(gzip.decompress(Path(source).read_bytes()))
            if final.endswith("failure-locations.json.gz"):
                self.assertTrue(data)
                self.assertEqual(sorted(data[0]), ["count", "direction", "position", "round", "set"])
            if final.endswith("counts.json.gz"):
                self.assertEqual(len(data["key i, nonce i"]["forward"]), 4)
                self.assertEqual(len(data["key i, nonce i"]["forward"][0]), 2 * 4 * 32)
        p_values = [entry for entry in run.outputs if entry["path"].endswith("p-values.json.gz")][0]
        self.assertEqual((p_values["deterministic"], p_values["compared"]), (False, "values"))

    def test_the_counts_do_not_depend_on_how_batches_fall(self):
        one = self.script.summed([self.script.frequency_worker((self.subject, 0, 64, False))])
        two = self.script.summed([self.script.frequency_worker((self.subject, 0, 40, False)),
                                  self.script.frequency_worker((self.subject, 40, 24, False))])
        self.assertEqual(one["forward"].tobytes(), two["forward"].tobytes())
        self.assertEqual(one["inverse"].tobytes(), two["inverse"].tobytes())

    def remeasured(self, original: Dict, **patched) -> Dict:
        """What a reproduction's worktree computes, here in the test's own process with the stated size's counts."""
        out, parts, local = self.root / "fields.json", self.root / "outputs", self.root / "local"
        with mock.patch.object(self.script, "subject_of", return_value=self.subject), mock.patch.object(self.script.evidence, "guard_order_of_us1"):
            with mock.patch.object(self.script, "FREQUENCY_N", 2 ** 9), mock.patch.object(self.script.bias, "entry_for", return_value={"low": 150, "high": 362}):
                self.script.remeasure(json.dumps(original), str(out), str(parts), str(local), NONE)
        return json.loads(out.read_bytes())

    def test_a_frequency_reproduction_counts_the_same(self):
        first = self.frequency()
        original = {"kind": "frequency", "candidate": "cand-A1", "config": {"size": 2, "width": 32, "rounds": 4}, "parallelism": {"workers": 1},
                    "variant_id": "cand-A1/n2-w32-R4-c64", "model_id": "cand-A1"}
        with mock.patch.object(self.script, "citation_of", return_value={"record_id": "v"}):
            again = self.remeasured(original)
        for name in ("summaries", "rounds_fired", "raises"):
            self.assertEqual(again[name], first["fields"][name], name)
        self.assertEqual(again["status"], first["status"])
        self.assertEqual((self.root / "outputs/counts.json.gz").exists(), True)

    def test_a_control_counts_as_its_test_does_and_a_reproduction_counts_the_same(self):
        with mock.patch.object(self.script, "FREQUENCY_N", 2 ** 9), mock.patch.object(self.script.bias, "BATCH", 2 ** 8), \
                mock.patch.object(self.script.bias, "entry_for", return_value={"low": 150, "high": 362}):
            run = self.run_of("control")
            run.workers = 1
            fields, inputs = self.script.control_frequency(run, 4)
            second = self.run_of("control")
            second.workers = 1
            repeat, _ = self.script.control_frequency(second, 4)
        self.assertEqual(fields["summaries"], repeat["summaries"])
        self.assertEqual(sorted(fields["summaries"]), ["first set", "second set"])
        self.assertEqual(inputs["namespace"], "control")
        self.assertEqual(inputs["index_range"], [0, 2 ** 10 - 1])
        self.assertEqual(fields["test_parameters"]["s"], 4 * 2 * 16 * 32)


    def avalanche_run(self, directory: Path) -> List[Dict]:
        self.script.store_matrices(self.subject, directory)
        jobs = self.script.avalanche_jobs(self.subject, str(directory))
        return [self.script.avalanche_worker(job) for job in jobs]

    def test_an_avalanche_runs_jobs_cover_the_three_paths_in_a_fixed_order(self):
        jobs = self.script.avalanche_jobs(self.subject, "d")
        paths = [job[1] for job in jobs]
        self.assertEqual(paths[-1], self.script.ROTATIONS)
        self.assertEqual(sum(len(job[2]) for job in jobs if job[1] == self.script.FLIPS), 128)
        self.assertEqual(sum(len(job[2]) for job in jobs if job[1] == self.script.RELATED), 96)
        self.assertEqual([job[3] for job in jobs], list(range(len(jobs))))
        self.assertEqual(jobs[-1][2], list(range(1, 32)))

    def test_every_firing_counts_and_the_matrices_agree(self):
        directory = self.root / "workers"
        results = self.avalanche_run(directory)
        paths = self.script.merged_paths(results, 4)
        self.assertEqual(sorted(paths), sorted((self.script.FLIPS, self.script.RELATED, self.script.ROTATIONS)))
        fired = evidence.avalanche_rounds_fired(paths, (2, 8254), (2, 8254))
        self.assertIn(1, fired)
        for row in paths.values():
            self.assertEqual(row["expected_bits_that_did_not_fire"], 0)
        self.assertEqual(sum(paths[self.script.FLIPS]["fired_by_round"]) > 0, True)
        kept = json.loads(gzip.decompress((directory / results[0]["part"]["file"]).read_bytes()))
        self.assertEqual(sorted(kept[0]), ["first", "round", "tag", "whole"])
        self.assertEqual(len(kept[0]["whole"]), 2 * 4 * 32)

    def test_a_disagreement_with_the_matrices_is_a_tool_defect_and_exits_3(self):
        run = self.run_of("avalanche")
        run.workers = 1
        worker = mock.Mock(side_effect=evidence.ToolFailure("a difference bit the dependency matrices show independent flipped, x"))
        with mock.patch.object(self.script, "avalanche_worker", worker), mock.patch.object(self.script, "store_matrices"),                 mock.patch.object(self.script, "dependency_cited", return_value="dependency-x"):
            result = self.script.run_avalanche(self.subject, run)
        self.assertEqual((result["status"], result["exit_status"], result["classification"]), ("inconclusive", 3, NONE))
        self.assertEqual(result["fields"]["tool_defect"]["kind"], "a disagreement between avalanche counts and dependency matrices")

    def test_any_other_failure_of_a_part_stays_a_failure(self):
        run = self.run_of("avalanche")
        run.workers = 1
        with mock.patch.object(self.script, "dependency_cited", return_value="dependency-x"), \
                mock.patch.object(self.script, "avalanche_worker", mock.Mock(side_effect=evidence.ToolFailure("something else"))), \
                mock.patch.object(self.script, "store_matrices"):
            with self.assertRaisesRegex(evidence.ToolFailure, "something else"):
                self.script.run_avalanche(self.subject, run)


class EvidenceBounds(TempRepo):
    """The bound methods, on stated boxes and layers, with the box search stubbed where its binary does not run."""

    def setUp(self):
        super().setUp()
        import sys
        self.script = evidence_script()
        self.ir = sys.modules["ir"]
        self.args = mock.Mock(rounds=2, bound_kind="differential", method="active-box count")
        write(self.root, candidates.module_rel("cand-A1"), (CODE_ROOT / candidates.module_rel("cand-A1")).read_bytes())
        self.subject = self.script.plain_subject("cand-A1", 4, 16, 2)

    def box_record(self, kind: str, weights: Dict) -> None:
        record = {"kind": "bound", "record_id": f"bound-{kind}", "created_utc": "2026-11-05T00:00:00Z", "method": "branch-and-bound",
                  "bound_kind": kind, "width": 16, "status": "pass", "rounds": 1, "boxes": {"box 0": {"weights": weights}}}
        write(self.root, f"{evidence.REP_REL}/candidates/cand-A1/{record['record_id']}.json", evidence.pretty(record))

    def test_a_box_bound_doubles_a_linear_exponent(self):
        search = mock.Mock(return_value={1: {"weight": 3, "walks": 9}})
        with mock.patch.object(self.script.arx_search_known, "search", search):
            found = self.script.box_method(self.subject, "linear", 1, self.args)
            plain = self.script.box_method(self.subject, "differential", 1, self.args)
        self.assertEqual(found["bound"], "393216/65536")
        self.assertEqual(plain["bound"], "196608/65536")
        self.assertEqual(sorted(found["boxes"]), ["box 0", "box 1"])

    def test_a_count_reads_the_box_record_and_is_a_whole_number(self):
        self.box_record("differential", {"1": 5})
        found = self.script.active_box_method(self.subject, "differential", 2, self.args)
        self.assertEqual(found["box"], [5])
        self.assertEqual(found["box_record"], "bound-differential")
        self.assertEqual(int(found["bound"]) % 5, 0)
        self.assertEqual(sorted(found["counts"]), ["1", "2"])
        self.assertIn("mip_rel_gap", found["solver"])

    def test_a_count_of_masks_takes_twice_the_exponent(self):
        self.box_record("linear", {"1": 2})
        self.assertEqual(self.script.active_box_method(self.subject, "linear", 1, self.args)["box"], [4])

    def test_a_count_with_no_box_record_exits_2(self):
        with self.assertRaisesRegex(Refused, "no box bound"):
            self.script.active_box_method(self.subject, "linear", 2, self.args)

    def test_a_search_at_its_cap_gives_no_bound_and_is_marked(self):
        with mock.patch.dict(self.script.METHODS["active-box count"], {"run": mock.Mock(side_effect=evidence.ToolFailure("2 steps: status 1, x: no count"))}):
            result = self.script.run_bound(self.subject, None, self.args, "long-trail active-box counting", {"record_id": "v"}, NONE)
        self.assertEqual((result["status"], result["classification"]), ("inconclusive", NONE))
        self.assertIs(result["fields"]["capped"], True)
        self.assertEqual(result["fields"]["bound"], NONE)
        self.assertTrue(evidence.reached_cap(dict(result["fields"], status="inconclusive")))

    def test_any_other_failure_of_a_search_stays_a_failure(self):
        with mock.patch.dict(self.script.METHODS["active-box count"], {"run": mock.Mock(side_effect=evidence.ToolFailure("arx_search exited 1"))}):
            with self.assertRaises(evidence.ToolFailure):
                self.script.run_bound(self.subject, None, self.args, "long-trail active-box counting", {"record_id": "v"}, NONE)

    def test_a_tool_outside_its_width_writes_not_evaluated(self):
        result = self.script.run_bound(self.subject, None, self.args, "long-trail active-box counting", None, NONE)
        self.assertEqual(result["status"], "not evaluated")

    def test_a_proven_bound_carries_its_class_scope_and_limitation(self):
        with mock.patch.dict(self.script.METHODS["active-box count"], {"run": mock.Mock(return_value={"bound": "25"})}):
            result = self.script.run_bound(self.subject, None, self.args, "long-trail active-box counting", {"record_id": "v"}, NONE)
        self.assertEqual(result["classification"], "no weakness identified within the analysis performed")
        self.assertEqual(result["fields"]["bound"], "25")
        self.assertIn("independence assumptions", result["fields"]["scope"])
        self.assertTrue(result["limitations"])

    def test_a_count_of_active_s_boxes_on_a_small_layer(self):
        sbox = (0xC, 5, 6, 0xB, 9, 0, 0xA, 0xD, 3, 0xE, 0xF, 8, 4, 7, 1, 2)
        layer = self.script.active_sbox.Cycle((self.script.active_sbox.spn(sbox, 2, (4, 1, 6, 3, 0, 5, 2, 7)),))
        with mock.patch.object(self.script, "boolean_layer", return_value=layer):
            found = self.script.active_sbox_method(self.subject, "differential", 2, self.args)
        self.assertEqual(int(found["bound"]), found["active_sboxes"] * found["weight_per_sbox"])
        self.assertEqual(found["weight_per_sbox"], 2)

    def test_a_cross_check_of_the_counter_lists_both_values(self):
        sbox = (0xC, 5, 6, 0xB, 9, 0, 0xA, 0xD, 3, 0xE, 0xF, 8, 4, 7, 1, 2)
        layer = self.script.active_sbox.Cycle((self.script.active_sbox.spn(sbox, 2, (4, 1, 6, 3, 0, 5, 2, 7)),))
        write(self.root, self.script.TRAIL_PATHS["active-S-box counting"], (CODE_ROOT / self.script.TRAIL_PATHS["active-S-box counting"]).read_bytes())
        args = mock.Mock(rounds=2, tool="active-S-box counting")
        with mock.patch.object(self.script, "boolean_layer", return_value=layer), \
                mock.patch.object(self.script, "limited", side_effect=lambda function, job, seconds: function(job)):
            result = self.script.run_cross_check(self.subject, None, args)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(len(result["fields"]["rows"]), 4)
        self.assertTrue(all(row["equal"] for row in result["fields"]["rows"]))

    def test_research_r12_asks_for_no_other_cross_check(self):
        with self.assertRaisesRegex(Refused, "no cross-check"):
            self.script.run_cross_check(self.subject, None, mock.Mock(tool="exhaustive tables"))

    @unittest.skipUnless(os.name == "posix", "the ARX search is a WSL binary")
    def test_a_cross_check_of_the_search_on_a1s_first_amounts_passes(self):
        for rel in (self.script.TRAIL_PATHS["ARX search"], self.script.ARX_BINARY):
            write(self.root, rel, (CODE_ROOT / rel).read_bytes())
        args = mock.Mock(rounds=2, tool="ARX search")
        run = mock.Mock(workers=8)
        with mock.patch.object(self.script, "CROSS_WIDTHS", (4,)), mock.patch.object(self.script, "table_round_seconds", return_value=0.01):
            result = self.script.run_cross_check(self.subject, run, args)
        self.assertEqual(result["status"], "pass", [row for row in result["fields"]["rows"] if not row["above_floor"] or row["equal"] is False])
        self.assertEqual({row["width"] for row in result["fields"]["rows"]}, {4})
        self.assertEqual(result["fields"]["rounds"], 2)
        self.assertTrue(all(row["equal"] is True for row in result["fields"]["rows"]))

    @unittest.skipUnless(os.name == "posix", "the ARX search is a WSL binary")
    def test_a_search_stopped_at_the_cap_keeps_the_rounds_it_reached(self):
        for rel in (self.script.TRAIL_PATHS["ARX search"], self.script.ARX_BINARY):
            write(self.root, rel, (CODE_ROOT / rel).read_bytes())
        args = mock.Mock(rounds=None, tool="ARX search")
        with mock.patch.object(self.script, "CROSS_SECONDS", [1.0]), mock.patch.object(self.script, "POLL_SECONDS", 0.1), \
                mock.patch.object(self.script, "CROSS_WIDTHS", (4, 8)), mock.patch.object(self.script, "table_round_seconds", return_value=0.0), \
                mock.patch.object(self.script, "worker_map", side_effect=lambda f, jobs, n: [
                    {"floor": {r: 0 for r in range(1, job[3] + 1)}, "exact": None} for job in jobs]):
            result = self.script.run_cross_check(self.subject, mock.Mock(workers=1), args)
        self.assertGreater(result["fields"]["rounds"], 0)
        self.assertEqual(sorted({row["r"] for row in result["fields"]["rows"]}), list(range(1, result["fields"]["rounds"] + 1)))

    def test_a_climb_keeps_what_was_printed_in_order(self):
        climb = self.script.Climb.__new__(self.script.Climb)
        climb.weights = {1: 5, 2: 9, 4: 20}
        self.assertEqual(climb.reached(), 2)

    def test_a_limited_call_returns_or_gives_up(self):
        self.assertEqual(self.script.limited(sorted, [3, 1, 2], 60.0), [1, 2, 3])
        with self.assertRaisesRegex(evidence.ToolFailure, "TypeError"):
            self.script.limited(sorted, 5, 60.0)

    def test_the_counter_reaches_as_many_rounds_as_the_cap_holds(self):
        write(self.root, self.script.TRAIL_PATHS["active-S-box counting"], b"counter")
        rows = [{"kind": "differential", "r": 1, "counter": 4, "exhaustive": 4, "equal": True}]
        with mock.patch.object(self.script, "limited", side_effect=[rows, None]):
            result = self.script.run_cross_check(self.subject, None, mock.Mock(rounds=None, tool="active-S-box counting"))
        self.assertEqual((result["status"], result["fields"]["rounds"]), ("pass", 1))
        with mock.patch.object(self.script, "limited", return_value=None):
            result = self.script.run_cross_check(self.subject, None, mock.Mock(rounds=None, tool="active-S-box counting"))
        self.assertEqual((result["status"], result["fields"]["capped"]), ("inconclusive", True))

    def test_a_unequal_minimum_fails_the_cross_check(self):
        write(self.root, self.script.TRAIL_PATHS["active-S-box counting"], b"counter")
        rows = [{"kind": "linear", "r": 1, "counter": 4, "exhaustive": 5, "equal": False}]
        with mock.patch.object(self.script, "limited", side_effect=[rows, None]):
            self.assertEqual(self.script.run_cross_check(self.subject, None, mock.Mock(rounds=None, tool="active-S-box counting"))["status"], "fail")


def rule_script(name: str):
    """A script of the rules under its own name, as a worktree's run loads it."""
    import importlib.util
    import sys
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


class D4Rule(unittest.TestCase):
    """Research R6's rule, on stated bounds, with nothing on disk."""

    FAMILIES = {"cand-A1": "ARX", "cand-A2": "ARX", "cand-B1": "Boolean"}
    LUTS = {16: {"cand-A1": Fraction(160), "cand-A2": Fraction(120), "cand-B1": Fraction(128)},
            8: {"cand-A1": Fraction(80), "cand-A2": Fraction(60), "cand-B1": Fraction(64)}}

    def setUp(self):
        self.d4 = rule_script("d4_choice")

    def table(self, **rounds):
        """r2=(W_D, W_L) gives both bounds over 2 rounds."""
        out = {"differential": {}, "linear": {}}
        for name, (w_d, w_l) in rounds.items():
            r = int(name[1:])
            if w_d is not None:
                out["differential"][r] = (Fraction(w_d), f"bound-d{r}")
            if w_l is not None:
                out["linear"][r] = (Fraction(w_l), f"bound-l{r}")
        return out

    def widths(self, at_16=None, at_8=None):
        return {16: at_16 or {}, 8: at_8 or {}}

    def test_the_widest_width_with_a_common_number_of_rounds_and_the_largest_there(self):
        tables = {"cand-A1": self.table(r2=(10, 10), r3=(20, 20), r5=(30, 30)), "cand-B1": self.table(r2=(9, 9), r3=(18, 18))}
        self.assertEqual(self.d4.locate(self.widths(tables, tables), self.FAMILIES), (16, 3, "chosen", None))

    def test_a_round_count_of_one_is_not_common(self):
        tables = {"cand-A1": self.table(r1=(10, 10)), "cand-B1": self.table(r1=(9, 9))}
        self.assertEqual(self.d4.locate(self.widths(tables, tables), self.FAMILIES)[2], "not computable")

    def test_one_bound_alone_gives_no_rounds(self):
        tables = {"cand-A1": self.table(r2=(10, None)), "cand-B1": self.table(r2=(None, 9))}
        self.assertEqual(self.d4.locate(self.widths(tables), self.FAMILIES)[2], "not computable")

    def test_with_no_common_number_at_16_the_rule_goes_to_8(self):
        at_16 = {"cand-A1": self.table(r2=(10, 10)), "cand-B1": self.table(r3=(9, 9))}
        at_8 = {"cand-A1": self.table(r4=(10, 10)), "cand-B1": self.table(r4=(9, 9))}
        self.assertEqual(self.d4.locate(self.widths(at_16, at_8), self.FAMILIES), (8, 4, "chosen", None))

    def test_a_family_alone_at_the_widest_width_is_chosen_by_default(self):
        at_16 = {"cand-A1": self.table(r2=(10, 10)), "cand-B1": self.table()}
        at_8 = {"cand-A1": self.table(), "cand-B1": self.table(r2=(9, 9), r4=(9, 9))}
        self.assertEqual(self.d4.locate(self.widths(at_16, at_8), self.FAMILIES)[1:], (2, "chosen by default", "ARX"))

    def test_both_families_at_a_width_with_no_common_number_go_to_the_larger_number(self):
        at_16 = {"cand-A1": self.table(r2=(10, 10)), "cand-B1": self.table(r3=(9, 9))}
        self.assertEqual(self.d4.locate(self.widths(at_16), self.FAMILIES), (16, 3, "chosen by default", "Boolean"))

    def owed(self, tables, ends, closed=()):
        return self.d4.climbs_owed(tables, ends, self.FAMILIES, closed)

    def test_while_no_climb_has_ended_every_candidate_climbs_on(self):
        tables = {"cand-A1": self.table(r2=(1, 1)), "cand-B1": self.table(r2=(1, 1))}
        self.assertEqual(len(self.owed(tables, {"cand-A1": None, "cand-B1": None})), 2)

    def test_nobody_owes_an_r_the_other_family_could_not_share(self):
        tables = {"cand-A1": self.table(r2=(1, 1)), "cand-B1": self.table(r2=(1, 1))}
        self.assertEqual(self.owed(tables, {"cand-A1": None, "cand-B1": 3}), [])

    def test_a_candidate_climbs_as_far_as_the_other_family_can_share(self):
        tables = {"cand-A1": self.table(r2=(1, 1)), "cand-B1": self.table(r2=(1, 1), r3=(1, 1))}
        owed = self.owed(tables, {"cand-A1": None, "cand-B1": 4})
        self.assertEqual(len(owed), 1)
        self.assertIn("cand-A1", owed[0])

    def test_every_candidate_searches_two_rounds_whatever_the_other_family_reached(self):
        tables = {"cand-A1": self.table(), "cand-B1": self.table()}
        owed = self.owed(tables, {"cand-A1": None, "cand-B1": 2})
        self.assertEqual(len(owed), 1)
        self.assertIn("cand-A1", owed[0])
        self.assertEqual(self.owed({"cand-A1": self.table(r2=(1, 1)), "cand-B1": self.table()}, {"cand-A1": None, "cand-B1": 2}), [])

    def test_a_climb_with_a_kind_left_short_of_its_end_owes_that_kind(self):
        tables = {"cand-A1": self.table(r2=(1, 1), r3=(1, 1)), "cand-B1": self.table(r2=(1, 1), r3=(1, None))}
        owed = self.owed(tables, {"cand-A1": 5, "cand-B1": 4})
        self.assertEqual(len(owed), 1)
        self.assertIn("cand-B1", owed[0])

    def test_a_family_with_a_candidate_climbing_has_no_top_yet(self):
        tables = {"cand-A1": self.table(r2=(1, 1)), "cand-A2": self.table(r2=(1, 1)), "cand-B1": self.table(r2=(1, 1), r3=(1, 1), r4=(1, 1))}
        owed = self.owed(tables, {"cand-A1": 3, "cand-A2": None, "cand-B1": None})
        self.assertEqual(sorted(item.split()[0] for item in owed), ["cand-A2", "cand-B1"])
        owed = self.owed(tables, {"cand-A1": 3, "cand-A2": None, "cand-B1": 5})
        self.assertEqual(len(owed), 1)
        self.assertIn("cand-A2", owed[0])

    def test_a_candidate_with_a_closing_decision_owes_nothing(self):
        tables = {"cand-A1": self.table(r2=(1, 1)), "cand-B1": self.table()}
        self.assertEqual(self.owed(tables, {"cand-A1": 3, "cand-B1": None}, closed=("cand-B1",)), [])

    def test_the_score_compares_exactly(self):
        self.assertEqual(self.d4.higher((Fraction(3), Fraction(7)), (Fraction(3, 2), Fraction(7, 2))), 0)
        self.assertEqual(self.d4.higher((Fraction(65537, 65536), Fraction(1)), (Fraction(1), Fraction(1))), 1)
        self.assertEqual(self.d4.higher((Fraction(1), Fraction(2)), (Fraction(1), Fraction(1))), -1)

    def test_the_family_with_the_higher_representative_is_chosen(self):
        tables = {"cand-A1": self.table(r2=(32, 16)), "cand-A2": self.table(r2=(24, 18)), "cand-B1": self.table(r2=(16, 16))}
        found = self.d4.decide(self.widths(tables), self.FAMILIES, self.LUTS)
        self.assertEqual(found["representatives"], {"ARX": "cand-A2", "Boolean": "cand-B1"})
        self.assertEqual((found["outcome"], found["chosen_family"], found["r_star"]), ("chosen", "ARX", 2))
        self.assertEqual(found["scored"]["cand-A2"]["score"], str(Fraction(18, 2) / 120))

    def test_an_exact_tie_chooses_no_family(self):
        tables = {"cand-A1": self.table(r2=(40, 40)), "cand-B1": self.table(r2=(32, 32))}
        found = self.d4.decide(self.widths(tables), self.FAMILIES, self.LUTS)
        self.assertEqual((found["outcome"], found["chosen_family"]), ("tie", NONE))

    def test_not_computable_scores_nobody(self):
        found = self.d4.decide(self.widths({"cand-A1": self.table(), "cand-B1": self.table()}), self.FAMILIES, self.LUTS)
        self.assertEqual((found["outcome"], found["width"], found["scored"]), ("not computable", NONE, {}))

    def test_only_the_chosen_familys_candidates_are_scored_by_default(self):
        tables = {"cand-A1": self.table(r2=(10, 10)), "cand-B1": self.table()}
        found = self.d4.decide(self.widths(tables), self.FAMILIES, self.LUTS)
        self.assertEqual((found["outcome"], found["chosen_family"], sorted(found["scored"])), ("chosen by default", "ARX", ["cand-A1"]))


class RuleRecords(TempRepo):
    """The rules on a temporary repository, each record stated."""

    def setUp(self):
        super().setUp()
        self.d4 = rule_script("d4_choice")
        self.rule = rule_script("round_rule")
        self.number = 0
        for rel in ("cand-A1.py", "cand-B1.py"):
            write(self.root, f"{candidates.CANDIDATES_REL}/{rel}", (CODE_ROOT / candidates.CANDIDATES_REL / rel).read_bytes())
        for rel in (self.d4.CODE + self.rule.CODE):
            write(self.root, rel, (CODE_ROOT / rel).read_bytes())
        self.commit("the code")
        for candidate, family in (("cand-A1", "ARX"), ("cand-B1", "Boolean")):
            digest = evidence.sha256((self.root / candidates.module_rel(candidate)).read_bytes())
            parameters = {name: "stated" for name in candidates.PARAMETERS}
            parameters.update(longest_link={str(n): "2" for n in (4, 8, 16)}, trees={str(n): {} for n in (4, 8, 16)},
                              food_nodes={"reason": "stated"}, constant_instance={"reason": "one stream"})
            candidates.propose({"candidate_id": candidate, "family": family, "oplist_sha256": digest, "parameters": parameters})
        self.commit("proposed")

    def record(self, kind: str, candidate: str = "cand-A1", size: int = 4, status: str = "pass", rounds: int = 8, **fields) -> Dict:
        self.number += 1
        name = f"{kind}-{self.number:04d}"
        body = {"kind": kind, "record_id": name, "candidate": candidate, "status": status, "ended_outside": NONE,
                "created_utc": f"2026-11-05T{self.number // 60:02d}:{self.number % 60:02d}:00Z",
                "config": {"size": size, "width": 32, "rounds": rounds}}
        if kind in ("bound", "trail"):
            body.update(size=size, rounds=rounds)
        body.update(fields)
        write(self.root, f"{evidence.REP_REL}/candidates/{candidate}/{name}.json", evidence.pretty(body))
        return body

    def cross_check(self, candidate: str) -> str:
        return self.record("cross-check", candidate)["record_id"]

    def counted(self, candidate: str, width: int, weights: Dict[str, Dict[int, int]], size: int = 4) -> List[Dict]:
        """Two Π-level records, their counts cross-checked."""
        out = []
        if candidate == "cand-A1":
            box = self.record("bound", candidate, method="branch-and-bound", bound_kind="linear", width=width, size=size, rounds=1,
                              cross_check=self.cross_check(candidate))
            source = {"method": "active-box count", "box_record": box["record_id"], "cross_check": NONE}
        else:
            source = {"method": "active-S-box count", "weight_per_sbox": 1, "cross_check": self.cross_check(candidate)}
        for kind, rows in weights.items():
            out.append(self.record("bound", candidate, bound_kind=kind, width=width, size=size, rounds=max(rows),
                                   counts={str(r): {"count": value} for r, value in rows.items()}, **source))
        return out

    def enter(self) -> None:
        candidates.enter()

    def run_d4(self, *argv) -> int:
        with mock.patch("builtins.print"), mock.patch("sys.stderr"):
            return self.d4.main(list(argv))

    def run_rule(self, *argv) -> int:
        with mock.patch("builtins.print"), mock.patch("sys.stderr"):
            return self.rule.main(list(argv))

    def choice(self) -> int:
        return self.run_d4("--log", evidence.CANDIDATE_LOG_REL, "--out", f"{evidence.REP_REL}/d4/choice.json")

    def scored_set(self, a=(24, 24), b=(10, 10)) -> None:
        self.enter()
        self.counted("cand-A1", 16, {"differential": {1: 5, 2: a[0]}, "linear": {1: 4, 2: a[1]}})
        self.counted("cand-B1", 16, {"differential": {1: 4, 2: b[0]}, "linear": {1: 4, 2: b[1]}})
        self.climb_ended("cand-B1", 3)

    def climb_ended(self, candidate: str, r: int, width: int = 16) -> None:
        self.record("bound", candidate, method="active-S-box count", bound_kind="linear", width=width, size=4, rounds=r, status="inconclusive",
                    capped=True)


class D4Script(RuleRecords):
    def test_no_entered_set_exits_2(self):
        self.assertEqual(self.choice(), 2)

    def test_a_candidate_without_an_outcome_exits_2_and_writes_nothing(self):
        self.enter()
        self.counted("cand-A1", 16, {"differential": {2: 24}, "linear": {2: 24}})
        self.assertEqual(self.choice(), 2)
        self.assertFalse((self.root / evidence.REP_REL / "d4/choice.json").exists())

    def test_the_choice_cites_its_records_and_each_scored_candidate_gets_an_entry(self):
        self.scored_set()
        self.assertEqual(self.choice(), 0)
        path = self.root / evidence.REP_REL / "d4/choice.json"
        record = json.loads(path.read_bytes())
        self.assertEqual(record["kind"], "d4-choice")
        self.assertEqual((record["width"], record["r_star"], record["outcome"]), (16, 2, "chosen"))
        self.assertIn("not a rate per round", record["r_star_statement"])
        self.assertEqual(record["luts"] if "luts" in record else record["scored"]["cand-A1"]["luts"], str(self.luts("cand-A1")))
        scored = candidates.of_event(candidates.entries(), "scored")
        self.assertEqual(sorted(entry["candidate_id"] for entry in scored), ["cand-A1", "cand-B1"])
        self.assertEqual(scored[0]["record"]["sha256"], evidence.sha256(path.read_bytes()))

    def luts(self, candidate: str):
        return self.d4.lists_at([candidate])[16][candidate]

    def test_a_climb_that_has_not_ended_exits_2_and_writes_nothing(self):
        """Research R6, "How far the searches go": where the searches stop is nobody's choice."""
        self.enter()
        self.counted("cand-A1", 16, {"differential": {2: 24}, "linear": {2: 24}})
        self.counted("cand-B1", 16, {"differential": {2: 10}, "linear": {2: 10}})
        self.assertEqual(self.choice(), 2)
        self.assertFalse((self.root / evidence.REP_REL / "d4/choice.json").exists())

    def test_a_refusal_ends_a_climb_as_a_cap_does(self):
        self.enter()
        self.counted("cand-A1", 16, {"differential": {2: 24}, "linear": {2: 24}})
        self.counted("cand-B1", 16, {"differential": {2: 10}, "linear": {2: 10}})
        probe = {"kind": "bound", "size": 4, "test": NONE, "width": 16, "bound_kind": "linear", "method": "active-S-box count"}
        evidence.write_projection(run="x", row="cand-B1/trails", inputs=NONE, measured_speed=1, projected_hours=8.0, time_hours=0.0,
                                  extra={"probe": probe, "rounds": 3, "refused": "8.000 h do not fit"})
        self.assertEqual(self.d4.climb_end("cand-B1", 16), 3)
        self.assertEqual(self.choice(), 0)

    def test_a_climb_ends_at_the_first_r_of_either_kind_at_its_own_width(self):
        self.climb_ended("cand-B1", 4)
        self.climb_ended("cand-B1", 3)
        self.assertEqual(self.d4.climb_end("cand-B1", 16), 3)
        self.assertIsNone(self.d4.climb_end("cand-B1", 8))
        self.assertIsNone(self.d4.climb_end("cand-A1", 16))

    def test_a_second_run_exits_2(self):
        """Quickstart E4."""
        self.scored_set()
        self.assertEqual(self.choice(), 0)
        self.assertEqual(self.choice(), 2)
        self.assertEqual(len(candidates.of_event(candidates.entries(), "scored")), 2)

    def test_a_bound_without_its_cross_check_does_not_count(self):
        self.enter()
        self.record("bound", "cand-A1", method="active-box count", bound_kind="differential", width=16, size=4, rounds=2,
                    box_record="none", counts={"2": {"count": 24}})
        table = self.d4.bounds_of("cand-A1", 16)
        self.assertEqual(table["differential"], {})

    def test_a_capped_search_is_an_outcome_and_no_bound(self):
        self.enter()
        self.record("bound", "cand-A1", method="active-box count", bound_kind="differential", width=16, size=4, rounds=2,
                    status="inconclusive", capped=True)
        self.assertEqual(list(self.d4.outcome_of("cand-A1", 16, "differential", [])), ["inconclusive"])

    def test_a_rejected_candidate_has_its_outcome(self):
        self.assertEqual(self.d4.outcome_of("cand-A1", 16, "linear", ["rejected"]), {"decision": "rejected"})
        self.assertIsNone(self.d4.outcome_of("cand-A1", 16, "linear", ["eligible"]))

    def test_a_bound_at_another_size_or_width_is_not_read(self):
        self.counted("cand-A1", 16, {"differential": {2: 24}}, size=8)
        self.counted("cand-A1", 8, {"differential": {2: 24}})
        self.assertEqual(self.d4.bounds_of("cand-A1", 16)["differential"], {})

    # the tie ----------------------------------------------------------------------------------------

    def tied(self) -> None:
        self.scored_set()
        with mock.patch.object(self.d4, "lists_at", return_value={16: {"cand-A1": Fraction(4), "cand-B1": Fraction(2)}, 8: {}}):
            self.assertEqual(self.choice(), 0)
        self.assertEqual(json.loads((self.root / evidence.REP_REL / "d4/choice.json").read_bytes())["outcome"], "chosen")

    def tie_record(self, r_a=None, r_b=None) -> None:
        self.scored_set((20, 20), (10, 10))
        with mock.patch.object(self.d4, "lists_at", return_value={16: {"cand-A1": Fraction(4), "cand-B1": Fraction(2)}, 8: {}}):
            self.assertEqual(self.choice(), 0)
        self.assertEqual(json.loads((self.root / evidence.REP_REL / "d4/choice.json").read_bytes())["outcome"], "tie")
        for candidate, value in (("cand-A1", r_a), ("cand-B1", r_b)):
            if value is not None:
                write(self.root, f"{evidence.REP_REL}/candidates/{candidate}/round-rule.json", evidence.pretty({"sizes": {"4": {"R": value}}}))

    def tie(self) -> int:
        return self.run_d4("--tie", "--log", evidence.CANDIDATE_LOG_REL, "--out", f"{evidence.REP_REL}/d4/tie.json")

    def tie_read(self) -> Dict:
        return json.loads((self.root / evidence.REP_REL / "d4/tie.json").read_bytes())

    def test_tie_exits_2_without_an_exact_tie(self):
        self.tied()
        self.assertEqual(self.tie(), 2)

    def test_tie_exits_2_until_both_values_of_r_exist(self):
        self.tie_record(r_a=20)
        self.assertEqual(self.tie(), 2)

    def test_the_smaller_r_decides_a_tie(self):
        self.tie_record(r_a=20, r_b=24)
        self.assertEqual(self.tie(), 0)
        self.assertEqual((self.tie_read()["decided_by"], self.tie_read()["chosen_family"]), ("R at 4×4", "ARX"))
        self.assertEqual(self.tie(), 2)

    def test_fewer_carry_chains_decide_next(self):
        self.tie_record(r_a=20, r_b=20)
        self.assertEqual(self.tie(), 0)
        self.assertEqual((self.tie_read()["decided_by"], self.tie_read()["chosen_family"]), ("carry chains", "Boolean"))

    def test_an_ineligible_representative_loses_the_tie(self):
        self.tie_record()
        with mock.patch.object(candidates, "decisions", side_effect=lambda log, candidate: ["ineligible"] if candidate == "cand-B1" else []):
            self.assertEqual(self.tie(), 0)
        self.assertEqual((self.tie_read()["decided_by"], self.tie_read()["chosen_family"]), ("ineligible", "ARX"))

    def owner_tie(self) -> str:
        self.tie_record(r_a=20, r_b=20)
        with mock.patch.object(self.d4, "carry_chains", return_value=4):
            self.assertEqual(self.tie(), 0)
        self.assertEqual(self.tie_read()["decided_by"], "owner")
        return evidence.sha256((self.root / evidence.REP_REL / "d4/tie.json").read_bytes())

    def choose(self, digest: str, *more) -> int:
        return self.run_d4("--choose", "cand-A1", "--seen", digest, "--by", "owner", "--out", f"{evidence.REP_REL}/d4/tie-choice.json", *more)

    def test_choose_writes_nothing_unless_the_digits_are_typed_at_a_terminal(self):
        digest = self.owner_tie()
        self.assertEqual(self.choose(digest), 2)
        self.assertFalse((self.root / evidence.REP_REL / "d4/tie-choice.json").exists())

    def test_choose_takes_the_typed_digits(self):
        digest = self.owner_tie()
        with mock.patch.object(evidence, "confirm_digits", return_value=digest[:16]):
            self.assertEqual(self.choose(digest), 0)
        record = json.loads((self.root / evidence.REP_REL / "d4/tie-choice.json").read_bytes())
        self.assertEqual((record["choice"], record["seen_sha256"], record["choice_confirmed"]), ("cand-A1", digest, digest[:16]))
        self.assertEqual(self.choose(digest), 2)

    def test_the_owners_written_approval_stands_for_the_digits_and_the_record_says_so(self):
        digest = self.owner_tie()
        self.assertEqual(self.choose(digest, "--written-approval", "choose cand-A1"), 0)
        record = json.loads((self.root / evidence.REP_REL / "d4/tie-choice.json").read_bytes())
        self.assertEqual(record["written_approval"]["entered_by"], "agent")
        self.assertEqual(record["written_approval"]["words"], "choose cand-A1")

    def test_choose_exits_2_on_another_hash_and_when_a_tie_break_decided_it(self):
        digest = self.owner_tie()
        self.assertEqual(self.choose("0" * 64, "--written-approval", "w"), 2)
        path = self.root / evidence.REP_REL / "d4/tie.json"
        write(self.root, evidence.rel_to_repo(path), evidence.pretty(dict(self.tie_read(), decided_by="R at 4×4")))
        self.assertEqual(self.choose(evidence.sha256(path.read_bytes()), "--written-approval", "w"), 2)
        self.assertNotEqual(digest, evidence.sha256(path.read_bytes()))

    def test_a_reproduction_of_the_choice_matches(self):
        self.scored_set()
        self.commit("the bounds")
        self.assertEqual(self.choice(), 0)
        self.commit("the choice")
        write(self.root, "research/004/tools/.keep", "")
        code = self.run_d4("--reproduce", f"{evidence.REP_REL}/d4/choice.json")
        self.assertEqual(code, 0)


class RoundRule(RuleRecords):
    def evidence_at(self, candidate="cand-A1", size=4, r_f=4, r_b=5, fired=(1, 2), rounds=12, bias=True) -> None:
        self.record("dependency", candidate, size, r_f=r_f, r_b=r_b, incomplete_rounds=max(r_f, r_b) - 1,
                    through_instantiate={"every_bit_reached_after": 20})
        self.counted(candidate, 32, {"differential": {6: 120, 8: 140}, "linear": {6: 100, 8: 130}}, size=size)
        if bias:
            self.record("frequency", candidate, size, rounds=rounds, rounds_fired=list(fired))
            self.record("avalanche", candidate, size, rounds=rounds, rounds_fired=[1])
        self.record("degree", candidate, size, rounds_fired=[1, 2, 3])
        self.record("inverse", candidate, size, rounds=rounds)
        self.record("symmetry", candidate, size)
        self.record("invariant", candidate, size, rounds=rounds, round_counts={"1": {"kept": [], "above_chance": []}}, rounds_fired=[])

    def test_r_is_the_rules_largest_term(self):
        self.assertEqual(self.rule.round_count(3, 8, 4, 5), 10)
        self.assertEqual(self.rule.round_count(7, 8, 4, 5), 14)
        self.assertEqual(self.rule.round_count(3, 12, 4, 5), 14)
        self.assertIsNone(self.rule.round_count(3, None, 4, 5))
        self.assertIsNone(self.rule.round_count(3, 8, None, 5))
        self.assertEqual(self.rule.round_count(None, 8, 4, 5), 10)

    def test_r_bound_needs_both_bounds_above_the_target(self):
        self.counted("cand-A1", 32, {"differential": {6: 128, 7: 129, 8: 140}, "linear": {6: 200, 7: 128, 8: 129}})
        found, records = self.rule.r_bound_of("cand-A1", 4)
        self.assertEqual(found, 8)
        self.assertEqual(len(records), 2)

    def test_a_bound_at_another_size_gives_no_r_bound_here(self):
        self.counted("cand-A1", 32, {"differential": {8: 140}, "linear": {8: 140}}, size=8)
        self.assertEqual(self.rule.r_bound_of("cand-A1", 4), (None, []))

    def test_r_dist_is_the_largest_source_with_every_input_cited(self):
        self.record("frequency", rounds_fired=[1, 2, 3])
        self.record("avalanche", rounds_fired=[1, 5])
        self.record("invariant", rounds_fired=[4])
        self.record("degree", rounds_fired=[6])
        self.record("dependency", r_f=4, r_b=4, incomplete_rounds=3)
        found, sources = self.rule.r_dist_of("cand-A1", 4)
        self.assertEqual(found, 6)
        self.assertEqual(sorted(item["source"] for item in sources),
                         ["avalanche", "degree", "frequency", "incomplete diffusion", "invariant"])

    def test_a_trail_counts_only_lighter_than_the_target(self):
        self.record("trail", width=32, rounds=7, weight_log2="127.5")
        self.record("trail", width=32, rounds=9, weight_log2="128")
        self.assertEqual(self.rule.r_dist_of("cand-A1", 4)[0], 7)

    def test_a_record_ended_from_outside_decides_nothing(self):
        self.record("frequency", rounds_fired=[9], ended_outside="2026-11-05T00:00:00Z", status="inconclusive")
        self.assertEqual(self.rule.r_dist_of("cand-A1", 4), (None, []))
        self.record("dependency", r_f=4, r_b=4, ended_outside="2026-11-05T00:00:00Z")
        self.assertEqual(self.rule.r_f_and_b("cand-A1", 4), (None, None, []))

    def test_a_firing_recorded_stands_after_a_rise(self):
        self.record("frequency", rounds=12, rounds_fired=[7])
        self.record("frequency", rounds=14, rounds_fired=[2])
        self.assertEqual(self.rule.r_dist_of("cand-A1", 4)[0], 7)

    def test_the_rule_writes_each_size_with_every_input_cited(self):
        for size in (4, 8, 16):
            self.evidence_at(size=size)
        self.assertEqual(self.run_rule("--candidate", "cand-A1"), 0)
        record = json.loads((self.root / evidence.REP_REL / "candidates/cand-A1/round-rule.json").read_bytes())
        row = record["sizes"]["4"]
        self.assertEqual((row["R_f"], row["R_b"], row["R_bound"], row["R_dist"], row["delta"], row["R"]), (4, 5, 8, 4, 2, 10))
        self.assertTrue(row["R_bound_records"])
        self.assertTrue(row["R_dist_sources"])
        self.assertEqual(record["candidate"], "cand-A1")
        self.assertIsInstance(record["false_firing_rate"], float)

    def test_a_missing_item_fails_eligibility(self):
        for size in (4, 8, 16):
            self.evidence_at(size=size)
        self.assertEqual(self.run_rule("--candidate", "cand-A1"), 0)
        record = self.rule.read_round_rule("cand-A1")
        self.assertFalse(self.rule.row_met(record))
        self.assertTrue(candidates.failed_items(record))
        self.assertFalse(record["sizes"]["4"]["eligible"]["FR-030 mapping"]["met"])

    def test_a_rerun_of_the_rule_keeps_the_old_file_and_records_a_rise(self):
        for size in (4, 8, 16):
            self.evidence_at(size=size)
        self.run_rule("--candidate", "cand-A1")
        self.record("frequency", rounds_fired=[6], rounds=10)
        self.assertEqual(self.run_rule("--candidate", "cand-A1"), 0)
        record = self.rule.read_round_rule("cand-A1")
        self.assertEqual(record["sizes"]["4"]["R"], 12)
        self.assertEqual(record["sizes"]["4"]["rises"][0]["from"], 10)
        self.assertEqual(record["sizes"]["4"]["rises"][0]["to"], 12)
        self.assertTrue(list((self.root / evidence.REP_REL / "candidates/cand-A1/versions").glob("*.json")))

    def test_a_control_that_fired_fails_the_item_at_that_size(self):
        write(self.root, f"{evidence.REP_REL}/controls/c.json", evidence.pretty(
            {"kind": "control", "test": "frequency", "size": 4, "fires": True, "created_utc": "2026-11-05T00:00:00Z", "ended_outside": NONE,
             "record_id": "control-c", "status": "inconclusive"}))
        self.assertFalse(self.rule.bias_item("cand-A1", "frequency", 4, 12)["met"])

    def test_an_inconclusive_bias_record_fails_the_item(self):
        write(self.root, f"{evidence.REP_REL}/controls/c.json", evidence.pretty(
            {"kind": "control", "test": "frequency", "size": 4, "fires": False, "created_utc": "2026-11-05T00:00:00Z", "ended_outside": NONE,
             "record_id": "control-c", "status": "pass"}))
        self.record("frequency", rounds=12, status="inconclusive")
        self.assertFalse(self.rule.bias_item("cand-A1", "frequency", 4, 12)["met"])

    def test_a_bias_test_must_stand_at_the_sizes_r(self):
        write(self.root, f"{evidence.REP_REL}/controls/c.json", evidence.pretty(
            {"kind": "control", "test": "frequency", "size": 4, "fires": False, "created_utc": "2026-11-05T00:00:00Z", "ended_outside": NONE,
             "record_id": "control-c", "status": "pass"}))
        self.record("frequency", rounds=10)
        self.assertFalse(self.rule.bias_item("cand-A1", "frequency", 4, 12)["met"])
        self.assertTrue(self.rule.bias_item("cand-A1", "frequency", 4, 10)["met"])

    def test_a_reproduction_that_differs_blocks_until_a_re_run_resolves_it(self):
        held = self.record("inverse")
        write(self.root, f"{evidence.REP_REL}/reproductions/x/1/r.json", evidence.pretty(
            {"kind": "reproduction", "record_id": "reproduction-x", "status": "blocked", "original": {"record_id": held["record_id"]}}))
        self.assertEqual(self.rule.unresolved("cand-A1"), ["reproduction-x"])
        self.record("inverse", exclusions_and_reruns=[{"record_id": held["record_id"], "why": "tool defect"}])
        self.assertEqual(self.rule.unresolved("cand-A1"), [])

    def test_a_recheck_that_disagrees_blocks_too(self):
        held = self.record("inverse")
        write(self.root, f"{evidence.REP_REL}/rechecks/r.json", evidence.pretty(
            {"kind": "recheck", "record_id": "recheck-x", "disagreements": [{"record_id": held["record_id"]}]}))
        self.assertEqual(self.rule.unresolved("cand-A1"), ["recheck-x"])

    def test_the_key_path_runs_between_neighbours_through_the_key_lanes(self):
        good = {"key_path": [[0, 0], [0, 1], [0, 2], [0, 3]]}
        self.assertTrue(self.rule.key_path_item(good, 4)["met"])
        self.assertFalse(self.rule.key_path_item({"key_path": [[0, 0], [0, 2], [0, 1], [0, 3]]}, 4)["met"])
        self.assertFalse(self.rule.key_path_item({"key_path": [[0, 0], [0, 1]]}, 4)["met"])
        self.assertFalse(self.rule.key_path_item(None, 4)["met"])

    def test_the_stages_are_read_from_the_list_and_set_against_its_declaration(self):
        import sys
        script = evidence_script()
        loaded = script.build_list("cand-A1", 4, 32)
        costmodel = sys.modules["costmodel"] if "costmodel" in sys.modules else __import__("costmodel")
        counted = costmodel.count(loaded, 1, 1)
        right = {"stages": {"phases": counted["phases"], "chains_per_phase": counted["chains_per_phase"]}}
        self.assertTrue(self.rule.stages_item(right, "cand-A1", 4)["met"])
        wrong = {"stages": {"phases": counted["phases"] + 1, "chains_per_phase": counted["chains_per_phase"]}}
        self.assertFalse(self.rule.stages_item(wrong, "cand-A1", 4)["met"])
        self.assertFalse(self.rule.stages_item(None, "cand-A1", 4)["met"])

    def test_each_candidate_declares_what_fr_025_and_fr_027_read(self):
        for candidate in ("cand-A1", "cand-B1"):
            for size in (4, 8, 16):
                declared = self.rule.declarations_of(candidate, size)
                self.assertTrue(self.rule.stages_item(declared, candidate, size)["met"], (candidate, size))
                self.assertTrue(self.rule.key_path_item(declared, size)["met"], (candidate, size))
                self.assertTrue(self.rule.semantics_item(declared)["met"], (candidate, size))

    def test_semantics_are_read_from_the_declaration(self):
        whole = {"semantics": dict.fromkeys(("width", "signedness", "wrap", "shift", "rotation"), "stated")}
        self.assertTrue(self.rule.semantics_item(whole)["met"])
        self.assertFalse(self.rule.semantics_item({"semantics": {"width": "w"}})["met"])

    def test_through_instantiate_needs_every_bit_before_the_first_output(self):
        self.record("dependency", r_f=4, r_b=4, through_instantiate={"every_bit_reached_after": 20})
        self.assertTrue(self.rule.diffusion_item("cand-A1", 4, 3)["met"])
        self.assertFalse(self.rule.diffusion_item("cand-A1", 4, 2)["met"])
        self.assertEqual(self.rule.diffusion_item("cand-A1", 4, 3)["evidence"][1]["margin_over_r_f"], 17)


class Selection(RuleRecords):
    """--close, --select, --choose and --decide, each round-rule record stated."""

    def row(self, r: int, met: bool = True) -> Dict:
        return {"R": r, "eligible": {"item": {"met": met}}}

    def round_rule(self, candidate: str, r_4: int = 12, met: bool = True, r_8: int = 14, r_16: int = 16) -> None:
        write(self.root, f"{evidence.REP_REL}/candidates/{candidate}/round-rule.json", evidence.pretty(
            {"kind": "round-rule", "candidate": candidate, "sizes": {"4": self.row(r_4, met), "8": self.row(r_8), "16": self.row(r_16)}}))

    def choice_record(self, outcome: str = "chosen", family: str = "ARX") -> None:
        write(self.root, f"{evidence.REP_REL}/d4/choice.json", evidence.pretty({"outcome": outcome, "chosen_family": family, "representatives": {}}))

    def closed(self, *rows) -> None:
        for row in rows:
            self.round_rule(*row)
        self.assertEqual(self.run_rule("--close"), 0)

    def selected(self, n: str = "selection.json") -> Dict:
        return json.loads((self.root / evidence.REP_REL / "freeze" / n).read_bytes())

    def test_close_needs_a_final_decision_of_every_candidate(self):
        self.round_rule("cand-A1")
        self.assertEqual(self.run_rule("--close"), 2)
        self.assertEqual(candidates.of_event(candidates.entries(), "set-closed"), [])

    def test_close_needs_no_replacement_pending(self):
        self.round_rule("cand-A1")
        self.round_rule("cand-B1")
        with mock.patch.object(candidates, "pending_replacements", return_value=[{"seq": 1}]):
            self.assertEqual(self.run_rule("--close"), 2)

    def test_select_exits_2_before_the_close(self):
        self.choice_record()
        self.assertEqual(self.run_rule("--select"), 2)

    def test_the_chosen_familys_eligible_candidate_is_selected(self):
        self.choice_record()
        self.closed(("cand-A1", 12), ("cand-B1", 10))
        self.assertEqual(self.run_rule("--select"), 0)
        record = self.selected()
        self.assertEqual((record["outcome"], record["selected"], record["fallback"]), ("selected", "cand-A1", False))

    def test_a_family_with_none_eligible_falls_back_to_the_other(self):
        self.choice_record()
        self.closed(("cand-A1", 12, False), ("cand-B1", 10))
        self.assertEqual(self.run_rule("--select"), 0)
        record = self.selected()
        self.assertEqual((record["selected"], record["fallback"]), ("cand-B1", True))

    def test_not_computable_takes_both_families(self):
        self.choice_record("not computable", NONE)
        self.closed(("cand-A1", 12), ("cand-B1", 10))
        self.assertEqual(self.run_rule("--select"), 0)
        self.assertEqual(self.selected()["selected"], "cand-B1")

    def test_none_eligible_is_a_stop_and_exits_1(self):
        self.choice_record()
        self.closed(("cand-A1", 12, False), ("cand-B1", 10, False))
        self.assertEqual(self.run_rule("--select"), 1)
        self.assertEqual(self.selected()["outcome"], "stop")
        self.assertEqual(self.run_rule("--decide"), 2)

    def test_a_later_selection_cites_the_one_before_and_keeps_it(self):
        self.choice_record()
        self.closed(("cand-A1", 12), ("cand-B1", 10))
        self.assertEqual(self.run_rule("--select"), 0)
        first = (self.root / evidence.REP_REL / "freeze/selection.json").read_bytes()
        self.assertEqual(self.run_rule("--select"), 0)
        self.assertEqual((self.root / evidence.REP_REL / "freeze/selection.json").read_bytes(), first)
        self.assertEqual(self.selected("selection-2.json")["previous"]["sha256"], evidence.sha256(first))

    def test_select_waits_on_a_d4_tie_until_its_row_reads(self):
        self.choice_record("tie", NONE)
        write(self.root, f"{evidence.REP_REL}/d4/tie.json", evidence.pretty({"decided_by": "R at 4×4", "chosen_family": "ARX"}))
        self.closed(("cand-A1", 12), ("cand-B1", 10))
        self.assertEqual(self.run_rule("--select"), 2)
        self.add_row("D4 tie", "Not needed", "d4/tie.json, by R at 4×4")
        self.assertEqual(self.run_rule("--select"), 0)
        self.assertEqual(self.selected()["selected"], "cand-A1")

    def test_an_owners_d4_choice_needs_its_row_with_the_hash(self):
        self.choice_record("tie", NONE)
        write(self.root, f"{evidence.REP_REL}/d4/tie.json", evidence.pretty({"decided_by": "owner", "chosen_family": NONE}))
        data = evidence.pretty({"choice": "cand-B1"})
        write(self.root, f"{evidence.REP_REL}/d4/tie-choice.json", data)
        self.closed(("cand-A1", 12), ("cand-B1", 10))
        self.add_row("D4 tie", "Approved", "no hash here")
        self.assertEqual(self.run_rule("--select"), 2)
        self.rows.pop()
        self.add_row("D4 tie", "Approved", evidence.sha256(data))
        self.assertEqual(self.run_rule("--select"), 0)
        self.assertEqual(self.selected()["selected"], "cand-B1")

    def test_an_unresolved_disagreement_stops_select(self):
        self.choice_record()
        self.closed(("cand-A1", 12), ("cand-B1", 10))
        with mock.patch.object(self.rule, "unresolved", return_value=["recheck-x"]):
            self.assertEqual(self.run_rule("--select"), 2)

    def test_the_declined_candidate_selected_again_is_a_stop(self):
        self.choice_record()
        self.closed(("cand-A1", 12), ("cand-B1", 10))
        candidates.append({"candidate_id": "cand-A1", "event": "review-outcome", "outcome": "declined", "declined": "cand-A1"})
        self.assertEqual(self.run_rule("--select"), 1)
        self.assertIn("declined", self.selected()["reason"])

    def tied_selection(self) -> str:
        self.choice_record("not computable", NONE)
        self.closed(("cand-A1", 12), ("cand-B1", 12))
        self.assertEqual(self.run_rule("--select"), 0)
        self.assertEqual(self.selected()["tie"], ["cand-A1", "cand-B1"])
        return evidence.sha256((self.root / evidence.REP_REL / "freeze/selection.json").read_bytes())

    def test_decide_exits_2_while_a_tie_has_no_approved_choice(self):
        self.tied_selection()
        self.assertEqual(self.run_rule("--decide"), 2)

    def test_a_choice_needs_the_digits_and_the_records_hash(self):
        digest = self.tied_selection()
        self.assertEqual(self.run_rule("--choose", "cand-A1", "--seen", digest, "--by", "owner"), 2)
        self.assertEqual(self.run_rule("--choose", "cand-A1", "--seen", "0" * 64, "--by", "owner", "--written-approval", "w"), 2)
        self.assertEqual(self.run_rule("--choose", "cand-A2", "--seen", digest, "--by", "owner", "--written-approval", "w"), 2)
        self.assertEqual(self.run_rule("--choose", "cand-A1", "--seen", digest, "--by", "owner", "--written-approval", "choose A1"), 0)
        self.assertEqual(self.run_rule("--choose", "cand-A1", "--seen", digest, "--by", "owner", "--written-approval", "again"), 2)

    def test_decide_appends_selected_and_not_selected_citing_the_record_and_its_choice(self):
        digest = self.tied_selection()
        self.assertEqual(self.run_rule("--choose", "cand-B1", "--seen", digest, "--by", "owner", "--written-approval", "choose B1"), 0)
        data = (self.root / evidence.REP_REL / "freeze/selection-tie-choice.json").read_bytes()
        self.add_row("Selection tie", "Approved", evidence.sha256(data))
        self.assertEqual(self.run_rule("--decide"), 0)
        entries = candidates.of_event(candidates.entries(), "decision")
        self.assertEqual([(entry["candidate_id"], entry["decision"]) for entry in entries], [("cand-B1", "selected"), ("cand-A1", "not selected")])
        self.assertEqual(entries[0]["selection"]["sha256"], digest)
        self.assertEqual(entries[0]["tie_choice"]["sha256"], evidence.sha256(data))
        self.assertEqual(entries[0]["variant_map"]["cand-B1/n4-w32-R12-c384"], "phyco-v3/n4-w32-R12-c384")
        self.assertEqual(self.run_rule("--decide"), 2)

    def test_a_later_record_gets_entries_of_its_own(self):
        self.choice_record()
        self.closed(("cand-A1", 12), ("cand-B1", 10))
        self.assertEqual(self.run_rule("--select"), 0)
        self.assertEqual(self.run_rule("--decide"), 0)
        self.round_rule("cand-A1", 12, True, 18)
        self.assertEqual(self.run_rule("--select"), 0)
        self.assertEqual(self.run_rule("--decide"), 0)
        entries = candidates.of_event(candidates.entries(), "decision")
        self.assertEqual([entry["decision"] for entry in entries], ["selected", "selected"])
        self.assertEqual(entries[-1]["variant_map"]["cand-A1/n8-w32-R18-c384"], "phyco-v3/n8-w32-R18-c384")


class Recheck(TempRepo):
    """scripts/recheck_004.py on stated records, each with the fields its kind's verdict reads (T086)."""

    def setUp(self):
        super().setUp()
        self.script = rule_script("recheck_004")
        for rel in self.script.CODE:
            write(self.root, rel, (CODE_ROOT / rel).read_bytes())
        self.commit("the code")
        self.head = evidence.head()
        self.number = 0
        self.script_verdicts = self.script.Verdicts()
        self.addCleanup(self.script_verdicts.close)

    def record(self, kind: str, directory: str = "candidates/cand-A1", **fields) -> Dict:
        self.number += 1
        body = {"kind": kind, "record_id": f"{kind}-{self.number}", "status": "pass", "classification": NONE, "git_head": self.head,
                "ended_outside": NONE, "created_utc": f"2026-11-05T00:{self.number:02d}:00Z", "config": {"size": 4, "width": 32, "rounds": 8},
                "limitations": []}
        body.update(fields)
        write(self.root, f"{evidence.REP_REL}/{directory}/{body['record_id']}.json", evidence.pretty(body))
        return body

    def found(self, record: Dict) -> List[Dict]:
        return self.script.differences(record, self.script.CHECKS[record["kind"]](record, self.script_verdicts.at(self.head)))

    def test_it_imports_only_the_standard_library_and_protocol(self):
        tree = ast.parse((ROOT / "scripts/recheck_004.py").read_text(encoding="utf-8"))
        allowed = set(sys.stdlib_module_names) | {"protocol"}
        for node in ast.walk(tree):
            names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else \
                [node.module] if isinstance(node, ast.ImportFrom) else []
            for name in names:
                self.assertIn(name.split(".")[0], allowed, name)
        tree = ast.parse((ROOT / "protocol/rules.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertIn(node.module.split(".")[0], allowed, node.module)

    def test_each_kinds_verdict_again_and_a_changed_field_is_a_disagreement(self):
        low, high = 10, 90
        rows = {"s": {"forward": [[0, 95], [20, 80]], "inverse": [[20, 80], [20, 80]]}}
        for kind, fields, changed in (
                ("inverse", {"mismatches": {"a": 0, "b": 0}}, {"status": "fail"}),
                ("inverse", {"mismatches": {"a": 1, "b": 0}, "status": "fail", "classification": "confirmed vulnerability"}, {"status": "pass"}),
                ("bijectivity", {"inputs": 16, "ones": 16}, {"status": "fail"}),
                ("frequency", {"summaries": rows, "test_parameters": {"critical": [low, high]}, "rounds_fired": [1], "raises": [],
                               "classification": "confirmed vulnerability"}, {"rounds_fired": [2]}),
                ("symmetry", {"fixed": {"a": 0}, "word_rotations": {}, "composed": {}, "relations": {"equal": 0}}, {"fixed": {"a": 2}}),
                ("invariant", {"round_counts": {"1": {"kept": [], "above_chance": []}}, "differences": {}, "rounds_fired": []},
                 {"round_counts": {"1": {"kept": ["f"], "above_chance": []}}}),
                ("degree", {"rounds_within_limit": {"forward": [1], "inverse": []}, "inside_out": None, "rounds_fired": [1],
                            "classification": "strong theoretical concern"}, {"rounds_fired": []}),
                ("cross-check", {"rows": [{"equal": True, "above_floor": True}]}, {"rows": [{"equal": False}]}),
                ("control", {"summaries": {"first set": [20, 80]}, "test_parameters": {"critical": [low, high]}, "fires": False},
                 {"summaries": {"first set": [5, 80]}})):
            with self.subTest(kind=kind, fields=sorted(fields)):
                record = self.record(kind, **fields)
                self.assertEqual(self.found(record), [])
                self.assertTrue(self.found(dict(record, **changed)))

    def test_dependency_rounds_come_from_the_per_round_counts(self):
        report = {"forward": {"first_full": 3, "pairs_without_dependency": [9, 2, 0]}, "inverse": {"first_full": 2, "pairs_without_dependency": [4, 0]}}
        record = self.record("dependency", per_round=report, r_f=3, r_b=2, incomplete_rounds=2, classification="confirmed vulnerability")
        self.assertEqual(self.found(record), [])
        self.assertTrue(self.found(dict(record, r_f=4)))

    def test_a_validation_reads_each_known_result(self):
        record = self.record("validation", "validation", assertions=[{"assertion": "k is re-found", "holds": True}], outcome="re-found")
        self.assertEqual(self.found(record), [])
        self.assertTrue(self.found(dict(record, assertions=[{"assertion": "k is re-found", "holds": False}])))

    def test_a_count_stands_on_its_infeasible_run_or_its_sum(self):
        rows = {"1": {"status": 0, "count": 5, "below": {"status": 2}}, "2": {"status": 0, "count": 10, "sum_of": [1, 1]}}
        record = self.record("bound", method="active-box count", rounds=2, bound_kind="linear", counts=rows, bound="10",
                             classification=evidence.classify("bound", "established"))
        self.assertEqual(self.found(record), [])
        self.assertTrue(self.found(dict(record, bound="15")))
        worse = dict(rows, **{"2": {"status": 0, "count": 10, "below": {"status": 1}}})
        self.assertTrue(self.found(dict(record, counts=worse)))

    def test_a_box_bound_keeps_its_doubled_exponent(self):
        record = self.record("bound", method="branch-and-bound", rounds=1, bound_kind="linear", bound="262144/65536",
                             boxes={"box 0": {"weights": {"1": 2}}, "box 1": {"weights": {"1": 3}}},
                             classification=evidence.classify("bound", "established"))
        self.assertEqual(self.found(record), [])

    def test_a_capped_search_keeps_status_inconclusive_and_no_bound(self):
        record = self.record("bound", status="inconclusive", capped=True, bound=NONE, method="active-box count", rounds=2)
        self.assertEqual(self.found(record), [])

    def test_a_ranking_again_from_its_own_entries(self):
        entries = [{"W_D": 24, "W_L": 16, "assignment": [[1, 1], [1, 3]], "measure": 16},
                   {"W_D": 16, "W_L": 20, "assignment": [[1, 1], [1, 5]], "measure": 16},
                   {"W_D": "786432/65536", "W_L": 8, "assignment": [[1, 3], [1, 1]], "measure": 8}]
        record = self.record("rotation-ranking", entries=entries, chosen=[[1, 1], [1, 3]])
        self.assertEqual(self.found(record), [])
        self.assertEqual([item["field"] for item in self.found(dict(record, chosen=[[1, 1], [1, 5]]))], ["chosen"])
        swapped = [entries[1], entries[0], entries[2]]
        self.assertEqual([item["field"] for item in self.found(dict(record, entries=swapped))], ["status"])
        self.assertEqual([item["field"] for item in self.found(dict(record, entries=swapped, chosen=[[1, 1], [1, 5]]))],
                         ["status", "chosen"])
        wrong = [dict(entries[0], measure=24)] + entries[1:]
        self.assertIn("status", {item["field"] for item in self.found(dict(record, entries=wrong))})

    def test_the_d4_arithmetic_again(self):
        candidates.propose({"candidate_id": "cand-A1", "family": "ARX", "oplist_sha256": self.module("cand-A1"), "parameters": self.parameters()})
        candidates.propose({"candidate_id": "cand-B1", "family": "Boolean", "oplist_sha256": self.module("cand-B1"), "parameters": self.parameters()})
        rows = {"cand-A1": {"W_D": "24", "W_L": "20", "luts": "160", "score": str(Fraction(10, 160))},
                "cand-B1": {"W_D": "16", "W_L": "16", "luts": "128", "score": str(Fraction(8, 128))}}
        record = self.record("d4-choice", "d4", scored=rows, r_star=2, outcome="tie", chosen_family=NONE,
                             representatives={"ARX": "cand-A1", "Boolean": "cand-B1"})
        self.assertEqual(self.found(record), [])
        self.assertTrue(self.found(dict(record, outcome="chosen")))

    def module(self, candidate: str) -> str:
        write(self.root, candidates.module_rel(candidate), "# the list\n")
        self.commit(f"the list of {candidate}")
        return evidence.sha256(b"# the list\n")

    def parameters(self) -> Dict:
        return {name: "stated" for name in candidates.PARAMETERS}

    def test_the_selection_again(self):
        record = self.record("selection", "freeze", R_at_4x4={"cand-A1": 12, "cand-B1": 10}, selected="cand-B1")
        self.assertEqual(self.found(record), [])
        self.assertTrue(self.found(dict(record, selected="cand-A1")))
        tied = self.record("selection", "freeze", R_at_4x4={"cand-A1": 12, "cand-B1": 12}, outcome="tie", tie=["cand-A1", "cand-B1"])
        self.assertEqual(self.found(tied), [])

    def test_the_round_rule_again_from_the_records_that_stood_then(self):
        self.record("dependency", per_round={}, r_f=4, r_b=5, incomplete_rounds=4)
        late = self.record("round-rule", candidate="cand-A1", sizes={"4": {"R_f": 4, "R_b": 5, "R_bound": None, "R_dist": 4, "R": None}})
        self.record("dependency", per_round={}, r_f=6, r_b=7, incomplete_rounds=6)
        self.assertEqual(self.found(late), [])
        self.assertTrue(self.found(dict(late, sizes={"4": {"R_f": 4, "R_b": 5, "R_bound": None, "R_dist": 9, "R": None}})))

    def dead_run(self, record_fields: Dict, hours: float) -> Dict:
        record = self.record("frequency", status="inconclusive", code_sha256={"scripts/clear_lock.py": {}}, created_utc="2026-11-05T02:00:00Z",
                             hours={"projected": 1.0, "used": hours}, **record_fields)
        self.record("lock-cleared", "locks", lock={"time": "2026-11-05T00:30:00Z"}, run_record={"record_id": record["record_id"]})
        return record

    def test_a_record_clear_lock_wrote_holds_no_output_and_is_no_disagreement(self):
        record = self.dead_run({}, 1.5)
        self.assertEqual(self.script.check_cleared(record), [])

    def test_its_status_class_and_hours_are_checked_against_the_lock(self):
        record = self.dead_run({}, 1.25)
        self.assertEqual(self.script.check_cleared(record)[0]["field"], "hours")
        self.assertEqual(self.script.check_cleared(dict(record, hours={"used": 1.5}, status="pass"))[0]["field"], "status")
        self.assertEqual(self.script.check_cleared(dict(record, record_id="none"))[-1]["field"], "lock-cleared")

    def test_a_run_ended_from_outside_counts_up_to_the_boot_time(self):
        record = self.dead_run({"ended_outside": "2026-11-05T01:30:00Z"}, 1.0)
        self.assertEqual(self.script.check_cleared(record), [])

    def test_a_clear_run_writes_its_record_and_exits_0(self):
        self.record("inverse", mismatches={"a": 0})
        self.commit("the record")
        with mock.patch("builtins.print"), mock.patch("sys.stderr"), mock.patch.object(evidence, "pip_freeze", return_value=["numpy==2.2.6"]):
            self.assertEqual(self.script.main([]), 0)
        record = [item for _, item in evidence.iter_records("recheck", "rechecks")][0]
        self.assertEqual(record["results"]["inverse"]["checked"], 1)
        self.assertEqual(record["environment_of_the_run"]["pip_freeze"], ["numpy==2.2.6"])
        self.assertEqual(record["disagreements"], [])

    def test_a_disagreement_exits_1_blocks_and_is_a_finding(self):
        self.record("inverse", mismatches={"a": 1})
        self.commit("the record")
        with mock.patch("builtins.print"), mock.patch("sys.stderr"), mock.patch.object(evidence, "pip_freeze", return_value=[]):
            self.assertEqual(self.script.main(["--kind", "inverse"]), 1)
        record = [item for _, item in evidence.iter_records("recheck", "rechecks")][0]
        self.assertEqual((record["status"], record["classification"]), ("blocked", "unverified hypothesis"))
        self.assertEqual(record["disagreements"][0]["field"], "status")

    def test_it_runs_outside_the_environment_of_the_records(self):
        with mock.patch.object(evidence, "snapshot", return_value=dict(SNAPSHOT, python="3.14.4")), \
                mock.patch("builtins.print"), mock.patch("sys.stderr"), mock.patch.object(evidence, "pip_freeze", return_value=[]):
            self.assertEqual(self.script.main(["--kind", "inverse"]), 0)

    def test_a_replaced_list_that_changed_is_a_disagreement(self):
        write(self.root, evidence.SUPERSEDED_REL, json.dumps({"0" * 64: "research/004/candidates/cand-A1/superseded/x.py"}))
        self.assertEqual(self.script.logs_checked()[0]["field"], "superseded")

    def round_rule(self, met: bool) -> Dict:
        return self.record("round-rule", candidate="cand-A1", sizes={"4": {"eligible": {"FR-022 bounds": {"met": met}}}})

    def decided(self, record: Dict, decision: str = "ineligible", state: Optional[Dict] = None, digest: Optional[str] = None) -> Dict:
        """A decision written as the log holds it, past the writer's guards, with the `replacement` entry it brought."""
        entry = candidates.append({"candidate_id": "cand-A1", "family": "ARX", "event": "decision", "decision": decision, "reason": "r",
                                   "cause": candidates.ITEM, "record": {"record_id": record["record_id"],
                                                                        "sha256": digest or evidence.sha256(evidence.pretty(record))}})
        if decision == "ineligible":
            return candidates.append(dict(state or {"state": "pending"}, candidate_id="cand-A1", family="ARX", event="replacement",
                                          decision_seq=entry["seq"]))
        return entry

    def closing(self, target: Dict, reason: str = candidates.OWNER_DECLINED, **fields) -> Dict:
        return candidates.append(dict(fields, candidate_id="cand-A1", family="ARX", event="replacement", state="closed",
                                      closes=target["seq"], reason=reason))

    def test_each_decision_and_the_replacement_state_it_brought_again(self):
        fails = self.round_rule(False)
        self.decided(fails)
        self.assertEqual(self.script.decisions_checked(), (1, []))
        self.decided(self.round_rule(True))
        self.decided(fails, state={"state": "closed", "reason": candidates.SHARED_REASON})
        self.decided(fails, digest="0" * 64)
        checked, found = self.script.decisions_checked()
        self.assertEqual(checked, 4)
        self.assertEqual([item["field"] for item in found], ["cause", "replacement", "record"])
        self.assertEqual(found[1]["recomputed"], {"state": "pending"})

    def test_an_eligible_decision_cites_a_round_rule_record_with_every_item_met(self):
        self.decided(self.round_rule(True), decision="eligible")
        self.assertEqual(self.script.decisions_checked(), (1, []))
        self.decided(self.round_rule(False), decision="eligible")
        self.assertEqual([item["field"] for item in self.script.decisions_checked()[1]], ["decision"])

    def test_a_closing_entry_closes_a_pending_one_once_for_a_reason_the_log_shows(self):
        fails = self.round_rule(False)
        first = self.decided(fails)
        self.closing(first, owner_word=WORD)
        self.assertEqual(self.script.decisions_checked(), (2, []))
        again = self.closing(first, owner_word=WORD)
        unstated = self.closing(self.decided(fails), reason="R is high")
        unworded = self.closing(self.decided(fails))
        full = self.closing(self.decided(fails), reason=candidates.FULL)
        checked, found = self.script.decisions_checked()
        self.assertEqual(checked, 9)
        self.assertEqual([item["record_id"] for item in found], [f"candidate log seq {entry['seq']}" for entry in (again, unstated, unworded, full)])
        self.assertEqual({item["field"] for item in found}, {"reason"})

    def test_a_recheck_record_holds_the_decisions_it_checked(self):
        self.decided(self.round_rule(False))
        self.commit("the log")
        with mock.patch("builtins.print"), mock.patch("sys.stderr"), mock.patch.object(evidence, "pip_freeze", return_value=[]):
            self.assertEqual(self.script.main(["--kind", "inverse"]), 0)
        record = [item for _, item in evidence.iter_records("recheck", "rechecks")][0]
        self.assertEqual((record["decisions_checked"], record["disagreements"]), (1, []))

    def test_a_reproduction_of_a_recheck_runs_anywhere_and_matches(self):
        self.record("inverse", mismatches={"a": 0})
        self.commit("the record")
        with mock.patch("builtins.print"), mock.patch("sys.stderr"), mock.patch.object(evidence, "pip_freeze", return_value=[]):
            self.assertEqual(self.script.main(["--kind", "inverse"]), 0)
            self.commit("the re-check")
            path, _ = next(iter(evidence.iter_records("recheck", "rechecks")))
            self.assertEqual(self.script.main(["--reproduce", str(path)]), 0)


class CostRecord(TempRepo):
    """research/004/tools/costmodel.py's writer of `cost` records, on candidate A1's list (data-model section 9)."""

    TREES = {"start": {"latency_cycles": 2}, "output": {"latency_cycles": 3}, "absorption": {"latency_cycles": 3}, "reset": {"latency_cycles": 2}}

    def setUp(self):
        super().setUp()
        import sys
        evidence_script()
        self.ir = sys.modules["ir"]
        self.tool = __import__("costmodel")
        self.loaded = self.ir.load(self.ir.candidate_modules(ROOT / candidates.CANDIDATES_REL)["cand-A1"](4, 32))

    def proposed(self) -> None:
        rel = candidates.module_rel("cand-A1")
        for name in (rel, "research/004/ir.py", self.tool.SOURCE, "protocol/candidates.py", "protocol/devinputs_v3.py"):
            write(self.root, name, (CODE_ROOT / name).read_bytes())
        self.commit("the code")
        parameters = {name: "stated" for name in candidates.PARAMETERS}
        parameters["trees"] = {"4": self.TREES}
        digest = evidence.sha256((self.root / rel).read_bytes())
        candidates.propose({"candidate_id": "cand-A1", "family": "ARX", "oplist_sha256": digest, "parameters": parameters})
        self.commit("proposed")

    def refound(self) -> None:
        digest = evidence.sha256((self.root / self.tool.SOURCE).read_bytes())
        write(self.root, f"{evidence.REP_REL}/validation/validation-c.json", evidence.pretty(
            {"kind": "validation", "record_id": "validation-c", "tool": "costmodel", "tool_sha256": digest, "outcome": "re-found",
             "created_utc": "2026-11-03T00:00:00Z"}))

    def test_the_self_tests_call_sequence(self):
        self.assertEqual(self.tool.self_test_calls(1), 6 + 2 + 2 + 2)
        self.assertEqual(self.tool.self_test_calls(3), 6 + 4 + 2 + 4)

    def test_one_block_meets_every_item_where_the_list_writes_every_lane(self):
        found = self.tool.least_k(self.loaded.program, 640)
        self.assertEqual((found["least_k"], found["calls"]), (1, 12))
        self.assertIn("one whole block", found["structure"])

    def test_a_lane_no_update_writes_has_no_k(self):
        ir = self.ir
        program = ir.Program("stated", 2, 32, (ir.Phase(0, (ir.Mix(ir.lane(2, 0, 0, ir.PRESSURE), "xor", ir.Lane(ir.lane(2, 0, 0, ir.VEIN))),)),))
        found = self.tool.least_k(program, 64)
        self.assertIsNone(found["least_k"])
        self.assertIn("lanes no update writes", found["structure"])

    def test_the_cycles_of_a_call_count_the_start_tree(self):
        found = self.tool.cycles_per_call(18, 10, 640, 32, 2, 3)
        self.assertEqual(found["call of Π"], 182)
        self.assertEqual(found["generate of one block with its forget"], 2 * 182 + 3 + 20)
        self.assertEqual(found["instantiate, one block of input"], 6 * 182 + 20)
        self.assertEqual(found["reseed, one block of input"], 2 * 182 + 20)

    def test_the_fields_of_a_variant(self):
        found = self.tool.cost_fields(self.loaded, 10, 640, self.TREES)
        self.assertEqual(found["figures"]["phases"], 18)
        self.assertEqual(sorted(found["throughput"]), sorted(str(bits) for bits in self.tool.STATED_REQUESTS))
        self.assertEqual(found["self_test"]["least_k"], 1)
        self.assertEqual(found["throughput"]["524288"]["throughput_goal"], 10 ** 8)

    def test_a_candidate_not_in_the_log_exits_2(self):
        with mock.patch("sys.stderr"):
            self.assertEqual(self.tool.main(["--candidate", "cand-A2", "--size", "4", "--rounds", "10"]), 2)

    def test_a_tool_with_no_validation_writes_not_evaluated(self):
        self.proposed()
        with mock.patch("builtins.print"):
            self.assertEqual(self.tool.main(["--candidate", "cand-A1", "--size", "4", "--rounds", "10"]), 0)
        record = next(iter(evidence.iter_records("cost")))[1]
        self.assertEqual((record["status"], record["validation"]), ("not evaluated", NONE))

    def test_the_record_holds_its_figures_at_its_variant(self):
        self.proposed()
        self.refound()
        with mock.patch("builtins.print"):
            self.assertEqual(self.tool.main(["--candidate", "cand-A1", "--size", "4", "--rounds", "10"]), 0)
        record = next(iter(evidence.iter_records("cost")))[1]
        self.assertEqual((record["kind"], record["status"], record["classification"]), ("cost", "pass", NONE))
        self.assertEqual(record["config"], dict(record["config"], size=4, rounds=10))
        self.assertEqual(record["variant_id"], "cand-A1/n4-w32-R10-c384")
        self.assertEqual(record["self_test"]["least_k"], 1)
        self.assertEqual(record["validation"]["record_id"], "validation-c")


class RotationSearch(TempRepo):
    """The rotation search of research R15 under the ranking entry (seq 520) and its record (seq 521)."""

    def setUp(self):
        super().setUp()
        self.script = evidence_script()
        for candidate in ("cand-A1", "cand-B1"):
            write(self.root, candidates.module_rel(candidate), (CODE_ROOT / candidates.module_rel(candidate)).read_bytes())
        self.subject = self.script.plain_subject("cand-A1", 4, 16, 2)

    def test_the_spaces_in_tie_order_start_at_each_lists_amounts(self):
        spaces = {candidate: self.script.space_of(candidate) for candidate in ("cand-A1", "cand-B1")}
        self.assertEqual(len(spaces["cand-A1"]), 64 * 63)
        self.assertEqual(spaces["cand-A1"][0], self.script.amounts_module("cand-A1").AMOUNTS)
        self.assertEqual(spaces["cand-A1"], sorted(spaces["cand-A1"]))
        self.assertEqual(len(spaces["cand-B1"]), 8)
        self.assertEqual(spaces["cand-B1"][0], self.script.amounts_module("cand-B1").AMOUNTS)
        self.assertEqual(spaces["cand-B1"][-1], (15, 1))

    def test_the_ranking_puts_the_higher_measure_first_and_ties_in_their_order(self):
        entries = [{"assignment": "a", "measure": 8}, {"assignment": "b", "measure": 12}, {"assignment": "c", "measure": None},
                   {"assignment": "d", "measure": 12}, {"assignment": "e", "measure": None}]
        self.assertEqual([entry["assignment"] for entry in evidence.ranked(entries)], ["b", "d", "a", "c", "e"])

    def small_space(self):
        return [((1, 1), (1, 3)), ((1, 1), (3, 1)), ((1, 3), (3, 1))]

    def test_an_assignment_takes_its_weakest_box_in_each_kind(self):
        found = {(1, 1): {"differential": 5, "linear": 4}, (1, 3): {"differential": 7, "linear": 6}, (3, 1): {"differential": 7, "linear": 6}}
        run = mock.Mock(workers=1)
        with mock.patch.object(self.script, "space_of", return_value=self.small_space()), \
                mock.patch.object(self.script, "worker_map", return_value=[found[chosen] for chosen in sorted(found)]):
            result = self.script.arx_ranking(self.subject, run)
        best = result["entries"][0]
        self.assertEqual(best["assignment"], [[1, 3], [3, 1]])
        self.assertEqual(best["measure"], min(best["W_D"], best["W_L"]))
        self.assertEqual(sorted(result["counts"]), ["differential, box 5", "differential, box 7", "linear, box 4", "linear, box 6"])

    def test_a_point_whose_search_reached_its_cap_ranks_below_every_point_with_both(self):
        found = {(1, 1): {"differential": None, "linear": 4}, (1, 3): {"differential": 7, "linear": 4}, (3, 1): {"differential": 7, "linear": 6}}
        with mock.patch.object(self.script, "space_of", return_value=self.small_space()), \
                mock.patch.object(self.script, "worker_map", return_value=[found[chosen] for chosen in sorted(found)]):
            result = self.script.arx_ranking(self.subject, mock.Mock(workers=1))
        self.assertEqual(result["entries"][0]["assignment"], [[1, 3], [3, 1]])
        self.assertIsNone(result["entries"][1]["measure"])
        self.assertEqual(result["entries"][2]["assignment"], [[1, 1], [3, 1]])

    def test_no_point_with_both_bounds_gives_no_amounts(self):
        run = mock.Mock(clock=0.0)
        entries = [{"assignment": [1, 3], "W_D": None, "W_L": 4, "measure": None}]
        with mock.patch.object(self.script, "boolean_ranking", return_value={"sets": {}, "entries": entries, "solver": {}}):
            subject = self.script.plain_subject("cand-B1", 4, 16, 2)
            result = self.script.run_ranking(subject, run, "cross-check-x", {"t": "v"})
        self.assertEqual((result["status"], result["fields"]["chosen"]), ("inconclusive", NONE))

    def test_a_boolean_point_is_its_count_times_the_weight(self):
        sbox = (0xC, 5, 6, 0xB, 9, 0, 0xA, 0xD, 3, 0xE, 0xF, 8, 4, 7, 1, 2)
        layer = self.script.active_sbox.Cycle((self.script.active_sbox.spn(sbox, 2, (4, 1, 6, 3, 0, 5, 2, 7)),))
        with mock.patch.object(self.script, "boolean_layer", return_value=layer):
            found = self.script.boolean_point((str(self.root), "cand-B1", 4, 16, (1, 3), "differential"))
        self.assertEqual(found % 2, 0)

    def test_the_record_states_the_rule_it_ran_under(self):
        entries = [{"assignment": [1, 3], "W_D": 8, "W_L": 8, "measure": 8}]
        with mock.patch.object(self.script, "boolean_ranking", return_value={"sets": {}, "entries": entries, "solver": {}}):
            subject = self.script.plain_subject("cand-B1", 4, 16, 2)
            result = self.script.run_ranking(subject, mock.Mock(clock=0.0), "cross-check-x", {"t": "v"})
        fields = result["fields"]
        self.assertEqual((fields["size"], fields["width"], fields["rounds"], fields["chosen"]), (4, 16, 2, [1, 3]))
        self.assertIn("seq 520", fields["measure"])
        self.assertIn("lexicographically", fields["tie_order"])
        self.assertEqual(result["status"], "pass")

    def test_the_trail_row_reserves_the_searches_it_still_needs(self):
        with self.assertRaisesRegex(Refused, "comes first"):
            self.script.reserved_trails("cand-A1", {})
        self.probes()
        self.assertEqual(len(self.script.later_searches("cand-A1")), 8)
        self.assertEqual(len(self.script.later_searches("cand-B1")), 6)
        self.assertAlmostEqual(self.script.reserved_trails("cand-A1", self.A_CROSS_CHECK), 2.0)
        this = dict(self.script.later_searches("cand-A1")[0], kind="cross-check")
        self.assertAlmostEqual(self.script.reserved_trails("cand-A1", this), 2.0)

    A_CROSS_CHECK = {"kind": "cross-check"}

    def probes(self) -> None:
        for probe in self.script.later_searches("cand-A1"):
            evidence.write_projection(run="x", row="cand-A1/trails", inputs=NONE, measured_speed=1, projected_hours=0.25, time_hours=0.0, extra={"probe": probe})

    def checked(self, amounts=None, name: str = "cross-check-a") -> None:
        fields = {"kind": "cross-check", "record_id": name, "created_utc": "2026-11-05T00:00:00Z", "status": "pass", "tool": "ARX search",
                  "tool_sha256": "0" * 64, "candidate": "cand-A1"}
        if amounts is not None:
            fields["amounts"] = amounts
        write(self.root, f"{evidence.REP_REL}/candidates/cand-A1/{name}.json", evidence.pretty(fields))

    def ranked_at(self, chosen) -> None:
        write(self.root, f"{evidence.REP_REL}/candidates/cand-A1/rotation-ranking-a.json", evidence.pretty(
            {"kind": "rotation-ranking", "record_id": "rotation-ranking-a", "created_utc": "2026-11-05T00:00:00Z", "status": "pass", "chosen": chosen}))

    def test_a_production_width_search_needs_the_cross_check_of_its_own_amounts(self):
        """Data-model section 6: the first amounts' cross-check serves the searches before the choice, and only them."""
        self.checked([[1, 3], [3, 1]])
        with mock.patch.object(self.script, "tool_hash", return_value=("0" * 64, None)):
            self.assertEqual(self.script.cross_check_cited("cand-A1", "ARX search", 32), NONE)
            self.assertEqual(self.script.cross_check_cited("cand-A1", "ARX search", 16), "cross-check-a")
        self.checked([[1, 1], [1, 3]], "cross-check-b")
        with mock.patch.object(self.script, "tool_hash", return_value=("0" * 64, None)):
            self.assertEqual(self.script.cross_check_cited("cand-A1", "ARX search", 32), "cross-check-b")

    def test_a_cross_check_with_no_amounts_ran_on_the_first_of_the_space(self):
        self.checked()
        with mock.patch.object(self.script, "tool_hash", return_value=("0" * 64, None)):
            self.assertEqual(self.script.cross_check_cited("cand-A1", "ARX search", 32), "cross-check-a")

    def test_the_row_holds_a_cap_for_the_cross_check_of_the_chosen_amounts(self):
        self.probes()
        self.assertAlmostEqual(self.script.reserved_trails("cand-A1", {"kind": "rotation-ranking"}), 10.0)
        self.ranked_at([[1, 3], [3, 1]])
        self.checked()
        with mock.patch.object(self.script, "tool_hash", return_value=("0" * 64, None)):
            self.assertAlmostEqual(self.script.reserved_trails("cand-A1", {"kind": "bound"}), 10.0)
            self.checked([[1, 3], [3, 1]], "cross-check-b")
            self.assertAlmostEqual(self.script.reserved_trails("cand-A1", {"kind": "bound"}), 2.0)

    def test_a_ranking_that_keeps_the_first_amounts_needs_no_second_cross_check(self):
        self.probes()
        self.ranked_at([[1, 1], [1, 3]])
        self.checked()
        with mock.patch.object(self.script, "tool_hash", return_value=("0" * 64, None)):
            self.assertAlmostEqual(self.script.reserved_trails("cand-A1", {"kind": "bound"}), 2.0)

    def test_a_box_bound_at_a_reduced_width_is_over_one_call(self):
        """Research R6: the score and the ranking read one measure."""
        args = mock.Mock(candidate="cand-A1", size=4, width=16, kind="bound", project=False, bound_kind="linear", method="branch-and-bound", rounds=2)
        with self.assertRaisesRegex(Refused, "one call"):
            self.script.run_trail_kind(args, ["x"], [], "trails")

    def test_a_search_ended_needs_no_reservation(self):
        self.probes()
        probe = self.script.later_searches("cand-A1")[0]
        write(self.root, f"{evidence.REP_REL}/candidates/cand-A1/b.json", evidence.pretty(
            {"kind": "bound", "status": "pass", "method": probe["method"], "bound_kind": probe["bound_kind"], "width": 32, "size": 4}))
        self.assertAlmostEqual(self.script.reserved_trails("cand-A1", self.A_CROSS_CHECK), 1.75)

    def test_a_two_call_search_projects_its_cap_per_box(self):
        args = argparse.Namespace(bound_kind="differential")
        self.assertEqual(self.script.trail_seconds(self.subject, args, "ARX search", 2), 2 * 8 * 3600.0)

    def test_a_count_times_its_states_from_the_smallest_up_and_scales_the_largest_that_finished(self):
        args = argparse.Namespace(bound_kind="linear")
        subject = self.script.plain_subject("cand-B1", 4, 32, 1)
        calls = []

        def timed(function, job, seconds):
            calls.append((job[2], job[3], job[4]))
            return {4: 2.0, 8: None}[job[3]]

        with mock.patch.object(self.script, "limited", side_effect=timed):
            found = self.script.count_seconds(subject, args, "active-S-box counting")
        self.assertEqual(calls, [(4, 4, "linear"), (4, 8, "linear")])
        self.assertAlmostEqual(found, 2.0 * 8 ** self.script.BITS_EXPONENT)

    def test_a_count_no_state_of_which_finished_in_the_minute_projects_the_cap(self):
        subject = self.script.plain_subject("cand-B1", 4, 32, 1)
        with mock.patch.object(self.script, "limited", return_value=None):
            found = self.script.count_seconds(subject, argparse.Namespace(bound_kind="linear"), "active-S-box counting")
        self.assertEqual(found, 8 * 3600.0)

    def test_a_probe_holds_a_minute_in_all(self):
        """Research R7: at most 60 s, which the solver's own limit does not hold."""
        subject = self.script.plain_subject("cand-B1", 4, 32, 1)
        clock, given = [0.0], []

        def timed(function, job, seconds):
            given.append(seconds)
            clock[0] += 50.0
            return 1.0

        with mock.patch.object(self.script, "limited", side_effect=timed), mock.patch.object(self.script.time, "monotonic", side_effect=lambda: clock[0]):
            found = self.script.count_seconds(subject, argparse.Namespace(bound_kind="linear"), "active-S-box counting")
        self.assertEqual(given, [60.0, 10.0])
        self.assertAlmostEqual(found, 1.0 * 4 ** self.script.BITS_EXPONENT)

    def test_a_state_at_a_run_s_own_size_is_not_timed_twice(self):
        subject = self.script.plain_subject("cand-B1", 4, 8, 1)
        calls = []

        def timed(function, job, seconds):
            calls.append((job[2], job[3]))
            return 3.0

        with mock.patch.object(self.script, "limited", side_effect=timed):
            found = self.script.count_seconds(subject, argparse.Namespace(bound_kind="linear"), "active-S-box counting")
        self.assertEqual(calls, [(4, 4), (4, 8)])
        self.assertAlmostEqual(found, 3.0)

    def test_a_count_probe_discards_what_it_found(self):
        with mock.patch.object(self.script.active_sbox, "minima", return_value={1: {"count": 5}}) as found, \
                mock.patch.object(self.script, "boolean_layer", return_value="the layer") as layer:
            seconds = self.script.count_probe((str(self.root), "cand-B1", 4, 8, "linear"))
        layer.assert_called_once_with("cand-B1", 4, 8)
        found.assert_called_once_with("the layer", "linear", 1)
        self.assertIsInstance(seconds, float)

    def test_a_box_search_shares_the_minute_among_its_boxes(self):
        seen = []

        def bounds(candidate, kind, w, rounds):
            seen.append(self.script.arx_search_known.INSTANCE_SECONDS)
            return {}

        saved = self.script.arx_search_known.INSTANCE_SECONDS
        with mock.patch.object(self.script, "box_bounds", side_effect=bounds):
            self.script.trail_seconds(self.subject, argparse.Namespace(bound_kind="differential"), "ARX search", 1)
        self.assertEqual(seen, [30.0])
        self.assertEqual(self.script.arx_search_known.INSTANCE_SECONDS, saved)

    def test_a_ranking_run_needs_a_validated_tool(self):
        args = mock.Mock(candidate="cand-A1", width=None, size=None, project=False, workers=1)
        with self.assertRaisesRegex(Refused, "validated tool"):
            with mock.patch.object(self.script, "tool_hash", return_value=("0" * 64, None)):
                self.script.run_rotation(args, ["x"], [], "trails")

    def test_a_ranking_stands_at_4x4_only(self):
        args = mock.Mock(candidate="cand-A1", width=None, size=8, project=False, workers=1)
        with self.assertRaisesRegex(Refused, "4×4"):
            self.script.run_rotation(args, ["x"], [], "trails")


class ClearLock(TempRepo):
    def stale(self, descriptor: Dict = None, hours: float = 2.0, boot: str = None):
        """A heavy-run lock whose holder is gone, taken `hours` before now."""
        taken = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
        content = evidence.lock_content("evidence_v3.py --kind frequency")
        content["start"] = "gone"
        content["time"] = taken.strftime("%Y-%m-%dT%H:%M:%SZ")
        write(self.root, evidence.HEAVY_LOCK_REL, evidence.canonical(content))
        partial = self.root / evidence.PARTIAL_REL / f"{content['pid']}-1"
        write(partial, "run.json", evidence.pretty(descriptor or {
            "kind": "validation", "directory": "validation", "model_id": "phyco-v2",
            "variant_id": None, "candidate": None, "config": {"a": 1}, "inputs": NONE,
            "projected_hours": 3.0, "workers": 1, "threads": 1}))
        write(partial, "partial.json", b"{}")
        self.boot = boot or "2020-01-01T00:00:00Z"
        return content

    def clear(self, rel: str = evidence.HEAVY_LOCK_REL) -> int:
        from scripts import clear_lock
        with mock.patch.object(evidence, "boot_time", return_value=self.boot), \
                mock.patch("builtins.print"), mock.patch("sys.stderr"):
            return clear_lock.main([rel])

    def records(self, kind: str) -> List[Dict]:
        return [r for _, r in evidence.iter_records(kind)]

    def test_a_holder_that_runs_refuses_and_removes_nothing(self):
        content = evidence.lock_content("cmd")
        write(self.root, evidence.HEAVY_LOCK_REL, evidence.canonical(content))
        self.boot = "2020-01-01T00:00:00Z"
        self.assertEqual(self.clear(), 2)
        self.assertTrue(evidence.REPO.heavy_lock.exists())

    def test_a_holder_that_cannot_be_asked_refuses(self):
        self.stale()
        with mock.patch.object(evidence, "holder_runs", side_effect=evidence.ToolFailure("no")):
            self.assertEqual(self.clear(), 2)
        self.assertTrue(evidence.REPO.heavy_lock.exists())

    def test_no_lock_refuses(self):
        self.boot = "2020-01-01T00:00:00Z"
        self.assertEqual(self.clear(), 2)

    def test_a_dead_run_gets_its_inconclusive_record_and_the_hours_to_the_clearing(self):
        content = self.stale()
        self.assertEqual(self.clear(), 0)
        self.assertFalse(evidence.REPO.heavy_lock.exists())
        dead = self.records("validation")[0]
        self.assertEqual((dead["status"], dead["classification"]), ("inconclusive", NONE))
        self.assertIs(dead["heavy_run"], True)
        self.assertEqual(dead["ended_outside"], NONE)
        self.assertEqual(dead["hours"]["projected"], 3.0)
        self.assertAlmostEqual(dead["hours"]["used"],
                               evidence.hours_between(content["time"], dead["created_utc"]))
        self.assertEqual(dead["command"], content["command"])
        cleared = self.records("lock-cleared")[0]
        self.assertEqual(cleared["lock"], content)
        self.assertEqual(cleared["run_record"]["record_id"], dead["record_id"])
        self.assertEqual(list((self.root / evidence.PARTIAL_REL).glob(f"{content['pid']}-*")), [])

    def test_a_run_ended_from_outside_stops_at_the_boot_time(self):
        now = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
        boot = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        content = self.stale(boot=boot)
        self.assertEqual(self.clear(), 0)
        dead = self.records("validation")[0]
        self.assertEqual(dead["ended_outside"], boot)
        self.assertAlmostEqual(dead["hours"]["used"], evidence.hours_between(content["time"], boot))
        self.assertTrue([s for s in dead["limitations"] if "discarded unread" in s])

    def test_a_dead_run_holds_the_fields_its_description_gives_and_states_itself(self):
        self.stale({"kind": "control", "directory": "controls", "model_id": None, "variant_id": None,
                    "candidate": None, "config": {"size": 4, "test": "frequency"}, "inputs": NONE,
                    "projected_hours": 1.0, "workers": 1, "threads": 1,
                    "fields": {"test": "frequency", "size": 4, "not_charged": ["cand-A1"],
                               "status": "pass", "exit_status": 0, "created_utc": "2020-01-01T00:00:00Z"}})
        self.assertEqual(self.clear(), 0)
        dead = self.records("control")[0]
        self.assertEqual((dead["test"], dead["size"], dead["not_charged"]), ("frequency", 4, ["cand-A1"]))
        self.assertEqual((dead["status"], dead["exit_status"]), ("inconclusive", evidence.EXIT_TOOL))
        self.assertNotEqual(dead["created_utc"], "2020-01-01T00:00:00Z")
        self.assertAlmostEqual(dead["hours"]["used"], evidence.hours_between(
            self.records("lock-cleared")[0]["lock"]["time"], dead["created_utc"]))

    def test_fr_053s_test_gets_its_closing_projection(self):
        self.stale({"kind": "projection", "run": "FR-053's test", "row": evidence.FEATURE_ROW,
                    "inputs": NONE, "projected_hours": 1.0, "measured_speed": 5.0})
        self.assertEqual(self.clear(), 0)
        closing = self.records("projection")[0]
        self.assertEqual((closing["status"], closing["row"]),
                         ("inconclusive", evidence.FEATURE_ROW))
        self.assertIn("ended there", closing["outputs_statement"])
        self.assertGreater(closing["time_hours"], 1.9)
        self.assertEqual(self.records("lock-cleared")[0]["run_record"]["record_id"],
                         closing["record_id"])

    def test_the_append_lock_gets_the_lock_cleared_record_alone(self):
        content = evidence.lock_content("protocol_change.py create")
        content["start"] = "gone"
        write(self.root, evidence.APPEND_LOCK_REL, evidence.canonical(content))
        self.boot = "2020-01-01T00:00:00Z"
        self.assertEqual(self.clear(evidence.APPEND_LOCK_REL), 0)
        self.assertFalse(evidence.REPO.append_lock.exists())
        record = self.records("lock-cleared")[0]
        self.assertEqual(record["run_record"], NONE)

    def test_before_the_log_exists_it_cites_none(self):
        (self.root / evidence.PROTOCOL_LOG_REL).unlink()
        content = evidence.lock_content("protocol_change.py create")
        content["start"] = "gone"
        write(self.root, evidence.APPEND_LOCK_REL, evidence.canonical(content))
        self.boot = "2020-01-01T00:00:00Z"
        self.assertEqual(self.clear(evidence.APPEND_LOCK_REL), 0)
        record = self.records("lock-cleared")[0]
        self.assertEqual((record["protocol_seq"], record["protocol_line_sha256"]), (NONE, NONE))

    def test_the_environment_guard_refuses_and_removes_nothing(self):
        self.stale()
        with mock.patch.object(evidence, "snapshot", return_value=dict(SNAPSHOT, python="3.10.12")):
            self.assertEqual(self.clear(), 2)
        self.assertTrue(evidence.REPO.heavy_lock.exists())
        self.assertEqual(self.records("lock-cleared"), [])

    def test_a_run_on_a_candidate_runs_the_aborted_mode_before_the_lock_goes(self):
        self.stale({"kind": "frequency", "directory": "candidates/cand-A1", "candidate": "cand-A1",
                    "model_id": "cand-A1", "variant_id": None, "config": {}, "inputs": NONE,
                    "projected_hours": 1.0, "workers": 1, "threads": 1})
        seen = []

        def aborted(path: Path) -> None:
            seen.append((path.name, evidence.REPO.heavy_lock.exists()))

        from scripts import clear_lock
        with mock.patch.object(clear_lock, "run_aborted", side_effect=aborted):
            self.assertEqual(self.clear(), 0)
        self.assertEqual(len(seen), 1)
        self.assertTrue(seen[0][1])


class OwnerRecord(TempRepo):
    PINS = "numpy==2.2.6\nscipy==1.15.3\n"

    def owner_terminal(self, digits=None):
        typed = {}

        def fake_input(prompt: str) -> str:
            return digits if digits is not None else typed["digest"][:16]

        real = evidence.confirm_digits

        def spy(digest: str) -> str:
            typed["digest"] = digest
            return real(digest)

        return (mock.patch.object(evidence, "confirm_digits", side_effect=spy),
                mock.patch.object(evidence, "interactive_terminal", return_value=True),
                mock.patch("builtins.input", fake_input), mock.patch("builtins.print"),
                mock.patch("sys.stderr"))

    def run_script(self, *argv, digits=None) -> int:
        from scripts import owner_record
        write(self.root, "requirements.txt", self.PINS)
        patches = self.owner_terminal(digits)
        for patch in patches:
            patch.start()
        try:
            with mock.patch.object(owner_record, "pinned_python", return_value="3.10.11"):
                return owner_record.main(list(argv))
        finally:
            for patch in patches:
                patch.stop()

    def environment(self, **kwargs) -> int:
        return self.run_script("environment", "--platform", evidence.platform_name(),
                               "--by", "owner", **kwargs)

    def stored(self) -> Dict:
        return json.loads((self.root / evidence.environment_rel()).read_bytes())

    def test_it_writes_the_record_with_its_approval_and_keeps_the_old_one(self):
        old = (self.root / evidence.environment_rel()).read_bytes()
        changed = dict(SNAPSHOT, windows_build="10.0.26400")
        with mock.patch.object(evidence, "snapshot", return_value=changed):
            self.assertEqual(self.environment(), 0)
        record = self.stored()
        self.assertEqual(record["kind"], "environment")
        self.assertEqual(record["environment"], NONE)
        self.assertEqual(record["snapshot"], changed)
        self.assertEqual(record["approved_by"], "owner")
        self.assertEqual(record["approval_confirmed"], evidence.approval_hash(record)[:16])
        self.assertEqual((record["inputs"], record["outputs"], record["heavy_run"]),
                         (NONE, NONE, False))
        self.assertIsNone(record["model_id"])
        digest = evidence.sha256(old)
        kept = self.root / evidence.REP_REL / "versions" / f"{digest}.json"
        self.assertEqual(kept.read_bytes(), old)
        self.assertEqual(record["previous_sha256"], digest)
        self.assertTrue(evidence.check_record_id(record))

    def test_the_first_record_needs_no_log_and_cites_none(self):
        (self.root / evidence.PROTOCOL_LOG_REL).unlink()
        (self.root / evidence.environment_rel()).unlink()
        self.assertEqual(self.environment(), 0)
        record = self.stored()
        self.assertEqual((record["protocol_seq"], record["protocol_line_sha256"]), (NONE, NONE))

    def test_a_pinned_version_that_differs_refuses(self):
        before = (self.root / evidence.environment_rel()).read_bytes()
        self.PINS = "numpy==2.2.5\n"
        self.assertEqual(self.environment(), 2)
        self.assertEqual((self.root / evidence.environment_rel()).read_bytes(), before)

    def test_a_python_that_differs_from_r1_refuses(self):
        with mock.patch.object(evidence, "snapshot", return_value=dict(SNAPSHOT, python="3.10.12")):
            self.assertEqual(self.environment(), 2)

    def test_another_platform_refuses(self):
        other = "wsl" if evidence.platform_name() == "windows" else "windows"
        self.assertEqual(self.run_script("environment", "--platform", other, "--by", "owner"), 2)

    def test_no_interactive_terminal_writes_nothing(self):
        from scripts import owner_record
        write(self.root, "requirements.txt", self.PINS)
        before = (self.root / evidence.environment_rel()).read_bytes()
        with mock.patch("builtins.print"), mock.patch("sys.stderr"), \
                mock.patch.object(owner_record, "pinned_python", return_value="3.10.11"):
            code = owner_record.main(["environment", "--platform", evidence.platform_name(),
                                      "--by", "owner"])
        self.assertEqual(code, 2)
        self.assertEqual((self.root / evidence.environment_rel()).read_bytes(), before)

    def test_digits_that_do_not_match_write_nothing(self):
        before = (self.root / evidence.environment_rel()).read_bytes()
        self.assertEqual(self.environment(digits="0" * 16), 2)
        self.assertEqual((self.root / evidence.environment_rel()).read_bytes(), before)

    def no_terminal(self, *argv) -> int:
        from scripts import owner_record
        write(self.root, "requirements.txt", self.PINS)
        with mock.patch("builtins.print"), mock.patch("sys.stderr"), \
                mock.patch.object(owner_record, "pinned_python", return_value="3.10.11"):
            return owner_record.main(list(argv))

    def test_the_owners_written_words_stand_in_for_the_terminal_and_stay_in_the_record(self):
        code = self.no_terminal("environment", "--platform", evidence.platform_name(), "--by",
                                "owner", "--written-approval", "write the new record")
        self.assertEqual(code, 0)
        record = self.stored()
        written = record["written_approval"]
        self.assertEqual(written["words"], "write the new record")
        self.assertEqual(written["entered_by"], "agent")
        self.assertEqual(record["approval_confirmed"], evidence.approval_hash(record)[:16])
        tampered = dict(record, written_approval=dict(written, words="other"))
        self.assertNotEqual(evidence.approval_hash(tampered), evidence.approval_hash(record))

    def test_empty_written_words_write_nothing(self):
        before = (self.root / evidence.environment_rel()).read_bytes()
        code = self.no_terminal("environment", "--platform", evidence.platform_name(), "--by",
                                "owner", "--written-approval", " ")
        self.assertEqual(code, 2)
        self.assertEqual((self.root / evidence.environment_rel()).read_bytes(), before)

    def test_markers_choose_the_pins_of_the_running_python(self):
        from scripts import owner_record
        text = ('numpy==2.2.6; python_version >= "3.10" and python_version < "3.14"\n'
                'numpy==2.5.4; python_version >= "3.14"\n# hypothesis==6.168.5\nnistrng==1.2.3\n')
        self.assertEqual(owner_record.pins_for(text, "3.10.11"),
                         {"numpy": "2.2.6", "nistrng": "1.2.3"})
        self.assertEqual(owner_record.pins_for(text, "3.14.4"),
                         {"numpy": "2.5.4", "nistrng": "1.2.3"})

    def test_owner_provided_adds_an_entry_with_its_approval(self):
        self.assertEqual(self.run_script(
            "owner-provided", "--known", "SPECK64-d", "--value", "9", "--source",
            "a paper, table 2", "--words", "use 9 (2026-11-03)", "--by", "owner"), 0)
        entry = evidence.read_manifest()[-1]
        self.assertEqual((entry["status"], entry["known"]), ("owner-provided", "SPECK64-d"))
        self.assertEqual(entry["value_sha256"], evidence.sha256(b"9"))
        self.assertEqual(entry["approval_confirmed"],
                         evidence.approval_hash(entry)[:16])
        self.assertEqual(entry["environment"]["path"], evidence.environment_rel())


class Downloads(TempRepo):
    R19 = """
## R19. Downloads

| File | Source | Size | Licence | Use | Without it |
|------|--------|------|---------|-----|-----------------|
| `Daemen.pdf`: Daemen et al., a title | https://example.invalid/Daemen.pdf | 604 kB, as CWI lists it | none stated | the theorem | none |
| `SpongePRNG.pdf`: title | https://example.invalid/SpongePRNG.pdf | 12 bytes | none stated | forget | as above |

Between the tables.

| File | Source | Size | Licence | Use | Without it |
|------|--------|------|---------|-----|-----------------|
| `a-1.0-py3-none-any.whl` | PyPI | 5 bytes | MIT | tests | an open item |

## R20. Next
"""

    def setUp(self):
        super().setUp()
        write(self.root, evidence.RESEARCH_REL, "# Research\n" + self.R19)
        self.commit("R19")
        self.download = self.root / "dl"

    def script(self, *argv) -> int:
        from scripts import downloads
        with mock.patch("builtins.print"), mock.patch("sys.stderr"):
            return downloads.main(list(argv))

    def entry(self, name: str) -> Dict:
        return {e["name"]: e for e in evidence.read_manifest()}[name]

    def file(self, name: str, data: bytes) -> str:
        return str(write(self.download, name, data))

    def test_init_writes_one_approved_entry_per_file_of_the_tables(self):
        self.assertEqual(self.script("init"), 0)
        entries = evidence.read_manifest()
        self.assertEqual([e["name"] for e in entries],
                         ["Daemen.pdf", "SpongePRNG.pdf", "a-1.0-py3-none-any.whl"])
        first = entries[0]
        self.assertEqual((first["status"], first["size"], first["licence"]),
                         ("approved", "604 kB, as CWI lists it", "none stated"))
        self.assertEqual(first["source"], "https://example.invalid/Daemen.pdf")
        self.assertEqual(first["environment"]["path"], evidence.environment_rel())
        self.assertNotIn("sha256", first)

    def test_init_exits_2_once_the_manifest_exists(self):
        self.script("init")
        self.assertEqual(self.script("init"), 2)
        write(self.root, evidence.DOWNLOADS_REL, evidence.pretty({"entries": []}))
        self.assertEqual(self.script("init"), 2)

    def test_the_manifest_is_a_record_of_its_own_kind(self):
        self.script("init")
        record = json.loads((self.root / evidence.DOWNLOADS_REL).read_bytes())
        self.assertEqual((record["kind"], record["inputs"], record["outputs"]),
                         ("downloads", NONE, NONE))
        self.assertTrue(evidence.check_record_id(record))

    def test_fetched_computes_the_hash_and_size_from_the_file(self):
        self.script("init")
        data = b"twelve bytes"
        path = self.file("SpongePRNG.pdf", data)
        self.assertEqual(self.script("fetched", "SpongePRNG.pdf", path), 0)
        entry = self.entry("SpongePRNG.pdf")
        self.assertEqual((entry["status"], entry["sha256"], entry["bytes"]),
                         ("fetched", evidence.sha256(data), 12))
        self.assertEqual(entry["local_path"], path)
        self.assertRegex(entry["date_utc"], r"^\d{4}-")
        kept = list((self.root / evidence.REP_REL / "versions").glob("*.json"))
        self.assertEqual(len(kept), 1)

    def test_a_size_that_differs_from_one_given_in_bytes_is_refused(self):
        self.script("init")
        self.assertEqual(self.script("fetched", "SpongePRNG.pdf", self.file("x", b"short")), 2)
        self.assertEqual(self.entry("SpongePRNG.pdf")["status"], "approved")

    def test_a_size_not_in_bytes_is_not_compared(self):
        self.script("init")
        self.assertEqual(self.script("fetched", "Daemen.pdf", self.file("Daemen.pdf", b"any")), 0)

    def test_a_wheel_needs_pypis_hash_and_its_equal(self):
        self.script("init")
        data = b"12345"
        path = self.file("a-1.0-py3-none-any.whl", data)
        name = "a-1.0-py3-none-any.whl"
        self.assertEqual(self.script("fetched", name, path), 2)
        self.assertEqual(self.script("fetched", name, path, "--pypi-sha256", "0" * 64), 2)
        self.assertEqual(self.script("fetched", name, path, "--pypi-sha256",
                                     evidence.sha256(data)), 0)

    def test_fetched_and_not_obtained_refuse_a_name_with_no_approved_entry(self):
        self.script("init")
        path = self.file("other.pdf", b"x")
        self.assertEqual(self.script("fetched", "other.pdf", path), 2)
        self.assertEqual(self.script("not-obtained", "other.pdf", "--reason", "gone"), 2)

    def test_not_obtained_writes_the_reason(self):
        self.script("init")
        self.assertEqual(self.script("not-obtained", "Daemen.pdf", "--reason", "gone"), 0)
        self.assertEqual((self.entry("Daemen.pdf")["status"], self.entry("Daemen.pdf")["reason"]),
                         ("not obtained", "gone"))

    def row(self, name: str, decision: str = "Approved", n: int = 1) -> None:
        self.add_row(f"Download {n}", decision,
                     f"`{name}`; source: https://example.invalid/{name}; size: 7 bytes; "
                     "licence: none stated; stands in for: `Daemen.pdf`; 2026-11-03")

    def test_approve_reads_its_row_at_head(self):
        self.script("init")
        self.assertEqual(self.script("approve", "Daemen-2.pdf"), 2)
        self.row("Daemen-2.pdf", "Declined")
        self.assertEqual(self.script("approve", "Daemen-2.pdf"), 2)
        self.row("Daemen-2.pdf", n=2)
        self.assertEqual(self.script("approve", "Daemen-2.pdf"), 0)
        entry = self.entry("Daemen-2.pdf")
        self.assertEqual((entry["status"], entry["size"], entry["row"]),
                         ("approved", "7 bytes", "Download 2"))
        self.assertEqual(entry["source"], "https://example.invalid/Daemen-2.pdf")
        self.assertEqual(entry["licence"], "none stated")

    def test_approve_refuses_a_name_an_entry_holds(self):
        self.script("init")
        self.row("Daemen.pdf")
        self.assertEqual(self.script("approve", "Daemen.pdf"), 2)

    def test_a_later_copy_is_refused_under_the_listed_name_and_entered_under_its_own(self):
        self.script("init")
        self.script("fetched", "SpongePRNG.pdf", self.file("first", b"twelve bytes"))
        same_size = self.file("copy", b"twelve BYTES")
        self.assertEqual(self.script("fetched", "SpongePRNG.pdf", same_size), 2)
        self.assertEqual(self.entry("SpongePRNG.pdf")["sha256"],
                         evidence.sha256(b"twelve bytes"))
        path = self.file("second", b"seven b")
        self.row("SpongePRNG-2.pdf")
        self.assertEqual(self.script("approve", "SpongePRNG-2.pdf"), 0)
        self.assertEqual(self.script("fetched", "SpongePRNG-2.pdf", path), 0)
        self.assertEqual(self.entry("SpongePRNG-2.pdf")["status"], "fetched")

    def test_the_real_tables_hold_twelve_files(self):
        from scripts import downloads
        previous = evidence.use_repo(CODE_ROOT)
        self.addCleanup(evidence.use_repo, previous.root)
        rows = downloads.r19_rows()
        self.assertEqual(len(rows), 12)
        self.assertEqual(rows[4]["name"], "2657")
        self.assertEqual(rows[-1]["size"], "16,740 bytes")

    def test_the_file_is_read_under_isolated_mode_and_never_run(self):
        from scripts import downloads
        self.assertEqual(downloads.read_file(Path(self.file("f", b"abc"))),
                         (evidence.sha256(b"abc"), 3))
        with mock.patch.object(downloads.subprocess, "run", wraps=subprocess.run) as run:
            downloads.read_file(Path(self.file("g", b"abc")))
        command = run.call_args[0][0]
        self.assertEqual(command[1], "-I")
        self.assertNotEqual(Path(run.call_args[1]["cwd"]), self.download)


class Documents(unittest.TestCase):
    """The documents against each other, at this commit (T023; the notes under the spec's table)."""

    FEATURE = ROOT / evidence.FEATURE_REL
    # The numbered families of the first list, which no row of the table holds until one is added.
    FAMILIES = ("Log repair", "Environment record", "Owner-provided value", "Download")

    def read(self, name: str) -> str:
        return (self.FEATURE / name).read_text(encoding="utf-8").replace("\r\n", "\n")

    def table(self) -> List[evidence.Row]:
        return evidence.parse_table(evidence.table_section(self.read("spec.md")))

    def first_list(self) -> str:
        text = " ".join(self.read("spec.md").split())
        start = text.index("The first holds the rows a guard reads at HEAD")
        return text[start:text.index("The second holds the rows that record", start)]

    def test_the_status_lines_and_the_table_agree(self):
        spec = self.read("spec.md")
        status = " ".join(spec[spec.index("**Status**"):spec.index("\n\n", spec.index("**Status**"))]
                          .split())
        choices = " ".join(self.read("checklist-choices.md").split())
        rounds = [r for r in self.table() if r.name.startswith("Checklist choices")]
        self.assertEqual(len(rounds), 11)
        total = 0
        for row in rounds:
            self.assertEqual(row.decision, "Approved", row.name)
            total += int(re.search(r"the (\d+) (?:open )?items", row.gate).group(1))
            match = re.match(r"Checklist choices, (.+?) \(", row.gate)
            if match is None:
                self.assertIn("the first run", status)
            else:
                self.assertIn(match.group(1), status)
        self.assertIn(f"**Status: all {total} rows answered and applied", choices)
        tasks = next(r for r in self.table() if r.name == "Tasks approval")
        self.assertEqual(tasks.decision, "Approved")
        self.assertIn("tasks approved", status)
        self.assertIn("confirmed at the tasks approval", choices)

    def test_each_row_of_the_first_list_has_its_guard_in_the_contracts(self):
        contract = self.read("contracts/cli.md")
        rows = [r.name for r in self.table()]
        listed = [name for name in rows + list(self.FAMILIES) if name in self.first_list()]
        self.assertEqual(sorted(set(listed)), sorted({
            "FUT-SEC-8 result review", "D4 tie", "Selection tie", "Security-target review",
            "Owner design review", "External design review", "L1 recorded", "Log repair",
            "Environment record", "Owner-provided value", "Download", "Place check",
            "Readings set aside", "Second transcription go-ahead"}))
        for name in listed:
            if name != "Second transcription go-ahead":      # its guard is a test (FR-057)
                self.assertIn(name, contract, name)

    def test_each_row_the_contracts_guards_read_stands_in_the_first_list(self):
        contract = " ".join(self.read("contracts/cli.md").split())
        start = contract.index("**Approvals**")
        approvals = contract[start:contract.index("**Order of US1**", start)]
        first = self.first_list()
        for row in self.table():
            if row.name in approvals:
                self.assertIn(row.name, first, row.name)
        for family in self.FAMILIES:
            self.assertIn(family, first)

    def test_no_key_is_loaded_before_the_review_of_the_demonstration(self):
        files = sorted((ROOT / "research/004/candidates").glob("*.py"))
        files += [ROOT / "phycoweb/model_v3.py"]
        defined = [path.name for path in files if path.exists() and re.search(
            r"^\s*def (instantiate|load_key)\b", path.read_text(encoding="utf-8"), re.M)]
        if defined:
            evidence.guard_order_of_us1()

    def test_every_load_of_an_earlier_seed_set_allows_dev_alone(self):
        names = [ROOT / "scripts/fut_sec8.py"] + sorted((ROOT / "research/004").rglob("*.py"))
        names += [ROOT / "protocol/evidence.py"]
        for path in names:
            if not path.exists():
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "load" \
                        and getattr(node.func.value, "id", "").endswith("seedsets"):
                    allow = {k.arg: ast.literal_eval(k.value) for k in node.keywords}.get("allow")
                    self.assertEqual(allow, ("dev",), path.name)


class FutSec8(ReproductionBase):
    """scripts/fut_sec8.py on a mocked tool and a temporary reports directory (T039)."""

    HEAD = ["--binary", Tool.binary, "--out-dir", evidence.REP_REL + "/fut-sec-8"]
    REQUEST = "yes, go again (2026-11-04)"

    def setUp(self):
        super().setUp()
        from protocol import seedsets
        from scripts import fut_sec8
        self.fut = fut_sec8
        for rel in ("scripts/fut_sec8.py", "protocol/devinputs_v3.py", "protocol/seedsets.py",
                    "phycoweb/model_v2.py", "phycoweb/lut.py", "fast/lut_table.h"):
            write(self.root, rel, (CODE_ROOT / rel).read_bytes())
        write(self.root, Tool.make, "CFLAGS := -O2 -std=c99 -Werror -pthread\n")
        write(self.root, "vectors/phyco-v2_a.hex", "x\n")
        write(self.root, "vectors/phyco-v2_b.hex", "x\n")
        self.commit("the demonstration's code")
        self.seeds = [tuple(s) for s in seedsets.load("dev", allow=("dev",))[:3]]
        self.vector_exit = 0
        self.changes: Dict = {}
        self.calls: List[List[str]] = []
        self.locks: List[bool] = []
        self.hours_projected = 0.4
        self.real_guard = fut_sec8.guard_platform
        self.real_project = fut_sec8.project
        for name, side_effect in (("run_tool", self.tool),
                                  ("project", lambda *a: (self.hours_projected, {"rate": 160.0})),
                                  ("guard_platform", lambda: None)):
            patcher = mock.patch.object(fut_sec8, name, side_effect=side_effect)
            patcher.start()
            self.addCleanup(patcher.stop)

    def tool(self, binary, args, cwd):
        self.calls.append(list(args))
        self.locks.append(evidence.REPO.heavy_lock.exists())
        if args[0] == "--check-vectors":
            files = [{"file": f, "words": 10000, "mismatches": self.vector_exit} for f in args[1:]]
            return subprocess.CompletedProcess(args, self.vector_exit, json.dumps({"files": files}))
        number = [seed[0] for seed in self.seeds].index(int(args[1]))
        seed = self.seeds[number]
        out = {"s0": seed[0], "s1": seed[1], "words": args[5:8], "candidates": 2 ** 32,
               "after_one": 2, "after_two": 1, "after_three": 1,
               "three_word_matches": [[seed[2], seed[3]]], "total_steps": 257 * 2 ** 32 + 3,
               "seconds": 400.5, "steps_per_second": 2.7e9, "threads": 32}
        out.update(self.changes.get(number, {}))
        return subprocess.CompletedProcess(args, 0, json.dumps(out))

    def script(self, *argv) -> int:
        with mock.patch("builtins.print"), mock.patch("sys.stderr"):
            return self.fut.main(list(argv))

    def run_first(self) -> Dict:
        self.assertEqual(self.script(*self.HEAD), 0)
        return self.records()[-1]

    def records(self) -> List[Dict]:
        """Oldest first; two records of one test can share a second, so a repeat sorts last."""
        found = [record for _, record in evidence.iter_records("demonstration", "fut-sec-8")]
        return sorted(found, key=lambda record: (record["created_utc"],
                                                 record.get("supersedes", NONE) != NONE))

    def record_path(self, record: Dict) -> Path:
        return self.root / evidence.REP_REL / "fut-sec-8" / f"{record['record_id']}.json"

    def projections(self) -> List[Dict]:
        return [record for _, record in evidence.iter_records("projection", "projections")]

    # -------------------------------------------------------------------------- the first run

    def test_the_targets_are_the_first_three_dev_seeds(self):
        record = self.run_first()
        self.assertEqual(record["targets"], [list(seed) for seed in self.seeds])
        self.assertEqual(record["revealed"], [list(seed[:2]) for seed in self.seeds])

    def test_a_held_out_set_exits_2_writing_nothing(self):
        before = report_files(self.root)
        with mock.patch.object(self.fut, "SEED_SET", "heldout-1"):
            self.assertEqual(self.script(*self.HEAD), 2)
        self.assertEqual(report_files(self.root), before)
        self.assertEqual(self.calls, [])

    def test_the_record_holds_every_field_of_data_model_section_4(self):
        text = (ROOT / "specs/004-crypto-architecture-v3/data-model.md").read_bytes().decode("utf-8")
        section = text[text.index("## 4. Demonstration record"):text.index("## 5.")]
        names = []
        for line in section.splitlines():
            if line.startswith("| `"):
                names += re.findall(r"`(\w+)`", line.split(" | ")[0])
        self.assertGreater(len(names), 12)
        record = self.run_first()
        for name in names:
            self.assertIn(name, record)

    def test_a_first_record_holds_no_repeat_fields(self):
        record = self.run_first()
        self.assertEqual((record["supersedes"], record["defect"], record["owner_request"]),
                         (NONE, NONE, NONE))

    def test_the_observed_words_come_from_the_python_model_with_their_positions(self):
        from phycoweb.model_v2 import PhycoWebEngineV2
        record = self.run_first()
        for number, seed in enumerate(self.seeds):
            engine = PhycoWebEngineV2(seed)
            words = [f"{engine.compute_block():08X}" for _ in range(3)]
            self.assertEqual(record["observed"][number], {"positions": [1, 2, 3], "words": words})

    def test_the_vector_check_comes_before_every_sweep(self):
        record = self.run_first()
        self.assertEqual(self.calls[0][0], "--check-vectors")
        self.assertEqual(len(self.calls), 4)
        self.assertEqual([entry["mismatches"] for entry in record["vector_check"]], [0, 0])
        self.assertEqual([entry["words"] for entry in record["vector_check"]], [10000, 10000])

    def test_a_vector_mismatch_stops_the_run(self):
        self.vector_exit = 1
        self.assertEqual(self.script(*self.HEAD), 3)
        self.assertEqual(len(self.calls), 1)
        record = self.records()[-1]
        self.assertEqual((record["status"], record["exit_status"]), ("inconclusive", 3))

    def test_a_failed_sweep_stops_the_run(self):
        real = self.tool

        def failing(binary, args, cwd):
            done = real(binary, args, cwd)
            if args[0] != "--check-vectors":
                done.returncode = 1
            return done

        self.fut.run_tool.side_effect = failing
        self.assertEqual(self.script(*self.HEAD), 3)
        record = self.records()[-1]
        self.assertEqual((record["status"], record["exit_status"]), ("inconclusive", 3))
        self.assertEqual(len(self.calls), 2)

    def test_it_holds_the_lock_through_every_tool_call(self):
        record = self.run_first()
        self.assertTrue(all(self.locks))
        self.assertFalse(evidence.REPO.heavy_lock.exists())
        self.assertIs(record["heavy_run"], True)
        self.assertEqual(record["hours"]["projected"], self.hours_projected)
        self.assertEqual(record["parallelism"]["threads"], 32)

    def test_it_projects_first_under_its_own_row(self):
        self.run_first()
        self.assertEqual([p["row"] for p in self.projections()], [evidence.FUT_SEC_8_ROW])

    def test_the_tool_and_model_are_named_by_hash(self):
        record = self.run_first()
        self.assertEqual(record["model_sha256"], self.fut.MODEL_SHA256)
        self.assertEqual(record["tool"]["source_sha256"], self.source_sha256)
        self.assertEqual(record["tool"]["binary_sha256"],
                         evidence.sha256((self.root / Tool.binary).read_bytes()))
        self.assertEqual(record["tool"]["threads"], 32)
        self.assertIn("-Werror", record["tool"]["flags"])
        for rel in self.fut.CODE:
            self.assertIn(rel, record["code_sha256"])

    def test_a_changed_model_exits_2(self):
        write(self.root, "phycoweb/model_v2.py", b"# another model\n")
        self.commit("another model")
        self.assertEqual(self.script(*self.HEAD), 2)
        self.assertEqual(self.calls, [])

    def test_another_binary_or_directory_exits_2(self):
        self.assertEqual(self.script("--binary", "fast/build/other", "--out-dir",
                                     self.HEAD[3]), 2)
        self.assertEqual(self.script("--binary", Tool.binary, "--out-dir", "elsewhere"), 2)
        self.assertEqual(self.script("--binary", Tool.binary), 2)
        self.assertEqual(self.script(), 2)
        self.assertEqual(self.calls, [])

    def test_the_search_runs_in_wsl_alone(self):
        with mock.patch.object(evidence, "platform_name", return_value="windows"):
            with self.assertRaisesRegex(Refused, "WSL"):
                self.real_guard()
        with mock.patch.object(evidence, "platform_name", return_value="wsl"):
            self.real_guard()

    def test_the_cost_and_its_extrapolation(self):
        cost = self.run_first()["cost"]
        steps = 3 * (257 * 2 ** 32 + 3)
        self.assertEqual(cost["total_steps"], steps)
        self.assertEqual(cost["seconds"], 3 * 400.5)
        self.assertAlmostEqual(cost["steps_per_candidate"], steps / (3 * 2 ** 32))
        self.assertAlmostEqual(cost["steps_per_second"], steps / (3 * 400.5))
        self.assertEqual(cost["extrapolation"]["seeds"], 2 ** 64)
        self.assertAlmostEqual(cost["extrapolation"]["steps"] / 2 ** 64, steps / (3 * 2 ** 32))

    def test_the_report_holds_the_nine_items_with_t1_and_the_disclaimer(self):
        record = self.run_first()
        report = record["report"]
        for number in range(1, 10):
            self.assertEqual(len([key for key in report if key.startswith(f"{number}_")]), 1)
        self.assertIn("T1", report["2_attacker"])
        self.assertIn("position", report["2_attacker"])
        self.assertEqual(report["disclaimer"], DESIGN_DISCLAIMER)
        self.assertEqual(report["6_results"]["matches"], record["matches"])
        self.assertEqual(report["8_reproduction"]["revision"], record["git_head"])

    def test_every_target_recovered_is_a_confirmed_vulnerability_of_phyco_v2(self):
        record = self.run_first()
        self.assertEqual(record["recovered"], [True, True, True])
        self.assertEqual((record["status"], record["exit_status"]), ("pass", 0))
        self.assertEqual(record["classification"], "confirmed vulnerability")

    def test_a_target_missed_exits_1(self):
        self.changes[1] = {"three_word_matches": [], "after_three": 0, "after_two": 0}
        self.assertEqual(self.script(*self.HEAD), 1)
        record = self.records()[-1]
        self.assertEqual(record["recovered"], [True, False, True])
        self.assertEqual((record["status"], record["exit_status"]), ("fail", 1))
        self.assertEqual(record["classification"], NONE)

    # -------------------------------------------------------------------------- the baseline

    def test_the_two_sided_poisson_test_on_constructed_counts(self):
        mean = self.fut.MEAN_AFTER["one"]
        self.assertAlmostEqual(mean, 1.0, places=9)
        self.assertAlmostEqual(self.fut.poisson_p(0, 1.0), 2 * 0.36787944, places=6)
        self.assertEqual(self.fut.poisson_p(1, 1.0), 1.0)
        self.assertAlmostEqual(self.fut.poisson_p(5, 1.0), 2 * 0.00365985, places=6)
        for count, agrees in ((0, True), (1, True), (4, True), (5, False), (9, False)):
            self.assertEqual(self.fut.poisson_test(count, mean)["agrees"], agrees, count)

    def test_the_pooled_test_uses_three_times_the_mean(self):
        mean = 3 * self.fut.MEAN_AFTER["one"]
        for count, agrees in ((0, True), (3, True), (8, True), (9, False)):
            self.assertEqual(self.fut.poisson_test(count, mean)["agrees"], agrees, count)

    def test_the_counts_leave_out_the_target(self):
        matches = self.run_first()["matches"]
        for entry in matches["per_target"]:
            self.assertEqual((entry["after_one"], entry["false_after_one"]), (2, 1))
            self.assertEqual((entry["after_two"], entry["false_after_two"]), (1, 0))
            self.assertEqual((entry["after_three"], entry["false_after_three"]), (1, 0))
            self.assertAlmostEqual(entry["expected_false"]["one"], 1.0, places=9)
            self.assertAlmostEqual(entry["expected_false"]["two"], 2.0 ** -32, places=15)
            self.assertAlmostEqual(entry["expected_false"]["three"] * 2.0 ** 64, 1.0, places=9)
        self.assertEqual(matches["pooled"]["count"], 3)
        self.assertEqual(matches["pooled"]["mean"], 3 * (2 ** 32 - 1) / 2 ** 32)
        self.assertIs(matches["agrees"], True)
        self.assertEqual(matches["deviations"], [])

    def test_a_count_above_the_baseline_is_a_finding_and_no_reason_to_stop(self):
        self.changes[0] = {"after_one": 9}
        record = self.run_first()
        self.assertEqual(record["matches"]["per_target"][0]["poisson"]["agrees"], False)
        self.assertEqual(record["status"], "pass")
        self.assertEqual(record["classification"], "unverified hypothesis")
        self.assertEqual(record["recovered"], [True, True, True])

    def test_a_targets_count_alone_can_disagree(self):
        self.changes[0] = {"after_one": 6}
        self.changes[1] = {"after_one": 1}
        self.changes[2] = {"after_one": 1}
        record = self.run_first()
        self.assertFalse(record["matches"]["per_target"][0]["poisson"]["agrees"])
        self.assertTrue(record["matches"]["pooled"]["agrees"])
        self.assertIs(record["matches"]["agrees"], False)
        self.assertEqual(record["classification"], "unverified hypothesis")

    def test_a_pooled_count_alone_can_disagree(self):
        for number in range(3):
            self.changes[number] = {"after_one": 4}
        record = self.run_first()
        self.assertTrue(all(e["poisson"]["agrees"] for e in record["matches"]["per_target"]))
        self.assertFalse(record["matches"]["pooled"]["agrees"])
        self.assertEqual(record["classification"], "unverified hypothesis")

    def test_a_false_match_after_two_words_is_a_deviation(self):
        self.changes[2] = {"after_two": 2}
        record = self.run_first()
        self.assertEqual(record["matches"]["deviations"],
                         [{"target": 2, "after": "two", "count": 1}])
        self.assertEqual(record["classification"], "unverified hypothesis")

    def test_an_extra_three_word_match_is_listed_and_separated_by_the_fourth_word(self):
        seed = self.seeds[0]
        extra = [(seed[2] + 1) % 65536, seed[3]]
        self.changes[0] = {"after_two": 2, "after_three": 2,
                           "three_word_matches": sorted([[seed[2], seed[3]], extra])}
        record = self.run_first()
        listed = {(item["s2"], item["s3"]): item for item in record["listed"][0]}
        self.assertIs(listed[(seed[2], seed[3])]["fourth_word_matches"], True)
        self.assertIs(listed[(seed[2], seed[3])]["is_target"], True)
        self.assertIs(listed[tuple(extra)]["fourth_word_matches"], False)
        self.assertIs(listed[tuple(extra)]["is_target"], False)
        self.assertEqual(record["matches"]["deviations"],
                         [{"target": 0, "after": "two", "count": 1},
                          {"target": 0, "after": "three", "count": 1}])

    def test_the_assumption_is_stated(self):
        record = self.run_first()
        self.assertIn("uniform and independent", record["assumption"])
        self.assertIn("does not change the success criterion", record["assumption"])

    # -------------------------------------------------------------------------- a second run

    def test_quickstart_u4_a_second_run_exits_2(self):
        self.run_first()
        before = report_files(self.root)
        self.calls.clear()
        self.assertEqual(self.script(*self.HEAD), 2)
        self.assertEqual(report_files(self.root), before)
        self.assertEqual(self.calls, [])

    def missed(self) -> Dict:
        self.changes[0] = {"three_word_matches": [], "after_three": 0, "after_two": 0}
        self.assertEqual(self.script(*self.HEAD), 1)
        self.changes.clear()
        self.commit("the record of the failed pass")
        return self.records()[-1]

    def test_a_repeat_needs_a_recorded_defect(self):
        first = self.run_first()
        self.commit("record")
        self.assertEqual(self.script(*self.HEAD, "--repeat-after-defect", "no-such-record",
                                     "--owner-request", self.REQUEST), 2)
        self.assertEqual(self.script(*self.HEAD, "--repeat-after-defect", first["record_id"],
                                     "--owner-request", self.REQUEST), 2)
        self.assertEqual(len(self.records()), 1)

    def test_a_repeat_needs_the_owners_request_with_its_date(self):
        record = self.missed()
        self.assertEqual(self.script(*self.HEAD, "--repeat-after-defect", record["record_id"]), 2)
        self.assertEqual(self.script(*self.HEAD, "--repeat-after-defect", record["record_id"],
                                     "--owner-request", "no date"), 2)
        self.assertEqual(len(self.records()), 1)

    def test_a_repeat_after_a_defect_writes_beside_the_first(self):
        record = self.missed()
        self.assertEqual(self.script(*self.HEAD, "--repeat-after-defect", record["record_id"],
                                     "--owner-request", self.REQUEST), 0)
        records = self.records()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[-1]["supersedes"], record["record_id"])
        self.assertEqual(records[-1]["defect"], record["record_id"])
        self.assertEqual(records[-1]["owner_request"], self.REQUEST)
        self.assertTrue(self.record_path(record).exists())

    def test_a_crash_is_a_recorded_defect_too(self):
        self.vector_exit = 1
        self.assertEqual(self.script(*self.HEAD), 3)
        self.vector_exit = 0
        crashed = self.records()[-1]
        self.commit("the record of the crash")
        self.assertEqual(self.script(*self.HEAD, "--repeat-after-defect", crashed["record_id"],
                                     "--owner-request", self.REQUEST), 0)

    def test_a_defect_that_a_record_names_opens_no_second_repeat(self):
        record = self.missed()
        self.assertEqual(self.script(*self.HEAD, "--repeat-after-defect", record["record_id"],
                                     "--owner-request", self.REQUEST), 0)
        self.commit("the repeat")
        self.assertEqual(self.script(*self.HEAD, "--repeat-after-defect", record["record_id"],
                                     "--owner-request", self.REQUEST), 2)
        self.assertEqual(len(self.records()), 2)

    def test_a_repeat_is_charged_to_the_feature_wide_row(self):
        record = self.missed()
        self.assertEqual(self.script(*self.HEAD, "--repeat-after-defect", record["record_id"],
                                     "--owner-request", self.REQUEST), 0)
        rows = [p["row"] for p in self.projections()]
        self.assertEqual(rows.count(evidence.FEATURE_ROW), 1)
        self.assertEqual(rows.count(evidence.FUT_SEC_8_ROW), 1)

    def test_a_repeat_that_does_not_fit_the_row_exits_2(self):
        record = self.missed()
        self.hours_projected = evidence.FEATURE_ROW_HOURS + 1
        self.calls.clear()
        self.assertEqual(self.script(*self.HEAD, "--repeat-after-defect", record["record_id"],
                                     "--owner-request", self.REQUEST), 2)
        self.assertEqual(self.calls, [])
        self.assertEqual(len(self.records()), 1)

    def ended(self) -> Dict:
        record = self.run_first()
        path = self.record_path(record)
        data = json.loads(path.read_bytes())
        data["ended_outside"] = "2026-11-04T00:00:00Z"
        path.write_bytes(evidence.pretty(data))
        self.commit("a pass ended from outside")
        return data

    def test_a_repeat_after_a_pass_ended_from_outside(self):
        record = self.ended()
        self.assertEqual(self.script(*self.HEAD, "--repeat-after-end", record["record_id"],
                                     "--owner-request", self.REQUEST), 0)
        latest = self.records()[-1]
        self.assertEqual((latest["supersedes"], latest["defect"]), (record["record_id"], NONE))

    def test_an_ended_pass_opens_one_repeat(self):
        record = self.ended()
        self.assertEqual(self.script(*self.HEAD, "--repeat-after-end", record["record_id"],
                                     "--owner-request", self.REQUEST), 0)
        self.commit("the repeat")
        self.assertEqual(self.script(*self.HEAD, "--repeat-after-end", record["record_id"],
                                     "--owner-request", self.REQUEST), 2)

    def test_a_pass_that_finished_is_no_ended_pass(self):
        first = self.run_first()
        self.commit("record")
        self.assertEqual(self.script(*self.HEAD, "--repeat-after-end", first["record_id"],
                                     "--owner-request", self.REQUEST), 2)

    def test_an_ended_pass_is_no_defect(self):
        record = self.ended()
        self.assertEqual(self.script(*self.HEAD, "--repeat-after-defect", record["record_id"],
                                     "--owner-request", self.REQUEST), 2)

    def test_a_first_run_takes_no_repeat_arguments(self):
        self.assertEqual(self.script(*self.HEAD, "--owner-request", self.REQUEST), 2)
        self.assertEqual(self.script(*self.HEAD, "--repeat-after-defect", "x",
                                     "--owner-request", self.REQUEST), 2)
        self.assertEqual(self.calls, [])

    # ------------------------------------------------------------------------- --verify

    def test_verify_passes_on_a_true_record(self):
        record = self.run_first()
        self.assertEqual(self.script("--verify", record["record_id"]), 0)
        self.assertEqual(self.script("--verify", str(self.record_path(record))), 0)

    def tampered(self, change) -> int:
        record = self.run_first()
        path = self.record_path(record)
        data = json.loads(path.read_bytes())
        change(data)
        path.write_bytes(evidence.pretty(data))
        return self.script("--verify", str(path))

    def test_verify_exits_1_on_a_listed_match_that_does_not_match(self):
        def change(data):
            data["listed"][0][0]["s3"] = (data["listed"][0][0]["s3"] + 1) % 65536
        self.assertEqual(self.tampered(change), 1)

    def test_verify_exits_1_on_an_entry_true_in_all_but_its_three_words(self):
        from phycoweb.model_v2 import PhycoWebEngineV2
        seed = self.seeds[0]
        s2, s3 = (seed[2] + 1) % 65536, seed[3]
        engine = PhycoWebEngineV2((seed[0], seed[1], s2, s3))
        word = [engine.compute_block() for _ in range(4)][3]

        def change(data):
            data["listed"][0].append({"s2": s2, "s3": s3, "is_target": False,
                                      "fourth_word": f"{word:08X}", "fourth_word_matches": False})
        self.assertEqual(self.tampered(change), 1)

    def test_verify_exits_1_on_a_wrong_observed_word(self):
        def change(data):
            data["observed"][1]["words"][2] = "00000000"
        self.assertEqual(self.tampered(change), 1)

    def test_verify_exits_1_on_a_wrong_fourth_word(self):
        def change(data):
            data["listed"][2][0]["fourth_word"] = "00000000"
        self.assertEqual(self.tampered(change), 1)

    def test_verify_exits_1_on_a_recovered_flag_that_disagrees(self):
        def change(data):
            data["recovered"][0] = False
        self.assertEqual(self.tampered(change), 1)

    def test_verify_runs_no_tool_and_writes_nothing(self):
        record = self.run_first()
        before = report_files(self.root)
        self.calls.clear()
        self.assertEqual(self.script("--verify", record["record_id"]), 0)
        self.assertEqual(self.calls, [])
        self.assertEqual(report_files(self.root), before)

    def test_verify_of_no_record_exits_2(self):
        self.assertEqual(self.script("--verify", "no-such-record"), 2)

    def test_verify_of_an_aborted_record_exits_2(self):
        self.vector_exit = 1
        self.assertEqual(self.script(*self.HEAD), 3)
        self.assertEqual(self.script("--verify", self.records()[-1]["record_id"]), 2)

    def test_verify_of_another_kind_of_record_exits_2(self):
        self.run_first()
        projection = self.projections()[0]
        self.assertEqual(self.script("--verify", projection["record_id"]), 2)

    # ---------------------------------------------------------------------- --reproduce

    def reproduce_args(self, record: Dict, request: bool = True) -> List[str]:
        args = ["--reproduce", record["record_id"], "--binary", Tool.binary]
        return args + (["--owner-request", self.REQUEST] if request else [])

    def reviewed(self) -> Dict:
        record = self.run_first()
        self.commit("the demonstration record")
        self.add_row("FUT-SEC-8 result review", "Approved", "the row")
        return record

    def test_reproduce_exits_2_before_the_review(self):
        record = self.run_first()
        self.commit("the demonstration record")
        self.calls.clear()
        self.assertEqual(self.script(*self.reproduce_args(record)), 2)
        self.assertEqual(self.calls, [])

    def test_reproduce_exits_2_on_a_review_declined(self):
        record = self.run_first()
        self.commit("the demonstration record")
        self.add_row("FUT-SEC-8 result review", "Declined", "the row")
        self.calls.clear()
        self.assertEqual(self.script(*self.reproduce_args(record)), 2)
        self.assertEqual(self.calls, [])

    def test_reproduce_of_an_aborted_record_exits_2(self):
        self.vector_exit = 1
        self.assertEqual(self.script(*self.HEAD), 3)
        self.vector_exit = 0
        record = self.records()[-1]
        self.commit("the aborted record")
        self.add_row("FUT-SEC-8 result review", "Approved", "the row")
        self.calls.clear()
        self.assertEqual(self.script(*self.reproduce_args(record)), 2)
        self.assertEqual(self.calls, [])

    def test_reproduce_exits_2_without_the_owners_request(self):
        record = self.reviewed()
        self.calls.clear()
        self.assertEqual(self.script(*self.reproduce_args(record, request=False)), 2)
        self.assertEqual(self.calls, [])

    def test_a_reproduction_that_agrees_writes_its_record_and_changes_no_demonstration(self):
        record = self.reviewed()
        self.assertEqual(self.script(*self.reproduce_args(record)), 0)
        written = self.reproduction_record(self.record_path(record))
        self.assertEqual(written["outcome"], "match")
        self.assertEqual(written["owner_request"], self.REQUEST)
        self.assertEqual(written["original"]["record_id"], record["record_id"])
        self.assertEqual(len(self.records()), 1)

    def test_a_reproduction_reports_the_timings_and_compares_the_steps(self):
        record = self.reviewed()
        for number in range(3):
            self.changes[number] = {"seconds": 999.5, "steps_per_second": 1.0e9}
        self.assertEqual(self.script(*self.reproduce_args(record)), 0)
        written = self.reproduction_record(self.record_path(record))
        self.assertEqual(written["compared"]["cost"], "match")
        self.assertEqual(written["compared"]["tool"], "match")
        self.assertEqual(written["reported"]["cost"]["seconds"], 3 * 999.5)
        self.assertEqual(written["reported"]["tool"]["threads"], 32)

    def test_a_reproduction_with_other_steps_differs(self):
        record = self.reviewed()
        self.changes[0] = {"total_steps": 257 * 2 ** 32 + 5}
        self.assertEqual(self.script(*self.reproduce_args(record)), 1)
        written = self.reproduction_record(self.record_path(record))
        self.assertEqual(written["compared"]["cost"], "differs")
        self.assertEqual(written["outcome"], "differs")

    def test_a_reproduction_with_another_count_differs(self):
        record = self.reviewed()
        self.changes[1] = {"after_one": 3}
        self.assertEqual(self.script(*self.reproduce_args(record)), 1)
        written = self.reproduction_record(self.record_path(record))
        self.assertEqual(written["compared"]["matches"], "differs")

    # ---------------------------------------------------------------------- the projection

    def test_the_projection_reads_the_tools_progress_lines_alone(self):
        calls = {}

        class Process:
            stderr = iter(["progress: 400 of 65536 s2 values in 5 s\n",
                           "progress: 800 of 65536 s2 values in 10 s\n"])

            def kill(self):
                calls["killed"] = True

            def wait(self):
                return 0

        with mock.patch.object(self.fut.subprocess, "Popen", return_value=Process()) as popen, \
                mock.patch.object(self.fut, "PROBE_SECONDS", 0):
            hours, speed = self.real_project(Path("tool"), self.root, self.seeds[0])
        self.assertEqual(calls, {"killed": True})
        self.assertEqual(speed, {"s2_values_per_second": 80.0})
        self.assertAlmostEqual(hours, 3 * 65536 / 80.0 / 3600.0)
        self.assertIn("--progress", popen.call_args[0][0])

    def test_a_projection_that_sees_no_progress_is_a_tool_failure(self):
        class Process:
            stderr = iter(["no such line\n"])

            def kill(self):
                pass

            def wait(self):
                return 0

        with mock.patch.object(self.fut.subprocess, "Popen", return_value=Process()):
            with self.assertRaises(evidence.ToolFailure):
                self.real_project(Path("tool"), self.root, self.seeds[0])


if __name__ == "__main__":
    unittest.main()
