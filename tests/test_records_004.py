"""Feature 004: tests of committed records and of the files whose hashes they hold (FR-053; research
R16, R18). Standard library only; these run from plan phase 1 on, so that a path missed later fails
as soon as the first record that cites it is committed."""
import gzip
import hashlib
import json
import subprocess
import unittest
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

from protocol import evidence
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


if __name__ == "__main__":
    unittest.main()
