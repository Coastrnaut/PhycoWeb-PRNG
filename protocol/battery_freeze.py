"""Battery-freeze records for the feature-003 held-out attempts (data-model section 6; FR-011,
FR-013).

`create` writes a draft freeze with empty approval fields; only the owner approves it.
`validate` lists every reason a freeze cannot be used. Path roots and the hashing of the
current state are module attributes so tests can redirect them.
"""
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from protocol import battery_seedsets

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports" / "003-extended-batteries-calibration"
MAX_ATTEMPTS = 2
RETRY_VERDICTS = ("INCONCLUSIVE", "INVALID")   # FR-013: a FAIL (or PASS) is final

# Repository files whose hashes are frozen.
SOURCES = {
    "phyco_v2_model_sha256": "phycoweb/model_v2.py",
    "lut_v1_model_sha256": "phycoweb/model.py",
    "lut_sha256": "phycoweb/lut.py",
    "stream_source_sha256": "fast/phyco_stream.c",
    "lut_table_sha256": "fast/lut_table.h",
    "driver_source_sha256": "fast/testu01_driver.c",
    "batteries_sha256": "protocol/batteries.py",
    "battery_run_sha256": "scripts/battery_run.py",
    "battery_attempt_sha256": "scripts/battery_attempt.py",
}
# Built binaries (repository build directory, git-ignored).
BINARIES = {
    "stream_binary_sha256": "fast/build/phyco_stream",
    "driver_binary_sha256": "fast/build/testu01_driver",
}


class FreezeError(Exception):
    """A freeze cannot be created or used; the message says why."""


def _sha256(path: Path) -> Optional[str]:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def tool_records() -> Dict:
    """The tool records written at tool acquisition (data-model section 5)."""
    out = {}
    for path in sorted((REPORTS / "tools").glob("*.json")):
        out[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    return out


def tool_binaries_now(tools: Dict) -> Dict:
    """Re-hash every binary named in the tool records, as it is on disk now."""
    out = {}
    for name, rec in tools.items():
        for label, entry in rec.get("binaries", {}).items():
            out[f"{name}:{label}"] = _sha256(Path(entry["path"]).expanduser())
    return out


def current() -> Dict:
    """Hashes of every frozen source, binary and tool binary as they are on disk now."""
    now = {field: _sha256(ROOT / rel) for field, rel in {**SOURCES, **BINARIES}.items()}
    now["tool_binaries"] = tool_binaries_now(tool_records())
    return now


def git_head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout.strip()


def attempt_dir(n: int) -> Path:
    return REPORTS / f"attempt-{n}"


def freeze_path(n: int) -> Path:
    return attempt_dir(n) / "freeze.json"


def next_attempt() -> int:
    """The only attempt that may be frozen or run next (FR-013)."""
    for n in range(1, MAX_ATTEMPTS + 1):
        record = attempt_dir(n) / "attempt.json"
        if not record.exists():
            if (attempt_dir(n) / "started.json").exists():
                raise FreezeError(f"attempt {n} was started but has no attempt record; "
                                  "the owner must review it")
            return n
        verdict = json.loads(record.read_text(encoding="utf-8"))["verdict"]
        if verdict not in RETRY_VERDICTS:
            raise FreezeError(f"attempt {n} ended {verdict}; no further attempt is allowed "
                              "(FR-013)")
    raise FreezeError(f"all {MAX_ATTEMPTS} attempts are used (FR-013)")


def create(n: int, S: int, commands: Dict, head=None, now: Optional[Dict] = None) -> Dict:
    if not 1 <= n <= MAX_ATTEMPTS:
        raise FreezeError(f"attempt must be 1..{MAX_ATTEMPTS}, got {n}")
    expected = next_attempt()
    if n != expected:
        raise FreezeError(f"attempt {n} is not the next allowed attempt ({expected})")
    if freeze_path(n).exists():
        raise FreezeError(f"{freeze_path(n)} already exists")
    if type(S) is not int or S < 1:
        raise FreezeError(f"S must be a positive integer, got {S!r}")
    now = now if now is not None else current()
    missing = [f for f, v in now.items() if v is None or (f == "tool_binaries" and not v)]
    missing += [k for k, v in now.get("tool_binaries", {}).items() if v is None]
    if missing:
        raise FreezeError(f"cannot freeze, missing: {missing}")
    seed_set = battery_seedsets.ORDER[n - 1]
    record = {"attempt": n, "seed_set": seed_set,
              "seed_set_fingerprint": battery_seedsets.FINGERPRINTS[seed_set],
              "status": "draft", "git_head": (head or git_head)()}
    record.update(now)
    record.update({"tools": tool_records(), "commands": commands, "S": S,
                   "threshold": 0.005 / S, "approved_by": "", "approved_on": ""})
    attempt_dir(n).mkdir(parents=True, exist_ok=True)
    freeze_path(n).write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    return record


def load(n: int) -> Dict:
    path = freeze_path(n)
    if not path.is_file():
        raise FreezeError(f"no freeze record {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate(record: Dict, n: int, now: Optional[Dict] = None) -> List[str]:
    """Every reason this freeze cannot be used for attempt n (empty list: usable)."""
    problems = []
    expected_set = battery_seedsets.ORDER[n - 1] if 1 <= n <= MAX_ATTEMPTS else None
    if record.get("attempt") != n or record.get("seed_set") != expected_set:
        problems.append(f"freeze is for attempt {record.get('attempt')} / "
                        f"{record.get('seed_set')}, not {n} / {expected_set}")
    for field in ("approved_by", "approved_on"):
        if not str(record.get(field, "")).strip():
            problems.append(f"freeze field {field!r} is empty: the owner has not approved it")
    S = record.get("S")
    if type(S) is not int or S < 1 or record.get("threshold") != 0.005 / S:
        problems.append("S / threshold missing or inconsistent")
    now = now if now is not None else current()
    for field, value in now.items():
        if record.get(field) != value:
            problems.append(f"{field} differs from the freeze: frozen {record.get(field)!r}, "
                            f"now {value!r}")
    return problems
