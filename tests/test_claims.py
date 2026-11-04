"""Feature 004: the claim test, every case FR-069 names (FR-050, FR-068, FR-069; SC-015, SC-018).

The register against README, security.md's sections 1.1 and 15 and the three disclaimer blocks; the
register against the Review & Approval rows and the files at HEAD; every wording rule, on sample
sentences that must and must not be flagged; the allow-list; and this repository at HEAD.
"""
import json
import unittest
from typing import Dict, List
from unittest import mock

from protocol import evidence
from protocol.disclaimer import DESIGN_DISCLAIMER
from protocol.evidence import NONE
from scripts import check_claims as cc
from tests.support_004 import SPEC_HEAD, SPEC_TAIL, TempRepo, write

FEATURE_DOC = "specs/004-crypto-architecture-v3/note.md"
STANDARD = "SP 800-90A"
BLOCK = f"> {DESIGN_DISCLAIMER}\n\n"
DISCLAIMER_PHRASE = "an established cryptographic random-number generator"
README = f"""# Title

> **Status.** {cc.FIXED_SENTENCE}
> The seed of `float-v0`, `lut-v1` and `phyco-v2` caps each of them at 64 bits.

## Section

Some text.
"""
SECURITY = f"""# Policy

> **Do not use it.** {cc.FIXED_SENTENCE}
> Use an established cryptographic RNG instead.

## 1. Status

### 1.1 Models

| Model | Source | Claim level (section 15) | Role |
|-------|--------|--------------------------|------|
| `float-v0` | a | L0; no claim | r |
| `lut-v1` | b | L0; no claim | r |
| `phyco-v2` | c | L0; no claim. More words | r |
| `phyco-v3` | none yet | L0; no claim | r |

### 1.2 Next

- `float-v0`: L0; no claim. Archived.
- `lut-v1`: L0; no claim. Rejected.
- `phyco-v2`: L0; no claim. Words.
- `phyco-v3`: L0; no claim. In progress.

> {cc.FIXED_SENTENCE} Use an established cryptographic RNG.
"""


def phrase(text: str) -> Dict:
    return {"phrase": text, "reason": "a test", "writer": "w", "date": "d"}


def new_register() -> Dict:
    def entry(bound: str) -> Dict:
        return {"claim_level": "L0", "in_progress": NONE, "claim": "no claim", "bound": bound,
                "evidence": [], "updated": "2026-11-03", "history": []}

    return {"models": {"float-v0": entry("at most 64 bits"), "lut-v1": entry("at most 64 bits"),
                       "phyco-v2": entry("at most 64 bits"), "phyco-v3": entry(NONE)},
            "allow_list": {"phrases": [phrase(DISCLAIMER_PHRASE)], "lines": []}}


def flags(text: str, register: Dict = None, rel: str = FEATURE_DOC) -> List[str]:
    lines = text.split("\n")
    return [f.rule for f in cc.scan_lines(rel, list(range(len(lines))), lines,
                                          register or new_register())]


class ClaimRepo(TempRepo):
    def write_spec(self) -> None:
        write(self.root, evidence.SPEC_REL, "# Spec\n\n" + BLOCK + SPEC_HEAD
              + "".join(line + "\n" for line in self.rows) + SPEC_TAIL)

    def setUp(self):
        super().setUp()
        write(self.root, evidence.RESEARCH_REL, "# Research\n\n" + BLOCK)
        write(self.root, "README.md", README)
        write(self.root, "security.md", SECURITY)
        self.commit("documents")
        self.register = new_register()
        patcher = mock.patch.object(cc, "code_files", return_value=[])
        patcher.start()
        self.addCleanup(patcher.stop)

    def rules(self) -> List[str]:
        return [f.rule + ": " + f.text for f in cc.run_checks(self.register)]

    def assert_clean(self) -> None:
        self.assertEqual(self.rules(), [])

    def assert_flagged(self, words: str) -> None:
        self.assertTrue([r for r in self.rules() if words in r], self.rules())

    def set_file(self, rel: str, old: str, new: str) -> None:
        text = (self.root / rel).read_text(encoding="utf-8")
        self.assertIn(old, text)
        write(self.root, rel, text.replace(old, new))


class Baseline(ClaimRepo):
    def test_a_repository_that_agrees_has_no_finding(self):
        self.assert_clean()


