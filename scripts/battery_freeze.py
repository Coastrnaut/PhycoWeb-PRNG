"""Create or validate a feature-003 battery freeze (contracts/cli.md; FR-011, FR-013).

  battery_freeze.py create --attempt N --S S
  battery_freeze.py validate --attempt N

`create` writes a draft with empty approval fields; the owner approves it. Exit 0 on success,
2 if refused or invalid.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from protocol import battery_freeze  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("create", "validate"))
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--S", type=int)
    args = parser.parse_args(argv)
    try:
        if args.action == "create":
            if args.S is None:
                parser.error("create needs --S")
            from protocol import batteries
            rec = battery_freeze.create(args.attempt, args.S, batteries.commands())
            print(f"draft freeze written: {battery_freeze.freeze_path(args.attempt)} "
                  f"(S = {rec['S']}, threshold = {rec['threshold']:.3e}); owner approval needed")
            return 0
        problems = battery_freeze.validate(battery_freeze.load(args.attempt), args.attempt)
    except battery_freeze.FreezeError as exc:
        print(exc, file=sys.stderr)
        return 2
    for p in problems:
        print(p, file=sys.stderr)
    if problems:
        return 2
    print(f"freeze for attempt {args.attempt} is valid and approved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
