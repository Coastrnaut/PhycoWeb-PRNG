# Data Model: Cryptographic Architecture and phyco-v3 Design

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

All records are JSON (UTF-8, LF line endings, sorted keys), written by one module,
`protocol/evidence.py`. Paths are under `reports/004-crypto-architecture-v3/` unless stated, and
files committed there are limited to `.json`, `.jsonl`, `.md`, `.csv`, `.txt` and `.gz`;
`protocol/evidence.py` refuses any other suffix there (research R16, R18). A record is never
overwritten: a repeat run writes a new record with a new identifier, and the old one stays.

**Format rules** for every record and generated file (FR-036, FR-053), so that another
implementation can write byte-identical files:

- Text is UTF-8 without a byte-order mark, with LF line endings only and a final newline.
  Scripts write with `encoding="utf-8"` and `newline="\n"`, and no hashed file is written by
  Windows PowerShell 5.1, whose `Out-File -Encoding utf8` adds a byte-order mark.
- JSON has sorted keys and `ensure_ascii=False`, with two-space indentation in a `.json` file
  and one object per line in a `.jsonl` log. Rationals are "p/q" strings. Floats appear only in
  reported statistics and are written with `repr`.
- Hex words of vectors and states are upper case and zero-padded to the word's width, with lanes in
  the design document's order. Every digest is written as 64 lower-case hex digits, as the existing
  records already are. A vector file's header is `# key=value` fields in a fixed order, separated by
  single spaces (section 11).
- A `.gz` file is written by `gzip.compress(data, compresslevel=9, mtime=0)`, so its header holds no
  file name and a zero time. Its raw hash is over the compressed bytes, and its output entry also
  holds `uncompressed_sha256`, the SHA-256 of its content, which a reproduction compares (research
  R16).
- `lf-normalized` content is the file's bytes with each CR LF pair replaced by LF, as Git
  normalizes, a lone CR kept; it is never computed from a file read in text mode, whose universal
  newlines also turn a lone CR into LF.
- Every list is sorted by a stated key: fired bits by round count, direction, set and bit;
  matches by candidate value; IDs lexicographically; symmetries in a stated enumeration order.
  Nothing depends on set iteration, hash randomization, thread completion or worker count.

## 1. Common fields (every evidence record; FR-061, security.md §17.2)

| Field | Type | Rule |
|-------|------|------|
| `record_id` | str | `<kind>-<UTC yyyymmddThhmmssZ>-<8 hex>`; unique; part of the file name |
| `kind` | str | one of the kinds of sections 4–11, `projection` or `lock-cleared` (below) |
| `created_utc` | str | ISO 8601, seconds |
| `model_id`, `variant_id` | str | `phyco-v2` for US1 and for tool validation on it; otherwise a candidate or `phyco-v3` variant ID (research R14) |
| `design_version`, `design_sha256` | str | the design document's version and hash; `none` before it exists |
| `spec_sha256` | hex | SHA-256 of `spec.md` at run time; the first record that cites a hash stores a copy of that spec as `spec-versions/<sha256>.md`, committed with the records (research R16) |
| `git_head`, `git_dirty` | str, bool | as in the feature-002 and feature-003 records |
| `code_sha256` | object | path → SHA-256 of every code file the run used: the script, the `protocol/` modules, the candidate's operation list, `research/004/ir.py` and its tools, a C source and its binary. A self-written tool's version is its hash (FR-039). With `git_dirty` often true, these hashes, not `git_head`, identify the code |
| `versions` | object | Python, numpy, scipy, gcc, and every tool used, with its version and licence |
| `environment` | object | path and SHA-256 of the platform's environment record, `environment-windows.json` or `environment-wsl.json` (research R1) |
| `platform` | object | operating system, CPU, logical CPUs, RAM |
| `parallelism` | object | worker and thread counts, and `PYTHONHASHSEED` if set |
| `command`, `config` | str, object | the interpreter by its full path (the Windows Python, or `~/.venvs/phycoweb/bin/python` in WSL), then the script and its arguments with paths relative to the repository root; the working directory and the repository root; every parameter |
| `inputs` | object | namespace (`dev` or `control`; for US1 the feature-002 `dev` set), kind, index range, fingerprint (R3) |
| `outputs` | list | `{path, sha256, bytes, committed}`, and `uncompressed_sha256` for a `.gz` file; `committed` false for local-only files (R16); a committed file has one of the suffixes of the introduction |
| `exit_status`, `assertions` | int, list | every assertion with its outcome |
| `status` | str | `pass`, `fail`, `inconclusive`, `not evaluated` or `blocked` (security.md §16.3), computed by code (FR-065) |
| `classification` | str | one of the four classes of security.md §9.1 (FR-060) |
| `analyst`, `reviewer`, `review_status` | str | the AI agent and model, or a person; `reviewer` stays `pending` until a review is recorded |
| `limitations` | list[str] | known limitations, and the scope of any negative result |
| `heavy_run` | bool | true if the run held the heavy-run lock (FR-045) |
| `disclaimer` | str | `protocol.disclaimer.DESIGN_DISCLAIMER`, verbatim (FR-068) |

