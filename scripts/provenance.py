"""Feature 004: the provenance log's command (contracts/cli.md; data-model section 14).

    provenance.py add FILE       one entry, its fields in FILE
    provenance.py review FILE    one review entry, with `follows`

FILE is a JSON object holding the entry's fields but `seq`, `prev_sha256` and `date_utc`, which the
writer adds. The agent runs `review` only on the owner's explicit word for that entry, quoted with
its date in it. It writes log entries and no record, and so has no --reproduce mode.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from protocol import evidence, provenance  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("mode", choices=("add", "review"))
    parser.add_argument("file")
    args = parser.parse_args(argv)

    def run() -> int:
        fields = json.loads(Path(args.file).read_bytes().decode("utf-8"))
        entry = provenance.add(fields) if args.mode == "add" else provenance.review(fields)
        print(f"{provenance.LOG}: entry {entry['seq']}")
        return evidence.EXIT_OK

    return evidence.main_guard(run)


if __name__ == "__main__":
    sys.exit(main())