class Disclaimers(ClaimRepo):
    def test_a_block_missing_exits_1(self):
        self.set_file("README.md", f"> **Status.** {cc.FIXED_SENTENCE}\n> The seed of `float-v0`, "
                      "`lut-v1` and `phyco-v2` caps each of them at 64 bits.\n", "")
        self.assert_flagged("a disclaimer block is missing")
        write(self.root, "README.md", README)
        text = SECURITY.replace(f"> {cc.FIXED_SENTENCE} Use an established cryptographic RNG.\n",
                                "")
        text = text.replace(f"> **Do not use it.** {cc.FIXED_SENTENCE}\n> Use an established "
                            "cryptographic RNG instead.\n", "")
        write(self.root, "security.md", text)
        self.assert_flagged("a disclaimer block is missing")

    def test_a_block_without_the_fixed_sentence(self):
        for rel, old in (("README.md", cc.FIXED_SENTENCE), ("security.md",
                         f"**Do not use it.** {cc.FIXED_SENTENCE}"),
                         ("security.md", f"> {cc.FIXED_SENTENCE} Use")):
            original = (self.root / rel).read_text(encoding="utf-8")
            self.set_file(rel, old, old.replace(cc.FIXED_SENTENCE, "Do not use it for secrets."))
            self.assert_flagged("the block lacks the fixed sentence")
            write(self.root, rel, original)

    def test_the_sentence_changed_by_one_word(self):
        self.set_file("README.md", cc.FIXED_SENTENCE,
                      cc.FIXED_SENTENCE.replace("every model", "each model"))
        self.assert_flagged("the block lacks the fixed sentence")

    def test_the_sentence_may_wrap_over_lines(self):
        self.set_file("README.md", cc.FIXED_SENTENCE,
                      cc.FIXED_SENTENCE.replace("every model ", "every\n> model "))
        self.assert_clean()

    def test_a_bound_above_an_entry(self):
        self.set_file("README.md", "at 64 bits", "at 128 bits")
        self.assert_flagged("a bound beyond the register's for phyco-v2")

    def test_a_bound_for_an_entry_that_holds_none(self):
        self.set_file("README.md", "`phyco-v2` caps", "`phyco-v3` caps")
        self.assert_flagged("a bound beyond the register's for phyco-v3")

    def test_a_line_that_states_a_bound_and_names_no_model(self):
        self.set_file("README.md", "The seed of `float-v0`, `lut-v1` and `phyco-v2` caps each of "
                      "them at 64 bits.", "The seed caps it at 64 bits.")
        self.assert_flagged("a bound that names no model")

    def test_a_figure_that_bounds_no_model(self):
        self.set_file("README.md", "Status.**", "Status.** It is below the 112-bit minimum.")
        self.assert_flagged("a bound that names no model")

    def test_a_power_of_2_is_a_bound(self):
        self.set_file("README.md", "at 64 bits", "at 2⁶⁵")
        self.assert_flagged("a bound beyond the register's")

    def test_a_claim_beside_no_claim(self):
        self.set_file("README.md", "caps each of them at 64 bits",
                      "caps the security level of each at 64 bits")
        self.assert_flagged("a claim beside no claim for phyco-v2")

    def test_a_claim_that_names_no_model(self):
        self.set_file("README.md", "**Status.**", "**Status.** It may resist attack.")
        self.assert_flagged("a claim that names no model")

    def test_each_of_the_three_phrases_is_read_as_negated(self):
        for text in ("It holds no claim.", "Tests do not show cryptographic security.",
                     "A test does not show cryptographic security."):
            write(self.root, "README.md", README.replace("**Status.**", f"**Status.** {text}"))
            self.assert_clean()

    def test_a_negation_outside_them_is_a_claim(self):
        for text in ("It makes no claims.", "It is not a claim of strength.",
                     "It shows no cryptographic security."):
            write(self.root, "README.md", README.replace("**Status.**", f"**Status.** {text}"))
            self.assert_flagged("a claim that names no model")

    def test_a_level_in_a_block(self):
        self.set_file("README.md", "**Status.**", "**Status.** `phyco-v2` is at L2.")
        self.assert_flagged("a level above claim_level: L2")

    def test_a_wording_rule_in_a_block_takes_no_entry(self):
        self.set_file("README.md", "**Status.**", "**Status.** It is random.")
        self.register["allow_list"]["phrases"].append(phrase("is random"))
        self.assert_flagged("random")

    def test_the_two_documents_carry_no_copy_of_the_design_form(self):
        self.set_file("README.md", "## Section", f"> {DESIGN_DISCLAIMER}\n\n## Section")
        self.assert_flagged("carries no copy")


