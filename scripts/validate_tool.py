#!/usr/bin/env python3
"""Feature 004: a tool re-finds a known result before its results count (FR-039; SC-007).

    validate_tool.py --tool NAME --known KNOWN_ID --out-dir $REP/validation
    validate_tool.py --reproduce RECORD [--owner-request "WORDS (DATE)"]

Exit 0 `re-found`, 1 `not re-found`, 2 refused, nothing written, 3 a tool failure. The contract is in
specs/004-crypto-architecture-v3/contracts/cli.md and the record in data-model section 7.

A tool's module gives `validation(known_id, known, keep)`, which runs the tool on one known result and
returns what it found, whether that is the known result, and its validated kind. `known` is the
module of a self-written or published known result, or None for a finding of security.md, and
`keep(name, data)` holds a local-only output. It may give `CODE`, the other files it runs,
`inputs(known_id)`, the record's `inputs`, `MODEL_ID`, and `HEAVY`, the known results that are heavy
runs, with `projection(known_id)`, their hours and measured speed.

Known results are read from research/004/validation/, each module naming its tool, its known result and
what it is the second of. A published value also names its download, or stands on an `owner-provided`
entry. After a failed validation a committed note, research/004/validation/defects/<record_id>.json,
holds the defect, its cause and the fix; the next attempt reads it and re-finds every known result of
the tool in one record. This script makes no security claim.
"""
import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
for place in (str(ROOT / "research/004"), str(ROOT)):
    if place not in sys.path:
        sys.path.insert(0, place)

from protocol import evidence  # noqa: E402
from protocol.evidence import NONE, Refused, ToolFailure  # noqa: E402

VALIDATION_REL = "research/004/validation"
DEFECTS_REL = VALIDATION_REL + "/defects"
TOOLS_REL = "research/004/tools"
OUT_DIR = evidence.REP_REL + "/validation"
LICENCE = "GPL-3.0, this repository"
CODE = ["scripts/validate_tool.py", "protocol/evidence.py", "protocol/disclaimer.py",
        "protocol/devinputs_v3.py"]
NOTE_FIELDS = ("defect", "cause", "fix")
FIRST = "none"
RUN_HERE = """
import importlib.util, sys
spec = importlib.util.spec_from_file_location("validate_tool", "scripts/validate_tool.py")
module = importlib.util.module_from_spec(spec)
sys.modules["validate_tool"] = module
spec.loader.exec_module(module)
getattr(module, sys.argv[1])(*sys.argv[2:])
"""


@dataclass(frozen=True)
class Tool:
    """`name` is the record's `tool`. `source` is what `tool_sha256` hashes; `driver` the module that
    gives `validation`, the source itself for a Python tool; a C tool also has its binary and make file."""
    name: str
    source: str
    driver: Optional[str] = None
    binary: Optional[str] = None
    make: Optional[str] = None


@dataclass(frozen=True)
class Known:
    known_id: str
    tool: str
    path: Optional[str]
    second_of: str
    statement: str = NONE


TOOLS: Dict[str, Tool] = {
    "bias": Tool("bias", f"{TOOLS_REL}/bias.py"),
    "invariants": Tool("invariants", f"{TOOLS_REL}/invariants.py"),
    "symmetry": Tool("symmetry", f"{TOOLS_REL}/symmetry.py"),
    "dependency": Tool("dependency", f"{TOOLS_REL}/dependency.py"),
    "degree": Tool("degree", f"{TOOLS_REL}/degree.py"),
    "bijectivity": Tool("bijectivity", f"{TOOLS_REL}/bijectivity.py"),
    "avalanche": Tool("avalanche", f"{TOOLS_REL}/avalanche.py"),
    "costmodel": Tool("costmodel", f"{TOOLS_REL}/costmodel.py"),
    "fut_sec8": Tool("fut_sec8", "fast/seed_search.c", f"{TOOLS_REL}/fut_sec8_known.py",
                     "fast/build/seed_search", "fast/seed_search.mk"),
    "exhaustive tables": Tool("exhaustive tables", f"{TOOLS_REL}/trails/tables.py"),
    "active-S-box counting": Tool("active-S-box counting", f"{TOOLS_REL}/trails/active_sbox.py"),
    "long-trail active-box counting": Tool("long-trail active-box counting",
                                           f"{TOOLS_REL}/trails/long_trail.py"),
    "ARX search": Tool("ARX search", f"{TOOLS_REL}/trails/arx_search.c",
                       f"{TOOLS_REL}/trails/arx_search_known.py",
                       f"{TOOLS_REL}/trails/build/arx_search", f"{TOOLS_REL}/trails/arx_search.mk"),
}
FINDINGS: Dict[str, Tuple[str, str]] = {
    "s7": ("symmetry", "security.md S7, its three rotation relations"),
    "s12": ("bias", "security.md S12, ranges and classes"),
    "s13-decay": ("invariants", "security.md S13(a), the vein decay's merged pair"),
    "s13-transport": ("invariants", "security.md S13(b), the transport difference"),
    "s14": ("bias", "security.md S14, the vein lanes' bit frequencies"),
    "s15": ("bias", "security.md S15, its 16 steps and its bound"),
    "fut-sec-8": ("fut_sec8", "the reviewed demonstration record, its three seeds and vector check"),
}
PUBLISHED: Dict[str, str] = {
    "speck32-diff": "ARX search",
    "speck32-lin": "ARX search",
    "present-tables": "exhaustive tables",
    "present-5r": "active-S-box counting",
    "sparkle-box": "long-trail active-box counting",
}


