"""Feature 004: fut_sec8.py's tools on their known result `fut-sec-8` (FR-003, FR-039; data-model section 7).

Nothing is run again. What must match is read from the reviewed demonstration record, the latest one,
which the row "FUT-SEC-8 result review" names by path and SHA-256 and which must read Approved at HEAD:
its three seeds, the first three of feature 002's `dev` set, each recovered, and its vector check, every
file compared with no mismatch. The record must also have been made by the tool now under validation,
its source's and its binary's hashes being the committed files'. fut_sec8.py and its search tool were
written before their validation, so that this known result has no second: its record says `none`, and a
failed validation leaves them unvalidated (data-model section 7). This tool makes no security claim.
"""
import sys
from pathlib import Path
from typing import Callable, Dict, Optional

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from protocol import evidence, seedsets  # noqa: E402

MODEL_ID = "phyco-v2"
SOURCE = "fast/seed_search.c"
BINARY = "fast/build/seed_search"
CODE = ("scripts/fut_sec8.py", "protocol/seedsets.py", "phycoweb/model_v2.py", "phycoweb/lut.py",
        "fast/lut_table.h")
SEEDS = 3
KIND = {"widths": [32], "operations": "phyco-v2's seed search over its two unrevealed seed words",
        "model": "an exhaustive sweep with a match on three output words",
        "uses": [{"use": "the FUT-SEC-8 demonstration", "covered_by": ["fut-sec-8"]}]}


def validation(known_id: str, known, keep: Optional[Callable[[str, bytes], None]]) -> Dict:
    evidence.guard_order_of_us1()
    path, record = evidence.latest_demonstration()
    seeds = [list(seed) for seed in seedsets.load("dev", allow=("dev",))[:SEEDS]]
    tool = record["tool"]
    source = evidence.sha256(evidence.REPO.path(SOURCE).read_bytes())
    binary = evidence.sha256(evidence.REPO.path(BINARY).read_bytes())
    checked = record["vector_check"]
    found = {"record_id": record["record_id"], "sha256": evidence.sha256(path.read_bytes()),
             "targets": record["targets"], "recovered": record["recovered"],
             "vector_check": checked, "source_sha256": tool["source_sha256"],
             "binary_sha256": tool["binary_sha256"]}
    held = record["targets"] == seeds and len(record["recovered"]) == SEEDS \
        and all(record["recovered"]) and bool(checked) \
        and all(item["mismatches"] == 0 and item["words"] > 0 for item in checked) \
        and tool["source_sha256"] == source and tool["binary_sha256"] == binary
    return {"found": found, "re_found": held, "validated_kind": KIND}


def inputs(known_id: str) -> Dict:
    return {"namespace": "feature-002/dev", "kind": "seed", "index_range": [0, SEEDS - 1],
            "fingerprint": seedsets.FINGERPRINTS["dev"]}
