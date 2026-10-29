"""Design-freeze records for held-out attempts (data-model section 3; FR-016; research R8).

`create` writes a draft freeze with empty approval fields; only the owner fills them in.
`validate` lists every reason a freeze cannot be used for an acceptance run. Path roots are
module attributes so tests can point them at a temporary directory.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports" / "002-core-dynamics-redesign"
MAX_ATTEMPTS = 3
MODEL = "phycoweb/model_v2.py"
LUT = "phycoweb/lut.py"
DESIGN = "specs/002-core-dynamics-redesign/design.md"
HARNESS = "sp80022"
# Paths that must have no uncommitted changes when a freeze is written.
FROZEN_PATHS = (MODEL, LUT, DESIGN, HARNESS + "/")
HASH_FIELDS = ("model_id", "model_sha256", "lut_sha256", "design_version", "design_sha256",
               "harness_version", "harness_sha256", "warmup")


class FreezeError(Exception):
    """A freeze cannot be created or used; the message says why."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def design_version(text: str) -> str:
    match = re.search(r"\*\*Version\*\*:\s*([0-9]+(?:\.[0-9]+)*)", text)
    if not match:
        raise FreezeError(f"{DESIGN} has no '**Version**: x.y' line")
    return match.group(1)


def current() -> Dict:
    """Hashes and versions of the model, design and harness as they are on disk now."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    import sp80022
    from phycoweb import model_v2
    design = ROOT / DESIGN
    return {
        "model_id": model_v2.MODEL_ID,
        "model_sha256": _sha256(ROOT / MODEL),
        "lut_sha256": _sha256(ROOT / LUT),
        "design_version": design_version(design.read_text(encoding="utf-8")),
        "design_sha256": _sha256(design),
        "harness_version": sp80022.__version__,
        "harness_sha256": sp80022.source_sha256(),
        "warmup": model_v2.WARMUP,
    }


def git_status(paths=FROZEN_PATHS) -> str:
    return subprocess.run(["git", "status", "--porcelain", "--", *paths], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


def git_head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout.strip()


def attempt_dir(n: int) -> Path:
    return REPORTS / f"attempt-{n}"


def freeze_path(n: int) -> Path:
    return attempt_dir(n) / "freeze.json"


def next_attempt() -> int:
    """1 + the highest attempt that has an attempt record."""
    done = [n for n in range(1, MAX_ATTEMPTS + 1) if (attempt_dir(n) / "attempt.json").exists()]
    return max(done, default=0) + 1


def create(n: int, dev_evidence: Path, status: Callable[[], str] = None,
           head: Callable[[], str] = None) -> Dict:
    status = status or git_status
    head = head or git_head
    if not 1 <= n <= MAX_ATTEMPTS:
        raise FreezeError(f"attempt must be 1..{MAX_ATTEMPTS}, got {n}")
    expected = next_attempt()
    if n != expected:
        raise FreezeError(f"attempt {n} is not the next attempt ({expected})")
    if attempt_dir(n).exists():
        raise FreezeError(f"{attempt_dir(n)} already exists")
    dirty = status().strip()
    if dirty:
        raise FreezeError("uncommitted changes to the model, design or harness:\n" + dirty)
    if not Path(dev_evidence).is_file():
        raise FreezeError(f"dev evidence {dev_evidence} not found")
    record = {"attempt": n, "seed_set": f"heldout-{n}", "status": "draft", "git_head": head()}
    record.update(current())
    record["dev_evidence"] = Path(dev_evidence).resolve().relative_to(ROOT).as_posix() \
        if Path(dev_evidence).resolve().is_relative_to(ROOT) else str(dev_evidence)
    record["approved_by"] = ""
    record["approved_on"] = ""
    attempt_dir(n).mkdir(parents=True)
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
    if record.get("attempt") != n or record.get("seed_set") != f"heldout-{n}":
        problems.append(f"freeze is for attempt {record.get('attempt')} / "
                        f"{record.get('seed_set')}, not {n} / heldout-{n}")
    for field in ("approved_by", "approved_on"):
        if not str(record.get(field, "")).strip():
            problems.append(f"freeze field {field!r} is empty: the owner has not approved it")
    now = now if now is not None else current()
    for field in HASH_FIELDS:
        if record.get(field) != now[field]:
            problems.append(f"{field} differs from the freeze: frozen {record.get(field)!r}, "
                            f"now {now[field]!r}")
    return problems
