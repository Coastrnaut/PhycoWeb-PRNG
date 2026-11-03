# CLI Contracts

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

Exit codes, as in feature 003: **0** success; **1** completed with a failing or non-PASS verdict
(by design); **2** refused by a guard (wrong namespace or index, missing approval, budget
exhausted, a fourth candidate, a size out of order, an operation list not in the log, an environment
that differs from its record, code not committed at HEAD, lock held, hash mismatch, broken log
chain, existing record), and nothing is written; **3** tool or I/O error, a recorded tool defect
included. `REP=reports/004-crypto-architecture-v3`. Every record is written through
`protocol/evidence.py` ([data-model.md](../data-model.md) §1), as `<record_id>.json` in its kind's
directory, unless the data model states its name (data model §1, Record files).

**Reproduction.** Every script that writes evidence or generated files also runs as
`--reproduce RECORD` (data model §1): it runs the recorded command's configuration in a separate
worktree of the original's `git_head`, the code files of its `code_sha256` checked against
that commit's blobs, with its output directory replaced by the main tree's
`$REP/reproductions/<record_id>/<n>/`, n = 1, 2, … for successive reproductions of that record, and
writes a `reproduction` record there: the original's ID and SHA-256, the commit it ran, each
compared field with its outcome, the reported fields, and `match` or `differs`. The outputs that the
original commits go there, under the same suffix and 10 MB rules, and an output it keeps
local-only goes to `data/local/004/<record_id>/`, `<record_id>` there being the
reproduction's own, its SHA-256 compared (data model §1). It runs only in the
environment that made the original, as recorded, a re-check's reproduction excepted
(research R1). It appends nothing to the candidate log, charges no candidate's
budget row and is not a re-run under research R7, so it can neither replace
evidence nor add any; the Budget and Order of sizes guards, which concern
evidence, do not refuse it, and every other guard applies, Committed code with the
original's commit in HEAD's place, so a search that reached its cap is not
reproduced (Trail tools). It is a heavy run where research R7 says so: it then runs only
with `--owner-request "WORDS (DATE)"`, the owner's request quoted with its
date, which its record keeps, and exits 2 without one; it takes the lock,
projects first and is charged to research R7's feature-wide row. A light
reproduction needs no request. A difference is a finding, exit 1: the original
stands; a difference in a field that enters a verdict blocks the candidate's eligibility, `blocked`,
until it is resolved, and, since it ran in the environment that made the original, it is a tool
defect of research R7, whose one re-run is new evidence in the original's row; a difference in the
p-values, which decide no verdict, makes the outcome `differs` and blocks nothing (data model §1).
`fut_sec8.py --reproduce` is this mode for the demonstration, under the conditions of its section.
`downloads.py`, `owner_record.py` and `design_freeze.py` have no `--reproduce`, each recording an
owner's act or an outside fact that a later run cannot regenerate, as their sections state (research
R16; REP-085).

## Guards shared by every script

- **Environment**: every write through `protocol/evidence.py` or through the log writers
  `protocol/changelog.py` and `protocol/provenance.py` checks at start the running
  environment against the platform's environment record in force (research
  R1) as a whole: Python, every package and version of `pip freeze` (one
  added, upgraded or removed), gcc and make in WSL, and the Windows build or
  the WSL distribution and kernel. Any difference exits 2, writing nothing and naming it, a Windows
  or WSL update included, for every write but the environment record itself (below); the
  owner then writes a new environment record with `scripts/owner_record.py
  environment` and approves it, with R1 updated first when a pinned version changes, and each later
  record, and each entry of the provenance log, the protocol change log and the downloads manifest,
  names the record in force as its `environment` (data model §1; REP-082). While the running
  environment differs from the record in force, or none is in force, the guard admits one write, the
  environment record itself, written by `owner_record.py environment` and checked instead against R1
  and the pins of `requirements.txt` for that platform, exit 2 on any difference, its `environment`
  field `none`, with the interpreter's version and each pinned package's version that the check
  compared, and, while the protocol change log does not exist, `protocol_seq` and
  `protocol_line_sha256` `none`, the guard "Protocol log" admitting it then (below; PRO-071). Every
  other write, a `lock-cleared` record included, also exits 2 unless the record in
  force has its Review & Approval row, "Environment record <n>", Approved at HEAD with
  its approval hash, kind `canonical`, the SHA-256 of its canonical JSON
  without the approval fields (data model introduction, §1; REP-083), an
  approval that needs no lock, so that a stale lock found after an update is
  cleared once the new record is approved; before the first record no lock can be held, since no
  log writer or heavy run starts before it (PRO-068). Each platform's first record comes before
  every other write, in plan phase 1's order (REP-082). Where the owner commits a new environment
  record's row on its own between the commit that records the owner design review's
  approval and the freeze's step (1), the owner design review is held again in
  "Owner design review <k>", naming the same versions where nothing else
  changed, and step (1) follows that row's approval (spec FR-043; PRO-072).
  `scripts/recheck_004.py` alone is exempt: it recomputes verdicts from committed
  counts by exact integer arithmetic and imports only the standard library and `protocol/` (its
  section, below).
- **Committed code**: a run that writes evidence exits 2 unless every source file in its
  `code_sha256` matches HEAD, committed and unmodified, which constitution 1.3.0's standing
  authorization to commit makes routine; data and report files may still be dirty, and the record
  lists the dirty paths. A binary is rebuilt from committed source, its hash reported only, and a
  test checks each record's `code_sha256` entries against the blobs at its `git_head` (FR-053;
  research R16). For `--reproduce`, the commit is the original's `git_head`, checked out in a
  separate worktree (introduction). A run that writes evidence also exits 2 while a file a record
  would cite, such as the sidecar or `research/004/candidates/superseded.json`, is modified in the
  working tree, so that `dirty_paths` never holds a cited file (data model introduction).
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
- **Protocol log**: every script that writes evidence exits 2, writing nothing, through
  `protocol/evidence.py`, while `research/004/protocol-changes.jsonl` does not exist, its chain does
  not check, or its first entries, one per listed row of every round answered before it was created
  and one per place the owner confirmed as an entry of its own (`protocol_change.py`, below), do not
  all hold the owner's `approval_confirmed`, each checked against the first 16 digits of the
  approval hash that the guard recomputes from the first entries as `protocol_change.py`
  computes it (below; REP-094); every record then cites the log's last entry in
  `protocol_seq` and `protocol_line_sha256` (spec FR-044; data model §1, §18). A `lock-cleared`
  record (`clear_lock.py`, below) and an environment record written by `owner_record.py environment`
  (below) are the two kinds `protocol/evidence.py` writes while the log does not exist, each with
  both fields `none`: the first since it records an event and clearing a stale lock is what lets the
  log be created (PRO-065), the second since it records the platform, holds no result and comes
  before the log, whose writer, `protocol/changelog.py`, checks the running environment against it
  (PRO-071); once the log exists each cites the last entry as every record does, an environment
  record written after a Windows or WSL update included. A `lock-cleared` record, like every other
  write, waits until the platform's environment record in force reads Approved at HEAD (Environment,
  above; PRO-068). `tests/test_protocol_004.py` covers the refusal of every other kind, both
  exceptions (PRO-071) and a first entry whose digits do not match (REP-094).
