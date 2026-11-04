"""The FUT-SEC-8 demonstration (spec FR-001 to FR-003; research R2; data-model section 4; WSL).

    fut_sec8.py --binary fast/build/seed_search --out-dir $REP/fut-sec-8
                [(--repeat-after-defect ID | --repeat-after-end RECORD) --owner-request "WORDS (DATE)"]
    fut_sec8.py --verify RECORD
    fut_sec8.py --reproduce RECORD --binary fast/build/seed_search --owner-request "WORDS (DATE)"

For each of three development targets, the first two seed words are revealed and every one of the
2^32 candidates for the last two is tried against the first three output words. One pass per target,
a heavy run; a repeat runs only on the owner's request, quoted with its date, after a recorded tool
defect or a pass ended from outside that no earlier record names. --verify re-checks a record's
listed matches with the Python model, with no sweep. This script makes no security claim.
"""
import argparse
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from phycoweb.model_v2 import MODEL_ID, WARMUP, PhycoWebEngineV2  # noqa: E402
from protocol import evidence, seedsets  # noqa: E402
from protocol.disclaimer import DESIGN_DISCLAIMER  # noqa: E402
from protocol.evidence import NONE, Refused, ToolFailure  # noqa: E402

BINARY = "fast/build/seed_search"
MODEL = "phycoweb/model_v2.py"
MAKE_FILE = "fast/seed_search.mk"
CODE = ["scripts/fut_sec8.py", "protocol/evidence.py", "protocol/disclaimer.py",
        "protocol/devinputs_v3.py", "protocol/seedsets.py", MODEL, "phycoweb/lut.py",
        "fast/seed_search.c", "fast/lut_table.h", MAKE_FILE, BINARY]
MODEL_SHA256 = "1260142d1205f5d7340cf3f82ed557bbe9dc7bb5de370e668688964d01f1c2ec"
SEED_SET = "dev"
NAMESPACE = "feature-002/dev"
TARGETS = 3
THREADS = 32
CANDIDATES = 2 ** 32
LEVEL = 0.01
# False matches per target after one, two and three words of 32 bits, the target left out.
MEAN_AFTER = {"one": (CANDIDATES - 1) / 2 ** 32, "two": (CANDIDATES - 1) / 2 ** 64,
              "three": (CANDIDATES - 1) / 2 ** 96}
ASSUMPTION = ("Each candidate's output words are uniform and independent of the target's. phyco-v2's "
              "biases (S12, S14) could make false matches more frequent, so a count above the "
              "baseline is an observation about phyco-v2 and does not change the success criterion.")
PROBE_SECONDS = 30
PROGRESS_SECONDS = 60
PROGRESS = re.compile(r"^progress: (\d+) of (\d+) s2 values in (\d+) s$")
REQUEST = re.compile(r"^.+\(\d{4}-\d{2}-\d{2}\)$", re.S)
RECORDS = "fut-sec-8"
OUT_DIR = evidence.REP_REL + "/" + RECORDS
Seed = Tuple[int, int, int, int]


def guard_platform() -> None:
    if evidence.platform_name() != "wsl":
        raise Refused("the search tool is built and run in WSL")


def targets() -> List[Seed]:
    """The first three seeds of feature 002's `dev` set; a held-out set exits 2."""
    try:
        return list(seedsets.load(SEED_SET, allow=("dev",))[:TARGETS])
    except (PermissionError, ValueError) as exc:
        raise Refused(str(exc)) from None


def words_of(seed: Sequence[int], count: int) -> List[int]:
    engine = PhycoWebEngineV2(seed)
    return [engine.compute_block() for _ in range(count)]


def guard_model(root: Path) -> str:
    digest = evidence.sha256((root / MODEL).read_bytes())
    if digest != MODEL_SHA256:
        raise Refused(f"{MODEL} hashes {digest}, not {MODEL_SHA256}")
    return digest


def guard_paths(binary: str, out_dir: Optional[str] = None) -> None:
    if Path(binary).as_posix() != BINARY:
        raise Refused(f"--binary {binary}: the tool is {BINARY}")
    if out_dir is not None:
        given = Path(out_dir).as_posix().rstrip("/")
        if given != OUT_DIR and Path(out_dir).resolve() != evidence.REPO.path(OUT_DIR).resolve():
            raise Refused(f"--out-dir {out_dir}: the demonstration's place is {OUT_DIR}")


# ---------------------------------------------------------------------------------- the tool