Statistical records (section 5, `frequency`, `avalanche` and `control`) also hold the items of
security.md §11.6: `sample_size`, `test_parameters`, `raw_counts` (path and SHA-256),
`p_values` (path and SHA-256), each JSON or gzip-compressed JSON, never `.npy`, `failure_locations`
(every fired bit with its round count, direction and input or difference set) and
`exclusions_and_reruns` (each citing the recorded tool defect, one of the kinds of research R7, with
its evidence; empty unless a tool defect is recorded).

- **Hashes.** Every SHA-256 a record holds is recorded beside its kind, `raw` or
  `lf-normalized` (research R16).
- **Every run writes a record.** A run started on a candidate or a variant writes a record even
  if aborted (`inconclusive` or `blocked`, with the reason). A run later found hit by a tool
  defect keeps its record, with the defect noted.
  A heavy run that died holding its lock gets that `inconclusive` record when
  `scripts/clear_lock.py` clears the lock, which also writes a `lock-cleared` record under `locks/`
  with the lock's content (research R16).
- **Projection records.** A `projection` record (research R7) is written for every 60 s
  projection and every timing probe: the run it projects and its budget row, its inputs (the
  first inputs of that run), the measured speed and the projected hours. Its outputs other than
  timing are discarded unread, and the record says so. Its time counts against the row of the
  run it projects.
  A projection record is not evidence: the order of sizes counts evidence records only (research
  R7), so a probe at a larger size runs before the run it projects.
- **Reproduction.** A reproduction of a record compares these fields with the original and reports
  every other field only: `kind`, `model_id`, `variant_id`, `design_sha256`, each source file's
  entry in `code_sha256`, `inputs`, each output's `sha256` and `bytes` (not its path),
  `exit_status`, `assertions`, `status`, `classification`, and the fields of its kind. Deterministic
  kinds (vectors, constants, dependency matrices, counts, digests) thus match byte for byte, and
  searches and solver runs by their values and verdicts. A different source hash makes it a new run,
  not a reproduction, and a binary's hash is reported only. Two kinds of output are compared by
  content instead: a `p_values` file, whose p-values must agree within a relative tolerance of 10⁻⁶
  and never decide a verdict, the reproduction listing any outside it; and a `.gz` file, by its
  `uncompressed_sha256`. The verdict is recomputed under the spec version the original cites
  (`spec-versions/<sha256>.md`), so a later spec change cannot alter it, and the environment is
  either of research R1's two, as recorded.

## 2. Development inputs (`protocol/devinputs_v3.py`; FR-040, R3)

| Constant or function | Rule |
|----------------------|------|
| `PREFIX` | `phycoweb-004/` |
| `NAMESPACES` | `dev`, `control`; nothing else is accepted |
| `key(i)`, `nonce(i)`, `pers(i, m)`, `reseed(i)` | 32, 16, min(m, 32) and 32 bytes from SHA-256 of `phycoweb-004/<ns>/<kind>/<i>` |
| `state(n, w, i)` | b = 2w·n² bits from the digests of `phycoweb-004/<ns>/state/n<n>w<w>/<i>/<j>`, j = 0, 1, …, read into lanes as R3 states |
| `synthetic_seed(n, j)` | the first 16 bytes of SHA-256 of `phycoweb-004/dev/synthetic/n<n>/<j>`, read as a big-endian integer: the seed of synthetic set j at size n (class 5 below) |
| `FINGERPRINTS` | per namespace and kind, and per (n, w) for `state`: SHA-256 of the hex values for i = 0…99, one per line, LF |
| `load(ns, kind, allow, ...)` | checks the fingerprint, refuses a namespace not in `allow` and any index outside the use's declared range i = 0…N − 1 (`PermissionError`; scripts exit 2) |

The empty personalization string is a named input of its own. Indices are decimal without
leading zeros. The module imports only `hashlib`. A keyed reduced variant of capacity c takes the
first c/8 bytes of `key(i)` and the first c/16 bytes of `nonce(i)` (R3, R14).

Every use takes its inputs from this module: the vectors (keys and nonces 0 and 1), the
constructed states from development keys, the D4 scoring, the tool validation and every test.
`control` serves only uniform controls, and `dev` is never a control. Each evidence kind's
namespace is fixed in code, not chosen on the command line, and the loader refuses `control`
for any kind but a control.

**Constructed inputs**, the closed class beside the derivation, each fixed by a public rule
before first use (research R3; FR-040). A constructed input takes its index from its rule, and
no value or index is picked after any output is seen.

| Class | Inputs | Rule |
|-------|--------|------|
| 1 | fixed patterns | all-zero, all-one, alternating, counting (FR-058, R8); the single-bit keys and nonces e_i for every i |
| 2 | edge states | the design document's list (FR-054) |
| 3 | derived from development inputs | the avalanche flips x ⊕ e_j, the key and nonce bit flips and the word rotations, for every j, bit and k the rule names (R4) |
| 4 | feature 002's `dev` seeds | for FUT-SEC-8 only (R2), the one external development set |
| 5 | synthetic counts | for the bias test's validation only (R4): set j = 0…99 at each size from numpy's `Generator(PCG64(synthetic_seed(n, j)))`; one `binomial(N, 1/2)` count per tested bit, in the test's bit order, except the planted bit at position j mod S, drawn as `binomial(N, 1/2 + δ)` at that size's δ (0.0030, 0.0031 or 0.0033); `validate_tool.py` draws the counts, and the validation record holds the numpy version and each set's SHA-256 (section 7) |

