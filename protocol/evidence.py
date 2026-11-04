"""Feature 004: the one writer of evidence records and the guards every script shares.

data-model section 1 states the records and research R16 how they are kept; contracts/cli.md,
"Guards shared by every script", states the guards, each of which refuses with exit 2 and writes
nothing. Exit codes: 0 success; 1 a failing or non-PASS verdict; 2 refused by a guard; 3 tool or
I/O error, a recorded tool defect included. Standard library only, so that scripts/recheck_004.py
may import it (FR-065). All paths hang on the module's REPO, which tests point at a temporary
repository with use_repo().

This module makes no security claim, and neither does any record it writes.
"""
from __future__ import annotations

import datetime
import gzip
import hashlib
import json
import os
import platform as platform_module
import re
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

from protocol.devinputs_v3 import InputRefused, UnknownInput
from protocol.disclaimer import DESIGN_DISCLAIMER

EXIT_OK, EXIT_VERDICT, EXIT_REFUSED, EXIT_TOOL = 0, 1, 2, 3
NONE = "none"
ANALYST = "Claude Code, model claude-opus-5-5"

REP_REL = "reports/004-crypto-architecture-v3"
FEATURE_REL = "specs/004-crypto-architecture-v3"
SPEC_REL = FEATURE_REL + "/spec.md"
RESEARCH_REL = FEATURE_REL + "/research.md"
DESIGN_REL = FEATURE_REL + "/design.md"
PROTOCOL_LOG_REL = "research/004/protocol-changes.jsonl"
CANDIDATE_LOG_REL = "research/004/candidates.jsonl"
PROVENANCE_LOG_REL = REP_REL + "/provenance.jsonl"
DOWNLOADS_REL = REP_REL + "/downloads.json"
SIDECAR_REL = "vectors/phyco-v3/MANIFEST.json"
SUPERSEDED_REL = "research/004/candidates/superseded.json"
REFUSED_LIST_REL = "research/004/refused-constants.json"
LOCAL_REL = "data/local/004"
HEAVY_LOCK_REL = "data/heavy-run.lock"
APPEND_LOCK_REL = "data/log-append.lock"

SUFFIXES = (".json", ".jsonl", ".md", ".csv", ".txt", ".gz")
MAX_COMMITTED_BYTES = 10_000_000
APPEND_LOCK_WAIT_S = 10.0
APPROVAL_FIELDS = ("freeze_status", "approved_by", "approved_utc", "approval_wording",
                   "approval_confirmed")
SELF_HASH_FIELDS = ("draft_sha256",)
PLACEHOLDER = "<record_id>"
PARTIAL_REL = LOCAL_REL + "/.partial"
RUN_FILE = "run.json"
STATUSES = ("pass", "fail", "inconclusive", "not evaluated", "blocked")

CLAIMABLE_SIZES = (4, 8, 16)
# Research R7's rows, per candidate, and the feature-wide row.
ROW_HOURS = {"trails": 48.0, "structural": 6.0, "statistics": 12.0}
FEATURE_ROW = "feature-wide"
FEATURE_ROW_HOURS = 66.0
FUT_SEC_8_ROW = "fut-sec-8"
# Evidence kinds that a candidate's row is charged for; every other heavy run charges no candidate.
CANDIDATE_KINDS = ("inverse", "bijectivity", "dependency", "frequency", "avalanche", "symmetry",
                   "invariant", "degree", "bound", "trail", "cross-check", "control")
# Research R7's test of a heavy run: a kind it budgets, more than one worker, or over 10 minutes.
BUDGETED_KINDS = CANDIDATE_KINDS + ("demonstration",)
LIGHT_HOURS = 10.0 / 60.0
# A candidate so decided is charged no uniform control that runs later (research R7).
CLOSING_DECISIONS = ("withdrawn", "rejected", "ineligible")
# Research R12's table: the rows that name the trail tools.
TRAIL_TOOLS = ("ARX search", "active-S-box counting", "long-trail active-box counting",
               "exhaustive tables")
TRAIL_TOOLS_REL = "research/004/tools/trails/"
# What makes two searches the same instance: a search at its cap stays refused with any tool.
SEARCH_FIELDS = ("bound_kind", "rounds", "width", "size")

# The two kinds that protocol/evidence.py writes while the protocol change log does not exist.
BEFORE_LOG_KINDS = ("lock-cleared", "environment")

# data-model section 1, "Fields compared, per kind": a reproduction compares COMMON_COMPARED and
# these, and reports every other field only. Per-round evidence kinds compare their sections'
# fields, which their scripts pass in; these are the fixed ones.
COMMON_COMPARED = ("kind", "model_id", "variant_id", "inputs", "exit_status", "assertions",
                   "status", "classification")
KIND_COMPARED = {
    "demonstration": ("targets", "revealed", "observed", "vector_check", "matches", "assumption",
                      "listed", "recovered", "model_sha256"),
    "validation": ("tool", "version", "tool_sha256", "licence", "source", "validated_kind",
                   "known_result", "second_known_result", "found", "outcome"),
    "bound": ("bound_kind", "rounds", "width", "size", "bound", "method", "tool", "validation",
              "scope", "cross_check"),
    "trail": ("trail_kind", "characteristic", "weight", "rounds", "size", "width", "tool",
              "validation"),
}
# The part of a field that a reproduction compares, the rest of it reported only (data-model
# section 1, "Fields compared, per kind").
PARTLY_COMPARED = {"demonstration": {"tool": ("source_sha256",),
                                     "cost": ("steps_per_candidate", "total_steps")}}
P_VALUE_TOLERANCE = 1e-6
P_VALUE_FLOOR = 2.0 ** -1022


class Refused(Exception):
    """A guard refused the run: exit 2, nothing written."""


class ToolFailure(Exception):
    """A tool or I/O error, a recorded tool defect included: exit 3."""


@dataclass
class Repo:
    """Every path this module touches, under one repository root."""
    root: Path

    def path(self, rel: str) -> Path:
        return self.root / rel

    @property
    def rep(self) -> Path:
        return self.path(REP_REL)

    @property
    def heavy_lock(self) -> Path:
        return self.path(HEAVY_LOCK_REL)

    @property
    def append_lock(self) -> Path:
        return self.path(APPEND_LOCK_REL)


ROOT_OF_CODE = Path(__file__).resolve().parents[1]
REPO = Repo(ROOT_OF_CODE)


def use_repo(root: Path) -> Repo:
    """Point the module at another repository, for tests; returns the one in use before."""
    global REPO, _SNAPSHOT
    previous = REPO
    REPO = Repo(Path(root))
    _SNAPSHOT = None
    return previous


# ------------------------------------------------------------------------------------- basics


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_utc(text: str) -> datetime.datetime:
    return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=datetime.timezone.utc)


def hours_between(start: str, end: str) -> float:
    return (parse_utc(end) - parse_utc(start)).total_seconds() / 3600.0


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(obj: Any) -> bytes:
    """The object's UTF-8 JSON with keys sorted, the separators , and : and no final newline."""
    text = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return text.encode("utf-8")


def pretty(obj: Any) -> bytes:
    """A .json file: sorted keys, two-space indentation, a final newline, LF only."""
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def git(*args: str, cwd: Optional[Path] = None, check: bool = True) -> bytes:
    result = subprocess.run(("git",) + args, cwd=cwd or REPO.root, capture_output=True)
    if check and result.returncode != 0:
        raise ToolFailure(f"git {' '.join(args)}: {result.stderr.decode('utf-8', 'replace')}")
    return result.stdout


def head() -> str:
    return git("rev-parse", "HEAD").decode("ascii").strip()


def show(path: str, commit: str = "HEAD") -> Optional[bytes]:
    """The blob of `path` at `commit`, or None where the commit holds no such file."""
    result = subprocess.run(("git", "show", f"{commit}:{path}"), cwd=REPO.root, capture_output=True)
    return result.stdout if result.returncode == 0 else None


def lf(data: bytes) -> bytes:
    """Each CR LF pair replaced by LF on the bytes, a lone CR kept (research R16)."""
    return data.replace(b"\r\n", b"\n")


def hash_kind(rel: str) -> str:
    """`raw` for a file pinned to LF or binary, `lf-normalized` for an existing text=auto file."""
    out = git("check-attr", "text", "eol", "--", rel).decode("utf-8")
    values = dict(line.rsplit(": ", 2)[1:] for line in out.splitlines())
    if values.get("text") == "unset" or values.get("eol") == "lf":
        return "raw"
    if values.get("eol") == "crlf":
        return "raw"
    return "lf-normalized"


def hash_entry(rel: str) -> Dict[str, str]:
    """A file's SHA-256 with its kind beside it, over bytes read raw (research R16)."""
    kind = hash_kind(rel)
    data = REPO.path(rel).read_bytes()
    return {"sha256": sha256(lf(data) if kind == "lf-normalized" else data), "kind": kind}


# ------------------------------------------------------------------------- headings and sections


FENCE_LINE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
ATX_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
ATX_CLOSING = re.compile(r"(?:^|[ \t]+)#+$")


@dataclass
class Heading:
    line: int
    level: int
    text: str
    path: str


def headings_of(lines: Sequence[str]) -> List[Heading]:
    """Each ATX heading outside fenced code blocks, as CommonMark reads them, with the texts of the
    headings that enclose it, from the highest level down, and its own, joined by " > "."""
    found: List[Heading] = []
    fence: Optional[str] = None
    stack: List[Heading] = []
    for number, raw in enumerate(lines):
        line = raw.rstrip("\n")
        fenced = FENCE_LINE.match(line)
        if fence is not None:
            if fenced and fenced.group(1)[0] == fence[0] and len(fenced.group(1)) >= len(fence) \
                    and not fenced.group(2).strip():
                fence = None
            continue
        if fenced and not (fenced.group(1)[0] == "`" and "`" in fenced.group(2)):
            fence = fenced.group(1)
            continue
        match = ATX_HEADING.match(line)
        if match:
            level = len(match.group(1))
            text = ATX_CLOSING.sub("", match.group(2) or "").strip()
            while stack and stack[-1].level >= level:
                stack.pop()
            heading = Heading(number, level, text, " > ".join([h.text for h in stack] + [text]))
            stack.append(heading)
            found.append(heading)
    return found


def section_bytes(data: bytes, section: str) -> bytes:
    """A section's text, from its heading line to the line before the next heading of the same or a
    higher level, or to the file's end, each line with its final LF (research R16; REP-088)."""
    lines = data.decode("utf-8").split("\n")
    heads = headings_of(lines)
    matches = [h for h in heads if section in (h.text, h.path)]
    if not matches:
        raise Refused(f"{section!r} names no section")
    if len(matches) > 1:
        raise Refused(f"{section!r} names more than one section")
    head = matches[0]
    later = [h.line for h in heads if h.line > head.line and h.level <= head.level]
    end = later[0] if later else len(lines)
    text = "\n".join(lines[head.line:end])
    return (text + "\n" if later else text).encode("utf-8")