class SecurityRows(ClaimRepo):
    def test_a_row_missing(self):
        self.set_file("security.md", "| `lut-v1` | b | L0; no claim | r |\n", "")
        self.assert_flagged("no section 1.1 row for lut-v1")

    def test_a_row_added(self):
        self.set_file("security.md", "| `lut-v1` | b", "| `other-v9` | d | L0; no claim | r |\n"
                      "| `lut-v1` | b")
        self.assert_flagged("a section 1.1 row with no register entry")

    def test_a_row_that_differs(self):
        self.set_file("security.md", "| `lut-v1` | b | L0; no claim |", "| `lut-v1` | b | L1; a |")
        self.assert_flagged("the row's cell differs")

    def test_the_cell_may_go_on_after_its_leading_level_and_claim(self):
        self.assert_clean()

    def test_section_15_must_state_the_register(self):
        self.set_file("security.md", "- `phyco-v3`: L0; no claim. In progress.\n", "")
        self.assert_flagged("section 15 does not state")


class ReadmeLines(ClaimRepo):
    def test_a_line_outside_the_block_whose_bound_is_beyond_the_register(self):
        self.set_file("README.md", "Some text.", "`phyco-v2` has a security level of 128 bits.")
        self.assert_flagged("a bound beyond the register's for phyco-v2")

    def test_a_line_outside_the_block_with_a_claim(self):
        self.set_file("README.md", "Some text.", "`phyco-v2` makes a claim here.")
        self.assert_flagged("a claim beside no claim for phyco-v2")

    def test_a_line_that_holds_none_of_the_words_is_not_read_so(self):
        self.set_file("README.md", "Some text.", "The seed is 16 bits wide and costs 2⁷² steps.")
        self.assert_clean()


class Levels(ClaimRepo):
    REVIEWS = ("FUT-SEC-8 result review", "Security-target review")

    def reviewed(self, digest: str = None) -> str:
        """The two reviews and "L1 recorded" Approved, naming a committed file by its SHA-256."""
        write(self.root, "docs/reviewed.md", "# Reviewed\n")
        self.commit("the reviewed file")
        digest = evidence.sha256(b"# Reviewed\n")
        for name in self.REVIEWS:
            self.add_row(name, "Approved", f"`docs/reviewed.md` {digest}")
        self.add_row("L1 recorded", "Approved", " and ".join(self.REVIEWS))
        return digest

    def level_one(self, digest: str) -> None:
        entry = self.register["models"]["phyco-v3"]
        entry["claim_level"] = "L1"
        entry["evidence"] = [{"path": "docs/reviewed.md", "sha256": digest}]
        self.set_file("security.md", "| `phyco-v3` | none yet | L0; no claim |",
                      "| `phyco-v3` | none yet | L1; no claim |")
        self.set_file("security.md", "- `phyco-v3`: L0; no claim.", "- `phyco-v3`: L1; no claim.")

    def test_a_register_above_the_rows(self):
        self.register["models"]["phyco-v3"]["claim_level"] = "L1"
        self.assert_flagged("phyco-v3 reads L1, and the rows give L0")

    def test_a_register_below_the_rows(self):
        self.reviewed()
        self.assert_flagged("phyco-v3 reads L0, and the rows give L1")

    def test_a_register_at_the_rows(self):
        self.level_one(self.reviewed())
        self.assertEqual([r for r in self.rules() if "the rows give" in r], [])

    def test_a_review_not_approved_gives_l0(self):
        self.reviewed()
        self.rows[-3] = self.rows[-3].replace("Approved", "Declined")
        self.write_spec()
        self.commit("declined")
        self.assertEqual(cc.expected_level(evidence.head_table()), "L0")

    def test_a_later_row_of_either_family_makes_l1_lapse(self):
        self.level_one(self.reviewed())
        self.add_row("Security-target review 2", "Approved", "again")
        self.assert_flagged("phyco-v3 reads L1, and the rows give L0")

    def test_a_reviewed_file_changed_at_head_with_the_register_at_l1(self):
        self.level_one(self.reviewed())
        write(self.root, "docs/reviewed.md", "# Changed\n")
        self.commit("changed")
        self.assert_flagged("phyco-v3 reads L1, and the rows give L0")

    def test_a_reviewed_file_changed_at_head_with_the_register_at_l0(self):
        self.reviewed()
        write(self.root, "docs/reviewed.md", "# Changed\n")
        self.commit("changed")
        self.assertEqual([r for r in self.rules() if "the rows give" in r], [])
        self.assert_flagged("history lacks the L1 of L1 recorded")

    def test_history_holds_the_lapsed_l1(self):
        self.reviewed()
        write(self.root, "docs/reviewed.md", "# Changed\n")
        self.commit("changed")
        self.register["models"]["phyco-v3"]["history"] = [{
            "level": "L1", "rows": ["L1 recorded"], "from": "d", "to": "d", "version": "0.1"}]
        self.assertEqual([r for r in self.rules() if "history" in r], [])

    def test_a_chapter_named_in_a_review_row(self):
        text = "# Doc\n\n## Mode\n\nwords\n\n## Next\n"
        write(self.root, "docs/doc.md", text)
        self.commit("doc")
        digest = evidence.sha256(b"## Mode\n\nwords\n\n")
        self.assertEqual(cc.named_hashes(f'`docs/doc.md`, chapter "Mode", {digest}'),
                         [("docs/doc.md", "Mode", digest)])
        self.assertTrue(cc.hash_holds("docs/doc.md", "Mode", digest))
        self.assertFalse(cc.hash_holds("docs/doc.md", "Next", digest))


