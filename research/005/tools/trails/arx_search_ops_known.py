"""Feature 005: the ARX search's companion on the ARX search's known results (research R7, R14; spec FR-019).

research/005/tools/trails/arx_search_ops.c is feature 004's search with one addition to what it prints: the state after every
step of every round of each trail it finds, and each addition's weight. This file runs its committed binary, in WSL, on each
known result of feature 004's ARX search, read from research/004/validation/ and never written. A known result is re-found
when the weights match, as feature 004's driver asks, and when every step printed is what the box's steps give: each linear
step recomputed, and each addition's weight recomputed from its printed inputs and output by the exact counts of
protocol/trailcheck.py, the weights summing to the trail's.

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

from protocol import trailcheck  # noqa: E402
from protocol.evidence import ToolFailure  # noqa: E402

BINARY = "research/005/tools/trails/build/arx_search_ops"
CODE = ["protocol/trailcheck.py", "protocol/oplist.py"]
INSTANCE_SECONDS = 8 * 3600
HEAVY = ("speck64-lin",)
SPECK64_ROUND = (("rot", 0, 24), ("add", 0, 1, 0), ("rot", 1, 3), ("xor", 1, 0, 0))
PROBE_ROUNDS = 4
# The ratio of walks that feature 004's first run of speck64-lin measured between 5 rounds and 4: the search here is that search.
WALKS_OF_THE_LAST_ROUND = 9_042_695_762 / 9_196_884
KIND = {"widths": [16, 32], "operations": "a box of two words of addition, subtraction, xor and rotations",
        "model": "Matsui's branch and bound on the exact models of addition of Lipmaa and Moriai and of Wallen, each trail printed "
                 "with the state after every step and each addition's weight",
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
        raise ToolFailure(f"arx_search_ops exited {done.returncode}: {done.stderr.strip()[-300:]}")
    return done.stdout


def search(kind: str, w: int, rounds: int, steps: Sequence) -> Dict[int, Dict]:
    """The optimal weight of each r from 1 to `rounds`, with the walks it took, a trail of that weight, the state after
    every step of every round of it and each addition's weight."""
    out: Dict[int, Dict] = {}
    for line in run([kind, str(w), str(rounds)] + [step_text(step) for step in steps]).split("\n"):
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "optimal":
            out[int(fields[1])] = {"weight": int(fields[2]), "walks": int(fields[3])}
        elif fields[0] == "trail":
            words = [int(value, 16) for value in fields[2:]]
            out[int(fields[1])]["trail"] = [[words[k], words[k + 1]] for k in range(0, len(words), 2)]
        elif fields[0] == "steps":
            words = [int(value, 16) for value in fields[2:]]
            pairs = [[words[k], words[k + 1]] for k in range(0, len(words), 2)]
            out[int(fields[1])]["steps"] = [pairs[k:k + len(steps)] for k in range(0, len(pairs), len(steps))]
        elif fields[0] == "weights":
            out[int(fields[1])]["weights"] = [int(value) for value in fields[2:]]
    if sorted(out) != list(range(1, rounds + 1)) or any("steps" not in row or "weights" not in row for row in out.values()):
        raise ToolFailure(f"the search reported rounds {sorted(out)}, not 1 to {rounds} with their steps")
    return out


def rotl(value: int, amount: int, w: int) -> int:
    amount %= w
    return ((value << amount) | (value >> (w - amount))) & ((1 << w) - 1)


def operations(kind: str, w: int, steps: Sequence, found: Dict) -> List[List[Dict]]:
    """Each addition of each round of a found trail, with its inputs, its output and its exact weight, recomputed here from
    the states the binary printed: a step that the box's steps do not give, or a weight that the exact count does not give,
    is a tool failure. For a difference the inputs are the written word's and the read word's, rotated; for a mask, the
    mask on the written word and the mask on the read word, rotated, the output the mask on the sum."""
    out = []
    listed = iter(found["weights"])
    differences = kind == "differential"
    for number, after in enumerate(found["steps"]):
        state = list(found["trail"][number])
        row = []
        for index, step in enumerate(steps):
            name, i = step[0], step[1]
            now = after[index]
            if name == "rot":
                wanted = list(state)
                wanted[i] = rotl(state[i], step[2], w)
            elif name == "xor":
                j, r = step[2], step[3]
                wanted = list(state)
                if differences:
                    wanted[i] = state[i] ^ rotl(state[j], r, w)
                else:
                    wanted[j] = state[j] ^ rotl(state[i], w - r, w)
            else:
                j, r = step[2], step[3]
                sub = name == "sub"
                stated = next(listed)
                if differences:
                    if now[j] != state[j]:
                        raise ToolFailure(f"round {number + 1}, step {index}: an addition changed the word it reads")
                    inputs, output = [state[i], rotl(state[j], r, w)], now[i]
                    held = trailcheck.add_count(w, inputs[0], inputs[1], output, sub) << stated == 1 << (2 * w)
                else:
                    inputs, output = [state[i], rotl(state[j] ^ now[j], r, w)], now[i]
                    total = trailcheck.add_sum(w, inputs[0], inputs[1], output, sub)
                    held = abs(total) << stated == 1 << (2 * w)
                if not held:
                    raise ToolFailure(f"round {number + 1}, step {index}: the printed weight {stated} is not the addition's")
                row.append({"step": index, "inputs": inputs, "output": output, "weight": stated})
                wanted = now
            if list(now) != list(wanted):
                raise ToolFailure(f"round {number + 1}, step {index}: the printed state is not the step's")
            state = list(now)
        if state != list(found["trail"][number + 1]):
            raise ToolFailure(f"round {number + 1} does not end in the trail's state")
        out.append(row)
    if sum(item["weight"] for row in out for item in row) != found["weight"]:
        raise ToolFailure("the additions' weights do not sum to the trail's")
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
    additions = {str(r): len([item for row in operations(known.KIND, known.W, known.ROUND, found[r]) for item in row])
                 for r in found}
    rows = {str(r): {key: row[key] for key in ("weight", "walks", "trail", "weights")} for r, row in found.items()}
    return {"found": {"rounds": rows, "additions_recomputed": additions}, "re_found": held, "validated_kind": KIND}


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
    """The search of `speck64-lin` up to 4 rounds, timed, and the fifth by the ratio of walks feature 004 measured."""
    if known_id not in HEAVY:
        raise ToolFailure(f"{known_id} is no heavy run")
    started = time.monotonic()
    search("linear", 32, PROBE_ROUNDS, SPECK64_ROUND)
    seconds = time.monotonic() - started
    return seconds * WALKS_OF_THE_LAST_ROUND / 3600.0, {"seconds_of_4_rounds": seconds, "walks_ratio": WALKS_OF_THE_LAST_ROUND}