def named_hash(rel: str, section: str = NONE) -> Tuple[str, str]:
    """The SHA-256 and kind of a file, or of a section of it, as data-model section 14 states."""
    entry = hash_entry(rel)
    if section == NONE:
        return entry["sha256"], entry["kind"]
    data = REPO.path(rel).read_bytes()
    return sha256(section_bytes(lf(data) if entry["kind"] == "lf-normalized" else data,
                                section)), entry["kind"]


# ---------------------------------------------------------------------------------- record IDs


def strip_for_id(record: Dict) -> Dict:
    drop = set(APPROVAL_FIELDS) | set(SELF_HASH_FIELDS) | {"record_id"}
    return {k: v for k, v in record.items() if k not in drop}


def substitute(node: Any, old: str, new: str) -> Any:
    if isinstance(node, str):
        return node.replace(old, new)
    if isinstance(node, list):
        return [substitute(v, old, new) for v in node]
    if isinstance(node, dict):
        return {k: substitute(v, old, new) for k, v in node.items()}
    return node


def record_id_for(record: Dict) -> str:
    """`<kind>-<UTC yyyymmddThhmmssZ>-<8 hex>`, the digits from the record's content, computed
    with its own ID written as <record_id> wherever a path holds it (data-model section 1)."""
    stamp = record["created_utc"].replace("-", "").replace(":", "")
    return f"{record['kind']}-{stamp}-{sha256(canonical(strip_for_id(record)))[:8]}"


def check_record_id(record: Dict) -> bool:
    rid = record["record_id"]
    return record_id_for(substitute(strip_for_id(record), rid, PLACEHOLDER)) == rid


def directory_of(kind: str, candidate: Optional[str] = None, original: Optional[str] = None,
                 n: Optional[int] = None) -> str:
    """The directory of a record of `kind`, relative to the reports directory (Record files)."""
    fixed = {"demonstration": "fut-sec-8", "control": "controls", "validation": "validation",
             "generator-run": "generator-runs", "generator-check": "generator-checks",
             "projection": "projections", "recheck": "rechecks", "lock-cleared": "locks"}
    if kind in fixed:
        return fixed[kind]
    if kind == "reproduction":
        return f"reproductions/{original}/{n}"
    if candidate is None:
        raise ValueError(f"a {kind} record needs its candidate's directory")
    return f"candidates/{candidate}"


def iter_records(kind: Optional[str] = None, directory: str = "") -> Iterator[Tuple[Path, Dict]]:
    """Every record under the reports directory, earlier fixed-name versions left out."""
    base = REPO.rep / directory if directory else REPO.rep
    if not base.exists():
        return
    for path in sorted(base.rglob("*.json")):
        if "versions" in path.relative_to(base).parts:
            continue
        try:
            record = json.loads(path.read_bytes().decode("utf-8"))
        except ValueError:
            continue
        if isinstance(record, dict) and (kind is None or record.get("kind") == kind):
            yield path, record


def find_record(record_id: str) -> Optional[Tuple[Path, Dict]]:
    for path, record in iter_records():
        if record.get("record_id") == record_id:
            return path, record
    return None


def rel_to_repo(path: Path) -> str:
    return path.resolve().relative_to(REPO.root.resolve()).as_posix()


# ------------------------------------------------------------------- environment and platform


_SNAPSHOT: Optional[Dict] = None


def platform_name() -> str:
    return "windows" if os.name == "nt" else "wsl"


def _command_line(*cmd: str) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return NONE
    lines = out.splitlines()
    return lines[0].strip() if lines else NONE


def pip_freeze() -> List[str]:
    """The interpreter's `-m pip freeze --all`, run without -I (research R1)."""
    out = subprocess.run((sys.executable, "-m", "pip", "freeze", "--all"), capture_output=True,
                         text=True, check=True).stdout
    return sorted(line for line in out.splitlines() if line.strip())


def snapshot() -> Dict:
    """The running environment as research R1 lists it, compared as a whole."""
    global _SNAPSHOT
    if _SNAPSHOT is None:
        snap: Dict[str, Any] = {"platform": platform_name(),
                                "python": platform_module.python_version(),
                                "packages": pip_freeze()}
        if os.name == "nt":
            snap["windows_build"] = platform_module.version()
        else:
            release = Path("/etc/os-release")
            pretty_name = NONE
            if release.exists():
                match = re.search(r'^PRETTY_NAME="?([^"\n]*)', release.read_text(), re.M)
                pretty_name = match.group(1) if match else NONE
            snap["wsl_distribution"] = pretty_name
            snap["kernel"] = platform_module.release()
            snap["gcc"] = _command_line("gcc", "--version")
            snap["make"] = _command_line("make", "--version")
        _SNAPSHOT = snap
    return _SNAPSHOT


def environment_rel(platform_id: Optional[str] = None) -> str:
    return f"{REP_REL}/environment-{platform_id or platform_name()}.json"


def approval_hash(record: Dict) -> str:
    """Kind `canonical`: over the canonical JSON without the approval fields (REP-083)."""
    return sha256(canonical({k: v for k, v in record.items() if k not in APPROVAL_FIELDS}))


def environment_field(record: Dict, rel: str) -> Dict:
    """How every record names the environment record in force, by both of its hashes."""
    return {"path": rel, "sha256": sha256(REPO.path(rel).read_bytes()), "sha256_kind": "raw",
            "approval_sha256": approval_hash(record), "approval_sha256_kind": "canonical"}


def guard_environment(kind: str) -> Any:
    """Every write checks the running environment against the record in force, as a whole. While
    they differ, or none is in force, the guard admits one write, the environment record itself,
    which scripts/owner_record.py checks against research R1 and the pins (PRO-068)."""
    if kind == "environment":
        return NONE
    rel = environment_rel()
    path = REPO.path(rel)
    if not path.exists():
        raise Refused(f"no environment record in force: {rel} does not exist")
    record = json.loads(path.read_bytes().decode("utf-8"))
    digest = approval_hash(record)
    rows = [r for r in head_table() if r.name.startswith("Environment record")
            and r.decision == "Approved" and digest in r.notes]
    if not rows:
        raise Refused(f"no row \"Environment record <n>\" reads Approved at HEAD with {digest}")
    differences = sorted(k for k in set(record["snapshot"]) | set(snapshot())
                         if record["snapshot"].get(k) != snapshot().get(k))
    if differences:
        raise Refused("the running environment differs from its record in: "
                      + ", ".join(differences))
    return environment_field(record, rel)


def total_ram() -> str:
    if os.name != "nt":
        with open("/proc/meminfo", encoding="ascii") as handle:
            return f"{int(handle.readline().split()[1]) * 1024} bytes"
    import ctypes

    class MemoryStatus(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                    ("total_physical", ctypes.c_ulonglong), ("free_physical", ctypes.c_ulonglong),
                    ("total_page", ctypes.c_ulonglong), ("free_page", ctypes.c_ulonglong),
                    ("total_virtual", ctypes.c_ulonglong), ("free_virtual", ctypes.c_ulonglong),
                    ("free_extended", ctypes.c_ulonglong)]

    status = MemoryStatus()
    status.length = ctypes.sizeof(MemoryStatus)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return NONE
    return f"{status.total_physical} bytes"


def platform_fields() -> Dict:
    return {"system": platform_module.platform(), "cpu": platform_module.processor() or NONE,
            "logical_cpus": os.cpu_count(), "ram": total_ram()}


def interpreter() -> str:
    """Its full path: on Windows the python.exe of the versioned prefix, with the alias resolved,
    and in WSL the venv's (research R1)."""
    if os.name == "nt":
        return str(Path(sys.base_prefix) / "python.exe")
    return sys.executable


def command_line(argv: Sequence[str]) -> str:
    """The interpreter by its full path, then the script and its arguments as given."""
    return shlex.join([interpreter()] + [str(a) for a in argv])


def versions_field(extra: Optional[Dict] = None) -> Dict:
    out: Dict[str, Any] = {"python": platform_module.python_version()}
    for line in snapshot()["packages"]:
        name, _, version = line.partition("==")
        if name in ("numpy", "scipy"):
            out[name] = version
    if "gcc" in snapshot():
        out["gcc"] = snapshot()["gcc"]
    out.update(extra or {})
    return out


# --------------------------------------------------------------------- the Review & Approval table


@dataclass
class Row:
    gate: str
    reviewer: str
    date: str
    decision: str
    notes: str

    @property
    def name(self) -> str:
        return self.gate.split(" (", 1)[0].strip()

    @property
    def k(self) -> int:
        match = re.search(r" (\d+)$", self.name)
        return int(match.group(1)) if match else 1


def table_section(text: str) -> str:
    """The table of spec.md's section "Review & Approval", LF-normalized."""
    lines = text.replace("\r\n", "\n").split("\n")
    start = next((i for i, ln in enumerate(lines) if ln.startswith("## Review & Approval")), None)
    if start is None:
        return ""
    out: List[str] = []
    for line in lines[start + 1:]:
        if line.startswith("|"):
            out.append(line)
        elif out:
            break
    return "\n".join(out)


def parse_table(section: str) -> List[Row]:
    rows = []
    for line in section.split("\n")[2:]:
        cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
        if len(cells) >= 5:
            rows.append(Row(cells[0], cells[1], cells[2], cells[3], " | ".join(cells[4:])))
    return rows


def head_table() -> List[Row]:
    """The table as committed at HEAD; exit 2 while the working tree's table differs (Approvals)."""
    blob = show(SPEC_REL)
    if blob is None:
        raise Refused(f"{SPEC_REL} is not committed at HEAD")
    committed = table_section(blob.decode("utf-8"))
    working = table_section(REPO.path(SPEC_REL).read_bytes().decode("utf-8"))
    if committed != working:
        raise Refused("the working tree's Review & Approval table differs from HEAD's")
    return parse_table(committed)


def family_row(family: str, rows: Optional[List[Row]] = None) -> Optional[Row]:
    """The row of a family with the highest k, the unnumbered row being the first."""
    pattern = re.compile(re.escape(family) + r"( \d+)?$")
    matches = [r for r in (rows if rows is not None else head_table())
               if pattern.fullmatch(r.name)]
    return max(matches, key=lambda r: r.k) if matches else None


def row_approved(family: str, rows: Optional[List[Row]] = None) -> bool:
    row = family_row(family, rows)
    return row is not None and row.decision == "Approved"


# --------------------------------------------------------------------------------- shared guards


def same_as_blob(rel: str, data: bytes, blob: bytes) -> bool:
    """A pinned file equals its blob byte for byte, an existing text=auto file once normalized."""
    return lf(data) == lf(blob) if hash_kind(rel) == "lf-normalized" else data == blob


def guard_committed_code(code_files: Iterable[str], commit: str = "HEAD",
                         root: Optional[Path] = None) -> None:
    """Every file of code_sha256 matches `commit`, committed and unmodified, and each C tool's
    binary was built from its committed source (Committed code). A reproduction names the
    original's commit and the worktree that holds it."""
    files = list(code_files)
    base = root or REPO.root
    for rel in files:
        blob = show(rel, commit)
        if blob is None:
            raise Refused(f"{rel} is not committed at {commit}")
        path = base / rel
        if not path.exists() or not same_as_blob(rel, path.read_bytes(), blob):
            raise Refused(f"{rel} differs from its blob at {commit}")
    for rel in files:
        if "/build/" in rel:
            source = c_source_of(rel)
            if source not in files:
                raise Refused(f"{rel}: its source {source} is not among the run's code files")
            printed = binary_source_sha256(base / rel)
            if printed != sha256((base / source).read_bytes()):
                raise Refused(f"{rel} prints --source-sha256 {printed}, not the hash of {source}")


