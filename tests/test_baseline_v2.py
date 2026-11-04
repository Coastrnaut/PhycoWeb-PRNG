"""Feature 004: the phyco-v2 archive and the freezes before it (FR-042; SC-012; T035).

Every file under baseline/phyco-v2/ matches its MANIFEST.json SHA-256 and its live source, and every
frozen file of features 002 and 003 still hashes as recorded: as its freeze records it, with one
exception that the records themselves state. Feature 003 fixed protocol/batteries.py after its
attempt, before this feature's first commit, and recorded the new hash in rescore-parser-fix.json;
its freeze's commit still holds the frozen bytes. This file makes no security claim.
"""
import contextlib
import datetime
import hashlib
import importlib.util
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from protocol import battery_freeze, freeze

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "baseline/phyco-v2"
MANIFEST = ARCHIVE / "MANIFEST.json"
SCRIPT = ROOT / "scripts/archive_phyco_v2.py"
NAMED = ("phycoweb/model_v2.py", "phycoweb/lut.py", "fast/phyco_stream.c", "fast/lut_table.h",
         "specs/002-core-dynamics-redesign/design.md")
FREEZE_002 = ROOT / "reports/002-core-dynamics-redesign/attempt-1/freeze.json"
FREEZE_003 = ROOT / "reports/003-extended-batteries-calibration/attempt-1/freeze.json"
RESCORE_003 = ROOT / "reports/003-extended-batteries-calibration/attempt-1/rescore-parser-fix.json"
PARSER = "protocol/batteries.py"
PARSER_FIX = "6039c52"
FIRST_COMMIT = "801c6d7"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True).stdout