- **Order of sizes**: evidence of a kind at 8×8 or 16×16 exits 2 unless that kind's run for the
  candidate at the next smaller claimable size has finished without making it ineligible
  (research R7). The guard counts evidence records only: a `--project` probe at a larger size writes
  nothing but its `projection` record, which is not evidence, so this guard never refuses it, and
  the probes at 8×8 and 16×16 that a 4×4 run's projection needs run before that run (quickstart E7).
- **Approvals**: every guard that reads the spec's Review & Approval table (Environment, above;
  Order of US1, below; `round_rule.py --select`; `design_freeze.py create`;
  `repair_log.py`; `validate_tool.py`'s source guard; `check_claims.py`;
  `protocol_change.py create`; the test of the second transcription's provenance) reads
  it as committed at HEAD, never the working tree, and exits 2 while the
  working tree's table differs from HEAD's. The rows that open a guard are set
  to Approved and committed by the owner (the note under that table), so an uncommitted row opens
  none, and the owner's review at each ⛔ gate lists the approval commits since the last gate. A
  review held again is a numbered row, "FUT-SEC-8 result review <k>", "Security-target review <k>"
  or "Owner design review <k>" (k = 2, 3, …), and a guard that reads such a family reads its row
  with the highest k, which must name by path and SHA-256 what the run cites: the latest
  demonstration record (Order of US1), or the chapter's version and the design document's version
  with the latest selection record (`design_freeze.py create`), the chapter's version being a set
  that `create` compares item by item, the SHA-256 of the chapters "Security target" and "Mode" and
  of `parameters.json` and `limits.json`, with the design document's version
  read (spec, the notes under the Review & Approval table). L1 is recorded
  again after a later row of either review family in "L1 recorded <k>", which
  names the highest-k row of each family, and `check_claims.py` reads the "L1 recorded" row with the
  highest k. The comparison of spec FR-044 is confirmed in the row "Place check",
  and one made again over later commits in "Place check <k>", each naming
  `research/004/place-check.json` by SHA-256, and `protocol_change.py create` reads
  the one with the highest k (PRO-063). A guard opens on Approved alone,
  except that `design_freeze.py create` also takes done, naming the manifest the review read by
  SHA-256, or "not arranged" on the external review's row, the one with the highest k among the rows
  of its family, "External design review" and "External design review <k>", that name
  the latest selection record (SEC-078), and `round_rule.py --select` takes
  "Not needed" on the "D4 tie" row (data model §17).
- **Order of US1**: any script that loads a key into a state of `phyco-v3` or of any candidate
  exits 2 unless the "FUT-SEC-8 result review" row of the spec's Review & Approval table, or the
  "FUT-SEC-8 result review <k>" with the highest k once the review has been held again, reads
  Approved at HEAD and names the latest demonstration record by path and SHA-256
  (Approvals, above; FR-001, FR-003). Key loading is code that loads a key into
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
  kind; until then its results are `not evaluated`. A use at a word width or kind of model outside
  its validated kind counts only once a further known result covering it, fixed with its source
  before the tool's first validation, is re-found, since a validation on the known results the tool
  had never widens its kind; a candidate's operation set is covered by that candidate's
  cross-checks, which are checks of the tool, not uses: they write no `not evaluated` and call for
  no validation again (research R12). A re-validated version of a tool in the fixed
  set may serve searches not yet run, never a search that reached its cap (Trail tools).