def c_source_of(binary_rel: str) -> str:
    """A file under a build/ directory comes from the .c file of its name beside that directory."""
    parts = binary_rel.split("/")
    i = parts.index("build")
    return "/".join(parts[:i] + [parts[-1] + ".c"])


def make_file_of(binary_rel: str) -> str:
    return c_source_of(binary_rel)[:-2] + ".mk"


def binary_source_sha256(path: Path) -> str:
    """What the binary prints with --source-sha256; empty where it does not run or says nothing."""
    try:
        return subprocess.run((str(path), "--source-sha256"), capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def guard_cited_files(extra: Iterable[str] = ()) -> List[str]:
    """Exit 2 while a file a record would cite is modified in the working tree (REP-099)."""
    cited = [SPEC_REL, RESEARCH_REL, DESIGN_REL, SIDECAR_REL, SUPERSEDED_REL,
             REFUSED_LIST_REL] + list(extra)
    for rel in cited:
        path = REPO.path(rel)
        blob = show(rel)
        if blob is None and not path.exists():
            continue
        if blob is None or not path.exists() or lf(path.read_bytes()) != lf(blob):
            raise Refused(f"{rel} is modified in the working tree")
    return cited


def dirty_paths() -> List[str]:
    """Every modified or untracked path not ignored, sorted."""
    out = git("status", "--porcelain", "-z", "--untracked-files=all",
              "--no-renames").decode("utf-8")
    fields = [f for f in out.split("\0") if f]
    return sorted(f[3:] for f in fields if len(f) > 3)


def guard_inputs(namespace: str, kind: str) -> None:
    """Only `dev` and `control`, and for US1 the feature-002 dev set (FR-040; cli, Inputs)."""
    if kind == "demonstration":
        if namespace != "feature-002/dev":
            raise Refused(f"namespace {namespace!r}: the demonstration takes feature 002's dev set")
        return
    if namespace not in ("dev", "control"):
        raise Refused(f"namespace {namespace!r} is neither dev nor control")
    if (namespace == "control") != (kind == "control"):
        raise Refused(f"namespace {namespace!r} does not serve kind {kind!r}")


def log_entries(rel: str) -> List[Tuple[Dict, bytes]]:
    """A hash-chained log's entries, each with its line as stored, the final LF included."""
    path = REPO.path(rel)
    if not path.exists():
        return []
    out = []
    for raw in path.read_bytes().splitlines(keepends=True):
        try:
            out.append((json.loads(raw.decode("utf-8")), raw))
        except ValueError:
            raise Refused(f"{rel}: the chain breaks: a line does not parse") from None
    return out


ZERO_HASH = "0" * 64


def first_break(rel: str) -> Optional[Tuple[int, str]]:
    """The seq of the first line the chain does not hold, with the cause, or None."""
    path = REPO.path(rel)
    previous = ZERO_HASH
    lines = path.read_bytes().splitlines(keepends=True) if path.exists() else []
    for seq, raw in enumerate(lines):
        try:
            entry = json.loads(raw.decode("utf-8"))
        except ValueError:
            return seq, "the line does not parse"
        if not raw.endswith(b"\n"):
            return seq, "the line has no final LF"
        if not isinstance(entry, dict) or entry.get("seq") != seq:
            return seq, "its seq is not its position"
        if entry.get("prev_sha256") != previous:
            return seq, "its prev_sha256 is not the SHA-256 of the line before"
        previous = sha256(raw)
    return None


def check_chain(rel: str) -> List[Tuple[Dict, bytes]]:
    """Exit 2 if the chain is broken: seq 0, 1, 2, ... and each prev_sha256 over the line before."""
    broken = first_break(rel)
    if broken is not None:
        raise Refused(f"{rel}: the chain breaks at line {broken[0]}: {broken[1]}")
    return log_entries(rel)


def guard_oplist(oplist_sha256: str) -> None:
    """Every tool refuses an operation list with no `proposed` or `correction` entry (FR-041)."""
    for entry, _ in log_entries(CANDIDATE_LOG_REL):
        if entry.get("event") in ("proposed", "correction") \
                and entry.get("oplist_sha256") == oplist_sha256:
            return
    raise Refused(f"operation list {oplist_sha256} has no proposed or correction entry")


def _without_approval(entry: Dict) -> Dict:
    return {k: v for k, v in entry.items() if k not in ("approver", "prev_sha256")}


def is_first_entry(entry: Dict) -> bool:
    return "rules" in entry


def first_entries_hash(entries: Sequence[Dict]) -> str:
    """Kind `canonical`, over one JSON array of the first entries in log order (REP-094)."""
    return sha256(canonical([_without_approval(e) for e in entries]))


def later_entry_hash(entry: Dict) -> str:
    return sha256(canonical(_without_approval(entry)))


def readings_of(entry: Dict) -> Iterator[Dict]:
    for rule in entry.get("rules", [entry]):
        yield from rule.get("readings") or []


def guard_protocol_log(kind: str) -> Tuple[Any, Any]:
    """Refuses every run that writes evidence until the log stands; returns the last entry's seq
    and line SHA-256 for the record to cite. Two kinds are admitted before the log exists."""
    if not REPO.path(PROTOCOL_LOG_REL).exists():
        if kind in BEFORE_LOG_KINDS:
            return NONE, NONE
        raise Refused(f"{PROTOCOL_LOG_REL} does not exist")
    entries = check_chain(PROTOCOL_LOG_REL)
    if not entries:
        raise Refused(f"{PROTOCOL_LOG_REL} holds no entry")
    first = [e for e, _ in entries if is_first_entry(e)]
    digits = first_entries_hash(first)[:16]
    for entry in first:
        if entry.get("approver", {}).get("approval_confirmed") != digits:
            raise Refused(f"first entry {entry.get('seq')}: its approval digits do not match")
    for entry, _ in entries:
        if is_first_entry(entry):
            continue
        if entry.get("approver", {}).get("approval_confirmed") != later_entry_hash(entry)[:16]:
            raise Refused(f"entry {entry.get('seq')}: its approval digits do not match")
    for entry, _ in entries:
        for reading in readings_of(entry):
            if reading.get("set_aside") and not reading.get("decision"):
                raise Refused(f"entry {entry.get('seq')}: a reading set aside holds no decision")
        if "repair" in entry:
            guard_repair_list(entry)
    last, raw = entries[-1]
    return last["seq"], sha256(raw)


def entry_citations(entry: Dict) -> List[Tuple[str, str, str]]:
    """What an entry cites: each object with `path` and `sha256`, and any `section` it has."""
    found: List[Tuple[str, str, str]] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if isinstance(node.get("path"), str) and isinstance(node.get("sha256"), str):
                found.append((node["path"], node["sha256"], node.get("section", NONE)))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(entry)
    return found


def citation_holds(rel: str, digest: str, section: str = NONE) -> bool:
    """Whether a file, or a section of it, has the SHA-256 at HEAD, on either kind of hash."""
    blob = show(rel)
    if blob is None:
        return False
    if section == NONE:
        return digest in (sha256(blob), sha256(lf(blob)))
    try:
        return digest == sha256(section_bytes(lf(blob), section))
    except Refused:
        return False


# The fields by which a log's entry cites an earlier one by its seq.
SEQ_CITATIONS = ("cites_seq", "follows", "closes", "corrects")


def cited_later(entry: Dict, raw: bytes, later: Sequence[Dict]) -> bool:
    """Whether a later entry that counts, or a record, cites the entry by seq or SHA-256."""
    digest = sha256(raw)
    for other in later:
        if any(other.get(name) == entry.get("seq") for name in SEQ_CITATIONS):
            return True
        if digest in canonical(other).decode("utf-8"):
            return True
    return any(digest in canonical(record).decode("utf-8") for _, record in iter_records())


def entry_counts(entry: Dict, raw: bytes, later: Sequence[Dict]) -> Tuple[bool, str]:
    """Data-model section 3's rule: an entry counts where everything it cites exists at HEAD with
    the SHA-256 it names; one that cites nothing counts only where a later entry that counts, or a
    record, cites it."""
    cited = entry_citations(entry)
    for rel, digest, section in cited:
        if not citation_holds(rel, digest, section):
            return False, f"{rel} does not hold {digest} at HEAD"
    last_id = entry.get("last_record_id")
    known = [r for r in entry.get("results_known") or [] if isinstance(r, str)]
    for record_id in ([last_id] if last_id and last_id != NONE else []) + known:
        if find_record(record_id) is None:
            return False, f"record {record_id} does not exist at HEAD"
    reviewed = entry.get("reviewed_sha256")
    if reviewed and not [r for r in parse_table(table_section(show(SPEC_REL).decode("utf-8")))
                         if r.name == entry.get("row") and reviewed in r.notes]:
        return False, f"its row does not name {reviewed} at HEAD"
    if "rules" in entry:
        from protocol import changelog
        if not changelog.rule_texts_hold(entry):
            return False, "a commit it names does not give its rule's text"
        return True, "every commit it names gives its rule's text"
    if cited or (last_id and last_id != NONE):
        return True, "every citation holds at HEAD"
    if cited_later(entry, raw, later):
        return True, "a later entry or a record cites it"
    return False, "it cites no record, and no later entry cites it"


def repair_list(entries_after: Sequence[Tuple[Optional[Dict], bytes]]) -> List[Dict]:
    """Per entry after the break, its seq, its SHA-256 in the broken file and whether it counts,
    the last first, since an entry may count by a later one that counts."""
    out: List[Dict] = []
    counting: List[Dict] = []
    for entry, raw in reversed(entries_after):
        if entry is None:
            out.append({"seq": None, "sha256": sha256(raw), "counts": False,
                        "reason": "the line does not parse"})
            continue
        counts, reason = entry_counts(entry, raw, counting)
        if counts:
            counting.append(entry)
        out.append({"seq": entry.get("seq"), "sha256": sha256(raw), "counts": counts,
                    "reason": reason})
    return list(reversed(out))


def lines_after(data: bytes, break_seq: int) -> List[Tuple[Optional[Dict], bytes]]:
    """A broken file's lines from the break on, each parsed if it parses."""
    out: List[Tuple[Optional[Dict], bytes]] = []
    for raw in data.splitlines(keepends=True)[break_seq:]:
        try:
            parsed = json.loads(raw.decode("utf-8"))
            out.append((parsed if isinstance(parsed, dict) else None, raw))
        except ValueError:
            out.append((None, raw))
    return out


def guard_repair_list(entry: Dict) -> None:
    """Exit 2 while a repair entry's list differs from the one recomputed from the repository."""
    repair = entry["repair"]
    broken = repair["broken_file"]
    path = REPO.path(broken["path"])
    if not path.exists() or sha256(path.read_bytes()) != broken["sha256"]:
        raise Refused(f"repair entry {entry.get('seq')}: the broken file is not as named")
    after = lines_after(path.read_bytes(), repair["break_seq"])
    if repair_list(after) != repair["entries_after"]:
        raise Refused(f"repair entry {entry.get('seq')}: its list differs from the repository")


def guard_repair_row(rel: str, row_name: str, break_seq: int) -> None:
    """The one append to a broken chain waits for its row "Log repair <n>", Approved at HEAD, which
    names that log and the seq of the break (cli, Hash-chained logs; PRO-076)."""
    rows = [r for r in head_table() if r.name == row_name]
    if not re.fullmatch(r"Log repair \d+", row_name) or not rows:
        raise Refused(f"no row {row_name!r} at HEAD")
    row = rows[-1]
    if row.decision != "Approved":
        raise Refused(f"the row {row_name!r} does not read Approved at HEAD")
    if rel not in row.notes or not re.search(rf"seq\W{{0,3}}{break_seq}\b", row.notes):
        raise Refused(f"the row {row_name!r} does not name {rel} and seq {break_seq}")


def repair_fields(rel: str, row_name: str) -> Dict:
    """A broken log's `repair` fields, the broken file kept unchanged with its SHA-256, through the
    row's guard; the log itself is restored by restore_chain under the append lock."""
    broken = first_break(rel)
    if broken is None:
        raise Refused(f"{rel}: its chain holds")
    break_seq, cause = broken
    guard_repair_row(rel, row_name, break_seq)
    source = REPO.path(rel)
    data = source.read_bytes()
    digest = sha256(data)
    keep = source.parent / "broken" / f"{source.stem}-{digest}.jsonl"
    keep.parent.mkdir(parents=True, exist_ok=True)
    if not keep.exists():
        keep.write_bytes(data)
    return {"break_seq": break_seq, "cause": cause, "row": row_name,
            "broken_file": {"path": rel_to_repo(keep), "sha256": digest, "sha256_kind": "raw"},
            "restored": f"the {break_seq} lines before the break, as stored",
            "entries_after": repair_list(lines_after(data, break_seq))}


def restore_chain(rel: str, repair: Dict, fields: Optional[Dict] = None,
                  finish: Optional[Callable[[Dict], Dict]] = None) -> Dict:
    """The restored log: the lines before the break as stored and the `repair` entry chained to
    the last of them. `finish` gives a writer's approval step the entry before it is written."""
    with AppendLock(rel):
        path = REPO.path(rel)
        kept = path.read_bytes().splitlines(keepends=True)[:repair["break_seq"]]
        entry = dict(fields or {})
        entry.update({"seq": len(kept), "repair": repair,
                      "prev_sha256": sha256(kept[-1]) if kept else ZERO_HASH,
                      "date_utc": utc_now()})
        if finish is not None:
            entry = finish(entry)
        data = b"".join(kept) + log_line(entry)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_bytes(data)
        os.replace(temporary, path)
    return entry


def is_finished(record: Dict) -> bool:
    """A run has finished where it gave a result: a run ended from outside has not, nor has a run
    that left its kind's evidence inconclusive."""
    if record.get("ended_outside", NONE) != NONE:
        return False
    return record.get("status") not in ("inconclusive", "blocked", "not evaluated")


def candidate_decisions(candidate: str) -> List[str]:
    return [e.get("decision") for e, _ in log_entries(CANDIDATE_LOG_REL)
            if e.get("candidate_id") == candidate and e.get("event") == "decision"]


def guard_order_of_sizes(candidate: str, kind: str, size: int, project: bool = False) -> None:
    """Evidence at 8×8 or 16×16 waits for the next smaller size's run of that kind (research R7).
    The guard counts evidence records only, so a --project probe is never refused."""
    if project or size not in CLAIMABLE_SIZES or size == CLAIMABLE_SIZES[0]:
        return
    smaller = CLAIMABLE_SIZES[CLAIMABLE_SIZES.index(size) - 1]
    if set(candidate_decisions(candidate)) & {"ineligible", "rejected"}:
        raise Refused(f"{candidate} is ineligible or rejected")
    for _, record in iter_records(kind, f"candidates/{candidate}"):
        if record.get("config", {}).get("size") == smaller and is_finished(record):
            return
    raise Refused(f"{kind} at {size}×{size} waits for its run at {smaller}×{smaller} to finish")


def latest_demonstration() -> Optional[Tuple[Path, Dict]]:
    records = list(iter_records("demonstration", "fut-sec-8"))
    return max(records, key=lambda item: item[1]["created_utc"]) if records else None


def guard_order_of_us1() -> None:
    """No key is loaded before the FUT-SEC-8 result review with the highest k reads Approved at
    HEAD and names the latest demonstration record by path and SHA-256 (FR-001, FR-003)."""
    row = family_row("FUT-SEC-8 result review")
    if row is None or row.decision != "Approved":
        raise Refused("the row \"FUT-SEC-8 result review\" does not read Approved at HEAD")
    latest = latest_demonstration()
    if latest is None:
        raise Refused("no demonstration record exists")
    path, _ = latest
    if rel_to_repo(path).split(REP_REL + "/", 1)[-1] not in row.notes \
            or sha256(path.read_bytes()) not in row.notes:
        raise Refused(f"the review row does not name the latest demonstration record {path.name}")


def validation_record(tool: Optional[str], tool_sha256: str, binary_sha256: Optional[str] = None,
                      known_kind: Optional[str] = None) -> Optional[Dict]:
    """The latest `re-found` record of the tool's exact hash, or None (cli, Tool validation). For a
    C tool the exact hash is the pair of source and binary; a tool of None matches by hash alone. A
    `not re-found` of that exact hash later than it closes it: a validation on one known result
    never outlasts a failure on another (data-model section 7)."""
    found = None
    failed = ""
    for _, record in iter_records("validation", "validation"):
        if tool is not None and record.get("tool") != tool:
            continue
        if record.get("tool_sha256") != tool_sha256:
            continue
        if binary_sha256 is not None:
            hashes = [e.get("sha256") for e in (record.get("code_sha256") or {}).values()]
            if binary_sha256 not in hashes:
                continue
        if record.get("outcome") == "not re-found":
            failed = max(failed, record["created_utc"])
        if record.get("outcome") != "re-found":
            continue
        if known_kind is not None and record.get("validated_kind") != known_kind:
            continue
        if found is None or record["created_utc"] > found["created_utc"]:
            found = record
    return None if found is not None and found["created_utc"] < failed else found


def validation_citation(tool: Optional[str], tool_sha256: str, binary_sha256: Optional[str] = None,
                        known_kind: Optional[str] = None) -> Optional[Dict]:
    """What a counted record holds in `validation`: the ID and SHA-256 of the validation record of
    the tool's exact hash (data-model section 5). None, and the result is `not evaluated`."""
    record = validation_record(tool, tool_sha256, binary_sha256, known_kind)
    if record is None:
        return None
    path = find_record(record["record_id"])
    if path is None:
        raise ToolFailure(f"{record['record_id']} is not under its own name")
    return {"record_id": record["record_id"], "sha256": sha256(path[0].read_bytes()),
            "sha256_kind": "raw"}


def validation_cited_before(record: Dict) -> bool:
    """A counted record's citation holds: the cited record has that hash and is earlier."""
    citation = record.get("validation")
    if not isinstance(citation, dict):
        return False
    found = find_record(citation["record_id"])
    if found is None or sha256(found[0].read_bytes()) != citation["sha256"]:
        return False
    return found[1]["created_utc"] < record["created_utc"]


def result_status(status: str, validated: bool) -> str:
    """A result of a tool without a `re-found` record of its kind and exact hash never counts."""
    return status if validated else "not evaluated"


def first_trail_search_started() -> bool:
    return any(True for kind in ("bound", "trail") for _ in iter_records(kind))


def reached_cap(record: Dict) -> bool:
    """A capped search is `inconclusive` with its instance's cap reached; one ended from outside
    did not reach it."""
    return record.get("status") == "inconclusive" and record.get("capped") is True \
        and record.get("ended_outside", NONE) == NONE


def search_reached_cap(candidate: str, search: Dict) -> bool:
    for _, record in iter_records("bound", f"candidates/{candidate}"):
        if reached_cap(record) and all(record.get(f) == search.get(f) for f in SEARCH_FIELDS):
            return True
    return False


def guard_trail_tools(tool: str, tool_sha256: str, binary_sha256: Optional[str] = None,
                      candidate: Optional[str] = None, search: Optional[Dict] = None,
                      rerun_after_defect: Optional[str] = None) -> None:
    """Once the first trail search has started, a tool outside the fixed set, or without an earlier
    `re-found` record of its exact hash, is refused, and so is a search that reached its cap, save
    research R7's one re-run after a recorded tool defect (cli, Trail tools)."""
    if not first_trail_search_started():
        return
    if tool not in TRAIL_TOOLS:
        raise Refused(f"{tool} is not in the fixed set of trail tools")
    if validation_record(tool, tool_sha256, binary_sha256) is None:
        raise Refused(f"{tool}: no re-found record of its exact hash")
    if candidate and search and rerun_after_defect is None \
            and search_reached_cap(candidate, search):
        raise Refused(f"{candidate}: search {search} reached its cap, and a speed-up is no defect")


def run_hours_used(record: Dict) -> float:
    """The hours a record says its run used, summed over a reproduction's runs."""
    hours = record.get("hours")
    if not isinstance(hours, dict):
        return 0.0
    if "runs" in hours:
        return sum(run.get("used", 0.0) for run in hours["runs"])
    return float(hours.get("used", 0.0))


def charges_no_candidate(record: Dict) -> bool:
    if record.get("kind") in CANDIDATE_KINDS:
        return False
    if record.get("kind") == "demonstration":
        return record.get("supersedes", NONE) != NONE
    return True


def feature_row_used() -> float:
    """Read from the records: the time of every `projection` record that names the row and the
    `hours` used of every other heavy record that charges no candidate, the FUT-SEC-8 row's pass
    excepted (cli, Budget)."""
    used = 0.0
    for _, record in iter_records():
        if record.get("kind") == "projection":
            if record.get("row") == FEATURE_ROW:
                used += float(record.get("time_hours", 0.0))
        elif record.get("heavy_run") is True and charges_no_candidate(record):
            used += run_hours_used(record)
    return used


def guard_feature_row(projections: Sequence[float]) -> None:
    left = FEATURE_ROW_HOURS - feature_row_used()
    if sum(projections) > left:
        raise Refused(f"the projections, {sum(projections):.3f} h, do not fit the {left:.3f} h "
                      f"left in research R7's feature-wide row")


def closing_date(candidate: str) -> Optional[str]:
    """The date of the candidate's first decision of CLOSING_DECISIONS, or None."""
    dates = [e["date_utc"] for e, _ in log_entries(CANDIDATE_LOG_REL)
             if e.get("candidate_id") == candidate and e.get("event") == "decision"
             and e.get("decision") in CLOSING_DECISIONS]
    return min(dates) if dates else None


def control_hours(candidate: str) -> float:
    """The uniform controls' hours that the candidate's 12 h row is charged, whether the control
    ran for it or before it: none for a control after a closing decision, nor for one its row
    could not hold, which the control's record lists in `not_charged` (research R7)."""
    closed = closing_date(candidate)
    total = 0.0
    for _, record in iter_records("control", "controls"):
        if candidate in record.get("not_charged", ()):
            continue
        if closed is None or record["created_utc"] <= closed:
            total += run_hours_used(record)
    return total


def candidate_row_used(candidate: str, row: str) -> float:
    """A candidate's row, read from its `evidence` entries, its row's projections and, for the
    statistics row, the uniform controls' records (research R7; cli, Budget)."""
    used = 0.0
    for entry, _ in log_entries(CANDIDATE_LOG_REL):
        if entry.get("candidate_id") == candidate and entry.get("event") == "evidence":
            used += float((entry.get("budget_used_h") or {}).get(row, 0.0))
    for _, record in iter_records("projection", "projections"):
        if record.get("row") == f"{candidate}/{row}":
            used += float(record.get("time_hours", 0.0))
    if row == "statistics":
        used += control_hours(candidate)
    return used


def guard_candidate_row(candidate: str, row: str, projected: float, reserved: float = 0.0) -> None:
    """A heavy run starts only if its projection, plus the probes of every run its row still needs,
    fits the hours left in its row (research R7)."""
    left = ROW_HOURS[row] - candidate_row_used(candidate, row)
    if projected + reserved > left:
        raise Refused(f"{candidate}: {projected + reserved:.3f} h do not fit the {left:.3f} h left "
                      f"in its {row} row")


# ----------------------------------------------------------------------------------- the locks


def process_start(pid: int) -> Optional[str]:
    """That process's start time, as the system gives it, or None if no such process runs."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.windll.kernel32
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.c_void_p] * 4
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return None
        try:
            times = [wintypes.FILETIME() for _ in range(4)]
            if not kernel.GetProcessTimes(handle, *[ctypes.byref(t) for t in times]):
                return None
            code = wintypes.DWORD()
            kernel.GetExitCodeProcess(handle, ctypes.byref(code))
            if code.value != 259:
                return None
            return str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)
        finally:
            kernel.CloseHandle(handle)
    stat = Path(f"/proc/{pid}/stat")
    try:
        text = stat.read_text()
    except OSError:
        return None
    return text.rsplit(")", 1)[1].split()[19]


def holder_runs(lock: Dict) -> bool:
    """Whether a process with the lock's PID and start time runs, in the lock's environment; a
    ToolFailure or an OSError where that environment cannot be asked."""
    pid = int(lock["pid"])
    if lock["environment"] == platform_name():
        return process_start(pid) == lock["start"]
    if lock["environment"] == "wsl":
        cmd = ("wsl.exe", "-e", "sh", "-c", f"cat /proc/{pid}/stat 2>/dev/null; true")
        out = subprocess.run(cmd, capture_output=True, text=True)
        if out.returncode != 0:
            raise ToolFailure("wsl.exe cannot be asked whether the lock's holder runs")
        return bool(out.stdout) and out.stdout.rsplit(")", 1)[1].split()[19] == lock["start"]
    cmd = ("powershell.exe", "-NoProfile", "-Command",
           f"$p = Get-Process -Id {pid} -ErrorAction SilentlyContinue; "
           f"if ($p) {{ $p.StartTime.ToFileTimeUtc() }}")
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise ToolFailure("powershell.exe cannot be asked whether the lock's holder runs")
    return out.stdout.strip() == lock["start"]


def boot_time(environment: str) -> str:
    """When the lock's environment last started, UTC, ISO 8601, seconds (research R7)."""
    if environment == "wsl":
        if platform_name() == "wsl":
            text = Path("/proc/stat").read_text()
        else:
            text = subprocess.run(("wsl.exe", "-e", "cat", "/proc/stat"), capture_output=True,
                                  text=True, check=True).stdout
        seconds = int(text.split("btime ", 1)[1].split()[0])
    elif platform_name() == "windows":
        import ctypes
        kernel = ctypes.windll.kernel32
        kernel.GetTickCount64.restype = ctypes.c_ulonglong
        seconds = int(time.time() - kernel.GetTickCount64() / 1000.0)
    else:
        cmd = ("powershell.exe", "-NoProfile", "-Command",
               "(Get-Date (Get-CimInstance Win32_OperatingSystem).LastBootUpTime)"
               ".ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')")
        return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
    stamp = datetime.datetime.fromtimestamp(seconds, datetime.timezone.utc)
    return stamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def lock_content(command: str) -> Dict:
    pid = os.getpid()
    return {"pid": pid, "start": process_start(pid), "environment": platform_name(),
            "host": socket.gethostname(), "command": command, "time": utc_now()}


def read_lock(path: Path) -> Dict:
    return json.loads(path.read_bytes().decode("utf-8"))


def take_lock(path: Path, command: str) -> Dict:
    """Exclusive create; a lock that exists is named, with whether its holder still runs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = lock_content(command)
    try:
        with open(path, "xb") as handle:
            handle.write(canonical(content) + b"\n")
    except FileExistsError:
        try:
            state = "its holder still runs" if holder_runs(read_lock(path)) \
                else "its holder no longer runs; scripts/clear_lock.py removes it"
        except (ValueError, KeyError, OSError, ToolFailure):
            state = "its holder cannot be read"
        raise Refused(f"{path.name} is held: {state}") from None
    return content


class HeavyRunLock:
    """data/heavy-run.lock, removed on exit; only scripts/clear_lock.py removes a stale one. The
    run's description goes under its temporary directory first, so that a run that dies holding
    the lock still gets the record of its kind (data-model section 1)."""

    def __init__(self, command: str, description: Optional[Dict] = None,
                 partial: Optional[Path] = None):
        self.command = command
        self.description = description
        self.partial = partial
        self.content: Optional[Dict] = None

    def __enter__(self) -> "HeavyRunLock":
        if self.partial is not None:
            self.partial.mkdir(parents=True, exist_ok=True)
            (self.partial / RUN_FILE).write_bytes(pretty(self.description))
        try:
            self.content = take_lock(REPO.heavy_lock, self.command)
        except Refused:
            if self.partial is not None:
                shutil.rmtree(self.partial, ignore_errors=True)
            raise
        return self

    def __exit__(self, *exc: Any) -> None:
        REPO.heavy_lock.unlink(missing_ok=True)


class AppendLock:
    """data/log-append.lock, taken for one append to a chained log; exit 2 if not free in 10 s."""

    def __init__(self, command: str, wait_s: float = APPEND_LOCK_WAIT_S):
        self.command = command
        self.wait_s = wait_s

    def __enter__(self) -> "AppendLock":
        deadline = time.monotonic() + self.wait_s
        while True:
            try:
                take_lock(REPO.append_lock, self.command)
                return self
            except Refused:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.2)

    def __exit__(self, *exc: Any) -> None:
        REPO.append_lock.unlink(missing_ok=True)


def append_entry(rel: str, entry: Dict, finish: Optional[Callable[[Dict], Dict]] = None) -> Dict:
    """One append to a hash-chained log: under the lock, the chain checked up to its last line,
    `seq`, `prev_sha256` and `date_utc` added by the writer (research R16). `finish` gives a
    writer's approval step the complete entry before it is written."""
    with AppendLock(rel):
        path = REPO.path(rel)
        data = path.read_bytes() if path.exists() else b""
        lines = data.splitlines(keepends=True)
        check_chain(rel)
        record = dict(entry)
        record["seq"] = len(lines)
        record["prev_sha256"] = sha256(lines[-1]) if lines else ZERO_HASH
        record.setdefault("date_utc", utc_now())
        if finish is not None:
            record = finish(record)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "ab") as handle:
            handle.write(log_line(record))
    return record


