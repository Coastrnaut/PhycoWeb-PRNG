"""Feature 004: tests of committed records and of the files whose hashes they hold (FR-053; research
R16, R18). Standard library only; these run from plan phase 1 on, so that a path missed later fails
as soon as the first record that cites it is committed."""
import gzip
import hashlib
import io
import json
import re
import subprocess
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterator, List, Tuple
from unittest import mock

from protocol import devinputs_v3, evidence
from protocol.disclaimer import DESIGN_DISCLAIMER

ROOT = Path(__file__).resolve().parents[1]
REPORTS = "reports/004-crypto-architecture-v3"
# Every path this feature pins, read while no record exists (research R18).
PINNED_PATHS = ("specs/004-crypto-architecture-v3/", REPORTS + "/", "research/004/",
                "vectors/phyco-v3/", "baseline/phyco-v2/")
GZ_PATHS = (REPORTS + "/", "research/004/", "vectors/phyco-v3/", "baseline/phyco-v2/")
BOM = b"\xef\xbb\xbf"


def git(*args: str, data: bytes = None) -> bytes:
    result = subprocess.run(("git",) + args, cwd=ROOT, input=data, capture_output=True, check=True)
    return result.stdout


def tracked(*prefixes: str) -> List[str]:
    return [p for p in git("ls-files", "--", *prefixes).decode("utf-8").splitlines() if p]


def committed_records() -> List[Tuple[str, Dict]]:
    """Every committed JSON record under the reports directory, with its path."""
    records = []
    for path in tracked(REPORTS + "/"):
        if path.endswith(".json"):
            records.append((path, json.loads((ROOT / path).read_text(encoding="utf-8"))))
    return records


def hashed_entries(node) -> Iterator[Tuple[str, str]]:
    """Each (path, hash kind) a record holds: an entry with `path` and `sha256`, and code_sha256."""
    if isinstance(node, dict):
        if isinstance(node.get("path"), str) and "sha256" in node:
            yield node["path"], node.get("sha256_kind", "raw")
        for key, value in node.items():
            if key == "code_sha256" and isinstance(value, dict):
                for path, entry in value.items():
                    yield path, entry.get("kind", "raw")
            else:
                yield from hashed_entries(value)
    elif isinstance(node, list):
        for value in node:
            yield from hashed_entries(value)


def attributes(paths: List[str]) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {path: {} for path in paths}
    text = git("check-attr", "--stdin", "text", "eol", data="\n".join(paths).encode("utf-8"))
    for line in text.decode("utf-8").splitlines():
        path, attr, value = line.rsplit(": ", 2)
        out[path][attr] = value
    return out


class LineEndings(unittest.TestCase):
    """Research R18: a hashed path has an explicit rule, or its record marks the hash."""

    def paths_to_check(self) -> Dict[str, str]:
        paths: Dict[str, str] = {}
        records = committed_records()
        for _, record in records:
            for path, kind in hashed_entries(record):
                if (ROOT / path).exists():
                    paths[path] = kind
        if not records:
            for path in tracked(*PINNED_PATHS):
                paths[path] = "raw"
            for path in tracked("protocol/*.json"):
                paths[path] = "raw"
        return paths

    def test_every_hashed_path_has_a_pin_or_is_marked(self):
        paths = self.paths_to_check()
        self.assertTrue(paths, "nothing to check: the pinned paths hold no tracked file")
        raw = sorted(path for path, kind in paths.items() if kind != "lf-normalized")
        attrs = attributes(raw)
        for path in raw:
            text, eol = attrs[path].get("text"), attrs[path].get("eol")
            self.assertTrue(text == "unset" or (text == "set" and eol == "lf"),
                            f"{path}: text {text}, eol {eol}: no explicit rule, no mark")

    def test_no_hashed_file_starts_with_a_byte_order_mark(self):
        for path in self.paths_to_check():
            with (ROOT / path).open("rb") as handle:
                self.assertNotEqual(handle.read(3), BOM, path)


class CodeHashes(unittest.TestCase):
    """FR-053: each code_sha256 entry, a C tool's binary among them, matches its git_head's blob."""

    def test_each_entry_matches_the_blob_at_git_head(self):
        for name, record in committed_records():
            head, code = record.get("git_head"), record.get("code_sha256")
            if not head or head == "none" or not code or code == "none":
                continue
            for path, entry in code.items():
                blob = git("show", f"{head}:{path}")
                self.assertEqual(hashlib.sha256(blob).hexdigest(), entry["sha256"],
                                 f"{name}: {path} at {head}")


class GzipHeaders(unittest.TestCase):
    """Research R16: every committed .gz file is written by gzip.compress(data, 9, mtime=0)."""

    def test_every_committed_gz_header(self):
        expected = gzip.compress(b"", compresslevel=9, mtime=0)[:10]
        for path in tracked(*GZ_PATHS):
            if path.endswith(".gz"):
                with (ROOT / path).open("rb") as handle:
                    self.assertEqual(handle.read(10), expected, path)


class CommittedFiles(unittest.TestCase):
    """Research R16: the reports directory's suffixes and its 10 MB, and nothing local tracked."""

    def test_nothing_under_data_local_is_tracked(self):
        self.assertEqual(tracked("data/local/"), [])

    def test_each_file_under_the_reports_directory_has_an_allowed_suffix_and_size(self):
        for path in tracked(REPORTS + "/"):
            self.assertTrue(path.endswith(evidence.SUFFIXES), path)
            self.assertLessEqual((ROOT / path).stat().st_size, evidence.MAX_COMMITTED_BYTES, path)


class RecordIds(unittest.TestCase):
    """Data model section 1: each record holds the ID that its own content gives."""

    def test_each_committed_record_holds_the_id_of_its_content(self):
        for path, record in committed_records():
            if "record_id" in record:
                self.assertTrue(evidence.check_record_id(record), path)


class Disclaimers(unittest.TestCase):
    """FR-061: each committed record holds the design-form disclaimer verbatim."""

    def test_each_committed_record_holds_it(self):
        for path, record in committed_records():
            if "record_id" in record:
                self.assertEqual(record.get("disclaimer"), DESIGN_DISCLAIMER, path)


# ---------------------------------------------------------------------------------- the security target

STATED_VARIANTS = """| ID | n | w | b | c | r | R | status |
|----|---|---|---|---|---|---|--------|
| phyco-v3/n4-w32-R20-c256 | 4 | 32 | 1,024 | 256 | 768 | 20 | claimable |
| phyco-v3/n8-w32-R24-c256 | 8 | 32 | 4,096 | 256 | 3,840 | 24 | claimable |
| phyco-v3/n16-w32-R32-c256 | 16 | 32 | 16,384 | 256 | 16,128 | 32 | claimable |
| phyco-v3/n2-w16-R8-c64 | 2 | 16 | 128 | 64 | 64 | 8 (reduced, for a stated test) | research |
| phyco-v3/n2-w4-R8-c16 | 2 | 4 | 32 | 16 | 16 | 8 (reduced, for a stated test) | research |
"""
STATED_LAYOUT = """| Size | w | c | Rate lanes | Capacity lanes | Key lanes | Nonce lanes |
|------|---|---|------------|----------------|-----------|-------------|
| 4×4 | 32 | 256 | 0-23 | 24-31 | 0-7 | 8-11 |
| 8×8 | 32 | 256 | 0-119 | 120-127 | 0-7 | 8-11 |
| 16×16 | 32 | 256 | 0-503 | 504-511 | 0-7 | 8-11 |
| 2×2 | 16 | 64 | 0-3 | 4-7 | 0-3 | 4,5 |
"""
STATED_LIMITS = """| Limit | Size | Value | Bits |
|-------|------|-------|------|
| keys u | all | 2^20 | none |
| instantiations per key | all | 2^20 | none |
| reseeds per instantiation | all | 2^24 | none |
| personalization string, bytes | all | 4,096 | none |
| reseed input, bytes | all | 4,096 | none |
| nonces, first way | all | a counter per key, never repeated or wrapped | none |
| nonces, second way | all | uniform values of the nonce's length | none |
| calls of Π per instantiation | 4×4 | 2^24 | 12,884,901,888 |
| calls of Π per instantiation | 8×8 | 2^24 | 64,424,509,440 |
| calls of Π per instantiation | 16×16 | 2^24 | 270,582,939,648 |
| calls of Π per key | 4×4 | 2^44 | 13,510,798,882,111,488 |
| calls of Π per key | 8×8 | 2^44 | 67,553,994,410,557,440 |
| calls of Π per key | 16×16 | 2^44 | 283,726,776,524,341,248 |
| calls of Π per request | 4×4 | 684 | 524,288 |
| calls of Π per request | 8×8 | 138 | 524,288 |
| calls of Π per request | 16×16 | 34 | 524,288 |
| calls of Π per instantiate | 4×4 | 46 | 35,328 |
| calls of Π per instantiate | 8×8 | 10 | 38,400 |
| calls of Π per instantiate | 16×16 | 4 | 64,512 |
"""


