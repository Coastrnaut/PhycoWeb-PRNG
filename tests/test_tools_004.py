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

import numpy as np

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

    def test_a_tool_may_name_its_model_per_known_result(self):
        self.tool_with('def model_id(known_id):\n    return "of " + known_id\n')
        self.main()
        self.assertEqual(self.records()[0]["model_id"], "of fake-known")

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

    def test_two_outputs_of_one_name_are_a_tool_failure(self):
        """A reproduction compares by file name, so that the second would hide the first."""
        self.tool_with('''
_real = validation


def validation(known_id, known, keep):
    keep("n4/a.txt", b"{}")
    keep("n8/a.txt", b"{}")
    return _real(known_id, known, keep)
''')
        self.assertEqual(self.main(), evidence.EXIT_TOOL)
        self.assertEqual(self.records()[0]["status"], "inconclusive")

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
        self.assertTrue(output["deterministic"])
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

    KEEPS = """
_real = validation


def validation(known_id, known, keep):
    keep("a.txt", b"one")
    keep("b.txt", b"two")
    return _real(known_id, known, keep)
"""

    def test_a_reproduction_compares_what_the_run_kept(self):
        write(self.root, TOOL_REL, TOOL_TEXT + self.KEEPS)
        self.commit("the tool keeps files")
        self.assertEqual(self.main(), evidence.EXIT_OK)
        record = self.records()[0]
        self.commit("the record")
        path = f"{VALIDATION}/{record['record_id']}.json"
        self.assertEqual(self.vt.main(["--reproduce", path]), evidence.EXIT_OK)
        reproduced = [r for _, r in evidence.iter_records("reproduction")][0]
        self.assertEqual(reproduced["compared"]["outputs"], "match")
        kept = {entry["path"].rsplit("/", 1)[-1]: entry for entry in reproduced["outputs"]}
        self.assertEqual(sorted(kept), ["a.txt", "b.txt"])
        self.assertFalse(kept["a.txt"]["committed"])
        wanted = f"{evidence.LOCAL_REL}/{reproduced['record_id']}/a.txt"
        self.assertEqual(kept["a.txt"]["path"], wanted)
        self.assertEqual((self.root / wanted).read_bytes(), b"one")

    def test_a_reproduction_whose_kept_file_differs_is_exit_1(self):
        write(self.root, TOOL_REL, TOOL_TEXT + self.KEEPS.replace('b"two"', 'b"two" + EXTRA') + 'EXTRA = b""\n')
        self.commit("the tool keeps files")
        self.assertEqual(self.main(), evidence.EXIT_OK)
        record = self.records()[0]
        real = self.vt.measure_in

        def measured(worktree, tool, known_ids, local, binary):
            out = real(worktree, tool, known_ids, local, binary)
            (local / "b.txt").write_bytes(b"three")
            return out

        path = f"{VALIDATION}/{record['record_id']}.json"
        with mock.patch.object(self.vt, "measure_in", side_effect=measured):
            self.assertEqual(self.vt.main(["--reproduce", path]), evidence.EXIT_VERDICT)
        reproduced = [r for _, r in evidence.iter_records("reproduction")][0]
        self.assertEqual(reproduced["compared"]["outputs"], "differs")
        self.assertEqual(reproduced["compared"]["found"], "match")

    def test_a_reproduction_of_nothing_is_refused(self):
        self.assertEqual(self.vt.main(["--reproduce", "nothing.json"]), evidence.EXIT_REFUSED)


def invariants_module():
    sys.path.insert(0, str(CODE_ROOT / "research/004"))
    sys.path.insert(0, str(CODE_ROOT / "research/004/tools"))
    import invariants
    return invariants


class Invariants(unittest.TestCase):
    """research/004/tools/invariants.py on stated lists (T053)."""

    @classmethod
    def setUpClass(cls):
        cls.tool = invariants_module()
        import ir
        cls.ir = ir

    def test_the_forms_of_each_parity(self):
        self.assertEqual(len(self.tool.forms(4)), 12)
        self.assertEqual(len(self.tool.forms(3)), 16)
        self.assertIn(("sum", "vein", 2), self.tool.forms(3))
        self.assertNotIn(("sum", "vein", 2), self.tool.forms(4))

    def test_a_forms_value_on_stated_lanes(self):
        n, w = 2, 8
        states = np.zeros((8, 1), dtype=np.uint64)
        states[self.ir.lane(n, 0, 0, 0), 0] = 0xF0
        states[self.ir.lane(n, 1, 1, 0), 0] = 0x20
        states[self.ir.lane(n, 0, 1, 0), 0] = 0x03
        states[self.ir.lane(n, 0, 0, 1), 0] = 0x55
        values = self.tool.form_values(states, n, w)
        self.assertEqual(int(values[("sum", "pressure", 0)][0]), 0x10)
        self.assertEqual(int(values[("xor", "pressure", 0)][0]), 0xD0)
        self.assertEqual(int(values[("sum", "pressure", 1)][0]), 0x03)
        self.assertEqual(int(values[("sum", "pressure", "all")][0]), 0x13)
        self.assertEqual(int(values[("xor", "vein", "all")][0]), 0x55)

    def test_the_levels_of_r13(self):
        even = Fraction(5, 1000) / 24
        self.assertEqual(self.tool.level_of(("sum", "vein", 0), 4), even)
        self.assertEqual(self.tool.level_of(("sum", "vein", "all"), 4), even)
        self.assertEqual(self.tool.level_of(("sum", "vein", "all"), 3), even)
        self.assertEqual(self.tool.level_of(("sum", "vein", 2), 3), Fraction(5, 1000) / 32)

    def tail(self, states, w, c):
        chance = Fraction(1, 2 ** w)
        return sum(math.comb(states, k) * chance ** k * (1 - chance) ** (states - k)
                   for k in range(c, states + 1))

    def test_the_critical_count_is_where_the_level_falls(self):
        for states, w, level in ((1024, 8, Fraction(1, 4800)), (1024, 4, Fraction(1, 6400)),
                                 (64, 2, Fraction(1, 1000))):
            c = self.tool.critical_count(states, w, level)
            self.assertLessEqual(self.tail(states, w, c), level)
            self.assertGreater(self.tail(states, w, c - 1), level)

    def test_a_count_at_the_critical_value_is_above_chance(self):
        level = Fraction(1, 4800)
        c = self.tool.critical_count(1024, 8, level)
        self.assertTrue(self.tool.above_chance(c, 1024, 8, level))
        self.assertFalse(self.tool.above_chance(c - 1, 1024, 8, level))

    def conserved(self):
        p, v = self.ir.lane(2, 0, 0, 0), self.ir.lane(2, 0, 1, 1)
        q = self.ir.lane(2, 1, 1, 0)
        r = self.ir.lane(2, 0, 1, 0)
        return self.ir.Program("c", 2, 16, (
            self.ir.Phase(0, (self.ir.Mix(p, "add", self.ir.Lane(v)), self.ir.Mix(q, "sub", self.ir.Lane(v)))),
            self.ir.Phase(1, (self.ir.Mix(v, "xor", self.ir.Rotl(self.ir.Lane(r), 3)),))))

    def test_a_kept_form_is_found_and_the_rest_are_not(self):
        loaded = self.ir.load(self.conserved())
        out = self.tool.check(loaded, self.tool.test_states(2, 16), (), (1, 3))
        for rounds in (1, 3):
            self.assertIn(("sum", "pressure", 0), out[rounds]["kept"])
            self.assertNotIn(("xor", "pressure", 0), out[rounds]["kept"])
            self.assertNotIn(("xor", "vein", 1), out[rounds]["kept"])
            self.assertEqual(out[rounds]["held"][("sum", "pressure", 0)], 1024)
            self.assertNotIn(("sum", "pressure", 0), out[rounds]["above_chance"])

    def test_a_form_that_misses_one_state_is_not_kept(self):
        n, w = 2, 8
        lane, other = self.ir.lane(n, 0, 0, 0), self.ir.lane(n, 0, 1, 0)
        states = np.zeros((8, 64), dtype=np.uint64)
        states[other, 0] = 1
        program = self.ir.Program("one", n, w, (self.ir.Phase(0, (
            self.ir.Mix(lane, "xor", self.ir.Lane(other)),)),))
        out = self.tool.check(self.ir.load(program), states, (), (1,))
        self.assertEqual(out[1]["held"][("xor", "pressure", 0)], 63)
        self.assertNotIn(("xor", "pressure", 0), out[1]["kept"])

    def test_each_round_count_is_run_for_itself(self):
        """An XOR with an unwritten lane cancels every second round, as in `colour-class`."""
        n, w = 2, 8
        lane, other = self.ir.lane(n, 0, 0, 0), self.ir.lane(n, 0, 1, 0)
        program = self.ir.Program("twice", n, w, (self.ir.Phase(0, (
            self.ir.Mix(lane, "xor", self.ir.Lane(other)),)),))
        out = self.tool.check(self.ir.load(program), self.tool.test_states(n, w), (), (1, 2))
        self.assertNotIn(("xor", "pressure", 0), out[1]["kept"])
        self.assertIn(("xor", "pressure", 0), out[2]["kept"])

    def test_a_form_above_chance_is_not_a_kept_one(self):
        """A lane that changes only in its top bit keeps a form on half the states."""
        n, w = 2, 8
        lane = self.ir.lane(n, 0, 0, 0)
        program = self.ir.Program("half", n, w, (self.ir.Phase(0, (
            self.ir.Mix(lane, "xor", self.ir.Shl(self.ir.Lane(self.ir.lane(n, 0, 1, 0)), 7)),)),))
        out = self.tool.check(self.ir.load(program), self.tool.test_states(n, w), (), (1,))
        over = out[1]["above_chance"]
        self.assertIn(("xor", "pressure", 0), over)
        self.assertNotIn(("xor", "pressure", 0), out[1]["kept"])

    def test_a_table_is_read_a_round_at_a_time(self):
        n, w = 2, 8
        program = self.ir.Program("c", n, w, (self.ir.Phase(0, (
            self.ir.Mix(0, "xor", self.ir.Constant(0)),)),))
        states = self.tool.test_states(n, w, 8)
        out = self.tool.check(self.ir.load(program), states, [(0x11,), (0x11,), (0x22,)], (1, 2, 3))
        self.assertNotIn(("xor", "pressure", 0), out[1]["kept"])
        self.assertIn(("xor", "pressure", 0), out[2]["kept"])
        self.assertNotIn(("xor", "pressure", 0), out[3]["kept"])

    def test_a_difference_kept_and_one_lost(self):
        n, w = 2, 8
        lane, other = self.ir.lane(n, 0, 0, 0), self.ir.lane(n, 0, 1, 1)
        program = self.ir.Program("d", n, w, (self.ir.Phase(1, (
            self.ir.Mix(other, "add", self.ir.Lane(lane)),)),))
        loaded = self.ir.load(program)
        states = self.tool.test_states(n, w, 16)
        on_other = self.tool.difference_kept(loaded, states, {other: 1}, (), 1)
        self.assertEqual((on_other["unchanged"], on_other["coinciding"]), (16, 0))
        on_lane = self.tool.difference_kept(loaded, states, {lane: 1}, (), 1)
        self.assertEqual(on_lane["unchanged"], 0)

    def test_a_difference_is_run_for_its_round_count(self):
        """A rotation by half the width: a difference of 1 is back in place after two rounds."""
        n, w = 2, 8
        loaded = self.ir.load(self.ir.Program("r", n, w, (self.ir.Phase(0, (self.ir.Rot(0, 4),)),)))
        states = np.zeros((8, 4), dtype=np.uint64)
        self.assertEqual(self.tool.difference_kept(loaded, states, {0: 1}, (), 1)["unchanged"], 0)
        self.assertEqual(self.tool.difference_kept(loaded, states, {0: 1}, (), 2)["unchanged"], 4)

    def test_coinciding_successors_are_counted_beside(self):
        n, w = 2, 8
        states = self.tool.test_states(n, w, 16)
        loaded = self.ir.load(self.ir.Program("r", n, w, (self.ir.Phase(0, (self.ir.Rot(0, 1),)),)))
        out = self.tool.difference_kept(loaded, states, {}, (), 1)
        self.assertEqual((out["unchanged"], out["coinciding"]), (16, 16))

    def test_a_difference_reads_the_constant_table(self):
        n, w = 2, 8
        states = self.tool.test_states(n, w, 8)
        loaded = self.ir.load(self.ir.Program("c", n, w, (self.ir.Phase(0, (
            self.ir.Mix(0, "xor", self.ir.Constant(0)),)),)))
        self.assertEqual(self.tool.difference_kept(loaded, states, {1: 1}, [(3,), (5,)], 2)["unchanged"], 8)

    def test_a_count_must_lie_in_every_interval(self):
        low, high = self.tool.interval(0.3, 1000)
        self.assertEqual((low, high), (263, 338), "0.3 at 1000, 2.576 standard deviations of 14.5")
        self.assertTrue(self.tool.in_interval(300, (0.3,), 1000))
        self.assertFalse(self.tool.in_interval(low - 1, (0.3,), 1000))
        self.assertFalse(self.tool.in_interval(high + 1, (0.3,), 1000))
        self.assertFalse(self.tool.in_interval(300, (0.3, 0.5), 1000))