class InProgress(ClaimRepo):
    def record(self, created: str = "2026-12-01T00:00:00Z", **fields) -> None:
        body = dict({"kind": "bound", "status": "pass", "validation": "v", "created_utc": created},
                    **fields)
        write(self.root, f"{evidence.REP_REL}/candidates/cand-A1/b.json", evidence.pretty(body))
        self.commit("a bound")

    def state(self, **fields) -> None:
        self.register["models"]["phyco-v3"]["in_progress"] = fields

    def test_naming_l2_with_no_counted_record(self):
        self.state(level="L2", start="2026-12-01", status="not reached")
        self.assert_flagged("in_progress names a level")

    def test_a_record_not_counted_leaves_none(self):
        self.record(status="inconclusive")
        self.assert_clean()

    def test_none_once_one_exists(self):
        self.record()
        self.assert_flagged("in_progress does not name L2")

    def test_another_start_date(self):
        self.record()
        self.state(level="L2", start="2026-11-30", status="not reached")
        self.assert_flagged("in_progress does not name L2")

    def test_the_first_records_date(self):
        self.record()
        self.state(level="L2", start="2026-12-01", status="not reached")
        self.assertEqual([r for r in self.rules() if "in_progress" in r], [])


class BoundAndEvidence(ClaimRepo):
    def profile(self) -> str:
        rel, _ = cc.profile_paths()
        data = evidence.pretty({"rows": [
            {"variant_id": "phyco-v3/n4", "claimable": True, "bound_bits": 128},
            {"variant_id": "phyco-v3/n2", "claimable": False, "bound_bits": 32}]})
        write(self.root, rel, data)
        self.commit("the profile")
        return evidence.sha256(data)

    def bound(self, digest: str, value: str = "at most 128 bits") -> None:
        rel, _ = cc.profile_paths()
        self.register["models"]["phyco-v3"]["bound"] = {
            "sizes": {"phyco-v3/n4": value}, "path": rel, "sha256": digest}

    def test_none_until_the_profile_exists(self):
        self.register["models"]["phyco-v3"]["bound"] = "at most 128 bits"
        self.assert_flagged("bound must read none")

    def test_a_bound_that_differs_from_the_profile(self):
        self.bound(self.profile(), "at most 127 bits")
        self.assert_flagged("bound differs from the profile's bound_bits")

    def test_a_bound_with_another_hash(self):
        self.profile()
        self.bound("0" * 64)
        self.assert_flagged("another SHA-256 of the size profile")

    def test_an_evidence_entry_missing(self):
        digest = self.profile()
        self.bound(digest)
        self.assert_flagged("evidence lacks")

    def test_an_evidence_entry_with_another_hash(self):
        digest = self.profile()
        self.bound(digest)
        rel, _ = cc.profile_paths()
        self.register["models"]["phyco-v3"]["evidence"] = [{"path": rel, "sha256": "0" * 64}]
        self.assert_flagged("evidence names another SHA-256")

    def test_at_their_values(self):
        digest = self.profile()
        self.bound(digest)
        rel, _ = cc.profile_paths()
        self.register["models"]["phyco-v3"]["evidence"] = [{"path": rel, "sha256": digest}]
        self.assert_clean()

    def test_the_least_of_the_sizes_unless_a_size_is_named(self):
        entry = {"bound": {"sizes": {"phyco-v3/n4": "at most 128 bits",
                                     "phyco-v3/n8": "at most 256 bits"}}}
        self.assertEqual(cc.register_bound(entry, None), 128)
        self.assertEqual(cc.register_bound(entry, "phyco-v3/n8"), 256)

    def test_a_level_outside_the_ladder(self):
        self.register["models"]["phyco-v3"]["claim_level"] = "L7"
        self.assert_flagged("outside L0 to L6")

    def test_an_entry_for_each_model(self):
        del self.register["models"]["lut-v1"]
        self.assert_flagged("no entry for lut-v1")