def stated_design(variants: str = STATED_VARIANTS, layout: str = STATED_LAYOUT, limits: str = STATED_LIMITS) -> str:
    return (f"# phyco-v3\n\nVersion: 0.1\n\n## Mode\n\n### Calls\n\n### Layout\n\n{layout}\n### Key loading\n\n"
            f"### Padding and domain separation\n\n### Forget\n\n### Serialization\n\n### Nonce reuse\n\n"
            f"### Limits\n\n{limits}\n## Permutation\n\n### Variant table\n\n{variants}\n")


def limits_script():
    from scripts import mode_limits_v3
    return mode_limits_v3


def small_variant():
    return limits_script().Variant("x/n2-w16-R8-c64", 2, 16, 128, 64, 64, 8, "none", "research")


class ModeLimitsTables(unittest.TestCase):
    """Three tables with fixed columns, each once: anything else is refused, exit 2 (T067)."""

    def setUp(self):
        self.tool = limits_script()

    def test_it_reads_each_table(self):
        text = stated_design()
        variants = self.tool.read_variants(text)
        self.assertEqual([v.b for v in variants], [1024, 4096, 16384, 128, 32])
        self.assertEqual(variants[3].reason, "reduced, for a stated test")
        self.assertEqual(variants[0].reason, "none")
        layouts = self.tool.read_layouts(text)
        self.assertEqual(layouts[(2, 16, 64)].nonce, (4, 5))
        self.assertEqual(layouts[(4, 32, 256)].capacity, tuple(range(24, 32)))
        limits = self.tool.read_limits(text, variants[:3])
        self.assertEqual((limits.keys, limits.instantiations, limits.calls, limits.per_key),
                         (2 ** 20, 2 ** 20, 2 ** 24, 2 ** 44))
        self.assertEqual(limits.per_size[(self.tool.PER_REQUEST, 8)], (138, 524288))

    def refused(self, text: str, reader=None):
        reader = reader or self.tool.read_variants
        with self.assertRaises(evidence.Refused):
            if reader is self.tool.read_limits:
                reader(text, self.tool.read_variants(stated_design())[:3])
            else:
                reader(text)

    def test_a_table_missing_or_twice_is_refused(self):
        self.refused(stated_design(variants="no table\n"))
        self.refused(stated_design(variants=STATED_VARIANTS + "\n" + STATED_VARIANTS))
        self.refused(stated_design(layout="no table\n"), self.tool.read_layouts)
        self.refused(stated_design(layout=STATED_LAYOUT + "\n" + STATED_LAYOUT), self.tool.read_layouts)
        self.refused(stated_design(limits="no table\n"), self.tool.read_limits)
        self.refused(stated_design(limits=STATED_LIMITS + "\n" + STATED_LIMITS), self.tool.read_limits)

    def test_a_section_or_chapter_named_twice_is_refused(self):
        self.refused(stated_design() + "\n## Permutation\n")
        self.refused(stated_design() + "\n### Variant table\n")
        self.refused(stated_design().replace("## Permutation", "## Other"))
        self.refused(stated_design().replace("### Variant table", "### Other"))

    def test_a_heading_in_fenced_code_is_no_heading(self):
        self.assertEqual(len(self.tool.read_variants(stated_design() + "\n```\n## Permutation\n```\n")), 5)
        text = stated_design() + "\n~~~\n### Variant table\n~~~\n"
        self.assertEqual(len(self.tool.read_variants(text)), 5)

    def test_a_heading_of_another_level_is_not_the_chapter(self):
        self.assertEqual(len(self.tool.read_variants(stated_design() + "\n### Permutation\n")), 5)

    def test_a_fence_closes_only_with_its_own_mark(self):
        self.assertEqual(len(self.tool.read_variants(stated_design() + "\n```\n~~~\n## Permutation\n```\n")), 5)

    def test_a_section_ends_at_the_next_heading_of_its_level(self):
        moved = stated_design(variants="| not a table |\n") + "\n### Other\n\n" + STATED_VARIANTS
        self.refused(moved)
        beyond = stated_design(variants="| not a table |\n") + "\n## Other\n\n" + STATED_VARIANTS
        self.refused(beyond)
        self.assertEqual(self.tool.mode_sections(stated_design())[:2], ["Calls", "Layout"])

    def test_a_row_it_cannot_read_is_refused(self):
        row = "| phyco-v3/n4-w32-R20-c256 | 4 | 32 | 1,024 | 256 | 768 | 20 | claimable |"
        for wrong in ("| phyco-v3/n4-w32-R20-c256 | 4 | 32 | 1,024 | 256 | 768 | 20 |",
                      "| phyco-v3/n4-w32-R20 | 4 | 32 | 1,024 | 256 | 768 | 20 | claimable |",
                      "| phyco-v3/n4-w32-R20-c256 | 8 | 32 | 1,024 | 256 | 768 | 20 | claimable |",
                      "| phyco-v3/n4-w32-R20-c256 | 4 | 16 | 1,024 | 256 | 768 | 20 | claimable |",
                      "| phyco-v3/n4-w32-R20-c256 | 4 | 32 | 1,024 | 128 | 768 | 20 | claimable |",
                      "| phyco-v3/n4-w32-R21-c256 | 4 | 32 | 1,024 | 256 | 768 | 20 | claimable |",
                      "| phyco-v3/n4-w32-R20-c256 | 4 | 32 | 1,024 | 256 | 768 | twenty | claimable |",
                      "| phyco-v3/n4-w32-R20-c256 | 4 | 32 | 1,000 | 256 | 744 | 20 | claimable |",
                      "| phyco-v3/n4-w32-R20-c256 | 4 | 32 | 1,024 | 256 | 700 | 20 | claimable |",
                      "| phyco-v3/n4-w32-R20-c0 | 4 | 32 | 1,024 | 0 | 1,024 | 20 | claimable |",
                      "| phyco-v3/n4-w32-R20-c1024 | 4 | 32 | 1,024 | 1,024 | 0 | 20 | claimable |",
                      "| phyco-v3/n4-w32-R20-c256 | 4 | 32 | 1,024 | 256 | 768 | 20 | production |",
                      "| phyco-v3/n4-w32-R20-c256 | four | 32 | 1,024 | 256 | 768 | 20 | claimable |"):
            self.refused(stated_design(variants=STATED_VARIANTS.replace(row, wrong)))
        self.refused(stated_design(variants=STATED_VARIANTS + row + "\n"))

    def test_a_layout_row_it_cannot_read_is_refused(self):
        row = "| 4×4 | 32 | 256 | 0-23 | 24-31 | 0-7 | 8-11 |"
        for wrong in ("| 4x4 | 32 | 256 | 0-23 | 24-31 | 0-7 | 8-11 |", "| 4×8 | 32 | 256 | 0-23 | 24-31 | 0-7 | 8-11 |",
                      "| 4×4 | 32 | 256 | 0-23 | 24-32 | 0-7 | 8-11 |", "| 4×4 | 32 | 256 | 0-23 | 24-31 | 7-0 | 8-11 |",
                      "| 4×4 | 32 | 256 | 0-23 | 24-31 | 0-7,7 | 8-11 |", "| 4×4 | 32 | 256 | a | 24-31 | 0-7 | 8-11 |",
                      "| 4×4 | 32 | 256 | 0-23/0 | 24-31 | 0-7 | 8-11 |"):
            self.refused(stated_design(layout=STATED_LAYOUT.replace(row, wrong)), self.tool.read_layouts)
        self.refused(stated_design(layout=STATED_LAYOUT + row + "\n"), self.tool.read_layouts)

    def test_lane_sets_read_as_written(self):
        self.assertEqual(self.tool.lane_set("1-7/2, 8", 16, "here"), (1, 3, 5, 7, 8))
        self.assertEqual(self.tool.lane_set("none", 16, "here"), ())
        self.assertEqual(self.tool.lane_set("15", 16, "here"), (15,))
        with self.assertRaises(evidence.Refused):
            self.tool.lane_set("16", 16, "here")

    def test_a_limits_row_it_cannot_read_is_refused(self):
        self.refused(stated_design(limits=STATED_LIMITS + "| keys u | all | 2^20 | none |\n"), self.tool.read_limits)
        self.refused(stated_design(limits=STATED_LIMITS + "| calls of Π per key | 4×4 | 2^44 | 1 |\n"), self.tool.read_limits)
        self.refused(stated_design(limits=STATED_LIMITS + "| another limit | all | 1 | none |\n"), self.tool.read_limits)
        self.refused(stated_design(limits=STATED_LIMITS + "| calls of Π per key | 2×2 | 2^44 | 1 |\n"), self.tool.read_limits)
        self.refused(stated_design(limits=STATED_LIMITS.replace("| keys u | all | 2^20 | none |\n", "")), self.tool.read_limits)
        self.refused(stated_design(limits=STATED_LIMITS.replace("| calls of Π per request | 8×8 | 138 | 524,288 |\n", "")),
                     self.tool.read_limits)
        self.refused(stated_design(limits=STATED_LIMITS.replace("| keys u | all | 2^20 |", "| keys u | all | many |")),
                     self.tool.read_limits)
        self.refused(stated_design(limits=STATED_LIMITS.replace("| 16×16 | 2^24 |", "| 16×16 | 2^25 |")), self.tool.read_limits)
        self.refused(stated_design(limits=STATED_LIMITS.replace("| 16×16 | 2^44 |", "| 16×16 | 2^45 |")), self.tool.read_limits)

    def test_a_table_with_no_separator_or_no_rows_is_refused(self):
        lines = STATED_VARIANTS.splitlines()
        self.refused(stated_design(variants="\n".join(lines[:1] + lines[2:]) + "\n"))
        self.refused(stated_design(variants="\n".join(lines[:2]) + "\n"))


