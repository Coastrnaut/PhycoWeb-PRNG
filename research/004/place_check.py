"""The comparison of the lists "Rows that change the protocol" (spec FR-044; data-model §18).

Reads with `git show`, at the commit it compares up to, the lists of
specs/004-crypto-architecture-v3/checklist-choices.md, each naming its round's two commits by hash,
and the text of each place a list heading names at every commit from the plan-approval commit on.
It writes research/004/place-check.json: per round, its list's heading, its two commits and each
place whose text changed between them, with the rows of that round listed under its rule; per span
outside the pairs, each commit that changed a place, with the place; each place changed by an edit
that no row made, with its commit and the list it is recorded beside; and `compared_to`.

A place's text, as committed with CR LF read as LF (spec FR-044), runs for an FR item from its line
`- **FR-0xx**` to the next line that starts an FR item, a bold group name or a heading; for a
research section from its heading `## R<k>.` to the next heading of that level; for a paragraph of
the protocol from its bold name to the next bold name or to the section's end; and for the plan's
table from its heading to the next heading.

Standard library only. Exit 0 once the file is written; 2, writing nothing, when a list names no
pair of commits, a heading names no place, or a pair is out of order; 3 when git cannot be run or a
commit cannot be read.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FEATURE = "specs/004-crypto-architecture-v3/"
LISTS = FEATURE + "checklist-choices.md"
PLAN_APPROVAL = "65bcbf2"
OUT = ROOT / "research" / "004" / "place-check.json"

LISTS_START = "## Rows that change the protocol"
LISTS_END = "## After the answer"
PROTOCOL = "### Pre-registered Design Protocol"
PLAN_TABLE = "### Values this plan fixes"
LIST_HEAD = re.compile(r"^From the (?:.+?), \d+ of its \d+ rows:$", re.M)
PAIR = re.compile(r"two commits(?: \(PRO-061\))?(?: are|,) ([0-9a-f]{7,40}) and ([0-9a-f]{7,40})")
BULLET = re.compile(r"^- \*\*(.+?)\*\*([^:\n]*(?:\n  [^:\n]*)*):\s*(.+?)(?=\n- |\n\n|\Z)",
                    re.M | re.S)
ROW = re.compile(r"\b(?:SEC|RAT|ANA|PRO|HW|REP)-\d{3}\b")
BOLD = re.compile(r"^\*\*([^*]+?)\.?\*\*")


class Refused(Exception):
    """A guard refusal: exit 2, nothing written."""


def git(*args: str) -> str:
    done = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True,
                          encoding="utf-8")
    if done.returncode != 0:
        raise OSError(f"git {' '.join(args)}: {done.stderr.strip()}")
    return done.stdout


def full(commit: str) -> str:
    return git("rev-parse", "--verify", f"{commit}^{{commit}}").strip()


def show(commit: str, path: str) -> list[str]:
    """The file's lines at the commit, CR LF read as LF; no lines when the file does not exist."""
    names = git("ls-tree", "--name-only", commit, "--", path).split("\n")
    if path not in names:
        return []
    return git("show", f"{commit}:{path}").replace("\r\n", "\n").split("\n")


def until(lines: list[str], start: int, stop) -> int:
    j = start + 1
    while j < len(lines) and not stop(lines[j]):
        j += 1
    return j


def place_texts(commit: str, cache: dict[str, dict[str, str]]) -> dict[str, str]:
    """Every place's text at the commit, keyed as heading_places() names them."""
    if commit in cache:
        return cache[commit]
    out: dict[str, list[str]] = {}
    spec = show(commit, FEATURE + "spec.md")
    for i, line in enumerate(spec):
        m = re.match(r"^- \*\*(FR-\d{3})\*\*", line)
        if m:
            j = until(spec, i, lambda s: s.startswith(("- **FR-", "**", "#")))
            out.setdefault(m.group(1), []).append("\n".join(spec[i:j]))
    starts = [i for i, line in enumerate(spec) if line.startswith(PROTOCOL)]
    if starts:
        end = until(spec, starts[0], lambda s: s.startswith("#"))
        heads = [i for i in range(starts[0] + 1, end) if BOLD.match(spec[i])]
        for i, j in zip(heads, heads[1:] + [end]):
            name = BOLD.match(spec[i]).group(1)
            out.setdefault("protocol: " + name, []).append("\n".join(spec[i:j]))
    research = show(commit, FEATURE + "research.md")
    for i, line in enumerate(research):
        m = re.match(r"^## (R\d+)\.", line)
        if m:
            j = until(research, i, lambda s: s.startswith("## "))
            out.setdefault(m.group(1), []).append("\n".join(research[i:j]))
    plan = show(commit, FEATURE + "plan.md")
    for i, line in enumerate(plan):
        if line.startswith(PLAN_TABLE):
            j = until(plan, i, lambda s: s.startswith("#"))
            out.setdefault("plan: Values this plan fixes", []).append("\n".join(plan[i:j]))
    cache[commit] = {k: "\n".join(v) for k, v in out.items()}
    return cache[commit]