- **Budget**: a script refuses work on a candidate whose budget row is spent (R7), exit 2, and a
  search that reaches its per-instance cap writes `inconclusive`. A heavy run first projects its
  hours on the candidate (at most 60 s), writing a `projection` record (data model §1), and
  exits 2, writing no evidence, unless its projection, plus the probes of every run its row still
  needs (its own kind at every larger claimable size, and every other kind of the row at every
  claimable size, in the row's fixed order of research R7), fits the hours left in its row. A probe
  writes nothing but its `projection` record, and its time counts against the row of the run it
  projects (data model §1). Every candidate's 12 h row is charged, at each size, the hours of that
  size's uniform controls (research R4), read from the `control` records, which append nothing to
  the candidate log, or by projection until they exist; the row of a candidate `withdrawn`,
  `rejected` or `ineligible` is charged no control that runs after that decision, and a
  candidate whose row cannot hold a control's hours takes no test of that kind at
  that size, its evidence there inconclusive, and is charged nothing for it
  (research R4, R7; ANA-074). Every heavy run that charges no candidate,
  the FUT-SEC-8 row's one pass per target excepted, a validation or re-validation, on a published
  value or on any other known result (research R7), a heavy reproduction, a FUT-SEC-8
  repeat after a tool defect or FR-053's test with two worker counts, projects
  first against research R7's feature-wide 66 h row and exits 2, writing
  nothing but its `projection` record, unless its projection fits the hours left there.
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
fut_sec8.py --binary fast/build/seed_search --out-dir $REP/fut-sec-8
            [--repeat-after-defect ID --owner-request "WORDS (DATE)"]
fut_sec8.py --verify RECORD
fut_sec8.py --reproduce RECORD --binary fast/build/seed_search --owner-request "WORDS (DATE)"
```

Takes the targets from `protocol.seedsets.load("dev", allow=("dev",))[:3]`, computes the
observations with `phycoweb/model_v2.py`, runs the vector check, then one sweep per target,
separates any extra three-word match with the fourth word, and writes a demonstration record,
`fut-sec-8/<record_id>.json` (data model §4). The first run is the demonstration's one pass per
target, with its vector check, under its own budget row (spec, Pre-registered Design Protocol). A
second run exits 2 unless `--repeat-after-defect` names a recorded tool defect that no earlier
record names (spec Edge Cases) and `--owner-request` quotes the owner's request with its date, so
that the agent never starts a repeat; the repeat, its vector check included, is a heavy
run charged to research R7's feature-wide row, against which it projects
first (Budget, above), and writes beside the first, holding `supersedes`, the
earlier record's ID, `defect`, the defect's, and `owner_request`. Exit 1
if a target is not recovered.

Neither of the other two modes is a demonstration attempt, and each takes a demonstration record by
its ID, so that every earlier record stays reproducible:

- `--verify RECORD` re-checks every listed three-word match and every recovered seed with
  `model_v2`, in seconds, with no sweep. Exit 1 on any disagreement.
- `--reproduce RECORD` is allowed only after the FUT-SEC-8 result review, and exits 2 before
  it. It re-runs the sweep, a heavy run of about 2³² × 257 steps per target,
  only with `--owner-request "WORDS (DATE)"`, the owner's request quoted
  with its date, which its `reproduction` record keeps, and exits 2 without
  one; it takes the lock, projects first and is charged to research R7's
  feature-wide row, as the introduction states. It writes a `reproduction` record
  under `$REP/reproductions/<record_id>/<n>/`, its outputs placed as the
  introduction describes, taking no `--out-dir`, compared field by field with the
  original under data model §1's rule: the demonstration's fields listed
  there are compared, its timings and the binary's hash reported only, and `design_sha256`, which no
  FUT-SEC-8 code reads, is not compared (data model §4). It can neither replace the demonstration
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
validate_tool.py --reproduce RECORD
```

Runs the tool on its known result (`s12`, `s13-decay`, `s13-transport`, `s14`, `s15`,
`fut-sec-8`, a published value such as `speck32-diff`, `speck32-lin`, `present-5r`,
`sparkle-box`, or a structural tool's known result of research R13) and writes a validation record
(data model §7). Each known result names its tool, as research R13 states: the invariant
checks re-find `s13-decay` and `s13-transport`, the bias test `s12`, `s14` and
`s15`, `fut_sec8.py`'s tools `fut-sec-8`, and each trail tool its published
value. Exit 1 if not re-found. A published value needs its source recorded, an
entry of `$REP/downloads.json` (research R19): a `fetched` file's entry with the paper's table and
value, or the `owner-provided` entry of a value the owner provides with its source, written by
`scripts/owner_record.py owner-provided`, whose Review & Approval row "Owner-provided value <n>"
reads Approved at HEAD (Approvals, above); any other entry, or none, exits 2. For each known result
at a validated width, the first and each further one, the first validation on it records its second
known result at that width, fixed with its source in the provenance log before the tool's first
validation, or the statement that it has none (data model §7, §14); after a failed validation at any
width, the re-validation re-finds every known result of the tool, the first and the second at each
of its widths, and for a tool with none at one of its widths it exits 2,
leaving the tool unvalidated (ANA-076). `--reproduce RECORD` runs that record's
validation again, as the introduction describes, and compares the fields data model §1 lists for a
validation.

For the bias test's validation, `validate_tool.py` draws at each size the 100 synthetic sets of
class 5, j = 0…99, and the 100 of the second family, j = 100…199, which plant their bit at position
⌊(j − 100)·S/100⌋, from numpy's `Generator(PCG64(s))`, with the seeds s from
`protocol.devinputs_v3.load('dev', 'synthetic', allow=('dev',), count=200,
n=n)` (data model §2, §7); in each family the planted bit must fire in 82 to 97 of its 100 sets, a
set counting only when its planted bit fires, and at most 3 of its sets may
hold a firing of an unplanted bit, each reported with its set, position and
count, more making the validation `not re-found`, exit 1 (data model §7).
The sets are local-only, under `data/local/004/<record_id>/`, and regenerated by this deterministic
command; the record commits each set's SHA-256, the numpy version and a per-set summary, the planted
bit's count and every fired bit, so a fresh clone recomputes both families' verdicts from committed
files and a regeneration checks every count (data model §7). No set is ever replaced: a later draw,
`--reproduce` included, must reproduce every hash in an environment with that numpy version, and a
draw that differs is reported and counts for nothing. After an approved numpy upgrade the old record
stays the validation in the old environment, and a new validation, a new record, decides in the new
one: outside 82 to 97, or with more than 3 sets holding an unplanted firing, the
tool is unvalidated there, its results `not evaluated`, until a defect is
found and fixed (research R3, R4).

## `scripts/evidence_v3.py`

```text
evidence_v3.py --candidate ID --kind KIND [--size N] [--width W] [--rounds R] [--project] --out-dir DIR
evidence_v3.py --kind control --test frequency|avalanche --size N [--project] --out-dir DIR
evidence_v3.py --reproduce RECORD
```

KIND is `inverse`, `bijectivity`, `dependency`, `frequency`, `avalanche`, `control`, `symmetry`,
`invariant`, `degree`, `bound` (with `--bound-kind differential|linear --method M`) or
`cross-check` (with `--tool NAME`), the cross-check between kinds of data model §7
on the candidate's boxes or nonlinear layer, charged to its trail row. The
candidate must be in the log; a `bound` needs a validated tool. Writes one record of data model §5,
§6 or §7 (a cross-check) and its raw outputs, and for a `bound` run of a tool that
searches Π also a `trail` record of the optimal characteristic it returns
(data model §6), and appends an `evidence` entry to the candidate log; with
`--reproduce RECORD` it runs that record's configuration as the introduction describes, writes only
its `reproduction` record and appends nothing. The counts
are those of research R4 and R13 and cannot be lowered by an option: a `frequency` run covers
both input sets, and an `avalanche` run the flip set and the related-key, related-nonce and
rotational sets. An `avalanche` run needs the candidate's `dependency` record at the same size,
or exits 2; a disagreement with its matrices writes the record with `status` `inconclusive` and
a tool-defect entry, and exits 3. Every run started writes a record, even if aborted
(`inconclusive` or `blocked`, with the reason). `--project` runs the timing probe of research
R7, writes a `projection` record and prints the projected hours against the budget row; it writes no
evidence. A `control` run, the second form, belongs to no candidate and takes no `--candidate`: it
runs once per test and size, before that test's first use at that size by any candidate, projects
first and runs once every row it counts can hold its hours, each charged them in full (Budget): the
12 h row of every entered candidate, except a candidate `withdrawn`, `rejected` or `ineligible`,
whose row is charged no control that runs after that decision, and a candidate whose
row cannot hold the hours, which takes no test of that kind at that size,
its evidence there inconclusive, and is charged nothing for it (ANA-074),
writes its record under `$REP/controls/`, with `model_id` and `variant_id`
null and its inputs from the `control` namespace, which serves every candidate, appends no
candidate-log entry, and exits 2 if that record exists, except for the one re-run after a
recorded tool defect in the control's own code (data model §5).

## `scripts/d4_choice.py`

```text
d4_choice.py --log research/004/candidates.jsonl --out $REP/d4/choice.json
d4_choice.py --tie --log research/004/candidates.jsonl --out $REP/d4/tie.json
d4_choice.py --choose ID --seen SHA256 --by NAME --out $REP/d4/tie-choice.json
d4_choice.py --reproduce RECORD
```

Computes the D4 choice of research R6 from saved bound records, using only those of a
tool that has passed its cross-check on that candidate, which each record's
`cross_check` cites (data model §6, §8). Exits 2 if `choice.json` exists, if
no entered set is recorded, or until every entered candidate has a final reduced-width outcome for
each bound kind at 16 and, where research R6 needs it, at 8: a bound record, the `inconclusive`
record of a capped search, or an `ineligible` or `rejected` log decision; the choice record lists
each outcome, and no search is retried to reach a score. After an exact tie, `--tie` writes
`tie.json` once, when R at 4×4 exists for both representatives or one of them is ineligible, with
`decided_by` (`R at 4×4`, `carry chains`, `ineligible` or `owner`); before that, or if `tie.json`
exists, it exits 2. While the tie waits, only the two representatives are analysed at the production
width, at 4×4 and only as far as R at 4×4 needs, and every other candidate of both families waits;
once `tie.json` decides, the losing representative stops, its records standing, as its family's
fallback (research R6, R7; RAT-072). `--choose`, run by the owner after `tie.json` exists,
prints `tie.json`'s SHA-256 and exits 2 unless standard input is an interactive terminal and the
owner types its first 16 hex digits; it writes `d4/tie-choice.json` with the choice, who, when,
`seen_sha256` and `choice_confirmed`, the digits typed, and exits 2 if that hash differs from
`tie.json`'s, if no tie exists, if a tie-break decided it (`decided_by` other
than `owner`) or if a choice exists; `tie.json` is never rewritten. Running
`--choose` is the owner's own act, which the agent never performs (spec FR-043, FR-044).

## `scripts/round_rule.py`

```text
round_rule.py --candidate ID           # writes candidates/<ID>/round-rule.json
round_rule.py --select                 # writes $REP/freeze/selection.json, later selection-<k>.json
round_rule.py --close                  # writes the candidate log's set-closed entry
round_rule.py --choose ID --seen SHA256 --by NAME   # writes the latest selection's tie choice
round_rule.py --reproduce RECORD       # a round-rule or selection record (introduction)
```

R = max(2·R_dist, R_bound + 2, 2·max(R_f, R_b)) per claimable size, every input cited by record ID.
It computes from the evidence records the N of spec FR-028's family-wise rate, the pairs of a
claimable size and a round count r at which the bias tests ran with 2r above the R then in force, up
to each firing's record for the rate stated beside it and by the freeze for the final report's
(ANA-075). With N it computes the avalanche test's term, its runs up to the same record, size by
size, a being 1 at a size where it measured at most 128 round counts and m/128 where it measured m
above 128, and the rate 1 − 0.995^(T·N)·∏(1 − 0.005·a)^T over the sizes run (spec FR-028; ANA-079).
`--close` writes the candidate log's `set-closed` entry once every candidate has a final
decision (`withdrawn`, `rejected` or `ineligible`, or, for an eligible candidate, its round-rule
record at every claimable size) and no `replacement` entry of the log is `pending` (data model §3),
an entry logged closed at once with the reason "cause shared" reading as closed (ANA-073), and
exits 2 otherwise. The representative that lost an exact D4 tie has its final decision as the
other family's candidates have theirs: `ineligible`, with the reason "D4 chose the other family by
its tie-breaks", unless the chosen family ends with no eligible candidate, when its family is
analysed as research R7 states (RAT-072). `--select` exits 2 before the `set-closed` entry,
and after a D4 tie until the spec's "D4 tie" row reads, at HEAD (Approvals, above), Approved with
the SHA-256 of `d4/tie-choice.json` where `d4/tie.json`'s `decided_by` is `owner`, or "Not needed",
naming the tie record and its tie-break, where a tie-break decided it, the family then taken
from `d4/tie.json`; it applies eligibility, the fallback to the other family, both families where
the D4 record's outcome is `not computable` (research R6), and the stop rule; exit 1
if the outcome is a stop. Eligibility is decided for every candidate from
its own records (data model §9): FR-018's folding rule, longest link, food nodes and tree figures
from the operation list and its `parameters` entry; FR-020's cycles per call and FR-026's figures
from its `cost` records per size, written by `research/004/tools/costmodel.py` from the operation
list, P and R; FR-022's bounds from its bound records; FR-023's statement on the streams and
FR-024's ranking report from its log entries; FR-025's stages, chains per phase and key path from
the operation list's declarations, checked by code; FR-027's semantics from the
operation list's declarations; FR-030's mapping from its `mapping` log entry.
FR-025's interface formats, call sequence and zeroization rules are the mode's,
decided once in the mode chapter. A missing item fails eligibility, and so does a `reproduction`
record of one of the candidate's records that differs on a field that enters a verdict, or a
`recheck` record that disagrees with one of them under the rules in force at its entry, until a
re-run after a recorded tool defect resolves it (data model §1, §9); `--select` reads the `recheck`
records beside the `reproduction` records and exits 2 while one holds an
unresolved disagreement for a record it cites. Any change before the freeze that
touches any candidate's eligibility or R at 4×4 after a selection record exists makes `--select` run
again over the whole set and write the next record, `selection-<k>.json`, k = 2, 3, …, citing the
previous one by path and SHA-256; earlier records stay. After a decline at the owner design review
that ends in a further candidate, that re-selection includes the declined candidate, and
if it selects the declined candidate again, the outcome is a stop, exit 1.
The decline reopens the set once, for one further candidate, replaced the same way if it becomes
`rejected` or `ineligible`, and `--close` writes a second `set-closed` entry
before `--select` runs again. `--choose`, run by the owner after a tie in the latest selection
record, prints that record's SHA-256 and exits 2 unless standard input is an interactive terminal
and the owner types its first 16 hex digits; it writes `freeze/selection-tie-choice.json`, or
`freeze/selection-<k>-tie-choice.json` for `selection-<k>.json`, with the choice, who, when,
`seen_sha256` and `choice_confirmed`, and exits 2 if that hash differs from the record's, if the
record has no tie or if a choice for it exists. A choice binds only the record whose hash it names:
a tie in a later record needs a new choice and a row of its own, "Selection tie
<k>", which `design_freeze.py create` reads as it reads "Selection tie".
Running `--choose` is the owner's own act, which the agent never performs (spec FR-043, FR-044).
`round-rule.json` keeps its fixed name: before it changes, `protocol/evidence.py` keeps its current
content as `versions/<sha256>.json` beside it, and the new content holds `previous_sha256` (data
model introduction). A selection record is never rewritten.

## `scripts/mode_limits_v3.py`

```text
mode_limits_v3.py --out $REP/security-target/limits.json
mode_limits_v3.py --reproduce RECORD
```

Evaluates the theorem's bound at the limits stated in the design document with ε = 2⁻⁶⁴ and
N = 2¹²⁸ (research R9), and the doubling check. Exit 1 if the bound exceeds ε at the limits;
`theorem` is `unverified` until its paper has been read: each theorem's entry cites the paper's
`fetched` entry in `downloads.json` by SHA-256, with the theorem's number and page, and the
script refuses `verified`, exit 2, without such an entry or when the file on
disk has another SHA-256 (data model §10). It also writes the size profile
`parameters.json` beside `limits.json` (data model §10), each row from the variant table and the
design document's layout, with FR-010's generic-bound checks computed by code; exit 1 on any
violation at a claimable size. Both files keep their fixed names: before one changes, its current
content is kept as `security-target/versions/<sha256>.json`, and the new content holds
`previous_sha256` (data model introduction). After the freeze it runs only with `--reproduce`, whose
record goes under `$REP/reproductions/`, and `protocol/evidence.py` refuses, exit 2, to write over
either file, which the freeze record pins (data model §13).

## Generators of constants and vectors

```text
gen_constants_v3.py [--check]                    # writes phycoweb/constants_v3.py
gen_constants_v3.py --candidate ID --variant VARIANT   # before the freeze (research R15)
gen_constants_v3.py --exploration N W            # outside the supported sizes (research R15)
gen_vectors_v3.py [--check] [--variant ID ...]   # writes vectors/phyco-v3/ (research R8)
gen_constructed_v3.py [--check]                  # writes the constructed-state vectors
gen_constants_v3.py --reproduce RECORD           # a generator-run or generator-check record
gen_vectors_v3.py --reproduce RECORD
gen_constructed_v3.py --reproduce RECORD
```

Each writes only deterministic content, under the format rules of the data model's
introduction. The command (script and arguments, relative to the repository root), the
interpreter, the model's SHA-256, the platform, the measured speed and the generation time go to the
sidecar `vectors/phyco-v3/MANIFEST.json`, append-only, one entry per generator run citing the
`record_id` of that run's `generator-run` record, which each run writes under `$REP/generator-runs/`
with the fields of data model §1 (FR-061) and each written file's path and SHA-256, the
sidecar left out, its entry being appended once the record is written, and
the freeze hashing the sidecar with the vectors (data model §11; REP-092);
`--check` does not compare the sidecar. `gen_constants_v3.py` also writes each constant table
as `vectors/phyco-v3/constants_n<n>_w<w>.json`. `--check` regenerates in memory, compares every
generated file byte for byte with the committed one and writes a `generator-check` record under
`$REP/generator-checks/` with the fields of data model §1 (FR-061), each generated file's path and
SHA-256 and the verdict `match` or `differs`; it exits 1 on any byte difference. SC-009's evidence
is each generator's pair of such records, one per platform, which quickstart M1 to M3 and the final
report cite. The sidecar is frozen with the vectors (data model §13), as the record of the runs that
produced them: after the freeze a generator runs only with `--check`, `--reproduce` or, for
`gen_constants_v3.py`, `--exploration`, which write their records under `$REP`, an exploration run's
beside its table (below), and never to the sidecar, and writing over a frozen file exits 2.
`--reproduce RECORD` (introduction), on each generator, runs the command of that `generator-run`
record again and compares every file it generates, in memory, with the SHA-256 the record holds
rather than with the file on disk, so that a later regeneration changes nothing, or, for a
`generator-check` record, runs that `--check` again and compares its hashes and verdict; it writes
no `.py` or `.hex` file and adds nothing to the sidecar, its `reproduction` record, under
`$REP/reproductions/<record_id>/<n>/`, holding each file's path, SHA-256 and outcome.

`gen_constants_v3.py --candidate ID --variant VARIANT` writes, before the freeze, the table of that
variant (n, w, R) of the candidate, with each call type's stream where its streams are distinct,
from the instance of the rule in its log entry's `parameters`, as
`research/004/candidates/<id>/constants/<variant>.json`, `<variant>` being the variant ID's part
after the design, with every check of research R15, and a `generator-run` record under
`$REP/generator-runs/` holding each table's path and SHA-256 and each check's verdict; it adds
nothing to the sidecar and exits 2 after the freeze. A table is written before the first record that
reads it, a rise of R writing the new variant's first (research R7), and a failed check or a
refused-list match makes the candidate fail FR-023, logged.

`gen_constants_v3.py --exploration N W` writes, before or after the freeze, the table of an (n, w)
outside the supported sizes, with every check of research R15, as
`research/004/exploration/constants_n<n>_w<w>.json`, and beside it its check record, a
`generator-run` record with `exploration` true, written through `protocol/evidence.py` to that
directory; it writes no frozen file, no sidecar entry and no evidence, and refuses a supported
(n, w), exit 2. A failed check, a refused-list match included, leaves that (n, w) without a table,
its record stating why, and is a finding recorded at once in security.md and the report (spec
FR-051), as a match found after the freeze is; `phyco-v3` stays as frozen.

They run in four steps, each generator's `--check` passing before the next step (data model §11):
(1) `gen_constants_v3.py`; (2) `gen_vectors_v3.py`, which writes the vectors through `pi` and
`ResearchDuplex`, which runs no self-test, and also writes, in the same run, from a
`ResearchDuplex` object of its own run through the self-test's call sequence alone,
each request with its forget call (spec FR-059; REP-096), each claimable
size's `selftest_<variant>.json`, the self-test's inputs and every expected
block, whole (spec FR-059), and `phycoweb/selftest_v3.py`, copied from those
files, so its `--check` covers them too (HW-077); (3) `Generator` imports
`phycoweb.selftest_v3` inside its constructor only and runs its self-test from it, so
step (2) imports the model before that module exists (model contract, Module rules);
(4) `gen_constructed_v3.py`, run once step (3)'s self-test has passed, which writes the
constructed-state vectors through `pi`, `pi_inv` and `ResearchDuplex` only, its research path to
chosen states included (model contract, Research duplex; REP-077, REP-078). `gen_constructed_v3.py`
and its `--check` run first `tests/test_model_v3.py`'s named test `test_generator_selftest`, which
builds a `Generator` and runs its self-test, on the platform where they run, exiting 2 unless it
passes and recording its result in the record each writes, so that step (4)'s pair of check records
shows that step (3) passed on each platform (SC-009; REP-086). Tests check that
`Generator` reproduces the vectors and that `selftest_v3` equals them, and the freeze hashes
`selftest_v3.py` with the vectors and the three generators, `gen_constants_v3.py`,
`gen_vectors_v3.py` and `gen_constructed_v3.py` (data model §13; REP-077).

## `scripts/design_freeze.py`

```text
design_freeze.py create                 # writes $REP/freeze/freeze.json with freeze_status draft
design_freeze.py approve --by NAME --wording TEXT   # the owner's approval; changes nothing else
design_freeze.py validate               # recomputes draft_sha256 and every hash
```

The freeze runs in five steps (FR-043): (1) the owner commits the feature files, the owner's next
commit after the one that records the owner design review's approval, the agent
committing no file of this feature from the first commit that records an owner
design review's approval to the feature's end, plan phase 9 included, a later row "Owner design
review <k>" and the change it reviews included, which the owner commits (PRO-070; SEC-084; PRO-072);
where the owner must commit a row on its own between that approval and this step, "Environment
record <n>" after a Windows or WSL update or "Log repair <n>", the owner design review is held again
in "Owner design review <k>", naming the same versions where nothing else changed, and step (1) is
then the owner's next commit after the commit that records that row's approval
(PRO-072); (2) `create` runs with `git_dirty` false, records that commit as
`owner_commit` and writes the record with `freeze_status` `draft`; (3) the owner runs `approve`,
which writes the approval into it; (4) the owner commits the record; (5) `validate` exits 0. Dirty
means a tracked file modified or an untracked file not ignored; ignored files, the locks and the
local-only outputs, do not count. The record holds what data model §13 lists: among others the
design document's version, named 1.0, with `reviewed_version`, the header's
0.<k> that it hashes, the files keeping that line (spec FR-034; RAT-080),
`rationale.md`, the selected operation list, `research/004/ir.py` with its tools, the
verdict scripts, `validate_tool.py` and `fut_sec8.py` among them, both freeze files, every module of
the repository that a frozen script imports, directly or through another module, listed from the
scripts' imports (REP-091), every evidence record behind R by ID and by SHA-256, and the last `seq`
and line SHA-256 of the candidate log, the provenance log and the protocol change log. The freeze's
code is `protocol/design_freeze.py`, with create, approve and validate as functions, and this script
is the command that calls it, as the other scripts call `protocol/evidence.py`; the record hashes
both files (data model §13).

`create` reads the spec's Review & Approval table at HEAD (Approvals, above) and exits 2 if the
security-target review's or the owner design review's row, the one with the highest k where
the review has been held again, is not Approved or does not review what the
record freezes, by path and SHA-256: the chapter's version, compared item by item, so that a
change to the chapters "Security target" or "Mode" or to `parameters.json` or
`limits.json` after the review, a `verified` or met mark included, exits 2 until a
"Security-target review <k>" naming the changed set reads Approved, while a change
elsewhere in the design document leaves that review standing; and the design
document's version with the latest selection record; if no row of the external review's family names
the latest selection record (each row names the selection record it applies to, a done row through
its manifest and a "not arranged" row when it is written), or if the highest-k row that does is
neither done nor "not arranged", or reads done and names no manifest, or one that neither
`review-package/MANIFEST.json` nor its `versions/` holds, so that a new selection record needs a row
of its own and a review done for another candidate is cited for the candidate and the version it
read only (spec FR-043; SEC-078), if the latest selection record has a tie
and its row, "Selection tie" or "Selection tie <k>", does not read Approved
with the SHA-256 of its choice record, if a theorem the mode chapter uses
is not `verified` in `limits.json` or a precondition of it is not marked met there, naming the
theorem, those marks being read as `unverified` while the security-target review row does not read
Approved (research R10), if `phycoweb/constants_v3.py`'s tables differ from the selected candidate's
at a supported (n, w) and its final R (research R15), if the design document's header holds a line
other than its title, the disclaimer and its line "Version: …" (spec FR-034), if the commit that
follows the one recording the owner design review's approval, in its row with the highest k, the
owner's commit of step (1), is not HEAD (spec FR-043; PRO-070), if, in the provenance log at HEAD,
an AI-drafted section of the design document or of `rationale.md` has a latest entry that is not a
review entry reading `accepted`, or one that names a row other than its review's with the highest k,
the security-target review's for the chapters "Security target" and "Mode" and the owner design
review's for every other section (spec FR-034; RAT-082), if `check_claims.py`
reports a finding at HEAD (SEC-084), or if `git_dirty` is true. `create`
stores that commit's hash as `owner_commit`, and `draft_sha256`, the SHA-256 of the record's
canonical JSON without that field and the approval fields, `freeze_status`, `approved_by`,
`approved_utc`, `approval_wording` and `approval_confirmed`, `record_id` included, which `create`
computes first, kind `canonical` (data model introduction, §13; REP-083, REP-084, REP-092). The
record's common `status` is computed by code as every record's is, `pass` once each of `create`'s
checks holds, as it must for `create` to write the record, and its fields of a run hold `create`'s,
`inputs` and `outputs` `none` (data model §1, §13; REP-093). `approve`, run by
the owner, prints `draft_sha256` and exits 2 unless standard input is an interactive terminal and
the owner types its first 16 hex digits; it then changes `freeze_status` from `draft` to `approved`,
adds `approved_by`, `approved_utc`, `approval_wording` and `approval_confirmed`, and changes nothing
else, the record keeping the `record_id` that `create` gave it (REP-092). Steps (1), (3)
and (4) are the owner's own acts, which the agent never performs (FR-043).
`validate` recomputes `draft_sha256` and every hash
and checks the format rules; it exits 1 if anything but the approval fields changed or a hash does
not match, and 2 while `freeze_status` is `draft` (data model §13). It has no `--reproduce`: the
record holds the owner's commit and approval, acts that a later run cannot regenerate, and
`validate` recomputes every hash the record holds (introduction; research R16; REP-085).

## `scripts/review_package.py`

```text
review_package.py [--check]               # writes $REP/review-package/ and its MANIFEST.json
review_package.py --reproduce RECORD      # a review-package record (introduction)
```

Run by the agent. It assembles the review package of spec FR-063 through
`protocol/review_package.py` and writes its manifest, `$REP/review-package/MANIFEST.json`, a record
of kind `review-package` with the fields of data model §16, through `protocol/evidence.py`, keeping
the earlier manifest under `versions/` first (data model introduction). `--check` rebuilds the
manifest from the files it lists, each hashed as data model §16 states, and compares it with the
committed one, exit 1 on any difference. Since the script writes a record, it also runs as
`--reproduce RECORD` (introduction). Sending the package is the owner's outward action (spec FR-063;
REP-085).