class AllowList(ClaimRepo):
    def line(self, path: str, text: str, **fields) -> Dict:
        return dict({"path": path, "text": text, "reason": "a test", "writer": "w", "date": "d"},
                    **fields)

    def test_an_entry_that_names_a_line_of_a_block(self):
        text = f"> **Status.** {cc.FIXED_SENTENCE}"
        self.register["allow_list"]["lines"].append(self.line("README.md", text))
        self.assert_flagged("an entry names a line of a block")

    def test_an_entry_that_names_a_finding_of_the_registers_checks(self):
        self.register["allow_list"]["lines"].append(
            self.line(cc.REGISTER_REL, "phyco-v3 reads L1", rule="the register's checks"))
        self.assert_flagged("an entry names a finding of the register's checks")

    def test_a_finding_of_the_register_passes_through_no_entry(self):
        self.register["models"]["phyco-v3"]["claim_level"] = "L1"
        self.register["allow_list"]["phrases"].append(phrase("phyco-v3 reads L1"))
        self.assert_flagged("the rows give L0")

    def test_a_line_entry_passes_its_line_and_no_other(self):
        write(self.root, FEATURE_DOC, "# Doc\n\n" + BLOCK + "It is random.\nIt is random too.\n")
        self.register["allow_list"]["lines"].append(self.line(FEATURE_DOC, "It is random."))
        found = [f.text for f in cc.run_checks(self.register) if f.rule == "random"]
        self.assertEqual(found, ["It is random too."])

    def test_an_entry_under_another_path_passes_nothing(self):
        self.assertEqual(flags("It is random.", {"models": new_register()["models"], "allow_list": {
            "phrases": [], "lines": [self.line("other.md", "It is random.")]}}), ["random"])

    def test_a_standing_phrase_passes_only_its_phrase(self):
        register = new_register()
        register["allow_list"]["phrases"].append(phrase("random permutation"))
        self.assertEqual(flags("modelled as a random permutation", register), [])
        self.assertEqual(flags("a random permutation of random words", register), ["random"])

    def test_a_copy_of_a_cited_version_reads_as_its_document(self):
        register = new_register()
        register["allow_list"]["lines"].append(self.line(evidence.SPEC_REL, "It is random."))
        rel = f"{evidence.REP_REL}/spec-versions/{'0' * 64}.md"
        self.assertEqual(flags("It is random.", register, rel), [])

    def test_entries_since_the_last_gate_are_printed(self):
        write(self.root, cc.REGISTER_REL, json.dumps(self.register))
        self.commit("the register")
        self.add_row("Tasks approval", "Approved", "gate")
        write(self.root, cc.REGISTER_REL, json.dumps(self.register))
        added = phrase("a new phrase")
        self.register["allow_list"]["phrases"].append(added)
        self.assertEqual(cc.entries_since_gate(self.register), [added])


class Documents(ClaimRepo):
    def test_a_document_without_the_design_form(self):
        write(self.root, FEATURE_DOC, "# Doc\n\nNo block.\n")
        self.assert_flagged("does not carry the design-form disclaimer")

    def test_a_copy_that_differs(self):
        write(self.root, FEATURE_DOC, "# Doc\n\n> " + DESIGN_DISCLAIMER[:-1] + "\n")
        self.assert_flagged("does not carry the design-form disclaimer")

    def test_a_copy_wrapped_over_lines_is_the_same_text(self):
        text = DESIGN_DISCLAIMER.replace(". ", ".\n> ")
        write(self.root, FEATURE_DOC, "# Doc\n\n> " + text + "\n")
        self.assert_clean()

    def test_a_report_under_the_reports_directory(self):
        write(self.root, f"{evidence.REP_REL}/report.md", "# Report\n")
        self.assert_flagged("does not carry the design-form disclaimer")


