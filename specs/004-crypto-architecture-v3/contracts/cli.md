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

## Guards shared by every script

- **Environment**: `protocol/evidence.py` checks at start the running environment against the
  platform's environment record in force (research R1) as a whole: Python, every package and version
  of `pip freeze` (one added, upgraded or removed), gcc and make in WSL, and the Windows build or
  the WSL distribution and kernel. Any difference exits 2, naming it, a Windows or WSL update
  included; the owner then writes a new environment record with `scripts/owner_record.py
  environment` and approves it, with R1 updated first when a pinned version changes, and each later
  record cites the record in force (data model §1). It also exits 2 unless
  the record in force has its Review & Approval row, "Environment record
  <n>", Approved at HEAD with its SHA-256 (Approvals, below). A new record is
  written only when its Python and pinned packages match R1 and the pins of `requirements.txt` for
  that platform. `scripts/recheck_004.py` alone is exempt: it recomputes verdicts from committed
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
- **Order of sizes**: evidence of a kind at 8×8 or 16×16 exits 2 unless that kind's run for the
  candidate at the next smaller claimable size has finished without making it ineligible
  (research R7). The guard counts evidence records only: a `--project` probe at a larger size writes
  nothing but its `projection` record, which is not evidence, so this guard never refuses it, and
  the probes at 8×8 and 16×16 that a 4×4 run's projection needs run before that run (quickstart E7).
