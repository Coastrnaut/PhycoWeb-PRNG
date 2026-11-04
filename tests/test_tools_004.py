"""Feature 004: a tool's results count only after it re-finds a known result (FR-039; SC-007; T049).

scripts/validate_tool.py runs here on a fake tool in a temporary repository, so that each test breaks one
thing. The last classes read the repository itself: every self-written known result stands in the
provenance log before its tool's first entry, with the hash it still has. This file makes no security
claim.
"""
import contextlib
import io
import json
import math
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional
from unittest import mock

from protocol import evidence
from protocol.evidence import NONE
from tests.support_004 import CODE_ROOT, TempRepo, Tool, write

VALIDATION = evidence.REP_REL + "/validation"
PROVENANCE = evidence.PROVENANCE_LOG_REL
TOOL_REL = "research/004/tools/fake.py"
TOOL_TEXT = '''"""A fake tool: it finds what `found.json` holds, beside this file."""
import json
from pathlib import Path

ANSWER = json.loads((Path(__file__).parent / "found.json").read_text(encoding="utf-8"))


def validation(known_id, known, keep):
    value = ANSWER.get(known_id, ANSWER["default"])
    if value == "crash":
        raise ValueError("the tool broke")
    return {"found": {"value": value}, "re_found": known is None or value == known.EXPECTED,
            "validated_kind": {"widths": [8], "operations": "stated", "model": "fake", "uses": []}}
'''
FIRST = "research/004/validation/fake-known.py"
SECOND = "research/004/validation/fake-known-second.py"
THIRD = "research/004/validation/fake-other.py"


def known_text(known_id, second_of="none", expected=7, tool="fake"):
    return (f'TOOL = "{tool}"\nKNOWN_ID = "{known_id}"\nSECOND_OF = "{second_of}"\n'
            f'SOURCE = "self-written"\nEXPECTED = {expected}\n')


class ValidationBase(TempRepo):
    """A repository with one fake tool, one known result and its second, in provenance order."""

    def setUp(self):
        super().setUp()
        sys.path.insert(0, str(CODE_ROOT))
        self.addCleanup(sys.path.remove, str(CODE_ROOT))
        from scripts import validate_tool
        self.vt = validate_tool
        patcher = mock.patch.dict(validate_tool.TOOLS, {"fake": validate_tool.Tool("fake", TOOL_REL)})
        patcher.start()
        self.addCleanup(patcher.stop)
        for rel in ("scripts/validate_tool.py", "protocol/devinputs_v3.py"):
            write(self.root, rel, (CODE_ROOT / rel).read_bytes())
        write(self.root, FIRST, known_text("fake-known"))
        write(self.root, SECOND, known_text("fake-known-second", "fake-known"))
        write(self.root, TOOL_REL, TOOL_TEXT)
        write(self.root, "research/004/tools/found.json", json.dumps({"default": 7}))
        self.entries: List[Dict] = []
        self.log_all(FIRST, SECOND, TOOL_REL)
        self.commit("the fake tool")

    def log_all(self, *paths: str) -> None:
        for rel in paths:
            digest, kind = evidence.named_hash(rel)
            self.entries.append({"path": rel, "section": NONE, "sha256": digest, "sha256_kind": kind,
                                 "tool": "Claude Code", "model": "m", "session": "s", "task_id": "T"})
        self.write_provenance()

    def write_provenance(self) -> None:
        lines, previous = b"", evidence.ZERO_HASH
        for seq, entry in enumerate(self.entries):
            raw = json.dumps(dict(entry, seq=seq, prev_sha256=previous), sort_keys=True).encode("utf-8") + b"\n"
            lines += raw
            previous = evidence.sha256(raw)
        write(self.root, PROVENANCE, lines)

    def main(self, *args: str, known: str = "fake-known", tool: str = "fake") -> int:
        return self.vt.main(["--tool", tool, "--known", known, "--out-dir", VALIDATION, *args])

    def refused(self, words: str, **kwargs) -> None:
        """Exit 2, for the stated reason and no other guard's."""
        said = io.StringIO()
        with contextlib.redirect_stderr(said):
            self.assertEqual(self.main(**kwargs), evidence.EXIT_REFUSED)
        self.assertIn(words, said.getvalue())

    def records(self) -> List[Dict]:
        """Oldest first; within one second, a re-validation after what it follows."""
        return sorted((r for _, r in evidence.iter_records("validation", "validation")),
                      key=lambda r: (r["created_utc"], "re_validation" in r))

    def finds(self, value, **others) -> None:
        write(self.root, "research/004/tools/found.json", json.dumps(dict(others, default=value)))
        self.commit("the tool changes what it finds")

    def fail_once(self) -> Dict:
        """One `not re-found`, and the tool fixed, by a new comment, so that its hash differs."""
        self.finds(9)
        self.assertEqual(self.main(), evidence.EXIT_VERDICT)
        failed = self.records()[-1]
        self.finds(7)
        write(self.root, TOOL_REL, TOOL_TEXT + "# fixed\n")
        self.entries.append(self.entry_of(TOOL_REL))
        self.write_provenance()
        self.commit("the fix")
        return failed

    def entry_of(self, rel: str) -> Dict:
        digest, kind = evidence.named_hash(rel)
        return {"path": rel, "section": NONE, "sha256": digest, "sha256_kind": kind, "tool": "Claude Code",
                "model": "m", "session": "s", "task_id": "T"}

    def note(self, failed: Dict, **fields) -> None:
        body = {"failed_record": failed["record_id"], "defect": "it read the wrong word",
                "cause": "an index off by one", "fix": "the index"}
        body.update(fields)
        write(self.root, f"{self.vt.DEFECTS_REL}/{failed['record_id']}.json", json.dumps(body))
        self.commit("the defect note")