def run_tool(binary: Path, args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess:
    """The tool's stdout is read; its progress goes on to this run's stderr."""
    return subprocess.run([str(binary), *args], cwd=cwd, stdout=subprocess.PIPE, text=True,
                          check=False)


def sweep_arguments(target: Seed, progress: int) -> List[str]:
    words = [f"{word:08X}" for word in words_of(target, 3)]
    return ["--s0", str(target[0]), "--s1", str(target[1]), "--words", *words,
            "--threads", str(THREADS), "--progress", str(progress)]


def vector_check(binary: Path, cwd: Path) -> List[Dict]:
    """Both golden files, before any sweep; any mismatch stops the run (FR-002)."""
    files = sorted(p.relative_to(cwd).as_posix() for p in cwd.glob("vectors/phyco-v2_*.hex"))
    done = run_tool(binary, ["--check-vectors", *files], cwd)
    if done.returncode != 0:
        raise ToolFailure(f"the vector check exited {done.returncode}: {done.stdout.strip()}")
    return json.loads(done.stdout)["files"]


def sweep(binary: Path, cwd: Path, target: Seed) -> Dict:
    done = run_tool(binary, sweep_arguments(target, PROGRESS_SECONDS), cwd)
    if done.returncode != 0:
        raise ToolFailure(f"the sweep exited {done.returncode}")
    return json.loads(done.stdout)


def project(binary: Path, cwd: Path, target: Seed, passes: int = TARGETS) -> Tuple[float, Dict]:
    """At most 60 s of the first target's sweep, stopped: its hours and measured speed, from its
    progress lines alone. Its other outputs are discarded unread (spec, Development inputs)."""
    process = subprocess.Popen([str(binary), *sweep_arguments(target, 5)], cwd=cwd,
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    deadline = time.monotonic() + PROBE_SECONDS
    rows, total, seconds = 0, 1, 0
    try:
        for line in process.stderr:
            match = PROGRESS.match(line.strip())
            if match:
                rows, total, seconds = (int(value) for value in match.groups())
            if time.monotonic() >= deadline or (total and rows >= total):
                break
    finally:
        process.kill()
        process.wait()
    if rows == 0 or seconds == 0:
        raise ToolFailure("the projection saw no progress")
    per_second = rows / seconds
    return passes * total / per_second / 3600.0, {"s2_values_per_second": per_second}


# ------------------------------------------------------------------------------- the analysis

def poisson_p(count: int, mean: float) -> float:
    """Two-sided: twice the smaller tail, at most 1."""
    term = math.exp(-mean)
    below = 0.0
    for k in range(count):
        below += term
        term *= mean / (k + 1)
    lower = below + term
    upper = 1.0 - below
    return min(1.0, 2.0 * min(lower, upper))


def poisson_test(count: int, mean: float) -> Dict:
    p = poisson_p(count, mean)
    return {"count": count, "mean": mean, "p": p, "level": LEVEL, "agrees": p >= LEVEL}


def is_match(result: Dict, target: Seed) -> bool:
    return [target[2], target[3]] in result["three_word_matches"]


def false_count(result: Dict, target: Seed, after: str) -> int:
    return result[f"after_{after}"] - (1 if is_match(result, target) else 0)


def listed(target: Seed, result: Dict) -> List[Dict]:
    """Every three-word match, any extra one separated by the fourth word."""
    fourth = words_of(target, 4)[3]
    out = []
    for s2, s3 in result["three_word_matches"]:
        word = words_of((target[0], target[1], s2, s3), 4)[3]
        out.append({"s2": s2, "s3": s3, "is_target": (s2, s3) == target[2:],
                    "fourth_word": f"{word:08X}", "fourth_word_matches": word == fourth})
    return sorted(out, key=lambda item: (item["s2"], item["s3"]))


def match_summary(seeds: Sequence[Seed], results: Sequence[Dict]) -> Dict:
    per_target = []
    deviations = []
    for number, (seed, result) in enumerate(zip(seeds, results)):
        false = {after: false_count(result, seed, after) for after in MEAN_AFTER}
        per_target.append({"target": number, "after_one": result["after_one"],
                           "after_two": result["after_two"], "after_three": result["after_three"],
                           "false_after_one": false["one"], "false_after_two": false["two"],
                           "false_after_three": false["three"],
                           "expected_false": dict(MEAN_AFTER),
                           "poisson": poisson_test(false["one"], MEAN_AFTER["one"])})
        for after in ("two", "three"):
            if false[after]:
                deviations.append({"target": number, "after": after, "count": false[after]})
    pooled = sum(entry["false_after_one"] for entry in per_target)
    pool = poisson_test(pooled, len(seeds) * MEAN_AFTER["one"])
    return {"per_target": per_target, "pooled": pool, "deviations": deviations,
            "agrees": pool["agrees"] and not deviations
            and all(entry["poisson"]["agrees"] for entry in per_target)}


def cost_of(results: Sequence[Dict]) -> Dict:
    steps = sum(result["total_steps"] for result in results)
    seconds = sum(result["seconds"] for result in results)
    candidates = sum(result["candidates"] for result in results)
    per_candidate = steps / candidates
    rate = steps / seconds
    seeds = 2 ** 64
    return {"per_target": [{"total_steps": r["total_steps"], "seconds": r["seconds"],
                            "steps_per_second": r["steps_per_second"]} for r in results],
            "steps_per_candidate": per_candidate, "total_steps": steps, "seconds": seconds,
            "steps_per_second": rate,
            "extrapolation": {"seeds": seeds, "steps": per_candidate * seeds,
                              "seconds": per_candidate * seeds / rate,
                              "seconds_per_candidate": seconds / candidates}}


def tool_field(root: Path, binary: Path) -> Dict:
    text = (root / MAKE_FILE).read_bytes().decode("utf-8")
    flags = re.search(r"^CFLAGS := (.+)$", text, re.M)
    return {"source_sha256": evidence.sha256((root / "fast/seed_search.c").read_bytes()),
            "binary_sha256": evidence.sha256(binary.read_bytes()),
            "compiler": evidence.snapshot().get("gcc", NONE),
            "flags": flags.group(1).strip() if flags else NONE, "threads": THREADS}


def report_of(fields: Dict, git_head: str) -> Dict:
    """The nine items of security.md section 12.4, with T1 as the attacker."""
    matches, cost = fields["matches"], fields["cost"]
    return {
        "1_attack_and_target_property": "Exhaustive search of the last two of phyco-v2's four "
        "16-bit seed words. Target property: the 64-bit seed, which bounds security strength "
        "against T1 at 64 bits (security.md S3).",
        "2_attacker": "T1, the known-output attacker of security.md section 5, who knows the "
        "design and the position of the observed words, here the first words after the warm-up. "
        "An unknown position would add a search over the offset.",
        "3_observations_and_inputs": {"revealed": "the first two seed words of each target",
                                      "observed": "the first three output words after the "
                                      f"{WARMUP}-step warm-up", "targets": len(fields["targets"])},
        "4_analysis": {"expected_false_matches": dict(MEAN_AFTER), "assumption": ASSUMPTION,
                       "test": "per target against a Poisson distribution of mean (2^32 - 1)/2^32 "
                       "and pooled against three times it, two-sided at level 0.01"},
        "5_implementation": dict(fields["tool"], source="fast/seed_search.c",
                                 driver="scripts/fut_sec8.py"),
        "6_results": {"recovered": fields["recovered"], "matches": matches,
                      "vector_check": fields["vector_check"]},
        "7_complexity": {"data": "three 32-bit output words per target",
                         "time": {key: cost[key] for key in ("steps_per_candidate", "total_steps",
                                                             "seconds", "steps_per_second")},
                         "memory": "one generator state per thread",
                         "extrapolation": cost["extrapolation"]},
        "8_reproduction": {"revision": git_head, "command": "scripts/fut_sec8.py --reproduce, "
                           "after the FUT-SEC-8 result review, on the owner's request",
                           "check": "scripts/fut_sec8.py --verify RECORD"},
        "9_implications_and_limitations": "The seed bound of phyco-v2 is reproduced on a reduced "
        "domain: two seed words are revealed and 2^32 candidates tried per target, and the cost of "
        "all 2^64 seeds is extrapolated, not executed. It says nothing about phyco-v3 or any other "
        "model, and no result here is a claim about any model's strength.",
        "disclaimer": DESIGN_DISCLAIMER,
    }


def measure(binary: Path, cwd: Path, seeds: Sequence[Seed], git_head: str) -> Dict:
    """The vector check, then one sweep per target; the record's fields of data-model section 4."""
    checked = vector_check(binary, cwd)
    results = [sweep(binary, cwd, seed) for seed in seeds]
    fields: Dict[str, Any] = {
        "targets": [list(seed) for seed in seeds],
        "revealed": [list(seed[:2]) for seed in seeds],
        "observed": [{"positions": [1, 2, 3], "words": [f"{word:08X}" for word in words_of(seed, 3)]}
                     for seed in seeds],
        "tool": tool_field(cwd, binary), "vector_check": checked,
        "matches": match_summary(seeds, results), "assumption": ASSUMPTION,
        "listed": [listed(seed, result) for seed, result in zip(seeds, results)],
        "recovered": [is_match(result, seed) for seed, result in zip(seeds, results)],
        "cost": cost_of(results), "model_sha256": guard_model(cwd)}
    fields["report"] = report_of(fields, git_head)
    return fields


def verdict(fields: Dict) -> Tuple[str, str, int, List[Dict]]:
    """Status, classification, exit status and assertions, by data-model section 1's table."""
    recovered = all(fields["recovered"])
    assertions = [{"check": f"target {number} recovered", "outcome": "pass" if found else "fail"}
                  for number, found in enumerate(fields["recovered"])]
    agrees = fields["matches"]["agrees"]
    assertions.append({"check": "false matches agree with the baseline",
                       "outcome": "pass" if agrees else "fail"})
    if not recovered:
        return "fail", NONE, evidence.EXIT_VERDICT, assertions
    outcome = "recovered" if agrees else "disagreement"
    return "pass", evidence.classify("demonstration", outcome), evidence.EXIT_OK, assertions


# ------------------------------------------------------------------------------- the three modes

def inputs_field() -> Dict:
    return {"namespace": NAMESPACE, "kind": "seed", "index_range": [0, TARGETS - 1],
            "fingerprint": seedsets.FINGERPRINTS[SEED_SET]}


def earlier_records() -> List[Dict]:
    return [record for _, record in evidence.iter_records("demonstration", RECORDS)]


def guard_request(request: Optional[str]) -> str:
    if not request or not REQUEST.match(request):
        raise Refused("a repeat runs only on the owner's request: --owner-request \"WORDS (DATE)\"")
    return request


def repeat_fields(args: argparse.Namespace, records: Sequence[Dict]) -> Dict:
    """`supersedes`, `defect` and `owner_request`, all `none` in the first record; a second run
    without a new defect or an ended pass, and the owner's request, exits 2."""
    by_id = {record["record_id"]: record for record in records}
    defect, ended = args.repeat_after_defect, args.repeat_after_end
    if not records:
        if defect or ended or args.owner_request:
            raise Refused("no earlier record: the first run is no repeat")
        return {"supersedes": NONE, "defect": NONE, "owner_request": NONE}
    if not defect and not ended:
        raise Refused("one pass per target: a record exists, and only --repeat-after-defect or "
                      "--repeat-after-end, on the owner's request, runs again")
    request = guard_request(args.owner_request)
    if defect:
        # A record that shows the fault: a target missed, or a crash (research R7's tool defects).
        record = by_id.get(defect)
        if record is None or record.get("exit_status") == evidence.EXIT_OK \
                or record.get("ended_outside", NONE) != NONE:
            raise Refused(f"{defect} is no recorded tool defect of the demonstration")
        if any(earlier.get("defect") == defect for earlier in records):
            raise Refused(f"an earlier record already names the defect {defect}")
        latest = max(records, key=lambda item: item["created_utc"])
        return {"supersedes": latest["record_id"], "defect": defect, "owner_request": request}
    record = by_id.get(ended)
    if record is None or record.get("ended_outside", NONE) == NONE:
        raise Refused(f"{ended} is no record of a pass ended from outside")
    if any(earlier.get("supersedes") == ended for earlier in records):
        raise Refused(f"an earlier record already names the ended pass {ended}")
    return {"supersedes": ended, "defect": NONE, "owner_request": request}


def demonstrate(args: argparse.Namespace, command: List[str]) -> int:
    guard_platform()
    guard_paths(args.binary, args.out_dir)
    root = evidence.REPO.root
    guard_model(root)
    seeds = targets()
    repeat = repeat_fields(args, earlier_records())
    binary = root / BINARY
    run = evidence.Run("demonstration", model_id=MODEL_ID, code_files=CODE, argv=command,
                       inputs=inputs_field(), heavy=True, threads=THREADS, namespace=NAMESPACE,
                       config={"threads": THREADS, "warmup": WARMUP})
    with run:
        started = time.monotonic()
        hours, speed = project(binary, root, seeds[0])
        row = evidence.FEATURE_ROW if repeat["supersedes"] != NONE else evidence.FUT_SEC_8_ROW
        evidence.write_projection(run="the FUT-SEC-8 demonstration", row=row, inputs=inputs_field(),
                                  measured_speed=speed, projected_hours=hours, argv=command,
                                  code_files=CODE, time_hours=(time.monotonic() - started) / 3600)
        if repeat["supersedes"] != NONE:
            evidence.guard_feature_row([hours])
        run.begin(hours)
        fields = measure(binary, root, seeds, evidence.head())
        fields.update(repeat)
        status, classification, exit_status, assertions = verdict(fields)
        path = run.finish(status, classification=classification, exit_status=exit_status,
                          assertions=assertions, fields=fields)
    print(f"{evidence.rel_to_repo(path)}: {status}, {sum(fields['recovered'])} of "
          f"{len(seeds)} targets recovered")
    return exit_status


def read_record(reference: str) -> Tuple[Path, Dict]:
    path = Path(reference)
    if path.is_file():
        return path, json.loads(path.read_bytes().decode("utf-8"))
    found = evidence.find_record(reference)
    if found is None:
        raise Refused(f"no record {reference}")
    return found


def disagreements(record: Dict) -> List[str]:
    """Every listed three-word match and every recovered seed, against the Python model."""
    found = []
    for number, seed in enumerate(record["targets"]):
        words = [f"{word:08X}" for word in words_of(seed, 4)]
        if record["observed"][number]["words"] != words[:3]:
            found.append(f"target {number}: the observed words differ")
        hit = False
        for item in record["listed"][number]:
            candidate = (seed[0], seed[1], item["s2"], item["s3"])
            words_c = [f"{word:08X}" for word in words_of(candidate, 4)]
            if words_c[:3] != words[:3]:
                found.append(f"target {number}: ({item['s2']}, {item['s3']}) matches no three words")
            if words_c[3] != item["fourth_word"] \
                    or (words_c[3] == words[3]) != item["fourth_word_matches"]:
                found.append(f"target {number}: ({item['s2']}, {item['s3']}): the fourth word differs")
            is_target = list(candidate) == list(seed)
            if is_target != item["is_target"]:
                found.append(f"target {number}: ({item['s2']}, {item['s3']}) is misnamed")
            hit = hit or is_target
        if hit != record["recovered"][number]:
            found.append(f"target {number}: `recovered` reads {record['recovered'][number]}")
    return found


def verify(reference: str) -> int:
    _, record = read_record(reference)
    found = disagreements(record)
    for line in found:
        print(line)
    print(f"{record['record_id']}: {len(found)} disagreements")
    return evidence.EXIT_VERDICT if found else evidence.EXIT_OK


def reproduce(args: argparse.Namespace, command: List[str]) -> int:
    guard_platform()
    guard_paths(args.binary)
    row = evidence.family_row("FUT-SEC-8 result review")
    if row is None or row.decision != "Approved":
        raise Refused("--reproduce runs only after the FUT-SEC-8 result review")
    path, original = read_record(args.reproduce)
    seeds = [tuple(seed) for seed in original["targets"]]

    def run(place: evidence.Place) -> Dict:
        started = time.monotonic()
        binary = place.binaries.get(BINARY, place.worktree / BINARY)
        fields = measure(binary, place.worktree, seeds, original["git_head"])
        status, classification, exit_status, assertions = verdict(fields)
        return dict(fields, kind="demonstration", model_id=MODEL_ID, variant_id=None,
                    inputs=original["inputs"], exit_status=exit_status, assertions=assertions,
                    status=status, classification=classification,
                    code_sha256=original["code_sha256"], outputs=[],
                    hours_used=(time.monotonic() - started) / 3600.0)

    def projection(worktree: Path) -> Tuple[float, Dict]:
        return project(worktree / BINARY, worktree, seeds[0])

    return evidence.reproduce(evidence.Reproduction(
        record_path=path, run=run, heavy=True, owner_request=args.owner_request,
        project=projection, code_files=CODE, argv=command))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--binary")
    parser.add_argument("--out-dir")
    parser.add_argument("--owner-request")
    repeat = parser.add_mutually_exclusive_group()
    repeat.add_argument("--repeat-after-defect")
    repeat.add_argument("--repeat-after-end")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify")
    mode.add_argument("--reproduce")
    args = parser.parse_args(argv)
    command = ["scripts/fut_sec8.py"] + list(argv if argv is not None else sys.argv[1:])

    def run() -> int:
        if args.verify:
            return verify(args.verify)
        if args.reproduce:
            if not args.binary:
                raise Refused("--reproduce needs --binary")
            return reproduce(args, command)
        if not args.binary or not args.out_dir:
            raise Refused("a demonstration needs --binary and --out-dir")
        return demonstrate(args, command)

    return evidence.main_guard(run)


if __name__ == "__main__":
    sys.exit(main())