def heading_places(name: str, text: str, protocol: set[str]) -> list[str]:
    """The places a list heading names: its protocol paragraph, research sections, FR items and the
    plan's table."""
    places = ["protocol: " + name] if name in protocol else []
    places += [f"R{k}" for k in re.findall(r"\bR(\d+)\b", text)]
    numbers: list[int] = []
    for a, b in re.findall(r"FR-(\d{3}) to FR-(\d{3})", text):
        numbers += range(int(a), int(b) + 1)
    numbers += [int(k) for k in re.findall(r"FR-(\d{3})", text)]
    places += [f"FR-{k:03d}" for k in dict.fromkeys(numbers)]
    if "the plan's table" in text:
        places.append("plan: Values this plan fixes")
    return list(dict.fromkeys(places))


def read_lists(commit: str, protocol: set[str]):
    lines = show(commit, LISTS)
    text = "\n".join(lines)
    if LISTS_START not in text or LISTS_END not in text:
        raise Refused(f"{LISTS} at {commit[:7]} holds no lists")
    sec = text[text.index(LISTS_START):text.index(LISTS_END)]
    heads = list(LIST_HEAD.finditer(sec))
    rules: dict[str, list[str]] = {}
    rounds = []
    for k, h in enumerate(heads):
        block = sec[h.start():heads[k + 1].start() if k + 1 < len(heads) else len(sec)]
        pair = PAIR.search(" ".join(block.split()))
        if not pair:
            raise Refused(f"the list {h.group(0)!r} names no pair of commits")
        listed: dict[str, list[str]] = {}
        for b in BULLET.finditer(block):
            name, places_text, ids = b.group(1), " ".join(b.group(2).split()), b.group(3)
            places = heading_places(name, places_text, protocol)
            if not places:
                raise Refused(f"the heading {name!r} names no place")
            for p in places:
                if p not in rules.setdefault(name, []):
                    rules[name].append(p)
            for rid in ROW.findall(ids):
                if rid not in listed.setdefault(name, []):
                    listed[name].append(rid)
        rounds.append({"heading": h.group(0), "commits": [full(pair.group(1)), full(pair.group(2))],
                       "listed": listed})
    return rules, rounds


def changed(rules, a: dict[str, str], b: dict[str, str]) -> dict[str, list[str]]:
    out = {}
    for rule, places in rules.items():
        diff = [p for p in places if a.get(p) != b.get(p)]
        if diff:
            out[rule] = diff
    return out


def commits(c0: str, c1: str) -> list[str]:
    return git("rev-list", "--reverse", f"{c0}..{c1}").split()


def per_commit(rules, c0: str, c1: str, cache) -> list[dict]:
    out = []
    for c in commits(c0, c1):
        before, after = place_texts(full(c + "^"), cache), place_texts(c, cache)
        for rule, places in changed(rules, before, after).items():
            out.append({"commit": c, "rule": rule, "places": places})
    return out


def compare(to: str) -> dict:
    to = full(to)
    cache: dict[str, dict[str, str]] = {}
    protocol = {k[len("protocol: "):] for k in place_texts(to, cache) if k.startswith("protocol: ")}
    rules, rounds = read_lists(to, protocol)
    bounds = [full(PLAN_APPROVAL)]
    for r in rounds:
        bounds += r["commits"]
    bounds.append(to)
    for x, y in zip(bounds, bounds[1:]):
        if x != y and subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", x, y]
                                     ).returncode != 0:
            raise Refused(f"{x[:7]} is not an ancestor of {y[:7]}: the pairs are out of order")
    result_rounds, spans, unmade = [], [], []
    for k, r in enumerate(rounds):
        c0, c1 = r["commits"]
        ch = changed(rules, place_texts(c0, cache), place_texts(c1, cache))
        rows = []
        for rule, places in ch.items():
            listed = r["listed"].get(rule, [])
            rows.append({"rule": rule, "places": places, "rows": listed})
            if not listed:
                for e in per_commit({rule: rules[rule]}, c0, c1, cache):
                    unmade.append({**e, "in": [c0, c1], "beside": r["heading"]})
        result_rounds.append({"heading": r["heading"], "commits": [c0, c1], "changed": rows})
    edges = [(bounds[0], rounds[0]["commits"][0] if rounds else to, None)]
    for k, r in enumerate(rounds):
        nxt = rounds[k + 1]["commits"][0] if k + 1 < len(rounds) else to
        edges.append((r["commits"][1], nxt, r["heading"]))
    for c0, c1, before in edges:
        found = per_commit(rules, c0, c1, cache)
        spans.append({"from": c0, "to": c1, "after": before, "changes": found})
        unmade += [{**e, "in": [c0, c1], "beside": before} for e in found]
    return {"lists": LISTS, "plan_approval": bounds[0], "compared_to": to, "rules": rules,
            "rounds": result_rounds, "spans": spans, "unmade": unmade}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--to", default="HEAD", help="the commit compared up to (default HEAD)")
    ap.add_argument("--out", default=str(OUT), help="the file written (default %(default)s)")
    args = ap.parse_args(argv)
    try:
        result = compare(args.to)
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3
    data = json.dumps(result, indent=1, ensure_ascii=False) + "\n"
    Path(args.out).write_bytes(data.encode("utf-8"))
    print(f"{args.out}: {len(result['rounds'])} rounds, {len(result['spans'])} spans, places "
          f"changed by an edit no row made: {len(result['unmade'])}; "
          f"compared to {result['compared_to'][:7]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