def log_line(entry: Dict) -> bytes:
    """One entry of a .jsonl log: sorted keys, characters as they are, one object per line."""
    return json.dumps(entry, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n"


def interactive_terminal() -> bool:
    """Whether standard input is a terminal. On Windows the NUL device passes isatty, so the console
    is asked as well; a Git Bash window's pipe is no terminal, and PowerShell's console is."""
    if not sys.stdin.isatty():
        return False
    if os.name != "nt":
        return True
    import ctypes
    import msvcrt
    kernel = ctypes.windll.kernel32
    kernel.GetConsoleMode.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    mode = ctypes.c_ulong()
    handle = ctypes.c_void_p(msvcrt.get_osfhandle(sys.stdin.fileno()))
    return bool(kernel.GetConsoleMode(handle, ctypes.byref(mode)))


def confirm_digits(digest: str) -> str:
    """The first 16 hex digits of the hash, which the owner types at an interactive terminal."""
    if not interactive_terminal():
        raise Refused("the approval step needs an interactive terminal: it is the owner's own act")
    try:
        typed = input("type its first 16 hex digits: ").strip()
    except EOFError:
        raise Refused("the approval step read no digits") from None
    if typed != digest[:16]:
        raise Refused("the digits typed are not the first 16 of the approval hash")
    return typed


def approval_step(digest: str) -> str:
    """An owner's own act, which the agent never performs: it prints the hash, kind `canonical`,
    and writes nothing unless the owner types its first 16 digits (spec FR-044; REP-083)."""
    print(f"approval hash (canonical): {digest}")
    return confirm_digits(digest)


# ------------------------------------------------------------------------------- the design file


def design_version() -> Tuple[str, str]:
    """The design document's version and SHA-256; 1.0 while the approved freeze names its hash."""
    path = REPO.path(DESIGN_REL)
    if not path.exists():
        return NONE, NONE
    data = path.read_bytes()
    match = re.search(r"^Version: (0\.\d+)$", data.decode("utf-8"), re.M)
    if not match:
        raise Refused(f"{DESIGN_REL} holds no line \"Version: 0.<k>\"")
    digest = sha256(data)
    return ("1.0" if (DESIGN_REL, digest) in pinned_entries() else match.group(1)), digest


def pinned_entries() -> List[Tuple[str, str]]:
    """Each (path, SHA-256) that the approved freeze record pins; none before its approval."""
    path = REPO.rep / "freeze" / "freeze.json"
    if not path.exists():
        return []
    record = json.loads(path.read_bytes().decode("utf-8"))
    if record.get("freeze_status") != "approved":
        return []
    return [(rel, digest) for rel, digest, _ in entry_citations(record)]


def keep_version(subdir: str, data: bytes) -> None:
    """Store a copy of a cited document under <subdir>/<sha256>.md, the first time it is cited."""
    target = REPO.rep / subdir / f"{sha256(data)}.md"
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


# ------------------------------------------------------------------------------------- the writer


def write_exclusive(path: Path, data: bytes) -> None:
    """A record is never overwritten: a second write of its path is refused."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "xb") as handle:
            handle.write(data)
    except FileExistsError:
        raise Refused(f"{path} exists, and a record is never overwritten") from None


def frozen_paths() -> List[str]:
    """The files that the approved freeze record pins."""
    return [path for path, _ in pinned_entries()]


def is_heavy(kind: str, workers: int = 1, threads: int = 1,
             projected_hours: Optional[float] = None, last_hours: Optional[float] = None) -> bool:
    """Research R7's test, a property of each run: a kind it budgets, more than one worker process
    or thread, or a run projected to take, or that last took, more than 10 minutes."""
    return kind in BUDGETED_KINDS or workers > 1 or threads > 1 \
        or (projected_hours or 0.0) > LIGHT_HOURS or (last_hours or 0.0) > LIGHT_HOURS


def check_committed_output(name: str, size: int) -> None:
    """A file under the reports directory has an allowed suffix and at most 10 MB (research R16)."""
    if not name.endswith(SUFFIXES):
        raise Refused(f"{name}: its suffix is not allowed under the reports directory")
    if size > MAX_COMMITTED_BYTES:
        raise Refused(f"{name}: {size} bytes, above the 10 MB of a committed output")


class Run:
    """One run of a script that writes evidence: its guards, its outputs and its record.

        with Run("inverse", candidate="cand-A1", code_files=[...], argv=sys.argv, ...) as run:
            run.output("summary.json", data)
            run.finish("pass", fields={...})

    A run that raises writes an aborted record, `inconclusive` with the reason; a guard's refusal
    writes nothing. A heavy run holds data/heavy-run.lock from entry to exit. `file_name` gives a
    name the data model states, written once, or with `fixed` kept under that name with versions/.
    What a record cites is read when the run starts. A run that is no evidence run, such as the
    records of scripts/clear_lock.py and scripts/owner_record.py, passes writes_evidence=False.
    `environment` holds a re-check's own environment, which is exempt from the guard.
    """

    def __init__(self, kind: str, *, candidate: Optional[str] = None,
                 model_id: Optional[str] = None, variant_id: Optional[str] = None,
                 code_files: Iterable[str] = (),
                 argv: Sequence[str] = (), config: Optional[Dict] = None, inputs: Any = NONE,
                 heavy: bool = False, projected_hours: Optional[float] = None,
                 last_hours: Optional[float] = None, workers: int = 1, threads: int = 1,
                 versions: Optional[Dict] = None, limitations: Iterable[str] = (),
                 directory: Optional[str] = None, file_name: Optional[str] = None,
                 fixed: bool = False, original: Optional[str] = None, n: Optional[int] = None,
                 namespace: Optional[str] = None, writes_evidence: bool = True,
                 cited: Iterable[str] = (), analyst: str = ANALYST,
                 environment: Optional[Dict] = None):
        self.kind = kind
        self.candidate = candidate
        self.model_id = model_id
        self.variant_id = variant_id
        self.code_files = list(code_files)
        self.argv = list(argv)
        self.config = dict(config or {})
        self.inputs = inputs
        self.heavy = heavy or is_heavy(kind, workers, threads, projected_hours, last_hours)
        self.projected_hours = projected_hours
        self.workers = workers
        self.threads = threads
        self.versions = versions
        self.limitations = list(limitations)
        self.directory = directory if directory is not None \
            else directory_of(kind, candidate, original, n)
        self.file_name = file_name
        self.fixed = fixed
        self.namespace = namespace
        self.writes_evidence = writes_evidence
        self.cited = list(cited)
        self.analyst = analyst
        self.own_environment = environment
        self.outputs: List[Dict] = []
        self.moves: List[Tuple[Path, str]] = []
        self.extra: Dict[str, Any] = {}
        self.lock: Optional[HeavyRunLock] = None
        self.clock = 0.0
        self.start: Dict[str, Any] = {}
        self.documents: List[Tuple[str, bytes]] = []
        self.environment: Any = NONE
        self.protocol: Tuple[Any, Any] = (NONE, NONE)
        self.finished = False
        self.record_path: Optional[Path] = None
        self.tmp = REPO.path(PARTIAL_REL) / f"{os.getpid()}-{time.monotonic_ns()}"

    def record_dir(self) -> Path:
        """The kind's place: under the reports directory, or beside an exploration table."""
        if self.directory.startswith("research/"):
            return REPO.path(self.directory)
        return REPO.rep / self.directory

    def stated_path(self) -> Optional[Path]:
        return self.record_dir() / self.file_name if self.file_name else None

    def __enter__(self) -> "Run":
        self.environment = self.own_environment if self.own_environment is not None \
            else guard_environment(self.kind)
        self.protocol = guard_protocol_log(self.kind)
        guard_committed_code(self.code_files)
        if self.writes_evidence:
            guard_cited_files(self.cited)
        if self.namespace is not None:
            guard_inputs(self.namespace, self.kind)
        stated = self.stated_path()
        if stated is not None and self.fixed and rel_to_repo(stated) in frozen_paths():
            raise Refused(f"{rel_to_repo(stated)} is pinned by the freeze record")
        if stated is not None and not self.fixed and stated.exists():
            raise Refused(f"{rel_to_repo(stated)} exists, and it is written once")
        self.read_citations()
        if self.heavy:
            self.lock = HeavyRunLock(command_line(self.argv), self.description(), self.tmp)
            self.lock.__enter__()
        self.clock = time.monotonic()
        return self

    def description(self) -> Dict:
        """What scripts/clear_lock.py needs for this run's record if it dies holding the lock."""
        return {"kind": self.kind, "candidate": self.candidate, "model_id": self.model_id,
                "variant_id": self.variant_id, "directory": self.directory, "config": self.config,
                "inputs": self.inputs, "projected_hours": self.projected_hours,
                "workers": self.workers, "threads": self.threads}

    def read_citations(self) -> None:
        """What the record cites, as it stands when the run starts; the copies come with the
        record, so that a refusal inside the run writes none."""
        spec, research = REPO.path(SPEC_REL).read_bytes(), REPO.path(RESEARCH_REL).read_bytes()
        version, design_digest = design_version()
        self.documents = [("spec-versions", spec), ("research-versions", research)]
        if design_digest != NONE:
            self.documents.append(("design-versions", REPO.path(DESIGN_REL).read_bytes()))
        dirty = dirty_paths()
        self.start = {"design_version": version, "design_sha256": design_digest,
                      "design_sha256_kind": "raw", "spec_sha256": sha256(spec),
                      "spec_sha256_kind": "raw", "research_sha256": sha256(research),
                      "research_sha256_kind": "raw", "git_head": head(), "git_dirty": bool(dirty),
                      "dirty_paths": dirty}

    def begin(self, projected_hours: Optional[float] = None) -> None:
        """The clock of the hours used starts here, after the run's projection, whose own time its
        `projection` record counts."""
        if projected_hours is not None:
            self.projected_hours = projected_hours
        self.clock = time.monotonic()

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        try:
            if exc_type is None or issubclass(exc_type, Refused):
                return False
            if not self.finished:
                self.finish("inconclusive", exit_status=EXIT_TOOL,
                            limitations=[f"aborted: {exc_type.__name__}: {exc}"])
            return False
        finally:
            if self.lock is not None:
                self.lock.__exit__(None, None, None)
            shutil.rmtree(self.tmp, ignore_errors=True)

    def output(self, name: str, data: bytes, *, deterministic: bool = True,
               compared: Optional[str] = None, local: bool = False) -> Dict:
        """Write one output under a temporary name; the record renames it to its ID (Record files).
        A .gz name compresses it as research R16 states. A committed output needs an allowed suffix
        and at most 10 MB; an output that is not deterministic is never local-only (R16)."""
        entry: Dict[str, Any] = {}
        if name.endswith(".gz"):
            entry["uncompressed_sha256"] = sha256(data)
            data = gzip.compress(data, compresslevel=9, mtime=0)
        if local and not deterministic:
            raise Refused(f"{name}: an output that is not deterministic is never local-only")
        if not local:
            check_committed_output(name, len(data))
        target = self.tmp / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        final = (f"{LOCAL_REL}/{PLACEHOLDER}/{name}" if local
                 else f"{rel_to_repo(self.record_dir())}/{PLACEHOLDER}/{name}")
        entry.update({"path": final, "sha256": sha256(data), "sha256_kind": "raw",
                      "bytes": len(data), "committed": not local, "deterministic": deterministic})
        if compared:
            entry["compared"] = compared
        self.outputs.append(entry)
        self.moves.append((target, final))
        return entry

    def common_fields(self) -> Dict:
        code = {rel: hash_entry(rel) for rel in self.code_files}
        record = dict(self.start)
        record.update({
            "kind": self.kind, "model_id": self.model_id, "variant_id": self.variant_id,
            "protocol_seq": self.protocol[0], "protocol_line_sha256": self.protocol[1],
            "protocol_line_sha256_kind": "raw", "code_sha256": code,
            "versions": versions_field(self.versions), "environment": self.environment,
            "platform": platform_fields(),
            "parallelism": {"workers": self.workers, "threads": self.threads,
                            "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED", NONE)},
            "command": command_line(self.argv),
            "config": dict(self.config, cwd=os.getcwd(), repository_root=str(REPO.root)),
            "inputs": self.inputs, "analyst": self.analyst, "reviewer": "pending",
            "review_status": "pending", "ended_outside": NONE, "disclaimer": DESIGN_DISCLAIMER})
        return record

    def prepare(self, status: str, *, classification: str = NONE, assertions: Iterable[Any] = (),
                exit_status: int = EXIT_OK, fields: Optional[Dict] = None,
                limitations: Iterable[str] = ()) -> Dict:
        """The complete record with its ID, nothing written, so that a writer that takes an owner's
        confirmation can print its approval hash first (data-model section 1; REP-092)."""
        if status not in STATUSES:
            raise ToolFailure(f"status {status!r} is not one of {STATUSES}")
        record = self.common_fields()
        record.update({"created_utc": utc_now(), "outputs": self.outputs,
                       "exit_status": exit_status, "assertions": list(assertions),
                       "status": status, "classification": classification,
                       "limitations": self.limitations + list(limitations),
                       "heavy_run": self.heavy, "hours": NONE})
        if self.heavy:
            record["hours"] = {"projected": self.projected_hours,
                               "used": (time.monotonic() - self.clock) / 3600.0}
        record.update(self.extra)
        record.update(fields or {})
        if self.fixed:
            stated = self.stated_path()
            record["previous_sha256"] = sha256(stated.read_bytes()) if stated.exists() else NONE
        record_id = record_id_for(record)
        record = substitute(record, PLACEHOLDER, record_id)
        record["record_id"] = record_id
        return record

    def write(self, record: Dict, approval: Optional[Dict] = None) -> Path:
        """Keep what the record cites, rename its outputs to its ID and write it."""
        out = dict(record, **(approval or {}))
        for subdir, data in self.documents:
            keep_version(subdir, data)
        for source, final in self.moves:
            target = REPO.path(final.replace(PLACEHOLDER, out["record_id"]))
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
        path = self.stated_path() or self.record_dir() / f"{out['record_id']}.json"
        if self.fixed:
            if path.exists():
                old = path.read_bytes()
                keep = path.parent / "versions" / f"{sha256(old)}.json"
                keep.parent.mkdir(parents=True, exist_ok=True)
                if not keep.exists():
                    keep.write_bytes(old)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(pretty(out))
        else:
            write_exclusive(path, pretty(out))
        self.finished = True
        self.record_path = path
        return path

    def finish(self, status: str, **kwargs: Any) -> Path:
        return self.write(self.prepare(status, **kwargs))