class ModeLimitsArithmetic(unittest.TestCase):
    """Each count and each term of Theorem 1, against a small case worked by hand (T067)."""

    def setUp(self):
        self.tool = limits_script()

    def test_the_calls_of_an_input_and_a_request(self):
        self.assertEqual([self.tool.input_blocks(n, 64) for n in (0, 1, 4, 5, 8, 9)], [1, 2, 2, 3, 3, 4])
        self.assertEqual(self.tool.input_blocks(4096, 768), 45)
        self.assertEqual(self.tool.input_blocks(4096, 16128), 3)
        self.assertEqual(self.tool.input_blocks(88, 768), 1)
        self.assertEqual(self.tool.input_blocks(89, 768), 2)
        variant = self.tool.read_variants(stated_design())[0]
        self.assertEqual(self.tool.request_calls(2 ** 19, variant), 684)
        self.assertEqual(self.tool.request_calls(768, variant), 2)
        self.assertEqual(self.tool.request_calls(769, variant), 3)

    def test_a_forget_takes_as_many_calls_as_c_needs(self):
        base = small_variant()
        self.assertEqual(self.tool.forget_calls(base), 1)
        self.assertEqual(self.tool.forget_calls(base._replace(c=256, r=128)), 2)
        self.assertEqual(self.tool.forget_calls(base._replace(c=257, r=128)), 3)

    def test_what_is_keyed(self):
        base = small_variant()
        self.assertTrue(self.tool.keyed(base))
        self.assertFalse(self.tool.keyed(base._replace(c=32, r=96)))
        self.assertFalse(self.tool.keyed(base._replace(c=64, r=92, b=156)), "r is no multiple of 32, with room to spare")
        self.assertFalse(self.tool.keyed(base._replace(c=96, r=128, b=224)), "c is no multiple of 64, with room to spare")
        self.assertFalse(self.tool.keyed(base._replace(c=64, r=32, b=96)))
        self.assertTrue(self.tool.keyed(base._replace(c=64, r=224, b=288)))
        self.assertFalse(self.tool.keyed(base._replace(c=128, r=64, b=192)), "no room for the key, the nonce and a word")
        self.assertTrue(self.tool.keyed(base._replace(c=128, r=96, b=224)))
        self.assertFalse(self.tool.keyed(base._replace(c=128, r=95, b=223)))

    def test_the_multicollision_limit_on_small_cases(self):
        self.assertEqual(self.tool.multicollision_limit(194, 64, 64), 2)
        self.assertEqual(self.tool.multicollision_limit(2, 64, 62), 1)
        self.assertEqual(self.tool.multicollision_limit(2, 64, 64), 1)
        self.assertEqual(self.tool.multicollision_limit(3, 64, 64), 2)
        self.assertEqual(self.tool.multicollision_limit(2 ** 65, 768, 256), 1)
        self.assertEqual(self.tool.multicollision_limit(13, 8, 8), 2, "C(13, 3) 2^8 passes 2^16 and not 2 2^16")

    def test_each_term_on_a_small_case(self):
        have = {"M": 100, "Omega": 10, "q": 5, "q_iv": 2, "L": 3, "u": 2, "N": 7}
        terms = self.tool.theorem_terms(have, small_variant(), 3)
        self.assertEqual(terms, {
            "overwrites": Fraction(13 * 7, 2 ** 64), "multicollisions": Fraction(2 * 2 * 8, 2 ** 64),
            "repeated paths": Fraction(91, 2 ** 64), "initial states": Fraction(92 * 5, 2 ** 128 - 5),
            "state pairs": Fraction(100 * 96, 2 ** 128), "initial keys": Fraction(92 * 5, 2 ** 128),
            "key search": Fraction(2 * 7, 2 ** 64), "key pairs": Fraction(1, 2 ** 64),
            "nonce collisions": Fraction(2 * 9, 2 ** 129)})

    def test_the_second_term_counts_twice_the_paths(self):
        have = {"M": 100, "Omega": 10, "q": 5, "q_iv": 2, "L": 3, "u": 2, "N": 7}
        with mock.patch.object(self.tool, "multicollision_limit", return_value=2) as limit:
            self.tool.theorem_terms(have, small_variant(), 3)
        limit.assert_called_once_with(194, 64, 64)

    def test_min_of_c_and_b_minus_k_is_read(self):
        have = {"M": 100, "Omega": 10, "q": 5, "q_iv": 2, "L": 3, "u": 2, "N": 7}
        wide = small_variant()._replace(b=512, c=64, r=448)
        self.assertEqual(self.tool.theorem_terms(have, wide, 3)["initial keys"], Fraction(460, 2 ** 128))
        narrow = small_variant()._replace(b=96, c=64, r=32)
        self.assertEqual(self.tool.theorem_terms(have, narrow, 3)["initial keys"], Fraction(460, 2 ** 96))

    def test_the_resources_at_the_limits(self):
        variant = self.tool.read_variants(stated_design())[0]
        self.assertEqual(self.tool.resources(2 ** 20, 2 ** 20, 2 ** 24, variant),
                         {"M": 2 ** 64, "Omega": 2 ** 63, "q": 2 ** 40, "q_iv": 2 ** 20, "L": 0, "u": 2 ** 20, "N": 2 ** 128})
        tight = small_variant()._replace(c=256, r=128)
        self.assertEqual(self.tool.resources(1, 1, 3, tight)["Omega"], 2)

    def test_the_bound_at_the_stated_limits_worked_by_hand(self):
        """2^63 flagged calls over 2^128 give 2^-65, the nonces' term 2^-69, the rest under 2^-107."""
        out = self.tool.compute(stated_design(), [], ROOT)
        for variant, entry in out["limits"]["bound"].items():
            self.assertEqual(entry["log2_bound"], "-64.912537", variant)
            self.assertEqual(entry["terms_log2"]["overwrites"], "-65.000000")
            self.assertEqual(entry["terms_log2"]["nonce collisions"], "-69.000000")
            self.assertEqual(entry["terms_log2"]["key search"], "-108.000000")
            self.assertTrue(entry["at_most_target_advantage"])
            self.assertTrue(entry["theorem_condition"])
        self.assertTrue(out["held"])

    def test_doubling_each_limit_passes_the_target_advantage(self):
        out = self.tool.compute(stated_design(), [], ROOT)
        for variant, rows in out["limits"]["doubling"].items():
            self.assertEqual(set(rows), {self.tool.KEYS, self.tool.INSTANTIATIONS, self.tool.PER_INSTANTIATION, self.tool.PER_KEY})
            self.assertTrue(all(row["above_target_advantage"] for row in rows.values()), variant)
            self.assertEqual(rows[self.tool.KEYS]["log2_bound"], "-63.912537")
            self.assertEqual(rows[self.tool.PER_INSTANTIATION]["log2_bound"], "-63.955606")

    def test_each_doubling_doubles_its_own_limit(self):
        limits = self.tool.read_limits(stated_design(), self.tool.read_variants(stated_design())[:3])
        variant = self.tool.read_variants(stated_design())[0]
        with mock.patch.object(self.tool, "bound_at", return_value=Fraction(1)) as bound:
            self.tool.doubled(limits, variant)
        self.assertEqual([c.args[:3] for c in bound.call_args_list],
                         [(2 ** 21, 2 ** 20, 2 ** 24), (2 ** 20, 2 ** 21, 2 ** 24), (2 ** 20, 2 ** 20, 2 ** 25), (2 ** 20, 2 ** 20, 2 ** 25)])

    def test_limits_past_the_target_advantage_fail(self):
        text = stated_design()
        for name, value in (("calls", 2 ** 25), ("keys", 2 ** 21), ("instantiations", 2 ** 21)):
            limits = self.tool.read_limits(text, self.tool.read_variants(text)[:3])
            with mock.patch.object(self.tool, "read_limits", return_value=limits._replace(**{name: value})), \
                    mock.patch.object(self.tool, "table_faults", return_value=[]):
                out = self.tool.compute(text, [], ROOT)
            self.assertFalse(out["held"], name)
            self.assertFalse(out["assertions"][0]["holds"], name)

    def test_a_limit_set_below_the_most_allowed_fails_the_doubling_check(self):
        text = stated_design()
        limits = self.tool.read_limits(text, self.tool.read_variants(text)[:3])
        with mock.patch.object(self.tool, "read_limits", return_value=limits._replace(calls=2 ** 22)), \
                mock.patch.object(self.tool, "table_faults", return_value=[]):
            out = self.tool.compute(text, [], ROOT)
        self.assertFalse(out["held"])
        entry = next(iter(out["limits"]["bound"].values()))
        self.assertTrue(entry["at_most_target_advantage"])

    def test_a_doubled_bound_under_the_target_advantage_fails_though_past_half_of_it(self):
        """At 2^23 calls the doubled bound is 2^-65 and a little: past half the target, and within it."""
        text = stated_design()
        limits = self.tool.read_limits(text, self.tool.read_variants(text)[:3])
        with mock.patch.object(self.tool, "read_limits", return_value=limits._replace(calls=2 ** 23)), \
                mock.patch.object(self.tool, "table_faults", return_value=[]):
            out = self.tool.compute(text, [], ROOT)
        rows = next(iter(out["limits"]["doubling"].values()))
        self.assertFalse(rows[self.tool.PER_INSTANTIATION]["above_target_advantage"])
        self.assertFalse(out["held"])

    def test_the_condition_on_n_plus_m_is_read(self):
        """At N = 2^253, 10 (N + M) passes 2^256, so that the theorem does not apply, whatever the bound
        reads. A target of 3 2^59 keeps the bound within it and its doubling past it, so that only this fails."""
        target = Fraction(3 * 2 ** 59)
        with mock.patch.object(self.tool, "OFFLINE_CALLS", 2 ** 253), mock.patch.object(self.tool, "TARGET_ADVANTAGE", target):
            out = self.tool.compute(stated_design(), [], ROOT)
        entry = next(iter(out["limits"]["bound"].values()))
        self.assertFalse(entry["theorem_condition"])
        self.assertTrue(entry["at_most_target_advantage"], "the bound alone would pass")
        self.assertTrue(all(row["above_target_advantage"] for row in next(iter(out["limits"]["doubling"].values())).values()))
        self.assertFalse(out["held"])
        with mock.patch.object(self.tool, "OFFLINE_CALLS", 2 ** 252), mock.patch.object(self.tool, "TARGET_ADVANTAGE", Fraction(2 ** 70)):
            out = self.tool.compute(stated_design(), [], ROOT)
        self.assertTrue(next(iter(out["limits"]["bound"].values()))["theorem_condition"], "10 2^252 is under 2^256")

    def test_the_table_faults_are_each_found(self):
        text = stated_design()
        claimable = self.tool.read_variants(text)[:3]
        limits = self.tool.read_limits(text, claimable)
        self.assertEqual(self.tool.table_faults(limits, claimable), [])
        for change, word in (({"keys": 3}, "keys u"), ({"instantiations": 3}, "instantiations"), ({"calls": 3}, "per instantiation"),
                             ({"per_key": 3}, "per key"), ({"instantiations": 2 ** 33}, "most R9"),
                             ({"per_key": 2 ** 43}, "product"), ({"reseeds": 2 ** 25}, "reseeds")):
            self.assertTrue(any(word in fault for fault in self.tool.table_faults(limits._replace(**change), claimable)), change)
        wrong = dict(limits.per_size)
        for key, value, word in (((self.tool.PER_INSTANTIATION, 8), (2 ** 24, 1), "per instantiation at 8×8"),
                                 ((self.tool.PER_KEY, 16), (2 ** 44, 1), "per key at 16×16"),
                                 ((self.tool.PER_REQUEST, 4), (685, 2 ** 19), "per request at 4×4"),
                                 ((self.tool.PER_REQUEST, 4), (684, 2 ** 20), "per request at 4×4"),
                                 ((self.tool.PER_INSTANTIATE, 4), (45, 45 * 768), "per instantiate at 4×4"),
                                 ((self.tool.PER_INSTANTIATE, 4), (46, 1), "per instantiate at 4×4")):
            changed = dict(wrong)
            changed[key] = value
            self.assertTrue(any(word in fault for fault in self.tool.table_faults(limits._replace(per_size=changed), claimable)), key)
        with self.assertRaises(evidence.Refused):
            self.tool.compute(stated_design(limits=STATED_LIMITS.replace("| keys u | all | 2^20 |", "| keys u | all | 3 |")), [], ROOT)

    def test_the_cap_is_the_smaller_of_two_limits(self):
        text = stated_design()
        claimable = self.tool.read_variants(text)[:3]
        limits = self.tool.read_limits(text, claimable)
        small = dict(limits.per_size)
        for v in claimable:
            small[(self.tool.PER_INSTANTIATION, v.n)] = (64, 64 * v.r)
            small[(self.tool.PER_KEY, v.n)] = (64 * 2 ** 20, 64 * 2 ** 20 * v.r)
        faults = self.tool.table_faults(limits._replace(calls=64, per_key=64 * 2 ** 20, reseeds=64, per_size=small), claimable)
        self.assertTrue(any("per request at 4×4" in fault for fault in faults), "64 calls of 768 bits are under the cap")
        self.assertFalse(any("per request at 16×16" in fault for fault in faults), "64 calls of 16,128 bits are over it")

    def test_the_log_prints_exactly(self):
        self.assertEqual(self.tool.log2_of(Fraction(1, 8)), "-3.000000")
        self.assertEqual(self.tool.log2_of(Fraction(0)), "-inf")
        self.assertEqual(self.tool.power(2 ** 24), "2^24")
        self.assertEqual(self.tool.power(684), "684")
        self.assertEqual(self.tool.power(0), "0")


