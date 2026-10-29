"""Write a draft design-freeze record for a held-out attempt (contracts/cli.md; FR-016).

The approval fields are left empty; the owner fills them in. Exit 0 on success, 2 on refusal.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from protocol import freeze  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--dev-evidence", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        record = freeze.create(args.attempt, args.dev_evidence)
    except freeze.FreezeError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(record, indent=1))
    print(f"wrote draft {freeze.freeze_path(args.attempt)}. The owner must fill in "
          f"approved_by and approved_on before acceptance.py will run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
