"""Feature 004: the candidate log's command (contracts/cli.md; data-model section 3).

    candidate_log.py propose FILE    a proposed entry, before any tool runs on it
    candidate_log.py mapping FILE    a candidate's mapping entry, before its first score
    candidate_log.py enter           one entered-d4 entry per candidate of the entered set
    candidate_log.py decide FILE     a decision, with the replacement entry it brings
    candidate_log.py correct FILE    a correction entry, citing the seq it corrects
    candidate_log.py replace FILE    closes a pending replacement entry, with its reason
    candidate_log.py outcome FILE    a review-outcome entry, after the review's row

FILE is a JSON object holding the entry's fields but `seq`, `prev_sha256` and `date_utc`, which the
writer adds. Every refusal of the log writer exits 2 and appends nothing. It writes log entries and
no record, and so has no --reproduce mode.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from protocol import candidates, evidence  # noqa: E402

WITH_FILE = {"propose": candidates.propose, "mapping": candidates.mapping,
             "decide": candidates.decide, "correct": candidates.correct,
             "replace": candidates.replace, "outcome": candidates.outcome}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("mode", choices=tuple(WITH_FILE) + ("enter",))
    parser.add_argument("file", nargs="?")
    args = parser.parse_args(argv)

    def run() -> int:
        if args.mode == "enter":
            written = candidates.enter()
        else:
            if not args.file:
                raise evidence.Refused(f"{args.mode} needs FILE")
            fields = json.loads(Path(args.file).read_bytes().decode("utf-8"))
            if not isinstance(fields, dict):
                raise evidence.Refused("FILE holds no JSON object")
            written = WITH_FILE[args.mode](fields)
        for entry in written if isinstance(written, list) else [written]:
            print(f"{candidates.LOG}: entry {entry['seq']}, {entry['event']}")
        return evidence.EXIT_OK

    return evidence.main_guard(run)


if __name__ == "__main__":
    sys.exit(main())
