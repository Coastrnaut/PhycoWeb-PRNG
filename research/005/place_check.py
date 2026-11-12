"""The comparison of feature 005's edits with the rows that made them (spec FR-031; tasks T001).

Feature 004's research/004/place_check.py (2392150), adapted to this feature's paths and to the
table form of its lists. It reads with `git show`, at the commit it compares up to,
specs/005-crypto-architecture-v4/checklist-choices.md: per round or batch, the rows of its choices
tables, each with the places its "Where" cell names, and its list "Rows that change the protocol",
each row with the places its Rule cell names and its direction, the list naming the round's two
commits by hash. It reads the text of every place at every commit from the plan-approval commit on,
and writes research/005/place-check.json: per round, its two commits and each place whose text
changed between them, with the rows of that round that name it; per span outside the pairs, each
commit that changed a place, with the places; each place changed by an edit that no row made, with
its commit and the list it is recorded beside; and `compared_to`.

A place's text, as committed with CR LF read as LF, runs for an FR or SC item from its line
`- **FR-0xx**` to the next line that starts an item, a bold group name or a heading; for a decision
from its row `| D<n> |`; for a bullet of the changed rules from its bold name to the next bullet;
for a research section from its heading `## R<k>.` to the next heading of that level; for a numbered
section of the data model from its heading to the next heading of the same or a higher level, with
the introduction before the first; for every other heading of the spec, the plan and the contract
from the heading to the next heading, a contract section keyed by its heading's code span, so that a
renamed heading reads as one place removed and one added; for the notes under the spec's Review &
Approval table from the line after the table to the next heading; and for quickstart.md,
research/005/plan-projections.json and research/005/plan_projections.py, the whole file. A line in
fenced code is never a heading. Two texts that differ only in white space are one text: a re-wrapped
paragraph is no edit. The Review & Approval table and the spec's lines above its first chapter, the
Status line among them, are each round's own record and no place.

Standard library only. Exit 0 once the file is written; 2, writing nothing, when a list names no
pair of commits, a listed row names no place, or a pair is out of order; 3 when git cannot be run or
a commit cannot be read. This tool makes no security claim.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FEATURE = "specs/005-crypto-architecture-v4/"
LISTS = FEATURE + "checklist-choices.md"
SPEC = FEATURE + "spec.md"
PLAN = FEATURE + "plan.md"
RESEARCH = FEATURE + "research.md"
DATA_MODEL = FEATURE + "data-model.md"
CLI = FEATURE + "contracts/cli.md"
QUICKSTART = FEATURE + "quickstart.md"
FILES = ("research/005/plan-projections.json", "research/005/plan_projections.py")
PLAN_APPROVAL = "afc6769"
OUT = ROOT / "research" / "005" / "place-check.json"

LIST_HEAD = "### Rows that change the protocol"
RULES = "Pre-registered Design Protocol: the changed rules"
APPROVALS = "Review & Approval"
DECISIONS = "Decisions Taken as Defaults"
NOTES = "spec: notes under the Review & Approval table"
INTRO = "data-model: introduction"
VALUES = "plan: Values this plan fixes"
STRUCTURE = ("plan: Project Structure", "plan: Documentation (this feature)",
             "plan: Source Code (repository root)")
FENCE = re.compile(r"^\s*(?:```|~~~)")
HEADING = re.compile(r"^(#{1,6}) (.*)$")
NUMBERED = re.compile(r"^#{1,6} (\d+)\. ")
ITEM = re.compile(r"^- \*\*((?:FR|SC)-\d{3})\*\*")
BULLET = re.compile(r"^- \*\*(.+?)\*\*")
DECISION = re.compile(r"^\| (D\d+) \|")
PAIR = re.compile(r"two commits are ([0-9a-f]{7,40}) \(its choices\) and ([0-9a-f]{7,40}) ")
ROW_ID = re.compile(r"\b(?:(?:SEC|RAT|ANA|PRO|HW|REP)-\d{3}|AR\d+-[A-Z]\d+)\b")


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


def same(a: str | None, b: str | None) -> bool:
    """Two texts are one where they differ only in white space."""
    if a is None or b is None:
        return a is b
    return " ".join(a.split()) == " ".join(b.split())


def clean(title: str) -> str:
    """A heading's name: its emphasised remark and a user story's title and priority left out."""
    title = re.sub(r"\s*\*\([^)]*\)\*\s*$", "", title).strip()
    story = re.match(r"(User Story \d+)\b", title)
    return story.group(1) if story else title


def leaves(lines: list[str]) -> list[tuple[str, int, int, int]]:
    """(name, level, first line, line after the last) of every heading outside fenced code, each
    running to the next heading."""
    heads, fenced = [], False
    for i, line in enumerate(lines):
        if FENCE.match(line):
            fenced = not fenced
        elif not fenced and HEADING.match(line):
            m = HEADING.match(line)
            heads.append((clean(m.group(2)), len(m.group(1)), i))
    return [(name, level, i, heads[k + 1][2] if k + 1 < len(heads) else len(lines))
            for k, (name, level, i) in enumerate(heads)]


def until(lines: list[str], start: int, stop) -> int:
    j = start + 1
    while j < len(lines) and not stop(lines[j]):
        j += 1
    return j


def spec_places(spec: list[str], out: dict[str, str]) -> None:
    for i, line in enumerate(spec):
        m = ITEM.match(line)
        if m:
            j = until(spec, i, lambda s: s.startswith(("- **FR-", "- **SC-", "**", "#")))
            out.setdefault(m.group(1), "\n".join(spec[i:j]))
        m = DECISION.match(line)
        if m:
            out.setdefault(m.group(1), line)
    sections = leaves(spec)
    for name, level, i, j in sections[1:]:
        if name in ("Functional Requirements", "Measurable Outcomes"):
            continue
        if name == APPROVALS:
            k = i + 1
            while k < j and not spec[k].startswith("|"):
                k += 1
            while k < j and spec[k].startswith("|"):
                k += 1
            out[NOTES] = "\n".join(spec[k:j])
        elif name == DECISIONS:
            out["spec: " + name] = "\n".join(s for s in spec[i:j] if not DECISION.match(s))
        elif name == RULES:
            starts = [k for k in range(i + 1, j) if BULLET.match(spec[k])]
            out["changed rules: introduction"] = "\n".join(spec[i:starts[0] if starts else j])
            for a, b in zip(starts, starts[1:] + [j]):
                key = "changed rules: " + BULLET.match(spec[a]).group(1)
                out.setdefault(key, "\n".join(spec[a:b]))
        else:
            out.setdefault("spec: " + name, "\n".join(spec[i:j]))


def place_texts(commit: str, cache: dict[str, dict[str, str]]) -> dict[str, str]:
    """Every place's text at the commit."""
    if commit in cache:
        return cache[commit]
    out: dict[str, str] = {}
    spec_places(show(commit, SPEC), out)
    research = show(commit, RESEARCH)
    first = next((i for i, s in enumerate(research) if re.match(r"^## R\d+\.", s)), len(research))
    if research:
        out["research: introduction"] = "\n".join(research[:first])
    for i, line in enumerate(research):
        m = re.match(r"^## (R\d+)\.", line)
        if m:
            j = until(research, i, lambda s: s.startswith("## "))
            out.setdefault(m.group(1), "\n".join(research[i:j]))
    plan = show(commit, PLAN)
    sections = leaves(plan)
    if plan:
        out["plan: header"] = "\n".join(plan[:sections[1][2] if len(sections) > 1 else len(plan)])
    for name, level, i, j in sections[1:]:
        key = VALUES if name.startswith("Values this plan fixes") else "plan: " + name
        out.setdefault(key, "\n".join(plan[i:j]))
    model = show(commit, DATA_MODEL)
    heads = [(i, level) for _, level, i, _ in leaves(model)]
    numbered = [(k, i, lv) for k, (i, lv) in enumerate(heads) if NUMBERED.match(model[i])]
    if numbered:
        out[INTRO] = "\n".join(model[:numbered[0][1]])
    for k, i, lv in numbered:
        j = next((x for x, level in heads[k + 1:] if level <= lv), len(model))
        out.setdefault("data-model §" + NUMBERED.match(model[i]).group(1), "\n".join(model[i:j]))
    cli = show(commit, CLI)
    sections = leaves(cli)
    if cli:
        first = sections[1][2] if len(sections) > 1 else len(cli)
        out["cli: introduction"] = "\n".join(cli[:first])
    for name, level, i, j in sections[1:]:
        span = re.match(r"^`([^`]+)`", name)
        key = re.sub(r"^scripts/", "", span.group(1)) if span else name
        out.setdefault("cli: " + key, "\n".join(cli[i:j]))
    quick = show(commit, QUICKSTART)
    if quick:
        out["quickstart"] = "\n".join(quick)
    for path in FILES:
        lines = show(commit, path)
        if lines:
            out[path] = "\n".join(lines)
    cache[commit] = out
    return out