class Fields(ValidationBase):

    def test_the_record_holds_every_field_of_section_7(self):
        self.assertEqual(self.main(), evidence.EXIT_OK)
        record = self.records()[0]
        for field in ("tool", "version", "tool_sha256", "licence", "source", "validated_kind",
                      "known_result", "second_known_result", "found", "outcome"):
            self.assertIn(field, record)
        self.assertEqual(record["kind"], "validation")
        self.assertEqual(record["tool"], "fake")
        self.assertEqual(record["outcome"], "re-found")
        self.assertEqual(record["status"], "pass")
        self.assertEqual(record["classification"], NONE)
        self.assertEqual(record["found"], {"fake-known": {"value": 7}})
        self.assertEqual(record["validated_kind"]["fake-known"]["widths"], [8])

    def test_a_self_written_tools_version_is_its_hash(self):
        self.main()
        record = self.records()[0]
        digest = evidence.sha256((self.root / TOOL_REL).read_bytes())
        self.assertEqual(record["tool_sha256"], digest)
        self.assertEqual(record["version"], digest)

    def test_the_record_cites_both_provenance_entries(self):
        self.main()
        record = self.records()[0]
        first, second = record["known_result"], record["second_known_result"]
        self.assertEqual((first["known_id"], first["provenance_seq"]), ("fake-known", 0))
        self.assertEqual(first["sha256"], evidence.sha256((self.root / FIRST).read_bytes()))
        self.assertEqual((second["known_id"], second["provenance_seq"]), ("fake-known-second", 1))
        self.assertEqual(second["sha256"], evidence.sha256((self.root / SECOND).read_bytes()))

    def test_the_tool_and_both_known_results_stand_in_code_sha256(self):
        self.main()
        code = self.records()[0]["code_sha256"]
        for rel in (TOOL_REL, FIRST, SECOND, "scripts/validate_tool.py"):
            self.assertIn(rel, code)

    def test_a_first_with_no_second_says_none(self):
        write(self.root, THIRD, known_text("fake-other"))
        self.entries.insert(0, self.entry_of(THIRD))
        self.write_provenance()
        self.commit("a known result with no second")
        self.assertEqual(self.main(known="fake-other"), evidence.EXIT_OK)
        self.assertEqual(self.records()[-1]["second_known_result"], NONE)

    def test_what_is_not_found_is_exit_1_and_a_failed_record(self):
        self.finds(9)
        self.assertEqual(self.main(), evidence.EXIT_VERDICT)
        record = self.records()[0]
        self.assertEqual((record["outcome"], record["status"]), ("not re-found", "fail"))
        self.assertEqual(record["found"], {"fake-known": {"value": 9}})
        self.assertEqual(record["classification"], NONE)

    def test_a_tool_that_breaks_is_exit_3_and_an_aborted_record(self):
        self.finds("crash")
        self.assertEqual(self.main(), evidence.EXIT_TOOL)
        record = self.records()[0]
        self.assertEqual(record["status"], "inconclusive")
        self.assertNotIn("outcome", record)

    def test_refusals_write_nothing(self):
        cases = (("--tool", "nothing", "--known", "fake-known", "--out-dir", VALIDATION),
                 ("--tool", "fake", "--known", "nothing", "--out-dir", VALIDATION),
                 ("--tool", "fake", "--known", "fake-known", "--out-dir", "elsewhere"))
        for argv in cases:
            self.assertEqual(self.vt.main(list(argv)), evidence.EXIT_REFUSED, argv)
        self.assertEqual(self.records(), [])

    def test_a_known_result_of_another_tool_is_refused(self):
        write(self.root, THIRD, known_text("fake-other", tool="another"))
        self.entries.insert(0, self.entry_of(THIRD))
        self.write_provenance()
        self.commit("another tool's")
        self.refused("a known result of another", known="fake-other")

    def test_uncommitted_tool_code_is_refused(self):
        write(self.root, TOOL_REL, TOOL_TEXT + "# changed\n")
        self.assertEqual(self.main(), evidence.EXIT_REFUSED)
        self.assertEqual(self.records(), [])


