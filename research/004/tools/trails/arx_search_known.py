"""Feature 004: the ARX search on its known results (research R12; FR-039; data-model section 7).

research/004/tools/trails/arx_search.c holds the search, and this file runs its committed binary, in WSL (research R1, R16), on each known result.
A file whose KIND and ROUND state a search gives the weights that must match; a file with a TRAIL gives a published trail, whose weight the
binary works out round by round. Every weight is a whole number from the exact models of addition, with no solver and no tolerance.

Analysis code: the model never imports it. This tool makes no security claim.
"""
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from protocol.evidence import ToolFailure  # noqa: E402

BINARY = "research/004/tools/trails/build/arx_search"
INSTANCE_SECONDS = 8 * 3600
HEAVY = ("speck64-lin",)
SPECK64_ROUND = (("rot", 0, 24), ("add", 0, 1, 0), ("rot", 1, 3), ("xor", 1, 0, 0))
PROBE_ROUNDS = 4
WALKS_OF_THE_LAST_ROUND = 9_042_695_762 / 9_196_884
KIND = {"widths": [16, 32], "operations": "a box of two words of addition, subtraction, xor and rotations",
        "model": "Matsui's branch and bound on the exact models of addition of Lipmaa and Moriai and of Wallen",
        "uses": [{"use": "a box's differential trails at w = 16", "covered_by": ["speck32-diff"]},
                 {"use": "a box's linear trails at w = 16", "covered_by": ["speck32-lin"]},
                 {"use": "a box's differential trails at w = 32", "covered_by": ["speck64-diff"]},
                 {"use": "a box's linear trails at w = 32", "covered_by": ["speck64-lin"]}]}


def program() -> str:
    path = Path(BINARY)
    return str(path if path.is_absolute() else ROOT / path)


def step_text(step: Sequence) -> str:
    return ":".join(str(item) for item in step)


def run(arguments: List[str]) -> str:
    try:
        done = subprocess.run([program()] + arguments, capture_output=True, text=True, timeout=INSTANCE_SECONDS)
    except subprocess.TimeoutExpired as exc:
        raise ToolFailure(f"the search stopped at its 8 h cap: no bound ({arguments[:3]})") from exc
    if done.returncode != 0:
        raise ToolFailure(f"arx_search exited {done.returncode}: {done.stderr.strip()[-300:]}")
    return done.stdout


def search(kind: str, w: int, rounds: int, steps: Sequence) -> Dict[int, Dict]:
    """The optimal weight of each r from 1 to `rounds`, with the walks it took and a trail of that weight."""
    out: Dict[int, Dict] = {}
    for line in run([kind, str(w), str(rounds)] + [step_text(step) for step in steps]).split("\n"):
        fields = line.split()
        if fields and fields[0] == "optimal":
            out[int(fields[1])] = {"weight": int(fields[2]), "walks": int(fields[3])}
        elif fields and fields[0] == "trail":
            words = [int(value, 16) for value in fields[2:]]
            out[int(fields[1])]["trail"] = [[words[k], words[k + 1]] for k in range(0, len(words), 2)]
    if sorted(out) != list(range(1, rounds + 1)):
        raise ToolFailure(f"the search reported rounds {sorted(out)}, not 1 to {rounds}")
    return out


def stated(kind: str, w: int, steps: Sequence, trail: Sequence[Tuple[int, int]]) -> Tuple[int, ...]:
    """The weight of each round of a stated trail, -1 where it cannot be."""
    words = [format(value, "x") for pair in trail for value in pair]
    lines = run([f"check-{kind}", str(w)] + [step_text(step) for step in steps] + ["--"] + words).strip().split("\n")
    return tuple(int(line.split()[2]) for line in lines)


def weights_of(known) -> Dict[int, int]:
    return known.WEIGHTS if known.KIND == "differential" else known.EXPONENTS


def re_find_search(known, keep) -> Dict:
    found = search(known.KIND, known.W, known.ROUNDS, known.ROUND)
    table = weights_of(known)
    held = all(found[r]["weight"] == table[r] for r in range(1, known.ROUNDS + 1))
    return {"found": {"rounds": {str(r): row for r, row in found.items()}}, "re_found": held, "validated_kind": KIND}


def re_find_trail(known, keep) -> Dict:
    weights = stated(known.KIND, known.W, known.ROUND, known.TRAIL)
    wanted = tuple(known.WEIGHTS if known.KIND == "differential" else known.EXPONENTS)
    held = weights == wanted and (not hasattr(known, "TOTAL") or sum(weights) == known.TOTAL)
    return {"found": {"weights": list(weights), "total": sum(weights)}, "re_found": held, "validated_kind": KIND}


RUNS: Dict[str, Callable] = {"speck32-diff": re_find_search, "speck32-lin": re_find_search, "speck64-diff": re_find_search,
                             "speck64-lin": re_find_search, "speck32-diff-second": re_find_trail, "speck32-lin-second": re_find_trail,
                             "speck64-diff-second": re_find_trail, "speck64-lin-second": re_find_trail}


def validation(known_id: str, known, keep: Optional[Callable[[str, bytes], None]]) -> Dict:
    return RUNS[known_id](known, keep)


def projection(known_id: str) -> Tuple[float, Dict]:
    """The search of `speck64-lin` up to 4 rounds, timed, and the fifth by the ratio of walks a first run measured: 9,042,695,762 at 5 rounds
    against 9,196,884 at 4, the walks of a round being what its time goes on."""
    if known_id not in HEAVY:
        raise ToolFailure(f"{known_id} is no heavy run")
    started = time.monotonic()
    search("linear", 32, PROBE_ROUNDS, SPECK64_ROUND)
    seconds = time.monotonic() - started
    return seconds * WALKS_OF_THE_LAST_ROUND / 3600.0, {"seconds_of_4_rounds": seconds, "walks_ratio": WALKS_OF_THE_LAST_ROUND}