## 3. Candidate log (`research/004/candidates.jsonl`; FR-041, SC-011)

One JSON object per line, append-only, each entry chained to the one before it. Every append
takes `data/log-append.lock` and checks the chain first (R16).

| Field | Rule |
|-------|------|
| `seq` | 0, 1, 2, … with no gaps |
| `prev_sha256` | SHA-256 of the previous line's UTF-8 bytes as stored, its final LF included, as 64 lower-case hex digits; 64 zeros for `seq` 0 |
| `candidate_id` | `cand-A1` to `cand-A3`, `cand-B1` to `cand-B3`; a candidate counts towards the stop rule from its first entry, `proposed`, whatever happens after, and a fourth `proposed` entry of a family is refused |
| `family` | `ARX` or `Boolean` (D4) |
| `event` | `proposed`, `entered-d4`, `scored`, `evidence`, `decision`, `correction`, `repair` |
| `oplist_sha256` | hash of the candidate's operation-list module (R11). The `proposed` entry with this hash comes before any tool run, and every tool refuses an operation list whose hash has no `proposed` or `correction` entry (exit 2) |
| `parameters` | round structure, nonlinear component, rotation and constant rules, generics; the instance of the constant rule (polynomial, seed, reading order, distinct streams per call type or not; R15); the rotation search's space of amounts, ranking measure, rounds, width and tie order (R15); and the reduced variants used as evidence (widths, sizes, round counts, capacities); and P, the number of phases in one round of the operation list at each size (FR-025). All are logged before the candidate's first tool run; a variant added later is logged with its reason before its first run |
| `evidence` | the IDs of every record of the candidate, used or not, as security.md §11.3's "report everything" asks |
| `budget_used_h` | `{trails, structural, statistics}` with the caps of R7; each heavy run's projected and used hours, measured speed and engine code hash. A budget lowered below the hours already used leaves zero hours: the results so far stand, and no further run of that row starts (R7) |
| `decision`, `reason` | `eligible`, `ineligible`, `rejected`, `withdrawn`, `selected` or `not selected`, with the reason (below) |
| `variant_map` | on the `selected` entry: the map from `cand-…/n…-w…-R…-c…` to `phyco-v3/…`, with the operation list's SHA-256; the model's tests check that `phyco-v3` reproduces the candidate's outputs through it |
| `date_utc` | ISO 8601 |

An entry is never edited or deleted; a correction is a new entry that cites the `seq` it
corrects. `cand-A1` is the long-trail ARX-box design (FR-022).

- **Decisions.** `rejected` and `ineligible` are given only for the rules' reasons: a failed
  inverse or bijectivity test, a failed eligibility item (FR-018 to FR-031, FR-037, R_bound
  not established, inconclusive evidence) or a spent budget. A candidate may be `withdrawn`
  before its first tool run, for any recorded reason, and it still counts towards the stop
  rule. The log writer refuses any other decision.
- **New candidate or variant.** A change makes a new candidate if it touches the operation
  list's structure: the nonlinear component, the round structure (its operations, their forms
  or order), the colour schedule, or the rule that generates the constants or the rotation
  amounts. It is a variant or fix, logged under its candidate, if it changes only values that
  the candidate's logged rules derive (w, n, R, c), or corrects a value to what those rules
  give. When in doubt, it is a new candidate (stop rule).
- **Superseded operation lists.** Before an operation list changes, its version is copied
  unchanged to `research/004/candidates/<id>/superseded/<sha256>.py`, and the committed
  inventory `research/004/candidates/superseded.json` lists every hash and path, so every
  `oplist_sha256` in the log stays checkable. The re-check verifies the inventory.
- **Repair.** A broken chain is repaired only with the owner's go-ahead, the Approved row "Log
  repair <n>" of the spec's Review & Approval table, which `repair_log.py --approval` names (R16).
  The broken file is kept unchanged with its SHA-256, and `scripts/repair_log.py` appends a `repair`
  entry with the break's position, its cause and what was restored. Entries after the break count
  only where the records they cite corroborate them, and the final report states the repair
  (R16).

```text
proposed ─► entered-d4 ─► scored ─┐       (only candidates entered before the D4 choice)
   │                              ▼
   ├────────────────────────► analysed ─► eligible ─► selected ─► frozen
   │                              │           └─────► not selected
   │                              └─► ineligible or rejected (reason recorded; stays in the log)
   └─► withdrawn (before the first tool run; counts towards the stop rule)
```

## 4. Demonstration record (`fut-sec-8/demonstration.json`; FR-001 to FR-003)