def named(parts: list[str], keys: set[str]) -> list[str]:
    """The places that the parts of a "Where" or a Rule cell name, among the places that exist."""
    places: list[str] = []

    def add(found) -> None:
        places.extend(p for p in found if p not in places)

    document = ""
    for part in parts:
        part = part.strip()
        word = re.match(r"(spec|research|data-model|contracts?(?:/cli\.md)?|plan|quickstart|tasks|"
                        r"security\.md|this file)\b", part)
        document = word.group(1) if word else document
        add(k for k in re.findall(r"\b(?:FR|SC)-\d{3}\b", part) if k in keys)
        if document == "tasks" or document == "security.md" or document == "this file":
            continue
        add(k for k in re.findall(r"(?<![\w-])D\d+\b", part) if k in keys)
        add(k for k in re.findall(r"\bR\d+\b", part) if k in keys and "research" in part)
        if "changed rules" in part:
            add(sorted(k for k in keys if k.startswith("changed rules: ")))
        if re.search(r"(Review & Approval )?notes\b", part):
            add([NOTES])
        for name in ("Context", "Edge Cases", "Assumptions", "Key Entities"):
            if name in part and document in ("spec", ""):
                add(["spec: " + name])
        add(k for k in ("spec: " + s for s in re.findall(r"User Story \d+", part)) if k in keys)
        if document == "data-model":
            add(f"data-model §{n}" for n in re.findall(r"§(\d+)", part))
            if "introduction" in part:
                add([INTRO])
        for script in re.findall(r"the contract's `(?:scripts/)?([^`]+)`", part):
            add(sorted(k for k in keys if k.startswith("cli: " + script)))
        if document.startswith("contract") and "the contract's `" not in part:
            add(sorted(k for k in keys if k.startswith("cli: ")))
        if document == "plan":
            rest = part[len("plan"):].strip(' "')
            if not rest:
                add(sorted(k for k in keys if k.startswith("plan: ")))
            if re.search(r"phase \d+|Plan Phases", part):
                add(["plan: Plan Phases"])
            if "Project Structure" in part:
                add(STRUCTURE)
            if "Technical Context" in part or "Testing" in part:
                add(["plan: Technical Context"])
            if "Values this plan fixes" in part:
                add([VALUES])
            for name in ("Summary", "Choices for owner review", "Constitution Check"):
                if name in part:
                    add(["plan: " + name])
        if document == "quickstart":
            add(["quickstart"])
        add(path for path in FILES if path.rsplit("/", 1)[-1] in part)
    return places