class ModeLimitsProfile(unittest.TestCase):
    """FR-009 and FR-010's checks, computed by code, and each row's bound with its terms (T067)."""

    def setUp(self):
        self.tool = limits_script()
        self.out = self.tool.compute(stated_design(), [], ROOT)
        self.rows = {row["variant_id"]: row for row in self.out["parameters"]["rows"]}

    def test_a_row_for_every_variant(self):
        self.assertEqual(len(self.rows), 5)
        row = self.rows["phyco-v3/n8-w32-R24-c256"]
        self.assertEqual((row["n"], row["w"], row["lanes_per_node"], row["b"], row["c"], row["r"], row["R"]), (8, 32, 2, 4096, 256, 3840, 24))
        self.assertEqual(row["status"], "claimable")
        self.assertEqual(row["keyed_variants"], ["phyco-v3/n8-w32-R24-c256"])
        self.assertEqual(self.rows["phyco-v3/n2-w4-R8-c16"]["keyed_variants"], ["phyco-v3/n2-w16-R8-c64"])
        self.assertEqual(self.rows["phyco-v3/n2-w16-R8-c64"]["R_reason"], "reduced, for a stated test")

    def test_a_claimable_row(self):
        row = self.rows["phyco-v3/n4-w32-R20-c256"]
        self.assertEqual((row["key_entropy_bits"], row["nonce_bits"]), (256, 128))
        self.assertEqual(row["reachable_secret_state_bits"], {"after_instantiate": 256, "after_generate": 256, "after_reseed": 256,
                                                              "basis": "by specification"})
        self.assertEqual(row["bound_bits"], 128)
        self.assertEqual(row["bound_terms"], {"key entropy": 256, "half the reachable secret state": 128, "multi-target": 236,
                                              "half of key and nonce": 192, "half the capacity": 128,
                                              "single-target quantum search": 128,
                                              "sets": ["half the capacity", "half the reachable secret state", "single-target quantum search"]})
        self.assertEqual(row["level_checked"], 128)
        self.assertTrue(row["quantum_met_with_equality"])
        self.assertEqual(row["violations"], [])
        self.assertEqual(row["bound_label"], "target, not a claim")
        self.assertEqual((row["rate_lanes"], row["capacity_lanes"], row["forget_calls"]), (24, 8, 1))
        self.assertTrue(all(row["checks"].values()))

    def test_a_keyed_reduced_row_is_checked_at_half_its_capacity(self):
        row = self.rows["phyco-v3/n2-w16-R8-c64"]
        self.assertEqual((row["key_entropy_bits"], row["nonce_bits"], row["level_checked"], row["bound_bits"]), (64, 32, 32, 32))
        self.assertEqual(row["bound_terms"]["multi-target"], 44)
        self.assertEqual(row["bound_terms"]["half of key and nonce"], 48)
        self.assertEqual(row["bound_label"], "research variant, no claim")
        self.assertEqual(row["checks"]["output volume"], "none")
        self.assertEqual(row["violations"], [])

    def test_a_keyless_row_has_no_bound(self):
        row = self.rows["phyco-v3/n2-w4-R8-c16"]
        self.assertEqual((row["key_entropy_bits"], row["nonce_bits"], row["bound_bits"], row["bound_terms"], row["checks"]),
                         (0, 0, "none", "none", "none"))
        self.assertEqual(row["bound_label"], "keyless: permutation only")
        self.assertEqual(row["reachable_secret_state_bits"], "none")

    def test_a_term_below_zero_counts_as_zero(self):
        text = stated_design(limits=STATED_LIMITS)
        limits = self.tool.read_limits(text, self.tool.read_variants(text)[:3])._replace(keys=2 ** 70)
        v = self.tool.read_variants(text)
        row = self.tool.profile_row(v[3], self.tool.read_layouts(text), limits, v, True, None)
        self.assertEqual(row["bound_terms"]["multi-target"], 0)
        self.assertEqual(row["bound_bits"], 0)
        self.assertEqual(row["bound_terms"]["sets"], ["multi-target"])
        self.assertIn("multi-target", row["violations"])

    def test_each_check_can_fail_at_a_claimable_size(self):
        text = stated_design()
        variants = self.tool.read_variants(text)
        limits = self.tool.read_limits(text, variants[:3])
        v = variants[0]
        layouts = self.tool.read_layouts(text)
        shrunk = v._replace(c=64, r=960)
        wide = dict(layouts)
        wide[(4, 32, 64)] = self.tool.Layout(4, 32, 64, tuple(range(30)), (30, 31), (0, 1), (2,))
        row = self.tool.profile_row(shrunk, wide, limits, variants, True, True)
        self.assertEqual(row["violations"], ["capacity", "key and nonce", "key entropy", "multi-target", "quantum search",
                                             "reachable secret state"])
        half = v._replace(c=128, r=896)
        wide[(4, 32, 128)] = self.tool.Layout(4, 32, 128, tuple(range(28)), tuple(range(28, 32)), tuple(range(4)), (4, 5))
        row = self.tool.profile_row(half, wide, limits, variants, True, True)
        self.assertEqual(row["violations"], ["capacity", "key and nonce", "multi-target", "quantum search", "reachable secret state"],
                         "a key of 128 bits meets the level; c, key and nonce, and the quantum check need twice it")
        row = self.tool.profile_row(v, layouts, limits._replace(keys=2 ** 129), variants, True, True)
        self.assertEqual(row["violations"], ["multi-target"])
        self.assertEqual(self.tool.profile_row(v, layouts, limits, variants, False, True)["violations"], ["nonce reuse stated"])
        self.assertEqual(self.tool.profile_row(v, layouts, limits, variants, True, False)["violations"], ["output volume"])

    def test_the_secret_state_is_counted_from_the_layout(self):
        text = stated_design()
        variants = self.tool.read_variants(text)
        limits = self.tool.read_limits(text, variants[:3])
        layouts = dict(self.tool.read_layouts(text))
        layouts[(4, 32, 256)] = layouts[(4, 32, 256)]._replace(capacity=(28, 29, 30, 31))
        row = self.tool.profile_row(variants[0], layouts, limits, variants, True, True)
        self.assertEqual(row["reachable_secret_state_bits"]["after_generate"], 128)
        self.assertEqual(row["bound_bits"], 64)
        self.assertIn("reachable secret state", row["violations"])

    def test_a_missing_nonce_section_is_refused_before_any_check(self):
        """A precondition of the theorem names it, so the run stops there; the check itself is shown above."""
        with self.assertRaises(evidence.Refused) as caught:
            self.tool.compute(stated_design().replace("### Nonce reuse\n\n", ""), [], ROOT)
        self.assertIn("Nonce reuse", str(caught.exception))

    def test_a_violation_at_a_claimable_size_fails_the_run(self):
        text = stated_design()
        with mock.patch.object(self.tool, "mode_sections", return_value=["Calls", "Layout", "Key loading", "Padding and domain separation",
                                                                          "Forget", "Serialization", "Limits", "Nonce"]), \
                mock.patch.object(self.tool, "theorem_entries", return_value=[]):
            out = self.tool.compute(text, [], ROOT)
        self.assertFalse(out["held"])
        self.assertFalse(out["assertions"][1]["holds"])
        self.assertTrue(out["assertions"][0]["holds"])

    def test_a_layout_outside_the_theorems_form_is_a_violation(self):
        for wrong in ("| 4×4 | 32 | 256 | 8-31 | 0-7 | 8-15 | 16-19 |", "| 4×4 | 32 | 256 | 0-23 | 24-31 | 24-31 | 8-11 |",
                      "| 4×4 | 32 | 256 | 0-23 | 24-31 | 0-7 | 12-15 |", "| 4×4 | 32 | 256 | 0-22 | 23-31 | 0-7 | 8-11 |",
                      "| 4×4 | 32 | 256 | 0-22 | 24-31 | 0-7 | 8-11 |"):
            out = self.tool.compute(stated_design(layout=STATED_LAYOUT.replace("| 4×4 | 32 | 256 | 0-23 | 24-31 | 0-7 | 8-11 |", wrong)), [], ROOT)
            self.assertFalse(out["held"], wrong)

    def test_a_keyed_variant_needs_a_layout_row(self):
        text = stated_design(layout=STATED_LAYOUT.replace("| 2×2 | 16 | 64 | 0-3 | 4-7 | 0-3 | 4,5 |\n", ""))
        with self.assertRaises(evidence.Refused):
            self.tool.compute(text, [], ROOT)

    def test_no_claimable_size_is_refused(self):
        with self.assertRaises(evidence.Refused) as caught:
            self.tool.compute(stated_design().replace("| claimable |", "| research |"), [], ROOT)
        self.assertIn("no claimable size", str(caught.exception))

    def test_a_research_row_fails_nothing(self):
        text = stated_design(layout=STATED_LAYOUT.replace("| 2×2 | 16 | 64 | 0-3 | 4-7 | 0-3 | 4,5 |", "| 2×2 | 16 | 64 | 0-3 | 4-7 | 0-3 | 6,7 |"))
        out = self.tool.compute(text, [], ROOT)
        self.assertTrue(out["held"])
        row = [r for r in out["parameters"]["rows"] if r["n"] == 2 and r["w"] == 16][0]
        self.assertTrue(row["violations"])