class Order(ValidationBase):
    """A known result is logged before its tool is drafted, and its hash still matches."""

    def test_a_known_result_with_no_entry_is_refused(self):
        self.entries = [e for e in self.entries if e["path"] != FIRST]
        self.write_provenance()
        self.commit("the entry gone")
        self.assertEqual(self.main(), evidence.EXIT_REFUSED)

    def test_a_second_with_no_entry_is_refused(self):
        self.entries = [e for e in self.entries if e["path"] != SECOND]
        self.write_provenance()
        self.commit("the entry gone")
        self.assertEqual(self.main(), evidence.EXIT_REFUSED)

    def test_a_known_result_logged_after_the_tool_is_refused(self):
        self.entries = [self.entries[1], self.entries[2], self.entries[0]]
        self.write_provenance()
        self.commit("out of order")
        self.assertEqual(self.main(), evidence.EXIT_REFUSED)

    def test_a_second_logged_after_the_tool_is_refused(self):
        self.entries = [self.entries[0], self.entries[2], self.entries[1]]
        self.write_provenance()
        self.commit("out of order")
        self.assertEqual(self.main(), evidence.EXIT_REFUSED)

    def test_a_known_result_changed_since_its_entry_is_refused(self):
        write(self.root, FIRST, known_text("fake-known") + "# edited\n")
        self.commit("edited")
        self.assertEqual(self.main(), evidence.EXIT_REFUSED)

    def test_a_second_changed_since_its_entry_is_refused(self):
        write(self.root, SECOND, known_text("fake-known-second", "fake-known") + "# edited\n")
        self.commit("edited")
        self.assertEqual(self.main(), evidence.EXIT_REFUSED)

    def test_the_order_is_read_from_the_tools_first_entry_not_its_latest(self):
        tool = self.entries[2]
        self.entries = [self.entries[1], tool, self.entries[0], dict(tool)]
        self.write_provenance()
        self.commit("a known result between two entries of the tool")
        self.refused("logged after its tool's first entry")

    def test_a_tool_with_no_entry_is_refused(self):
        self.entries = [e for e in self.entries if e["path"] != TOOL_REL]
        self.write_provenance()
        self.commit("the tool's entry gone")
        self.assertEqual(self.main(), evidence.EXIT_REFUSED)

    def test_a_broken_chain_is_refused(self):
        lines = (self.root / PROVENANCE).read_bytes().split(b"\n")
        write(self.root, PROVENANCE, b"\n".join([lines[1], lines[0], lines[2], b""]))
        self.commit("broken")
        self.assertEqual(self.main(), evidence.EXIT_REFUSED)


class Counted(ValidationBase):
    """data-model section 5, Validation cited, and cli contract, Tool validation."""

    def validated(self) -> str:
        self.assertEqual(self.main(), evidence.EXIT_OK)
        return evidence.sha256((self.root / TOOL_REL).read_bytes())

    def test_a_citation_holds_the_id_and_hash_of_the_exact_version(self):
        digest = self.validated()
        citation = evidence.validation_citation("fake", digest)
        record = self.records()[0]
        path = self.root / VALIDATION / f"{record['record_id']}.json"
        self.assertEqual(citation["record_id"], record["record_id"])
        self.assertEqual(citation["sha256"], evidence.sha256(path.read_bytes()))

    def test_another_hash_has_no_citation(self):
        self.validated()
        self.assertIsNone(evidence.validation_citation("fake", "0" * 64))

    def test_a_c_tools_exact_hash_is_a_pair(self):
        record = {"kind": "validation", "tool": "c", "tool_sha256": "a" * 64, "outcome": "re-found",
                  "validated_kind": {}, "created_utc": "2026-11-04T00:00:00Z", "record_id": "validation-x",
                  "code_sha256": {"b": {"sha256": "c" * 64}}}
        write(self.root, f"{VALIDATION}/validation-x.json", evidence.pretty(record))
        self.assertIsNotNone(evidence.validation_citation("c", "a" * 64, "c" * 64))
        self.assertIsNone(evidence.validation_citation("c", "a" * 64, "d" * 64))
        self.assertIsNone(evidence.validation_citation("c", "e" * 64, "c" * 64))

    def test_a_cited_validation_must_be_earlier_than_its_result(self):
        digest = self.validated()
        citation = evidence.validation_citation("fake", digest)
        created = self.records()[0]["created_utc"]
        later = {"validation": citation, "created_utc": "2099-01-01T00:00:00Z"}
        self.assertTrue(evidence.validation_cited_before(later))
        self.assertFalse(evidence.validation_cited_before(dict(later, created_utc=created)))
        self.assertFalse(evidence.validation_cited_before(dict(later, created_utc="2001-01-01T00:00:00Z")))

    def test_a_citation_whose_record_changed_does_not_hold(self):
        digest = self.validated()
        citation = evidence.validation_citation("fake", digest)
        later = {"validation": citation, "created_utc": "2099-01-01T00:00:00Z"}
        path = self.root / VALIDATION / f"{citation['record_id']}.json"
        path.write_bytes(path.read_bytes() + b"\n")
        self.assertFalse(evidence.validation_cited_before(later))

    def test_no_citation_at_all_does_not_hold(self):
        self.assertFalse(evidence.validation_cited_before({"created_utc": "2099-01-01T00:00:00Z"}))
        self.assertFalse(evidence.validation_cited_before({"validation": NONE, "created_utc": "2099"}))

    def test_a_result_without_one_is_not_evaluated(self):
        self.assertEqual(evidence.result_status("pass", False), "not evaluated")
        self.assertEqual(evidence.result_status("pass", True), "pass")

    def test_a_later_failure_at_the_same_hash_closes_the_validation(self):
        digest = self.validated()
        record = {"kind": "validation", "tool": "fake", "tool_sha256": digest, "outcome": "not re-found",
                  "validated_kind": {}, "created_utc": "2099-01-01T00:00:00Z", "record_id": "validation-y",
                  "code_sha256": {}}
        write(self.root, f"{VALIDATION}/validation-y.json", evidence.pretty(record))
        self.assertIsNone(evidence.validation_record("fake", digest))

    def test_a_failure_of_another_version_leaves_this_one(self):
        digest = self.validated()
        record = {"kind": "validation", "tool": "fake", "tool_sha256": "0" * 64, "outcome": "not re-found",
                  "validated_kind": {}, "created_utc": "2099-01-01T00:00:00Z", "record_id": "validation-y",
                  "code_sha256": {}}
        write(self.root, f"{VALIDATION}/validation-y.json", evidence.pretty(record))
        self.assertIsNotNone(evidence.validation_record("fake", digest))

    def test_an_aborted_record_closes_nothing(self):
        digest = self.validated()
        record = {"kind": "validation", "tool": "fake", "tool_sha256": digest, "status": "inconclusive",
                  "created_utc": "2099-01-01T00:00:00Z", "record_id": "validation-y", "code_sha256": {}}
        write(self.root, f"{VALIDATION}/validation-y.json", evidence.pretty(record))
        self.assertIsNotNone(evidence.validation_record("fake", digest))