DISCARDED = "its outputs other than timing were discarded unread"


def write_simple_record(kind: str, directory: str, fields: Dict, status: str = "pass",
                        argv: Sequence[str] = (), code_files: Iterable[str] = (),
                        writes_evidence: bool = True) -> Path:
    """A record that makes no run of its own, such as `lock-cleared` or `projection`."""
    run = Run(kind, directory=directory, argv=argv, code_files=code_files,
              writes_evidence=writes_evidence)
    with run:
        return run.finish(status, fields=fields)


def write_projection(*, run: str, row: str, inputs: Any, measured_speed: Any,
                     projected_hours: float, time_hours: float, statement: Optional[str] = None,
                     status: str = "pass", argv: Sequence[str] = (),
                     code_files: Iterable[str] = (), writes_evidence: bool = True,
                     extra: Optional[Dict] = None) -> Path:
    """Every 60 s projection and timing probe; not evidence (data-model section 1). FR-053's test
    with two worker counts states what it did in place of the sentence on its outputs."""
    fields = {"run": run, "row": row, "inputs": inputs, "measured_speed": measured_speed,
              "projected_hours": projected_hours, "time_hours": time_hours,
              "outputs_statement": statement or DISCARDED}
    fields.update(extra or {})
    return write_simple_record("projection", "projections", fields, status=status, argv=argv,
                               code_files=code_files, writes_evidence=writes_evidence)


