"""Feature 004: repairs a broken hash chain in one of the three logs (contracts/cli.md).

    repair_log.py --log LOG --approval REF

Only with the owner's go-ahead: REF names the row "Log repair <n>", which must read Approved at HEAD
and name the same log and the `seq` of the break. The broken file is kept unchanged with its
SHA-256, and the `repair` entry goes through the log's one writer as the one append to a broken
chain. In the protocol change log it goes through the owner's approval step, as every entry does. It
writes log entries and no record, and so has no --reproduce mode.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from protocol import changelog, evidence, provenance  # noqa: E402


def writer(log: str):
    """The log's one writer; protocol/candidates.py, written later, is imported only when needed."""
    if log == evidence.PROTOCOL_LOG_REL:
        return changelog.repair
    if log == evidence.PROVENANCE_LOG_REL:
        return provenance.repair
    if log == evidence.CANDIDATE_LOG_REL:
        from protocol import candidates
        return candidates.repair
    raise evidence.Refused(f"{log} is none of the three logs")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--log", required=True)
    parser.add_argument("--approval", required=True)
    args = parser.parse_args(argv)

    def run() -> int:
        entry = writer(args.log)(args.approval)
        counted = sum(1 for e in entry["repair"]["entries_after"] if e["counts"])
        print(f"{args.log}: repair entry {entry['seq']}; {counted} of "
              f"{len(entry['repair']['entries_after'])} entries after the break count")
        return evidence.EXIT_OK

    return evidence.main_guard(run)


if __name__ == "__main__":
    sys.exit(main())