## `scripts/recheck_004.py`

```text
recheck_004.py [--kind KIND]
recheck_004.py --reproduce RECORD
```

Recomputes every verdict of the feature from saved outputs (FR-065) and compares it with the
recorded one. Its kinds are those of FR-065's list: the demonstration; the tool validations and
re-validations and the cross-checks between kinds; the inverse, bijectivity, dependency, bias,
uniform-control, symmetry, invariant, degree and bound checks; the D4 choice; the check of generated
files on each platform; the size profile's generic-bound checks and the bound at the limits;
eligibility and selection, each recomputed from committed counts by exact arithmetic. Exit 1
on any disagreement, with each listed. Every verdict is recomputable on a
fresh clone from committed files, so it works from the committed per-round summaries, for
example R_f from the per-round flag "every output bit depends on every input bit". Where
local-only outputs are present, it also re-derives each committed summary from them. Its output
lists both checks per kind, and it verifies the inventory of superseded operation lists
(data model §3). With `--reproduce RECORD` it runs a recorded re-check again, as the introduction
describes, comparing its verdicts and counts (data model §1); like the re-check, it may run in any
environment.

It recomputes each verdict under the rules in force at the protocol change-log entry its record
cites and, where a later stricter change applies (FR-044), also under the current rules; both are
listed. A disagreement under the rules in force at a record's entry is a finding: the record's
result becomes an unverified hypothesis, `blocked` (spec FR-060), until it is resolved, and the
disagreement is a tool defect of research R7, whose one re-run follows the fix; one under a later
stricter change is that change's recomputed verdict, applied as a stricter change and recorded in
the change log's `results_known` (data model §18), not a defect. A reproduction of a `recheck`
record that differs is a tool defect of this script wherever it ran, since its verdicts and counts
depend on no environment. A cited file kept under a fixed name is resolved
from its `versions/` (data model introduction). Under the rules in force at a record's entry it runs
the verdict functions at that record's `git_head` (below), and under the current rules those at
HEAD.

