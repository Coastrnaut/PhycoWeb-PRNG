"""Feature 005: the plan's calibration (FR-004) and provisional projection table (FR-005, FR-006, FR-008), computed from feature
004's committed records alone, which it reads and never writes (FR-003). Run from the repository root:

    python -X utf8 research/005/plan_projections.py [--check]

It writes research/005/plan-projections.json, or with --check compares a fresh computation with the committed file and exits 1 on a
difference. The rules are research R1 to R3 of specs/005-crypto-architecture-v4/research.md:

- Calibration (R1): every feature-004 projection paired with the run it projected, the ratio of measured to projected hours per
  tool or kind and size, and the factor F = max(1, the largest ratio over pairs projected at 0.001 h or more and below the cap).
  A pair whose run ended at its cap gives its ratio as a lower bound, used as it is. A tool with no such pair at a size takes the
  largest factor of any tool at that size, and failing that its own largest factor at any size.
- Projected need of a bound search (R2): a search feature 004 made has its measured hours, or reaches this plan's cap where it ended
  at its cap; a search feature 004 projected but did not make has its projection times F, or reaches the cap where feature 004's
  projection was its 8 h cap (no estimate) or the product is not below the cap; a search feature 004 neither made nor projected
  reaches the cap.
- The listed climb (R2): per reference design, size and kind, r = 1, 2, ... in order, ending after the first search projected to
  reach the cap (FR-015), at the first r whose bound, searched or summed (FR-016), has weight above 128 (FR-017), or at R_max.
- Rows (R3): each row at least the margin times the sum of the projected needs it holds (FR-005), with the caps and the candidate
  limit of the option given, checked against the option's ceiling (FR-008): 2,200 h for option E, the ceiling the owner raised at
  the plan approval of 2026-11-09, which `approved_option` names, and D7's 720 h for the others.
- Each calibration pair cites its projection and its run by record ID, path and SHA-256 over the committed bytes (kind raw).

This script makes no security claim.
"""
import argparse
import fnmatch
import hashlib
import json
import statistics
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REP4 = "reports/004-crypto-architecture-v3"
# Feature 004's records are read as committed at this commit, never from the working tree, so that a later record
# never changes the calibration (spec FR-004).
BASELINE = "99e6994"
OUT = ROOT / "research/005/plan-projections.json"
CAP_004 = 8.0
R_MAX = 64
MARGIN = 2
CEILING = 720.0
SIZES = (16, 8, 4)
KINDS = ("linear", "differential")
REFERENCE = {"cand-A1": "ARX", "cand-B1": "Boolean"}
OPTIONS = {
    # the owner's choice at the plan approval of 2026-11-09: "extend run limits even more to ensure we find a good candidate also"
    "E (the owner's extension)": {"caps": {16: 48.0, 8: 24.0, 4: 8.0}, "per_family": 3,
                                  "provisional": {"structural": 12.0, "bias": 24.0},
                                  "feature_wide": {"probes": 40.0, "two whole-suite runs per platform": 2.0,
                                                   "reproductions and re-checks": 9.0},
                                  "ceiling": 2200.0},
    "A (recommended)": {"caps": {16: 12.0, 8: 4.0, 4: 4.0}, "per_family": 3},
    "B": {"caps": {16: 20.0, 8: 20.0, 4: 8.0}, "per_family": 2},
    "C": {"caps": {16: 24.0, 8: 4.0, 4: 4.0}, "per_family": 3},
    "feature 004's caps": {"caps": {16: 8.0, 8: 8.0, 4: 8.0}, "per_family": 3},
}
# Kinds whose runs feature 004 never made at w = 32: provisional needs per candidate, twice feature 004's rows, until the probes of
# FR-005 replace them before any candidate is proposed (R3).
PROVISIONAL = {"structural": 6.0, "bias": 12.0}
FEATURE_WIDE_NEED = {"probes": 30.0, "two whole-suite runs per platform": 2.0, "reproductions and re-checks": 9.0}
# The option the plan approval of 2026-11-09 fixed (spec, Review & Approval, "Plan approval").
APPROVED = "E (the owner's extension)"


_BLOBS = {}


def committed():
    """Every JSON file of feature 004's reports at the baseline commit, by its path, read once with git."""
    if not _BLOBS:
        names = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", BASELINE, "--", REP4],
                               capture_output=True, check=True).stdout.decode("utf-8").split("\n")
        names = sorted(name for name in names if name.endswith(".json"))
        batch = subprocess.run(["git", "-C", str(ROOT), "cat-file", "--batch"], capture_output=True, check=True,
                               input="".join(f"{BASELINE}:{name}\n" for name in names).encode("utf-8")).stdout
        at = 0
        for name in names:
            end = batch.index(b"\n", at)
            size = int(batch[at:end].split()[2])
            _BLOBS[name] = batch[end + 1:end + 1 + size]
            at = end + 1 + size + 1
    return _BLOBS