def load_script():
    spec = importlib.util.spec_from_file_location("archive_phyco_v2", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TheArchive(unittest.TestCase):

    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.entries = self.manifest["files"]

    def source_path(self, entry) -> str:
        return entry["source"].split("@", 1)[0]

    def test_it_holds_the_files_of_data_model_section_12(self):
        vectors = sorted(p.relative_to(ROOT).as_posix() for p in ROOT.glob("vectors/phyco-v2_*.hex"))
        self.assertEqual(len(vectors), 2)
        self.assertEqual(sorted(self.source_path(e) for e in self.entries),
                         sorted(NAMED + tuple(vectors)))

    def test_each_copy_matches_its_manifest_hash(self):
        for entry in self.entries:
            with self.subTest(path=entry["archive_path"]):
                self.assertEqual(sha256((ROOT / entry["archive_path"]).read_bytes()),
                                 entry["sha256"])

    def test_each_copy_matches_its_live_source_byte_for_byte(self):
        for entry in self.entries:
            with self.subTest(path=entry["archive_path"]):
                self.assertEqual((ROOT / entry["archive_path"]).read_bytes(),
                                 (ROOT / self.source_path(entry)).read_bytes())

    def test_each_copy_equals_its_blob_at_the_commit_it_names(self):
        for entry in self.entries:
            with self.subTest(path=entry["archive_path"]):
                path, commit = entry["source"].split("@", 1)
                self.assertEqual(git(ROOT, "show", f"{commit}:{path}"),
                                 (ROOT / entry["archive_path"]).read_bytes())

    def test_the_archive_holds_nothing_else(self):
        listed = {Path(e["archive_path"]).name for e in self.entries} | {"MANIFEST.json"}
        self.assertEqual({p.name for p in ARCHIVE.iterdir()}, listed)

    def test_the_manifest_holds_the_fields_of_float_v0s(self):
        self.assertEqual(sorted(self.manifest), ["created_utc", "files", "git_head"])
        datetime.datetime.fromisoformat(self.manifest["created_utc"])
        self.assertRegex(self.manifest["git_head"], r"^[0-9a-f]{40}$")
        for entry in self.entries:
            self.assertEqual(sorted(entry), ["archive_path", "note", "sha256", "source"])
            self.assertRegex(entry["source"], r"^[^@]+@[0-9a-f]{7,40}$")
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
            self.assertTrue(entry["note"])
            self.assertTrue(entry["archive_path"].startswith("baseline/phyco-v2/"))

    def test_the_manifests_commit_is_in_this_history(self):
        git(ROOT, "merge-base", "--is-ancestor", self.manifest["git_head"], "HEAD")

    def test_quickstart_p1(self):
        done = subprocess.run([sys.executable, str(SCRIPT), "--check"], cwd=ROOT,
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("0 mismatches", done.stdout)


class ArchiveScript(unittest.TestCase):
    """The script's refusals, on a small repository of its own."""

    def setUp(self):
        self.script = load_script()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "test@example.invalid")
        git(self.root, "config", "user.name", "test")
        git(self.root, "config", "core.autocrlf", "false")
        self.paths = NAMED + ("vectors/phyco-v2_a.hex", "vectors/phyco-v2_b.hex")
        for number, rel in enumerate(self.paths):
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"file {number}\r\nbytes stay as they are\n".encode("ascii"))
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "sources")
        patcher = mock.patch.multiple(self.script, ROOT=self.root,
                                      ARCHIVE=self.root / "baseline/phyco-v2",
                                      MANIFEST=self.root / "baseline/phyco-v2/MANIFEST.json")
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_script(self, *args: str) -> int:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return self.script.main(list(args))

    def archive(self) -> Path:
        self.assertEqual(self.run_script(), 0)
        return self.root / "baseline/phyco-v2"

    def manifest(self) -> dict:
        return json.loads((self.root / "baseline/phyco-v2/MANIFEST.json").read_text("utf-8"))

    def test_copies_are_byte_exact_and_the_live_files_stay_unchanged(self):
        before = {rel: (self.root / rel).read_bytes() for rel in self.paths}
        archive = self.archive()
        for rel, data in before.items():
            self.assertEqual((self.root / rel).read_bytes(), data)
            self.assertEqual((archive / Path(rel).name).read_bytes(), data)
        self.assertEqual(self.run_script("--check"), 0)

    def test_the_manifest_names_the_commit_that_holds_each_file(self):
        self.archive()
        head = git(self.root, "rev-parse", "HEAD").decode().strip()
        self.assertEqual(self.manifest()["git_head"], head)
        for entry in self.manifest()["files"]:
            self.assertEqual(entry["source"].split("@")[1], head[:7])

    def test_a_second_run_changes_nothing(self):
        self.archive()
        first = (self.root / "baseline/phyco-v2/MANIFEST.json").read_bytes()
        self.assertEqual(self.run_script(), 0)
        self.assertEqual((self.root / "baseline/phyco-v2/MANIFEST.json").read_bytes(), first)

    def test_an_archive_that_differs_exits_2_and_nothing_changes(self):
        archive = self.archive()
        (archive / "lut.py").write_bytes(b"changed")
        manifest = (archive / "MANIFEST.json").read_bytes()
        self.assertEqual(self.run_script(), 2)
        self.assertEqual((archive / "lut.py").read_bytes(), b"changed")
        self.assertEqual((archive / "MANIFEST.json").read_bytes(), manifest)

    def test_a_manifest_that_differs_exits_2(self):
        archive = self.archive()
        data = self.manifest()
        data["files"][0]["sha256"] = "0" * 64
        (archive / "MANIFEST.json").write_text(json.dumps(data), "utf-8")
        self.assertEqual(self.run_script(), 2)

    def test_a_copy_that_differs_from_its_live_source_stops_the_first_run_too(self):
        archive = self.root / "baseline/phyco-v2"
        archive.mkdir(parents=True)
        (archive / "lut.py").write_bytes(b"not the source")
        self.assertEqual(self.run_script(), 2)
        self.assertFalse((archive / "MANIFEST.json").exists())
        self.assertFalse((archive / "model_v2.py").exists())

    def test_a_live_file_that_differs_from_head_exits_2_writing_nothing(self):
        (self.root / "phycoweb/lut.py").write_bytes(b"uncommitted")
        self.assertEqual(self.run_script(), 2)
        self.assertFalse((self.root / "baseline/phyco-v2").exists())

    def test_a_third_vector_is_refused(self):
        (self.root / "vectors/phyco-v2_c.hex").write_bytes(b"third")
        self.assertEqual(self.run_script(), 2)
        self.assertFalse((self.root / "baseline/phyco-v2").exists())

    def test_check_finds_each_kind_of_mismatch(self):
        def tampered(change) -> int:
            archive = self.archive()
            saved = {p: p.read_bytes() for p in archive.iterdir()}
            live = (self.root / "fast/lut_table.h").read_bytes()
            change(archive)
            code = self.run_script("--check")
            for p in list(archive.iterdir()):
                if p not in saved:
                    p.unlink()
            for p, data in saved.items():
                p.write_bytes(data)
            (self.root / "fast/lut_table.h").write_bytes(live)
            return code

        def wrong_hash(archive: Path) -> None:
            data = self.manifest()
            data["files"][1]["sha256"] = "0" * 64
            (archive / "MANIFEST.json").write_text(json.dumps(data), "utf-8")

        for change in (lambda a: (a / "lut.py").write_bytes(b"x"),
                       lambda a: (a / "lut.py").unlink(),
                       lambda a: (a / "stray.py").write_bytes(b"x"),
                       lambda a: (self.root / "fast/lut_table.h").write_bytes(b"x"),
                       wrong_hash):
            self.assertEqual(tampered(change), 1)
        self.assertEqual(self.run_script("--check"), 0)

    def test_check_with_no_manifest_exits_1(self):
        self.assertEqual(self.run_script("--check"), 1)