class InvariantsOnKnown(unittest.TestCase):
    """The tool on the known results that run quickly, each deciding fact broken once."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(CODE_ROOT))
        from scripts import validate_tool
        cls.vt = validate_tool
        cls.tool = invariants_module()
        cls.table = validate_tool.known_results()

    def known(self, name):
        return self.vt.load_known(self.table[name])

    def test_the_seconds_of_s13_are_re_found(self):
        for name in ("s13-transport-second", "s13-decay-second"):
            self.assertTrue(self.tool.validation(name, self.known(name), None)["re_found"], name)

    def test_a_stated_list_breaks_its_known_result_when_it_changes(self):
        known = self.known("invariants-planted")
        wrong = tuple((label, n, build, {1: (), known.ROUNDS: ()}) for label, n, build, _ in known.CASES[:1])
        with mock.patch.object(known, "CASES", wrong), mock.patch.object(known, "WIDTHS", (16,)):
            self.assertFalse(self.tool.validation("invariants-planted", known, None)["re_found"])

    def test_a_form_said_kept_that_is_not_breaks_it(self):
        known = self.known("invariants-planted")
        label, n, build, _ = known.CASES[3]
        wrong = ((label, n, build, {1: (("sum", "vein", 0),), known.ROUNDS: ()}),)
        with mock.patch.object(known, "CASES", wrong), mock.patch.object(known, "WIDTHS", (16,)):
            self.assertFalse(self.tool.validation("invariants-planted", known, None)["re_found"])

    def test_on_none_a_form_above_chance_breaks_it(self):
        known = self.known("invariants-planted")
        label, n, build, wanted = known.CASES[3]
        with mock.patch.object(known, "CASES", ((label, n, build, wanted),)), \
                mock.patch.object(known, "WIDTHS", (16,)), \
                mock.patch.object(self.tool, "above_chance", return_value=True):
            self.assertFalse(self.tool.validation("invariants-planted", known, None)["re_found"])

    def test_above_chance_on_a_planted_list_decides_nothing(self):
        known = self.known("invariants-planted")
        label, n, build, wanted = known.CASES[0]
        with mock.patch.object(known, "CASES", ((label, n, build, wanted),)), \
                mock.patch.object(known, "WIDTHS", (16,)), \
                mock.patch.object(self.tool, "above_chance", return_value=True):
            self.assertTrue(self.tool.validation("invariants-planted", known, None)["re_found"])

    def test_a_difference_not_kept_breaks_the_transport_second(self):
        known = self.known("s13-transport-second")
        with mock.patch.object(known, "difference", return_value={0: 1}):
            self.assertFalse(self.tool.validation("s13-transport-second", known, None)["re_found"])

    def test_a_pair_that_does_not_merge_breaks_the_decay_second(self):
        known = self.known("s13-decay-second")
        with mock.patch.object(known, "pair", lambda m: (1, 2 ** 20)):
            self.assertFalse(self.tool.validation("s13-decay-second", known, None)["re_found"])

    def test_another_share_breaks_the_decay_second(self):
        known = self.known("s13-decay-second")
        with mock.patch.object(known, "SHARE", 0.5):
            self.assertFalse(self.tool.validation("s13-decay-second", known, None)["re_found"])

    def s13(self, name, measured, wanted, field):
        function = {"decay": "decay_mode", "transport": "transport_mode"}[name]
        recorded = {field: wanted}
        run = {"decay": self.tool.re_find_decay, "transport": self.tool.re_find_transport}[name]
        with mock.patch.object(self.tool, function, return_value=measured), \
                mock.patch.object(self.tool, "recorded", return_value=recorded):
            return run(None, None)["re_found"]

    def test_s13_a_needs_every_pair_merged_and_both_shares(self):
        wanted = {"share_with_a_partner": 0.42, "expected_share": 0.41}

        def found(pairs=100, same=100, partners=2075):
            return {"steps": 5000, "pairs_tested": pairs, "identical_successors": same,
                    "states_with_a_partner": partners}

        field = "s13_vein_decay"
        self.assertTrue(self.s13("decay", found(), wanted, field))
        self.assertFalse(self.s13("decay", found(same=99), wanted, field))
        self.assertFalse(self.s13("decay", found(pairs=0, same=0), wanted, field))
        self.assertFalse(self.s13("decay", found(partners=1500), wanted, field))

    def test_s13_b_needs_every_sum_unchanged_and_both_shares(self):
        wanted = {"share_identical": 0.316, "expected_share": 0.3164}

        def found(states=1000, same=1000, coinciding=316):
            return {"steps": 2000, "all_class_1_states": states, "transport_unchanged": same,
                    "identical_successors": coinciding}

        field = "s13_alternating_mode"
        self.assertTrue(self.s13("transport", found(), wanted, field))
        self.assertFalse(self.s13("transport", found(same=999), wanted, field))
        self.assertFalse(self.s13("transport", found(states=0, same=0, coinciding=0), wanted, field))
        self.assertFalse(self.s13("transport", found(coinciding=100), wanted, field))

    def test_a_lost_difference_at_either_round_count_breaks_the_transport_second(self):
        known = self.known("s13-transport-second")
        for lost in (1, known.ROUNDS):
            def kept(loaded, states, delta, table, rounds):
                return {"states": 4, "unchanged": 3 if rounds == lost else 4, "coinciding": 0}

            with mock.patch.object(self.tool, "difference_kept", kept):
                self.assertFalse(self.tool.validation("s13-transport-second", known, None)["re_found"], lost)

    def test_each_pair_of_s13_a_differs_by_one_where_the_decay_merges_it(self):
        p = self.tool.probes()
        seen = []
        real = p.clone

        def recording(engine):
            copy = real(engine)
            step = copy.compute_block

            def stepped():
                seen.append(list(copy.D))
                return step()

            copy.compute_block = stepped
            return copy

        with mock.patch.object(p, "DECAY_STEPS", 3), mock.patch.object(p, "clone", recording):
            self.tool.decay_mode()
        self.assertEqual(len(seen), 24)
        for first, second in zip(seen[0::2], seen[1::2]):
            moved = [(a, b) for a, b in zip(first, second) if a != b]
            self.assertEqual(len(moved), 1)
            self.assertEqual((moved[0][0] % 16, moved[0][1] - moved[0][0]), (15, 1))

    def test_a_pair_across_a_class_edge_is_left_out(self):
        class Engine:
            def __init__(self, seed):
                self.D = [(1 << 30) - 1, 5, 5, 5]

            def compute_block(self):
                pass

        p = self.tool.probes()

        def copied(engine):
            other = Engine(None)
            other.D = list(engine.D)
            return other

        with mock.patch.object(self.tool, "PhycoWebEngineV2", Engine), \
                mock.patch.object(p, "DECAY_STEPS", 1), mock.patch.object(p, "clone", copied), \
                mock.patch.object(p, "state", lambda e: tuple(e.D)):
            self.assertEqual(self.tool.decay_mode()["pairs_tested"], 3)

    def test_the_modes_on_a_short_sample_are_those_of_the_probes(self):
        p = self.tool.probes()
        with mock.patch.object(p, "DECAY_STEPS", 200), mock.patch.object(p, "ALT_STEPS", 500):
            decay, ours = p.decay_collisions(), self.tool.decay_mode()
            transport, theirs = p.alternating_mode(), self.tool.transport_mode()
        for field in ("pairs_tested", "identical_successors", "states_with_a_partner"):
            self.assertEqual(decay[field], ours[field], field)
        self.assertEqual(transport["all_class_1_states"], theirs["all_class_1_states"])
        self.assertEqual(transport["transport_unchanged"], theirs["transport_unchanged"])
        self.assertEqual(transport["identical_successors"], theirs["identical_successors"])

    def test_only_the_s13_results_are_of_the_model(self):
        self.assertEqual(self.tool.model_id("s13-decay"), "phyco-v2")
        self.assertEqual(self.tool.model_id("s13-transport"), "phyco-v2")
        self.assertIsNone(self.tool.model_id("invariants-planted"))
        self.assertEqual(self.tool.inputs("s13-decay")["kind"], "seed")
        self.assertEqual(self.tool.inputs("invariants-planted")["kind"], "state")


def symmetry_module():
    sys.path.insert(0, str(CODE_ROOT / "research/004"))
    sys.path.insert(0, str(CODE_ROOT / "research/004/tools"))
    import symmetry
    return symmetry


class Symmetry(unittest.TestCase):
    """research/004/tools/symmetry.py on stated patterns (T054)."""

    @classmethod
    def setUpClass(cls):
        cls.tool = symmetry_module()
        import ir
        cls.ir = ir

    def test_the_group_moves_a_node_and_holds_each_map_once(self):
        for n, size in ((3, 71), (4, 127), (5, 199), (8, 511)):
            items = self.tool.group(n)
            self.assertEqual(len(items), size, n)
            self.assertEqual(len({image for _, image in items}), size, n)
            self.assertNotIn(tuple(self.tool.nodes(n)), [image for _, image in items])

    def test_at_2x2_several_names_are_one_map(self):
        items = self.tool.group(2)
        self.assertEqual(len({image for _, image in items}), len(items))
        self.assertLess(len(items), 8 * 4 - 1)

    def test_each_symmetry_keeps_the_torus(self):
        """A symmetry sends neighbours to neighbours, wrap-around links included."""
        for n in (3, 4, 5):
            order = self.tool.nodes(n)
            for _, image in self.tool.group(n):
                table = dict(zip(order, image))
                for i, j in order:
                    near = self.ir.neighbours(n, *table[(i, j)])
                    self.assertIn(table[((i + 1) % n, j)], near)
                    self.assertIn(table[(i, (j + 1) % n)], near)

    def test_each_named_linear_part(self):
        items = dict(self.tool.group(5))
        self.assertEqual(items[("r90", 0, 0)][self.tool.nodes(5).index((1, 2))], (2, 4))
        self.assertEqual(items[("r270", 0, 0)][self.tool.nodes(5).index((1, 2))], (3, 1))
        self.assertEqual(items[("r180", 0, 0)][self.tool.nodes(5).index((1, 2))], (4, 3))
        self.assertEqual(items[("swap", 0, 0)][self.tool.nodes(5).index((1, 2))], (2, 1))
        self.assertEqual(items[("flip-j", 0, 0)][self.tool.nodes(5).index((1, 2))], (1, 3))
        self.assertEqual(items[("flip-i", 0, 0)][self.tool.nodes(5).index((1, 2))], (4, 2))
        self.assertEqual(items[("anti", 0, 0)][self.tool.nodes(5).index((1, 2))], (3, 4))
        self.assertEqual(items[("id", 2, 3)][self.tool.nodes(5).index((1, 2))], (3, 0))

    def test_the_uniform_pattern_is_fixed_by_everything(self):
        pattern = {node: 1 for node in self.tool.nodes(3)}
        self.assertEqual(len(self.tool.fixing(pattern, 3)), 71)

    def test_a_node_outside_a_pattern_holds_nothing(self):
        self.assertEqual(self.tool.fixing({(0, 0): 1, (0, 1): 1, (1, 2): 1}, 4), [])

    def test_a_value_counts_not_only_a_place(self):
        """Three values at three nodes not on a line: a symmetry would have to hold each in place."""
        n = 3
        same = {(0, 0): 1, (0, 1): 2, (1, 0): 2}
        different = {(0, 0): 1, (0, 1): 2, (1, 0): 3}
        self.assertEqual(len(self.tool.fixing(same, n)), 1)
        self.assertEqual(self.tool.fixing(different, n), [])

    def test_word_rotations_of_a_stated_round(self):
        words = {(0, 0): ((0, 0x33),), (1, 1): ((0, 0x33),)}
        self.assertEqual(self.tool.word_rotations(words, 8), [4])
        self.assertEqual(self.tool.word_rotations({(0, 0): ((0, 0x1D),)}, 8), [])
        self.assertEqual(self.tool.word_rotations({(0, 0): ((0, 0x55),)}, 8), [2, 4, 6])
        self.assertEqual(self.tool.word_rotations({(0, 0): ((1, 0x33),)}, 8), [4], "on a vein")

    def test_one_word_of_a_round_is_not_enough(self):
        words = {(0, 0): ((0, 0x33),), (1, 1): ((0, 0x1D),)}
        self.assertEqual(self.tool.word_rotations(words, 8), [])

    def test_a_symmetry_composed_with_a_word_rotation(self):
        """Neither alone fixes it: `swap` exchanges two words a rotation by 4 apart, and that rotation
        leaves the third, of period 4, where it is."""
        pattern = {(0, 0): ((0, 0x33),), (0, 1): ((0, 0x1D),), (1, 0): ((0, 0xD1),)}
        self.assertEqual(self.tool.fixing(pattern, 3), [])
        self.assertEqual(self.tool.word_rotations(pattern, 8), [])
        self.assertEqual(self.tool.composed(pattern, 3, 8), [[["swap", 0, 0], 4]])

    def test_a_list_gives_its_patterns(self):
        n, w = 4, 8
        p00, v01 = self.ir.lane(n, 0, 0, 0), self.ir.lane(n, 0, 1, 1)
        program = self.ir.Program("p", n, w, (
            self.ir.Phase(0, (self.ir.Mix(p00, "xor", self.ir.Xor(self.ir.Constant(1), self.ir.Rotl(
                self.ir.Lane(self.ir.lane(n, 0, 0, 1)), 3))),)),
            self.ir.Phase(1, (self.ir.Rot(v01, 5),))))
        each = self.tool.patterns(program, [(0xA, 0xB), (0xC, 0xD)])
        self.assertEqual(each["placement"], {(0, 0): 1})
        self.assertEqual(each["round 0"], {(0, 0): ((0, 0xB),)})
        self.assertEqual(each["round 1"], {(0, 0): ((0, 0xD),)})
        self.assertEqual(each["amounts"], {(0, 0): (("Rotl", 3),), (0, 1): (("Rot", 5),)})

    def test_a_lane_kind_is_part_of_a_constants_place(self):
        n, w = 4, 8
        program = self.ir.Program("p", n, w, (self.ir.Phase(0, (
            self.ir.Mix(self.ir.lane(n, 0, 0, 1), "xor", self.ir.Constant(0)),)),))
        self.assertEqual(self.tool.patterns(program, [(7,)])["round 0"], {(0, 0): ((1, 7),)})

    def test_amounts_are_read_at_every_depth(self):
        lane = self.ir.Lane(0)
        expr = self.ir.Not(self.ir.Xor(self.ir.Shl(lane, 1), self.ir.And(self.ir.Shr(lane, 2), self.ir.Or(
            self.ir.Rotl(self.ir.Rotl(lane, 3), 4), lane))))
        self.assertEqual(self.tool.amounts_in(expr), [("Shl", 1), ("Shr", 2), ("Rotl", 4), ("Rotl", 3)])

    def test_no_amounts_gives_no_pattern_and_no_constants_gives_no_placement(self):
        n, w = 4, 8
        with_rot = self.ir.Program("r", n, w, (self.ir.Phase(0, (self.ir.Rot(0, 1),)),))
        self.assertEqual(sorted(self.tool.patterns(with_rot, ())), ["amounts"])
        with_constant = self.ir.Program("c", n, w, (self.ir.Phase(0, (
            self.ir.Mix(0, "xor", self.ir.Constant(0)),)),))
        self.assertNotIn("amounts", self.tool.patterns(with_constant, [(1,)]))

    def test_a_claimable_size_checks_each_pattern_on_its_own(self):
        n, w = 4, 8
        program = self.ir.Program("c", n, w, (self.ir.Phase(0, (
            self.ir.Mix(0, "xor", self.ir.Constant(0)),)),))
        out = self.tool.check(program, [(0x1D,)])
        self.assertFalse(out["joined"])
        self.assertEqual(sorted(out["fixed"]), ["placement", "round 0"])

    def test_at_3x3_the_placements_join_the_constants(self):
        n, w = 3, 8
        program = self.ir.Program("c", n, w, (
            self.ir.Phase(0, (self.ir.Mix(self.ir.lane(n, 0, 0, 0), "xor", self.ir.Constant(0)),)),
            self.ir.Phase(1, (self.ir.Mix(self.ir.lane(n, 0, 1, 0), "xor", self.ir.Constant(1)),
                              self.ir.Rot(self.ir.lane(n, 1, 0, 1), 3)))))
        out = self.tool.check(program, [(0x1D, 0x2B)])
        self.assertTrue(out["joined"])
        self.assertEqual(sorted(out["fixed"]), ["round 0 with the placements"])
        self.assertEqual(out["fixed"]["round 0 with the placements"], [])

    def test_the_check_reports_word_rotations_and_compositions(self):
        n, w = 4, 8
        program = self.ir.Program("c", n, w, (self.ir.Phase(0, (
            self.ir.Mix(0, "xor", self.ir.Constant(0)),)),))
        out = self.tool.check(program, [(0x33,)])
        self.assertEqual(out["word_rotations"]["round 0"], [4])
        self.assertTrue(out["composed"]["round 0"] == [] or out["composed"]["round 0"])

    def test_relations_between_stated_words(self):
        found = self.tool.relations([0x12, 0x21, 0xED, 0x12, 0x55], 8)
        self.assertEqual(found["equal"], [[0x12, 0x12]])
        self.assertIn([0x12, 0x21, [4]], found["rotations"])
        self.assertIn([0x12, 0xED], found["complements"])
        self.assertIn([0x21, 0xED, [4]], found["rotated_complements"])
        self.assertEqual(found["periodic"], [[0x55, [2, 4, 6]]])

    def test_equal_words_are_equal_and_no_rotation_of_each_other(self):
        found = self.tool.relations([0x55, 0x55], 8)
        self.assertEqual(found["equal"], [[0x55, 0x55]])
        self.assertEqual(found["rotations"], [])


class SymmetryOnKnown(unittest.TestCase):
    """The tool on its known results, each deciding fact broken once."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(CODE_ROOT))
        from scripts import validate_tool
        cls.vt = validate_tool
        cls.tool = symmetry_module()
        cls.table = validate_tool.known_results()

    def known(self, name):
        return self.vt.load_known(self.table[name])

    def run_known(self, name, known=None):
        return self.tool.validation(name, known or self.known(name), None)["re_found"]

    def test_each_known_result_is_re_found(self):
        for name in ("s7", "symmetry-s7-second", "symmetry-planted", "symmetry-planted-second"):
            self.assertTrue(self.run_known(name), name)

    def test_s7_needs_each_of_its_three_relations(self):
        import phycoweb.model_v2 as model
        with mock.patch.object(model, "X1", 0x5A5A5A5B):
            self.assertFalse(self.run_known("s7"))
        with mock.patch.object(model, "X3", 0xA5A5A5A4):
            self.assertFalse(self.run_known("s7"))
        with mock.patch.object(self.tool, "RESET_VEINS", (0x00010000, 0x00020000, 0x00040000, 0x00080001)):
            self.assertFalse(self.run_known("s7"))

    def test_s7_reads_its_periodic_word_for_itself(self):
        import phycoweb.model_v2 as model
        real = self.tool.relations

        def without(words, w):
            found = real(words, w)
            return dict(found, periodic=[item for item in found["periodic"] if item[0] != model.X1])

        with mock.patch.object(self.tool, "relations", without):
            self.assertFalse(self.run_known("s7"))

    def test_the_seconds_relations_are_compared_one_by_one(self):
        name = "symmetry-s7-second"
        for field, value in (("FIXED_BY", {}), ("ROTATIONS", ()), ("COMPLEMENTS", ())):
            known = self.known(name)
            with mock.patch.object(known, field, value):
                self.assertFalse(self.run_known(name, known), field)
        known = self.known(name)
        with mock.patch.object(known, "WORDS", known.WORDS + (known.UNRELATED,)):
            self.assertFalse(self.run_known(name, known), "two equal words")

    def narrowed(self, known, **changes):
        entry = dict(known.CASES[0], **changes)
        return mock.patch.object(known, "CASES", (entry,)), mock.patch.object(known, "WIDTHS", (8,))

    def test_a_planted_result_needs_each_pattern(self):
        name = "symmetry-planted"
        for changes in ({"placement": ()}, {"round": ()}, {"placement": (("id", 2, 2),)}):
            known = self.known(name)
            first, second = self.narrowed(known, **changes)
            with first, second:
                self.assertFalse(self.run_known(name, known), changes)

    def test_a_planted_result_needs_its_word_rotations(self):
        name = "symmetry-planted"
        known = self.known(name)
        first, second = self.narrowed(known)
        with first, second, mock.patch.object(known, "word_rotations", lambda entry, w: (4,)):
            self.assertFalse(self.run_known(name, known))

    def test_a_planted_result_needs_every_round(self):
        name = "symmetry-planted"
        known = self.known(name)
        first, second = self.narrowed(known)
        with first, second, mock.patch.object(known, "ROUNDS", 3):
            self.assertFalse(self.run_known(name, known))

    def test_a_composition_on_a_planted_list_breaks_it(self):
        name = "symmetry-planted"
        known = self.known(name)
        first, second = self.narrowed(known)
        with first, second, mock.patch.object(self.tool, "composed", return_value=[[["id", 0, 0], 1]]):
            self.assertFalse(self.run_known(name, known))

    def test_a_list_with_amounts_breaks_a_first_that_has_none(self):
        name = "symmetry-planted"
        known = self.known(name)
        first, second = self.narrowed(known)
        with first, second, mock.patch.object(self.tool, "amounts_at", return_value={(0, 0): (("Rot", 1),)}):
            self.assertFalse(self.run_known(name, known))

    def test_the_second_needs_each_amounts_result_and_the_placement(self):
        name = "symmetry-planted-second"
        known = self.known(name)
        label, n, amount, _ = known.AMOUNTS[0]
        with mock.patch.object(known, "AMOUNTS", ((label, n, amount, ()),)):
            self.assertFalse(self.run_known(name, known))
        known = self.known(name)
        with mock.patch.object(known, "TURNS", ()):
            self.assertFalse(self.run_known(name, known))

    def test_the_second_needs_each_rounds_constants_unfixed(self):
        name = "symmetry-planted-second"
        known = self.known(name)
        same = {w: tuple([known.WORDS[w][0]] * 8) for w in known.WIDTHS}
        with mock.patch.object(known, "WORDS", same):
            self.assertFalse(self.run_known(name, known))

    def test_only_s7_is_of_the_model(self):
        self.assertEqual(self.tool.model_id("s7"), "phyco-v2")
        self.assertIsNone(self.tool.model_id("symmetry-planted"))