def load(pattern):
    out = []
    for path, blob in committed().items():
        if not fnmatch.fnmatchcase(path, REP4 + "/" + pattern) or path.count("/") != (REP4 + "/" + pattern).count("/"):
            continue
        record = json.loads(blob.decode("utf-8"))
        record["_path"] = path
        out.append(record)
    return out


def sha256_of(rel):
    """SHA-256 over a committed file's bytes at the baseline commit, kind raw."""
    return hashlib.sha256(committed()[rel]).hexdigest()


def candidate_of(record):
    return record["_path"].split("/")[-2]


def weight(bound):
    """A bound's weight, read exactly: feature 004's counted bounds hold it as a whole number (the count times the box's or the
    S-box's weight), and its box searches as a rational, such as 393216/65536 for a weight of 6."""
    if isinstance(bound, int) or (isinstance(bound, str) and bound not in ("", "none")):
        return Fraction(bound)
    raise ValueError(f"no weight in the bound {bound!r}")


def calibration(projections, bounds):
    index = {}
    for b in bounds:
        if "size" in b:
            index.setdefault((candidate_of(b), b["size"], b["width"], b["bound_kind"], b.get("rounds"), b["method"]), []).append(b)
    pairs = []
    for p in projections:
        probe = p.get("probe") or {}
        if probe.get("kind") != "bound":
            continue
        cand = p["run"].split(" of ")[1].split(" at ")[0]
        key = (cand, probe.get("size"), probe.get("width"), probe.get("bound_kind"), p.get("rounds"), probe.get("method"))
        hits = index.get(key)
        if not hits:
            continue
        run = hits[-1]
        pairs.append({"tool": probe.get("method"), "size": probe.get("size"), "width": probe.get("width"), "candidate": cand,
                      "kind": probe.get("bound_kind"), "rounds": p.get("rounds"), "projected_h": p["projected_hours"],
                      "measured_h": run["budget"]["hours_used"], "capped": run["status"] != "pass",
                      "projection": p["record_id"], "run": run["record_id"],
                      "projection_path": p["_path"], "projection_sha256": sha256_of(p["_path"]),
                      "run_path": run["_path"], "run_sha256": sha256_of(run["_path"]), "sha256_kind": "raw"})
    usable = [q for q in pairs if 0.001 <= q["projected_h"] < CAP_004]
    factors = {}
    for q in usable:
        key = f'{q["tool"]}@{q["size"]}'
        factors[key] = max(factors.get(key, 1.0), q["measured_h"] / q["projected_h"])
    ratios = [q["measured_h"] / q["projected_h"] for q in pairs if q["projected_h"] > 0]
    summary = {"pairs": len(pairs), "pairs_used_for_factors": len(usable),
               "ratio_min": min(ratios), "ratio_median": statistics.median(ratios), "ratio_max": max(ratios),
               "projected_at_the_cap": sum(1 for q in pairs if q["projected_h"] == CAP_004),
               "projected_below_0.001_h": sum(1 for q in pairs if q["projected_h"] < 0.001)}
    return pairs, factors, summary