def cells_of(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split(" | ")]


def read_lists(commit: str, keys: set[str]):
    """Per round or batch: its heading, its two commits, the rows of its choices tables with the
    places their "Where" cells name, and the rows of its list with their rule, direction and
    places."""
    text = "\n".join(show(commit, LISTS))
    rules: dict[str, list[str]] = {}
    rounds = []
    for section in re.split(r"(?m)^## ", text)[1:]:
        title = section.split("\n", 1)[0].strip()
        if LIST_HEAD not in section:
            continue
        body, _, listing = section.partition(LIST_HEAD)
        heading = (LIST_HEAD[4:] + listing.split("\n", 1)[0]).strip()
        pair = PAIR.search(" ".join(listing.split()))
        if not pair:
            raise Refused(f"the list {heading!r} names no pair of commits")
        rows = []
        for line in body.split("\n"):
            cells = cells_of(line) if line.startswith("| ") else []
            if len(cells) == 5 and ROW_ID.fullmatch(cells[0]):
                rows.append({"row": cells[0], "where": cells[4],
                             "places": named(re.split(r";", cells[4]), keys)})
        listed = []
        for line in listing.split("\n"):
            cells = cells_of(line) if line.startswith("| ") else []
            if len(cells) == 4 and ROW_ID.search(cells[0]):
                inner = re.search(r"\(([^()]*)\)\s*$", cells[1])
                name = cells[1][:inner.start()].strip() if inner else cells[1]
                places = named(re.split(r"[;,]", inner.group(1)) if inner else [], keys)
                if not places:
                    raise Refused(f"the rule {cells[1]!r} of {heading!r} names no place")
                listed.append({"rows": ROW_ID.findall(cells[0]), "rule": name,
                               "direction": cells[2], "places": places})
                for p in places:
                    if p not in rules.setdefault(name, []):
                        rules[name].append(p)
        rounds.append({"title": title, "heading": heading,
                       "commits": [full(pair.group(1)), full(pair.group(2))],
                       "rows": rows, "listed": listed})
    return rules, rounds


