"""Feature 004: the protocol change log's command (contracts/cli.md; data-model section 18).

    protocol_change.py check           the comparison alone; writes nothing
    protocol_change.py create          the first entries, from checklist-choices.md
    protocol_change.py propose FILE    one later entry, its fields in FILE

`create` and `propose` end in the approval step, an owner's own act that the agent never performs:
it prints the approval hash and appends nothing unless standard input is an interactive terminal and
the owner types its first 16 hex digits. It writes log entries and no record, and so has no
--reproduce mode.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from protocol import changelog, evidence  # noqa: E402


def report(result: dict) -> None:
    """Each place whose text changed, with its commit, the rows of its round listed under its rule
    and each place changed by an edit that no row made."""
    for item in result["rounds"]:
        print(item["heading"])
        for changed in item["changed"]:
            print(f"  {changed['rule']}: {', '.join(changed['places'])}; rows "
                  f"{', '.join(changed['rows']) or 'none'}")
    print(f"changed by an edit that no row made: {len(result['unmade'])}")
    for item in result["unmade"]:
        print(f"  {item['commit'][:7]} {item['rule']}: {', '.join(item['places'])}")
    print(f"compared to {result['compared_to'][:7]}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("mode", choices=("check", "create", "propose"))
    parser.add_argument("file", nargs="?")
    args = parser.parse_args(argv)

    def run() -> int:
        if args.mode == "check":
            report(changelog.check())
            return evidence.EXIT_OK
        if args.mode == "create":
            return changelog.create()
        if not args.file:
            raise evidence.Refused("propose needs FILE")
        fields = json.loads(Path(args.file).read_bytes().decode("utf-8"))
        entry = changelog.propose(fields)
        print(f"{changelog.LOG}: entry {entry['seq']}")
        return evidence.EXIT_OK

    return evidence.main_guard(run)


if __name__ == "__main__":
    sys.exit(main())