It is exempt from the environment guard (Guards, above): it recomputes verdicts from committed
counts by exact integer arithmetic (data model §5), with the verdict functions of
`protocol/evidence.py` that the scripts which wrote the records call, for the rules in force at a
record's entry those at its `git_head`, taken from a separate worktree of that
commit and named per record, so that it runs the code that produced each
verdict (FR-043) and a function changed before the freeze is never applied to
records it did not compute, and it imports only the standard library and those
`protocol/` modules that do the same, which a test checks. It writes a `recheck` record,
`$REP/rechecks/<record_id>.json`, holding the interpreter, the platform and the full `pip freeze` it
ran with, and says when that environment is not one of research R1's. A reproduction that re-runs
evidence stays in the environment that made its original (research R1); SC-017's fresh clone is this
re-check, as quickstart F3 runs it.

## `scripts/repair_log.py`

```text
repair_log.py --log LOG --approval REF
```

Repairs a broken hash chain in one of the three logs, only with the owner's go-ahead: `--approval`
names the row "Log repair <n>" of the spec's Review & Approval table, and the script reads the spec
at HEAD and exits 2 unless that row reads Approved and names the same log and the `seq` of the
break. The broken file is kept unchanged with its SHA-256, and a `repair` entry records the break's
position, its cause and what was restored. Entries after the break count only where the records they
cite corroborate them, and the final report states the repair (research R16). Where the owner
commits a "Log repair <n>" row on its own between the commit that records the owner design review's
approval and the freeze's step (1), the owner design review is held again in "Owner design review
<k>", naming the same versions where nothing else changed, and step (1) follows that row's approval
(spec FR-043; PRO-072).