def dependency_module():
    sys.path.insert(0, str(CODE_ROOT / "research/004"))
    sys.path.insert(0, str(CODE_ROOT / "research/004/tools"))
    import dependency
    return dependency


class Dependency(unittest.TestCase):
    """research/004/tools/dependency.py on stated lists (T055)."""

    @classmethod
    def setUpClass(cls):
        cls.tool = dependency_module()
        import ir
        cls.ir = ir

    def sets(self, program, rounds=1, direction="forward"):
        return self.tool.as_sets(self.tool.matrix(program, direction, rounds), program.w)

    def one(self, update, w=8):
        return self.ir.Program("one", 2, w, (self.ir.Phase(0, (update,)),))

    def test_the_identity(self):
        sets = self.tool.as_sets(self.tool.identity(2, 8), 8)
        self.assertEqual(len(sets), 64)
        self.assertTrue(all(value == {key} for key, value in sets.items()))

    def test_a_row_holds_every_bit_at_any_length(self):
        for bits in (1, 63, 64, 65, 128, 200):
            row = self.tool.full_rows(bits)
            self.assertEqual(len(row), self.tool.words_for(bits))
            self.assertEqual(int(np.unpackbits(row.view(np.uint8)).sum()), bits)

    def test_xor_unites_and_rotation_moves(self):
        sets = self.sets(self.one(self.ir.Mix(0, "xor", self.ir.Rotl(self.ir.Lane(1), 3))))
        self.assertEqual(sets[(0, 5)], {(0, 5), (1, 2)})
        self.assertEqual(sets[(0, 1)], {(0, 1), (1, 6)})
        self.assertEqual(sets[(1, 5)], {(1, 5)})

    def test_shifts_bring_in_nothing(self):
        left = self.sets(self.one(self.ir.Mix(0, "xor", self.ir.Shl(self.ir.Lane(1), 3))))
        self.assertEqual(left[(0, 5)], {(0, 5), (1, 2)})
        self.assertEqual(left[(0, 2)], {(0, 2)})
        right = self.sets(self.one(self.ir.Mix(0, "xor", self.ir.Shr(self.ir.Lane(1), 3))))
        self.assertEqual(right[(0, 2)], {(0, 2), (1, 5)})
        self.assertEqual(right[(0, 5)], {(0, 5)})

    def test_and_or_not_unite(self):
        for form in (self.ir.And, self.ir.Or):
            sets = self.sets(self.one(self.ir.Mix(0, "xor", form(self.ir.Not(self.ir.Lane(1)), self.ir.Lane(2)))))
            self.assertEqual(sets[(0, 3)], {(0, 3), (1, 3), (2, 3)})

    def test_addition_and_subtraction_reach_every_lower_bit(self):
        for op in ("add", "sub"):
            sets = self.sets(self.one(self.ir.Mix(0, op, self.ir.Lane(1))))
            self.assertEqual(sets[(0, 2)], {(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)})
            self.assertEqual(sets[(0, 0)], {(0, 0), (1, 0)})

    def test_a_constant_holds_nothing(self):
        sets = self.sets(self.one(self.ir.Mix(1, "add", self.ir.Constant(0))))
        self.assertEqual(sets[(1, 2)], {(1, 0), (1, 1), (1, 2)})

    def test_a_rotation_update_moves_a_lane(self):
        sets = self.sets(self.one(self.ir.Rot(0, 3)))
        self.assertEqual(sets[(0, 5)], {(0, 2)})

    def test_a_phase_reads_the_values_at_its_start(self):
        """On a list the loader would refuse, so that list order gives another answer."""
        program = self.ir.Program("x", 2, 8, (self.ir.Phase(0, (
            self.ir.Mix(1, "xor", self.ir.Lane(2)), self.ir.Mix(0, "xor", self.ir.Lane(1)))),))
        self.assertEqual(self.sets(program)[(0, 3)], {(0, 3), (1, 3)})

    def test_the_inverse_runs_the_undone_list(self):
        program = self.ir.Program("x", 2, 8, (
            self.ir.Phase(0, (self.ir.Rot(1, 1),)),
            self.ir.Phase(0, (self.ir.Mix(0, "xor", self.ir.Lane(1)),))))
        self.assertEqual(self.sets(program, 1, "forward")[(0, 3)], {(0, 3), (1, 2)})
        self.assertEqual(self.sets(program, 1, "inverse")[(0, 3)], {(0, 3), (1, 3)})

    def test_rounds_compose(self):
        program = self.one(self.ir.Rot(0, 1))
        self.assertEqual(self.sets(program, 3)[(0, 5)], {(0, 2)})

    def test_first_full_stops_when_nothing_changes(self):
        self.assertIsNone(self.tool.first_full(self.one(self.ir.Mix(0, "xor", self.ir.Lane(1))), "forward"))

    def test_first_full_stops_at_its_limit(self):
        """A rotation never settles, so that only the limit ends the walk."""
        seen = []
        for rounds, _ in self.tool.walk(self.one(self.ir.Rot(0, 1)), "forward", self.tool.identity(2, 8), 5):
            seen.append(rounds)
        self.assertEqual(seen, [1, 2, 3, 4, 5])

    def test_missing_pairs_counts_what_is_absent(self):
        n, w = 2, 4
        bits = 32
        self.assertEqual(self.tool.missing_pairs(self.tool.identity(n, w), bits), 32 * 32 - 32)

    def test_dependent_bits_reads_one_input_bits_column(self):
        state = self.tool.matrix(self.one(self.ir.Mix(0, "xor", self.ir.Rotl(self.ir.Lane(1), 3))), "forward", 1)
        flipped = 1 * 8 + 2
        out = self.tool.dependent_bits(state, flipped)
        self.assertEqual({(int(a), int(b)) for a, b in zip(*np.nonzero(out))}, {(0, 5), (1, 2)})

    def test_the_report_counts_each_round_and_finds_r_f(self):
        sys.path.insert(0, str(CODE_ROOT))
        from scripts import validate_tool
        table = validate_tool.known_results()
        known = validate_tool.load_known(table["dependency-small-second"])
        out = self.tool.report(known.sweep(2, 4))
        self.assertEqual(out["forward"]["first_full"], 2)
        self.assertEqual(out["inverse"]["first_full"], 8)
        self.assertEqual(out["forward"]["pairs_without_dependency"], [1024 - 604, 0])
        self.assertEqual(out["inverse"]["pairs_without_dependency"][:2], [1024 - 176, 1024 - 320])
        self.assertEqual(out["inverse"]["pairs_without_dependency"][-1], 0)

    def test_the_report_of_a_list_that_never_fills(self):
        out = self.tool.report(self.one(self.ir.Mix(0, "xor", self.ir.Lane(1))))
        self.assertIsNone(out["forward"]["first_full"])
        self.assertEqual(len(out["forward"]["pairs_without_dependency"]), 2)

    def test_the_margin_through_instantiate(self):
        """Two key bits, one in each word of a loop of two lanes: the sets fill after two rounds."""
        n, w = 2, 4
        program = self.ir.Program("m", n, w, (
            self.ir.Phase(0, (self.ir.Mix(0, "add", self.ir.Rotl(self.ir.Lane(4), 1)),)),))
        start = np.zeros((8, w, 1), dtype=np.uint64)
        start[0, 0, 0] = 1
        self.assertIsNone(self.tool.first_full(program, "forward", 8, start, 2))
        out = self.tool.margin(program, start, 2, 7)
        self.assertEqual(out["every_bit_reached_after"], None)
        self.assertFalse(out["holds"])

    def test_the_margin_when_every_lane_holds_every_symbol(self):
        n, w = 2, 4
        program = self.ir.Program("r", n, w, (self.ir.Phase(0, (self.ir.Rot(0, 1),)),))
        start = np.full((8, w, 1), np.uint64(3), dtype=np.uint64)
        out = self.tool.margin(program, start, 2, 5, 8)
        self.assertEqual(out["every_bit_reached_after"], 1)
        self.assertTrue(out["holds"])
        self.assertEqual(out["rounds_before_first_output"], 5)
        self.assertIsNone(out["margin_over_r_f"])

    def test_the_margin_over_r_f(self):
        sys.path.insert(0, str(CODE_ROOT))
        from scripts import validate_tool
        known = validate_tool.load_known(validate_tool.known_results()["dependency-small-second"])
        program = known.sweep(2, 4)
        start = np.full((8, 4, 1), np.uint64(1), dtype=np.uint64)
        out = self.tool.margin(program, start, 1, 5)
        self.assertEqual((out["r_f"], out["margin_over_r_f"]), (2, 3))
        self.assertEqual(out["every_bit_reached_after"], 1)

    def test_a_late_arrival_does_not_hold(self):
        sys.path.insert(0, str(CODE_ROOT))
        from scripts import validate_tool
        known = validate_tool.load_known(validate_tool.known_results()["dependency-small-second"])
        program = known.sweep(2, 4)
        start = np.zeros((8, 4, 1), dtype=np.uint64)
        start[1, 0, 0] = 1
        out = self.tool.margin(program, start, 1, 1)
        self.assertEqual(out["every_bit_reached_after"], 2)
        self.assertFalse(out["holds"])
        self.assertTrue(self.tool.margin(program, start, 1, 2)["holds"], "the last round before it")