def read_manifest() -> List[Dict]:
    """The downloads manifest's entries; none before it exists."""
    path = REPO.path(DOWNLOADS_REL)
    if not path.exists():
        return []
    return json.loads(path.read_bytes().decode("utf-8"))["entries"]


def manifest_run(argv: Sequence[str], code_files: Iterable[str]) -> Run:
    """The run that writes the downloads manifest, a record of a kind of its own (REP-085)."""
    return Run("downloads", directory="", file_name="downloads.json", fixed=True, argv=argv,
               code_files=code_files, writes_evidence=False)


def write_manifest(run: Run, entries: List[Dict], assertions: Iterable[Any] = ()) -> Path:
    return run.finish("pass", assertions=assertions,
                      fields={"entries": entries, "inputs": NONE, "outputs": NONE})


# ---------------------------------------------------------------------------------- classification


def classify(kind: str, outcome: str) -> str:
    """data-model section 1's table by kind and outcome (FR-060, FR-065)."""
    findings = {
        ("frequency", "fired"): "confirmed vulnerability",
        ("avalanche", "fired"): "confirmed vulnerability",
        ("invariant", "above-chance"): "confirmed vulnerability",
        ("trail", "found"): "confirmed vulnerability",
        ("dependency", "incomplete"): "confirmed vulnerability",
        ("inverse", "failed"): "confirmed vulnerability",
        ("bijectivity", "failed"): "confirmed vulnerability",
        ("symmetry", "failed"): "confirmed vulnerability",
        ("invariant", "kept"): "confirmed vulnerability",
        ("degree", "raises"): "strong theoretical concern",
        ("bound", "established"): "no weakness identified within the analysis performed",
        ("frequency", "not-fired"): "no weakness identified within the analysis performed",
        ("avalanche", "not-fired"): "no weakness identified within the analysis performed",
        ("reproduction", "differs-verdict"): "unverified hypothesis",
        ("recheck", "disagreement"): "unverified hypothesis",
        ("demonstration", "recovered"): "confirmed vulnerability",
        ("demonstration", "disagreement"): "unverified hypothesis",
    }
    if outcome == "unvalidated":
        return "unverified hypothesis"
    return findings.get((kind, outcome), NONE)


