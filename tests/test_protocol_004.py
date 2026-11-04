"""Feature 004: the evidence writer, the guards every script shares and the common part of
--reproduce (T008; FR-038, FR-039, FR-040, FR-044, FR-045, FR-053, FR-061; research R7, R12, R16).
Each guard refuses with exit 2 and writes nothing. No test here makes a heavy run."""
import gzip
import json
import os
import re
import unittest
from pathlib import Path
from typing import Dict, List
from unittest import mock

from protocol import evidence
from protocol.disclaimer import DESIGN_DISCLAIMER
from protocol.evidence import NONE, Refused
from tests.support_004 import SNAPSHOT, TempRepo, Tool, report_files, write

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


if __name__ == "__main__":
    unittest.main()