class MappingChapter(ClaimRepo):
    def design(self, chapter: str, heading: str = "## Slime-mould mapping\n\n") -> None:
        write(self.root, evidence.DESIGN_REL, "# Design\n\n" + BLOCK + "Version: 0.1\n\n" + heading
              + chapter + "\n## Next\n\nsecurity words here\n")
        self.commit("design")

    def test_the_heading_missing_or_found_twice(self):
        self.design("words\n", heading="## Other\n\n")
        self.assert_flagged("stands 0 times")
        self.design("words\n\n## Slime-mould mapping\n\nmore\n")
        self.assert_flagged("stands 2 times")

    def test_only_the_fixed_sentence_passes(self):
        self.design(cc.MAPPING_SENTENCE + "\n")
        self.assertEqual(cc.mapping_findings(self.register), [])

    def test_each_word_of_the_list_is_flagged_inside_and_only_inside(self):
        for word in ("security", "insecure", "strong", "resistant", "unpredictable", "chaotic",
                     "Lyapunov", "ergodicity", "emergent", "complexity", "biological", "mixing",
                     "Diffusion", "avalanche", "batteries"):
            self.design(f"The veins bring {word} here.\n")
            self.assertTrue(cc.mapping_findings(self.register), word)

    def test_a_chapter_with_none_of_the_words(self):
        self.design("Pressure lanes stand for nodes, and vein lanes for tubes.\n")
        self.assertEqual(cc.mapping_findings(self.register), [])