class Freezes(unittest.TestCase):
    """The hashes each freeze records, recomputed by the code that wrote them."""

    def test_feature_002(self):
        record = json.loads(FREEZE_002.read_text(encoding="utf-8"))
        now = freeze.current()
        for field in ("model_sha256", "lut_sha256", "design_sha256", "harness_sha256"):
            self.assertEqual(now[field], record[field], field)

    def test_feature_003s_commit_holds_what_its_freeze_records(self):
        record = json.loads(FREEZE_003.read_text(encoding="utf-8"))
        self.assertEqual(len(battery_freeze.SOURCES), 9)
        for field, rel in battery_freeze.SOURCES.items():
            self.assertEqual(sha256(git(ROOT, "show", f"{record['git_head']}:{rel}")), record[field],
                             rel)

    def test_feature_003_sources_hash_as_recorded(self):
        record = json.loads(FREEZE_003.read_text(encoding="utf-8"))
        fixed = json.loads(RESCORE_003.read_text(encoding="utf-8"))["parser_sha256_fixed"]
        for field, rel in battery_freeze.SOURCES.items():
            wanted = fixed if rel == PARSER else record[field]
            self.assertEqual(sha256((ROOT / rel).read_bytes()), wanted, rel)

    def test_the_one_change_since_the_freeze_is_the_recorded_fix(self):
        record = json.loads(FREEZE_003.read_text(encoding="utf-8"))
        commits = git(ROOT, "log", "--format=%h", "--abbrev=7", f"{record['git_head']}..HEAD", "--",
                      PARSER).decode().split()
        self.assertEqual(commits, [PARSER_FIX])
        git(ROOT, "merge-base", "--is-ancestor", PARSER_FIX, FIRST_COMMIT)

    def test_feature_003_binaries_where_they_are_built(self):
        record = json.loads(FREEZE_003.read_text(encoding="utf-8"))
        found = 0
        for field, rel in battery_freeze.BINARIES.items():
            path = ROOT / rel
            if path.is_file():
                found += 1
                self.assertEqual(sha256(path.read_bytes()), record[field], rel)
        if not found:
            self.skipTest("needs the WSL build under fast/build/")

    def test_feature_003_tool_binaries_where_they_are_installed(self):
        record = json.loads(FREEZE_003.read_text(encoding="utf-8"))
        now = battery_freeze.tool_binaries_now(battery_freeze.tool_records())
        self.assertEqual(sorted(now), sorted(record["tool_binaries"]))
        present = {name: value for name, value in now.items() if value is not None}
        if not present:
            self.skipTest("needs the tools of feature 003, installed in WSL only")
        for name, value in present.items():
            self.assertEqual(value, record["tool_binaries"][name], name)


if __name__ == "__main__":
    unittest.main()