## `scripts/owner_record.py`

```text
owner_record.py environment --platform windows|wsl --by NAME   # $REP/environment-<platform>.json
owner_record.py owner-provided --known KNOWN_ID --value TEXT --source TEXT --words TEXT --by NAME
```

Run by the owner only: each mode is an owner's own act, outside the standing authorization for local
commits, which the agent never performs (spec FR-044). `environment` records the running environment
as research R1 lists it, the one write the Environment guard admits while the running environment
differs from the platform's record in force or none is in force, checked against R1 and the pins of
`requirements.txt` for that platform instead, exit 2, writing nothing, on any difference, its
`environment` field `none`, with the interpreter's version and each pinned package's version that
the check compared (PRO-068); each platform's first record comes before every other write through
`protocol/evidence.py` or a log writer, and a new one follows the wheels' install, in plan phase 1's
order (REP-082); while the protocol change log does not exist, the guard "Protocol log" admits an
environment record with `protocol_seq` and `protocol_line_sha256` `none`, as it admits a
`lock-cleared` record, and once it exists each environment record, one written
after a Windows or WSL update included, cites its last entry as every record
does (PRO-071); `owner-provided` adds an entry to `$REP/downloads.json` with
the owner's words, the source the owner names, the date and the value's SHA-256 (research R19). Each
mode prints the approval hash of what it writes, kind `canonical`, the SHA-256 of its
canonical JSON without the approval fields, `approved_by`, `approved_utc` and
`approval_confirmed`, an environment record's `record_id` included, which is computed
first, without them (data model introduction; REP-083, REP-092), and exits 2,
writing nothing, unless standard input is an interactive terminal and the owner
types its first 16 hex digits; it then writes the record or entry with `approved_by`, `approved_utc`
and `approval_confirmed`, keeping the fixed-name file's current content under `versions/` first
(data model introduction). The owner then adds and commits its Review & Approval row, "Environment
record <n>" or "Owner-provided value <n>", with that hash, which the Environment guard and
`validate_tool.py`'s source guard read at HEAD (Approvals, above); every `environment` field names
an environment record by that hash and by the raw SHA-256 of its file as committed, which names it
under `versions/` and in `previous_sha256` (data model §1; REP-083). It has no `--reproduce`: each
mode records an owner's act, which a later run cannot regenerate (introduction; REP-085).