def changed(a: dict[str, str], b: dict[str, str]) -> list[str]:
    return sorted(p for p in set(a) | set(b) if not same(a.get(p), b.get(p)))


def commits(c0: str, c1: str) -> list[str]:
    return git("rev-list", "--reverse", f"{c0}..{c1}").split()


def per_commit(c0: str, c1: str, cache) -> list[dict]:
    out = []
    for c in commits(c0, c1):
        places = changed(place_texts(full(c + "^"), cache), place_texts(c, cache))
        if places:
            out.append({"commit": c, "places": places})
    return out


def compare(to: str) -> dict:
    to = full(to)
    cache: dict[str, dict[str, str]] = {}
    bounds = [full(PLAN_APPROVAL)]
    keys: set[str] = set(place_texts(to, cache)) | set(place_texts(bounds[0], cache))
    _, rounds = read_lists(to, keys)
    for r in rounds:
        bounds += r["commits"]
        for c in r["commits"]:
            keys |= set(place_texts(c, cache))
    bounds.append(to)
    for x, y in zip(bounds, bounds[1:]):
        if x != y and subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", x, y]
                                     ).returncode != 0:
            raise Refused(f"{x[:7]} is not an ancestor of {y[:7]}: the pairs are out of order")
    rules, rounds = read_lists(to, keys)
    result_rounds, spans, unmade = [], [], []
    for r in rounds:
        c0, c1 = r["commits"]
        rows = []
        for place in changed(place_texts(c0, cache), place_texts(c1, cache)):
            by_where = [row["row"] for row in r["rows"] if place in row["places"]]
            by_rule = [rid for item in r["listed"] if place in item["places"]
                       for rid in item["rows"]]
            rows.append({"place": place, "rows": by_where, "listed": by_rule})
            if not by_where and not by_rule:
                for e in per_commit(c0, c1, cache):
                    if place in e["places"]:
                        unmade.append({"commit": e["commit"], "place": place, "in": [c0, c1],
                                       "beside": r["heading"]})
        result_rounds.append({"title": r["title"], "heading": r["heading"], "commits": [c0, c1],
                              "rows": len(r["rows"]),
                              "listed": [{k: item[k]
                                          for k in ("rows", "rule", "direction", "places")}
                                         for item in r["listed"]],
                              "changed": rows})
    edges = [(bounds[0], rounds[0]["commits"][0] if rounds else to, None)]
    for k, r in enumerate(rounds):
        nxt = rounds[k + 1]["commits"][0] if k + 1 < len(rounds) else to
        edges.append((r["commits"][1], nxt, r["heading"]))
    for c0, c1, before in edges:
        found = per_commit(c0, c1, cache)
        spans.append({"from": c0, "to": c1, "after": before, "changes": found})
        unmade += [{"commit": e["commit"], "place": place, "in": [c0, c1], "beside": before}
                   for e in found for place in e["places"]]
    return {"lists": LISTS, "plan_approval": bounds[0], "compared_to": to,
            "places": sorted(place_texts(to, cache)), "rules": rules, "rounds": result_rounds,
            "spans": spans, "unmade": unmade}


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