| Field | Rule |
|-------|------|
| `targets` | the first three seeds of the feature-002 `dev` set, from `protocol.seedsets.load("dev", allow=("dev",))` |
| `revealed` | per target, (s₀, s₁) |
| `observed` | per target, the first three output words after the 256-step warm-up, with their positions (T1 knows them) |
| `tool` | SHA-256 of `fast/seed_search.c` and of the binary (also in `code_sha256`); compiler, flags, threads |
| `vector_check` | per golden file: 10,000 words compared, mismatches; must be 0 before the sweep |
| `matches` | per target, after one, two and three words, beside the expected numbers (about 1, 2⁻³² and 2⁻⁶⁴). The one-word false-match count is compared per target with a Poisson distribution of mean (2³² − 1)/2³², two-sided at level 0.01, and with the three targets pooled; any false match after two or three words is reported as a deviation. A disagreement is a finding (FR-060), never a reason to sweep again |
| `assumption` | each candidate's output words are uniform and independent of the target's; `phyco-v2`'s biases (S12, S14) could make false matches more frequent, so a count above the baseline is an observation about `phyco-v2` and does not change the success criterion |
| `listed` | every (s₂, s₃) that matches three words, sorted by candidate value; any extra one separated by the fourth word |
| `recovered` | per target: whether the target is among the three-word matches |
| `cost` | steps per candidate, total steps and seconds, steps per second; extrapolation to 2⁶⁴ seeds |
| `model_sha256` | `1260142d…` for `phycoweb/model_v2.py`, checked |
| `report` | the nine items of security.md §12.4, with T1 as the attacker |

The record is the search tool's validation record (security.md §12.5), and security.md's
best-attack register row for exhaustive seed search cites it (FR-003).

A `fut-sec-8-reproduction` record (`fut-sec-8/reproduction-<record_id>.json`) is written only
by `fut_sec8.py --reproduce`, after the FUT-SEC-8 result review. It holds the same fields and
is compared field by field with the demonstration record, under section 1's comparison rule.
It is not a demonstration attempt: it can neither replace the demonstration record nor change
the review, and a difference is a finding. `fut_sec8.py --verify` re-checks every listed match
and every recovered seed with `model_v2`, with no sweep.

## 5. Structural and statistical evidence (`candidates/<id>/<kind>-<record_id>.json`)

