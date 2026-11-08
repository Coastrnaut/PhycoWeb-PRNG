"""Feature 004: removes a stale lock (contracts/cli.md; data-model section 1; research R7, R16).

    clear_lock.py LOCK      data/heavy-run.lock or data/log-append.lock

Run by the owner or at the owner's request. It removes LOCK only when it can show, in the lock's
environment, that no process with the lock's PID and start time still runs; otherwise it exits 2 and
removes nothing. It writes a `lock-cleared` record and, for the heavy-run lock, the `inconclusive`
record of the run that died holding it, or FR-053's test's closing `projection` record, which the
`lock-cleared` record names. A `lock-cleared` record records an event and is not reproduced, so
this script has no --reproduce mode.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from protocol import evidence  # noqa: E402
from protocol.evidence import NONE, Refused  # noqa: E402

CODE = ["scripts/clear_lock.py", "protocol/evidence.py", "protocol/disclaimer.py"]
OUTSIDE = ("a reboot, a power loss or an update ended the run; its partial outputs were discarded "
           "unread and it gave no result")
DIED = ("the run died holding the lock; its partial outputs were discarded unread, and its hours "
        "used are the most it can have used, since nothing else shows when it died")
# What the record of a dead run states of itself, which no field of its description replaces.
OWN_FIELDS = ("record_id", "kind", "status", "classification", "exit_status", "assertions",
              "limitations", "outputs", "inputs", "model_id", "variant_id")


def partial_of(lock: Dict) -> Optional[Path]:
    """The temporary directory of the run that holds the lock, its latest with a description."""
    found = sorted(evidence.REPO.path(evidence.PARTIAL_REL).glob(f"{lock['pid']}-*"))
    with_file = [p for p in found if (p / evidence.RUN_FILE).exists()]
    return with_file[-1] if with_file else None


def run_aborted(record_path: Path) -> None:
    """The run on a candidate is charged and the log cites its record (cli, evidence_v3.py)."""
    script = evidence.REPO.path("scripts/evidence_v3.py")
    if not script.exists():
        raise evidence.ToolFailure("scripts/evidence_v3.py does not exist")
    subprocess.run((sys.executable, str(script), "--aborted", str(record_path)), check=True)


def hours_and_end(lock: Dict, created: str) -> Tuple[float, str]:
    """The hours to the clearing, or, where the boot time of the lock's environment is later than
    the time the lock holds, to that boot time, the run having ended from outside."""
    boot = evidence.boot_time(lock["environment"])
    if boot > lock["time"]:
        return evidence.hours_between(lock["time"], boot), boot
    return evidence.hours_between(lock["time"], created), NONE


def write_dead_run(lock: Dict, partial: Path, argv: List[str]) -> Tuple[Path, Dict]:
    """The `inconclusive` record that every started run writes, with the fields its description
    gives that the readers of its kind find a record by, such as a control's test and size and the
    rows it charges (research R7, "Runs ended from outside")."""
    described = json.loads((partial / evidence.RUN_FILE).read_bytes().decode("utf-8"))
    created = evidence.utc_now()
    used, ended = hours_and_end(lock, created)
    statement = OUTSIDE if ended != NONE else DIED
    if described["kind"] == "projection":
        path = evidence.write_projection(
            run=described.get("run", NONE), row=described["row"],
            inputs=described.get("inputs", NONE),
            measured_speed=described.get("measured_speed", NONE),
            projected_hours=described.get("projected_hours"), time_hours=used,
            statement="the test ended there and kept none", status="inconclusive", argv=argv,
            code_files=CODE, writes_evidence=False,
            extra={"created_utc": created, "ended_outside": ended, "heavy_run": True,
                   "command": lock["command"], "limitations": [statement]})
        return path, described
    run = evidence.Run(described["kind"], candidate=described.get("candidate"),
                       model_id=described.get("model_id"), variant_id=described.get("variant_id"),
                       directory=described["directory"], config=described.get("config"),
                       inputs=described.get("inputs", NONE), workers=described.get("workers", 1),
                       threads=described.get("threads", 1), argv=argv, code_files=CODE,
                       writes_evidence=False, heavy=False)
    run.heavy = False
    fields = {name: value for name, value in (described.get("fields") or {}).items()
              if name not in OWN_FIELDS}
    fields.update({"created_utc": created, "ended_outside": ended, "heavy_run": True,
                   "command": lock["command"],
                   "hours": {"projected": described.get("projected_hours"), "used": used}})
    with run:
        path = run.finish("inconclusive", exit_status=evidence.EXIT_TOOL, limitations=[statement],
                          fields=fields)
    return path, described


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("lock", type=lambda text: Path(text).as_posix())
    args = parser.parse_args(argv)
    command = ["scripts/clear_lock.py", args.lock]

    def run() -> int:
        path = evidence.REPO.path(args.lock)
        if args.lock not in (evidence.HEAVY_LOCK_REL, evidence.APPEND_LOCK_REL):
            raise Refused(f"{args.lock} is neither of the two locks")
        if not path.exists():
            raise Refused(f"{args.lock} does not exist")
        lock = evidence.read_lock(path)
        try:
            running = evidence.holder_runs(lock)
        except (OSError, ValueError, KeyError, evidence.ToolFailure) as exc:
            raise Refused(f"it cannot be shown that the holder is gone: {exc}") from None
        if running:
            raise Refused(f"{args.lock}: its holder still runs")
        evidence.guard_environment("lock-cleared")
        evidence.guard_protocol_log("lock-cleared")
        named: object = NONE
        partial = None
        if args.lock == evidence.HEAVY_LOCK_REL:
            partial = partial_of(lock)
            if partial is None:
                raise evidence.ToolFailure(f"no description of the run of PID {lock['pid']} under "
                                           f"{evidence.PARTIAL_REL}")
            record_path, described = write_dead_run(lock, partial, command)
            record = json.loads(record_path.read_bytes().decode("utf-8"))
            named = {"record_id": record["record_id"], "path": evidence.rel_to_repo(record_path),
                     "sha256": evidence.sha256(record_path.read_bytes()), "sha256_kind": "raw"}
            if described.get("candidate"):
                run_aborted(record_path)
        evidence.write_simple_record("lock-cleared", "locks",
                                     {"lock": lock, "lock_file": args.lock, "run_record": named},
                                     argv=command, code_files=CODE, writes_evidence=False)
        if partial is not None:
            shutil.rmtree(partial, ignore_errors=True)
        path.unlink()
        print(f"{args.lock}: removed")
        return evidence.EXIT_OK

    return evidence.main_guard(run)


if __name__ == "__main__":
    sys.exit(main())