def kind_calibration():
    """Every other kind of evidence: the feature-004 records that hold their own projected and used hours (R1)."""
    out = {}
    for path, blob in committed().items():
        try:
            record = json.loads(blob.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue
        hours = record.get("hours") if isinstance(record, dict) else None
        if record.get("kind") in (None, "bound") or not isinstance(hours, dict) or "projected" not in hours or "used" not in hours:
            continue
        entry = out.setdefault(record["kind"], {"pairs": 0, "ratios": [], "factor": 1.0})
        entry["pairs"] += 1
        if hours["projected"] >= 0.001:
            ratio = hours["used"] / hours["projected"]
            entry["ratios"].append(round(ratio, 4))
            entry["factor"] = max(entry["factor"], ratio)
    return out


def factor(factors, tool, size):
    if f"{tool}@{size}" in factors:
        return factors[f"{tool}@{size}"]
    at_size = [v for k, v in factors.items() if k.endswith(f"@{size}")]
    if at_size:
        return max(at_size)
    own = [v for k, v in factors.items() if k.startswith(f"{tool}@")]
    return max(own) if own else 1.0


def climbs(projections, bounds, factors, caps):
    made = {}
    for b in bounds:
        if "size" in b and b["width"] == 32:
            made[(candidate_of(b), b["size"], b["bound_kind"], b.get("rounds"))] = b
    projected = {}
    for p in projections:
        probe = p.get("probe") or {}
        if probe.get("kind") == "bound" and probe.get("width") == 32 and p.get("rounds") is not None:
            cand = p["run"].split(" of ")[1].split(" at ")[0]
            projected[(cand, probe["size"], probe["bound_kind"], p["rounds"])] = (p["projected_hours"], probe["method"])
    tools = {"cand-A1": "active-box count", "cand-B1": "active-S-box count"}
    table = {}
    for cand in REFERENCE:
        for size in SIZES:
            cap = caps[size]
            for kind in KINDS:
                listed, established, total = [], {}, 0.0
                for r in range(1, R_MAX + 1):
                    row = {"r": r}
                    rec = made.get((cand, size, kind, r))
                    if cand == "cand-A1" and r == 1:
                        box = made.get((cand, 4, kind, 1))
                        row.update(need_h=box["budget"]["hours_used"] if size == 4 else 0.0, source=box["record_id"],
                                   note="the box's own bound over one call, searched once at 4×4 and read at every size")
                        established[1] = weight(box["bound"])
                    elif rec is not None and rec["status"] == "pass":
                        row.update(need_h=rec["budget"]["hours_used"], source=rec["record_id"])
                        established[r] = weight(rec["bound"])
                    elif rec is not None:
                        row.update(need_h=cap, source=rec["record_id"], note="ended at feature 004's cap: reaches this cap")
                    elif (cand, size, kind, r) in projected:
                        hours, tool = projected[(cand, size, kind, r)]
                        f = factor(factors, tool, size)
                        if hours >= CAP_004 or hours * f >= cap:
                            row.update(need_h=cap, note=f"feature 004 projected {hours:.3f} h, factor {f:.3g}: reaches this cap")
                        else:
                            row.update(need_h=hours * f, note=f"feature 004 projected {hours:.3f} h, factor {f:.3g}")
                    else:
                        row.update(need_h=cap, note="neither made nor projected in feature 004: reaches this cap")
                    total += row["need_h"]
                    listed.append(row)
                    if row["need_h"] >= cap and "note" in row and "reaches" in row["note"]:
                        break
                    sums = [established[s] + established[r - s] for s in range(1, r) if s in established and r - s in established]
                    best = max([established.get(r, Fraction(0))] + sums)
                    established[r] = best
                    if best > 128:
                        row["weight_above_128"] = str(best)
                        break
                # after the searches end, the climb goes on by sums alone (FR-016, FR-017): R_bound as the sums give it
                r_bound = next((r for r in sorted(established) if established[r] > 128), None)
                r = max(established) if established else 0
                while r_bound is None and established and r < R_MAX:
                    r += 1
                    sums = [established[s] + established[r - s] for s in range(1, r) if s in established and r - s in established]
                    established[r] = max(sums) if sums else Fraction(0)
                    if established[r] > 128:
                        r_bound = r
                table[f"{cand} {size}x{size} {kind}"] = {"searches": listed, "need_h": round(total, 4), "cap_h": cap,
                                                         "r_bound_by_searches_and_sums": r_bound}
    return table


def rows_for(table, option):
    caps, per_family = option["caps"], option["per_family"]
    provisional = option.get("provisional", PROVISIONAL)
    feature_wide = option.get("feature_wide", FEATURE_WIDE_NEED)
    ceiling = option.get("ceiling", CEILING)
    out = {}
    for cand, family in REFERENCE.items():
        trails = sum(v["need_h"] for k, v in table.items() if k.startswith(cand + " "))
        need = trails + sum(provisional.values())
        out[family] = {"trails_need_h": round(trails, 3), "structural_need_h": provisional["structural"],
                       "bias_need_h": provisional["bias"], "row_h": round(MARGIN * need, 1)}
    wide = round(MARGIN * sum(feature_wide.values()), 1)
    total = round(per_family * sum(v["row_h"] for v in out.values()) + wide, 1)
    # FR-006: each cap at least the margin times the longest listed search projected to finish under it
    fr006 = {}
    for size in SIZES:
        for kind in KINDS:
            longest = max([s["need_h"] for k, v in table.items() if k.endswith(f" {size}x{size} {kind}")
                           for s in v["searches"] if "reaches" not in s.get("note", "")] or [0.0])
            fr006[f"{size}x{size} {kind}"] = {"longest_finishing_h": round(longest, 4), "floor_h": round(MARGIN * longest, 4),
                                              "cap_h": caps[size], "holds": caps[size] >= MARGIN * longest}
    return {"caps_h": {f"{n}x{n}": c for n, c in caps.items()}, "candidates_per_family": per_family, "rows": out,
            "ceiling_h": ceiling, "provisional_needs_h": provisional, "feature_wide_needs_h": feature_wide,
            "feature_wide_row_h": wide, "sum_of_rows_h": total, "fits_ceiling": total <= ceiling,
            "fr006": fr006, "fr006_holds": all(v["holds"] for v in fr006.values())}


def compute():
    projections, bounds = load("projections/*.json"), load("candidates/*/bound-*.json")
    pairs, factors, summary = calibration(projections, bounds)
    options = {}
    for name, option in OPTIONS.items():
        table = climbs(projections, bounds, factors, option["caps"])
        options[name] = {"climbs": table, **rows_for(table, option)}
    return {"note": "computed by research/005/plan_projections.py from feature 004's committed records; no security claim",
            "approved_option": APPROVED, "ceiling_h": OPTIONS[APPROVED]["ceiling"], "margin": MARGIN, "r_max": R_MAX,
            "calibration": {"summary": summary, "factors": factors, "pairs": pairs, "other_kinds": kind_calibration()},
            "options": options}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    text = json.dumps(compute(), ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if args.check:
        same = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("plan-projections.json matches" if same else "plan-projections.json differs")
        return 0 if same else 1
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