- **Approvals**: every guard that reads the spec's Review & Approval table (Environment, above;
  Order of US1, below; `round_rule.py --select`; `design_freeze.py create`;
  `repair_log.py`; `validate_tool.py`'s source guard; `check_claims.py`; the test of the second
  transcription's provenance) reads it as committed at HEAD, never the working tree,
  and exits 2 while the working tree's table differs from HEAD's. The rows that open a guard are set
  to Approved and committed by the owner (the note under that table), so an uncommitted row opens
  none, and the owner's review at each ⛔ gate lists the approval commits since the last gate. A
  review held again is a numbered row, "FUT-SEC-8 result review <k>", "Security-target review <k>"
  or "Owner design review <k>" (k = 2, 3, …), and a guard that reads such a family reads its row
  with the highest k, which must name by path and SHA-256 what the run cites: the latest
  demonstration record (Order of US1), or the chapter's version and the design document's version
  with the latest selection record (`design_freeze.py create`). A guard opens on Approved alone,
  except that `design_freeze.py create` also takes done or "not arranged" on the external review's
  row and `round_rule.py --select` takes "Not needed" on the "D4 tie" row (data model §17).
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
  kind; until then its results are `not evaluated`. A re-validated version of a tool in the fixed
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
  the candidate log, or by projection until they exist. Every heavy run that charges no candidate, a
  validation or re-validation on published values, a heavy reproduction or FR-053's test with two
  worker counts, projects first against research R7's feature-wide 66 h row and exits 2, writing
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
fut_sec8.py --binary fast/build/seed_search --out-dir $REP/fut-sec-8 [--repeat-after-defect ID]
fut_sec8.py --verify RECORD
fut_sec8.py --reproduce RECORD --binary fast/build/seed_search
```

Takes the targets from `protocol.seedsets.load("dev", allow=("dev",))[:3]`, computes the
observations with `phycoweb/model_v2.py`, runs the vector check, then one sweep per target,
separates any extra three-word match with the fourth word, and writes a demonstration record,
`fut-sec-8/<record_id>.json` (data model §4). A second run exits 2 unless `--repeat-after-defect`
names a recorded tool defect that no earlier record names (spec Edge Cases); the repeat writes
beside the first, holding `supersedes`, the earlier record's ID, and `defect`, the defect's. Exit 1
if a target is not recovered.

Neither of the other two modes is a demonstration attempt, and each takes a demonstration record by
its ID, so that every earlier record stays reproducible:

- `--verify RECORD` re-checks every listed three-word match and every recovered seed with
  `model_v2`, in seconds, with no sweep. Exit 1 on any disagreement.
- `--reproduce RECORD` is allowed only after the FUT-SEC-8 result review, and exits 2 before
  it. It re-runs the sweep as a heavy run and writes a `reproduction` record
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
`sparkle-box`, or a structural tool's known result of research R13) and writes a validation
record (data model §7). Exit 1 if not re-found. A published value needs its source recorded, an
entry of `$REP/downloads.json` (research R19): a `fetched` file's entry with the paper's table and
value, or the `owner-provided` entry of a value the owner provides with its source, written by
`scripts/owner_record.py owner-provided`, whose Review & Approval row "Owner-provided value <n>"
reads Approved at HEAD (Approvals, above); any other entry, or none, exits 2. A
tool's first validation records its second known result, fixed with its source
in the provenance log before that validation, or the statement that it has none (data model §7,
§14); after a failed validation, the re-validation re-finds the second as well as the first, and for
a tool with none it exits 2, leaving the tool unvalidated. `--reproduce RECORD` runs that record's
validation again, as the introduction describes, and compares the fields data model §1 lists for a
validation.

For the bias test's validation, `validate_tool.py` draws at each size the 100 synthetic sets of
class 5, j = 0…99, and the 100 of the second family, j = 100…199, which plant their bit at position
⌊(j − 100)·S/100⌋, from numpy's `Generator(PCG64(s))`, with the seeds s from
`protocol.devinputs_v3.load('dev', 'synthetic', allow=('dev',), count=200,
n=n)` (data model §2, §7); each family must fire in 82 to 97 of its 100 sets.
The sets are local-only, under `data/local/004/<record_id>/`, and regenerated by this deterministic
command; the record commits each set's SHA-256, the numpy version and a per-set summary, the planted
bit's count and every fired bit, so a fresh clone recomputes both 82-to-97 verdicts from committed
files and a regeneration checks every count (data model §7). No set is ever replaced: a later draw,
`--reproduce` included, must reproduce every hash in an environment with that numpy version, and a
draw that differs is reported and counts for nothing. After an approved numpy upgrade the old record
stays the validation in the old environment, and a new validation, a new record, decides in the new
one: outside 82 to 97 the tool is unvalidated there, its results `not evaluated`, until a defect is
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
first and runs only if every entered candidate's 12 h row can hold its hours, since each row is
charged them (Budget), writes its record under `$REP/controls/`, with `model_id` and `variant_id`
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
`tie.json` once, when R at 4×4 exists for both representatives or one of them is ineligible; before
that, or if `tie.json` exists, it exits 2. `--choose`, run by the owner after `tie.json` exists,
prints `tie.json`'s SHA-256 and exits 2 unless standard input is an interactive terminal and the
owner types its first 16 hex digits; it writes `d4/tie-choice.json` with the choice, who, when,
`seen_sha256` and `choice_confirmed`, the digits typed, and exits 2 if that hash differs from
`tie.json`'s, if no tie exists or if a choice exists; `tie.json` is never rewritten. Running
`--choose` is the owner's own act, which the agent never performs (spec FR-043, FR-044).

## `scripts/round_rule.py`

```text
round_rule.py --candidate ID           # writes candidates/<ID>/round-rule.json
round_rule.py --select                 # writes $REP/freeze/selection.json, later selection-<k>.json
round_rule.py --close                  # writes the candidate log's set-closed entry
round_rule.py --choose ID --seen SHA256 --by NAME   # writes the latest selection's tie choice
round_rule.py --reproduce RECORD       # a round-rule or selection record (introduction)
```

R = max(2·R_dist, R_bound + 2, 2·max(R_f, R_b)) per claimable size, every input cited by record
ID. `--close` writes the candidate log's `set-closed` entry once every candidate has a final
decision (`withdrawn`, `rejected` or `ineligible`, or, for an eligible candidate, its round-rule
record at every claimable size) and no `replacement` entry of the log is `pending`
(data model §3), and exits 2 otherwise. `--select` exits 2 before that entry,
and after a D4 tie until the spec's "D4 tie" row reads Approved at HEAD with the SHA-256 of
`d4/tie-choice.json` (Approvals, above); it applies eligibility, the fallback to the other family
and the stop rule; exit 1 if the outcome is a stop. Eligibility is decided for every candidate from
its own records (data model §9): FR-018's folding rule, longest link, food nodes and tree figures
from the operation list and its `parameters` entry; FR-020's cycles per call and FR-026's figures
from its `cost` records per size, written by `research/004/tools/costmodel.py` from the operation
list, P and R; FR-022's bounds from its bound records; FR-023's statement on the streams and
FR-024's ranking report from its log entries; FR-025's stages, chains per phase and key path from
the operation list's declarations, checked by code; FR-027's semantics from the
operation list's declarations; FR-030's mapping from its `mapping` log entry.
FR-025's interface formats, call sequence and zeroization rules are the mode's,
decided once in the mode chapter. A missing item fails eligibility, and so does a `reproduction`
record of one of the candidate's records that differs on a field that enters a verdict, until a
re-run after a recorded tool defect resolves it (data model §1). Any change before the freeze that
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
with the fields of data model §1 (FR-061) and each written file's path and SHA-256 (data model §11);
`--check` does not compare the sidecar. `gen_constants_v3.py` also writes each constant table
as `vectors/phyco-v3/constants_n<n>_w<w>.json`. `--check` regenerates in memory, compares every
generated file byte for byte with the committed one and writes a `generator-check` record under
`$REP/generator-checks/` with the fields of data model §1 (FR-061), each generated file's path and
SHA-256 and the verdict `match` or `differs`; it exits 1 on any byte difference. SC-009's evidence
is each generator's pair of such records, one per platform, which quickstart M1 to M3 and the final
report cite. The sidecar is frozen with the vectors (data model §13), as the record of the runs that
produced them: after the freeze a generator runs only with `--check` or `--reproduce`, which write
their records under `$REP` and never to the sidecar, and writing over a frozen file exits 2.
`--reproduce RECORD` (introduction), on each generator, runs the command of that `generator-run`
record again and compares every file it generates, in memory, with the SHA-256 the record holds
rather than with the file on disk, so that a later regeneration changes nothing, or, for a
`generator-check` record, runs that `--check` again and compares its hashes and verdict; it writes
no `.py` or `.hex` file and adds nothing to the sidecar, its `reproduction` record, under
`$REP/reproductions/<record_id>/<n>/`, holding each file's path, SHA-256 and outcome.

They run in three steps, each generator's `--check` passing before the next step (data model §11):
(1) `gen_constants_v3.py`; (2) `gen_vectors_v3.py`, which writes the vectors through `pi` and
`ResearchDuplex`, which runs no self-test, and also writes `phycoweb/selftest_v3.py`, the
self-test's inputs and expected output, copied from the vectors, so its `--check` covers that file
too; (3) `Generator` imports `phycoweb.selftest_v3` inside its constructor only and runs its
self-test from it, so step (2) imports the model before that module exists (model contract, Module
rules). Tests check that `Generator` reproduces the vectors and that `selftest_v3` equals them, and
the freeze hashes `selftest_v3.py` with the vectors (data model §13).

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
scripts, both freeze files, every evidence record behind R by ID and by SHA-256, and the last `seq`
and line SHA-256 of the candidate log, the provenance log and the protocol change log. The freeze's
code is `protocol/design_freeze.py`, with create, approve and validate as functions, and this script
is the command that calls it, as the other scripts call `protocol/evidence.py`; the record hashes
both files (data model §13).

`create` reads the spec's Review & Approval table at HEAD (Approvals, above) and exits 2 if the
security-target review's or the owner design review's row, the one with the highest k where
the review has been held again, is not Approved or does not review what the
record freezes, by path and SHA-256: the chapter's version, and the design
document's version with the latest selection record; if the external review row is
neither done nor "not arranged", if the latest selection record has a tie
and its row, "Selection tie" or "Selection tie <k>", does not read Approved
with the SHA-256 of its choice record, if a theorem the mode chapter uses
is not `verified` in `limits.json` or a precondition of it is not marked met there, naming the
theorem, those marks being read as `unverified` while the security-target review row does not read
Approved (research R10), or if `git_dirty` is true. `create` stores `draft_sha256`, the
SHA-256 of the record's canonical JSON without that field and the approval fields. `approve`, run by
the owner, prints `draft_sha256` and exits 2 unless standard input is an interactive terminal and
the owner types its first 16 hex digits; it then changes `status` from `draft` to `approved`, adds
`approved_by`, `approved_utc`, `approval_wording` and `approval_confirmed`, and changes nothing
else. Steps (1), (3) and (4) are the owner's own acts, which the agent never performs (FR-043).
`validate` recomputes `draft_sha256` and every hash
and checks the format rules; it exits 1 if anything but the approval fields changed or a hash does
not match, and 2 while `status` is `draft` (data model §13).

## `scripts/recheck_004.py`

```text
recheck_004.py [--kind KIND]
recheck_004.py --reproduce RECORD
```

Recomputes every verdict of the feature from saved outputs (FR-065) and compares it with the
recorded one. Exit 1 on any disagreement, with each listed. Every verdict is recomputable on a
fresh clone from committed files, so it works from the committed per-round summaries, for
example R_f from the per-round flag "every output bit depends on every input bit". Where
local-only outputs are present, it also re-derives each committed summary from them. Its output
lists both checks per kind, and it verifies the inventory of superseded operation lists
(data model §3). With `--reproduce RECORD` it runs a recorded re-check again, as the introduction
describes, comparing its verdicts and counts (data model §1); like the re-check, it may run in any
environment.

It recomputes each verdict under the rules in force at the protocol change-log entry its record
cites and, where a later stricter change applies (FR-044), also under the current rules; both are
listed, and a disagreement in either is reported. A cited file kept under a fixed name is resolved
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
cite corroborate them, and the final report states the repair (research R16).

## `scripts/owner_record.py`

```text
owner_record.py environment --platform windows|wsl --by NAME   # $REP/environment-<platform>.json
owner_record.py owner-provided --known KNOWN_ID --value TEXT --source TEXT --words TEXT --by NAME
```

Run by the owner only: each mode is an owner's own act, outside the standing authorization for local
commits, which the agent never performs (spec FR-044). `environment` records the running environment
as research R1 lists it, only when its Python and pinned packages match R1 and the pins of
`requirements.txt` for that platform; `owner-provided` adds an entry to `$REP/downloads.json` with
the owner's words, the source the owner names, the date and the value's SHA-256 (research R19). Each
mode prints the SHA-256 of what it writes, taken over its canonical JSON without the approval
fields, and exits 2, writing nothing, unless standard input is an interactive terminal and the owner
types its first 16 hex digits; it then writes the record or entry with `approved_by`, `approved_utc`
and `approval_confirmed`, keeping the fixed-name file's current content under `versions/` first
(data model introduction). The owner then adds and commits its Review & Approval row, "Environment
record <n>" or "Owner-provided value <n>", with that SHA-256, which the Environment guard and
`validate_tool.py`'s source guard read at HEAD (Approvals, above).

## `scripts/clear_lock.py`

```text
clear_lock.py LOCK                      # data/heavy-run.lock or data/log-append.lock
```

Run by the owner or at the owner's request. It removes LOCK only when it can show, in the
lock's environment, that no process with the PID and start time the lock holds still runs;
otherwise it exits 2 and removes nothing. It writes a `lock-cleared` record,
`$REP/locks/<record_id>.json`, with the lock's content and, for the heavy-run lock, the
`inconclusive` record of the run that died holding it (data model §1; research R16). A
`lock-cleared` record records an event and is not reproduced, so this script has no `--reproduce`
mode (spec FR-061).

## `scripts/check_claims.py`

```text
check_claims.py
```

Runs FR-069's test as written, with its scope, rules, strength rule and allow-list: it checks
README, security.md §1.1 and §15 and the disclaimers against `protocol/claims.json` and that every
hand-written document of this feature carries the design-form disclaimer, the eight checklists,
checklist-choices.md and, once written, tasks.md among them, and it scans every
Markdown file under `specs/004-crypto-architecture-v3/` and `reports/004-crypto-architecture-v3/`,
the checklists and checklist-choices.md included, README, security.md, and the comments and
docstrings of the files FR-069 names. A line its rules flag passes only through an allow-list entry
of the register, with its reason (data model §15). It reads the spec's Review & Approval row "L1
recorded" as committed at HEAD (Approvals, above), and a register that gives `phyco-v3` a level
above L0 while that row does not read Approved is a finding. Exit 1 on any finding (SC-018).
`tests/test_claims.py` runs it. It writes no record and runs as a test, so FR-061's reproduction
test leaves it out (spec FR-061).