class Source(ValidationBase):
    """cli contract: a published value needs a recorded source, or the run exits 2."""

    PAPER = "research/004/validation/fake-paper.py"

    def setUp(self):
        super().setUp()
        patcher = mock.patch.dict(self.vt.PUBLISHED, {"fake-paper": "fake"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.manifest([])

    def manifest(self, entries: List[Dict]) -> None:
        write(self.root, evidence.DOWNLOADS_REL, evidence.pretty({"entries": entries}))
        self.commit("the manifest")

    def paper_file(self) -> None:
        write(self.root, self.PAPER, 'TOOL = "fake"\nKNOWN_ID = "fake-paper"\nSECOND_OF = "none"\n'
                                     'DOWNLOAD = "paper.pdf"\nPAPER = "A paper"\nTABLE = "Table 1"\n'
                                     'VALUE = 7\nEXPECTED = 7\n')
        self.entries.insert(0, self.entry_of(self.PAPER))
        self.write_provenance()
        self.commit("the value read from the paper")

    def fetched(self, status="fetched"):
        return {"name": "paper.pdf", "status": status, "sha256": "a" * 64, "source": "https://example.invalid"}

    def provided(self):
        return {"name": "owner-provided: fake-paper", "status": "owner-provided", "known": "fake-paper",
                "source": "A paper, Table 1", "value": "7", "words": "yes"}

    def test_no_source_at_all_is_refused(self):
        self.assertEqual(self.main(known="fake-paper"), evidence.EXIT_REFUSED)

    def test_an_entry_only_approved_is_no_source(self):
        self.paper_file()
        self.manifest([self.fetched("approved")])
        self.assertEqual(self.main(known="fake-paper"), evidence.EXIT_REFUSED)

    def test_a_file_never_obtained_is_no_source(self):
        self.paper_file()
        self.manifest([self.fetched("not-obtained")])
        self.assertEqual(self.main(known="fake-paper"), evidence.EXIT_REFUSED)

    def test_a_fetched_file_is_cited_with_its_table_and_value(self):
        self.paper_file()
        self.manifest([self.fetched()])
        self.assertEqual(self.main(known="fake-paper"), evidence.EXIT_OK)
        source = self.records()[0]["source"]
        self.assertEqual((source["entry"], source["sha256"]), ("paper.pdf", "a" * 64))
        self.assertEqual((source["paper"], source["table"], source["value"]), ("A paper", "Table 1", 7))

    def test_an_owner_provided_value_without_its_row_is_refused(self):
        self.manifest([self.provided()])
        self.assertEqual(self.main(known="fake-paper"), evidence.EXIT_REFUSED)

    def test_an_owner_provided_value_with_a_pending_row_is_refused(self):
        self.manifest([self.provided()])
        self.add_row("Owner-provided value 1", "_pending_", evidence.approval_hash(self.provided()))
        self.assertEqual(self.main(known="fake-paper"), evidence.EXIT_REFUSED)

    def test_a_row_approved_only_in_the_working_tree_is_refused(self):
        self.manifest([self.provided()])
        self.add_row("Owner-provided value 1", "Approved", evidence.approval_hash(self.provided()),
                     commit=False)
        self.assertEqual(self.main(known="fake-paper"), evidence.EXIT_REFUSED)

    def test_a_row_that_names_another_entry_is_refused(self):
        self.manifest([self.provided()])
        self.add_row("Owner-provided value 1", "Approved", "0" * 64)
        self.assertEqual(self.main(known="fake-paper"), evidence.EXIT_REFUSED)

    def test_a_row_of_another_family_is_refused(self):
        self.manifest([self.provided()])
        self.add_row("Download 9", "Approved", evidence.approval_hash(self.provided()))
        self.refused("reads Approved at HEAD", known="fake-paper")

    def test_an_owner_provided_value_with_its_row_approved_at_head_is_cited(self):
        self.manifest([self.provided()])
        self.add_row("Owner-provided value 1", "Approved", evidence.approval_hash(self.provided()))
        self.assertEqual(self.main(known="fake-paper"), evidence.EXIT_OK)
        source = self.records()[0]["source"]
        self.assertEqual(source["entry"], "owner-provided: fake-paper")
        self.assertEqual(source["value"], "7")
        self.assertEqual(self.records()[0]["known_result"]["value"], "7")

    def test_a_self_written_known_result_needs_no_download(self):
        self.assertEqual(self.main(), evidence.EXIT_OK)
        self.assertEqual(self.records()[0]["source"], {"repository": FIRST})


class Revalidation(ValidationBase):
    """data-model section 7: no use counts again on a fix tuned to one value."""

    def test_after_a_failure_a_plain_run_is_refused(self):
        self.fail_once()
        self.refused("must hold the defect, its cause and the fix")

    def test_of_two_unanswered_failures_the_later_is_open(self):
        old = {"record_id": "old", "tool": "fake", "outcome": "not re-found",
               "created_utc": "2026-11-04T00:00:00Z"}
        new = dict(old, record_id="new", created_utc="2026-11-04T00:00:09Z")
        with mock.patch.object(evidence, "iter_records", return_value=[(None, old), (None, new)]):
            self.assertEqual(self.vt.open_failure(self.vt.TOOLS["fake"])["record_id"], "new")
        with mock.patch.object(evidence, "iter_records", return_value=[(None, new), (None, old)]):
            self.assertEqual(self.vt.open_failure(self.vt.TOOLS["fake"])["record_id"], "new")

    def test_a_note_must_hold_the_defect_its_cause_and_the_fix(self):
        failed = self.fail_once()
        for field in ("defect", "cause", "fix"):
            self.note(failed, **{field: ""})
            self.assertEqual(self.main(), evidence.EXIT_REFUSED, field)

    def test_a_note_for_another_record_is_refused(self):
        failed = self.fail_once()
        self.note(failed, failed_record="validation-other")
        self.assertEqual(self.main(), evidence.EXIT_REFUSED)

    def test_the_re_validation_re_finds_every_known_result_in_one_record(self):
        failed = self.fail_once()
        self.note(failed)
        self.assertEqual(self.main(), evidence.EXIT_OK)
        record = self.records()[-1]
        self.assertEqual(sorted(record["found"]), ["fake-known", "fake-known-second"])
        again = record["re_validation"]
        self.assertEqual(again["failed_record"], failed["record_id"])
        self.assertEqual((again["defect"], again["cause"], again["fix"]),
                         ("it read the wrong word", "an index off by one", "the index"))
        self.assertEqual(sorted(again["known_results"]), ["fake-known", "fake-known-second"])
        self.assertIn("note_sha256", again)
        self.assertIn(f"{self.vt.DEFECTS_REL}/{failed['record_id']}.json", record["code_sha256"])

    def test_a_fix_tuned_to_the_first_value_fails_on_the_second(self):
        failed = self.fail_once()
        self.note(failed)
        self.finds(7, **{"fake-known-second": 8})
        self.assertEqual(self.main(), evidence.EXIT_VERDICT)
        record = self.records()[-1]
        self.assertEqual(record["outcome"], "not re-found")
        self.assertEqual(self.main(), evidence.EXIT_REFUSED)

    def test_attempts_chain_by_what_they_answer_not_by_their_times(self):
        failed = self.fail_once()
        self.note(failed)
        self.finds(7, **{"fake-known-second": 8})
        self.assertEqual(self.main(), evidence.EXIT_VERDICT)
        second = [r for r in self.records() if "re_validation" in r][-1]
        self.assertEqual(second["re_validation"]["failed_record"], failed["record_id"])
        with mock.patch.object(evidence, "iter_records",
                               return_value=[(None, dict(r, created_utc="2026-11-04T00:00:00Z"))
                                             for r in self.records()]):
            self.assertEqual(self.vt.open_failure(self.vt.TOOLS["fake"])["record_id"],
                             second["record_id"])
        self.finds(7)
        self.note(second)
        self.assertEqual(self.main(), evidence.EXIT_OK)
        self.assertIsNone(self.vt.open_failure(self.vt.TOOLS["fake"]))

    def test_a_tool_with_no_second_at_one_result_stays_unvalidated(self):
        write(self.root, THIRD, known_text("fake-other"))
        self.entries.insert(0, self.entry_of(THIRD))
        self.write_provenance()
        self.commit("a known result with no second")
        failed = self.fail_once()
        self.note(failed)
        self.assertEqual(self.main(), evidence.EXIT_REFUSED)
        self.assertEqual(self.records()[-1]["record_id"], failed["record_id"])

    def test_once_closed_a_plain_run_goes_again(self):
        failed = self.fail_once()
        self.note(failed)
        self.assertEqual(self.main(), evidence.EXIT_OK)
        self.assertEqual(self.main(known="fake-known-second"), evidence.EXIT_OK)

    def test_the_new_version_counts_only_after_its_re_validation(self):
        failed = self.fail_once()
        digest = evidence.sha256((self.root / TOOL_REL).read_bytes())
        self.assertIsNone(evidence.validation_record("fake", digest))
        self.note(failed)
        self.main()
        self.assertIsNotNone(evidence.validation_record("fake", digest))

    def test_the_failed_versions_results_stay_uncounted(self):
        failed = self.fail_once()
        self.assertIsNone(evidence.validation_record("fake", failed["tool_sha256"]))


class Hooks(ValidationBase):
    """What a tool's module may give beside `validation`."""

    def tool_with(self, text: str) -> None:
        write(self.root, TOOL_REL, TOOL_TEXT + text)
        self.commit("the tool gives more")

    def test_a_tool_names_its_model(self):
        self.tool_with('MODEL_ID = "phyco-v2"\n')
        self.main()
        self.assertEqual(self.records()[0]["model_id"], "phyco-v2")

    def test_no_model_by_default(self):
        self.main()
        self.assertIsNone(self.records()[0]["model_id"])

    def test_a_tools_other_files_stand_in_code_sha256(self):
        self.tool_with('CODE = ("research/004/tools/found.json",)\n')
        self.main()
        self.assertIn("research/004/tools/found.json", self.records()[0]["code_sha256"])

    def test_a_tool_states_its_inputs(self):
        self.tool_with('def inputs(known_id):\n    return {"namespace": "dev", "known": known_id}\n')
        self.main()
        self.assertEqual(self.records()[0]["inputs"], {"namespace": "dev", "known": "fake-known"})

    def test_kept_outputs_are_local_only_under_the_records_id(self):
        self.tool_with('''
_real = validation


def validation(known_id, known, keep):
    keep("sets/a.json", b"{}")
    return _real(known_id, known, keep)
''')
        self.assertEqual(self.main(), evidence.EXIT_OK)
        record = self.records()[0]
        output = record["outputs"][0]
        self.assertFalse(output["committed"])
        self.assertEqual(output["path"], f"{evidence.LOCAL_REL}/{record['record_id']}/sets/a.json")
        self.assertEqual((self.root / output["path"]).read_bytes(), b"{}")


class Heavy(ValidationBase):
    """R7: a heavy validation projects first against the feature-wide row."""

    HOURS = 0.5
    TEXT = '''
HEAVY = ("fake-known",)


def projection(known_id):
    return HOURS, {"rate": 10.0}
'''

    def setUp(self):
        super().setUp()
        self.heavy_tool(self.HOURS)

    def heavy_tool(self, hours: float) -> None:
        write(self.root, TOOL_REL, TOOL_TEXT + f"HOURS = {hours}\n" + self.TEXT)
        self.commit("a heavy tool")

    def projections(self) -> List[Dict]:
        return [r for _, r in evidence.iter_records("projection")]

    def test_it_projects_first_and_records_its_hours(self):
        self.assertEqual(self.main(), evidence.EXIT_OK)
        record = self.records()[0]
        self.assertTrue(record["heavy_run"])
        self.assertEqual(record["hours"]["projected"], self.HOURS)
        projection = self.projections()[0]
        self.assertEqual(projection["row"], evidence.FEATURE_ROW)
        self.assertEqual(projection["projected_hours"], self.HOURS)

    def test_it_is_refused_once_the_row_cannot_hold_it(self):
        self.heavy_tool(evidence.FEATURE_ROW_HOURS + 1)
        self.assertEqual(self.main(), evidence.EXIT_REFUSED)
        self.assertEqual(self.records(), [])
        self.assertEqual(len(self.projections()), 1)

    def test_a_light_known_result_of_the_same_tool_stays_light(self):
        write(self.root, THIRD, known_text("fake-other"))
        self.entries.insert(0, self.entry_of(THIRD))
        self.write_provenance()
        self.commit("a light known result")
        self.assertEqual(self.main(known="fake-other"), evidence.EXIT_OK)
        self.assertFalse(self.records()[0]["heavy_run"])
        self.assertEqual(self.projections(), [])

    def test_a_heavy_reproduction_needs_the_owners_word(self):
        self.main()
        record = self.records()[0]
        path = f"{VALIDATION}/{record['record_id']}.json"
        self.assertEqual(self.vt.main(["--reproduce", path]), evidence.EXIT_REFUSED)

    def test_a_heavy_reproduction_projects_in_its_worktree(self):
        self.main()
        record = self.records()[0]
        self.commit("the record")
        path = f"{VALIDATION}/{record['record_id']}.json"
        self.assertEqual(self.vt.main(["--reproduce", path, "--owner-request", "yes (2026-11-04)"]),
                         evidence.EXIT_OK)
        self.assertEqual(len(self.projections()), 2)


class Reproduce(ValidationBase):

    def test_a_reproduction_matches(self):
        self.main()
        self.commit("the record")
        record = self.records()[0]
        path = f"{VALIDATION}/{record['record_id']}.json"
        self.assertEqual(self.vt.main(["--reproduce", path]), evidence.EXIT_OK)

    def test_a_reproduction_reads_the_commit_of_the_original(self):
        self.main()
        record = self.records()[0]
        self.finds(9)
        path = f"{VALIDATION}/{record['record_id']}.json"
        self.assertEqual(self.vt.main(["--reproduce", path]), evidence.EXIT_OK)

    def test_a_reproduction_that_differs_is_exit_1(self):
        self.main()
        record = self.records()[0]
        with mock.patch.object(self.vt, "measure_in", return_value={
                "fake-known": {"found": {"value": 9}, "re_found": False,
                               "validated_kind": record["validated_kind"]["fake-known"]}}):
            path = f"{VALIDATION}/{record['record_id']}.json"
            self.assertEqual(self.vt.main(["--reproduce", path]), evidence.EXIT_VERDICT)

    def test_a_reproduction_that_differs_only_in_what_it_found_is_exit_1(self):
        self.main()
        record = self.records()[0]
        with mock.patch.object(self.vt, "measure_in", return_value={
                "fake-known": {"found": {"value": 8}, "re_found": True,
                               "validated_kind": record["validated_kind"]["fake-known"]}}):
            path = f"{VALIDATION}/{record['record_id']}.json"
            self.assertEqual(self.vt.main(["--reproduce", path]), evidence.EXIT_VERDICT)

    def test_a_reproduction_of_nothing_is_refused(self):
        self.assertEqual(self.vt.main(["--reproduce", "nothing.json"]), evidence.EXIT_REFUSED)


class TheRepository(unittest.TestCase):
    """The known results as committed, read from the repository itself."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(CODE_ROOT))
        from scripts import validate_tool
        cls.vt = validate_tool
        cls.entries = [entry for entry, _ in evidence.log_entries(PROVENANCE)]

    def known(self):
        return [k for k in self.vt.known_results().values() if k.path]

    def test_every_self_written_known_result_has_an_entry_with_its_hash(self):
        for known in self.known():
            digest = evidence.sha256((CODE_ROOT / known.path).read_bytes())
            entries = [e for e in self.entries if e["path"] == known.path]
            self.assertTrue(entries, known.path)
            self.assertEqual(entries[-1]["sha256"], digest, known.path)

    def test_every_known_result_stands_before_its_tools_first_entry(self):
        for known in self.known():
            tool = self.vt.TOOLS[known.tool]
            first = [e["seq"] for e in self.entries if e["path"] == tool.source]
            if not first:
                continue
            ours = [e["seq"] for e in self.entries if e["path"] == known.path]
            self.assertLess(min(ours), min(first), known.path)

    def test_every_known_result_names_a_tool(self):
        for known in self.vt.known_results().values():
            self.assertIn(known.tool, self.vt.TOOLS, known.known_id)

    def test_every_second_names_a_known_result_of_its_tool(self):
        table = self.vt.known_results()
        for known in table.values():
            if known.second_of != NONE:
                self.assertIn(known.second_of, table, known.known_id)
                self.assertEqual(table[known.second_of].tool, known.tool, known.known_id)

    def test_every_structural_first_has_a_second(self):
        table = self.vt.known_results()
        seconds = {k.second_of for k in table.values()}
        for known in table.values():
            if known.second_of == NONE and known.known_id != "fut-sec-8" \
                    and known.known_id not in self.vt.PUBLISHED:
                self.assertIn(known.known_id, seconds, known.known_id)

    def test_every_stated_list_loads_at_every_size_it_names(self):
        sys.path.insert(0, str(CODE_ROOT / "research/004"))
        import ir
        table = self.vt.known_results()
        count = 0
        for known_id, lists in stated_lists(table, self.vt.load_known):
            for program in lists:
                ir.load(program)
                count += 1
        self.assertGreater(count, 100)


def stated_lists(table, load):
    """Every operation list the known results state, each at the sizes its own file names."""
    def module(known_id):
        return load(table[known_id])

    for name in ("dependency-small", "dependency-small-second"):
        m = module(name)
        builds = m.BUILD.values() if hasattr(m, "BUILD") else (m.sweep,)
        yield name, [build(n, w) for build in builds for n, w in m.PAIRS]
    m = module("symmetry-planted")
    yield m.KNOWN_ID, [m.build(e, w) for e in m.CASES + (m.WORD_ROTATION,) for w in m.WIDTHS]
    m = module("symmetry-planted-second")
    yield m.KNOWN_ID, [m.build_amounts(name, n, amount, w) for name, n, amount, _ in m.AMOUNTS
                       for w in m.WIDTHS] + [m.build_placement(w) for w in m.WIDTHS]
    for name in ("invariants-planted", "invariants-planted-second"):
        m = module(name)
        yield name, [build(n, w) for _, n, build, _ in m.CASES for w in m.WIDTHS]
    m = module("s13-transport-second")
    yield m.KNOWN_ID, [m.build(m.N, m.W)]
    for name in ("bijectivity-maps", "bijectivity-maps-second"):
        yield name, [module(name).permutation()]
    for name in ("avalanche-planted", "avalanche-planted-second"):
        m = module(name)
        yield name, [build(n) for build in (m.unmixed, m.closed, m.commuting) for n in m.SIZES]
    m = module("costmodel-examples")
    yield m.KNOWN_ID, [m.build(label, builder) for label, builder, _ in m.EXAMPLES]
    m = module("costmodel-examples-second")
    yield m.KNOWN_ID, [m.build(label, builder, want["n"], want["w"]) for label, builder, want in m.EXAMPLES]
    m = module("degree-small")
    yield m.KNOWN_ID, [m.build(n, w) for n, w in m.PAIRS]
    m = module("degree-small-second")
    yield m.KNOWN_ID, [builder(n, w) for _, builder, n, w, _ in m.CASES]


def exact_critical(n: int, level: Fraction):
    """The largest low count and the smallest high count at which a two-sided p-value is at most
    `level`, by exact integer arithmetic over the binomial distribution with p = 1/2."""
    total = 2 ** n
    tail, low = 0, -1
    for k in range(n // 2 + 1):
        tail += math.comb(n, k)
        if min(Fraction(2 * tail, total), Fraction(1)) > level:
            break
        low = k
    return low, n - low


class CriticalCounts(unittest.TestCase):
    """research/004/tools/critical_counts.json: code, appended to and never changed (R4)."""

    REL = "research/004/tools/critical_counts.json"

    def setUp(self):
        if not (CODE_ROOT / self.REL).exists():
            self.skipTest("the table does not exist yet (T051)")
        self.table = json.loads((CODE_ROOT / self.REL).read_text(encoding="utf-8"))

    def test_every_count_is_recomputed_exactly(self):
        for entry in self.table["entries"]:
            level = Fraction(entry["level_numerator"], entry["level_denominator"])
            self.assertEqual(exact_critical(entry["n"], level), (entry["low"], entry["high"]), entry)

    def test_the_file_is_only_appended_to(self):
        log = evidence.git("log", "--format=%H", "--", self.REL, cwd=CODE_ROOT).decode().split()
        newer: Optional[List] = None
        for commit in log:
            blob = evidence.git("show", f"{commit}:{self.REL}", cwd=CODE_ROOT)
            older = json.loads(blob.decode("utf-8"))["entries"]
            if newer is not None:
                self.assertEqual(newer[:len(older)], older, commit)
            newer = older


@unittest.skipIf(platform.system() == "Windows", "the make file runs in WSL")
class ArxBuild(unittest.TestCase):
    """research R16, R18: the make file gives a binary of one SHA-256 from any directory."""

    MAKE = "research/004/tools/trails/arx_search.mk"
    SOURCE = "research/004/tools/trails/arx_search.c"
    BINARY = "research/004/tools/trails/build/arx_search"

    def test_a_second_directory_builds_the_same_binary(self):
        if not (CODE_ROOT / self.MAKE).exists():
            self.skipTest("the make file does not exist yet (T063)")
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp)
            for rel in (self.MAKE, self.SOURCE):
                target = other / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(CODE_ROOT / rel, target)
            subprocess.run(["make", "-f", self.MAKE], cwd=other, check=True, capture_output=True)
            self.assertEqual(evidence.sha256((other / self.BINARY).read_bytes()),
                             evidence.sha256((CODE_ROOT / self.BINARY).read_bytes()))


if __name__ == "__main__":
    unittest.main()
