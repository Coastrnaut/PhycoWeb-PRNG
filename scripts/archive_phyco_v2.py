"""Archive phyco-v2 byte for byte (spec FR-042, SC-012; research R18; data-model section 12).

    archive_phyco_v2.py            copies the files into baseline/phyco-v2/ and writes MANIFEST.json
    archive_phyco_v2.py --check    exit 1 on any mismatch of a copy, its hash and its live source

Archived files are immutable: an archive that exists and differs exits 2, writing nothing. The live
files stay unchanged. The feature-001 script, scripts/archive_baseline.py, is left as it is.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "baseline" / "phyco-v2"
MANIFEST = ARCHIVE / "MANIFEST.json"
EXIT_OK, EXIT_MISMATCH, EXIT_REFUSED = 0, 1, 2
VECTOR_NOTE = "A golden vector of phyco-v2."
NOTES = {
    "phycoweb/model_v2.py": "The phyco-v2 reference model.",
    "phycoweb/lut.py": "The lookup table the model reads.",
    "fast/phyco_stream.c": "The C stream of phyco-v2.",
    "fast/lut_table.h": "The lookup table the C stream reads.",
    "specs/002-core-dynamics-redesign/design.md": "The phyco-v2 design document, version 1.0.",
}


class Refused(Exception):
    """The archive cannot be written; the message says why."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    if result.returncode != 0:
        raise Refused(f"git {' '.join(args)}: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout


def sources() -> List[str]:
    """The files of data-model section 12: the five it names and both vectors."""
    vectors = sorted(p.relative_to(ROOT).as_posix() for p in ROOT.glob("vectors/phyco-v2_*.hex"))
    if len(vectors) != 2:
        raise Refused(f"expected both vectors, found {vectors}")
    return list(NOTES) + vectors


def entry_for(rel: str) -> Dict:
    """A manifest entry; the source is committed unchanged, so that `path@commit` holds these bytes."""
    data = (ROOT / rel).read_bytes()
    if git("status", "--porcelain", "--", rel).strip():
        raise Refused(f"{rel} differs from HEAD: commit it first")
    commit = git("log", "-1", "--format=%h", "--abbrev=7", "--", rel).decode().strip()
    return {"archive_path": (ARCHIVE / Path(rel).name).relative_to(ROOT).as_posix(),
            "source": f"{rel}@{commit}", "sha256": sha256(data),
            "note": NOTES.get(rel, VECTOR_NOTE)}


def read_manifest() -> Optional[Dict]:
    return json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else None


def write() -> int:
    entries = [entry_for(rel) for rel in sources()]
    # Every target is checked before anything is written.
    for entry in entries:
        target = ROOT / entry["archive_path"]
        if target.exists() and sha256(target.read_bytes()) != entry["sha256"]:
            raise Refused(f"{entry['archive_path']} exists and differs; archived files are "
                          "immutable")
    previous = read_manifest()
    if previous is not None and previous["files"] != entries:
        raise Refused(f"{MANIFEST.relative_to(ROOT).as_posix()} exists and differs; archived files "
                      "are immutable")
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    for rel, entry in zip(sources(), entries):
        target = ROOT / entry["archive_path"]
        if not target.exists():
            target.write_bytes((ROOT / rel).read_bytes())
    if previous is None:
        manifest = {"created_utc": datetime.now(timezone.utc).isoformat(),
                    "git_head": git("rev-parse", "HEAD").decode().strip(), "files": entries}
        MANIFEST.write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    print(f"{ARCHIVE.relative_to(ROOT).as_posix()}: {len(entries)} files")
    return EXIT_OK


def mismatches() -> List[str]:
    """Every difference between a copy, its manifest hash and its live source."""
    manifest = read_manifest()
    if manifest is None:
        return [f"{MANIFEST.relative_to(ROOT).as_posix()} does not exist"]
    found = []
    listed = {MANIFEST.name}
    for entry in manifest["files"]:
        copy = ROOT / entry["archive_path"]
        live = ROOT / entry["source"].split("@", 1)[0]
        listed.add(copy.name)
        if not copy.is_file():
            found.append(f"{entry['archive_path']} is missing")
            continue
        data = copy.read_bytes()
        if sha256(data) != entry["sha256"]:
            found.append(f"{entry['archive_path']} differs from its manifest hash")
        if not live.is_file() or live.read_bytes() != data:
            found.append(f"{entry['archive_path']} differs from its live source")
    named = sorted(entry["source"].split("@", 1)[0] for entry in manifest["files"])
    if named != sorted(sources()):
        found.append("the manifest does not list the files of data-model section 12")
    found.extend(f"{path.name} is not in the manifest" for path in sorted(ARCHIVE.iterdir())
                 if path.name not in listed)
    return found


def check() -> int:
    found = mismatches()
    for line in found:
        print(line)
    print(f"{len(found)} mismatches")
    return EXIT_MISMATCH if found else EXIT_OK


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        return check() if args.check else write()
    except Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return EXIT_MISMATCH if args.check else EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