class DependencyOnKnown(unittest.TestCase):
    """The tool on its known results, each deciding fact broken once."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(CODE_ROOT))
        from scripts import validate_tool
        cls.vt = validate_tool
        cls.tool = dependency_module()
        cls.table = validate_tool.known_results()

    def known(self, name):
        return self.vt.load_known(self.table[name])

    def test_each_is_re_found_entry_by_entry(self):
        for name in ("dependency-small", "dependency-small-second"):
            out = self.tool.validation(name, self.known(name), None)
            self.assertTrue(out["re_found"], name)
            self.assertEqual(sum(row["differences"] for row in out["found"]["rows"]), 0)

    def test_one_entry_changed_breaks_the_first(self):
        known = self.known("dependency-small")
        real = known.expected

        def wrong(name, n, w, direction, rounds):
            out = {key: set(value) for key, value in real(name, n, w, direction, rounds).items()}
            out[(0, 0)] = out[(0, 0)] | {(1, 1)}
            return out

        with mock.patch.object(known, "expected", wrong):
            self.assertFalse(self.tool.validation("dependency-small", known, None)["re_found"])

    def test_an_entry_too_few_breaks_the_second(self):
        known = self.known("dependency-small-second")
        real = known.expected

        def wrong(n, w, direction, rounds):
            out = {key: set(value) for key, value in real(n, w, direction, rounds).items()}
            out[(0, 0)] = set(list(out[(0, 0)])[1:])
            return out

        with mock.patch.object(known, "expected", wrong), mock.patch.object(known, "PAIRS", ((2, 4),)):
            self.assertFalse(self.tool.validation("dependency-small-second", known, None)["re_found"])

    def test_a_stated_r_f_or_r_b_is_compared(self):
        known = self.known("dependency-small-second")
        with mock.patch.object(known, "first_full", lambda n: {"forward": 3, "inverse": 2 * n * n}), \
                mock.patch.object(known, "PAIRS", ((2, 4),)):
            self.assertFalse(self.tool.validation("dependency-small-second", known, None)["re_found"])
        with mock.patch.object(known, "first_full", lambda n: {"forward": 2, "inverse": 1}), \
                mock.patch.object(known, "PAIRS", ((2, 4),)):
            self.assertFalse(self.tool.validation("dependency-small-second", known, None)["re_found"])

    def test_a_first_that_should_never_fill_is_compared(self):
        known = self.known("dependency-small")
        with mock.patch.object(known, "FIRST_FULL", {"rules": 3, "chain": None}), \
                mock.patch.object(known, "PAIRS", ((2, 4),)):
            self.assertFalse(self.tool.validation("dependency-small", known, None)["re_found"])

    def test_a_key_the_tool_found_that_is_not_wanted_counts(self):
        self.assertEqual(self.tool.differences({1: 2, 3: 4}, {1: 2}), 1)
        self.assertEqual(self.tool.differences({1: 2}, {1: 2, 3: 4}), 1)
        self.assertEqual(self.tool.differences({1: 2}, {1: 2}), 0)


def degree_module():
    sys.path.insert(0, str(CODE_ROOT / "research/004"))
    sys.path.insert(0, str(CODE_ROOT / "research/004/tools"))
    import degree
    return degree


class Degree(unittest.TestCase):
    """research/004/tools/degree.py on stated functions (T056)."""

    @classmethod
    def setUpClass(cls):
        cls.tool = degree_module()
        import ir
        cls.ir = ir
        cls.a, cls.b, cls.c = ir.Lane(1), ir.Lane(2), ir.Lane(3)

    def test_a_table_reads_its_normal_form(self):
        self.assertEqual(self.tool.table_degree(np.array([0, 0, 0, 1], dtype=np.uint8), 2), 2)
        self.assertEqual(self.tool.table_degree(np.array([0, 1, 1, 0], dtype=np.uint8), 2), 1)
        self.assertEqual(self.tool.table_degree(np.array([1, 1, 1, 1], dtype=np.uint8), 2), 0)
        self.assertEqual(self.tool.table_degree(np.array([0, 0, 0, 0], dtype=np.uint8), 2), 0)
        self.assertEqual(self.tool.table_degree(np.array([0, 1, 1, 1], dtype=np.uint8), 2), 2)

    def test_the_monomials_of_a_stated_table(self):
        """x or y is x + y + xy, so that the monomials are 1, 2 and 3."""
        self.assertEqual(self.tool.anf_monomials(np.array([0, 1, 1, 1], dtype=np.uint8), 2).tolist(), [1, 2, 3])

    def test_the_table_is_left_as_it_was(self):
        """1 + x + y + xy, whose transform is not itself, unlike x or y."""
        table = np.array([1, 0, 0, 0], dtype=np.uint8)
        self.assertEqual(self.tool.anf_monomials(table, 2).tolist(), [0, 1, 2, 3])
        self.assertEqual(table.tolist(), [1, 0, 0, 0])

    def test_the_rule_on_each_operation(self):
        ir, a, b, c = self.ir, self.a, self.b, self.c
        degree = self.tool.expression_degree
        self.assertEqual(degree(a), 1)
        self.assertEqual(degree(ir.Constant(0)), 0)
        self.assertEqual(degree(ir.Not(a)), 1)
        self.assertEqual(degree(ir.Rotl(a, 3)), 1)
        self.assertEqual(degree(ir.Shl(a, 3)), 1)
        self.assertEqual(degree(ir.Shr(a, 3)), 1)
        self.assertEqual(degree(ir.Xor(a, b)), 1)
        self.assertEqual(degree(ir.And(a, b)), 2)
        self.assertEqual(degree(ir.Or(a, b)), 2)
        self.assertEqual(degree(ir.And(ir.Not(a), ir.Rotl(a, 1))), 2)
        self.assertEqual(degree(ir.And(a, ir.Or(b, c))), 3)

    def test_a_constant_adds_nothing_to_a_monomial(self):
        ir, a = self.ir, self.a
        self.assertEqual(self.tool.expression_degree(ir.And(a, ir.Constant(0))), 1)
        self.assertEqual(self.tool.expression_degree(ir.And(ir.Constant(1), ir.Constant(0))), 0)
        self.assertEqual(self.tool.expression_degree(ir.Xor(ir.Constant(1), ir.Constant(0))), 0)

    def test_the_degree_is_the_normal_forms_not_a_nested_sum(self):
        """a and (a or b) is a, and (a and b) xor (a and b) is 0."""
        ir, a, b = self.ir, self.a, self.b
        self.assertEqual(self.tool.expression_degree(ir.And(a, ir.Or(a, b))), 1)
        self.assertEqual(self.tool.expression_degree(ir.Xor(ir.And(a, b), ir.And(a, b))), 0)

    def test_not_is_read_in_the_table(self):
        """not a or a is 1, and not a and a is 0."""
        ir, a = self.ir, self.a
        self.assertEqual(self.tool.expression_degree(ir.Or(ir.Not(a), a)), 0)
        self.assertEqual(self.tool.expression_degree(ir.And(ir.Not(a), a)), 0)

    def test_one_bit_read_twice_is_one_variable(self):
        ir, a, b = self.ir, self.a, self.b
        self.assertEqual(self.tool.expression_degree(ir.And(ir.Rotl(a, 3), ir.Rotl(a, 3))), 1)
        self.assertEqual(self.tool.expression_degree(ir.And(ir.Rotl(ir.Rotl(a, 1), 2), ir.Rotl(a, 3))), 1)
        self.assertEqual(self.tool.expression_degree(ir.And(ir.Rotl(a, 3), ir.Rotl(a, 4))), 2)
        self.assertEqual(self.tool.expression_degree(ir.And(a, b)), 2)

    def test_a_rotation_above_a_function_goes_down_to_its_leaves(self):
        ir, a, b = self.ir, self.a, self.b
        moved = ir.Rotl(ir.And(a, b), 3)
        self.assertEqual(self.tool.expression_degree(ir.And(moved, ir.Rotl(a, 3))), 2)
        self.assertEqual(self.tool.expression_degree(ir.And(moved, ir.Rotl(ir.Lane(4), 3))), 3)

    def test_a_shift_is_part_of_a_leafs_name(self):
        ir, a = self.ir, self.a
        self.assertEqual(self.tool.expression_degree(ir.And(ir.Shl(a, 1), ir.Shr(a, 1))), 2)
        self.assertEqual(self.tool.expression_degree(ir.And(ir.Shl(a, 1), ir.Shl(a, 1))), 1)

    def test_a_long_xor_needs_no_table(self):
        ir = self.ir
        expr = ir.Lane(0)
        for t in range(1, 32):
            expr = ir.Xor(expr, ir.Rotl(ir.Lane(0), t))
        self.assertEqual(self.tool.expression_degree(expr), 1)

    def test_too_many_leaves_for_a_table_is_a_failure(self):
        ir = self.ir
        expr = ir.Lane(0)
        for t in range(1, 20):
            expr = ir.Xor(expr, ir.Rotl(ir.Lane(0), t))
        with self.assertRaises(ValueError):
            self.tool.expression_degree(ir.And(expr, ir.Lane(1)))

    def test_each_update(self):
        ir, a = self.ir, self.a
        degree = self.tool.update_degree
        self.assertEqual(degree(ir.Rot(0, 1), 7), 1)
        self.assertEqual(degree(ir.Mix(0, "xor", a), 7), 1)
        self.assertEqual(degree(ir.Mix(0, "xor", ir.Constant(0)), 7), 1)
        self.assertEqual(degree(ir.Mix(0, "xor", ir.And(a, self.b)), 7), 2)
        self.assertEqual(degree(ir.Mix(0, "add", a), 7), 7)
        self.assertEqual(degree(ir.Mix(0, "sub", a), 7), 7)
        self.assertEqual(degree(ir.Mix(0, "add", ir.Constant(0)), 7), 7)
        self.assertEqual(degree(ir.Mix(0, "add", ir.And(a, self.b)), 7), 14)

    def program(self, *phases, n=2, w=4):
        return self.ir.Program("p", n, w, tuple(phases))

    def test_a_phase_takes_its_largest_and_an_empty_phase_counts_one(self):
        ir, a, b = self.ir, self.a, self.b
        program = self.program(ir.Phase(0, (ir.Mix(0, "add", a), ir.Mix(2, "xor", ir.And(a, b)))),
                               ir.Phase(0, ()))
        self.assertEqual(self.tool.phase_degrees(program, 3), [3, 1])

    def test_a_round_is_the_product_of_its_phases(self):
        ir, a, b = self.ir, self.a, self.b
        program = self.program(ir.Phase(0, (ir.Mix(0, "add", a),)), ir.Phase(0, (ir.Mix(0, "xor", ir.And(a, b)),)))
        self.assertEqual(self.tool.round_degree(program, 3), 6)

    def test_the_cap_is_b_minus_1(self):
        self.assertEqual(self.tool.capped(6, 1, 31), 6)
        self.assertEqual(self.tool.capped(6, 2, 31), 31)
        self.assertEqual(self.tool.capped(6, 3, 31), 31)
        self.assertEqual(self.tool.capped(5, 2, 25), 25)
        self.assertEqual(self.tool.capped(10 ** 6, 10 ** 4, 1023), 1023)

    def test_counts_read_the_size(self):
        ir, a = self.ir, self.a
        program = self.program(ir.Phase(0, (ir.Mix(0, "add", a),)))
        self.assertEqual(self.tool.counts(program, 3, (1, 2, 3, 4)), [3, 9, 27, 31])

    def test_rounds_within_a_limit(self):
        self.assertEqual(self.tool.within([3, 9, 27], (1, 2, 3), 9), [1, 2])

    def test_the_inside_out_count(self):
        rounds = (1, 2, 3)
        self.assertEqual(self.tool.inside_out([4, 16, 31], [4, 16, 31], rounds, 20), (4, 17))
        self.assertEqual(self.tool.inside_out([4, 16, 31], [4, 16, 31], rounds, 3), None)
        self.assertEqual(self.tool.inside_out([4, 16, 31], [4, 8, 31], rounds, 16), (4, 17))
        self.assertEqual(self.tool.inside_out([4, 16, 31], [4, 16, 31], rounds, 31), (6, 32))

    def test_the_cost_is_that_of_the_larger_count(self):
        self.assertEqual(self.tool.inside_out([2, 8], [2, 8], (1, 2), 8), (4, 9))
        self.assertEqual(self.tool.inside_out([2, 8, 99], [3, 5, 99], (1, 2, 3), 8), (4, 9))
        self.assertEqual(self.tool.inside_out([2, 3, 99], [3, 8, 99], (1, 2, 3), 8), (4, 9))

    def test_the_pairs_may_come_in_any_order(self):
        self.assertEqual(self.tool.inside_out([8, 2], [8, 2], (2, 1), 8), (4, 9))

    def test_a_records_fields(self):
        ir, a = self.ir, self.a
        program = self.program(ir.Phase(0, (ir.Mix(0, "add", a),)))
        out = self.tool.record_fields(program, (1, 2), 5)
        self.assertEqual(out["phase_counts"], {"forward": [3], "inverse": [3]})
        self.assertEqual(out["counts"]["forward"], [3, 9])
        self.assertEqual(out["upper_bounds"]["forward"], [4, 16])
        self.assertEqual(out["rounds_within_limit"]["forward"], [1])
        self.assertEqual(out["rounds_with_bound_within_limit"]["inverse"], [1])
        self.assertEqual(out["inside_out"], (2, 4))
        self.assertEqual(out["marked"], "the rule's count, not an upper bound")

    def test_a_record_reads_the_inverse_in_its_own_order(self):
        ir, a = self.ir, self.a
        program = self.program(ir.Phase(0, (ir.Mix(0, "add", a),)), ir.Phase(0, (ir.Rot(0, 1),)))
        phases = self.tool.record_fields(program, (1,), 5)["phase_counts"]
        self.assertEqual(phases, {"forward": [3, 1], "inverse": [1, 3]})

    def test_lanes_group_by_what_they_read(self):
        ir = self.ir
        program = self.program(ir.Phase(0, (ir.Mix(0, "add", ir.Lane(1)),)),
                               ir.Phase(1, (ir.Rot(2, 1), ir.Mix(4, "xor", ir.Lane(5)))))
        self.assertEqual(self.tool.groups_of(program), [[0, 1], [2], [4, 5]])

    def test_the_exact_degree_of_stated_boxes(self):
        """x + y at w = 4: its top bit is degree 4, x3 + y3 + the carry of degree 3 plus one."""
        ir = self.ir
        add = self.program(ir.Phase(0, (ir.Mix(0, "add", ir.Lane(1)),)))
        self.assertEqual(self.tool.exact_degree(add, 1), 4)
        turn = self.program(ir.Phase(0, (ir.Rot(0, 1),)))
        self.assertEqual(self.tool.exact_degree(turn, 1), 1)
        both = self.program(ir.Phase(0, (ir.Mix(0, "xor", ir.And(ir.Lane(1), ir.Rotl(ir.Lane(1), 1))),)))
        self.assertEqual(self.tool.exact_degree(both, 1), 2)

    def test_the_exact_degree_runs_its_rounds(self):
        ir = self.ir
        program = self.program(ir.Phase(0, (ir.Mix(0, "xor", ir.Lane(1)),)),
                               ir.Phase(0, (ir.Mix(1, "xor", ir.And(ir.Lane(0), ir.Rotl(ir.Lane(0), 1))),)))
        self.assertEqual(self.tool.exact_degree(program, 1), 2)
        self.assertGreater(self.tool.exact_degree(program, 2), 2)

    def test_the_exact_degree_of_too_large_a_group_is_not_computed(self):
        ir = self.ir
        program = self.program(ir.Phase(0, (ir.Mix(0, "add", ir.Lane(1)),)), n=2, w=16)
        self.assertIsNone(self.tool.exact_degree(program, 1))

    def test_the_exact_degree_takes_constants_as_0(self):
        ir = self.ir
        program = self.program(ir.Phase(0, (ir.Mix(0, "add", ir.Constant(0)),)))
        self.assertEqual(self.tool.exact_degree(program, 1), 1)


class DegreeOnKnown(unittest.TestCase):
    """The tool on its known results, each deciding fact broken once."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(CODE_ROOT))
        from scripts import validate_tool
        cls.vt = validate_tool
        cls.tool = degree_module()
        cls.table = validate_tool.known_results()

    def known(self, name):
        return self.vt.load_known(self.table[name])

    def run_known(self, name, known):
        return self.tool.validation(name, known, None)["re_found"]

    def test_each_is_re_found(self):
        for name in ("degree-small", "degree-small-second"):
            self.assertTrue(self.run_known(name, self.known(name)), name)

    def test_the_exact_degree_is_reported_beside_and_under_the_bound(self):
        out = self.tool.validation("degree-small", self.known("degree-small"), None)
        rows = {(row["n"], row["w"]): row for row in out["found"]["rows"]}
        self.assertEqual(len(rows[(2, 4)]["exact_degrees"]), 3)
        self.assertEqual(len(rows[(2, 8)]["exact_degrees"]), 3)
        self.assertNotIn("exact_degrees", rows[(4, 32)])
        for key in ((2, 4), (2, 8)):
            for degree, bound in zip(rows[key]["exact_degrees"], rows[key]["upper_bounds"]["forward"]):
                self.assertLessEqual(degree, bound)

    def test_each_table_of_the_first_is_compared(self):
        for field in ("COUNTS", "BOUNDS"):
            known = self.known("degree-small")
            wrong = dict(getattr(known, field))
            wrong[(2, 4)] = (18, 31, 30)
            with mock.patch.object(known, field, wrong):
                self.assertFalse(self.run_known("degree-small", known), field)

    def test_the_inside_out_count_is_compared_both_ways(self):
        known = self.known("degree-small")
        for wrong in ({(2, 4): (2, 18), (2, 8): (2, 43), (4, 32): None},
                      {(2, 4): (1, 19), (2, 8): (2, 43), (4, 32): None},
                      {(2, 4): None, (2, 8): (2, 43), (4, 32): None},
                      {(2, 4): (2, 19), (2, 8): (2, 43), (4, 32): (2, 19)}):
            with mock.patch.object(known, "INSIDE_OUT", wrong):
                self.assertFalse(self.run_known("degree-small", known), wrong)

    def test_a_bound_under_the_exact_degree_breaks_it(self):
        known = self.known("degree-small")
        with mock.patch.object(self.tool, "exact_degree", return_value=10 ** 6):
            self.assertFalse(self.run_known("degree-small", known))

    def test_each_case_of_the_second_is_compared(self):
        name = "degree-small-second"
        for field, value in (("counts", (4, 16, 31, 30)), ("bounds", (4, 16, 31, 30)),
                             ("inside_out", (4, 16))):
            known = self.known(name)
            label, builder, n, w, entry = known.CASES[0]
            with mock.patch.object(known, "CASES", ((label, builder, n, w, dict(entry, **{field: value})),)):
                self.assertFalse(self.run_known(name, known), field)

    def test_each_direction_of_the_count_is_compared(self):
        name = "degree-small"
        known = self.known(name)
        real = self.tool.record_fields
        for direction in ("forward", "inverse"):
            def changed(program, rounds, limit=126):
                out = real(program, rounds, limit)
                out["counts"] = dict(out["counts"], **{direction: [1] * len(rounds)})
                return out

            with mock.patch.object(self.tool, "record_fields", changed):
                self.assertFalse(self.run_known(name, known), direction)

    def test_one_wrong_case_of_the_second_is_enough(self):
        name = "degree-small-second"
        known = self.known(name)
        label, builder, n, w, entry = known.CASES[0]
        cases = ((label, builder, n, w, dict(entry, counts=(1, 1, 1, 1))),) + known.CASES[1:]
        with mock.patch.object(known, "CASES", cases):
            self.assertFalse(self.run_known(name, known))

    def test_the_limit_of_the_second_is_read(self):
        name = "degree-small-second"
        known = self.known(name)
        label, builder, n, w, entry = known.CASES[0]
        with mock.patch.object(known, "CASES", ((label, builder, n, w, dict(entry, limit=3)),)):
            self.assertFalse(self.run_known(name, known))

    def test_a_bound_under_the_exact_degree_breaks_the_second_only_at_small_widths(self):
        name = "degree-small-second"
        known = self.known(name)
        small = tuple(c for c in known.CASES if c[3] == 4)
        with mock.patch.object(self.tool, "exact_degree", return_value=10 ** 6), \
                mock.patch.object(known, "CASES", small):
            self.assertFalse(self.run_known(name, known))
        large = tuple(c for c in known.CASES if c[3] == 32)
        with mock.patch.object(self.tool, "exact_degree", return_value=10 ** 6), \
                mock.patch.object(known, "CASES", large):
            self.assertTrue(self.run_known(name, known))


