
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "baseline"
REPORT_DIR = ROOT / "reports" / "phase-0"
REPORT_FILE = REPORT_DIR / "baseline_inventory.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return (result.stdout or result.stderr).strip()


def main() -> int:
    if not (ROOT / ".git").exists():
        print(f"WARNING: no .git directory found at {ROOT}")

    tracked_status = git_output("status", "--short", "--branch")
    print("Repository:", ROOT)
    print("\nGit status:\n", tracked_status or "(clean / no status output)")

    if not BASELINE.is_dir():
        print(f"\nWARNING: baseline directory not found: {BASELINE}")

    excluded = {".git", ".venv", "__pycache__", ".pytest_cache"}
    files = []

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue

        relative = path.relative_to(ROOT)
        if any(part in excluded for part in relative.parts):
            continue
        if REPORT_DIR in path.parents or path == REPORT_FILE:
            continue

        try:
            record = {
                "path": relative.as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "in_baseline": BASELINE in path.parents,
            }
            files.append(record)
        except OSError as exc:
            files.append({
                "path": relative.as_posix(),
                "error": str(exc),
            })

    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "repository": str(ROOT),
        "git_branch": git_output("branch", "--show-current"),
        "git_head": git_output("rev-parse", "HEAD"),
        "git_status": tracked_status,
        "files": files,
        "limitations": [
            "Inventory only; does not establish algorithm correctness.",
            "Hashes identify file contents at audit time.",
            "Review the Git status before treating this report as a baseline.",
        ],
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(f"\nInventoried {len(files)} files.")
    print(f"Report: {REPORT_FILE}")
    print("Review the report and Git diff before committing it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
