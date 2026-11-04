"""Feature 004: the downloads manifest, $REP/downloads.json (contracts/cli.md; research R19).

    downloads.py init                                    the approved entries, from research R19
    downloads.py approve NAME                            one later file, from its row "Download <n>"
    downloads.py fetched NAME PATH [--pypi-sha256 HEX]   --pypi-sha256 required for a wheel
    downloads.py not-obtained NAME --reason TEXT

Run by the agent. A row "Download <n>" names the file in backticks, then `source:`, `size:` and
`licence:` fields separated by semicolons, with `stands in for:` where it replaces a listed file. A
downloaded file is read under -I by a child process in a directory of its own, and never run. It
has no --reproduce: its entries record outside facts, which a later run cannot regenerate.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from protocol import evidence  # noqa: E402
from protocol.evidence import Refused  # noqa: E402

CODE = ["scripts/downloads.py", "protocol/evidence.py", "protocol/disclaimer.py"]
BYTES = re.compile(r"^([\d,]+) bytes$")
HASH_FILE = ("import hashlib, os, sys; path = sys.argv[1]; "
             "data = open(path, 'rb').read(); "
             "print(hashlib.sha256(data).hexdigest(), len(data))")


def r19_rows() -> List[Dict]:
    """One row per file of research R19's two tables, as research.md holds them at HEAD."""
    text = evidence.show(evidence.RESEARCH_REL).decode("utf-8").replace("\r\n", "\n")
    start = text.index("## R19.")
    end = text.find("\n## ", start + 1)
    rows = []
    for line in text[start:end if end > 0 else len(text)].split("\n"):
        if not line.startswith("| ") or line.startswith(("| File |", "|---")):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
        name = re.match(r"`([^`]+)`", cells[0])
        if name is None or len(cells) < 4:
            raise Refused(f"research R19 holds a row that names no file: {line[:60]}")
        rows.append({"name": name.group(1), "source": cells[1], "size": cells[2],
                     "licence": cells[3]})
    return rows


def read_file(path: Path) -> Tuple[str, int]:
    """The SHA-256 and size, from a child under -I, its working directory outside the download's,
    so that nothing beside the file is imported and the file is never run."""
    done = subprocess.run((sys.executable, "-I", "-c", HASH_FILE, str(path.resolve())),
                          capture_output=True, text=True, cwd=str(ROOT))
    if done.returncode != 0:
        raise evidence.ToolFailure(f"{path}: {done.stderr.strip()}")
    digest, size = done.stdout.split()
    return digest, int(size)


def bytes_given(size: str) -> Optional[int]:
    match = BYTES.match(size.strip())
    return int(match.group(1).replace(",", "")) if match else None


def download_row(name: str) -> evidence.Row:
    rows = [r for r in evidence.head_table()
            if re.fullmatch(r"Download \d+", r.name) and f"`{name}`" in r.notes]
    if not rows:
        raise Refused(f"no row \"Download <n>\" names {name} at HEAD")
    if rows[-1].decision != "Approved":
        raise Refused(f"the row {rows[-1].name!r} does not read Approved at HEAD")
    return rows[-1]


def row_field(notes: str, name: str) -> str:
    match = re.search(rf"\b{name}:\s*([^;]+)", notes)
    if match is None:
        raise Refused(f"the row names no {name}")
    return match.group(1).strip()


def approved_entry(entries: List[Dict], name: str) -> Dict:
    for entry in entries:
        if entry["name"] == name and entry["status"] == "approved":
            return entry
    raise Refused(f"no `approved` entry holds {name}")


def init(run: evidence.Run) -> None:
    if evidence.REPO.path(evidence.DOWNLOADS_REL).exists():
        raise Refused(f"{evidence.DOWNLOADS_REL} exists")
    entries = [dict(row, status="approved", environment=run.environment) for row in r19_rows()]
    evidence.write_manifest(run, entries)


def approve(run: evidence.Run, name: str) -> None:
    entries = evidence.read_manifest()
    if any(entry["name"] == name for entry in entries):
        raise Refused(f"an entry holds {name}: a later copy takes a name of its own")
    row = download_row(name)
    entry = {"name": name, "status": "approved", "row": row.name, "environment": run.environment,
             "source": row_field(row.notes, "source"), "size": row_field(row.notes, "size"),
             "licence": row_field(row.notes, "licence")}
    match = re.search(r"\bstands in for:\s*`([^`]+)`", row.notes)
    if match:
        entry["stands_in_for"] = match.group(1)
    evidence.write_manifest(run, entries + [entry])


def fetched(run: evidence.Run, name: str, path: Path, pypi_sha256: Optional[str]) -> None:
    entries = evidence.read_manifest()
    entry = approved_entry(entries, name)
    digest, size = read_file(path)
    given = bytes_given(entry["size"])
    if given is not None and given != size:
        raise Refused(f"{name}: {size} bytes, not the {given} its row gives")
    if name.endswith(".whl"):
        if pypi_sha256 is None:
            raise Refused(f"{name}: a wheel needs --pypi-sha256")
        if pypi_sha256 != digest:
            raise Refused(f"{name}: SHA-256 {digest}, not PyPI's {pypi_sha256}")
    entry.update({"status": "fetched", "sha256": digest, "sha256_kind": "raw", "bytes": size,
                  "date_utc": evidence.utc_now(), "local_path": str(path),
                  "environment": run.environment})
    evidence.write_manifest(run, entries)


def not_obtained(run: evidence.Run, name: str, reason: str) -> None:
    entries = evidence.read_manifest()
    entry = approved_entry(entries, name)
    entry.update({"status": "not obtained", "reason": reason, "environment": run.environment})
    evidence.write_manifest(run, entries)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    modes = parser.add_subparsers(dest="mode", required=True)
    modes.add_parser("init")
    modes.add_parser("approve").add_argument("name")
    got = modes.add_parser("fetched")
    got.add_argument("name")
    got.add_argument("path")
    got.add_argument("--pypi-sha256")
    missing = modes.add_parser("not-obtained")
    missing.add_argument("name")
    missing.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    command = ["scripts/downloads.py"] + list(argv if argv is not None else sys.argv[1:])

    def run() -> int:
        manifest = evidence.manifest_run(command, CODE)
        with manifest:
            if args.mode == "init":
                init(manifest)
            elif args.mode == "approve":
                approve(manifest, args.name)
            elif args.mode == "fetched":
                fetched(manifest, args.name, Path(args.path), args.pypi_sha256)
            else:
                not_obtained(manifest, args.name, args.reason)
        print(f"{evidence.DOWNLOADS_REL}: {args.mode}")
        return evidence.EXIT_OK

    return evidence.main_guard(run)


if __name__ == "__main__":
    sys.exit(main())