def bijectivity_module():
    sys.path.insert(0, str(CODE_ROOT / "research/004"))
    sys.path.insert(0, str(CODE_ROOT / "research/004/tools"))
    import bijectivity
    return bijectivity


class Bijectivity(unittest.TestCase):
    """research/004/tools/bijectivity.py at a size a test can sweep (T057). The 2^32 inputs are the
    validation's own, a heavy run."""

    @classmethod
    def setUpClass(cls):
        cls.tool = bijectivity_module()
        import ir
        cls.ir = ir

    def test_packing_is_lane_by_lane(self):
        words = np.array([0x87654321], dtype=np.uint64)
        lanes = self.tool.unpack(words)
        self.assertEqual(lanes[:, 0].tolist(), [1, 2, 3, 4, 5, 6, 7, 8])
        self.assertEqual(int(self.tool.pack(lanes)[0]), 0x87654321)

    def test_packing_at_another_shape(self):
        lanes = self.tool.unpack(np.array([0xAB], dtype=np.uint64), lanes=2, w=4)
        self.assertEqual(lanes[:, 0].tolist(), [0xB, 0xA])
        self.assertEqual(int(self.tool.pack(lanes, 4)[0]), 0xAB)

    def test_a_permutation_fills_the_bitmap(self):
        out = self.tool.sweep(lambda s: s[::-1], lanes=2, w=4, batch=7)
        self.assertEqual((out["inputs"], out["ones"]), (256, 256))
        self.assertTrue(self.tool.passes(out))

    def test_a_map_with_collisions_leaves_it_short(self):
        """x and y, with y kept: the sum over y of 2^popcount(y), 3^4 = 81."""
        def step(states):
            out = states.copy()
            out[0] = states[0] & states[1]
            return out

        out = self.tool.sweep(step, lanes=2, w=4, batch=16)
        self.assertEqual(out["ones"], 81)
        self.assertFalse(self.tool.passes(out))

    def test_the_batch_size_changes_nothing(self):
        def step(states):
            out = states.copy()
            out[0] = states[0] | states[1]
            return out

        results = [self.tool.sweep(step, lanes=2, w=4, batch=b) for b in (1, 7, 16, 255, 256, 1000)]
        self.assertEqual(len({(r["ones"], r["bitmap_sha256"]) for r in results}), 1)

    def test_the_hash_is_of_the_bitmap(self):
        """A map to the output 0 alone: one bit set, the lowest of 32 bytes."""
        out = self.tool.sweep(lambda s: np.zeros_like(s), lanes=2, w=4, batch=16)
        self.assertEqual(out["ones"], 1)
        self.assertEqual(out["bitmap_sha256"], evidence.sha256(b"\x01" + bytes(31)))

    def test_a_high_output_lands_in_the_last_byte(self):
        out = self.tool.sweep(lambda s: np.full_like(s, 15), lanes=2, w=4, batch=16)
        self.assertEqual(out["bitmap_sha256"], evidence.sha256(bytes(31) + b"\x80"))

    def small_known(self, permutation_ones=256, collision_ones=81):
        ir = self.ir
        module = mock.Mock()
        module.ROUNDS = 2
        module.PERMUTATION_ONES = permutation_ones
        module.COLLISION_ONES = collision_ones
        module.permutation.return_value = ir.Program("r", 2, 4, (ir.Phase(0, (ir.Rot(0, 1),)),))

        def collisions(states):
            out = states.copy()
            out[0] = states[0] & states[1]
            return out

        module.collisions = collisions
        return module

    def run_small(self, known):
        real = self.tool.sweep
        def narrow(step, **_):
            def widened(states):
                full = np.zeros((8, states.shape[1]), dtype=np.uint64)
                full[:2] = states
                return step(full)[:2]
            return real(widened, lanes=2, w=4, batch=16)
        with mock.patch.object(self.tool, "sweep", narrow):
            return self.tool.validation("bijectivity-maps", known, None)

    def test_each_count_is_compared_exactly(self):
        self.assertTrue(self.run_small(self.small_known())["re_found"])
        self.assertFalse(self.run_small(self.small_known(permutation_ones=255))["re_found"])
        self.assertFalse(self.run_small(self.small_known(collision_ones=82))["re_found"])

    def test_the_list_runs_its_stated_rounds(self):
        ir = self.ir
        known = self.small_known()
        loaded = ir.load(known.permutation())
        states = np.zeros((8, 1), dtype=np.uint64)
        states[0, 0] = 1
        self.assertEqual(int(self.tool.steps_of(known)["permutation"](states)[0, 0]),
                         int(ir.permute_batch(loaded, states, rounds=2)[0, 0]))

    def test_each_known_result_is_a_heavy_run(self):
        self.assertEqual(set(self.tool.HEAVY), {"bijectivity-maps", "bijectivity-maps-second"})

    def test_a_probe_times_both_maps_and_reads_the_whole_sweep(self):
        with mock.patch.object(self.tool, "time_batches", side_effect=[1.0, 3.0]):
            hours, speed = self.tool.projection("bijectivity-maps")
        self.assertAlmostEqual(hours, 4.0 * (2 ** 32 / 2 ** 22) / 3600.0)
        self.assertEqual(speed["seconds_per_batch"], {"permutation": 1.0, "collisions": 3.0})

    def test_a_probe_gives_seconds_per_batch(self):
        with mock.patch.object(self.tool, "BATCH", 16), \
                mock.patch.object(self.tool.time, "monotonic", side_effect=[10.0, 18.0]):
            self.assertEqual(self.tool.time_batches(lambda s: s, 2), 4.0)

    def test_a_probe_batch_is_timed_on_the_real_map(self):
        calls = []

        def step(states):
            calls.append(states.shape)
            return states

        with mock.patch.object(self.tool, "BATCH", 1024):
            self.assertGreaterEqual(self.tool.time_batches(step, 2), 0.0)
        self.assertEqual(calls, [(8, 1024), (8, 1024)])


def avalanche_module():
    sys.path.insert(0, str(CODE_ROOT / "research/004"))
    sys.path.insert(0, str(CODE_ROOT / "research/004/tools"))
    import avalanche
    return avalanche