class WordingRules(unittest.TestCase):
    def assert_rule(self, text: str, rule: str) -> None:
        self.assertIn(rule, flags(text), text)

    def assert_passes(self, text: str) -> None:
        self.assertEqual(flags(text), [], text)

    def test_each_form_of_random(self):
        for word in ("random", "randomly", "randomness", "randomize", "randomizes", "randomized",
                     "randomizing", "randomization", "randomise", "randomises", "randomised",
                     "randomising", "randomisation", "Random", "RANDOM"):
            self.assert_rule(f"The output is {word} here.", "random")

    def test_a_word_is_a_run_of_letters_and_digits(self):
        for text in ("a random-nonce limit", "the random_state seed", "`numpy.random` here",
                     "truly random"):
            self.assert_rule(text, "random")
        for text in ("`os.urandom`", "`getrandom()`", "randoms", "derandomized"):
            self.assert_passes(text)

    def test_the_other_line_words(self):
        for text, rule in (("a high-entropy source", "high-entropy"), ("it is secure", "secure"),
                           ("securely stored", "secure"), ("cryptographically secure", "secure"),
                           ("proven secure", "secure"), ("phyco-v3 is unbreakable", "unbreakable"),
                           ("in constant time", "constant time"), ("a constant-time path",
                                                                   "constant time"),
                           ("a related-key analysis", "related-key or weak-key analysis"),
                           ("a weak-key analysis", "related-key or weak-key analysis"),
                           ("it gives prediction resistance", "prediction resistance")):
            self.assert_rule(text, rule)

    def test_each_form_of_prove(self):
        for word in ("prove", "proves", "proved", "proving", "proven", "provably"):
            self.assert_rule(f"The tests {word} it.",
                             "a form of prove without its object and record")

    def test_proven_with_its_object_and_its_record(self):
        self.assert_passes("The proven trail bound is cited from its record `x.json`.")
        self.assert_rule("The proven trail bound holds.",
                         "a form of prove without its object and record")

    def test_a_strength_not_labelled(self):
        rule = "a strength not labelled as a target"
        for text in ("It has 128 bits of security.", "The strength is 256 bits.",
                     "It costs 2¹²⁸ against this security.", "A 128-bit strength."):
            self.assert_rule(text, rule)
        for text in ("The security target is 128 bits.", "FR-005 sets a strength of 128 bits.",
                     "The state has 256 bits.", "It costs 2¹²⁸ steps."):
            self.assert_passes(text)

    def test_near_means_the_same_sentence_or_row(self):
        self.assert_passes("It has 128 bits. The strength stands elsewhere.")
        self.assert_rule("| 128 bits | strength |", "a strength not labelled as a target")
        self.assert_passes("| 128 bits | a |\n| b | strength |")
        self.assert_rule("It has 128\nbits of\nstrength.", "a strength not labelled as a target")

    def test_results_offered_as_evidence(self):
        rule = "results offered as evidence"
        for text in ("The avalanche test shows good mixing.",
                     "Battery results are evidence of security.",
                     "Frequency results give evidence for strong security."):
            self.assert_rule(text, rule)
        self.assert_passes("The avalanche test reports its counts.")

    def test_each_conformity_form_near_a_standard(self):
        rule = "a conformity word near a standard's name"
        for word in ("comply", "complies", "complied", "complying", "compliant", "compliance",
                     "conform", "conforms", "conformed", "conforming", "conformance", "conformant",
                     "approve", "approves", "approved", "approving", "approval"):
            self.assert_rule(f"It is {word} with {STANDARD}.", rule)
            self.assert_passes(f"It is {word} here.")
        self.assert_rule("FIPS 140-3 approved", rule)

    def test_drbg_beside_a_model(self):
        for text in ("phyco-v3 is a DRBG.", "the model is a DRBG", "the generator is a DRBG",
                     "the design is a DRBG"):
            self.assert_rule(text, "DRBG beside a model")
        self.assert_passes("Use a DRBG instead.")

    def test_fips_140_beside_self_test(self):
        self.assert_rule("a FIPS 140-3 self-test", "FIPS 140 beside self-test")
        self.assert_passes("a start-up self-test")

    def test_evaluation_beside_a_review(self):
        for text in ("the external review is an evaluation", "an evaluated design review",
                     "certified by external review"):
            self.assert_rule(text, "evaluation beside a review")
        self.assert_passes("three evaluated candidates")

    def test_the_level_rule_with_the_register(self):
        rule = "a level above claim_level: "
        self.assert_rule("phyco-v3 is at L2", rule + "L2")
        self.assert_rule("the design reaches L3", rule + "L3")
        self.assert_rule("at level L1 now", rule + "L1")
        self.assert_passes("It stays at L0.")
        self.assert_passes("the L10 word and aL1 and L1x")

    def test_the_level_rule_reads_the_lowest_level_a_line_names(self):
        register = new_register()
        register["models"]["phyco-v3"]["claim_level"] = "L1"
        self.assertEqual(flags("`phyco-v3` is at L1", register), [])
        self.assertTrue(flags("`phyco-v3` is at L2", register))
        self.assertTrue(flags("`phyco-v3` and `phyco-v2` are at L1", register))
        self.assertTrue(flags("this one is at L1", register))

    def test_the_ladder_rows_stand_through_their_entries(self):
        row = "| L2 | Internally analysed | design rationale |"
        self.assert_rule(row, "a level above claim_level: L2")
        register = new_register()
        register["allow_list"]["lines"].append({"path": "security.md", "text": row, "reason": "r",
                                                "writer": "w", "date": "d"})
        self.assertEqual(flags(row, register, "security.md"), [])

    def test_a_quotation_passes_in_the_checklists_only(self):
        rel = evidence.FEATURE_REL + "/checklists/security.md"
        self.assertEqual(flags('Does it say "random" or `secure`?', rel=rel), [])
        self.assertEqual(flags("Does it say random?", rel=rel), ["random"])
        self.assertTrue(flags('Does it say "random"?'))

    def test_a_code_comment_and_a_docstring_are_scanned(self):
        source = '"""A random module."""\n# is secure\nx = "random"\n'
        self.assertEqual(sorted(cc.python_comments(source).values()), ["A random module.",
                                                                       "is secure"])
        self.assertEqual(cc.c_comments("int x; // random\n/* a\n secure */\n"),
                         {0: "random", 1: "a", 2: "secure"})


class ThisRepository(unittest.TestCase):
    """FR-069's test at HEAD: 0 findings from plan phase 1 on (SC-018)."""

    def test_it_reports_no_finding(self):
        with mock.patch("builtins.print"):
            code = cc.main([])
        if code:
            register = json.loads(cc.read_text(cc.REGISTER_REL))
            self.fail("\n".join(f"{f.path}:{f.line}: {f.rule}: {f.text[:100]}"
                                for f in cc.run_checks(register)[:40]))


if __name__ == "__main__":
    unittest.main()