class ModeLimitsTheorems(unittest.TestCase):
    """`verified` needs the paper's `fetched` entry and its file on disk (FR-012; R10)."""

    def setUp(self):
        self.tool = limits_script()
        self.sections = self.tool.mode_sections(stated_design())

    def test_both_are_unverified_until_the_review(self):
        entries = self.tool.theorem_entries([], ROOT, self.sections)
        self.assertEqual([e["status"] for e in entries], ["unverified", "unverified"])
        self.assertEqual(entries[0]["fetched_sha256"], "none")
        self.assertTrue(all(not row["met"] for e in entries for row in e["preconditions"]))

    def test_a_fetched_entry_is_cited_by_its_hash(self):
        manifest = [{"name": "Daemen.pdf", "status": "fetched", "sha256": "ab", "local_path": "x"},
                    {"name": "169.pdf", "status": "approved"}]
        entries = self.tool.theorem_entries(manifest, ROOT, self.sections)
        self.assertEqual([e["fetched_sha256"] for e in entries], ["ab", "none"])

    def mark(self, status="verified"):
        marked = [dict(self.tool.THEOREMS[0], status=status)]
        return mock.patch.object(self.tool, "THEOREMS", tuple(marked))

    def test_verified_needs_a_fetched_entry(self):
        for manifest in ([], [{"name": "Daemen.pdf", "status": "approved"}]):
            with self.mark(), self.assertRaises(evidence.Refused):
                self.tool.theorem_entries(manifest, ROOT, self.sections)

    def test_verified_needs_the_file_on_disk_with_its_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "paper.pdf"
            path.write_bytes(b"the paper")
            entry = {"name": "Daemen.pdf", "status": "fetched", "sha256": hashlib.sha256(b"the paper").hexdigest(), "local_path": str(path)}
            with self.mark():
                out = self.tool.theorem_entries([entry], ROOT, self.sections)
            self.assertEqual(out[0]["status"], "verified")
            self.assertTrue(all(row["met"] for row in out[0]["preconditions"]))
            with self.mark(), self.assertRaises(evidence.Refused):
                self.tool.theorem_entries([dict(entry, sha256="00")], ROOT, self.sections)
            path.unlink()
            with self.mark(), self.assertRaises(evidence.Refused):
                self.tool.theorem_entries([entry], ROOT, self.sections)

    def test_a_path_with_backslashes_reads_as_the_manifest_writes_it(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "sub").mkdir()
            (Path(folder) / "sub" / "paper.pdf").write_bytes(b"x")
            entry = {"name": "Daemen.pdf", "status": "fetched", "sha256": hashlib.sha256(b"x").hexdigest(), "local_path": "sub\\paper.pdf"}
            with self.mark():
                self.assertEqual(self.tool.theorem_entries([entry], Path(folder), self.sections)[0]["status"], "verified")

    def test_another_status_is_refused(self):
        with self.mark("accepted"), self.assertRaises(evidence.Refused):
            self.tool.theorem_entries([], ROOT, self.sections)

    def test_a_precondition_names_a_section_of_the_mode_chapter(self):
        self.assertEqual({row[1] for t in self.tool.THEOREMS for row in t["preconditions"]} - set(self.sections), set())
        with self.assertRaises(evidence.Refused):
            self.tool.theorem_entries([], ROOT, self.sections[1:])


