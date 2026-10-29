"""Derive, print or check the feature-002 seed sets (contracts/cli.md).

Printing a held-out set is allowed: its seeds are already public in the spec, and printing
them is not use.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from protocol import seedsets  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--set", choices=sorted(seedsets.FINGERPRINTS), dest="name")
    parser.add_argument("--print", action="store_true", dest="do_print")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not (args.check or (args.do_print and args.name)):
        parser.print_usage(sys.stderr)
        return 2
    if args.check:
        ok = True
        for name, expected in seedsets.FINGERPRINTS.items():
            actual = seedsets.fingerprint(seedsets.derive(name))
            print(f"{name:10s} {actual} {'OK' if actual == expected else 'MISMATCH'}")
            ok &= actual == expected
        if not ok:
            return 2
    if args.do_print and args.name:
        try:
            seeds = seedsets.load(args.name, allow={args.name})
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 2
        sys.stdout.write(seedsets.canonical_text(seeds))
    return 0


if __name__ == "__main__":
    sys.exit(main())