class Avalanche(unittest.TestCase):
    """research/004/tools/avalanche.py on stated lists (T058)."""

    @classmethod
    def setUpClass(cls):
        cls.tool = avalanche_module()
        import dependency
        import ir
        cls.ir, cls.dep = ir, dependency

    def test_the_flip_set_of_each_size(self):
        self.assertEqual(len(self.tool.flip_set(4)), 1024)
        self.assertEqual(len(self.tool.flip_set(8)), 512)
        self.assertEqual(len(self.tool.flip_set(16)), 1024)
        self.assertEqual(self.tool.flip_set(4), list(range(1024)))
        node = self.ir.lane(8, 3, 3, 1) * 32 + 5
        self.assertIn(node, self.tool.flip_set(8))
        self.assertNotIn(self.ir.lane(8, 3, 4, 0) * 32, self.tool.flip_set(8))

    def test_s_a_is_r4s(self):
        self.assertEqual(self.tool.s_a(4), 2494 * 1024)
        self.assertEqual(self.tool.s_a(8), 1470 * 4096)
        self.assertEqual(self.tool.s_a(16), 2494 * 16384)

    def test_a_flip_touches_one_bit(self):
        states = np.zeros((4, 2), dtype=np.uint64)
        out = self.tool.flipped(states, 2 * 8 + 3, 8)
        self.assertEqual(out[2].tolist(), [8, 8])
        self.assertEqual(int(out.sum()), 16)
        self.assertEqual(int(states.sum()), 0)

    def test_a_rotation_of_every_word(self):
        states = np.array([[0x81], [0x01]], dtype=np.uint64)
        self.assertEqual(self.tool.rotated(states, 1, 8).tolist(), [[0x03], [0x02]])

    def rot_list(self, amount=1):
        return self.ir.load(self.ir.Program("r", 2, 8, (self.ir.Phase(0, (self.ir.Rot(0, amount),)),)))

    def test_difference_counts_follow_each_round(self):
        loaded = self.rot_list()
        first = np.zeros((8, 4), dtype=np.uint64)
        second = self.tool.flipped(first, 0, 8)
        base = self.tool.trajectory(loaded, first, [None] * 3)
        early, out = self.tool.difference_counts(loaded, base, second, [None] * 3, 8)
        for r in range(3):
            self.assertEqual(out[r, 0].tolist(), [4 if b == r + 1 else 0 for b in range(8)])
        self.assertTrue((early == out).all(), "no state lies past the first 2^13")

    def test_the_two_counts_part_at_the_first_2_13_states(self):
        difference = np.array([[1, 1, 0, 1, 1]], dtype=np.uint64)
        with mock.patch.object(self.tool, "N_FIRST", 2):
            early, whole = self.tool.two_counts(difference, 2)
        self.assertEqual((int(early[0, 0]), int(whole[0, 0])), (2, 4))

    def test_the_counts_of_a_run_part_there_too(self):
        loaded = self.rot_list()
        first = np.zeros((8, 6), dtype=np.uint64)
        second = first.copy()
        second[0, :] = 1
        second[0, 4:] = 2
        with mock.patch.object(self.tool, "N_FIRST", 4):
            base = self.tool.trajectory(loaded, first, [None])
            early, whole = self.tool.difference_counts(loaded, base, second, [None], 8)
        self.assertEqual(early[0, 0].tolist()[:3], [0, 4, 0])
        self.assertEqual(whole[0, 0].tolist()[:3], [0, 4, 2])

    def test_a_trajectory_holds_each_round_and_leaves_its_input(self):
        loaded = self.rot_list()
        states = np.zeros((8, 4), dtype=np.uint64)
        states[0, :] = 1
        kept = states.copy()
        out = self.tool.trajectory(loaded, states, [None] * 3)
        self.assertEqual([int(step[0, 0]) for step in out], [2, 4, 8])
        self.assertTrue((states == kept).all())

    def test_the_projection_times_a_record(self):
        hours, detail = self.tool.projection("avalanche-planted-n4")
        self.assertEqual(detail["flips"], 2494)
        self.assertGreater(hours * 3600, detail["seconds_per_flip"] * 2494)
        self.assertLess(hours, 1)

    def test_rotational_counts_of_a_lane_that_commutes_are_0(self):
        states = np.array([[0x1D, 0x2B]] * 8, dtype=np.uint64)
        early, out = self.tool.rotational_counts(self.rot_list(3), states, 2, [None] * 2, 8)
        self.assertEqual((int(early.sum()), int(out.sum())), (0, 0))

    def test_rotational_counts_of_a_list_that_does_not_commute(self):
        loaded = self.ir.load(self.ir.Program("a", 2, 8, (self.ir.Phase(0, (
            self.ir.Mix(0, "add", self.ir.Lane(1)),)),)))
        states = np.full((8, 1), 0xFF, dtype=np.uint64)
        states[1, 0] = 1
        early, out = self.tool.rotational_counts(loaded, states, 1, [None], 8)
        self.assertGreater(int(out[0, 0].sum()), 0)
        self.assertTrue((early == out).all())

    def test_the_rotational_counts_part_there_too(self):
        loaded = self.ir.load(self.ir.Program("a", 2, 8, (self.ir.Phase(0, (
            self.ir.Mix(0, "add", self.ir.Lane(1)),)),)))
        states = np.full((8, 3), 0xFF, dtype=np.uint64)
        states[1, 0] = 0
        states[1, 1:] = 1
        with mock.patch.object(self.tool, "N_FIRST", 1):
            early, whole = self.tool.rotational_counts(loaded, states, 1, [None], 8)
        self.assertEqual(int(early.sum()), 0, "state 0 commutes: adding 0")
        self.assertGreater(int(whole.sum()), 0)

    def test_a_mask_of_lanes(self):
        mask = self.tool.lanes_mask([1], (3, 2))
        self.assertEqual(mask.tolist(), [[False, False], [True, True], [False, False]])

    def tally(self):
        return self.tool.Tally("p", 2, {"low": 1, "high": 9}, {"low": 1, "high": 9})

    def test_a_tally_counts_a_missed_bit_and_an_other_firing(self):
        tally = self.tally()
        counts = np.array([[0, 5, 10], [5, 5, 5]])
        expected = np.array([[True, True, False], [False, False, False]])
        tally.add("t", 0, counts, counts, expected)
        self.assertEqual(tally.missed, 1)
        self.assertEqual(tally.other_by_round, [1, 0])
        self.assertEqual(tally.lines, ["p t round 1 lane 0 bit 2 counts 10 10\n"])
        self.assertFalse(tally.summary()["holds"], "a missed bit")

    def test_a_bit_fires_on_either_count(self):
        first, whole = {"low": 1, "high": 9}, {"low": 10, "high": 90}
        for early, later, fires in ((5, 50, False), (9, 50, True), (5, 90, True), (0, 50, True), (5, 10, True)):
            tally = self.tool.Tally("p", 1, first, whole)
            tally.add("t", 0, np.array([[early]]), np.array([[later]]), np.array([[False]]))
            self.assertEqual(tally.other_by_round, [1 if fires else 0], (early, later))

    def test_another_firing_below_r_decides_nothing(self):
        tally = self.tally()
        tally.add("t", 0, np.array([[10]]), np.array([[10]]), np.array([[False]]))
        tally.add("t", 1, np.array([[5]]), np.array([[5]]), np.array([[False]]))
        self.assertTrue(tally.summary()["holds"])
        self.assertEqual(tally.summary()["other_firings_by_round"], [1, 0])

    def test_another_firing_at_r_decides(self):
        tally = self.tally()
        tally.add("t", 1, np.array([[10]]), np.array([[10]]), np.array([[False]]))
        summary = tally.summary()
        self.assertFalse(summary["holds"])
        self.assertEqual(summary["other_firings_at_r"], 1)

    def test_a_flip_of_a_bit_the_matrices_show_independent_is_a_tool_defect(self):
        with self.assertRaises(ToolFailureClass()):
            self.tool.cross_check(np.array([[0, 1]]), np.array([[True, True]]), "t")
        self.tool.cross_check(np.array([[0, 1]]), np.array([[True, False]]), "t")

    def run_one(self, program, numbers, planted=()):
        loaded = self.ir.load(program)
        rounds = 2
        states = np.zeros((2 * program.n ** 2, 16), dtype=np.uint64)
        rows = {"forward": [None] * rounds, "inverse": [None] * rounds}
        tally = self.tool.Tally("p", rounds, {"low": 0, "high": 16}, {"low": 0, "high": 16})
        matrices = self.tool.matrices_of(program, rounds, ("forward", "inverse"))
        self.tool.run_flips(loaded, states, numbers, rows, matrices, lambda lane: planted, tally,
                            ("forward", "inverse"))
        return tally

    def test_a_list_of_one_rotation_fires_exactly_its_expected_set(self):
        """Each output bit either depends on the flip and always flips, or depends on nothing of it."""
        program = self.ir.Program("r", 2, 8, (self.ir.Phase(0, (self.ir.Rot(0, 1),)),))
        tally = self.run_one(program, [3])
        self.assertEqual(tally.tests, 4)
        self.assertEqual(tally.missed, 0)
        self.assertEqual(tally.other_by_round, [2, 2], "the flipped bit itself, once per direction")

    def test_a_flip_where_the_matrices_show_none_stops_the_run(self):
        """The list rotates, and matrices of a list that does not say the bit moved."""
        program = self.ir.Program("r", 2, 8, (self.ir.Phase(0, (self.ir.Rot(0, 1),)),))
        loaded = self.ir.load(program)
        states = np.zeros((8, 16), dtype=np.uint64)
        tally = self.tool.Tally("p", 1, {"low": 0, "high": 16}, {"low": 0, "high": 16})
        still = {"forward": [self.dep.identity(2, 8)]}
        with self.assertRaises(ToolFailureClass()):
            self.tool.run_flips(loaded, states, [3], {"forward": [None]}, still, lambda lane: (), tally,
                                ("forward",))

    def test_a_flip_past_the_first_states_stops_the_run_too(self):
        """The cross-check reads the count over every state, so that no later state escapes it."""
        program = self.ir.Program("r", 2, 8, (self.ir.Phase(0, (self.ir.Rot(0, 1),)),))
        loaded = self.ir.load(program)
        states = np.zeros((8, 16), dtype=np.uint64)
        tally = self.tool.Tally("p", 1, {"low": 0, "high": 16}, {"low": 0, "high": 16})
        still = {"forward": [self.dep.identity(2, 8)]}
        with mock.patch.object(self.tool, "N_FIRST", 0), self.assertRaises(ToolFailureClass()):
            self.tool.run_flips(loaded, states, [3], {"forward": [None]}, still, lambda lane: (), tally,
                                ("forward",))

    def test_every_rotation_is_run_both_ways(self):
        program = self.ir.Program("r", 2, 8, (self.ir.Phase(0, (self.ir.Rot(0, 1),)),))
        loaded = self.ir.load(program)
        states = np.zeros((8, 4), dtype=np.uint64)
        tally = self.tool.Tally("p", 1, {"low": 0, "high": 4}, {"low": 0, "high": 4})
        self.tool.run_rotations(loaded, states, (0,), tally, {"forward": [None], "inverse": [None]})
        self.assertEqual(tally.tests, 7 * 2)

    def test_a_planted_lane_that_flips_half_the_time_is_missed(self):
        program = self.ir.Program("x", 2, 8, (self.ir.Phase(0, (
            self.ir.Mix(0, "xor", self.ir.Lane(1)),)),))
        loaded = self.ir.load(program)
        states = np.zeros((8, 16), dtype=np.uint64)
        states[0, ::2] = 0
        matrices = self.tool.matrices_of(program, 1, ("forward",))
        base = self.tool.trajectory(loaded, states, [None])
        _, out = self.tool.difference_counts(loaded, base, self.tool.flipped(states, 8, 8), [None], 8)
        self.assertEqual(int(out[0, 0, 0]), 16)
        rows = {"forward": [None]}
        half = {"low": 0, "high": 17}
        tally = self.tool.Tally("p", 1, half, half)
        self.tool.run_flips(loaded, states, [8], rows, matrices, lambda lane: (0,), tally, ("forward",))
        self.assertGreater(tally.missed, 0, "lane 0 is planted, and bit 0 of it flips every time")

    def test_the_matrices_are_read_per_direction_and_round(self):
        program = self.ir.Program("x", 2, 8, (
            self.ir.Phase(0, (self.ir.Rot(1, 1),)),
            self.ir.Phase(0, (self.ir.Mix(0, "xor", self.ir.Lane(1)),))))
        out = self.tool.matrices_of(program, 3, ("forward", "inverse"))
        self.assertEqual(sorted(out), ["forward", "inverse"])
        self.assertEqual(len(out["forward"]), 3)
        self.assertFalse((out["forward"][0] == out["inverse"][0]).all())

    def test_a_key_is_read_as_big_endian_words(self):
        self.assertEqual(self.tool.words_of(bytes([1, 2, 3, 4, 5, 6, 7, 8])), [0x01020304, 0x05060708])

    def test_the_verdict_code_fires_exactly_at_the_critical_values(self):
        entry = {"n": 100, "low": 30, "high": 70}
        self.assertTrue(self.tool.verdict_code(entry)["holds"])
        self.assertEqual(self.tool.verdict_code(entry)["counts"], 101)
        with mock.patch.object(self.tool.bias, "fires", lambda counts, e: counts <= e["low"]):
            self.assertFalse(self.tool.verdict_code(entry)["holds"])

    def test_power_is_exact_on_a_stated_row(self):
        """n = 4, p = 3/4: firing at 0 or 4 is (1/4)^4 + (3/4)^4 = 82/256."""
        entry = {"n": 4, "low": 0, "high": 4}
        self.assertEqual(self.tool.power(entry, Fraction(1, 4)), Fraction(82, 256))

    def test_power_at_no_bias_is_the_tails(self):
        entry = {"n": 10, "low": 1, "high": 9}
        self.assertEqual(self.tool.power(entry, Fraction(0)), Fraction(22, 1024))

    def test_the_power_at_r4s_stated_biases_exactly(self):
        """At N_a = 2^13 the stated biases, rounded to four places, give 0.8985, 0.9007 and 0.8987, which
        is why N_a rose: at 8,256 they give 0.9047, 0.9070 and 0.9054 (FR-044; the change log)."""
        table = self.tool.bias.read_table()
        for n, was, now in ((4, 0.898546, 0.90471), (8, 0.900737, 0.90699), (16, 0.898723, 0.90541)):
            entry = self.tool.bias.entry_for("avalanche", 2 ** 13, self.tool.s_a(n), table)
            self.assertAlmostEqual(float(self.tool.power(entry, self.tool.DELTA_A[n])), was, places=5)
            entry = self.tool.bias.entry_for("avalanche", 8256, self.tool.s_a(n), table)
            value = self.tool.power(entry, self.tool.DELTA_A[n])
            self.assertAlmostEqual(float(value), now, places=4)
            self.assertGreaterEqual(value, self.tool.LEAST_POWER)

    def test_the_size_of_a_known_result(self):
        self.assertEqual(self.tool.size_of("avalanche-planted-n16"), 16)
        self.assertEqual(self.tool.size_of("avalanche-planted-second-n8"), 8)

    def test_each_size_is_a_known_result_of_its_own_with_its_own_second(self):
        sys.path.insert(0, str(CODE_ROOT))
        from scripts import validate_tool
        table = validate_tool.known_results()
        self.assertEqual(table["avalanche-planted-second-n8"].second_of, "avalanche-planted-n8")
        self.assertEqual(table["avalanche-planted-n8"].second_of, NONE)
        self.assertEqual(table["avalanche-planted-n8"].path, table["avalanche-planted-n4"].path)
        self.assertNotIn("avalanche-planted", table)
        self.assertEqual([k.known_id for k in validate_tool.seconds_of(table, "avalanche-planted-n16")],
                         ["avalanche-planted-second-n16"])

    def test_the_input_bits_are_found_from_the_loader(self):
        sys.path.insert(0, str(CODE_ROOT))
        from scripts import validate_tool
        table = validate_tool.known_results()
        known = validate_tool.load_known(table["avalanche-planted-n4"])
        bits = self.tool.input_bits(known, 4)
        self.assertEqual(len(bits), 384)
        self.assertEqual(len(set(bits)), 384)
        self.assertEqual(bits[0], self.ir.lane(4, 0, 0, 0) * 32)
        self.assertEqual(bits[7 * 32], self.ir.lane(4, 2, 2, 0) * 32)
        self.assertEqual(bits[8 * 32], self.ir.lane(4, 0, 0, 1) * 32)
        self.assertEqual(bits[11 * 32 + 31], self.ir.lane(4, 2, 2, 1) * 32 + 31)


def ToolFailureClass():
    return evidence.ToolFailure