# ---------------------------------------------------------------------------------- reproduction


def compared_fields(original: Dict, extra: Sequence[str] = ()) -> List[str]:
    """COMMON_COMPARED and the fields of the record's kind that the original holds."""
    fields = list(COMMON_COMPARED) + list(KIND_COMPARED.get(original.get("kind"), ())) + list(extra)
    return [f for f in fields if f in original]


def source_entries(code: Dict) -> Dict:
    """A reproduction compares each source file's entry; a binary's hash is reported only."""
    return {rel: entry for rel, entry in (code or {}).items() if "/build/" not in rel}


def deterministic_outputs(record: Dict) -> Dict:
    out = {}
    for entry in record.get("outputs") or []:
        name = entry["path"].rsplit("/", 1)[-1]
        if entry.get("deterministic"):
            key = "uncompressed_sha256" if "uncompressed_sha256" in entry else "sha256"
            out[name] = {"hash": entry[key], "bytes": entry.get("bytes")
                         if key == "sha256" else None}
    return out


def p_values_agree(a: float, b: float) -> bool:
    """Within 10⁻⁶ of the larger magnitude, or both below the smallest normal double."""
    if abs(a) < P_VALUE_FLOOR and abs(b) < P_VALUE_FLOOR:
        return True
    return abs(a - b) <= P_VALUE_TOLERANCE * max(abs(a), abs(b))


def _flat_values(node: Any) -> List[float]:
    if isinstance(node, (int, float)) and not isinstance(node, bool):
        return [float(node)]
    if isinstance(node, dict):
        return [v for key in sorted(node) for v in _flat_values(node[key])]
    if isinstance(node, list):
        return [v for item in node for v in _flat_values(item)]
    return []


def read_output_values(path: Path) -> Any:
    data = path.read_bytes()
    if path.name.endswith(".gz"):
        data = gzip.decompress(data)
    return json.loads(data.decode("utf-8"))


def compare_records(original: Dict, new: Dict,
                    extra: Sequence[str] = ()) -> Tuple[Dict, bool, List]:
    """Each compared field with its outcome, whether a field that enters a verdict differs, and
    each p-value outside the tolerance (data-model section 1, Reproduction)."""
    outcomes: Dict[str, str] = {}
    verdict_differs = False
    for name in compared_fields(original, extra):
        same = original.get(name) == new.get(name)
        outcomes[name] = "match" if same else "differs"
        verdict_differs = verdict_differs or not same
    for name, keys in PARTLY_COMPARED.get(original.get("kind"), {}).items():
        ours, theirs = original.get(name) or {}, new.get(name) or {}
        same = all(ours.get(key) == theirs.get(key) for key in keys)
        outcomes[name] = "match" if same else "differs"
        verdict_differs = verdict_differs or not same
    same = source_entries(original.get("code_sha256")) == source_entries(new.get("code_sha256"))
    outcomes["code_sha256"] = "match" if same else "differs"
    verdict_differs = verdict_differs or not same
    same = deterministic_outputs(original) == deterministic_outputs(new)
    outcomes["outputs"] = "match" if same else "differs"
    verdict_differs = verdict_differs or not same
    outside: List[Dict] = []
    new_by_name = {e["path"].rsplit("/", 1)[-1]: e for e in new.get("outputs") or []}
    for entry in original.get("outputs") or []:
        if entry.get("compared") != "values":
            continue
        name = entry["path"].rsplit("/", 1)[-1]
        ours = _flat_values(read_output_values(REPO.path(entry["path"])))
        theirs_entry = new_by_name.get(name)
        theirs = _flat_values(read_output_values(REPO.path(theirs_entry["path"]))) \
            if theirs_entry else []
        found = [{"output": name, "index": i, "original": a, "reproduced": b}
                 for i, (a, b) in enumerate(zip(ours, theirs)) if not p_values_agree(a, b)]
        if len(ours) != len(theirs):
            found.append({"output": name, "index": None, "original": len(ours),
                          "reproduced": len(theirs)})
        outcomes[name] = "differs" if found else "match"
        outside.extend(found)
    return outcomes, verdict_differs, outside


def every_field_differs(original: Dict, extra: Sequence[str] = ()) -> Dict:
    """A rebuild refused or failed counts as a difference in every compared field (research R16)."""
    names = compared_fields(original, extra) + list(PARTLY_COMPARED.get(original.get("kind"), {}))
    names += ["code_sha256", "outputs"]
    return {name: "differs" for name in names}


def make_binary(worktree: Path, binary_rel: str) -> None:
    """Build a C tool with its make file, which runs in WSL (research R1); tests replace this."""
    make_file = make_file_of(binary_rel)
    directory = str(Path(make_file).parent)
    subprocess.run(("make", "-C", directory, "-f", Path(make_file).name), cwd=worktree,
                   capture_output=True, check=True)


def add_worktree(commit: str) -> Path:
    base = REPO.path(LOCAL_REL) / ".worktrees"
    base.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(prefix="wt-", dir=base))
    git("worktree", "add", "--detach", "--force", str(path), commit)
    return path


def remove_worktree(path: Path) -> None:
    git("worktree", "remove", "--force", str(path), check=False)
    shutil.rmtree(path, ignore_errors=True)


def next_reproduction(original_id: str) -> int:
    base = REPO.rep / "reproductions" / original_id
    taken = [int(p.name) for p in base.iterdir() if p.is_dir() and p.name.isdigit()] \
        if base.exists() else []
    return max(taken, default=0) + 1


@dataclass
class Place:
    """Where one run of a reproduction runs and writes: the worktree, the main tree's directory for
    the outputs the original commits, a temporary directory for those it keeps local-only, renamed
    to the reproduction's own ID, and for a second run the rebuilt binaries."""
    worktree: Path
    out: Path
    local: Path
    binaries: Dict[str, Path]


@dataclass
class Reproduction:
    """What a script's --reproduce gives the common part. `run(place)` makes one run of the recorded
    configuration and returns its fields; `project(worktree)` gives a heavy run's hours and measured
    speed; `extra` names the compared fields of the kind; `recheck` holds a re-check's own
    environment, whose reproduction runs anywhere; `code_files` is the reproducing script's code."""
    record_path: Path
    run: Callable[[Place], Dict]
    heavy: bool = False
    owner_request: Optional[str] = None
    project: Optional[Callable[[Path], Tuple[float, Any]]] = None
    extra: Sequence[str] = ()
    recheck: Optional[Dict] = None
    code_files: Sequence[str] = ()
    argv: Sequence[str] = ()


def environment_record_id(cited: Dict) -> str:
    """The ID of the environment record that `cited` names, resolved from versions/ if changed."""
    path = REPO.path(cited["path"])
    for found in (path, path.parent / "versions" / f"{cited['sha256']}.json"):
        if found.exists() and sha256(found.read_bytes()) == cited["sha256"]:
            return json.loads(found.read_bytes().decode("utf-8")).get("record_id", cited["path"])
    return cited["path"]