| Kind | Fields beyond section 1 | Verdict computed by code |
|------|-------------------------|--------------------------|
| `inverse` | sizes and variants; the 16 vector inputs and 2¹⁰ test states; both directions | `pass` if 0 mismatches |
| `bijectivity` | variant 2×2, w = 4; 2³² inputs; ones in the output bitmap; bitmap SHA-256 | `pass` if 2³² distinct outputs |
| `dependency` | per round and direction, the bit pairs without dependency; R_f, R_b; per-round summaries committed, full matrices local (R16) | R_f and R_b reported |
| `frequency` | two input sets of N = 2²⁰ (key i with nonce i; key 0 with nonce i), S = 4b, threshold 0.005/S; per set, round count and direction the smallest p-value and the fired bits; the critical-count table it used (path and SHA-256) | fires or not, by comparing each count with its integer critical values (R4); raises R_dist |
| `avalanche` | N_a = 2¹³; the flip set F, the 384 key and nonce bits flipped in instantiation states (forward only) and the rotation amounts 1…w − 1; S_A = (2·\|F\| + 384 + 2(w − 1))·b, threshold 0.005/(128·S_A); as for `frequency`; the `dependency` record it is cross-checked against, with every disagreement | fires or not; raises R_dist; any disagreement is a tool defect and makes the record `inconclusive` |
| `control` | the test it controls, its counts, its inputs (R3's `control` states, taken as R4 states), whether it fired; a re-run after a tool defect runs its control again first, with the same counts | if it fired, that size's bias evidence is `inconclusive` |
| `symmetry` | patterns and symmetries checked, in the stated enumeration order; symmetries that fix a pattern; the relations checked between the constants of one call (R13) | `pass` if none |
| `invariant` | forms and differences checked; any kept on every test state; per form and round count, the count of test states on which it holds against its chance rate (R13) | `pass` if none; a form above its chance rate by the binomial test of R13 raises R_dist |

- **Exact verdicts.** The critical-count table, `research/004/tools/critical_counts.json`,
  holds per (N, S) and (N_a, S_A) the integer critical counts derived by exact integer
  arithmetic over the binomial distribution (R4). It is committed, and scipy's p-values are
  reported only: a reproduction compares them within a relative tolerance of 10⁻⁶, and counts,
  critical counts and verdicts byte for byte (section 1).
- **Validation cited.** Every counted record holds `validation`, the ID and SHA-256 of the
  validation record of the tool's exact hash, whose `created_utc` is earlier (FR-039; SC-007).
- **Unvalidated tools.** A trail or distinguisher found by a tool not yet validated is recorded
  as an unverified hypothesis (FR-060), with `status` `blocked`, and it blocks the candidate's
  eligibility until a validated tool, or direct evaluation of the trail with the validated
  exact models, settles it. If confirmed, it raises R_dist. A possible weakness can only raise
  R or block, never vanish.

## 6. Trail-bound record (`candidates/<id>/bound-<record_id>.json`; FR-038)

| Field | Rule |
|-------|------|
| `bound_kind` | `differential` (trail probability) or `linear` (squared trail correlation) |
| `rounds`, `width`, `size` | the variant it bounds |
| `bound` | a rational as a "p/q" string, and its −log₂. A floating-point solver value becomes the rational by rounding in the direction that weakens the bound: a weight is rounded down, never up |
| `method` | for example `active-box count`, `exhaustive table`, `milp`, `branch-and-bound` |
| `tool`, `validation` | the tool, and the ID and SHA-256 of the validation record of its exact hash, whose `created_utc` must be earlier (FR-039; SC-007); a tool used outside its validated kind writes `not evaluated` |
| `solver` | for `milp`, the fixed settings of R12: `mip_rel_gap` 0, the `time_limit`, the solver status, the proven dual bound used (never the best solution found), and HiGHS's built-in tolerances and thread count in the pinned scipy, recorded as such |
| `scope` | "single trails under the usual independence assumptions; clustering into differentials and linear hulls, and key-dependent effects, open for feature 005" |
| `budget` | hours used and the cap; only a proven result gives a `bound` (R12), and a capped or timed-out search has `status` `inconclusive` and no `bound` |

A bound from a tool not yet validated never counts; a trail it finds is an unverified hypothesis
(section 5).

## 7. Tool validation record (`validation/<tool>-<record_id>.json`; FR-039)

`tool`, `version`, `tool_sha256`, `licence`, `source` (in the repository, or the entry of the
downloads manifest `downloads.json`, research R19, with the paper's table and value),
`validated_kind` (word width, operation set and kind of model; R12), `known_result` (paper,
table and value, or the security.md finding S12–S15 or FUT-SEC-8), `found`, `outcome`
(`re-found` or `not re-found`). A tool's results count only after a `re-found` record of the
same kind and of the tool's exact hash exists.

- **What must match.** The exact published value over the stated rounds: for a trail search,
  the weight of the optimal trail, not the trail itself; for the S-box tables, every entry; for
  PRESENT, the stated minimum of active S-boxes over 5 rounds. Any difference is `not
  re-found`.
  For the known results that are not published values, what must match is exact equality for every
  deterministic fact: S12's ranges and classes; S15's 16 steps and its bound 2¹²⁸ · (2³¹ + 1)⁴;
  S13(a)'s merged pair 16m + 15 and 16m + 16; S7's three rotation relations; each structural tool's
  counts and matrices, entry by entry; R5's counts; and FUT-SEC-8's three seeds and its vector
  check. A measured fraction, such as S13's 41% and 32% or S14's bit frequencies, matches when the
  tool's count lies in the binomial interval around the recorded fraction, for the tool's sample
  size, with at most 0.005 in each tail. Anything else is `not re-found`.
- **After a failed validation**, the record of the next attempt holds the defect, its cause and
  the fix, and the re-validation re-finds a second known result of its kind as well as the
  first, named in the defect record before the fix runs. Every attempt is a record of its own.
  Results of the failed version never count; results already counted from an earlier
  validated version stand, since they cite its hash.
- **The bias test** (R4): S14's bias re-found on `phyco-v2`, and on 100 sets of synthetic
  binomial counts with one bit planted at the 90%-power biases it fires in 82 to 97 of the 100
  sets.
  The sets are class 5 of section 2, and the record holds the numpy version and each set's SHA-256.
- **Self-written known results.** Each known result this feature writes itself (the small operation
  list with its hand-derived matrices, the map with collisions, the variant with a planted gap, R5's
  hand-counted examples) is written with its SHA-256 and entered in the provenance log (section 14)
  before the tool it validates is drafted, so its entry's `seq` comes before the tool's first entry.
  The validation record cites both entries, and a test checks their order and that the hashes still
  match.
- **A value that cannot be obtained** leaves the tool unvalidated and its results `not
  evaluated`, unless the owner provides the value with its source (R12, R19).

## 8. D4 choice record (`d4/choice.json`; R5, R6)

`entered` (candidate IDs with their log `seq`), `width` (16 or 8), `r_star`, with the
statement that r* compares the candidates over the same rounds and is not a rate per round
(R6); per scored candidate `W_D` and `W_L` as rationals, `luts` (R5) and the score;
`representatives`; `outcome` (`chosen`, `chosen by default`, `tie` or `not computable`, R6);
`chosen_family`; `tie_breaks_applied`; `bound_records`. Written once by `scripts/d4_choice.py`
from saved bound records; a second run that would change it is refused. After a tie,
`d4/tie.json` is written once by `d4_choice.py --tie`, with both values of R at 4×4, or the
ineligibility that decided it. If the tie-breaks reach the owner's choice, it is made only
after `d4/tie.json` exists, recorded in the record and in the Review & Approval row "D4 tie"
with the date, the choice and the record's SHA-256, and it never changes.

## 9. Round rule, eligibility and selection

`candidates/<id>/round-rule.json`, per claimable size: `R_f`, `R_b`, `R_bound` (with its bound
records), `R_dist` (with its evidence records), `delta` = 2, `R`, and `eligible` with each item
of FR-018 to FR-031 and FR-037 and its evidence. `selection.json`: the eligible candidates of the
chosen family, or of the other family if it has none, or of both families if D4 was not
computable; R at 4×4; any tie and the owner's recorded choice; or the stop-rule outcome with its
reason. The owner's choice in a tie is made only after `selection.json` exists, recorded in the
record and in the Review & Approval row "Selection tie" with the date, the choice and the
record's SHA-256, and it never changes.

## 10. Size profile and security target (`security-target/`)

`parameters.json`, one row per supported size:

- `n`, `w`, `lanes_per_node` (2), `b`, `c`, `r`, `variant_id`, and `R`. A research variant's R
  carries its reason: the round rule's value where its inputs exist at that variant, or a
  reduced count chosen for a stated test and marked as reduced; the variant ID carries R.
- `key_entropy_bits` and `nonce_bits`: c and c/2, so 256 and 128 at every claimable size, and 0
  for a keyless variant (R14). `keyed_variants` names each size's keyed variants: the
  production variant at every claimable size, and at 2×2 at least one keyed reduced variant,
  such as `n2-w16-R8-c64` with an 8-byte key and a 4-byte nonce. Keyless variants are listed as
  permutation-only.
- `reachable_secret_state_bits`, per call boundary (after instantiate, after each generate with
  its forget call, after each reseed): the bits of the state that no public input sets and no
  output reveals, the capacity part, c bits, for the duplex as designed. It is counted from the
  specified layout (which lanes form the capacity part, and that no call writes or outputs
  them) and recorded as "by specification", not measured. Public parts are never counted:
  constants, domain-separation bits, counters, the nonce, the personalization string, reseed
  inputs and every output; a reseed input is never secret state, even from a secret source,
  since FR-016 treats it as chosen by the attacker. A value below 2s at any boundary fails
  FR-010.
- `bound_bits` and `status` (`claimable` or `research`). A research row's bound is labelled
  "research variant, no claim", and it is never compared with s = 128 or reported as a
  strength.
- The generic-bound checks of FR-010, at s = c/2 for a keyed reduced variant, each a check that
  can fail, with 0 violations required at every claimable size: output volume (every limit at
  most what the theorem allows at ε, R9's doubling check), multi-target search, key plus nonce,
  capacity, quantum search (T11 as single-target key search only, FR-008: k/2 ≥ s, which holds with
  equality and no margin at k = 256 and s = 128, recorded as met with equality), and the
  stated behaviour on nonce reuse, with its test.
- At claimable sizes, `throughput_implied`, in 32-bit words per second at 200 MHz (FR-026): computed
  from the rate r/(P·R + ⌈r/i⌉) bits per cycle, where i is the output interface's
  `interface_bits_per_cycle`, since the next call starts only after the consumer has taken the block
  (FR-025), with r/(P·R) and i reported beside it; per stated request size (the 2¹⁹-bit cap and
  4,096 words), counting each request's output calls plus its forget call, with instantiate's calls
  spread over a stated number of requests per instantiation; and `rate_before_forget` beside it as
  an upper bound (R5). Beside them, `throughput_goal` (10⁸; R5), which is reported and never an
  eligibility rule.

`limits.json`: `epsilon` (2⁻⁶⁴), `N` (2¹²⁸), the theorem (paper, theorem number, `verified` or
`unverified`); the limits per instantiation, per request and per key, each in calls of Π, the
theorem's unit, which is primary, and in bits at every claimable size (a request of n bits
takes ⌈n/r⌉ output calls plus one forget call, and instantiate's calls are stated); every other
online quantity the bound counts with its limit; `u`; the two allowed ways of choosing nonces,
and for random nonces the collision term q²/2¹²⁹ in the bound and the random-nonce
instantiation limit, at most 2³², which the model applies to every key whatever its nonces (R9); the
bound at the limits and the doubling check of R9.

## 11. Vectors (`vectors/phyco-v3/`; FR-036, FR-054)

| File | Content |
|------|---------|
| `pi_<variant>.json` | 16 inputs and their Π and Π⁻¹ outputs, as lanes in hex in the design document's order; the state after every phase of every round for the first 4, as `pi_trace` returns it |
| `mode_<variant>_dev<i>.hex` | header line, then 10,000 lines of `%08X`, as the `phyco-v2` vector files |
| `digest_<variant>.json` | SHA-256 of the first 2²⁰ output words for key and nonce 0, in requests of 4,096 words, over FR-015's canonical serialization as 4·2²⁰ raw bytes, not over the `%08X` text lines |
| `constructed_<variant>.json` | per edge state: name, construction, whether a key reaches it, inputs, outputs |
| `constants_n<n>_w<w>.json` | the constant table of one supported (n, w), as `phycoweb/constants_v3.py` holds it (R15), with the count of words skipped by the reading order and every repeat of a class where one call needs more constants than there are aperiodic classes (FR-023) |
| `MANIFEST.json` | the sidecar: one entry per generator run with the command (script and arguments, relative to the repository root), the interpreter, the model's SHA-256, the platform, the measured speed (calls of Π and words per second) and the generation time; `--check` does not compare it |

The header of a mode vector file reads, for example:

```text
# model=phyco-v3 variant=phyco-v3/n4-w32-R<R>-c256 key=dev/0 nonce=dev/0 pers=empty requests=1,7,64,1000 count=10000 format=u32-hex
```

The header's fields come in this fixed order, each `key=value`, separated by single spaces.
Generated files hold only deterministic content, under the format rules of the introduction,
so that `--check` can compare them byte for byte; everything that differs between runs or
platforms goes to the sidecar `MANIFEST.json` (R8). A variant directory name is the variant ID
with `/` replaced by `_`.

**Order of generation** (FR-036, FR-059): three steps, each generator's `--check` passing in this
order. (1) `gen_constants_v3.py` writes the constant tables. (2) `gen_vectors_v3.py` writes the
vectors through `pi` and `ResearchDuplex`, which runs no self-test, and also writes
`phycoweb/selftest_v3.py`, the self-test's inputs and expected output, copied from the vectors.
(3) `Generator` imports `phycoweb.selftest_v3` and runs the self-test from it. Tests check that
`Generator` reproduces the vectors and that `selftest_v3` equals them, and the freeze hashes
`selftest_v3.py` with the vectors (section 13).

## 12. Baseline archive (`baseline/phyco-v2/MANIFEST.json`; FR-042)

As `baseline/float-v0/MANIFEST.json`: `created_utc`, `git_head`, and `files`, each with
`archive_path`, `source` (path and commit), `sha256` and `note`. The archive holds
`phycoweb/model_v2.py`, `phycoweb/lut.py`, `fast/phyco_stream.c`, `fast/lut_table.h`,
`specs/002-core-dynamics-redesign/design.md` and both `vectors/phyco-v2_*.hex`. A test checks each
copy against its manifest hash and its live source (SC-012).

## 13. Design freeze record (`freeze/freeze.json`; FR-043)

- **Hashes**, each with its kind (`raw` or `lf-normalized`, R16): the design document (with
  its version); `rationale.md`, versioned with it; `phycoweb/model_v3.py`;
  `phycoweb/constants_v3.py`, with its table per supported (n, w); `phycoweb/selftest_v3.py`
  (section 11); every vector file, including the constructed-state vectors and the constant tables
  beside them; the scripts that generate the constants and the vectors; the selected operation list;
  `research/004/ir.py` with its tools; and the scripts that compute verdicts: `evidence_v3.py`,
  `round_rule.py`, `d4_choice.py`, `recheck_004.py`, `protocol/devinputs_v3.py` and
  `protocol/evidence.py`.
- **Round count**: per claimable size, R with every input of the round rule, and every evidence
  record behind R, by ID and by SHA-256.
- **Logs**: the last `seq` and line SHA-256 of the candidate log, the provenance log and the
  protocol change log.
- **Selection**: the `variant_map` of the `selected` entry (section 3), with the operation
  list's SHA-256.
- Tool versions; `git_head`; `git_dirty`, which must be false; `draft_sha256`, written by `create`:
  the SHA-256 of the record's canonical JSON without that field and the approval fields; and
  `status`, `draft` until the owner approves. `design_freeze.py approve --by NAME --wording TEXT`,
  run by the owner, changes `status` to `approved`, adds `approved_by`, `approved_utc` and
  `approval_wording`, and changes nothing else.

The freeze runs in five steps (FR-043): (1) the owner commits the feature files;
(2) `design_freeze.py create` runs with `git_dirty` false and writes the record as `draft`;
(3) the owner runs `design_freeze.py approve --by NAME --wording TEXT`; (4) the owner commits the
record; (5) `validate` exits 0. Dirty means a tracked file modified or an untracked file not
ignored; ignored files (the locks, local-only outputs) do not count, and local-only outputs are in
the record by SHA-256 anyway. `validate` recomputes `draft_sha256` and every hash and checks the
format rules; it exits 1 if anything but the approval fields changed or a hash does not match, and 2
while `status` is `draft`. After approval the frozen files must not change: a fix to a verdict
script is a new file, so that the re-check (FR-065) runs the code that produced the verdicts. The
approval status of the design document and the rationale stays outside the frozen files (FR-034).

## 14. Provenance record (`provenance.jsonl`; FR-067)

One line per file drafted or repaired with an AI tool: `seq` and `prev_sha256`, chained as the
candidate log is (section 3: the previous line's UTF-8 bytes as stored, final LF included), `path`,
`section`, `sha256`, `tool` and `model`, `session`, `date_utc`, `task_id`, `review_status`. Every
append takes `data/log-append.lock` and checks the chain first (R16), and a broken chain is repaired
as in section 3. The entries for `phycoweb/model_v3.py` and `tests/v3_reference.py` must name
different sessions (FR-057). A known result this feature writes itself (section 7) has an entry of
its own, with its SHA-256, before the first entry of the tool it validates. `section` names a part
of a file: each AI-drafted section of the rationale has its own entry with its review status, which
the owner design review updates, so that the frozen text carries no status (FR-034).

## 15. Claim and evidence register (`protocol/claims.json`; FR-069)

One entry per model ID (`float-v0`, `lut-v1`, `phyco-v2`, `phyco-v3`): `claim_level` (L0…L5),
`in_progress`, `claim` (`no claim`), `bound` (for example "at most 64 bits" for `phyco-v2`),
`evidence` (record paths), `updated`. `phyco-v3` starts at L0 and moves to L1 only when the spec's
"L1 recorded" row reads Approved, after the FUT-SEC-8 result review and the security-target review,
security.md §15's L1 gate since version 2.13 (FR-012); the spec approval recorded no level.

- `claim_level` keeps the highest level reached (L0 or L1 in this feature). `in_progress` names
  a level started and not reached, L2, with its start date and "not reached". The claim test
  checks that no document states a level above `claim_level`.
- `fut_sec`, for `phyco-v3`: each FUT-SEC requirement's status in the terms of the spec's
  traceability table. FUT-SEC-4 is met by statement (D7); FUT-SEC-5 is met by specification for
  key loading, and by evidence for diffusion through instantiation (FR-029) and research R4's
  first-order related-key and related-nonce differences, and stays open for feature 005's analysis
  (FR-049). L1's "FUT-SEC-1 to FUT-SEC-6 met by specification" (security.md §15) is decided on this
  one reading: the security-target review accepts the design document's section on key loading and
  cites the selected candidate's evidence records of the measured part, which exist by then, since
  the review is the first step of plan phase 8, after the selection, so nothing remains to measure.
- `allow_list`: the lines the claim test would flag that may stand, each with its path, its
  text and its reason. The test flags any strength (a number of bits beside "security",
  "strength" or "secure", or a cost such as 2¹²⁸ beside "security") unless the same sentence or row
  carries "target" or quotes a rule. It also flags "random", "truly random", "randomness" and
  "high-entropy" in every line it scans, since Principle IV forbids describing the generator so
  beyond what committed evidence supports. "Near" and "beside" in its rules mean the same sentence
  or table row. A flagged line passes only through this list, a rule's own text included, one entry
  per rule line. Standing entries, one fixed phrase each with its reason, let these uses stand: the
  project's name, PhycoWeb-PRNG; "random permutation" and "ideal permutation" in a bound's
  statement; random nonces as a usage rule; the random baseline and the uniform controls of the
  tests; "an established cryptographic random-number generator" in the disclaimer; security.md §6's
  rows, which state a standard's own status; and the spec's FR-025 sentence on zeroization in the
  model, which says what the model does not promise. Any other flagged line needs an entry of its
  own.

## 16. Review package (`review-package/MANIFEST.json`; FR-063)

Every item of security.md §14, each with its path, `git_head` and SHA-256 with its kind, plus
the known limitations and the unresolved findings. An existing `text=auto` file is hashed over
its LF-normalized content and marked `lf-normalized`, so the hash is the same on every
checkout, and no existing file's pin changes (R18). Assembling the package is in scope; sending
it is the owner's action.

## 17. State transitions

- **Candidate**: the diagram in section 3.
- **Claim level of `phyco-v3`**: `claim_level` L0 now; L1 once its gate has passed after the
  review of FUT-SEC-8 and of the security-target chapter (FR-012), recorded in the Review &
  Approval row "L1 recorded". While any theorem the mode chapter uses is "unverified" (R10),
  that row reads "blocked" and names the missing paper. L0 needs no row. L2 is never
  `claim_level` in this feature: `in_progress` names it from the first counted trail-bound
  record, with its start date and "not reached". Every level carries "no claim".
- **Protocol rules**: as pre-registered; a change is an entry of section 18, only in its stated
  stricter direction (FR-044).
- **Design document**: draft versions 0.x; the version the owner design review approves; frozen
  as 1.0. After the freeze any change is a new model ID (FR-028).
- **Gates** (spec Review & Approval table): `_pending_` to Approved or Declined, with date and
  notes; one row per download approval.
- **Evidence status**: `not evaluated` until a record exists; `inconclusive` for a capped search
  or a fired control; `blocked` while a gate it needs is pending; otherwise the computed verdict.

## 18. Protocol change log (`research/004/protocol-changes.jsonl`; FR-044)

One JSON object per line, append-only, chained and locked as the candidate log is (section 3):
every append takes `data/log-append.lock` and checks the chain first (R16).

| Field | Rule |
|-------|------|
| `seq`, `prev_sha256` | as in section 3 |
| `date_utc` | ISO 8601 |
| `rule` | the pre-registered rule changed, by its name in the spec's protocol or its research section |
| `old_text`, `new_text` | the rule's text before and after |
| `reason` | why it changed; for an entry from the checklist answers, its row ID in checklist-choices.md |
| `direction` | `stricter`, in the rule's stated stricter direction, or `settled`: a case the protocol leaves open, fixed only before any result it affects exists, with the owner's approval, and never looser than any reading of the existing text (FR-044) |
| `readings` | for a `settled` entry, each reading of the existing text compared, with why the new text is no looser than it; empty for a `stricter` entry |
| `approver` | the owner, with the approval's date |
| `last_record_id` | the last evidence record ID that existed when the change was made, so that "before any result it affects" can be checked; `none` while no evidence record exists |
| `results_known` | the results known at the time, by record ID, and for each candidate already evaluated, the verdicts recomputed under the new rule (R7); empty while no result exists |

A change applies to every candidate, those already evaluated included. The log's first entries,
written when it is created, are one per answered row of
[checklist-choices.md](./checklist-choices.md), of both runs of 2026-11-01, whose applied change
altered the text of a pre-registered rule, whatever its tag: the 31 rows tagged Stricter or Settle
(18 and 13), and the Add, Align and Clarify rows that changed such a rule, for example ANA-028's
known result for the bias tool. Each cites its row ID and takes `stricter`, in the rule's stated
direction, or `settled`. The list is fixed by row ID before the log is created. Among them, the
constant rule's values (research R15) and the SHA-256 of its refused list are `settled` entries
written before the first candidate is scored. The spec's Clarifications point to the log.
