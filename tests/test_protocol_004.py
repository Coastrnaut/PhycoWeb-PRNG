"""Feature 004: the evidence writer, the guards every script shares and the common part of
--reproduce (T008; FR-038, FR-039, FR-040, FR-044, FR-045, FR-053, FR-061; research R7, R12, R16).
Each guard refuses with exit 2 and writes nothing. No test here makes a heavy run."""
import ast
import datetime
import gzip
import json
import os
import re
import subprocess
import unittest
from pathlib import Path
from typing import Dict, List
from unittest import mock

from protocol import changelog, evidence, provenance
from protocol.disclaimer import DESIGN_DISCLAIMER
from protocol.evidence import NONE, Refused
from tests.support_004 import CODE_ROOT, SNAPSHOT, TempRepo, Tool, report_files, write

ROOT = Path(__file__).resolve().parents[1]
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
    built with the refused list that T027 writes standing in; nothing is written."""

    def test_they_agree_with_the_lists_and_the_confirmed_rows(self):
        stored = json.loads((ROOT / changelog.PLACE_CHECK_REL).read_bytes())
        self.assertEqual(changelog.check(stored["compared_to"]), stored)
        fake = {"path": changelog.REFUSED_REL, "sha256": "0" * 64, "sha256_kind": "raw"}
        with mock.patch.object(changelog, "check_refused_list_at_head", return_value=fake):
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