class AvalancheStem(unittest.TestCase):
    """A shortened run of each path on the stated stem, each deciding fact broken once."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(CODE_ROOT))
        from scripts import validate_tool
        cls.vt = validate_tool
        cls.tool = avalanche_module()
        cls.table = validate_tool.known_results()

    def setUp(self):
        self.known = self.vt.load_known(self.table["avalanche-planted-n4"])
        self.kept = {}

    def run_known(self, least_power=Fraction(9, 10), **changes):
        tool = self.tool
        sample = {"flip_set": lambda n, w=32: [0, 511, tool.ir.lane(4, 1, 1, 1) * 32 + 3] if n == 4 else [],
                  "input_bits": lambda known, n: [0, 7 * 32, 8 * 32, 11 * 32 + 31]}
        sample.update(changes)
        with mock.patch.object(tool, "flip_set", sample["flip_set"]), \
                mock.patch.object(tool, "input_bits", sample["input_bits"]), \
                mock.patch.object(tool, "s_a", lambda n, w=32: 2494 * 1024), \
                mock.patch.object(tool, "LEAST_POWER", least_power):
            return tool.re_find(self.known, 4, self.kept.__setitem__)

    def test_a_sample_of_each_path_holds(self):
        with mock.patch.object(self.tool, "run_rotations", wraps=self.few_rotations):
            out = self.run_known()
        for path in out["found"]["paths"]:
            self.assertTrue(path["holds"], path["path"])
        self.assertTrue(out["re_found"])
        self.assertIn("other-firings-n4.txt", self.kept)
        self.assertTrue(self.kept["other-firings-n4.txt"])

    def test_the_record_states_both_counts_and_the_chance_of_both(self):
        with mock.patch.object(self.tool, "run_rotations", wraps=self.few_rotations):
            found = self.run_known()["found"]
        self.assertEqual(found["critical"], {"over the first 2^13": [3790, 4402], "over N_a": [3821, 4435]})
        entry = self.tool.bias.entry_for("avalanche", 8256, 2494 * 1024)
        threshold = Fraction(entry["level_numerator"], entry["level_denominator"])
        self.assertEqual(found["chance_of_a_false_firing_per_flipped_bit_at_most"], float(2 * threshold * 1024))

    def few_rotations(self, loaded, states, planted, tally, rows):
        w = 32
        mask = self.tool.lanes_mask(planted, (states.shape[0], w))
        for k in (1, 16):
            early, whole = self.tool.rotational_counts(loaded, states, k, rows["forward"], w)
            for r in range(whole.shape[0]):
                tally.add(f"k {k}", r, early[r], whole[r], mask)

    def test_a_lane_said_to_be_planted_that_is_not_breaks_the_flip_path(self):
        with mock.patch.object(self.tool, "run_rotations", wraps=self.few_rotations), \
                mock.patch.object(self.known, "planted_bits", lambda path, n, lane=None: (0,)):
            self.assertFalse(self.run_known()["re_found"])

    def test_a_failed_verdict_code_or_power_breaks_it(self):
        with mock.patch.object(self.tool, "run_rotations", wraps=self.few_rotations), \
                mock.patch.object(self.tool, "verdict_code", side_effect=[{"holds": True}, {"holds": False}]):
            self.assertFalse(self.run_known()["re_found"], "the count over N_a")
        with mock.patch.object(self.tool, "run_rotations", wraps=self.few_rotations), \
                mock.patch.object(self.tool, "verdict_code", side_effect=[{"holds": False}, {"holds": True}]):
            self.assertFalse(self.run_known()["re_found"], "the count over 2^13")
        with mock.patch.object(self.tool, "run_rotations", wraps=self.few_rotations), \
                mock.patch.object(self.tool, "LEAST_POWER", Fraction(1, 2)):
            self.assertFalse(self.run_known(least_power=Fraction(91, 100))["re_found"],
                             "at N_a = 8,256 the power at 4x4 is 0.9047")

    def test_the_inputs_name_the_three_kinds(self):
        kinds = [item["kind"] for item in self.tool.inputs("avalanche-planted-n4")["sets"]]
        self.assertEqual(kinds, ["state", "key", "nonce"])

    def test_the_larger_sizes_are_heavy(self):
        self.assertNotIn("avalanche-planted-n4", self.tool.HEAVY)
        self.assertIn("avalanche-planted-n16", self.tool.HEAVY)
        self.assertIn("avalanche-planted-second-n8", self.tool.HEAVY)


class FutSec8Known(unittest.TestCase):
    """research/004/tools/fut_sec8_known.py, on the reviewed demonstration record (T052)."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(CODE_ROOT / "research/004/tools"))
        import fut_sec8_known
        cls.known = fut_sec8_known
        cls.path, cls.record = evidence.latest_demonstration()

    def result(self, **changes):
        record = json.loads(json.dumps(self.record))
        record.update(changes)
        with mock.patch.object(evidence, "latest_demonstration", return_value=(self.path, record)):
            return self.known.validation("fut-sec-8", None, None)

    def test_the_reviewed_record_is_re_found(self):
        out = self.result()
        self.assertTrue(out["re_found"])
        self.assertEqual(out["found"]["record_id"], self.record["record_id"])
        self.assertEqual(out["found"]["sha256"], evidence.sha256(self.path.read_bytes()))

    def test_each_seed_must_be_the_first_three_of_dev(self):
        self.assertFalse(self.result(targets=self.record["targets"][:2])["re_found"])
        self.assertFalse(self.result(targets=[[1, 2, 3, 4]] + self.record["targets"][1:])["re_found"])

    def test_each_seed_must_be_recovered(self):
        self.assertFalse(self.result(recovered=[True, True, False])["re_found"])
        self.assertFalse(self.result(recovered=[True, True])["re_found"])

    def test_every_vector_file_must_match(self):
        checked = json.loads(json.dumps(self.record["vector_check"]))
        checked[-1]["mismatches"] = 1
        self.assertFalse(self.result(vector_check=checked)["re_found"])
        self.assertFalse(self.result(vector_check=[])["re_found"])
        empty = json.loads(json.dumps(self.record["vector_check"]))
        empty[0]["words"] = 0
        self.assertFalse(self.result(vector_check=empty)["re_found"])

    def test_the_record_must_be_of_the_tool_under_validation(self):
        for field in ("source_sha256", "binary_sha256"):
            tool = dict(self.record["tool"], **{field: "0" * 64})
            self.assertFalse(self.result(tool=tool)["re_found"], field)

    def test_a_record_the_review_does_not_name_is_refused(self):
        with mock.patch.object(evidence, "family_row", return_value=None):
            with self.assertRaises(evidence.Refused):
                self.known.validation("fut-sec-8", None, None)

    def test_it_has_no_second_so_a_failure_leaves_it_unvalidated(self):
        sys.path.insert(0, str(CODE_ROOT))
        from scripts import validate_tool
        table = validate_tool.known_results()
        self.assertEqual(validate_tool.seconds_of(table, "fut-sec-8"), [])
        with self.assertRaisesRegex(evidence.Refused, "stays unvalidated"):
            validate_tool.targets_after({"record_id": "x"}, validate_tool.TOOLS["fut_sec8"], table)


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
    for name in ("avalanche-planted-n4", "avalanche-planted-second-n4"):
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


def two_sided_p_at(n: int, c: int) -> Fraction:
    """Twice P(X <= c), X binomial(n, 1/2), at most 1, exactly: one minus the middle of the row."""
    middle = sum(math.comb(n, k) for k in range(c + 1, n - c))
    return min(Fraction(1), 1 - Fraction(middle, 2 ** n))


def bias_module():
    sys.path.insert(0, str(CODE_ROOT / "research/004"))
    sys.path.insert(0, str(CODE_ROOT / "research/004/tools"))
    import bias
    return bias


class CriticalCounts(unittest.TestCase):
    """research/004/tools/critical_counts.json: code, appended to and never changed (R4)."""

    REL = "research/004/tools/critical_counts.json"

    def setUp(self):
        if not (CODE_ROOT / self.REL).exists():
            self.skipTest("the table does not exist yet (T051)")
        self.table = json.loads((CODE_ROOT / self.REL).read_text(encoding="utf-8"))
        self.bias = bias_module()

    def test_every_count_is_exactly_where_the_level_falls(self):
        """Recomputed by the definition: the level is met at `low`, and not one step inside it."""
        for entry in self.table["entries"]:
            n, low = entry["n"], entry["low"]
            level = Fraction(entry["level_numerator"], entry["level_denominator"])
            self.assertEqual(entry["high"], n - low, entry)
            self.assertFalse(self.above(n, low, level), entry)
            self.assertTrue(self.above(n, low + 1, level), entry)

    def above(self, n: int, c: int, level: Fraction) -> bool:
        """Whether the two-sided p-value at c lies above the level: the middle of the row by its own
        recurrence from the centre, compared by cross-multiplying, so that n = 2^20 is quick."""
        k = n // 2
        term = self.bias.central_binomial(n)
        middle = term
        while k - 1 > c:
            term = term * k // (n - k + 1)
            k -= 1
            middle += 2 * term
        return ((1 << n) - middle) * level.denominator > level.numerator << n

    def test_the_tool_derives_the_committed_table(self):
        self.assertEqual(self.bias.table_entries(), self.table["entries"][:10])

    def test_each_level_is_the_rule_of_r4(self):
        for entry in self.table["entries"]:
            level = Fraction(entry["level_numerator"], entry["level_denominator"])
            if entry["test"] == "avalanche":
                self.assertEqual(level, Fraction(5, 1000) / (128 * entry["s"]), entry)
            else:
                self.assertEqual(level, Fraction(5, 1000) / entry["s"], entry)

    def test_the_table_holds_every_size_of_r4(self):
        pairs = {(e["test"], e["n"], e["s"]) for e in self.table["entries"]}
        for size, flips in ((4, 1024), (8, 512), (16, 1024)):
            b = 64 * size * size
            self.assertIn(("frequency", 2 ** 20, 4 * b), pairs)
            self.assertIn(("avalanche", 2 ** 13, (2 * flips + 384 + 62) * b), pairs)
            self.assertIn(("avalanche", 8256, (2 * flips + 384 + 62) * b), pairs)

    def test_the_file_is_only_appended_to(self):
        log = evidence.git("log", "--format=%H", "--", self.REL, cwd=CODE_ROOT).decode().split()
        newer: Optional[List] = None
        for commit in log:
            blob = evidence.git("show", f"{commit}:{self.REL}", cwd=CODE_ROOT)
            older = json.loads(blob.decode("utf-8"))["entries"]
            if newer is not None:
                self.assertEqual(newer[:len(older)], older, commit)
            newer = older
        current = self.table["entries"]
        if newer is not None:
            self.assertEqual(current[:len(newer)], newer)


