"""Run one battery on one generator stream (feature 003; contracts/cli.md; research R5).

  battery_run.py --role positive|negative|candidate --battery practrand|smallcrush|crush|bigcrush
                 --orientation fwd|rev (--seed S0 S1 S2 S3 | --os) --out DIR (--set dev | --attempt N)
                 [--stop-on-fail] [--practrand-tlmax LOG2]

The stream from fast/build/phyco_stream is relayed to the tool while every byte is hashed
(SHA-256), so the input is identified even though it is not stored. Writes DIR/log.txt (tool
stdout), DIR/stderr.txt, DIR/pvalues.jsonl (TestU01), DIR/run.json. With --set dev only the
feature-002 dev seeds and feature-001 seeds are accepted; with --attempt N the freeze must be
approved and valid and the seed must belong to that attempt's set. Run in WSL.
Exit 0 when the tool completed, 2 if refused, 3 on a tool or I/O error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from protocol import battery_freeze, battery_seedsets, batteries, seedsets  # noqa: E402
from protocol.disclaimer import DISCLAIMER  # noqa: E402

STREAM = ROOT / "fast" / "build" / "phyco_stream"
DRIVER = ROOT / "fast" / "build" / "testu01_driver"
RNG_TEST = Path("~/practrand/RNG_test").expanduser()
CHUNK = 1 << 20


class Refused(Exception):
    pass


def check_seed(args) -> None:
    """Guards: generator/seed match the role, and the seed is allowed for this mode."""
    if args.role == "positive":
        if not args.os or args.seed:
            raise Refused("the positive control uses --os and no seed")
    elif args.os or not args.seed:
        raise Refused(f"role {args.role} needs --seed")
    if args.stop_on_fail and args.role != "negative":
        raise Refused("--stop-on-fail is allowed only for the negative control (spec Edge Cases)")
    if args.orientation not in batteries.ORIENTATIONS[args.battery]:
        raise Refused(f"{args.battery} has no orientation {args.orientation}")
    seed = tuple(args.seed) if args.seed else None
    if args.seed_set == "dev":
        allowed = set(seedsets.load("dev", allow={"dev"})) | set(seedsets.FEATURE001_SEEDS)
        if seed is not None and seed not in allowed:
            raise Refused(f"seed {seed} is not a development seed (FR-010)")
        return
    if args.practrand_tlmax is not None:
        raise Refused("--practrand-tlmax is allowed only with --set dev")
    try:
        record = battery_freeze.load(args.attempt)
        problems = battery_freeze.validate(record, args.attempt)
    except battery_freeze.FreezeError as exc:
        raise Refused(str(exc))
    if problems:
        raise Refused("freeze not usable: " + "; ".join(problems))
    if seed is not None and seed not in battery_seedsets.load(record["seed_set"],
                                                              allow={record["seed_set"]}):
        raise Refused(f"seed {seed} is not in {record['seed_set']}")


def build_commands(args, out: Path):
    gen = batteries.GENERATOR[args.role]
    stream = [str(STREAM), gen, *map(str, args.seed or [])]
    if args.orientation == "rev":
        stream.append("--reverse")
    if args.battery == "practrand":
        tlmax = args.practrand_tlmax or batteries.PRACTRAND_TLMAX_LOG2
        consumer = [str(RNG_TEST), *batteries.practrand_args(args.stop_on_fail, tlmax)]
        return stream, consumer, tlmax
    consumer = [str(DRIVER), args.battery, "--name", out.name, "--pvalues",
                str(out / "pvalues.jsonl")]
    return stream, consumer, None


def relay(stream_cmd, consumer_cmd, out: Path):
    """stream | hash | consumer. Returns (consumer exit, stream exit, bytes, sha256)."""
    digest, n = hashlib.sha256(), 0
    with open(out / "log.txt", "wb") as log, open(out / "stderr.txt", "wb") as err:
        consumer = subprocess.Popen(consumer_cmd, stdin=subprocess.PIPE, stdout=log, stderr=err)
        stream = subprocess.Popen(stream_cmd, stdout=subprocess.PIPE, stderr=err)
        try:
            while True:
                chunk = stream.stdout.read(CHUNK)
                if not chunk:
                    break
                try:
                    consumer.stdin.write(chunk)
                except BrokenPipeError:
                    break
                digest.update(chunk)
                n += len(chunk)
        finally:
            stream.stdout.close()
            try:
                consumer.stdin.close()
            except BrokenPipeError:
                pass
            stream_status = stream.wait()
            consumer_status = consumer.wait()
    return consumer_status, stream_status, n, digest.hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=batteries.ROLES)
    parser.add_argument("--battery", required=True, choices=batteries.BATTERIES)
    parser.add_argument("--orientation", required=True, choices=("fwd", "rev"))
    parser.add_argument("--seed", type=int, nargs=4)
    parser.add_argument("--os", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--set", dest="seed_set", choices=("dev",))
    mode.add_argument("--attempt", type=int)
    parser.add_argument("--stop-on-fail", action="store_true")
    parser.add_argument("--practrand-tlmax", type=int)
    args = parser.parse_args(argv)
    try:
        check_seed(args)
        if args.out.exists() and any(args.out.iterdir()):
            raise Refused(f"{args.out} already has results; runs are never repeated")
    except Refused as exc:
        print(exc, file=sys.stderr)
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    stream_cmd, consumer_cmd, tlmax = build_commands(args, args.out)
    started = time.time()
    consumer_status, stream_status, n_bytes, sha = relay(stream_cmd, consumer_cmd, args.out)
    meta = {
        "role": args.role, "generator": batteries.GENERATOR[args.role],
        "seed": list(args.seed) if args.seed else None, "battery": args.battery,
        "orientation": args.orientation, "mode": "dev" if args.seed_set else f"attempt-{args.attempt}",
        "stop_on_fail": args.stop_on_fail, "length_target_log2": tlmax,
        "stream_command": stream_cmd, "consumer_command": consumer_cmd,
        "stream_bytes": n_bytes, "stream_sha256": sha, "exit_status": consumer_status,
        "stream_exit_status": stream_status,
        "started": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(started)),
        "elapsed_s": round(time.time() - started, 1),
        "host": platform.platform(), "python": platform.python_version(),
        "disclaimer": DISCLAIMER,
    }
    (args.out / "run.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    (args.out / "stream.sha256").write_text(f"{sha}  {n_bytes} bytes\n", encoding="ascii")
    parsed = batteries.load_run(args.out)
    summary = {k: parsed[k] for k in ("n_pvalues", "complete", "stopped_early")}
    summary.update(rule2=len(parsed["rule2"]), rule3=len(parsed["rule3"]),
                   min_q=min((r["q"] for r in parsed["results"] if r["q"] is not None), default=None))
    print(json.dumps(summary))
    return 0 if consumer_status == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