## `scripts/downloads.py`

```text
downloads.py init                                    # the approved entries, from research R19
downloads.py fetched NAME PATH [--pypi-sha256 HEX]   # --pypi-sha256 required for a wheel
downloads.py not-obtained NAME --reason TEXT
```

Run by the agent. It writes the downloads manifest, `$REP/downloads.json`, through
`protocol/evidence.py` (research R19; data model introduction). `init` writes one `approved` entry
per file of research R19's two tables, as research.md holds them at HEAD, with its name, source,
size and licence, and exits 2 once the manifest exists. `fetched` computes the SHA-256 and the size
from the downloaded file itself, read under `-I` from its own directory and never run, refuses a
size that differs from a size R19 gives in bytes and, for a wheel, a SHA-256 that differs from
PyPI's for that file, and writes the entry `fetched` with its SHA-256, the download date and the
local path. `not-obtained` writes `not obtained` with the reason. Each mode refuses, exit 2, writing
nothing, a name that no `approved` entry holds, and keeps the manifest's earlier content under
`versions/` first (data model introduction). An `owner-provided` entry stays the owner's own act,
written by `owner_record.py owner-provided` (above). `tests/test_protocol_004.py` covers each
refusal (REP-076). It has no `--reproduce`: its entries record outside facts, the files as fetched
and the reasons a file was not obtained, which a later run cannot regenerate (introduction;
REP-085).

## `scripts/protocol_change.py`

```text
protocol_change.py check                  # the comparison alone; writes nothing
protocol_change.py create                 # the first entries, from checklist-choices.md
protocol_change.py propose FILE           # one later entry, its fields in FILE
```

The one writer of the protocol change log, `research/004/protocol-changes.jsonl`, through
`protocol/changelog.py` (spec FR-044; data model §18). `create` runs only while the log does not
exist, and exits 2 once it does. `check` reads the lists "Rows that change the protocol" of
checklist-choices.md, in round order, each naming its round's two commits by hash, and compares each
rule's text, in each place its heading names, each place's text delimited as spec FR-044 states,
over each round's pair and over every span from the plan-approval commit outside the pairs; it
prints each place whose text changed, with its commit, the rows of that round listed under its rule
and each place changed by an edit that no row made, and writes nothing. It makes the comparison that
`research/004/place_check.py`, committed for it, standard library only, made before the
tasks approval, reading the named commits with `git show`: that script wrote
`research/004/place-check.json`, which the results beside the lists restate and which the owner
confirmed in the Review & Approval row "Place check", naming its SHA-256 and each place changed by
an edit that no row made, confirmed as an entry of its own or as no change of rule, with the reason
(spec FR-044). A test checks that `check` gives that file's result over its commits. `create` reads
the row "Place check" at HEAD, or the "Place check <k>" with the highest k (Approvals, above), runs
the same comparison first and exits 2, writing nothing, while a place whose text changed has no row
of that round listed under its rule and no such confirmation, while its result up to `compared_to`
differs from the file the row names, or while a place changed after `compared_to`, until the
comparison is made again over the later commits and its file confirmed in "Place check <k>", read
with the highest k (PRO-063). Otherwise it builds one first entry per listed row, with `rules`,
`row`, `granularity` and `place_check`, and one per place confirmed as an entry of its own, with
`rules` at the edit's parent and at its commit, `row` none, `granularity` `commit` with `commit`,
the edit's hash, `reason`, the owner's confirmation naming the commit, and `place_check` for the
pair or span that holds the commit; an edit inside a round's pair is recorded beside that round's
list, and its entry follows the round's row entries; an edit between two rounds is recorded beside
the list of the round before it, as ad2c195's is beside the re-run's, and its entry follows that
round's entries, so that the log keeps the order of the commits (data model §18; PRO-064).
`propose FILE` builds one later entry from FILE, a JSON object holding its fields,
which the agent may write as a proposal. Each refuses, exit 2, appending nothing, an entry, or a
rule of a first entry, without `direction`, a `settled` one without `readings`, and an entry without
`last_record_id` or `results_known`. Each then ends in the approval step, an owner's own act that
the agent never performs (spec FR-044): it prints the SHA-256 of the entry, or of the first entries
together, taken over one canonical JSON array of the first entries in log order, or over the later
entry alone, each entry without its approval field, `approver` whole, and
without `prev_sha256`, both filled once the owner has typed the digits, a hash
of kind `canonical` (data model §1, §18; REP-094), `create` printing also
their number, counted from the lists (PRO-069), and appends nothing unless
standard input is an interactive terminal and the owner types its first 16 hex digits, which
`approver` records as `approval_confirmed`. After the approval step `create` writes the first
entries to a temporary file beside the log's path and renames it to that path once all are written,
so that a writer that dies leaves no partial log, only the lock, which `scripts/clear_lock.py`
removes (PRO-065). Every append takes `data/log-append.lock` and checks the
chain first (Hash-chained logs, above). It writes log entries and no record, and so has no
`--reproduce` mode (spec FR-061). `tests/test_protocol_004.py` covers each refusal.

## `scripts/provenance.py`

```text
provenance.py add FILE                    # one entry, its fields in FILE (data model §14)
provenance.py review FILE                 # one review entry, with `follows`
```

