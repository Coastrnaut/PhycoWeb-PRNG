"""Feature 004: the owner's own records (contracts/cli.md; research R1, R19; REP-082, REP-083).

    owner_record.py environment --platform windows|wsl --by NAME [--written-approval WORDS]
    owner_record.py owner-provided --known KNOWN_ID --value TEXT --source TEXT --words TEXT
                                   --by NAME [--written-approval WORDS]

Each mode is an owner's own act, which the agent performs only on the owner's written approval,
given before the act and quoted in --written-approval (spec FR-044). Each prints the approval hash of
what it writes, kind `canonical`, and writes nothing unless standard input is an interactive
terminal and the owner types its first 16 hex digits, or --written-approval holds the owner's words,
which the record keeps. Its Review & Approval row, with that hash, is then added and committed. It
has no --reproduce: each mode records an owner's act, which a later run cannot regenerate.
"""
import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from protocol import evidence  # noqa: E402
from protocol.evidence import NONE, Refused  # noqa: E402

CODE = ["scripts/owner_record.py", "protocol/evidence.py", "protocol/disclaimer.py"]
# Research R1's interpreter and compiler per platform, the text of a protocol heading (PRO-078).
PYTHON = {"windows": "3.10.11", "wsl": "3.14.4"}
GCC = "15.2.0"
MARKER = re.compile(r'python_version\s*(>=|<)\s*"([\d.]+)"')


def pinned_python(platform: str) -> str:
    return PYTHON[platform]


def version_tuple(text: str) -> Tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def marker_holds(marker: str, python: str) -> bool:
    running = version_tuple(python)[:2]
    for operator, value in MARKER.findall(marker):
        wanted = version_tuple(value)[:2]
        if (operator == ">=" and running < wanted) or (operator == "<" and running >= wanted):
            return False
    return True


def pins_for(text: str, python: str) -> Dict[str, str]:
    """The pins of requirements.txt that apply to that Python, by their markers."""
    pins: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        requirement, _, marker = line.partition(";")
        name, _, version = requirement.strip().partition("==")
        if version and marker_holds(marker, python):
            pins[name.strip().lower()] = version.strip()
    return pins


def compare_with_pins(platform: str, snapshot: Dict) -> Dict:
    """The check the guard "Environment" makes of this one write: Python, gcc and each pinned
    package against research R1 and requirements.txt, exit 2 on any difference (PRO-068)."""
    python = pinned_python(platform)
    differences: List[str] = []
    if snapshot["python"] != python:
        differences.append(f"python {snapshot['python']}, not {python}")
    if platform == "wsl" and GCC not in str(snapshot.get("gcc")):
        differences.append(f"gcc {snapshot.get('gcc')}, not {GCC}")
    installed = {}
    for line in snapshot["packages"]:
        name, _, version = line.partition("==")
        installed[name.lower()] = version
    text = evidence.REPO.path("requirements.txt").read_bytes().decode("utf-8")
    pins = pins_for(text, snapshot["python"])
    for name, version in sorted(pins.items()):
        if installed.get(name) != version:
            differences.append(f"{name} {installed.get(name)}, not {version}")
    if differences:
        raise Refused("the running environment differs from research R1 and the pins: "
                      + "; ".join(differences))
    return {"python": snapshot["python"], "packages": pins}


def held(written: Optional[Dict]) -> Dict:
    """The field that keeps the owner's written approval, inside the hash it confirms."""
    return {} if written is None else {"written_approval": written}


def write_environment(platform: str, by: str, argv: List[str],
                      written: Optional[Dict] = None) -> int:
    if platform != evidence.platform_name():
        raise Refused(f"this is {evidence.platform_name()}, not {platform}")
    snapshot = evidence.snapshot()
    compared = compare_with_pins(platform, snapshot)
    run = evidence.Run("environment", directory="", file_name=f"environment-{platform}.json",
                       fixed=True, argv=argv, code_files=CODE, writes_evidence=False, analyst=by)
    with run:
        fields = {"snapshot": snapshot, "compared": compared, "inputs": NONE, "outputs": NONE}
        record = run.prepare("pass", assertions=[{"check": "research R1 and the pins",
                                                  "outcome": "pass"}],
                             fields=dict(fields, **held(written)))
        digits = evidence.approval_step(evidence.approval_hash(record), written)
        path = run.write(record, {"approved_by": by, "approved_utc": evidence.utc_now(),
                                  "approval_confirmed": digits})
    print(f"{evidence.rel_to_repo(path)} written; add its row \"Environment record <n>\" with that "
          "hash, set it to Approved and commit")
    return evidence.EXIT_OK


def write_owner_provided(args: argparse.Namespace, argv: List[str],
                         written: Optional[Dict] = None) -> int:
    run = evidence.manifest_run(argv, CODE)
    with run:
        entry = {"name": f"owner-provided: {args.known}", "status": "owner-provided",
                 "known": args.known, "source": args.source, "words": args.words,
                 "date_utc": evidence.utc_now(), "value": args.value,
                 "value_sha256": evidence.sha256(args.value.encode("utf-8")),
                 "environment": run.environment}
        entry.update(held(written))
        digits = evidence.approval_step(evidence.approval_hash(entry), written)
        entry.update({"approved_by": args.by, "approved_utc": evidence.utc_now(),
                      "approval_confirmed": digits})
        evidence.write_manifest(run, evidence.read_manifest() + [entry])
    print(f"{evidence.DOWNLOADS_REL}: entry written; add its row \"Owner-provided value <n>\" with "
          "that hash, set it to Approved and commit")
    return evidence.EXIT_OK


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    modes = parser.add_subparsers(dest="mode", required=True)
    environment = modes.add_parser("environment")
    environment.add_argument("--platform", required=True, choices=("windows", "wsl"))
    environment.add_argument("--by", required=True)
    environment.add_argument("--written-approval")
    provided = modes.add_parser("owner-provided")
    for name in ("--known", "--value", "--source", "--words", "--by"):
        provided.add_argument(name, required=True)
    provided.add_argument("--written-approval")
    args = parser.parse_args(argv)
    command = ["scripts/owner_record.py"] + list(argv if argv is not None else sys.argv[1:])

    def run() -> int:
        given = args.written_approval
        written = None if given is None else evidence.written_approval(given)
        if args.mode == "environment":
            return write_environment(args.platform, args.by, command, written)
        return write_owner_provided(args, command, written)

    return evidence.main_guard(run)


if __name__ == "__main__":
    sys.exit(main())
