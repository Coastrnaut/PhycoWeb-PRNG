"""Feature 005: the projection table (spec FR-005, FR-009; research R5; data-model section 4).

    projection_table.py            writes $REP/projection-table.json
    projection_table.py --check    recomputes it and exits 1 on a difference

After the probes and before the candidate log's first `proposed` entry. The table holds the values of
the option that research/005/plan-projections.json names as `approved_option`, each lowered where a
probe shows less and never raised: per family, size and kind each listed search with its need and its
source (a feature-004 run or a probe by record ID, path and SHA-256 over the committed bytes, the
plan's own projection, or the cap); the structural and bias needs, the smaller of the provisional
need and the sum over the sizes of each finished probe's hours and each other size's equal share;
per candidate row the value the plan fixed and the value that holds; the caps; and the sum against
the ceiling. A probe that shows a need above its row is printed and recorded here.

It exits 2 once any `proposed` entry exists, when plan-projections.json fails its --check, or when a
listed probe's record is missing or not committed. It holds numbers, record IDs and fixed field
names and no prose (spec FR-024). It runs under PHYCOWEB_FEATURE=005 and writes no other file. This
script makes no security claim.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from protocol import candidates, evidence  # noqa: E402
from protocol.evidence import NONE, Refused  # noqa: E402

SCRIPT = "scripts/projection_table.py"
PLAN_SCRIPT = "research/005/plan_projections.py"
PLAN_REL = evidence.PLAN_PROJECTIONS_REL
BASELINE = "99e6994"
REP_004 = evidence.FEATURES["004"]["rep"]
REFERENCE = {"cand-A1": "ARX", "cand-B1": "Boolean"}
SIZES = (16, 8, 4)
KINDS = ("linear", "differential")
PROBED_SIZES = (16, 8)
SHARE = {"structural": 4.0, "bias": 8.0}
FINISHED, LIMIT, REFUSED = "finished", "reached the probe limit", "refused"
SUB_ROWS = ("trails", "structural", "bias")


def guard_feature() -> None:
    if evidence.FEATURE != "005":
        raise Refused("projection_table.py runs under PHYCOWEB_FEATURE=005")


def plan() -> Tuple[Dict, Dict, str]:
    """plan-projections.json as committed, its approved option and its SHA-256 over those bytes."""
    blob = evidence.show(PLAN_REL)
    if blob is None:
        raise Refused(f"{PLAN_REL} is not committed")
    if evidence.REPO.path(PLAN_REL).read_bytes() != blob:
        raise Refused(f"{PLAN_REL} differs from its committed bytes")
    data = json.loads(blob.decode("utf-8"))
    return data, data["options"][data["approved_option"]], evidence.sha256(blob)


def guard_plan_check() -> None:
    done = subprocess.run([sys.executable, "-X", "utf8", str(evidence.REPO.path(PLAN_SCRIPT)), "--check"],
                          cwd=evidence.REPO.root, capture_output=True, text=True)
    if done.returncode != 0:
        raise Refused(f"{PLAN_REL} fails its --check: {done.stdout.strip() or done.stderr.strip()}")


def guard_no_candidate() -> None:
    if candidates.of_event(candidates.entries(), "proposed"):
        raise Refused("the candidate log holds a `proposed` entry: the table is written before the first")


def probe_key(probe: Dict) -> Tuple:
    return (probe.get("design"), probe.get("kind"), probe.get("size"), probe.get("bound_kind", NONE),
            probe.get("rounds", NONE) if probe.get("kind") == "bound" else NONE)


def probes() -> Dict[Tuple, Dict]:
    """The latest probe record of each listed run, each committed, with its path and SHA-256."""
    out: Dict[Tuple, Dict] = {}
    for path, record in evidence.iter_records("projection", "projections"):
        probe = record.get("table_probe")
        if not isinstance(probe, dict):
            continue
        rel = evidence.rel_to_repo(path)
        blob = evidence.show(rel)
        if blob is None or blob != path.read_bytes():
            raise Refused(f"the probe record {rel} is not committed as it stands")
        key = probe_key(probe)
        if key not in out or record["created_utc"] > out[key]["created_utc"]:
            out[key] = dict(record, _source={"record_id": record["record_id"], "path": rel,
                                             "sha256": evidence.sha256(blob), "sha256_kind": "raw"})
    return out


def source_004(candidate: str, record_id: str) -> Dict:
    rel = f"{REP_004}/candidates/{candidate}/{record_id}.json"
    blob = evidence.show(rel, BASELINE)
    if blob is None:
        raise Refused(f"{rel} is not committed at {BASELINE}")
    return {"record_id": record_id, "path": rel, "sha256": evidence.sha256(blob), "sha256_kind": "raw"}


def listed_searches(option: Dict) -> List[Tuple[str, int, str, int]]:
    """The searches research R5 probes: those of the approved option at 16×16 and 8×8 that feature
    004 neither made nor ran to its cap, each climb in its listed order."""
    out = []
    for design in REFERENCE:
        for size in PROBED_SIZES:
            for kind in KINDS:
                for search in option["climbs"][f"{design} {size}x{size} {kind}"]["searches"]:
                    if "source" not in search:
                        out.append((design, size, kind, search["r"]))
    return out


def climb(design: str, size: int, kind: str, option: Dict, held: Dict[Tuple, Dict]) -> Dict:
    """One listed climb: each search's need, the plan's or a finished probe's where that is less; a
    search probe that reached the limit reads as its search reaching its cap, where the climb ends."""
    planned = option["climbs"][f"{design} {size}x{size} {kind}"]
    cap = float(planned["cap_h"])
    runs, total = [], 0.0
    for search in planned["searches"]:
        need = float(search["need_h"])
        run: Dict[str, Any] = {"r": search["r"], "plan_need_h": need}
        probe = held.get((design, "bound", size, kind, search["r"]))
        if "source" in search:
            run["source"] = source_004(design, search["source"])
        elif probe is not None:
            run["source"] = probe["_source"]
            run["probe_result"] = probe["result"]
            if probe["result"] == FINISHED:
                need = min(need, float(probe["probe_hours"]))
            elif probe["result"] == LIMIT:
                need = cap
                run["reaches_cap"] = True
        else:
            run["source"] = "cap" if need >= cap else "plan"
        run["need_h"] = need
        runs.append(run)
        total += need
        if run.get("reaches_cap"):
            break
    plan_need = float(planned["need_h"])
    return {"cap_h": cap, "runs": runs, "plan_need_h": plan_need, "need_h": round(min(plan_need, total), 4)}


def kind_need(design: str, kind: str, provisional: float, held: Dict[Tuple, Dict]) -> Dict:
    """A structural or bias need: per size a finished probe's hours, or the size's equal share."""
    sizes: Dict[str, Dict] = {}
    total, least = 0.0, 0.0
    for size in sorted(SIZES):
        probe = held.get((design, kind, size, NONE, NONE))
        if probe is None:
            raise Refused(f"the probe of {kind} on {design} at {size}×{size} has no record")
        row: Dict[str, Any] = {"source": probe["_source"], "probe_result": probe["result"], "share_h": SHARE[kind]}
        if probe["result"] == FINISHED:
            row["hours"] = float(probe["probe_hours"])
            row["need_h"] = float(probe["probe_hours"])
            least += row["need_h"]
        else:
            row["need_h"] = SHARE[kind]
            least += float(probe.get("time_hours", 0.0)) if probe["result"] == LIMIT else 0.0
        total += row["need_h"]
        sizes[f"{size}x{size}"] = row
    return {"sizes": sizes, "plan_need_h": provisional, "need_h": round(min(provisional, total), 4),
            "shown_at_least_h": round(least, 4)}


def compute() -> Dict:
    guard_feature()
    data, option, digest = plan()
    held = probes()
    for design, size, kind, r in listed_searches(option):
        earlier = [held.get((design, "bound", size, kind, s)) for s in range(1, r)]
        ended = any(p is not None and p["result"] == LIMIT for p in earlier)
        if not ended and (design, "bound", size, kind, r) not in held:
            raise Refused(f"the probe of the {kind} search of {design} at {size}×{size}, r = {r}, has no record")
    margin = data["margin"]
    families: Dict[str, Dict] = {}
    rows: Dict[str, Dict] = {}
    above: List[Dict] = []
    for design, family in REFERENCE.items():
        climbs = {f"{size}x{size}": {kind: climb(design, size, kind, option, held) for kind in KINDS} for size in SIZES}
        trails = sum(c["need_h"] for per_size in climbs.values() for c in per_size.values())
        needs = {"trails": {"plan_need_h": float(option["rows"][family]["trails_need_h"]), "need_h": round(trails, 3)}}
        for kind in ("structural", "bias"):
            needs[kind] = kind_need(design, kind, float(option["provisional_needs_h"][kind]), held)
        families[family] = {"reference_design": design, "climbs": climbs,
                            "structural": needs["structural"], "bias": needs["bias"]}
        row: Dict[str, Dict] = {}
        for name in SUB_ROWS:
            planned = round(margin * needs[name]["plan_need_h"], 1)
            row[name] = {"plan_h": planned, "need_h": needs[name]["need_h"],
                         "holds_h": min(planned, round(margin * needs[name]["need_h"], 1))}
            shown = needs[name].get("shown_at_least_h", 0.0)
            if shown > row[name]["holds_h"]:
                above.append({"family": family, "row": name, "shown_at_least_h": shown, "holds_h": row[name]["holds_h"],
                              "probes": [s["source"]["record_id"] for s in needs[name]["sizes"].values()]})
        plan_row = float(option["rows"][family]["row_h"])
        row["row"] = {"plan_h": plan_row, "holds_h": min(plan_row, round(sum(row[name]["holds_h"] for name in SUB_ROWS), 1))}
        rows[family] = row
    per_family = option["candidates_per_family"]
    wide = float(option["feature_wide_row_h"])
    total = round(per_family * sum(row["row"]["holds_h"] for row in rows.values()) + wide, 1)
    used = round(sum(float(p.get("time_hours", 0.0)) for p in held.values()), 4)
    return {"kind": "projection-table", "feature": evidence.FEATURE, "config": {evidence.FEATURE_SETTING: evidence.FEATURE},
            "classification": NONE, "plan_projections_sha256": digest, "plan_projections_sha256_kind": "raw",
            "approved_option": data["approved_option"], "margin": margin,
            "caps_h": {name: {"plan_h": float(cap), "holds_h": float(cap)} for name, cap in option["caps_h"].items()},
            "candidates_per_family": per_family, "families": families, "rows": rows,
            "feature_wide_row": {"plan_h": wide, "holds_h": wide, "probes_share_h": float(option["feature_wide_needs_h"]["probes"]),
                                 "probes_used_h": used},
            "sum_of_rows_h": total, "plan_sum_of_rows_h": float(option["sum_of_rows_h"]),
            "ceiling_h": float(option["ceiling_h"]), "fits_ceiling": total <= float(option["ceiling_h"]),
            "above_row": above}


def table_path() -> Path:
    return evidence.REPO.rep / evidence.PROJECTION_TABLE


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    def body() -> int:
        guard_feature()
        path = table_path()
        if args.check:
            guard_plan_check()
            same = path.exists() and path.read_bytes() == evidence.pretty(compute())
            print(f"{evidence.rel_to_repo(path)} " + ("matches" if same else "differs"))
            return evidence.EXIT_OK if same else evidence.EXIT_VERDICT
        guard_no_candidate()
        guard_plan_check()
        evidence.guard_feature_path(evidence.rel_to_repo(path))
        table = compute()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(evidence.pretty(table))
        for item in table["above_row"]:
            print(f"above its row: {item['family']} {item['row']}: at least {item['shown_at_least_h']} h shown, "
                  f"{item['holds_h']} h held")
        print(f"{evidence.rel_to_repo(path)}: {table['sum_of_rows_h']} h of {table['ceiling_h']} h")
        return evidence.EXIT_OK

    return evidence.main_guard(body)


if __name__ == "__main__":
    sys.exit(main())