# ------------------------------------------------------------------------------ what is known

def load_module(path: Path) -> ModuleType:
    name = "validation_" + path.stem.replace("-", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def known_results() -> Dict[str, Known]:
    """Every known result: the files under research/004/validation/, the findings, and the published
    values whose file is not written yet, which stand on an `owner-provided` entry or are refused."""
    table: Dict[str, Known] = {}
    for known_id, (tool, statement) in FINDINGS.items():
        table[known_id] = Known(known_id, tool, None, FIRST, statement)
    for known_id, tool in PUBLISHED.items():
        table[known_id] = Known(known_id, tool, None, FIRST)
    directory = evidence.REPO.path(VALIDATION_REL)
    for path in sorted(directory.glob("*.py")) if directory.exists() else ():
        module = load_module(path)
        table[module.KNOWN_ID] = Known(module.KNOWN_ID, module.TOOL, evidence.rel_to_repo(path),
                                       module.SECOND_OF)
    return table


def load_known(known: Known) -> Optional[ModuleType]:
    return load_module(evidence.REPO.path(known.path)) if known.path else None


def seconds_of(table: Dict[str, Known], known_id: str) -> List[Known]:
    return [k for k in table.values() if k.second_of == known_id]


def of_tool(table: Dict[str, Known], name: str) -> List[Known]:
    return [k for k in table.values() if k.tool == name]


# ------------------------------------------------------------------------------------- guards

def guard_out_dir(out_dir: str) -> None:
    if Path(out_dir).as_posix() != OUT_DIR and \
            Path(out_dir).resolve() != evidence.REPO.path(OUT_DIR).resolve():
        raise Refused(f"records go under {OUT_DIR}")


def entries_of(rel: str, entries: Sequence[Dict]) -> List[Dict]:
    return [e for e in entries if e.get("path") == rel]


def logged(known: Known, entries: Sequence[Dict], before: int) -> Dict:
    """A self-written known result's entry: its hash the file's, and logged before the tool."""
    if known.path is None:
        return {"known_id": known.known_id, "statement": known.statement}
    found = entries_of(known.path, entries)
    if not found:
        raise Refused(f"{known.path} has no provenance entry")
    digest, kind = evidence.named_hash(known.path)
    if found[-1]["sha256"] != digest:
        raise Refused(f"{known.path} differs from its provenance entry")
    first = min(e["seq"] for e in found)
    if first >= before:
        raise Refused(f"{known.path} was logged after its tool's first entry")
    return {"known_id": known.known_id, "path": known.path, "sha256": digest, "sha256_kind": kind,
            "provenance_seq": first}


def guard_order(tool: Tool, targets: Sequence[Known], table: Dict[str, Known]) -> Dict[str, Dict]:
    """Each known result and each second stands in the log, unchanged, before the tool's first entry
    (data-model sections 7 and 14)."""
    entries = [entry for entry, _ in evidence.check_chain(evidence.PROVENANCE_LOG_REL)]
    own = entries_of(tool.source, entries)
    if not own:
        raise Refused(f"{tool.source} has no provenance entry")
    before = min(e["seq"] for e in own)
    cited = {}
    for known in targets:
        cited[known.known_id] = logged(known, entries, before)
        for second in seconds_of(table, known.known_id):
            cited[second.known_id] = logged(second, entries, before)
    return cited


def owner_provided(known_id: str) -> Optional[Dict]:
    """The entry the owner gave for a value, with its row Approved at HEAD, or a refusal."""
    entries = [e for e in evidence.read_manifest()
               if e.get("status") == "owner-provided" and e.get("known") == known_id]
    if not entries:
        return None
    entry = entries[-1]
    digest = evidence.approval_hash(entry)
    for row in evidence.head_table():
        if row.gate.startswith("Owner-provided value") and row.decision == "Approved" \
                and digest in row.notes:
            return {"entry": entry["name"], "source": entry["source"], "value": entry["value"],
                    "row": row.gate, "approval_sha256": digest}
    raise Refused(f"{entry['name']}: no row \"Owner-provided value <n>\" reads Approved at HEAD")


def guard_source(known: Known) -> Dict:
    """A published value needs a `fetched` entry of the manifest, or an `owner-provided` one."""
    if known.known_id not in PUBLISHED:
        return {"repository": known.path or known.statement}
    provided = owner_provided(known.known_id)
    if provided is not None:
        return provided
    module = load_known(known)
    if module is None:
        raise Refused(f"{known.known_id}: no recorded source for its value")
    fetched = [e for e in evidence.read_manifest()
               if e.get("name") == module.DOWNLOAD and e.get("status") == "fetched"]
    if not fetched:
        raise Refused(f"{known.known_id}: {module.DOWNLOAD} is not a fetched entry of the manifest")
    return {"entry": module.DOWNLOAD, "sha256": fetched[-1]["sha256"], "paper": module.PAPER,
            "table": module.TABLE, "value": module.VALUE}


def open_failure(tool: Tool) -> Optional[Dict]:
    """The tool's `not re-found` record that no attempt answers. Each re-validation names the failure
    it follows, so that the attempts form a chain whatever their times, a second apart or less: a
    failed re-validation is the open failure in its turn, and a `re-found` one closes the chain."""
    records = [r for _, r in evidence.iter_records("validation", "validation")
               if r.get("tool") == tool.name]
    answered = {(r.get("re_validation") or {}).get("failed_record") for r in records}
    failed = [r for r in records
              if r.get("outcome") == "not re-found" and r["record_id"] not in answered]
    return max(failed, key=lambda r: r["created_utc"]) if failed else None


def defect_note(failed: Dict) -> Tuple[str, Dict]:
    rel = f"{DEFECTS_REL}/{failed['record_id']}.json"
    path = evidence.REPO.path(rel)
    if not path.exists():
        raise Refused(f"after {failed['record_id']}, {rel} must hold the defect, its cause and the fix")
    note = json.loads(path.read_bytes().decode("utf-8"))
    if note.get("failed_record") != failed["record_id"]:
        raise Refused(f"{rel} names another record")
    for field in NOTE_FIELDS:
        if not note.get(field):
            raise Refused(f"{rel} holds no {field}")
    return rel, note


def targets_after(failed: Dict, tool: Tool, table: Dict[str, Known]) -> List[Known]:
    """Every known result of the tool, the first and the second at each of its widths; a first with
    no second leaves the tool unvalidated (data-model section 7; ANA-076)."""
    every = of_tool(table, tool.name)
    for known in every:
        if known.second_of == NONE and not seconds_of(table, known.known_id):
            raise Refused(f"{tool.name} has no second known result of {known.known_id}, so it stays "
                          f"unvalidated after {failed['record_id']}")
    return every


# ------------------------------------------------------------------------------------ measuring

def measure(tool: Tool, known_ids: Sequence[str], keep: Callable[[str, bytes], Any],
            binary: Optional[str] = None) -> Dict[str, Dict]:
    """One result per known result, from the tool's own module."""
    table = known_results()
    module = load_module(evidence.REPO.path(tool.driver or tool.source))
    if binary is not None:
        module.BINARY = binary
    try:
        return {known_id: module.validation(known_id, load_known(table[known_id]), keep)
                for known_id in known_ids}
    except (Refused, ToolFailure):
        raise
    except Exception as exc:
        raise ToolFailure(f"{tool.name}: {type(exc).__name__}: {exc}") from exc


def measure_here(tool_fields: str, out: str, known_ids: str, local: str, binary: str) -> None:
    """The run of a reproduction, in its worktree: everything is read from that commit."""
    def keep(name: str, data: bytes) -> None:
        target = Path(local) / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    results = measure(Tool(**json.loads(tool_fields)), known_ids.split(","), keep,
                      None if binary == NONE else binary)
    Path(out).write_bytes(evidence.pretty(results))


def project_here(tool_fields: str, out: str, known_id: str) -> None:
    """A heavy reproduction's projection, in its worktree."""
    tool = Tool(**json.loads(tool_fields))
    module = load_module(evidence.REPO.path(tool.driver or tool.source))
    Path(out).write_bytes(evidence.pretty(list(module.projection(known_id))))


def run_here(worktree: Path, function: str, tool: Tool, *arguments: str) -> Any:
    """A subprocess in the worktree, since a reproduction reads the code at the original's commit."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "results.json"
        done = subprocess.run([sys.executable, "-X", "utf8", "-c", RUN_HERE, function,
                               json.dumps(asdict(tool)), str(out), *arguments],
                              cwd=worktree, capture_output=True, text=True, encoding="utf-8",
                              errors="replace")
        if done.returncode != 0:
            raise ToolFailure(f"the tool exited {done.returncode}: {done.stderr.strip()[-400:]}")
        return json.loads(out.read_bytes().decode("utf-8"))


def measure_in(worktree: Path, tool: Tool, known_ids: Sequence[str], local: Path,
               binary: Optional[str]) -> Dict[str, Dict]:
    return run_here(worktree, "measure_here", tool, ",".join(known_ids), str(local), binary or NONE)


def project_in(worktree: Path, tool: Tool, known_id: str) -> Tuple[float, Any]:
    hours, speed = run_here(worktree, "project_here", tool, known_id)
    return hours, speed


def outcome_of(results: Dict[str, Dict]) -> str:
    return "re-found" if all(result["re_found"] for result in results.values()) else "not re-found"


def verdict(results: Dict[str, Dict]) -> Tuple[str, str, int, List[Dict]]:
    outcome = outcome_of(results)
    assertions = [{"assertion": f"{known_id} is re-found", "holds": bool(result["re_found"])}
                  for known_id, result in results.items()]
    if outcome == "re-found":
        return outcome, "pass", evidence.EXIT_OK, assertions
    return outcome, "fail", evidence.EXIT_VERDICT, assertions


def tool_code(tool: Tool, module: ModuleType, table: Dict[str, Known],
              targets: Sequence[Known]) -> List[str]:
    code = list(CODE) + [tool.source]
    code += [rel for rel in (tool.driver, tool.binary, tool.make) if rel]
    code += list(getattr(module, "CODE", ()))
    for known in targets:
        for item in [known] + seconds_of(table, known.known_id):
            if item.path:
                code.append(item.path)
    return list(dict.fromkeys(code))


def fields_of(tool: Tool, known_id: str, targets: Sequence[Known], cited: Dict[str, Dict],
              sources: Dict[str, Dict], results: Dict[str, Dict], table: Dict[str, Known]) -> Dict:
    digest = evidence.sha256(evidence.REPO.path(tool.source).read_bytes())
    seconds = seconds_of(table, known_id)
    first = dict(cited[known_id])
    if "value" in sources[known_id]:
        first["value"] = sources[known_id]["value"]
    return {"tool": tool.name, "version": digest, "tool_sha256": digest, "licence": LICENCE,
            "source": sources[known_id],
            "validated_kind": {k: r["validated_kind"] for k, r in results.items()},
            "known_result": first,
            "second_known_result": cited[seconds[0].known_id] if seconds else NONE,
            "found": {k: r["found"] for k, r in results.items()},
            "outcome": outcome_of(results)}


def validate(args: argparse.Namespace, command: List[str]) -> int:
    guard_out_dir(args.out_dir)
    if args.tool not in TOOLS:
        raise Refused(f"no tool {args.tool!r}")
    tool = TOOLS[args.tool]
    table = known_results()
    if args.known not in table:
        raise Refused(f"no known result {args.known!r}")
    known = table[args.known]
    if known.tool != tool.name:
        raise Refused(f"{args.known} is a known result of {known.tool}, not of {tool.name}")
    failed = open_failure(tool)
    targets = [known]
    note_rel: Optional[str] = None
    note: Dict = {}
    if failed is not None:
        note_rel, note = defect_note(failed)
        targets = targets_after(failed, tool, table)
    sources = {item.known_id: guard_source(item) for item in targets}
    cited = guard_order(tool, targets, table)
    module = load_module(evidence.REPO.path(tool.driver or tool.source))
    code = tool_code(tool, module, table, targets) + ([note_rel] if note_rel else [])
    ids = [item.known_id for item in targets]
    inputs = getattr(module, "inputs", lambda _: NONE)(args.known)
    heavy = any(item in getattr(module, "HEAVY", ()) for item in ids)
    run = evidence.Run("validation", model_id=getattr(module, "MODEL_ID", None), code_files=code,
                       argv=command, inputs=inputs, heavy=heavy)
    with run:
        if heavy:
            started = time.monotonic()
            hours, speed = module.projection(args.known)
            evidence.write_projection(run=f"the validation of {tool.name} on {args.known}",
                                      row=evidence.FEATURE_ROW, inputs=inputs, measured_speed=speed,
                                      projected_hours=hours, argv=command, code_files=code,
                                      time_hours=(time.monotonic() - started) / 3600.0)
            evidence.guard_feature_row([hours])
            run.begin(hours)

        def keep(name: str, data: bytes) -> None:
            run.output(name, data, local=True)

        results = measure(tool, ids, keep)
        fields = fields_of(tool, args.known, targets, cited, sources, results, table)
        if failed is not None:
            fields["re_validation"] = dict(
                {name: note[name] for name in NOTE_FIELDS}, failed_record=failed["record_id"],
                known_results=ids, note_sha256=evidence.sha256(evidence.REPO.path(note_rel).read_bytes()))
        outcome, status, exit_status, assertions = verdict(results)
        path = run.finish(status, classification=evidence.classify("validation", outcome),
                          exit_status=exit_status, assertions=assertions, fields=fields)
    print(f"{evidence.rel_to_repo(path)}: {tool.name} on {args.known}: {outcome}")
    return exit_status


def kept_outputs(local: Path) -> List[Dict]:
    """The files a reproduction's run kept, as a record lists them, for the comparison with the
    original's: each is deterministic and local-only."""
    entries = []
    for path in sorted(p for p in local.rglob("*") if p.is_file()):
        data = path.read_bytes()
        entries.append({"path": path.relative_to(local).as_posix(), "sha256": evidence.sha256(data),
                        "sha256_kind": "raw", "bytes": len(data), "committed": False,
                        "deterministic": True})
    return entries


def reproduce(args: argparse.Namespace, command: List[str]) -> int:
    path = Path(args.reproduce)
    path = path if path.is_absolute() else evidence.REPO.path(args.reproduce)
    if not path.exists():
        raise Refused(f"{args.reproduce} does not exist")
    original = json.loads(path.read_bytes().decode("utf-8"))
    if original.get("kind") != "validation" or "outcome" not in original:
        raise Refused(f"{args.reproduce} is no finished validation record")
    tool = TOOLS.get(original["tool"])
    if tool is None:
        raise Refused(f"no tool {original['tool']!r}")
    known_ids = list(original["found"])

    def run(place: evidence.Place) -> Dict:
        started = time.monotonic()
        rebuilt = place.binaries.get(tool.binary) if tool.binary else None
        results = measure_in(place.worktree, tool, known_ids, place.local,
                             str(rebuilt) if rebuilt else None)
        outcome, status, exit_status, assertions = verdict(results)
        fields = {name: original[name] for name in ("tool", "version", "tool_sha256", "licence",
                                                    "source", "known_result", "second_known_result")}
        fields.update(kind="validation", model_id=original.get("model_id"), variant_id=None,
                      inputs=original["inputs"], exit_status=exit_status, assertions=assertions,
                      status=status, classification=evidence.classify("validation", outcome),
                      code_sha256=original["code_sha256"], outputs=kept_outputs(place.local),
                      validated_kind={k: r["validated_kind"] for k, r in results.items()},
                      found={k: r["found"] for k, r in results.items()}, outcome=outcome,
                      hours_used=(time.monotonic() - started) / 3600.0)
        return fields

    def projection(worktree: Path) -> Tuple[float, Any]:
        return project_in(worktree, tool, original["known_result"]["known_id"])

    return evidence.reproduce(evidence.Reproduction(
        record_path=path, run=run, heavy=bool(original.get("heavy_run")),
        owner_request=args.owner_request, project=projection, code_files=CODE, argv=command))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--tool")
    parser.add_argument("--known")
    parser.add_argument("--out-dir")
    parser.add_argument("--reproduce")
    parser.add_argument("--owner-request")
    args = parser.parse_args(argv)
    command = ["scripts/validate_tool.py"] + list(argv if argv is not None else sys.argv[1:])

    def run() -> int:
        if args.reproduce:
            return reproduce(args, command)
        if not args.tool or not args.known or not args.out_dir:
            raise Refused("a validation needs --tool, --known and --out-dir")
        return validate(args, command)

    return evidence.main_guard(run)


if __name__ == "__main__":
    sys.exit(main())
