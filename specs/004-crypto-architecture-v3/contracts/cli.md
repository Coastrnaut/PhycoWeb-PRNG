# CLI Contracts

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

Exit codes, as in feature 003: **0** success; **1** completed with a failing or non-PASS verdict
(by design); **2** refused by a guard (wrong namespace or index, missing approval, budget
exhausted, a fourth candidate, a size out of order, an operation list not in the log, an
environment that does not match its pins, lock held, hash mismatch, broken log chain, existing
record), and nothing is written; **3** tool or I/O error, a recorded tool defect included.
`REP=reports/004-crypto-architecture-v3`. Every record is written through `protocol/evidence.py`
([data-model.md](../data-model.md) §1).

## Guards shared by every script

- **Environment**: `protocol/evidence.py` checks at start that the interpreter and the
  installed packages match research R1 and the pins of `requirements.txt` for that platform,
  and exits 2 on any mismatch. A changed environment needs R1 updated first, with the owner's
  approval.
- **Inputs**: only the namespaces `dev` and `control` of `protocol/devinputs_v3.py`, and for
  US1 the feature-002 `dev` set; anything else exits 2 (FR-040). `control` serves only uniform
  controls and `dev` is never a control: each evidence kind's namespace is fixed in code, not
  chosen on the command line, and the loader refuses `control` for any kind but a control and
  any index outside the use's declared range. Every tool that reads feature 002's or 003's seed
  sets loads only feature 002's `dev` set, with `allow=("dev",)` as `fut_sec8.py` does, and
  exits 2 on any held-out set, as security.md §11.3 requires of development tools;
  `tests/test_protocol_004.py` checks every such call.
- **Operation lists**: every tool refuses an operation list whose SHA-256 has no `proposed` or
  `correction` entry in the candidate log, exit 2 (FR-041).
- **Heavy runs**: a heavy run is any run that is of a kind research R7 budgets, uses more than one
  worker process or thread, or is projected to take, or last took, more than 10 minutes;
  `seed_search` sweeps, exhaustive bijectivity, trail searches and the frequency and
  avalanche tests are examples. Every heavy run takes `data/heavy-run.lock` with an exclusive
  create, projects first (Budget, below) and records `heavy_run` true. If the lock exists, it
  exits 2, naming the lock and whether its holder still runs, checked in the lock's environment.
  The lock holds the PID and that process's start time, the environment (`windows` or `wsl`), the
  host, the command and the time it was taken, and is removed on exit; only `scripts/clear_lock.py`
  removes a stale one (below). A test checks that every budgeted kind and every script with a worker
  option takes the lock (FR-045; research R7, R16).
- **Hash-chained logs**: every append to `research/004/candidates.jsonl`,
  `research/004/protocol-changes.jsonl` or `$REP/provenance.jsonl` takes
  `data/log-append.lock` by exclusive create, checks the chain up to the last line, appends one
  line chained to it, whose `prev_sha256` is the SHA-256 of the previous line's UTF-8 bytes as
  stored, its final LF included (data model §3), and releases the lock. The lock holds the same
  fields as the heavy-run lock, and only `scripts/clear_lock.py` removes a stale one. It exits 2,
  appending nothing, if the lock is not free within 10 s, naming the lock and whether its holder
  still runs, or if the chain is broken (research R16).
- **Order of sizes**: evidence of a kind at 8×8 or 16×16 exits 2 unless that kind's run for the
  candidate at the next smaller claimable size has finished without making it ineligible
  (research R7). The guard counts evidence records only: a `--project` probe at a larger size writes
  nothing but its `projection` record, which is not evidence, so this guard never refuses it, and
  the probes at 8×8 and 16×16 that a 4×4 run's projection needs run before that run (quickstart E7).
- **Approvals**: every guard that reads the spec's Review & Approval table (Order of US1, below;
  `design_freeze.py create`; `repair_log.py`) reads it as committed at HEAD, never the working tree,
  and exits 2 while the working tree's table differs from HEAD's. The rows that open a guard are set
  to Approved and committed by the owner (the note under that table), so an uncommitted row opens
  none, and the owner's review at each ⛔ gate lists the approval commits since the last gate.
- **Order of US1**: any script that loads a key into a state of `phyco-v3` or of any candidate
  exits 2 unless the "FUT-SEC-8 result review" row of the spec's Review & Approval table reads
  Approved at HEAD (Approvals, above; FR-001, FR-003). Key loading is code that loads a key into
  such a state: the mode's instantiate in the model, the research duplex, and any script that runs
  instantiate, such as the instantiation states of research R4. It is not the development-input
  loader, which derives keys but loads none, nor a keyless operation list of Π, nor the design
  document's text. `tests/test_protocol_004.py` fails if `phycoweb/model_v3.py` or a candidate
  defines key loading before that.