def guard_original_environment(original: Dict) -> None:
    """A reproduction runs in the environment that made the original, and in no other (REP-100)."""
    in_force = guard_environment("reproduction")
    cited = original.get("environment")
    if not isinstance(cited, dict) or cited.get("approval_sha256") != in_force["approval_sha256"]:
        name = environment_record_id(cited) if isinstance(cited, dict) else NONE
        raise Refused(f"environment record {name} is not in force")


def guard_design_version(original: Dict, worktree: Path) -> None:
    """The design document is read from the worktree, which matches its stored version (REP-099)."""
    digest = original.get("design_sha256", NONE)
    if digest == NONE:
        return
    stored = REPO.rep / "design-versions" / f"{digest}.md"
    at_commit = worktree / DESIGN_REL
    for path in (stored, at_commit):
        if not path.exists() or sha256(path.read_bytes()) != digest:
            raise Refused(f"{path} is not design version {digest}")


def rebuild_admitted(original: Dict, binary_rel: str, digest: str) -> bool:
    """Tool validation and Trail tools: a rebuild that differs is a new version of the tool, run
    only with a `re-found` record of its own exact hash, whatever the kind of the record reproduced,
    and a trail tool's only in the fixed set (data-model section 7; cli, Trail tools)."""
    source = original["code_sha256"][c_source_of(binary_rel)]["sha256"]
    record = validation_record(None, source, digest)
    if record is None:
        return False
    return not binary_rel.startswith(TRAIL_TOOLS_REL) or not first_trail_search_started() \
        or record.get("tool") in TRAIL_TOOLS


def rebuild_binaries(original: Dict, worktree: Path) -> Tuple[Dict, Dict[str, Path], bool]:
    """Each binary rebuilt with its make file, the committed one removed first so that make cannot
    take it as up to date. Returns the rebuilds' hashes, reported only, those a second run takes,
    and whether one failed or was refused, which counts as a difference (research R16)."""
    code = original.get("code_sha256") or {}
    note: Dict[str, Dict] = {}
    rebuilt: Dict[str, Path] = {}
    counted = False
    for rel in sorted(r for r in code if "/build/" in r):
        (worktree / rel).unlink(missing_ok=True)
        try:
            make_binary(worktree, rel)
            digest = sha256((worktree / rel).read_bytes())
        except (OSError, subprocess.SubprocessError) as exc:
            note[rel] = {"sha256": NONE, "failed": str(exc)}
            counted = True
            continue
        note[rel] = {"sha256": digest, "sha256_kind": "raw"}
        if digest == code[rel]["sha256"]:
            continue
        if not rebuild_admitted(original, rel, digest):
            note[rel]["refused"] = True
            counted = True
        elif binary_source_sha256(worktree / rel) != code[c_source_of(rel)]["sha256"]:
            note[rel]["failed"] = "its --source-sha256 differs from its source's entry"
            counted = True
        else:
            rebuilt[rel] = worktree / rel
    return note, rebuilt, counted


def project_runs(job: Reproduction, original: Dict, trees: Sequence[Path]) -> List[float]:
    """Each run it will make projects first; together they must fit the feature-wide row."""
    if job.project is None:
        raise ToolFailure("a heavy reproduction needs its script's projection")
    hours = []
    for tree in trees:
        started = time.monotonic()
        projected, speed = job.project(tree)
        hours.append(projected)
        write_projection(run=f"reproduction of {original['record_id']}", row=FEATURE_ROW,
                         inputs=original.get("inputs", NONE), measured_speed=speed,
                         projected_hours=projected, argv=job.argv, code_files=job.code_files,
                         time_hours=(time.monotonic() - started) / 3600.0)
    guard_feature_row(hours)
    return hours


def adopt_outputs(run: Run, place: Place, result: Dict, prefix: str = "") -> None:
    """The run's outputs, under the suffix and 10 MB rules, those kept local-only going to
    data/local/004/<record_id>/ under the reproduction's own ID (data-model section 1)."""
    for path in sorted(place.out.rglob("*")):
        if path.is_file():
            check_committed_output(path.name, path.stat().st_size)
    if place.local.exists():
        for path in sorted(place.local.rglob("*")):
            if path.is_file():
                name = path.relative_to(place.local).as_posix()
                if not name.startswith("rebuilt/"):
                    run.moves.append((path, f"{LOCAL_REL}/{PLACEHOLDER}/{prefix}{name}"))
    for entry in result.get("outputs") or []:
        entry = dict(entry)
        if not entry.get("committed", True):
            name = entry["path"].rsplit("/", 1)[-1]
            entry["path"] = f"{LOCAL_REL}/{PLACEHOLDER}/{prefix}{name}"
        run.outputs.append(entry)


def reported_fields(result: Dict, compared: Dict) -> Dict:
    """Every other field of the run, reported only (data-model section 1, Reproduction), a field
    compared in part among them."""
    partly = PARTLY_COMPARED.get(result.get("kind"), {})
    return {k: v for k, v in result.items()
            if (k not in compared or k in partly) and k not in ("code_sha256", "outputs", "hours_used")}


def run_reproduction(job: Reproduction, run: Run, original: Dict, out: Path,
                     worktrees: List[Path]) -> int:
    """The runs of a reproduction and its record, inside the Run that holds any heavy-run lock."""
    commit = original["git_head"]
    code = original.get("code_sha256") or {}
    main = add_worktree(commit)
    worktrees.append(main)
    for rel, entry in code.items():
        blob = show(rel, commit)
        if blob is None or sha256(blob) != entry["sha256"]:
            raise Refused(f"{rel} at {commit} does not match the record's code_sha256")
    guard_committed_code(code, commit, main)
    guard_design_version(original, main)
    note: Dict[str, Dict] = {}
    rebuilt: Dict[str, Path] = {}
    counted = False
    second: Optional[Path] = None
    if any("/build/" in rel for rel in code):
        second = add_worktree(commit)
        worktrees.append(second)
        note, rebuilt, counted = rebuild_binaries(original, second)
    trees = [main] + ([second] if rebuilt and second else [])
    projections = project_runs(job, original, trees) if run.heavy else []
    run.begin(sum(projections) if run.heavy else None)

    started = time.monotonic()
    out.mkdir(parents=True, exist_ok=True)
    place = Place(main, out, run.tmp / "local", {})
    place.local.mkdir(parents=True, exist_ok=True)
    first = job.run(place)
    used = float(first.get("hours_used", (time.monotonic() - started) / 3600.0))
    adopt_outputs(run, place, first)
    hours_runs = [{"projected": projections[0], "used": used}] if run.heavy else []
    outcomes, verdict_differs, outside = compare_records(original, first, job.extra)
    if counted:
        outcomes = every_field_differs(original, job.extra)
        verdict_differs = True

    second_outcomes: Optional[Dict] = None
    reported_second: Optional[Dict] = None
    not_made: Optional[str] = None
    if rebuilt and not counted:
        left = FEATURE_ROW_HOURS - feature_row_used() - used
        if run.heavy and projections[1] > left:
            not_made = (f"the second run's projection, {projections[1]:.3f} h, no longer fits the "
                        f"{left:.3f} h left, the first run having taken more than its own")
        else:
            started = time.monotonic()
            place = Place(second, out / "rebuilt", run.tmp / "local" / "rebuilt", rebuilt)
            place.out.mkdir(parents=True, exist_ok=True)
            place.local.mkdir(parents=True, exist_ok=True)
            result = job.run(place)
            used_2 = float(result.get("hours_used", (time.monotonic() - started) / 3600.0))
            adopt_outputs(run, place, result, prefix="rebuilt/")
            if run.heavy:
                hours_runs.append({"projected": projections[1], "used": used_2})
            second_outcomes, differs_2, outside_2 = compare_records(original, result, job.extra)
            reported_second = reported_fields(result, second_outcomes)
            verdict_differs = verdict_differs or differs_2
            outside = outside + outside_2

    fields: Dict[str, Any] = {"compared": outcomes, "compared_rebuilt": second_outcomes,
                              "rebuild": note, "reported": reported_fields(first, outcomes),
                              "reported_rebuilt": reported_second, "p_values_outside": outside}
    if run.heavy:
        fields["hours"] = {"runs": hours_runs}
    limitations: List[str] = []
    if not_made is not None:
        fields["reason"] = not_made
        limitations.append(not_made)
    if verdict_differs:
        status, outcome = "blocked", "differs"
        classification = classify("reproduction", "differs-verdict")
    elif outside:
        status, outcome, classification = "fail", "differs", NONE
    elif not_made is not None:
        status, outcome, classification = "inconclusive", NONE, NONE
    else:
        status, outcome, classification = "pass", "match", NONE
    fields["outcome"] = outcome
    exit_status = EXIT_OK if outcome == "match" else EXIT_VERDICT
    run.finish(status, classification=classification, fields=fields, limitations=limitations,
               exit_status=exit_status)
    return exit_status


def reproduce(job: Reproduction) -> int:
    """The common part of every --reproduce mode (cli contract, Reproduction; research R16).

    Returns 0 for `match` and 1 otherwise, the record written; raises Refused, exit 2, with nothing
    written but a heavy run's `projection` records."""
    data = job.record_path.read_bytes()
    original = json.loads(data.decode("utf-8"))
    original_id = original["record_id"]
    if original.get("ended_outside", NONE) != NONE:
        raise Refused(f"{original_id} holds ended_outside: its run gave no result")
    if reached_cap(original):
        raise Refused(f"{original_id} reached its cap, and is not reproduced (Trail tools)")
    parallelism = original.get("parallelism") or {}
    heavy = job.heavy or is_heavy(original.get("kind"), parallelism.get("workers", 1),
                                  parallelism.get("threads", 1), None, run_hours_used(original))
    if heavy and not job.owner_request:
        raise Refused("a heavy reproduction runs only with --owner-request \"WORDS (DATE)\"")
    if job.recheck is None:
        guard_original_environment(original)
    directory = f"reproductions/{original_id}/{next_reproduction(original_id)}"
    run = Run("reproduction", directory=directory, model_id=original.get("model_id"),
              variant_id=original.get("variant_id"), code_files=job.code_files, argv=job.argv,
              heavy=heavy, environment=job.recheck)
    run.extra = {"original": {"record_id": original_id, "sha256": sha256(data),
                              "sha256_kind": "raw"},
                 "commit": original["git_head"], "owner_request": job.owner_request or NONE}
    out = REPO.rep / directory
    worktrees: List[Path] = []
    with run:
        try:
            return run_reproduction(job, run, original, out, worktrees)
        except Refused:
            shutil.rmtree(out, ignore_errors=True)
            raise
        finally:
            for tree in worktrees:
                remove_worktree(tree)


# ---------------------------------------------------------------------------------- script helpers


def main_guard(fn: Callable[[], int]) -> int:
    """Run a script's body, turning a refusal into exit 2 and a tool failure into exit 3. The
    loader's refusals are refusals here, though one of them is a PermissionError (data-model
    section 2), so they are named before OSError, which stays a tool failure."""
    try:
        return fn()
    except (Refused, InputRefused, UnknownInput) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return EXIT_REFUSED
    except (ToolFailure, OSError) as exc:
        print(f"tool failure: {exc}", file=sys.stderr)
        return EXIT_TOOL