class ModeLimitsCommand(unittest.TestCase):
    """The command line, the two fixed names and the exit statuses (cli contract)."""

    def setUp(self):
        self.tool = limits_script()

    def test_out_is_the_fixed_name_only(self):
        with mock.patch("sys.stderr", new=io.StringIO()) as err:
            self.assertEqual(self.tool.main(["--out", "elsewhere/limits.json"]), evidence.EXIT_REFUSED)
        self.assertIn("--out must be", err.getvalue())

    def test_no_design_document_is_refused(self):
        wanted = str(evidence.REPO.rep / "security-target" / "limits.json")
        with mock.patch.object(self.tool.evidence, "DESIGN_REL", "specs/none/design.md"), mock.patch("sys.stderr", new=io.StringIO()) as err:
            self.assertEqual(self.tool.main(["--out", wanted]), evidence.EXIT_REFUSED)
        self.assertIn("does not exist", err.getvalue())

    def test_a_mode_is_needed_and_one_only(self):
        with mock.patch("sys.stderr", new=io.StringIO()), self.assertRaises(SystemExit):
            self.tool.main([])
        with mock.patch("sys.stderr", new=io.StringIO()), self.assertRaises(SystemExit):
            self.tool.main(["--out", "a", "--reproduce", "b"])

    def test_a_reproduction_needs_a_file_of_its_kind(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "other.json"
            path.write_text('{"kind": "validation"}', encoding="utf-8")
            with mock.patch("sys.stderr", new=io.StringIO()) as err:
                self.assertEqual(self.tool.main(["--reproduce", str(path)]), evidence.EXIT_REFUSED)
            self.assertIn("no size profile", err.getvalue())
            with mock.patch("sys.stderr", new=io.StringIO()):
                self.assertEqual(self.tool.main(["--reproduce", str(path) + ".none"]), evidence.EXIT_REFUSED)

    def fake_run(self, seen):
        class Fake:
            def __init__(self, name):
                self.name = name

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def finish(self, status, **kwargs):
                seen.append((self.name, status, kwargs))
                return evidence.REPO.rep / "security-target" / self.name
        return Fake

    def test_both_files_are_written_each_under_its_name(self):
        seen = []
        result = self.tool.compute(stated_design(), [], ROOT)
        fake = self.fake_run(seen)
        with mock.patch.object(self.tool, "fixed_run", side_effect=lambda name, _: fake(name)), mock.patch("sys.stdout", new=io.StringIO()):
            self.assertEqual(self.tool.write(result, ["x"]), evidence.EXIT_OK)
        self.assertEqual([(name, status) for name, status, _ in seen], [("parameters.json", "pass"), ("limits.json", "pass")])
        self.assertIn("rows", seen[0][2]["fields"])
        self.assertIn("epsilon", seen[1][2]["fields"])
        self.assertEqual(seen[1][2]["exit_status"], evidence.EXIT_OK)

    def test_a_failure_writes_its_verdict_and_exits_one(self):
        seen = []
        result = dict(self.tool.compute(stated_design(), [], ROOT), held=False)
        fake = self.fake_run(seen)
        with mock.patch.object(self.tool, "fixed_run", side_effect=lambda name, _: fake(name)), mock.patch("sys.stdout", new=io.StringIO()):
            self.assertEqual(self.tool.write(result, ["x"]), evidence.EXIT_VERDICT)
        self.assertEqual([status for _, status, _ in seen], ["fail", "fail"])
        self.assertEqual(seen[1][2]["exit_status"], evidence.EXIT_VERDICT)

    def test_the_limits_file_holds_what_section_10_names(self):
        fields = self.tool.compute(stated_design(), [], ROOT)["limits"]
        for name in ("epsilon", "N", "theorems", "u", "per_instantiation", "per_key", "per_request", "other_limits", "nonces",
                     "bound", "doubling"):
            self.assertIn(name, fields)
        self.assertEqual(fields["per_instantiation"]["bits"]["phyco-v3/n4-w32-R20-c256"], 2 ** 24 * 768)
        self.assertEqual(fields["per_key"]["calls"], "2^44")
        self.assertEqual(fields["nonces"]["collision_term"], "q^2/2^129")
        self.assertEqual(fields["per_request"]["phyco-v3/n16-w32-R32-c256"], {"calls": 34, "bits": 2 ** 19})
        self.assertEqual(set(fields), set(self.tool.LIMITS_FIELDS))


DESIGN_FILE = ROOT / "specs/004-crypto-architecture-v3/design.md"
RATIONALE_FILE = ROOT / "specs/004-crypto-architecture-v3/rationale.md"
LIMITS_FILE = ROOT / REPORTS / "security-target/limits.json"
PROFILE_FILE = ROOT / REPORTS / "security-target/parameters.json"
DESIGN_CHAPTERS = ("Security target", "Mode", "Permutation", "Hardware structure", "Replaced mechanisms", "Slime-mould mapping")
RATIONALE_CHAPTERS = ("Security target", "Mode", "Components", "Nonlinearity", "Diffusion", "Constants", "Margin", "Attack classes",
                      "Network questions", "Alternatives")
NAMED_SECTIONS = {"Mode": ("Key loading", "Diffusion through instantiation", "Layout", "Limits"),
                  "Permutation": ("Variant table", "Inverse", "Network questions"), "Hardware structure": ("Self-test",)}
K_COLUMNS = ("Variant", "k", "Structure", "Named structure and reason")
PARAMETER_COLUMNS = ("Variant", "n", "w", "b", "c", "r", "R", "Key entropy", "Reachable secret state", "Bound", "Status")
OUTPUT_COLUMNS = ("Limit", "Size", "Calls of Π", "Bits")


STUB = "Not drafted yet."


def chapters_of(text: str) -> List[str]:
    tool = limits_script()
    return [title for _, level, title in tool.headings(text.split("\n")) if level == 2]


def drafted(text: str) -> List[str]:
    """The chapters that hold more than the stub line of a chapter still to come."""
    tool = limits_script()
    lines = text.split("\n")
    heads = tool.headings(lines)
    out = []
    for name in chapters_of(text):
        first, last = tool.span(heads, 2, name, 0, len(lines))
        if [line for line in lines[first + 1:last] if line.strip()] != [STUB]:
            out.append(name)
    return out


def header_of(text: str) -> List[str]:
    """The lines before the first chapter, blank ones left out."""
    lines = text.split("\n")
    first = next(line for line, level, _ in limits_script().headings(lines) if level == 2)
    return [line for line in lines[:first] if line.strip()]


class Chapters(unittest.TestCase):
    """FR-034's chapters, each once and in this order, and each named section in its chapter (T068).
    Both files hold every chapter from their first version, since FR-030's test needs the mapping
    chapter's heading: one still to come holds the stub line alone, and what names it waits."""

    def setUp(self):
        for path in (DESIGN_FILE, RATIONALE_FILE):
            if not path.exists():
                self.skipTest(f"{path.name} does not exist yet (T069, T071)")
        self.design = DESIGN_FILE.read_bytes().decode("utf-8")
        self.rationale = RATIONALE_FILE.read_bytes().decode("utf-8")

    def test_the_design_documents_chapters_stand_in_order(self):
        self.assertEqual(chapters_of(self.design), list(DESIGN_CHAPTERS))

    def test_the_rationales_chapters_stand_in_order(self):
        self.assertEqual(chapters_of(self.rationale), list(RATIONALE_CHAPTERS))

    def test_the_first_two_chapters_of_each_are_drafted(self):
        self.assertEqual(drafted(self.design)[:2], ["Security target", "Mode"])
        self.assertEqual(drafted(self.rationale)[:2], ["Security target", "Mode"])

    def test_every_chapter_is_drafted(self):
        if len(drafted(self.design)) < len(DESIGN_CHAPTERS) or len(drafted(self.rationale)) < len(RATIONALE_CHAPTERS):
            self.skipTest("the later chapters are drafted from plan phase 6 on")
        self.assertEqual(drafted(self.design), list(DESIGN_CHAPTERS))
        self.assertEqual(drafted(self.rationale), list(RATIONALE_CHAPTERS))

    def test_a_stub_is_not_a_drafted_chapter(self):
        text = "# t\n\n## One\n\nwords\n\n## Two\n\nNot drafted yet.\n\n## Three\n\nNot drafted yet.\nmore\n"
        self.assertEqual(drafted(text), ["One", "Three"])

    def test_each_named_section_stands_once_in_its_chapter(self):
        tool = limits_script()
        lines = self.design.split("\n")
        heads = tool.headings(lines)
        present = drafted(self.design)
        for chapter, sections in NAMED_SECTIONS.items():
            if chapter in present:
                first, last = tool.span(heads, 2, chapter, 0, len(lines))
                for section in sections:
                    tool.span(heads, 3, section, first, last)

    def test_the_tables_stand_once_each_and_read(self):
        tool = limits_script()
        present = drafted(self.design)
        tool.read_table(tool.section_lines(self.design, "Mode", "Layout"), tool.LAYOUT_COLUMNS, "layout")
        tool.read_table(tool.section_lines(self.design, "Mode", "Limits"), tool.LIMIT_COLUMNS, "limits")
        if "Permutation" in present:
            tool.read_table(tool.section_lines(self.design, "Permutation", "Variant table"), tool.VARIANT_COLUMNS, "variants")
        if "Hardware structure" in present:
            tool.read_table(tool.section_lines(self.design, "Hardware structure", "Self-test"), K_COLUMNS, "k")

    def test_each_header_holds_its_title_disclaimer_and_version_only(self):
        for name, text in (("design", self.design), ("rationale", self.rationale)):
            header = header_of(text)
            self.assertTrue(header[0].startswith("# "), name)
            self.assertRegex(header[-1], r"^Version: 0\.\d+$", name)
            body = " ".join(line.lstrip("> ").strip() for line in header[1:-1])
            self.assertEqual(body, DESIGN_DISCLAIMER, name)

    def test_the_two_versions_are_equal(self):
        self.assertEqual(header_of(self.design)[-1], header_of(self.rationale)[-1])


class PaddingInjective(unittest.TestCase):
    """FR-014's committed check: every input length from 0 to its maximum and every call type, at each
    keyed rate, with 0 collisions, and distinct development inputs giving distinct block sequences."""
    RATES = (64, 224, 768, 3840, 16128)
    MOST = 4096

    def setUp(self):
        self.tool = limits_script()

    def test_every_length_and_call_type_gives_its_own_layout_at_each_rate(self):
        codes = (self.tool.PERSONALIZATION_BLOCK, self.tool.RESEED_BLOCK)
        for r in self.RATES:
            seen = {}
            for code in codes:
                for length in range(self.MOST + 1):
                    blocks = self.tool.absorbed_blocks(code, bytes(length), r)
                    digest = hashlib.sha256(b"".join(blocks)).digest()
                    self.assertNotIn(digest, seen, (r, code, length, seen.get(digest)))
                    seen[digest] = (code, length)
            self.assertEqual(len(seen), 2 * (self.MOST + 1))

    def test_every_length_reads_back_at_each_rate(self):
        for r in self.RATES:
            for length in list(range(0, 300)) + [self.MOST - 1, self.MOST]:
                data = bytes((i * 7 + 1) % 251 for i in range(length))
                blocks = self.tool.absorbed_blocks(self.tool.RESEED_BLOCK, data, r)
                code, read, count = self.tool.decoded_input(blocks + [self.tool.control_block(self.tool.FORGET_BLOCK, r)])
                self.assertEqual((code, read, count), (self.tool.RESEED_BLOCK, data, len(blocks)), (r, length))

    def test_a_blocks_shape_and_count_are_the_chapters(self):
        for r in self.RATES:
            for length in (0, 1, 4, 5, 87, 88, 89, self.MOST):
                blocks = self.tool.absorbed_blocks(self.tool.PERSONALIZATION_BLOCK, bytes(length), r)
                self.assertEqual(len(blocks), self.tool.input_blocks(length, r), (r, length))
                self.assertTrue(all(len(block) == r // 8 for block in blocks))
                self.assertTrue(all(block[-4:] == b"\x01\0\0\0" for block in blocks))

    def test_the_encoding_on_a_small_case_by_hand(self):
        self.assertEqual(self.tool.absorbed_blocks(2, b"abcde", 96),
                         [b"\x05\0\0\0abcd\x02\0\0\0", b"e\0\0\0\0\0\0\0\x02\0\0\0"])
        self.assertEqual(self.tool.absorbed_blocks(1, b"", 64), [b"\0\0\0\0\x01\0\0\0"])
        self.assertEqual(self.tool.control_block(4, 96), bytes(8) + b"\x04\0\0\0")

    def test_the_four_domain_words_are_distinct_and_none_is_zero(self):
        codes = (self.tool.PERSONALIZATION_BLOCK, self.tool.RESEED_BLOCK, self.tool.GENERATE_BLOCK, self.tool.FORGET_BLOCK)
        self.assertEqual(sorted(codes), [1, 2, 3, 4])

    def test_a_trailing_zero_byte_changes_the_blocks(self):
        for r in self.RATES:
            self.assertNotEqual(self.tool.absorbed_blocks(1, b"ab", r), self.tool.absorbed_blocks(1, b"ab\0", r))

    def test_distinct_development_inputs_give_distinct_block_sequences(self):
        count = 100
        reseeds = list(devinputs_v3.load("dev", "reseed", ("dev",), count))
        strings = list(devinputs_v3.load("dev", "pers", ("dev",), count, m=32))
        short = list(devinputs_v3.load("dev", "pers", ("dev",), count, m=5))
        for r in self.RATES:
            for code, inputs in ((self.tool.RESEED_BLOCK, reseeds), (self.tool.PERSONALIZATION_BLOCK, strings + short)):
                sequences = {b"".join(self.tool.absorbed_blocks(code, data, r)) for data in inputs}
                self.assertEqual(len(sequences), len(set(inputs)), (r, code))
                self.assertEqual(len(set(inputs)), len(inputs), "the development inputs are distinct")

    def test_the_two_input_types_differ_on_one_input(self):
        for r in self.RATES:
            self.assertNotEqual(self.tool.absorbed_blocks(1, b"same", r), self.tool.absorbed_blocks(2, b"same", r))


class SecurityTargetFiles(unittest.TestCase):
    """T066: the two files hold data-model section 10's fields, the chapter restates them row by row
    and value by value, and each bound is recomputed from its terms (FR-010, FR-034; SEC-090)."""

    def setUp(self):
        for path in (LIMITS_FILE, PROFILE_FILE):
            if not path.exists():
                self.skipTest("the two files exist from T107 on, once the variant table holds every R")
        self.limits = json.loads(LIMITS_FILE.read_bytes().decode("utf-8"))
        self.profile = json.loads(PROFILE_FILE.read_bytes().decode("utf-8"))
        self.design = DESIGN_FILE.read_bytes().decode("utf-8")

    def test_each_row_holds_section_10s_fields(self):
        names = ("n", "w", "lanes_per_node", "b", "c", "r", "variant_id", "R", "key_entropy_bits", "nonce_bits", "keyed_variants",
                 "reachable_secret_state_bits", "bound_bits", "bound_terms", "status", "checks")
        for row in self.profile["rows"]:
            for name in names:
                self.assertIn(name, row, row["variant_id"])
            if row["status"] == "claimable":
                for name in ("throughput_implied", "throughput_goal", "rate_before_forget"):
                    self.assertIn(name, row, row["variant_id"])
                self.assertIsInstance(row["throughput_implied"], (int, float))

    def test_each_bound_is_recomputed_from_the_rows_other_fields(self):
        u = self.profile["u"]
        log_u = int(u.split("^")[1])
        for row in self.profile["rows"]:
            terms = row["bound_terms"]
            if terms == "none":
                self.assertEqual(row["bound_bits"], "none")
                self.assertEqual(row["key_entropy_bits"], 0)
                continue
            k, nonce, c = row["key_entropy_bits"], row["nonce_bits"], row["c"]
            secret = min(v for key, v in row["reachable_secret_state_bits"].items() if key != "basis")
            wanted = {"key entropy": k, "half the reachable secret state": secret // 2, "multi-target": max(k - log_u, 0),
                      "half of key and nonce": (k + nonce) // 2, "half the capacity": c // 2, "single-target quantum search": k // 2}
            self.assertEqual({key: terms[key] for key in wanted}, wanted, row["variant_id"])
            self.assertEqual(row["bound_bits"], min(wanted.values()))

    def test_the_chapters_parameter_table_restates_the_profile(self):
        tool = limits_script()
        table = tool.read_table(tool.section_lines(self.design, "Security target", "Parameter table"), PARAMETER_COLUMNS, "parameters")
        rows = {row["variant_id"]: row for row in self.profile["rows"]}
        self.assertEqual({row["Variant"] for row in table}, set(rows))
        for row in table:
            have = rows[row["Variant"]]
            secret = have["reachable_secret_state_bits"]
            secret = secret if secret == "none" else secret["after_generate"]
            self.assertEqual(tuple(row[name] for name in PARAMETER_COLUMNS[1:]),
                             tuple(str(value) for value in (have["n"], have["w"], have["b"], have["c"], have["r"], have["R"],
                                                            have["key_entropy_bits"], secret, have["bound_bits"], have["status"])))

    def test_the_chapters_output_limits_restate_the_limits_file(self):
        tool = limits_script()
        table = tool.read_table(tool.section_lines(self.design, "Security target", "Output limits"), OUTPUT_COLUMNS, "output limits")
        read = {(row["Limit"], row["Size"]): (row["Calls of Π"], row["Bits"]) for row in table}
        for variant, bits in self.limits["per_instantiation"]["bits"].items():
            size = f"{variant.split('-w')[0].split('/n')[1]}×{variant.split('-w')[0].split('/n')[1]}"
            self.assertEqual(read[("per instantiation", size)], (self.limits["per_instantiation"]["calls"], f"{bits:,}"))
            self.assertEqual(read[("per key", size)], (self.limits["per_key"]["calls"], f"{self.limits['per_key']['bits'][variant]:,}"))
            request = self.limits["per_request"][variant]
            self.assertEqual(read[("per request", size)], (str(request["calls"]), f"{request['bits']:,}"))


class RationaleValues(unittest.TestCase):
    """RAT-090: the rationale restates no value of either file: a citation holds them, and the three
    margins of its chapter "Margin" stand as FR-034's bullet states them."""
    SYMBOL = re.compile(r"(?<![\w-])(?:k|s|c|r|R|u|ε|N)\s*(?:=|≤|≥|<|>)\s*(?:\d|2\^|2⁻|2[⁰¹²³⁴⁵⁶⁷⁸⁹])")
    FIELD = re.compile(r"`?\b(?:key_entropy_bits|nonce_bits|reachable_secret_state_bits|bound_bits|epsilon)\b`?\s*(?:=|:|is)\s*\d")
    CITATION = re.compile(r"\(design document, chapter \"[^\"]+\"(?:, section \"[^\"]+\")?\)|\(record [\w-]+, SHA-256 [0-9a-f]{64}\)")

    def setUp(self):
        if not RATIONALE_FILE.exists():
            self.skipTest("rationale.md does not exist yet (T071)")
        self.text = RATIONALE_FILE.read_bytes().decode("utf-8")

    def findings(self, text: str) -> List[str]:
        tool = limits_script()
        lines = text.split("\n")
        heads = tool.headings(lines)
        skipped = range(0)
        if any(level == 2 and title == "Margin" for _, level, title in heads):
            skipped = range(*tool.span(heads, 2, "Margin", 0, len(lines)))
        out = []
        for number, line in enumerate(lines):
            if number in skipped:
                continue
            bare = self.CITATION.sub("", line)
            if self.SYMBOL.search(bare) or self.FIELD.search(bare):
                out.append(line)
        return out

    def test_no_line_writes_a_value_outside_a_citation(self):
        self.assertEqual(self.findings(self.text), [])

    def test_the_check_finds_a_value_and_passes_a_citation(self):
        self.assertTrue(self.findings("## Mode\n\nThe capacity is c = 256 here.\n"))
        self.assertTrue(self.findings("## Mode\n\nWe take ε ≤ 2⁻⁶⁴ throughout.\n"))
        self.assertTrue(self.findings("## Mode\n\n`bound_bits` = 128 at the size.\n"))
        self.assertEqual(self.findings("## Mode\n\nIts value (design document, chapter \"Mode\", section \"Limits\").\n"), [])
        self.assertEqual(self.findings("## Margin\n\nR = 20 at this size.\n"), [])
        self.assertTrue(self.findings("## Margin\n\nR = 20.\n\n## Other\n\nR = 20.\n"))


if __name__ == "__main__":
    unittest.main()
