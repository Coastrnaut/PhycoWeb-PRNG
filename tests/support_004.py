"""Feature 004: a temporary repository for the tests of the writers and guards. It holds what the
guards read, a spec with a Review & Approval table, research.md, an approved environment record and
a protocol change log with one approved first entry, so that each test breaks exactly one thing."""
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional
from unittest import mock

from protocol import evidence

CODE_ROOT = Path(__file__).resolve().parents[1]
# The code files that the owner's scripts name, committed in every temporary repository.
CODE_COPIES = ("protocol/evidence.py", "protocol/disclaimer.py", "scripts/clear_lock.py",
               "scripts/owner_record.py", "scripts/downloads.py")
GITATTRIBUTES = """* text=auto
*.py text eol=lf
*.c text eol=lf
*.md text eol=lf
reports/004-crypto-architecture-v3/** text eol=lf
research/004/** text eol=lf
**/build/** binary
"""

SPEC_HEAD = """# Spec

Some text.

## Review & Approval *(Constitution Principle VIII)*

| Gate | Reviewer | Date | Decision | Notes |
|------|----------|------|----------|-------|
"""

SPEC_TAIL = """
Notes under the table.

## Next
"""

SNAPSHOT = {"platform": evidence.platform_name(), "python": "3.10.11",
            "packages": ["numpy==2.2.6", "scipy==1.15.3"], "windows_build": "10.0.26300",
            "gcc": "gcc (Ubuntu 15.2.0) 15.2.0"}


def pin_feature_004():
    """For a module whose tests read feature 004's committed records or build its temporary
    repositories: feature 004 is in force while the module loads and while its tests run, whatever
    PHYCOWEB_FEATURE the suite was started with (feature 005, FR-003). Returns the module's
    setUpModule and tearDownModule."""
    evidence.set_feature("004")

    def set_up() -> None:
        evidence.set_feature("004")

    def tear_down() -> None:
        evidence.set_feature(evidence.ENTRY_FEATURE)

    return set_up, tear_down


def write(root: Path, rel: str, data) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
    return path


def remove_tree(path: str) -> None:
    """A temporary repository, read-only git objects included, which Windows will not delete as they stand."""
    def writable(function, name, _):
        os.chmod(name, stat.S_IWRITE)
        function(name)

    shutil.rmtree(path, onerror=writable)


def report_files(root: Path) -> List[str]:
    """Every file under the reports directory, relative to it."""
    rep = root / evidence.REP_REL
    return sorted(p.relative_to(rep).as_posix() for p in rep.rglob("*") if p.is_file()) \
        if rep.exists() else []


class TempRepo(unittest.TestCase):
    """A committed repository with the environment record and the protocol change log in force."""

    rows: List[str] = []

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="phyco004-")
        self.root = Path(self.tmp)
        self.addCleanup(remove_tree, self.tmp)
        self.previous = evidence.use_repo(self.root)
        self.addCleanup(evidence.use_repo, self.previous.root)
        patcher = mock.patch.object(evidence, "snapshot", return_value=dict(SNAPSHOT))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.run_git("init", "-q")
        self.run_git("config", "user.name", "owner")
        self.run_git("config", "user.email", "owner@example.invalid")
        self.run_git("config", "core.autocrlf", "false")
        write(self.root, ".gitattributes", GITATTRIBUTES)
        write(self.root, ".gitignore", "data/local/\ndata/*.lock\n")
        write(self.root, evidence.RESEARCH_REL, "# Research\n")
        write(self.root, "scripts/tool.py", "print('tool')\n")
        for rel in CODE_COPIES:
            write(self.root, rel, (CODE_ROOT / rel).read_bytes())
        self.rows = []
        self.write_spec()
        self.commit("first")
        self.install_environment()
        self.install_protocol_log()

    def run_git(self, *args: str, cwd: Optional[Path] = None) -> str:
        result = subprocess.run(("git",) + args, cwd=cwd or self.root, capture_output=True,
                                text=True, check=True)
        return result.stdout

    def commit(self, message: str = "commit") -> str:
        self.run_git("add", "-A")
        self.run_git("commit", "-q", "--allow-empty", "-m", message)
        return self.run_git("rev-parse", "HEAD").strip()

    def write_spec(self) -> None:
        write(self.root, evidence.SPEC_REL,
              SPEC_HEAD + "".join(line + "\n" for line in self.rows) + SPEC_TAIL)

    def add_row(self, gate: str, decision: str, notes: str, commit: bool = True) -> None:
        self.rows.append(f"| {gate} | owner | 2026-11-03 | {decision} | {notes} |")
        self.write_spec()
        if commit:
            self.commit(f"row {gate}")

    def install_environment(self) -> Dict:
        record = {"kind": "environment", "snapshot": dict(SNAPSHOT), "approved_by": "owner",
                  "approved_utc": "2026-11-03T00:00:00Z", "approval_confirmed": "0" * 16}
        rel = evidence.environment_rel()
        write(self.root, rel, evidence.pretty(record))
        self.add_row("Environment record 1", "Approved", evidence.approval_hash(record))
        return record

    def first_entry(self, seq: int = 0, prev: str = evidence.ZERO_HASH, **fields) -> Dict:
        entry = {"seq": seq, "prev_sha256": prev, "date_utc": "2026-11-03T00:00:00Z",
                 "rules": [{"rule": "Bias rule", "old_text": "a", "new_text": "b",
                            "direction": "stricter", "readings": []}],
                 "row": "ANA-001", "granularity": "round", "last_record_id": "none",
                 "results_known": []}
        entry.update(fields)
        return entry

    def write_log(self, entries: List[Dict]) -> None:
        lines = b""
        previous = evidence.ZERO_HASH
        for seq, entry in enumerate(entries):
            entry = dict(entry, seq=seq, prev_sha256=previous)
            raw = json.dumps(entry, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n"
            lines += raw
            previous = evidence.sha256(raw)
        write(self.root, evidence.PROTOCOL_LOG_REL, lines)

    def approve(self, entries: List[Dict]) -> List[Dict]:
        """Fill `approver`, the first entries together and each later one alone."""
        first = [e for e in entries if evidence.is_first_entry(e)]
        digits = evidence.first_entries_hash(first)[:16]
        out = []
        for entry in entries:
            value = digits if evidence.is_first_entry(entry) \
                else evidence.later_entry_hash(entry)[:16]
            out.append(dict(entry, approver={"owner": "owner", "date": "2026-11-03",
                                             "approval_confirmed": value}))
        return out

    def install_protocol_log(self) -> None:
        self.write_log(self.approve([self.first_entry()]))
        self.commit("protocol log")


class Tool:
    """Names of the committed files of a mocked C tool in a temporary repository."""
    source = "fast/seed_search.c"
    binary = "fast/build/seed_search"
    make = "fast/seed_search.mk"