class Bias(unittest.TestCase):
    """research/004/tools/bias.py on stated counts."""

    @classmethod
    def setUpClass(cls):
        cls.bias = bias_module()
        import ir
        cls.ir = ir

    def test_the_central_coefficient_is_math_combs_at_small_n(self):
        self.bias.central_binomial.cache_clear()
        for n in (2, 4, 6, 10, 100, 1000, 4096, 8192):
            self.assertEqual(self.bias.central_binomial(n), math.comb(n, n // 2), n)

    def test_the_central_coefficient_at_the_test_sizes_by_lucas_theorem(self):
        """C(n, k) modulo a prime p is the product of C(n_i, k_i) over the digits of n and k in base
        p: a check that shares nothing with how the integer was built."""
        def lucas(n, k, p):
            out = 1
            while n or k:
                n, n_digit = divmod(n, p)
                k, k_digit = divmod(k, p)
                out = out * math.comb(n_digit, k_digit) % p
            return out

        primes = {2 ** 20: (19, 47, 71, 73, 103, 157, 241, 269, 293, 313),
                  2400000: (61, 71, 73, 103, 139, 173, 199, 223, 227, 233)}
        for n, chosen in primes.items():
            value = self.bias.central_binomial(n)
            for p in chosen:
                self.assertEqual(value % p, lucas(n, n // 2, p), (n, p))
                self.assertNotEqual(value % p, 0, "a residue of 0 would show nothing")
            self.assertEqual(value.bit_length(), n - int(0.5 * math.log2(math.pi * n / 2)), n)

    def test_critical_counts_meet_the_definition(self):
        for n, level in ((10, Fraction(1, 10)), (100, Fraction(1, 1000)), (1000, Fraction(1, 10 ** 6))):
            low, high = self.bias.critical(n, level)
            self.assertEqual(high, n - low)
            self.assertLessEqual(two_sided_p_at(n, low), level)
            self.assertGreater(two_sided_p_at(n, low + 1), level)

    def test_a_stated_critical_count(self):
        """C(10, 0) + C(10, 1) = 11, so twice the tail at 1 is 22/1024 = 0.0215, and at 2 is 0.109."""
        self.assertEqual(self.bias.critical(10, Fraction(1, 10)), (1, 9))
        self.assertEqual(self.bias.critical(10, Fraction(22, 1024)), (1, 9))
        self.assertEqual(self.bias.critical(10, Fraction(21, 1024)), (0, 10))

    def test_an_odd_n_is_refused(self):
        with self.assertRaises(ValueError):
            self.bias.critical(11, Fraction(1, 10))

    def test_a_verdict_compares_integers_at_both_ends(self):
        entry = {"low": 10, "high": 90}
        counts = np.array([0, 10, 11, 50, 89, 90, 100])
        self.assertEqual(self.bias.fires(counts, entry).tolist(),
                         [True, True, False, False, False, True, True])

    def test_p_values_are_exact_on_a_stated_row(self):
        self.assertAlmostEqual(float(self.bias.p_values(np.array([1]), 10)[0]), 22 / 1024, places=12)
        self.assertAlmostEqual(float(self.bias.p_values(np.array([9]), 10)[0]), 22 / 1024, places=12)
        self.assertEqual(float(self.bias.p_values(np.array([5]), 10)[0]), 1.0)

    def test_ones_agrees_with_a_count_bit_by_bit(self):
        rng = np.random.default_rng(7)
        for w in (4, 8, 16, 32):
            for states in (rng.integers(0, 2 ** w, size=(5, 37), dtype=np.uint64),
                           np.full((3, 9), 2 ** w - 1, dtype=np.uint64), np.zeros((3, 0), dtype=np.uint64)):
                by_bit = [[int(((states[lane] >> np.uint64(bit)) & np.uint64(1)).sum()) for bit in range(w)]
                          for lane in range(states.shape[0])]
                self.assertEqual(self.bias.ones(states, w).tolist(), by_bit, w)

    def test_ones_reads_no_bit_past_the_width(self):
        self.assertEqual(self.bias.ones(np.array([[0xFF0]], dtype=np.uint64), 4).tolist(), [[0, 0, 0, 0]])
        self.assertEqual(self.bias.ones(np.array([[0x1FF]], dtype=np.uint64), 8).tolist(), [[1] * 8])
        self.assertEqual(self.bias.ones(np.array([[1 << 32]], dtype=np.uint64), 8).tolist(), [[0] * 8])

    def test_ones_reads_a_part_of_a_batch(self):
        states = np.arange(40, dtype=np.uint64).reshape(4, 10)
        for part in (states[:, 3:8], states[:, ::2], states[1:3]):
            self.assertEqual(self.bias.ones(part, 8).tolist(), self.bias.ones(part.copy(), 8).tolist())

    def test_ones_counts_each_lane_and_bit(self):
        states = np.array([[0b101, 0b100], [0b011, 0b000]], dtype=np.uint64)
        counts = self.bias.ones(states, 4)
        self.assertEqual(counts.tolist(), [[1, 0, 2, 0], [1, 1, 0, 0]])

    def test_the_test_order_is_lanes_then_bits_from_the_top(self):
        counts = np.array([[1, 2, 3], [4, 5, 6]])
        self.assertEqual(self.bias.test_order(counts).tolist(), [3, 2, 1, 6, 5, 4])

    def rotation_list(self):
        return self.ir.load(self.ir.Program("rot", 2, 8, (self.ir.Phase(0, (self.ir.Rot(0, 1),)),)))

    def test_frequency_counts_follow_each_round_both_ways(self):
        loaded = self.rotation_list()
        states = np.zeros((8, 2), dtype=np.uint64)
        states[0] = [0b1, 0b1]
        out = self.bias.frequency_counts(loaded, [states], (), 3)
        for r in range(3):
            self.assertEqual(out["forward"][r, 0].tolist(), [2 if b == r + 1 else 0 for b in range(8)])
            self.assertEqual(out["inverse"][r, 0].tolist(), [2 if b == 7 - r else 0 for b in range(8)])

    def test_batches_add_up(self):
        loaded = self.rotation_list()
        states = np.ones((8, 4), dtype=np.uint64)
        whole = self.bias.frequency_counts(loaded, [states], (), 2)
        parts = self.bias.frequency_counts(loaded, self.bias.batches_of(states, 3), (), 2)
        self.assertTrue((whole["forward"] == parts["forward"]).all())
        self.assertTrue((whole["inverse"] == parts["inverse"]).all())

    def test_the_inverse_reads_the_table_from_its_end(self):
        program = self.ir.Program("c", 2, 8, (self.ir.Phase(0, (
            self.ir.Mix(0, "xor", self.ir.Constant(0)),)),))
        loaded = self.ir.load(program)
        states = np.zeros((8, 1), dtype=np.uint64)
        out = self.bias.frequency_counts(loaded, [states], [(0x01,), (0x02,)], 2)
        self.assertEqual(out["forward"][0, 0].tolist()[:2], [1, 0])
        self.assertEqual(out["forward"][1, 0].tolist()[:2], [1, 1])
        self.assertEqual(out["inverse"][0, 0].tolist()[:2], [0, 1])
        self.assertEqual(out["inverse"][1, 0].tolist()[:2], [1, 1])

    def test_fired_bits_are_named_in_the_test_order(self):
        counts = np.array([[0, 5, 5], [5, 5, 10]])
        self.assertEqual(self.bias.fired_bits(counts, {"low": 1, "high": 9}), [[2, 0], [3, 10]])

    def test_the_control_of_differences_pairs_consecutive_states(self):
        states = np.array([[1, 3, 4, 4]], dtype=np.uint64)
        self.assertEqual(self.bias.control_differences(states).tolist(), [[2, 0]])

    def test_control_counts_sum_their_batches(self):
        batches = [np.array([[1, 1]], dtype=np.uint64), np.array([[1, 0]], dtype=np.uint64)]
        self.assertEqual(self.bias.control_counts(batches, 2).tolist(), [[3, 0]])

    def test_the_planted_bit_of_each_family(self):
        self.assertEqual(self.bias.planted_position("class 5", 7, 4096), 7)
        self.assertEqual(self.bias.planted_position("class 5", 5000, 4096), 904)
        self.assertEqual(self.bias.planted_position("second", 100, 4096), 0)
        self.assertEqual(self.bias.planted_position("second", 199, 4096), 4055)
        self.assertEqual(self.bias.planted_position("second", 150, 65536), 32768)

    def test_a_draw_repeats_and_plants_its_bit(self):
        one = self.bias.draw_set(12345, 64, 9, 0.2, n=1000)
        two = self.bias.draw_set(12345, 64, 9, 0.2, n=1000)
        self.assertTrue((one == two).all())
        self.assertEqual(len(one), 64)
        self.assertGreater(int(one[9]), 620)
        self.assertLess(int(np.abs(np.delete(one, 9) - 500).max()), 120)
        self.assertFalse((one == self.bias.draw_set(12346, 64, 9, 0.2, n=1000)).all())

    def test_a_sets_text_is_decimal_one_count_per_line(self):
        self.assertEqual(self.bias.set_text(np.array([12, 7])), b"12\n7\n")

    def test_a_family_holds_only_inside_both_limits(self):
        holds = self.bias.family_holds
        self.assertEqual([holds(f, 0) for f in (81, 82, 97, 98)], [False, True, True, False])
        self.assertEqual([holds(90, u) for u in (3, 4)], [True, False])

    def test_a_family_counts_a_set_only_when_its_planted_bit_fires(self):
        sets = [{"planted_fires": True, "unplanted": []}, {"planted_fires": False, "unplanted": [[1, 2]]},
                {"planted_fires": True, "unplanted": [[3, 4]]}]
        out = self.bias.summarise("class 5", 4, sets)
        self.assertEqual((out["planted_fired"], out["sets_with_unplanted"]), (2, 2))

    def test_a_family_run_writes_every_set_and_finds_its_plant(self):
        kept = {}
        entry = {"low": 1000, "high": 530000}
        with mock.patch.object(self.bias, "DELTA", {4: 0.49}):
            out = self.bias.run_family("second", range(100, 103), 4, entry, kept.__setitem__)
        self.assertEqual(sorted(kept), [f"synthetic-n4-{j}.txt" for j in range(100, 103)])
        first = out["sets"][0]
        self.assertEqual(first["sha256"], evidence.sha256(kept["synthetic-n4-100.txt"]))
        self.assertTrue(first["planted_fires"])
        self.assertEqual(first["planted"], 0)
        self.assertEqual(first["unplanted"], [])

    def test_a_firing_elsewhere_is_no_firing_of_the_plant(self):
        counts = np.full(4096, 524288)
        counts[5] = 10 ** 6
        entry = {"low": 1000, "high": 530000}
        with mock.patch.object(self.bias, "draw_set", return_value=counts):
            out = self.bias.run_family("class 5", range(0, 1), 4, entry, lambda name, data: None)
        first = out["sets"][0]
        self.assertFalse(first["planted_fires"])
        self.assertEqual(first["unplanted"], [[5, 10 ** 6]])
        self.assertEqual((out["planted_fired"], out["sets_with_unplanted"]), (0, 1))

    def test_the_interval_at_a_stated_fraction(self):
        low, high = self.bias.interval(0.25, 100000)
        self.assertLess(abs(low - 24647), 3)
        self.assertLess(abs(high - 25353), 3)
        self.assertEqual(self.bias.interval(0.0, 1000), (0, 0))


class BiasSeconds(unittest.TestCase):
    """The stated maps of the bias test's second known results, run by the tool."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(CODE_ROOT))
        from scripts import validate_tool
        cls.vt = validate_tool
        cls.bias = bias_module()
        cls.table = validate_tool.known_results()

    def run_known(self, name):
        return self.bias.validation(name, self.vt.load_known(self.table[name]), None)

    def test_each_is_re_found(self):
        for name in ("s12-second", "s14-second", "s15-second"):
            self.assertTrue(self.run_known(name)["re_found"], name)

    def test_a_map_with_another_edge_is_not_s12s(self):
        known = self.vt.load_known(self.table["s12-second"])
        with mock.patch.object(known, "EDGE", ((2 ** 32 - 1, 2 ** 31 - 1),)):
            self.assertFalse(self.bias.validation("s12-second", known, None)["re_found"])

    def test_a_map_with_a_word_off_the_edge_is_not_s12s(self):
        known = self.vt.load_known(self.table["s12-second"])
        with mock.patch.object(known, "TOP", 1):
            self.assertFalse(self.bias.validation("s12-second", known, None)["re_found"])

    def test_another_frequency_is_not_s14s(self):
        known = self.vt.load_known(self.table["s14-second"])
        with mock.patch.object(known, "FREQUENCY", {7: 0.3}):
            self.assertFalse(self.bias.validation("s14-second", known, None)["re_found"])

    def test_a_map_that_sets_bit_31_is_not_s14s(self):
        known = self.vt.load_known(self.table["s14-second"])
        with mock.patch.object(known, "step", lambda state: [w | (1 << 31) for w in state]):
            self.assertFalse(self.bias.validation("s14-second", known, None)["re_found"])

    def test_another_bound_or_step_count_is_not_s15s(self):
        known = self.vt.load_known(self.table["s15-second"])
        with mock.patch.object(known, "BOUND", 1):
            self.assertFalse(self.bias.validation("s15-second", known, None)["re_found"])
        with mock.patch.object(known, "STEPS", 3):
            self.assertFalse(self.bias.validation("s15-second", known, None)["re_found"])
        with mock.patch.object(known, "STEPS", 5):
            self.assertFalse(self.bias.validation("s15-second", known, None)["re_found"],
                             "4 is the first step count with the bound, not 5")

    def test_a_word_within_the_bound_one_step_early_is_not_s15s(self):
        known = self.vt.load_known(self.table["s15-second"])
        at_once = lambda value, steps: known.LIMIT if value == known.EDGE[0] else 0
        with mock.patch.object(known, "after", at_once):
            self.assertFalse(self.bias.validation("s15-second", known, None)["re_found"])


class BiasOnTheModel(unittest.TestCase):
    """What the tool reads of `phyco-v2`, on a short sample, each deciding fact broken once."""

    @classmethod
    def setUpClass(cls):
        cls.bias = bias_module()

    def test_the_sample_is_the_probes(self):
        self.assertEqual(self.bias.vein_count(), 2400000)

    def test_s15s_bound_follows_from_the_range(self):
        with mock.patch.object(self.bias, "descent", return_value={
                "bit31_off_the_edge": 0, "veins_above_2_31": 0}):
            self.assertTrue(self.bias.re_find_s15(None, None)["re_found"])
        with mock.patch.object(self.bias, "descent", return_value={
                "bit31_off_the_edge": 1, "veins_above_2_31": 1}):
            self.assertFalse(self.bias.re_find_s15(None, None)["re_found"])

    def s12(self, values, wanted_fields=None, **descent):
        after = dict({"bit31_off_the_edge": 0, "veins_above_2_31": 0}, **descent)
        wanted = {"totals": dict({"class_counts": [1, 2, 0, 0], "bit31_set": 0, "vein_values": 3},
                                 **(wanted_fields or {}))}
        with mock.patch.object(self.bias, "vein_values",
                               return_value=np.array(values, dtype=np.uint64)), \
                mock.patch.object(self.bias, "descent", return_value=after), \
                mock.patch.object(self.bias, "recorded", return_value=wanted):
            return self.bias.re_find_s12(None, None)["re_found"]

    def test_s12_needs_every_class_count_and_the_edge(self):
        low, high = 1, 1 << 30
        self.assertTrue(self.s12([low, high, high]))
        self.assertFalse(self.s12([low, low, high]))
        self.assertFalse(self.s12([low, high, 3 << 30]))
        self.assertFalse(self.s12([low, high, high], bit31_off_the_edge=1))
        self.assertFalse(self.s12([low, high, high], veins_above_2_31=1))
        self.assertFalse(self.s12([low, high]))

    def test_s12_reads_each_recorded_total_for_itself(self):
        low, high = 1, 1 << 30
        self.assertFalse(self.s12([low, high, 2 << 30], {"class_counts": [1, 1, 1, 0]}))
        self.assertTrue(self.s12([low, high, 2 << 30], {"class_counts": [1, 1, 1, 0], "bit31_set": 1}))
        self.assertFalse(self.s12([low, high, high], {"vein_values": 99}))

    def s14(self, values=None, fired=None, families=True, **wanted):
        """re_find_s14 on a stated sample of 4000 words, every bit at its recorded frequency."""
        top = 1 << 30
        if values is None:
            values = [top + (i & 0xFF) for i in range(4000)]
        array = np.array(values, dtype=np.uint64)
        ones = self.bias.ones(array.reshape(1, -1))[0][::-1]
        probe = {"s14_bit_bias": dict({
            "d_ones_frequency_bit31_to_bit0": [float(c) / array.size for c in ones],
            "d_range": [f"0x{int(array.min()):08X}", f"0x{int(array.max()):08X}"]}, **wanted)}
        entry = {"low": 10 ** 9, "high": 0} if fired else {"low": -1, "high": 10 ** 9}
        with mock.patch.object(self.bias, "vein_values", return_value=array), \
                mock.patch.object(self.bias, "recorded", return_value=probe), \
                mock.patch.object(self.bias, "read_table", return_value={}), \
                mock.patch.object(self.bias, "entry_for", return_value=entry) as self.asked, \
                mock.patch.object(self.bias, "run_family", return_value={"holds": families}) as self.ran:
            return self.bias.re_find_s14(None, None)

    def test_s14_reads_every_deciding_fact(self):
        fired_all = self.s14(fired=True)
        self.assertTrue(fired_all["re_found"])
        self.assertFalse(self.s14()["re_found"], "the five top bits must fire")
        self.assertFalse(self.s14(fired=True, families=False)["re_found"], "a family must hold")
        self.assertFalse(self.s14(fired=True, d_range=["0x0", "0x1"])["re_found"], "the range")
        moved = [0.9] * 32
        self.assertFalse(self.s14(fired=True, d_ones_frequency_bit31_to_bit0=moved)["re_found"])

    def test_s14_needs_bit_31_never_set_and_bit_29_the_complement_of_bit_30(self):
        top = 1 << 30
        self.assertFalse(self.s14([top + i for i in range(3999)] + [3 << 30], fired=True)["re_found"],
                         "bit 31 set once, with bits 30 and 29 still different")
        self.assertFalse(self.s14([3 << 29] * 1 + [top + i for i in range(3999)], fired=True)["re_found"],
                         "bits 30 and 29 equal once, with bit 31 clear")

    def test_s14_runs_both_families_at_each_size_at_that_sizes_counts(self):
        self.s14(fired=True)
        asked = [call.args[:3] for call in self.asked.call_args_list]
        for n in (4, 8, 16):
            self.assertIn(("frequency", 2 ** 20, 256 * n * n), asked)
        ran = [(call.args[0], call.args[2]) for call in self.ran.call_args_list]
        self.assertEqual(sorted(ran), sorted((family, n) for n in (4, 8, 16)
                                             for family in ("class 5", "second")))
        self.assertEqual({len(call.args[1]) for call in self.ran.call_args_list}, {100})

    def test_s14_records_what_it_read(self):
        found = self.s14(fired=True)["found"]
        self.assertEqual(found["vein_values"], 4000)
        self.assertEqual(found["bit30_differs_from_bit29"], 4000)
        self.assertEqual(found["numpy"], np.__version__)
        self.assertEqual(found["ones_bit31_to_bit0"][1], 4000)

    def test_the_sample_reads_every_vein_after_every_step_in_seed_order(self):
        from phycoweb.model_v2 import PhycoWebEngineV2
        from protocol import seedsets
        with mock.patch.object(self.bias, "STEPS", 2):
            values = self.bias.vein_values().tolist()
        wanted = []
        for seed in [seedsets.load("dev", allow=("dev",))[0], (0, 0, 0, 0), (65535,) * 4]:
            engine = PhycoWebEngineV2(list(seed))
            for _ in range(2):
                engine.compute_block()
                wanted += engine.D
        self.assertEqual(values, wanted)

    def test_the_uniform_start_counts_what_it_says(self):
        tops = [1 << 31, (1 << 31) + 1]
        with mock.patch.object(self.bias, "STARTS", 1), \
                mock.patch.object(self.bias.PhycoWebEngineV2, "compute_block", lambda s: setattr(
                    s, "D", [1, tops[0], tops[1], tops[1]])):
            after = self.bias.descent()
        self.assertEqual(after["veins_above_2_31"], 2)
        self.assertEqual(after["bit31_set"], 3)
        self.assertEqual(after["bit31_off_the_edge"], 2)
        self.assertEqual(after["largest"], tops[1])

    def test_the_uniform_start_takes_pressures_and_veins_from_the_state_in_lane_order(self):
        seen = {}
        states = [[1, 2, 3, 4, 5, 6, 7, 8]]

        def step(engine):
            seen["P"], seen["D"] = list(engine.P), list(engine.D)

        with mock.patch.object(self.bias, "STARTS", 1), \
                mock.patch.object(self.bias.devinputs_v3, "load", return_value=states), \
                mock.patch.object(self.bias.PhycoWebEngineV2, "compute_block", step):
            self.bias.descent()
        self.assertEqual((seen["P"], seen["D"]), ([1, 3, 5, 7], [2, 4, 6, 8]))

    def test_the_inputs_name_what_each_known_result_reads(self):
        kinds = {name: [item["kind"] for item in self.bias.inputs(name)["sets"]]
                 for name in ("s12", "s14", "s15", "s15-second")}
        self.assertEqual(kinds["s12"], ["seed", "state"])
        self.assertEqual(kinds["s14"], ["seed", "synthetic", "synthetic", "synthetic"])
        self.assertEqual(kinds["s15"], ["state"])
        self.assertEqual(kinds["s15-second"], ["state"])

    def test_the_uniform_start_is_read_lane_by_lane(self):
        with mock.patch.object(self.bias, "STARTS", 8):
            after = self.bias.descent()
        self.assertEqual((after["starts"], after["steps"]), (8, 16))
        self.assertEqual(after["veins_above_2_31"], 0)
        self.assertEqual(after["bit31_off_the_edge"], 0)


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