The one writer of the provenance log, `$REP/provenance.jsonl`, through `protocol/provenance.py`
(spec FR-067; data model §14). FILE is a JSON object holding the entry's fields but `seq`,
`prev_sha256` and `date_utc`, which the writer adds. `add` appends an entry for a file, or a section
of one, drafted or repaired with an AI tool, or for a known result this feature writes itself or a
tool's second known result; `review` appends a review entry, with `follows`, the `seq` of the entry
it follows, and the status the review gives, or the review of an evidence record, naming the
record's ID and SHA-256. Each computes the `sha256` and `sha256_kind` of the named file, section or
record as data model §14 states, over the file's bytes, LF-normalized for an existing `text=auto`
file and raw otherwise, a section from its heading line, an ATX heading outside fenced code blocks
as CommonMark reads it, to the line before the next heading of the same or a higher level, or to the
file's end, `section` naming it by its heading's text, preceded, where that text occurs more than
once in the file, by the texts of the headings that enclose it, from the highest level down, joined
by " > " (data model §14; REP-088), and refuses, exit 2, appending nothing, an entry with a
field of its kind missing, a `section` that names no section or more than one
(REP-088) or a `sha256` or kind that differs (REP-079), or a review entry whose
`row` does not read at HEAD, with its `reviewed_sha256`, the decision the entry records, Approved
for `accepted` and Declined for `changes-requested`, or whose `reviewer` names an AI tool or
session, or a review entry while the named file, or, where the row names a chapter by its own
SHA-256, the chapter, does not have at that moment the SHA-256 that the row names for it, while its
`follows` is not the latest entry for that path and section, or while the section's text differs
from the text whose `sha256` that entry holds, so that the status the latest entry gives is that of
the text the reviewer read, a section changed after its last entry getting an `add` entry before its
review, each refusal a case of `tests/test_protocol_004.py` (RAT-081); a review entry
holds `reviewer`, `row`, `reviewed_sha256` and `owner_word`, and the agent
runs `review` only on the owner's explicit word for that entry, quoted with its date in it, as for a
row's approval (spec FR-064, FR-067; data model §14; RAT-077). It writes the owner design review's
review entries after the commit that records that review's approval and before the freeze's step
(1), leaving them in the working tree, which step (1)'s commit holds, so that `design_freeze.py
create` finds them in the provenance log at HEAD (spec FR-043; RAT-082). Right after
the log's creation, before any other entry, `add` writes one entry per file drafted before the log,
the files outside the feature directory that this feature's sessions changed among
them, whole or per section changed, with `drafted_from` and `drafted_to`
from the spec's first commit, 801c6d7, on, and the other fields data model §14 lists for such an
entry (spec FR-067; REP-080, REP-089); a file entered per section changed gets one entry per section
of the deepest heading that holds a changed line, none for a section only because a subsection of it
changed, a section whose heading's text changed keeps one series of entries under its heading as it
stands, and a removed section is entered under the section that held it, with `removed` naming the
removed heading and the commit that removed it (data model §14; REP-095). Every append
takes `data/log-append.lock` and checks the chain first (Hash-chained logs,
above). It writes log entries and no record, and so has no `--reproduce` mode (spec FR-061).
`tests/test_protocol_004.py` covers each refusal.

## `scripts/clear_lock.py`

```text
clear_lock.py LOCK                      # data/heavy-run.lock or data/log-append.lock
```

Run by the owner or at the owner's request. It removes LOCK only when it can show, in the
lock's environment, that no process with the PID and start time the lock holds still runs;
otherwise it exits 2 and removes nothing. It writes a `lock-cleared` record,
`$REP/locks/<record_id>.json`, with the lock's content and, for the heavy-run lock, the
`inconclusive` record of the run that died holding it (data model §1; research R16). While the
protocol change log does not exist, a `lock-cleared` record is one of the two kinds that the guard
"Protocol log" lets `protocol/evidence.py` write, an environment record the other (Protocol
log, above; PRO-071), each with `protocol_seq` and `protocol_line_sha256`
`none`; before the log exists only `data/log-append.lock` can be held, since
every run that takes the heavy-run lock writes evidence, so that a writer of
the logs that died holding it never blocks the log's creation (PRO-065). Like every other write, its
`lock-cleared` record waits until the platform's environment record in force reads Approved at HEAD
(Environment, above), and it exits 2, removing nothing, while the guard refuses the record: a stale
lock found after a Windows or WSL update is cleared once the new record, which needs no lock, is
approved, and before the first environment record no lock can be held, since no
log writer or heavy run starts before it (PRO-068). A `lock-cleared` record
records an event and is not reproduced, so this script has no `--reproduce`
mode (spec FR-061).

## `scripts/check_claims.py`

```text
check_claims.py
```

Runs FR-069's test as written, with its scope, rules, strength rule and allow-list: it checks
README, security.md §1.1 and §15 and the disclaimers, README's status block and security.md's own
blocks, the one that opens it and the one that closes it, each of which must say that PhycoWeb-PRNG,
every model included, must not be used to generate secrets and state no level, claim or bound beyond
the register's (SEC-086), against `protocol/claims.json` and that every hand-written document of
this feature carries the design-form disclaimer, the eight checklists, checklist-choices.md and,
once written, tasks.md among them, README and security.md keeping their own
blocks and carrying no copy of it (spec FR-068; SEC-086), and it scans every
Markdown file under `specs/004-crypto-architecture-v3/` and `reports/004-crypto-architecture-v3/`,
the checklists and checklist-choices.md included, README, security.md, and the comments and
docstrings of the files FR-069 names. A line its rules flag passes only through an allow-list entry
of the register, with its path and text, its reason, its writer and its date, counted from the
commit that adds it, and every run prints each entry added since the last ⛔ gate's approval commit,
which the owner's review at that gate lists (data model §15; SEC-087). Its level rule flags every
name of a level above `claim_level` in every scanned line as a whole word, `claim_level` being, for
each line, the lowest level the register gives the models the line names by ID, and L0 where it
names none, the lines that name a level without stating one for a model standing through the entries
data model §15 lists, and its sample sentences "phyco-v3 is at L2" and "the
design reaches L3" must be flagged and security.md §15's ladder rows must
pass (spec FR-069; SEC-085). It reads the spec's Review & Approval rows "L1
recorded" and "L1 recorded <k>" and those of the FUT-SEC-8 result review and the security-target
review as committed at HEAD (Approvals, above), and a register whose level for `phyco-v3` differs
from the one those rows give is a finding: L1 while the "L1 recorded" row with the highest k reads
Approved and names the highest-k row of each review family, both Approved, and every hash those
review rows name, the chapter's version item by item and the demonstration record, matches the file
at HEAD (SEC-079), and L0 otherwise, with security.md §15's line stating the same level and
`history` holding every L1 that a later row or a change to the reviewed set ended, with its dates,
the rows it rested on and the version reviewed. An `in_progress` that names L2
while no counted trail-bound record exists at HEAD, names a start date other
than the first such record's, or reads `none` once one exists is a finding
too (SEC-080). The agent writes the register's change in a commit of its
own right after the owner's commit that changes those rows, so that at the owner's commit the check
reports the register behind the rows (data model §15); it writes the return to L0 that a
change to a reviewed file brings in the commit that makes the change, or
right after an owner's commit that makes it, and `in_progress` in the commit that writes the first
counted trail-bound record (SEC-079, SEC-080). Inside the window in which the agent commits no file
of this feature, from the first commit that records an owner design review's approval to the
feature's end (spec FR-043), `protocol/claims.json` and security.md among those files, the agent
writes each of these changes in the working tree, once the owner has set the row or
made the change there, and the owner's commit holds it, so that at every
commit of the window the register gives the rows' level, and `design_freeze.py
create` exits 2 while this check reports a finding at HEAD (SEC-084). Exit 1
on any finding (SC-018). `tests/test_claims.py` runs it, with a register above, below and at the
rows' level, a `history` missing a lapsed L1, a reviewed file changed at HEAD with the register at
L1 and at L0, and an `in_progress` naming L2 with no counted trail-bound record, naming
another start date, or reading `none` once one exists among its cases (SEC-079,
SEC-080). It writes no record and runs as a test, so FR-061's reproduction
test leaves it out (spec FR-061).
