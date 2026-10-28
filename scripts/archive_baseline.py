"""Archive the floating-point PhycoWeb variants with SHA-256 hashes (spec FR-013).

Archived files are immutable: an existing file with a different hash aborts the run.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "baseline" / "float-v0"
MANIFEST = ARCHIVE / "MANIFEST.json"

# Last commit that changed readmee.md; pinned so later README edits cannot alter the archive.
READMEE_COMMIT = "0522cbc"
LISTING_HEADING = "2. Complete Bit-Accurate Python Verification Model"
LISTING_END = "Use code with caution."

# (archive name, git revision, path in that revision, note) — notes from research.md R4.
GIT_SOURCES = [
    ("MycoPRNG.py", "290e563^", "MycoPRNG.py",
     "Food passed in as arguments; threshold D[0] > 2000; max(1, ...) floor. Not the reference."),
    ("nist_bench.py", "d6980eb^", "nist_bench.py",
     "64-node grid, xorshift128* food, quadratic pressure term, D > 3276 saturation count, "
     "sp80022suite harness. Distinct design; not the reference."),
    ("nistrng_bench.py", "d6980eb^", "nistrng_bench.py",
     "xorshift128+-based engine with nistrng harness (int8 input; Cumulative Sums unreliable, "
     "research R6). Not the reference."),
    ("phycoweb_nist_eval.py", "d6980eb^", "phycoweb_nist_eval.py",
     "Initial D = 512; food_b into P[1]; disruption on D[0] or D[1]; XOR into P[0]/P[2]. "
     "Not the reference."),
]
README_NOTE = ("Reference behavior; lut-v1 preserves every stage except the perturbation source. "
               "Returns signed int32 words (research R2).")


def git_bytes(*args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.decode(errors='replace')}")
    return result.stdout


def extract_listing(readme: bytes) -> bytes:
    lines = readme.split(b"\n")
    heading = lines.index(LISTING_HEADING.encode())
    start = lines.index(b"python", heading) + 1
    end = lines.index(LISTING_END.encode(), start)
    return b"\n".join(lines[start:end]) + b"\n"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    readme = git_bytes("show", f"{READMEE_COMMIT}:readmee.md")
    entries = [("readmee_model.py", extract_listing(readme),
                f"readmee.md@{READMEE_COMMIT} (listing in section 2)", README_NOTE)]
    for name, rev, path, note in GIT_SOURCES:
        entries.append((name, git_bytes("show", f"{rev}:{path}"), f"{path}@{rev}", note))

    # Check every target before writing anything.
    for name, data, _, _ in entries:
        target = ARCHIVE / name
        if target.exists() and sha256(target.read_bytes()) != sha256(data):
            print(f"ERROR: {target.relative_to(ROOT)} exists with a different hash; "
                  "archived files are immutable.", file=sys.stderr)
            return 2

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    files = []
    for name, data, source, note in entries:
        target = ARCHIVE / name
        if target.exists():
            print(f"unchanged  {target.relative_to(ROOT).as_posix()}")
        else:
            target.write_bytes(data)
            print(f"archived   {target.relative_to(ROOT).as_posix()}")
        files.append({
            "archive_path": target.relative_to(ROOT).as_posix(),
            "source": source,
            "sha256": sha256(data),
            "note": note,
        })

    if MANIFEST.exists():
        previous = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if previous.get("files") == files:
            print(f"unchanged  {MANIFEST.relative_to(ROOT).as_posix()}")
            return 0

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": git_bytes("rev-parse", "HEAD").decode().strip(),
        "files": files,
    }
    with MANIFEST.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
    print(f"wrote      {MANIFEST.relative_to(ROOT).as_posix()} ({len(files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