- **Tool validation**: one rule for every counted result, positive or negative (FR-039). A
  result of a tool without a `re-found` validation record of its kind and of its exact hash is
  written with `status` `not evaluated` and never counts; a trail or distinguisher it finds is
  recorded as an unverified hypothesis, `blocked`, which blocks the candidate's eligibility
  until a validated tool, or direct evaluation with the validated exact models, settles it
  (data model §5). A tool is validated again after any change to its code (its SHA-256 differs), a
  dependency upgrade, or a use at a word width, operation set or kind of model outside its validated
  kind; until then its results are `not evaluated`. A re-validated version of a tool in the fixed
  set may serve searches not yet run, never a search that reached its cap (Trail tools).
- **Budget**: a script refuses work on a candidate whose budget row is spent (R7), exit 2, and a
  search that reaches its per-instance cap writes `inconclusive`. A heavy run first projects its
  hours on the candidate (at most 60 s), writing a `projection` record (data model §1), and
  exits 2, writing no evidence, unless its projection, plus the probes of every run its row still
  needs (its own kind at every larger claimable size, and every other kind of the row at every
  claimable size, in the row's fixed order of research R7), fits the hours left in its row. A probe
  writes nothing but its `projection` record, and its time counts against the row of the run it
  projects (data model §1).
- **Trail tools**: once the feature's first trail search has started, a trail tool is refused,
  exit 2, unless its name is in the fixed set (the rows of research R12's table: ARX search,
  active-S-box counting, long-trail active-box counting, exhaustive tables) and its exact hash has
  an earlier `re-found` record. A search that reached its cap is refused, exit 2, with any tool or
  version, except as research R7's one re-run after a recorded tool defect; a speed-up is not a
  defect (research R12).

## `fast/build/seed_search` (C, WSL; built by `make -C fast -f seed_search.mk`)

```text
seed_search --check-vectors FILE [FILE ...]
seed_search --s0 S0 --s1 S1 --words W1 W2 W3 [--threads 32] [--progress SECONDS]
```

- `--check-vectors`: regenerates every word of each `phyco-v2` vector file from the seed in its
  header and compares; exit 0 only if all 10,000 words of every file match, 1 otherwise.
- Sweep: S0 and S1 are integers 0…65535 and W1 to W3 32-bit hex words; anything else exits 2.
  For every (s₂, s₃) it runs the 256-step warm-up and compares the first output words, dropping
  a candidate at its first mismatch.
- Output: one JSON object on stdout with the counts after one, two and three words, every
  three-word match, total steps, seconds, steps per second and threads. Progress goes to stderr,
  every SECONDS, written only by the main thread from counters that the worker threads update;
  the workers write nothing (research R2).

## `scripts/fut_sec8.py` (WSL)

```text
fut_sec8.py --binary fast/build/seed_search --out-dir $REP/fut-sec-8 [--repeat-after-defect ID]
fut_sec8.py --verify RECORD
fut_sec8.py --reproduce RECORD --binary fast/build/seed_search --out-dir $REP/fut-sec-8
```

Takes the targets from `protocol.seedsets.load("dev", allow=("dev",))[:3]`, computes the
observations with `phycoweb/model_v2.py`, runs the vector check, then one sweep per target,
separates any extra three-word match with the fourth word, and writes the demonstration record
(data model §4). A second run exits 2 unless `--repeat-after-defect` names a recorded tool
defect (spec Edge Cases). Exit 1 if a target is not recovered.

Neither of the other two modes is a demonstration attempt:

- `--verify RECORD` re-checks every listed three-word match and every recovered seed with
  `model_v2`, in seconds, with no sweep. Exit 1 on any disagreement.
- `--reproduce RECORD` is allowed only after the FUT-SEC-8 result review, and exits 2 before
  it. It re-runs the sweep as a heavy run and writes a `fut-sec-8-reproduction` record, compared
  field by field with the original (data model §4). It can neither replace the demonstration
  record nor change the review, and a difference is a finding, exit 1.

## `scripts/archive_phyco_v2.py`

```text
archive_phyco_v2.py [--check]
```

Copies the files of data model §12 byte for byte into `baseline/phyco-v2/` and writes
`MANIFEST.json`. Exits 2 if the archive exists and differs; `--check` exits 1 on any mismatch
between a copy, its manifest hash and its live source.

## `scripts/validate_tool.py`

```text
validate_tool.py --tool NAME --known KNOWN_ID --out-dir $REP/validation
```

Runs the tool on its known result (`s12`, `s13-decay`, `s13-transport`, `s14`, `s15`,
`fut-sec-8`, a published value such as `speck32-diff`, `speck32-lin`, `present-5r`,
`sparkle-box`, or a structural tool's known result of research R13) and writes a validation
record (data model §7). Exit 1 if not re-found. A published value needs its source recorded
(the entry of `$REP/downloads.json`, or a value the owner provides with its source, and the
paper's table and value) or exits 2. After a failed validation, the re-validation names a
second known result of the tool's kind as well as the first.

For the bias test's validation, `validate_tool.py` draws the 100 synthetic sets of class 5 at each
size from numpy's `Generator(PCG64(s))`, with s = `protocol.devinputs_v3.synthetic_seed(n, j)` (data
model §2). The validation record holds the numpy version and each set's SHA-256, and a reproduction
in the same environment draws the sets again and compares (research R3, R4).

## `scripts/evidence_v3.py`

```text
evidence_v3.py --candidate ID --kind KIND [--size N] [--width W] [--rounds R] [--project] --out-dir DIR
```

KIND is `inverse`, `bijectivity`, `dependency`, `frequency`, `avalanche`, `control`, `symmetry`,
`invariant`, `degree` or `bound` (with `--bound-kind differential|linear --method M`). The
candidate must be in the log; a `bound` needs a validated tool. Writes one record of data model
§5 or §6 and its raw outputs, and appends an `evidence` entry to the candidate log. The counts
are those of research R4 and R13 and cannot be lowered by an option: a `frequency` run covers
both input sets, and an `avalanche` run the flip set and the related-key, related-nonce and
rotational sets. An `avalanche` run needs the candidate's `dependency` record at the same size,
or exits 2; a disagreement with its matrices writes the record with `status` `inconclusive` and
a tool-defect entry, and exits 3. Every run started writes a record, even if aborted
(`inconclusive` or `blocked`, with the reason). `--project` runs the timing probe of research
R7, writes a `projection` record and prints the projected hours against the budget row; it writes no
evidence. A `control` run belongs to no candidate: it runs once per test and size, before that
test's first use at that size by any candidate, writes its record under `$REP/controls/`, which
serves every candidate, and exits 2 if that record exists, except for the one re-run after a
recorded tool defect in the control's own code (data model §5).

## `scripts/d4_choice.py`

```text
d4_choice.py --log research/004/candidates.jsonl --out $REP/d4/choice.json
d4_choice.py --tie --log research/004/candidates.jsonl --out $REP/d4/tie.json
```

Computes the D4 choice of research R6 from saved bound records. Exits 2 if `choice.json`
exists or if no entered set is recorded. After an exact tie, `--tie` writes `tie.json` once,
when R at 4×4 exists for both representatives or one of them is ineligible; before that, or if
`tie.json` exists, it exits 2.

## `scripts/round_rule.py`

```text
round_rule.py --candidate ID           # writes candidates/<ID>/round-rule.json
round_rule.py --select                 # writes $REP/freeze/selection.json
```

R = max(2·R_dist, R_bound + 2, 2·max(R_f, R_b)) per claimable size, every input cited by record
ID. `--select` applies eligibility, the fallback to the other family and the stop rule; exit 1 if
the outcome is a stop. Eligibility is decided for every candidate from its own records (data model
§9): FR-026's figures from its `cost` record per size, written by `research/004/tools/costmodel.py`
from the operation list, P and R; FR-027's semantics from the operation list's declarations;
FR-030's mapping from its `mapping` log entry. A missing item fails eligibility. After a decline at
the owner design review that ends in a further candidate, `--select` runs again over the whole set,
the declined candidate included, and writes `selection-2.json`, citing `selection.json`; if it
selects the declined candidate again, the outcome is a stop, exit 1.

## `scripts/mode_limits_v3.py`

```text
mode_limits_v3.py --out $REP/security-target/limits.json
```

Evaluates the theorem's bound at the limits stated in the design document with ε = 2⁻⁶⁴ and
N = 2¹²⁸ (research R9), and the doubling check. Exit 1 if the bound exceeds ε at the limits;
`theorem` is `unverified` until its paper has been read.

## Generators of constants and vectors

```text
gen_constants_v3.py [--check]                    # writes phycoweb/constants_v3.py
gen_vectors_v3.py [--check] [--variant ID ...]   # writes vectors/phyco-v3/ (research R8)
gen_constructed_v3.py [--check]                  # writes the constructed-state vectors
```

Each writes only deterministic content, under the format rules of the data model's
introduction. The command (script and arguments, relative to the repository root), the
interpreter, the model's SHA-256, the platform, the measured speed and the generation time go to
the sidecar `vectors/phyco-v3/MANIFEST.json`, one entry per generator run (data model §11),
which `--check` does not compare. `gen_constants_v3.py` also writes each constant table as
`vectors/phyco-v3/constants_n<n>_w<w>.json`. `--check` regenerates in memory and exits 1 on any
byte difference. After the freeze, writing over a frozen file exits 2.

They run in three steps, each generator's `--check` passing before the next step (data model §11):
(1) `gen_constants_v3.py`; (2) `gen_vectors_v3.py`, which writes the vectors through `pi` and
`ResearchDuplex`, which runs no self-test, and also writes `phycoweb/selftest_v3.py`, the
self-test's inputs and expected output, copied from the vectors, so its `--check` covers that file
too; (3) `Generator` imports `phycoweb.selftest_v3` and runs its self-test from it. Tests check that
`Generator` reproduces the vectors and that `selftest_v3` equals them, and the freeze hashes
`selftest_v3.py` with the vectors (data model §13).

## `scripts/design_freeze.py`

```text
design_freeze.py create                 # writes $REP/freeze/freeze.json with status draft
design_freeze.py approve --by NAME --wording TEXT   # the owner's approval; changes nothing else
design_freeze.py validate               # recomputes draft_sha256 and every hash
```

The freeze runs in five steps (FR-043): (1) the owner commits the feature files; (2) `create`
runs with `git_dirty` false and writes the record as `draft`; (3) the owner runs `approve`, which
writes the approval into it; (4) the owner commits the record; (5) `validate` exits 0. Dirty means a
tracked file modified or an untracked file not ignored; ignored files, the locks and the
local-only outputs, do not count. The record holds what data model §13 lists: among others
`rationale.md`, the selected operation list, `research/004/ir.py` with its tools, the verdict
scripts, every evidence record behind R by ID and by SHA-256, and the last `seq` and line
SHA-256 of the candidate log, the provenance log and the protocol change log.

`create` reads the spec's Review & Approval table at HEAD (Approvals, above) and exits 2 if the
owner design review row is not Approved, if the external review row is
neither done nor "not arranged", or if `git_dirty` is true. `create` stores `draft_sha256`, the
SHA-256 of the record's canonical JSON without that field and the approval fields. `approve`, run by
the owner, changes `status` from `draft` to `approved`, adds `approved_by`, `approved_utc` and
`approval_wording`, and changes nothing else. `validate` recomputes `draft_sha256` and every hash
and checks the format rules; it exits 1 if anything but the approval fields changed or a hash does
not match, and 2 while `status` is `draft` (data model §13).

## `scripts/recheck_004.py`

```text
recheck_004.py [--kind KIND]
```

Recomputes every verdict of the feature from saved outputs (FR-065) and compares it with the
recorded one. Exit 1 on any disagreement, with each listed. Every verdict is recomputable on a
fresh clone from committed files, so it works from the committed per-round summaries, for
example R_f from the per-round flag "every output bit depends on every input bit". Where
local-only outputs are present, it also re-derives each committed summary from them. Its output
lists both checks per kind, and it verifies the inventory of superseded operation lists
(data model §3).

## `scripts/repair_log.py`

```text
repair_log.py --log LOG --approval REF
```

Repairs a broken hash chain in one of the three logs, only with the owner's go-ahead: `--approval`
names the row "Log repair <n>" of the spec's Review & Approval table, and the script reads the spec
at HEAD and exits 2 unless that row reads Approved and names the same log and the `seq` of the
break. The broken file is kept unchanged with its SHA-256, and a `repair` entry records the break's
position, its cause and what was restored. Entries after the break count only where the records they
cite corroborate them, and the final report states the repair (research R16).

## `scripts/clear_lock.py`

```text
clear_lock.py LOCK                      # data/heavy-run.lock or data/log-append.lock
```

Run by the owner or at the owner's request. It removes LOCK only when it can show, in the
lock's environment, that no process with the PID and start time the lock holds still runs;
otherwise it exits 2 and removes nothing. It writes a `lock-cleared` record under
`$REP/locks/` with the lock's content and, for the heavy-run lock, the `inconclusive` record
of the run that died holding it (data model §1; research R16).

## `scripts/check_claims.py`

```text
check_claims.py
```

Checks README, security.md §1.1 and §15 and the disclaimers against `protocol/claims.json`, that
every hand-written document of this feature carries the design-form disclaimer, and that
forbidden wording (FR-050) appears only in the rules that forbid it. Exit 1 on any finding
(SC-018). `tests/test_claims.py` runs it.
