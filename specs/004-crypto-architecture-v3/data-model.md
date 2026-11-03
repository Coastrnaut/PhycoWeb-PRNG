# Data Model: Cryptographic Architecture and phyco-v3 Design

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

All records are JSON (UTF-8, LF line endings, sorted keys), written by one module,
`protocol/evidence.py`. Paths are under `reports/004-crypto-architecture-v3/` unless stated, and
files committed there are limited to `.json`, `.jsonl`, `.md`, `.csv`, `.txt` and `.gz`;
`protocol/evidence.py` refuses any other suffix there (research R16, R18), a
reproduction's outputs included (section 1, Reproduction). A record is never
overwritten: a repeat run, the demonstration's included (section 4), writes a
new record with a new identifier beside the old one, which stays, its file
named by its `record_id` (section 1, Record files). The stated exceptions
are the files kept under a fixed name: `candidates/<id>/round-rule.json`,
`security-target/parameters.json` and `limits.json`, the environment records, `downloads.json` and
`review-package/MANIFEST.json`; the environment records, the downloads manifest and the review
package's manifest are records of kinds of their own, `environment`, `downloads` and
`review-package`, as the freeze record is of kind `freeze` (section 1; REP-085). Before one changes,
`protocol/evidence.py` keeps its current content as `<dir>/versions/<sha256>.json` beside it, and
the new content holds `previous_sha256`, both the raw SHA-256 of that content as
committed (REP-083); a record that cites one gives its path and SHA-256, and the
re-check resolves either from the versions (research R16). The downloads manifest's `approved`,
`fetched` and `not obtained` entries are written by `scripts/downloads.py`, run by the agent, and
its `owner-provided` entries by `scripts/owner_record.py owner-provided`, the owner's own act, both
through `protocol/evidence.py` (research R19; REP-076). After the freeze, `protocol/evidence.py`
refuses, exit 2, to write over one that the freeze record pins, `parameters.json`, `limits.json` and
the selected candidate's `round-rule.json` among them (section 13). The selection records are
written once each and never rewritten: a later selection is a new record,
`freeze/selection-<k>.json` (section 9). Three committed files are append-only, their earlier
entries never changing: `research/004/tools/critical_counts.json`, which is code (section 5), the
sidecar `vectors/phyco-v3/MANIFEST.json` (section 11) and `research/004/candidates/superseded.json`
(section 3); a record that cites one gives its SHA-256 and the entry it used, and every evidence
script exits 2 while a file a record would cite is modified in the working tree, so that
`dirty_paths` never holds one (section 1). The freeze record changes only by the
owner's approval, which `scripts/design_freeze.py approve` writes into it
through the freeze code of `protocol/design_freeze.py`, its draft checked by
`draft_sha256` (section 13).

**Format rules** for every record and generated file (FR-036, FR-053), so that another
implementation can write byte-identical files:

- Text is UTF-8 without a byte-order mark, with LF line endings only and a final newline.
  Scripts write with `encoding="utf-8"` and `newline="\n"`, and no hashed file is written by
  Windows PowerShell 5.1, whose `Out-File -Encoding utf8` adds a byte-order mark.
- JSON has sorted keys and `ensure_ascii=False`, with two-space indentation in a `.json` file
  and one object per line in a `.jsonl` log. Rationals are "p/q" strings. Floats appear only in
  reported statistics and are written with `repr`.
- Canonical JSON, over which an approval hash, `draft_sha256` and the eight hex digits of a
  `record_id` are taken, is the object's UTF-8 JSON with keys sorted, the separators `,` and `:`
  with no spaces, no final newline and non-ASCII characters written as they are; a hash over it is
  of kind `canonical` (section 1; REP-083). The eight hex digits of a `record_id` are computed
  first, over the record's canonical JSON without `record_id`, without the approval fields and
  without any hash taken over the record itself, an approval hash or `draft_sha256`, so that
  approving a record leaves its ID derived from its content; an approval hash and `draft_sha256` are
  then computed over the canonical JSON without the approval fields and without that hash,
  `record_id` included (section 1, Record files; REP-092).
- Hex words of vectors and states are upper case and zero-padded to the word's width, with lanes in
  the design document's order. Every digest is written as 64 lower-case hex digits, as the existing
  records already are. A vector file's header is `# key=value` fields in a fixed order, separated by
  single spaces (section 11). In a fingerprint's text (section 2), byte strings (keys, nonces,
  personalization strings, reseed inputs) are lower-case hex, as digests are, and states are written
  as here.
- A `.gz` file is written by `gzip.compress(data, compresslevel=9, mtime=0)`, so its header holds no
  file name and a zero time, and a test checks the header of every committed `.gz` file under this
  feature's paths (research R16); feature 003's, listed with their hashes in its `SHA256SUMS`, are
  outside its scope and stay unchanged. Its raw hash is over the compressed bytes, and its output
  entry also holds `uncompressed_sha256`, the SHA-256 of its content, which a reproduction compares
  for every `.gz` file but a `p_values` file (section 1; research R16).
- `lf-normalized` content is the file's bytes with each CR LF pair replaced by LF, as Git
  normalizes, a lone CR kept; it is never computed from a file read in text mode, whose universal
  newlines also turn a lone CR into LF.
- Every list is sorted by a stated key: fired bits by round count, direction, set and bit;
  matches by candidate value; IDs lexicographically; symmetries in a stated enumeration order.
  Nothing depends on set iteration, hash randomization, thread completion or worker count.

## 1. Common fields (every evidence record; FR-061, security.md §17.2)

| Field | Type | Rule |
|-------|------|------|
| `record_id` | str | `<kind>-<UTC yyyymmddThhmmssZ>-<8 hex>`, the eight hex digits derived from the record's content, computed first, without the approval fields and without any hash over the record itself (introduction, format rules; REP-092); unique; the record's file is `<record_id>.json` unless this data model states its name (Record files, below) |
| `kind` | str | one of: `demonstration` (section 4); `inverse`, `bijectivity`, `dependency`, `frequency`, `avalanche`, `control`, `symmetry`, `invariant` and `degree` (section 5); `bound` and `trail` (section 6); `validation` and `cross-check` (section 7); `d4-choice`, `d4-tie` and `d4-tie-choice` (section 8); `round-rule`, `cost`, `selection` and `selection-tie-choice` (section 9); `size-profile` and `limits` (section 10); `generator-run` and `generator-check` (section 11); `projection`, `lock-cleared`, `reproduction` and `recheck` (below); and `environment`, `downloads`, `freeze` and `review-package`, the records kept under a name of their own (research R1, R19; sections 13, 16; below; REP-085) |
| `created_utc` | str | ISO 8601, seconds |
| `model_id`, `variant_id` | str or null | `phyco-v2` for US1 and for tool validation on it; null for a `control` record, which belongs to no model (section 5); in the four kinds kept under a name of their own, `model_id` `phyco-v3` in the freeze record and the review package's manifest and null in the other two, and `variant_id` null in all four (Kinds kept under a name of their own, below; REP-093); otherwise a candidate or `phyco-v3` variant ID (research R14) |
| `design_version`, `design_sha256` | str | the design document's version, read by `protocol/evidence.py` from its header's line "Version: 0.<k>", and 1.0 while the design document has the SHA-256 that the approved freeze record names, the header keeping the 0.<k> that the owner design review read, which the record holds as `reviewed_version` (spec FR-034; RAT-080), and its hash; `none` before it exists; the first record that cites a version stores that document as `design-versions/<sha256>.md`, committed with the records, as spec versions are (research R16) |
| `spec_sha256` | hex | SHA-256 of `spec.md` at run time; the first record that cites a hash stores a copy of that spec as `spec-versions/<sha256>.md`, committed with the records (research R16) |
| `research_sha256` | hex | SHA-256 of `research.md` at run time, which holds the values that decide verdicts; kept as `research-versions/<sha256>.md`, as spec versions are (research R16) |
| `protocol_seq`, `protocol_line_sha256` | int, hex, or `none` | the protocol change log's last entry when the run started (section 18), by `seq` and line SHA-256, which every record holds, since the shared guard "Protocol log" refuses every run that writes evidence before the log exists with its first entries approved (section 18; cli contract); both `none` in a `lock-cleared` record or an environment record written while the log does not exist, the two kinds `protocol/evidence.py` writes then: the first since it records an event and clearing a stale lock is what lets the log be created (PRO-065), the second, written by `owner_record.py environment`, since it records the platform, holds no result and comes before the log, whose writer checks the running environment against it (PRO-071); once the log exists each cites its last entry |
| `git_head`, `git_dirty`, `dirty_paths` | str, bool, list | as in the feature-002 and feature-003 records; `dirty_paths` lists every modified or untracked path not ignored, which may be data and report files only, since code is committed before every evidence run (`code_sha256`), and never a file a record would cite: every evidence script exits 2 while one is modified in the working tree (introduction) |
| `code_sha256` | object | path → SHA-256 of every code file the run used: the script, the `protocol/` modules, the candidate's operation list, `research/004/ir.py` and its tools, `research/004/tools/critical_counts.json` among them (section 5), a C source and its binary. A self-written tool's version is its hash (FR-039). Code is committed before every evidence run: a run that writes evidence exits 2 unless every source file here matches HEAD, committed and unmodified, and a binary is rebuilt from committed source, its hash reported only by a reproduction; a test checks each entry against the blob at `git_head`, the commit a reproduction runs (Reproduction, below; research R16) |
| `versions` | object | Python, numpy, scipy, gcc, and every tool used, with its version and licence |
| `environment` | object | path of the platform's environment record in force, `environment-windows.json` or `environment-wsl.json` (research R1), and its two hashes, each with its kind: its SHA-256 over its bytes as committed, kind `raw`, which also names it under `versions/` and in `previous_sha256`, and its approval hash, kind `canonical`, over its canonical JSON without the approval fields (introduction, format rules), which `owner_record.py` prints, its row names and the guard compares, so that the guard, the re-check and a later reader resolve the same record from either (REP-083); written by the owner with `scripts/owner_record.py environment`, with `approved_by`, `approved_utc` and `approval_confirmed`, and Approved in its own Review & Approval row, "Environment record <n>", at HEAD, which the start check compared the running environment with as a whole (Python, every package of `pip freeze --all`, taken as research R1 states, gcc and make in WSL, the Windows build or the WSL distribution and kernel); an earlier one resolved from `versions/` (introduction); a `recheck` record holds its own environment instead (below); the environment record itself, the one write the guard "Environment" admits while no record is in force or the running environment differs from it, holds `none`, with the interpreter's version and each pinned package's version that its check against research R1 and the pins of `requirements.txt` compared (PRO-068); each entry of the provenance log, the protocol change log and the downloads manifest names the record in force the same way, as its `environment` (sections 14, 18; research R19; REP-082) |
| `platform` | object | operating system, CPU, logical CPUs, RAM |
| `parallelism` | object | worker and thread counts, and `PYTHONHASHSEED` if set |
| `command`, `config` | str, object | the interpreter by its full path (on Windows the `python.exe` of the Store distribution's versioned prefix, `sys.executable` with the alias resolved; in WSL `~/.venvs/phycoweb/bin/python`; research R1), then the script and its arguments with paths relative to the repository root; the working directory and the repository root; every parameter |
| `inputs` | object | namespace (`dev` or `control`; for US1 the feature-002 `dev` set), kind, index range, fingerprint (R3) |
| `outputs` | list | `{path, sha256, bytes, committed, deterministic}`, `uncompressed_sha256` for a `.gz` file, and `compared` for an output compared otherwise than by its hash; `committed` false for local-only files, written under `data/local/004/<record_id>/`, the ID of the record that lists them, a reproduction's own included, and never under this directory (R16); `deterministic` false for an output that is not, such as a raw solver log with timings, whose `sha256` and `bytes` a reproduction reports only, and for a `p_values` file, with `compared: values`, whose `sha256`, `bytes` and `uncompressed_sha256` a reproduction reports only, comparing its values (Reproduction, below); a committed file has one of the suffixes of the introduction and at most 10 MB, a reproduction's included, and `protocol/evidence.py` refuses a larger one, naming it |
| `exit_status`, `assertions` | int, list | every assertion with its outcome |
| `status` | str | `pass`, `fail`, `inconclusive`, `not evaluated` or `blocked` (security.md §16.3), computed by code (FR-065); in the freeze record `pass` once each of `create`'s checks holds, as it must for `create` to write the record, its approval state being the field `freeze_status` of its own (section 13; REP-093) |
| `classification` | str | one of the four classes of security.md §9.1, or `none` for a record without a finding, computed by code (FR-065) from the table below by kind and outcome; a reviewer may add only a note (FR-060) |
| `analyst`, `reviewer`, `review_status` | str | the AI agent and model, or a person; `reviewer` and `review_status` stay as written, `pending` where no review preceded the record, which is never overwritten: its review is a provenance entry that names the record's ID and SHA-256 (section 14) |
| `limitations` | list[str] | known limitations, and the scope of any negative result; a MILP bound at w = 16 or 32 states that it is proven by the solver within HiGHS's built-in tolerances, with no exact confirmation (R12) |
| `heavy_run` | bool | true if the run held the heavy-run lock (FR-045) |
| `disclaimer` | str | `protocol.disclaimer.DESIGN_DISCLAIMER`, verbatim (FR-068) |

Statistical records (section 5, `frequency`, `avalanche` and `control`) also hold the items of
security.md §11.6: `sample_size`, `test_parameters`, `raw_counts` (path and SHA-256),
`p_values` (path and SHA-256), each JSON or gzip-compressed JSON, never `.npy`, `failure_locations`
(every fired bit with its round count, direction and input or difference set) and
`exclusions_and_reruns` (each citing the recorded tool defect, one of the kinds of research R7, with
its evidence; empty unless a tool defect is recorded).

**Classification** by kind and outcome, computed by code (FR-060, FR-065). security.md §9.1
classifies findings, so a record without one holds `none`; a reviewer may add a note, never change
the class.

| Kind and outcome | `classification` |
|------------------|------------------|
| No finding: vectors, constants and constructed states with their generator runs and checks, the environment, downloads, freeze and review-package records (REP-085), projections, validations and cross-checks (a failed one is a tool defect, section 7), the size profile and the limits, the `cost` and `lock-cleared` records, a `recheck` record without a disagreement under the rules in force at a record's entry (one under a later stricter change is that change's recomputed verdict, section 18), the D4 choice, tie and tie-choice records, the round-rule and selection records and the selections' tie choices, a reproduction that matches, and a search at its cap, which keeps `status` `inconclusive` | `none` |
| A fired `control` (section 5) | `none`, with `status` `inconclusive` for that test and size |
| A firing (a bias test's, or an invariant form held above its chance rate), a trail found by a validated tool (section 6), or a `dependency` record showing incomplete diffusion, raising R or not | `confirmed vulnerability` of the reduced rounds it covers, worded with its round count and, for a firing, the stated family-wise chance of a false firing |
| A failed `inverse`, `bijectivity` or `symmetry` check, or a kept invariant | `confirmed vulnerability` of the candidate, worded as the failed property, with its decision |
| A `degree` record that raises R_dist, its inside-out count included | `strong theoretical concern`: an argument shows it, and no run demonstrates it |
| A proven bound (section 6) | `no weakness identified within the analysis performed`, with its scope |
| A test that does not fire | `no weakness identified within the analysis performed`, with its scope |
| A reproduction that differs on a field that enters a verdict | `unverified hypothesis`, with `status` `blocked` until it is resolved (Reproduction, below) |
| A reproduction that differs only in the p-values, which decide no verdict | `none`: a finding about the run's reproducibility, reported, which blocks nothing |
| A `recheck` record with a disagreement under the rules in force at a record's entry | `unverified hypothesis` for that record's result, with `status` `blocked` until it is resolved, the disagreement being a tool defect (Re-check records, below) |
| A finding of a tool not yet validated | `unverified hypothesis`, with `status` `blocked` |
| The demonstration record (section 4) | `confirmed vulnerability` of `phyco-v2`'s seed bound once every target is recovered; a disagreement in its match counts is an `unverified hypothesis` until the FUT-SEC-8 result review |

- **Hashes.** Every SHA-256 a record holds is recorded beside its kind, `raw` or `lf-normalized`
  over a file's bytes (research R16), or `canonical` over a record's canonical JSON (introduction):
  an environment record's or an `owner-provided` entry's approval hash, the freeze record's
  `draft_sha256` (REP-083), and the approval hash of the protocol change log's writer, over one
  canonical JSON array of the first entries in log order or over a later entry alone, each entry
  without `approver` and `prev_sha256` (section 18; REP-094).
- **Record files.** Every record file is `<directory>/<record_id>.json`, the directory being its
  kind's place: `fut-sec-8/` for a `demonstration`; `candidates/<id>/` for the kinds of sections 5
  and 6 but `control`, and for a `cross-check` and a `cost` record; `controls/` for a `control`;
  `validation/`, `generator-runs/`, `generator-checks/`, `projections/` and `rechecks/` for the
  kinds they are named after, but an exploration table's `generator-run` record, which sits beside
  its table in `research/004/exploration/` (section 11); `locks/` for a `lock-cleared` record; and
  `reproductions/<record_id>/<n>/`, with the original's ID, for a `reproduction`. Files whose names
  this data model states keep them: the fixed-name files, with `versions/` (introduction); those
  written once under a stated name, a second write being refused: `d4/choice.json`, `d4/tie.json`
  and `d4/tie-choice.json` (section 8) and the selection records and their tie choices (section 9);
  and the freeze record, `freeze/freeze.json`, which changes only by the owner's approval
  (introduction, section 13). The eight hex digits of a `record_id` are the first eight of the
  SHA-256 of the record's canonical JSON without `record_id`, without the approval fields and
  without any hash taken over the record itself, an approval hash or `draft_sha256`,
  and with its own ID written as `<record_id>` wherever a path holds it,
  computed before those hashes, which then include it (introduction, format
  rules; REP-092); until the record is complete, its outputs are written
  under a temporary name, renamed to the ID before the record is written.
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
- **Fixed-name files.** A record that cites a file kept under a fixed name (introduction) gives its
  path and SHA-256, and the re-check resolves either from `<dir>/versions/`.
- **Kinds kept under a name of their own.** The environment records (`environment`, research R1),
  the downloads manifest (`downloads`, R19), the freeze record (`freeze`, section 13) and the review
  package's manifest (`review-package`, section 16) hold the common fields of this section and the
  fields of their own sections: `command`, `config`, `code_sha256`, `versions`, `platform`,
  `parallelism`, `exit_status`, `assertions`, each of the script's checks with its outcome, and
  `heavy_run`, false, hold the run of the script that wrote the record or its latest change,
  `owner_record.py environment`, `downloads.py` or `owner_record.py owner-provided`,
  `design_freeze.py create` and `review_package.py`, so that each is traced to the command and the
  code that wrote it, while `inputs` and `outputs` are `none`, the files each names being held in
  its own fields; `model_id` is `phyco-v3` in the freeze record and the review package's manifest
  and null in the other two, and `variant_id` is null in all four, the freeze record's
  variants standing in its `variant_map` (REP-093). Each is written through
  `protocol/evidence.py`, the freeze record's changes through `protocol/design_freeze.py`, and
  `scripts/review_package.py` assembles the review package through `protocol/review_package.py` and
  writes its manifest, its `--check` rebuilding the manifest from the files it lists and comparing
  it (cli contract). `downloads.py`, `owner_record.py` and `design_freeze.py` have no `--reproduce`,
  each recording an owner's act or an outside fact that a later run cannot regenerate (research R16;
  REP-085).
- **Re-check records.** `recheck_004.py` writes a `recheck` record, `rechecks/<record_id>.json`,
  which names, per record, the commits whose verdict functions it ran, that
  record's `git_head`, from a worktree of it, for the rules in force at its
  entry and HEAD for the current rules (research R16), and holds in place of
  `environment` the interpreter, the platform and the full `pip freeze` it
  ran with, and says when that environment is not one of research R1's: the re-check is exempt from
  the environment guard (cli contract). A disagreement under the rules in force at a record's entry
  blocks the candidate as a differing reproduction does: the record's result becomes an unverified
  hypothesis, `blocked` (spec FR-060), the `recheck` record is a finding, and the disagreement is a
  tool defect of research R7, whose one re-run follows the fix; a disagreement under a later
  stricter change is that change's recomputed verdict, applied as research R7's stricter change and
  recorded in `results_known` (section 18), not a defect. A reproduction of a `recheck` record that
  differs is a tool defect of `recheck_004.py` wherever it ran, since its verdicts and counts depend
  on no environment.
- **Reproduction.** A reproduction of a record is run by its script's `--reproduce RECORD` mode (cli
  contract), `fut_sec8.py`'s for a demonstration record included, in a separate worktree of the
  original's `git_head`, the code files of its `code_sha256` checked against that commit's blobs, so
  the committed-code guard applies to that commit, not to HEAD's files. It writes its `reproduction`
  record into the main tree's `reproductions/<record_id>/<n>/`, `<record_id>` being the original's
  and n = 1, 2, … for successive reproductions of that record, with each output that the original
  commits, under the same suffix and 10 MB rules (`outputs`); an output that the original keeps
  local-only goes to `data/local/004/<record_id>/`, `<record_id>` there being the reproduction's
  own, never committed, and the record holds its SHA-256, compared with the original's. A
  generator's reproduction of a `generator-run` record compares each generated file in memory
  with the SHA-256 that record holds (section 11) and writes no `.py` or
  `.hex` file, its record holding each file's path, SHA-256 and outcome. The record holds the
  original's ID and SHA-256, the commit it ran, each compared field with its outcome, the reported
  fields, and `match` or `differs`. A reproduction appends nothing to the candidate
  log, charges no candidate's budget row and is not a re-run under research
  R7, so it can neither replace evidence nor add any; a heavy one runs only on the owner's request,
  quoted with its date in the record's `owner_request`, and is charged to research R7's feature-wide
  row. A difference is a finding: the original stands; a difference in a field that enters a verdict
  (every compared field but the p-values) makes the candidate's eligibility `blocked`, as an
  unverified hypothesis does (FR-060), until it is resolved, and, since it ran in the environment
  that made the original (below), it is a tool defect of research R7, whose one re-run is a new
  measurement in the original's row and raises R by the round rule if it fires; a difference in the
  p-values, which decide no verdict, makes the outcome `differs` and blocks nothing.
  `round_rule.py` reads the `reproduction` and `recheck` records of the candidate's records
  (section 9). It compares these fields with the original and reports every other
  field only: `kind`, `model_id`, `variant_id`, each source file's entry in `code_sha256`, `inputs`,
  each deterministic output's `sha256` and `bytes` (not its path), `exit_status`, `assertions`,
  `status`, `classification`, and the fields the table below lists for its kind, `design_sha256`
  among them only where the table says so. Timings and the raw solver log are never compared.
  Deterministic kinds (vectors, constants, dependency matrices, counts, digests) thus match byte for
  byte, and searches and solver runs by their values and verdicts. A different source hash makes it
  a new run, not a reproduction, and a binary's hash is reported only. A
  `p_values` output is marked `deterministic` false with `compared: values`
  (`outputs`), so its `sha256`, `bytes` and `uncompressed_sha256` are reported only,
  and its values are compared, in either format, decompressed first: two
  p-values agree when their difference is at most 10⁻⁶ times the larger of their
  magnitudes, or when both are below 2⁻¹⁰²², the smallest normal double, so that a 0 beside a
  subnormal agrees. A value outside makes the outcome `differs`, exit 1, with the values
  listed: a finding about the run's reproducibility that blocks no candidate,
  since no p-value decides a verdict (section 5, "Exact verdicts"). Every
  other `.gz` file is compared by its `uncompressed_sha256`. The verdict is
  recomputed under the spec version, the research version and the protocol change-log entry the
  original cites (`spec-versions/`, `research-versions/`, section 18), so a later change cannot
  alter it, and it runs in the environment that made the original, as recorded, and in no other, a
  `recheck` record's reproduction excepted, which runs anywhere, as the re-check does (research R1).

**Fields compared, per kind** (FR-053). A reproduction compares the fields of the Reproduction
bullet above that its original holds, and those this table lists for its kind; it reports the rest.
Timings (seconds, steps or calls per second, projected and used hours, measured speed) and the raw
solver log are never compared. `design_sha256` is compared only for a kind whose code reads the
design document, which the table names; for every other kind it is reported, and `none` stays
`none`. Any other script that reads the design document is added to this table before its first run.

| Kind | Also compared | Reported only |
|------|---------------|---------------|
| Demonstration (section 4) | `targets`, `revealed`, `observed`, `vector_check`, `matches`, `assumption`, `listed`, `recovered`, `model_sha256`; of `tool`, the source's SHA-256; of `cost`, the steps per candidate and the total steps | of `cost`, the seconds, the steps per second and the extrapolation; the rest of `tool` (the binary's hash, compiler, flags, threads); `report`, which restates the compared fields with timings; `design_sha256` |
| Structural evidence (section 5: `inverse`, `bijectivity`, `dependency`, `symmetry`, `invariant`, `degree`) | the fields of its row in section 5 | the projected and used hours, the measured speed; `design_sha256` |
| Statistical evidence (section 5: `frequency`, `avalanche`, `control`) | the fields of its row and the items of security.md §11.6 above: counts, critical counts and fired bits byte for byte, and the p-values by value | as for structural evidence |
| Trail bound and trail (section 6) | `bound_kind`, `rounds`, `width`, `size`, `bound`, `method`, `tool`, `validation`, `scope`, `cross_check`; of `solver`, the settings, the status and the proven dual bound; of `budget`, the cap; of a `trail` record, `trail_kind`, `characteristic` and `weight` | of `budget`, the hours used; the raw solver log; `design_sha256` |
| Tool validation (section 7) | `tool`, `version`, `tool_sha256`, `licence`, `source`, `validated_kind`, `known_result`, `second_known_result`, `found`, `outcome` | the projected and used hours; `design_sha256` |
| Cross-check between kinds (`cross-check`; section 7) | `tool` and its version, and, per r and width, the tool's value beside each exhaustive one with its outcome: for an ARX-box, the internal-trail search's value at w = 4 and whether they are equal, and the floor at w = 4 and 8 and whether the value lies at or above it; for the active-S-box counter, the exhaustive minimum and whether they are equal | the projected and used hours; `design_sha256` |
| D4 choice, round rule, cost records and selection (sections 8 and 9) | every field of its section | `design_sha256` |
| Size profile and limits (`mode_limits_v3.py`; section 10) | every field of section 10, and `design_sha256`, since its code reads the design document's variant table, layout and limits (RAT-085) | none of its own |
| Generator run, constant tables (`generator-run` of `gen_constants_v3.py`; section 11) | each written file's path and SHA-256, computed in memory and compared with the record's, and `design_sha256`, since its restatement check reads the design document (research R15); for a candidate's tables (`--candidate`) and an exploration table (`--exploration`), each check's verdict as well | the measured speed and the generation time |
| Generator run, vectors (`gen_vectors_v3.py`) | each written file's path and SHA-256, as for the constant tables, and `design_sha256`, since its code reads the design document's table of k (section 11; REP-097) | as for the constant tables |
| Generator run, constructed states (`gen_constructed_v3.py`) | each written file's path and SHA-256, as for the constant tables | as for the constant tables, and `design_sha256` |
| Generator check (`generator-check`; section 11) | each generated file's path and SHA-256 and the verdict, and `design_sha256` for `gen_constants_v3.py`'s and `gen_vectors_v3.py`'s (REP-097) | `design_sha256` for `gen_constructed_v3.py`'s |
| Review package (`review-package`; section 16) | every field of section 16, and `design_sha256`, since its code reads the design document | none of its own (REP-085) |
| Re-check (`recheck`; above) | per record, each recomputed verdict, its agreement with the recorded one and the commit whose functions computed it; the counts of agreements and disagreements | the interpreter, the platform and the `pip freeze` it ran with |
| Projection (above) | nothing beyond the common fields | the measured speed and the projected hours |

No row is needed for a `lock-cleared` record, which records an event, a `reproduction` record, which
is not reproduced, a tie choice (`d4-tie-choice`, `selection-tie-choice`), an owner's own act that
no script repeats, or an `environment`, `downloads` or `freeze` record, whose writers have no
`--reproduce` (Kinds kept under a name of their own, above; REP-085); the claim test writes no
record (spec FR-061).

## 2. Development inputs (`protocol/devinputs_v3.py`; FR-040, R3)

| Constant or function | Rule |
|----------------------|------|
| `PREFIX` | `phycoweb-004/` |
| `NAMESPACES` | `dev`, `control`; nothing else is accepted |
| `key(ns, i)`, `nonce(ns, i)`, `pers(ns, i, m)`, `reseed(ns, i)` | 32, 16, min(m, 32) and 32 bytes from SHA-256 of `phycoweb-004/<ns>/<kind>/<i>`; outside the module and its own tests, called only through `load` (below) |
| `state(ns, n, w, i)` | b = 2w·n² bits from the digests of `phycoweb-004/<ns>/state/n<n>w<w>/<i>/<j>`, j = 0, 1, …, read into lanes as R3 states |
| `synthetic_seed(ns, n, j)` | for `ns` = `dev` only, the first 16 bytes of SHA-256 of `phycoweb-004/dev/synthetic/n<n>/<j>`, read as a big-endian integer: the seed of synthetic set j at size n (class 5 below) |
| `FINGERPRINTS` | per namespace and kind, per (n, w) for `state` and per n for `synthetic`: the SHA-256 of the fingerprint text below; (n, w) over spec FR-018's sizes with research R14's widths (4 at 2×2 only, 8, 16 and 32), at most 16 pairs, and n over the claimable sizes, all written in plan phase 1 before the first record, after which nothing is added (research R3) |
| `load(ns, kind, allow, count, ...)` | the only way scripts take inputs, as feature 002's scripts use `protocol/seedsets.py`'s `load`: it checks the namespace against `allow` (`PermissionError`; scripts exit 2) and the kind's fingerprint (for `state` at the given n and w, for `synthetic` at the given n) and returns the values i = 0…count − 1, so no index outside the use's declared range can be read; it refuses, naming it, any (n, w) or n without a fingerprint and any kind without one (scripts exit 2), and a test checks that every allowed pair has a fingerprint |

The empty personalization string is a named input of its own. Indices are decimal without
leading zeros. The module imports only `hashlib`. A keyed reduced variant of capacity c takes the
first c/8 bytes of `key(ns, i)` and the first c/16 bytes of `nonce(ns, i)` (R3, R14). A test fails
if code outside the module and its own tests calls a derivation function.

**Fingerprint text** (FR-040; research R3), fixed so that another implementation computes the same
fingerprints: the values for i = 0…99, or j = 0…99 for `synthetic`, one per line, each line ending
in LF, the last included, in ASCII, as `protocol/seedsets.py` writes. Keys, nonces, personalization
strings and reseed inputs are lower-case hex of their bytes, as digests are written; a state is one
string of its w-bit words in upper-case hex in the design document's lane order, as the format rules
write states (introduction), which gives its first b bits in hex whatever that order is; a synthetic
seed is a decimal integer. A personalization string's fingerprint is taken over its full 32 bytes,
so it does not depend on m, which the design fixes later; a use with m < 32 takes a prefix the
fingerprint already covers.

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
| 5 | synthetic counts | for the bias test's validation only (R4): set j = 0…99 at each size from numpy's `Generator(PCG64(s))`, s being its seed, which `load` returns for the kind `synthetic`; one `binomial(N, 1/2)` count per tested bit, in the test's bit order, except the planted bit at position j mod S, drawn as `binomial(N, 1/2 + δ)` at that size's δ (0.0030, 0.0031 or 0.0033); `validate_tool.py` draws the counts, which are local-only (research R16) and never replaced; a set's SHA-256 covers its counts as decimal text, one per line in the test's bit order, each line ending in LF, and the validation record commits it with the numpy version and a per-set summary (section 7); the test's bit order is research R4's: set 1, then set 2, within each the b bits after Π, then the b bits after Π⁻¹, lanes in the design document's index order and bits most significant first; the validation's second family, j = 100…199, is drawn the same way, each set planting its bit at position ⌊(j − 100)·S/100⌋ (section 7) |

## 3. Candidate log (`research/004/candidates.jsonl`; FR-041, SC-011)

One JSON object per line, append-only, each entry chained to the one before it. Every append takes
`data/log-append.lock` and checks the chain first (R16). The log, the superseded copies and their
inventory are pinned to LF with every file under `research/004/` (research R18), so the hashes that
cite them hold on every checkout.

| Field | Rule |
|-------|------|
| `seq` | 0, 1, 2, … with no gaps |
| `prev_sha256` | SHA-256 of the previous line's UTF-8 bytes as stored, its final LF included, as 64 lower-case hex digits; 64 zeros for `seq` 0 |
| `candidate_id` | `cand-A1` to `cand-A3`, `cand-B1` to `cand-B3`; a candidate counts towards the stop rule from its first entry, `proposed`, whatever happens after, and a fourth `proposed` entry of a family is refused |
| `family` | `ARX` or `Boolean` (D4) |
| `event` | `proposed`, `mapping`, `entered-d4`, `scored`, `evidence`, `decision`, `correction`, `repair`, `replacement`, `set-closed`, `review-outcome`. A `review-outcome` entry, holding the owner design review's row with its highest k, the outcome, `declined`, `revised`, `fixed` or `stopped`, its reasons, for a decline what the rules need to select a further candidate, and for a revision or a fix the candidate's old and new versions, is written by `candidate_log.py outcome` after the commit that records the decision of that row, which it reads at HEAD, exiting 2 on an outcome the row does not record (Decline at the owner design review, below; ANA-083). A `mapping` entry, written before the candidate's first score, holds FR-030's mapping of the candidate's own components, FR-030's five, the colour schedule, the local linear layer between boxes, the round constants, its key path, spec FR-025's key register at each node that holds key bits with the key shift chain through those nodes, from its operation-list declarations, and any other it adds (RAT-078): each one's place in the metaphor and the attack class, bound or need it serves; the mapping chapter restates only the first part, and the rationale's component list states the second, citing this entry; the structures that every candidate shares, those of the mode and the core, the rest of spec FR-034's component list (RAT-078), take their roles from spec FR-025 and FR-059 in place of the entry and have no place in the metaphor (spec FR-030, FR-034; RAT-073). A `replacement` entry names a candidate that became `rejected` or `ineligible` while its family had fewer than three evaluated candidates and the budget allowed: logged `pending` with that decision where the decision's cause lies in the candidate itself, its own evidence or properties, it is closed by the replacement's `proposed` entry, which cites its `seq`, or by a later `replacement` entry that cites it with the stated reason (the family full, the budget spent, or "the owner declined the proposed design", the owner's word quoted with its date; ANA-087); where its family or the whole set shares the cause, the entry is logged closed at once, with the reason "cause shared", and no replacement is entered for it (Decisions, below; ANA-073), and `round_rule.py --close` reads them (Entered set, below). A `set-closed` entry names no candidate: `round_rule.py --close` writes it once every candidate has a final decision and no replacement is pending, and `--select` exits 2 before it (Entered set, below) |
| `oplist_sha256` | hash of the candidate's operation-list module (R11). The `proposed` entry with this hash comes before any tool run, and every tool refuses an operation list whose hash has no `proposed` or `correction` entry (exit 2); the module is committed before that run, as every source file of a run that writes evidence is (section 1) |
| `parameters` | round structure, nonlinear component, rotation and constant rules, generics; the instance of the constant rule (polynomial, seed, reading order, distinct streams per call type or not, with the reason; R15); the rotation search's space of amounts, its K ≥ 2 sets and their placement rule from n, and its width (16 first), the ranking measure, rounds and tie order being the protocol change log's one rule for every candidate (R15), and, if R6's rule fixes the D4 width at 8, a new entry before the search at 8 with the same space, K and placement rule; FR-018's folding rule, longest link per size, food nodes with their positions and reason, and each tree's fan-in per stage, depth, registered stages and latency, which eligibility reads (section 9); and the reduced variants used as evidence (widths, sizes, round counts, capacities); and P, the number of phases in one round of the operation list at each size (FR-025). All are logged before the candidate's first tool run; a variant added later is logged with its reason before its first run |
| `evidence` | the IDs of every record of the candidate, used or not, as security.md §11.3's "report everything" asks |
| `budget_used_h` | `{trails, structural, statistics}` with the caps of R7, the D4 reduced-width searches and the rotation-amount searches under `trails`; the uniform controls' hours, logged by no candidate, are added to `statistics` by the Budget guard from the control records (section 5); each heavy run's projected and used hours, measured speed and engine code hash. A budget lowered below the hours already used leaves zero hours: the results so far stand, and no further run of that row starts (R7) |
| `decision`, `reason` | `eligible`, `ineligible`, `rejected`, `withdrawn`, `selected` or `not selected`, with the reason (below) and, for `rejected` and `ineligible`, the record that shows it by ID and SHA-256 (Decisions, below; ANA-088); a `selected` or `not selected` entry cites its selection record by path and SHA-256, with the record's tie choice where there is one (section 9; ANA-081) |
| `variant_map` | on each `selected` entry, which `round_rule.py --decide` writes after a selection record, the latest being the one in force (section 9; ANA-081): the map from `cand-…/n…-w…-R…-c…` to `phyco-v3/…`, with the operation list's SHA-256; the model's tests check that `phyco-v3` reproduces the candidate's outputs through it; each variant ID carries the final R that the candidate's `round-rule.json` gives at its size, a rise of R at 8×8 or 16×16 after a selection record bringing the next record and its entries (section 9; ANA-085) |
| `date_utc` | ISO 8601 |

An entry is never edited or deleted; a correction is a new entry that cites the `seq` it
corrects. `cand-A1` is the long-trail ARX-box design (FR-022).

Each kind of entry has one writer, which the agent runs (cli contract): `evidence_v3.py` appends the
`evidence` entries; `d4_choice.py` one `scored` entry per scored candidate when it writes
`d4/choice.json`, citing it by path and SHA-256 (section 8); `round_rule.py --decide` the `selected`
and `not selected` decisions after each selection record and `round_rule.py --close` the
`set-closed` entry (section 9; Entered set, below); `repair_log.py`, through
`protocol/candidates.py`, the `repair` entry (Repair, below; PRO-076); and `candidate_log.py`,
through `protocol/candidates.py`, every other entry, its `propose`, `mapping`, `enter`, `decide`,
`correct`, `replace` and `outcome` appending the `proposed` entry, the `mapping` entry, one
`entered-d4` entry per candidate of the entered set before any score, a decision other
than `selected` and `not selected`, a `rejected` or `ineligible` one with the `replacement` entry it
brings, a `correction`, a `replacement` entry that closes a pending one with its
reason, and the `review-outcome` entry (ANA-083), each from a file holding the
entry's fields but `seq`, `prev_sha256` and `date_utc`, which the writer
adds. Every refusal of the log writer that this section states is the command's, exit 2, appending
nothing, `enter` among them once a `scored` entry exists, and a `proposed` entry that records the
owner's approval of a replacement, or of a further candidate after a decline, is written only on the
owner's explicit word, quoted with its date in it, as a provenance review entry's `owner_word` is,
and so is a `replacement` entry that closes a pending one with the reason "the owner declined the
proposed design" (section 14; spec FR-041; RAT-077; ANA-080, ANA-081; ANA-087).

- **Decisions.** `rejected` and `ineligible` are given only for the rules' reasons: a failed
  inverse or bijectivity test, a failed eligibility item (FR-018 to FR-031, FR-037, R_bound
  not established, inconclusive evidence), a spent budget, or, for a candidate of the family D4 did
  not choose that was not analysed at the production width, "not analysed at the
  production width: D4 chose the other family", and, for the representative
  that lost an exact D4 tie, "D4 chose the other family by its tie-breaks"
  (spec "Nonlinearity choice rule"; RAT-072). A candidate may be `withdrawn`
  before its first tool run, for any recorded reason, and it still counts towards the stop
  rule. The log writer refuses any other decision. A decision cites by ID and SHA-256 the record
  that shows its reason: a failed check's record for `rejected`, the round-rule record's eligibility
  item for `ineligible`, R7's rows with the record of the need for a spent budget, as `replace`
  reads them (ANA-078), and the D4 record for the two D4 reasons; `candidate_log.py decide` exits 2
  on a decision whose cited record does not show its reason, on a D4 reason before every candidate
  of the chosen family has its final decision with one of them eligible, and on a `replacement`
  state other than the one the rules' classification gives, `pending` or closed with the
  cause shared, and the re-check recomputes every decision and `replacement`
  state with eligibility and selection, a disagreement blocking as for any
  record (spec FR-065; ANA-088). A raised R is never by itself a reason for a
  decision: the measurements it needs run as new measurements in their budget rows, and a row that
  cannot hold them makes the candidate `ineligible` for a spent budget (spec Edge Cases). A
  decision's `replacement` entry is logged `pending` only where the decision's cause lies in the
  candidate itself, its own evidence or properties; where its family or the whole set shares the
  cause, as for the reasons "not analysed at the production width: D4 chose the other family" and
  "D4 chose the other family by its tie-breaks", and for the decisions that a fired uniform control,
  the lack of a validated trail route or a match in the shared polynomial bring, the entry is logged
  closed at once, with the reason "cause shared", and no replacement is entered for it (spec
  "Eligibility and selection"; ANA-073). An `ineligible` decision for a row that cannot hold a run
  the rules require of every candidate at that size, a uniform control's hours, a stricter change's
  new measurement or a trail search at 16×16, is classed by that run's recorded need: shared where
  the need exceeds the row's value of research R7, at its current value after any lowering, which
  every replacement's row of that value shares, the decision's `replacement` entry then being logged
  closed at once with the reason "cause shared", and the candidate's own where the candidate's
  earlier charges to that row left too little (ANA-078).
- **Entered set.** Candidates are entered before any is scored (R6's entered set). A further
  candidate is entered later only in place of one that became `rejected` or `ineligible`, never
  because another's R is high, and one is entered for every candidate that became `rejected` or
  `ineligible` for a cause of its own, its own evidence or properties, while its family has fewer
  than three evaluated candidates and the budget allows, and none for a decision whose
  `replacement` entry was logged closed at once with the reason "cause shared"
  (Decisions, above; ANA-073, ANA-077): the agent proposes it, and the owner
  approves its entry, quoted with its date in its `proposed` entry, which closes the
  `replacement` entry logged with the decision; a stated reason, the family full, the budget spent
  or "the owner declined the proposed design", closes it otherwise, the last written only on the
  owner's explicit word quoted with its date, after which the agent proposes no other design for
  that entry, so that the set closes on the candidates entered (ANA-087).
  The budget allows while each of the replacement's own rows of research
  R7, at its current value after any lowering, holds more than zero hours and at least the recorded
  need of each run that the rules require of every candidate at that size and that would be charged
  to it, a uniform control's hours, a stricter change's new measurement or a trail search at 16×16,
  so that a replacement is not entered only to end as the candidate it replaces did (Decisions,
  above; ANA-078); it is spent when one of those rows, at its current value, is at zero after a
  lowering or below the recorded need of such a run, and the log writer closes a
  `replacement` entry for that reason only when R7's rows, the record of that
  need and, for a lowered row, the protocol change log's entry that lowered
  the budget show it, exit 2 otherwise. The set closes at a `set-closed`
  entry, written by `round_rule.py --close` once every candidate has a final decision and no
  `replacement` entry is `pending`; `--select` exits 2 before it, and no candidate is entered after
  it but as a decline at the owner design review allows: after a `set-closed` entry
  `candidate_log.py propose` exits 2 unless the latest `review-outcome` entry is `declined`, with no
  later `set-closed` entry, and the candidate is that decline's further candidate or one of its
  replacements, so that the set reopens once (Decline at the owner design review, below; ANA-083). A
  final decision is `withdrawn`, `rejected` or `ineligible`, or, for an eligible candidate,
  its round-rule record at every claimable size (section 9); the other family's candidates, the
  representative that lost an exact D4 tie among them, analysed at the production width, or further,
  only if D4's chosen family ends with no eligible candidate, are otherwise `ineligible` (Decisions,
  above; RAT-072).
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
- **Decline at the owner design review.** The declined candidate stays eligible and in the set, and
  the decline's reasons are logged under it in a `review-outcome` entry, as is each other outcome of
  the review (ANA-083). The decline reopens the set once, for one further
  candidate within the stop rule that the rules can select: from the chosen family, or from the
  other family only where the declined candidate was selected by the fallback or D4 was not
  computable, and only while its family has fewer than three evaluated candidates; before its
  `proposed` entry, the decline's log entry states what the rules need to
  select it, an R at 4×4 below the declined one's or a tie. Where none can be
  entered, the decline ends in one of spec FR-043's other outcomes. The further candidate is
  entered and evaluated like any other, and replaced the same way if it becomes
  `rejected` or `ineligible`, within the one reopening; once it has a final
  decision, a second `set-closed` entry closes the set, and `round_rule.py --select` runs again over
  the whole set: if the rules select the further candidate, it goes to the review; if they select
  the declined one again, the outcome is a stop, logged with the review's reasons. The declined
  candidate is never brought back to the review unchanged; a revision of its document, the decline's
  first outcome, stays possible instead (spec FR-043).
- **Repair.** A broken chain is repaired only with the owner's go-ahead, the Approved row "Log
  repair <n>" of the spec's Review & Approval table, which `repair_log.py --approval` names (R16).
  The broken file is kept unchanged with its SHA-256, and `scripts/repair_log.py` appends a `repair`
  entry through the log's one writer, `protocol/candidates.py` here, which takes
  `data/log-append.lock` and admits it, while that row reads Approved at HEAD, as the one append to
  a broken chain; in each log, this one, the provenance log (section 14) and the protocol change log
  (section 18), the entry holds the same fields: the break's `seq`, its cause, the broken file's
  path and SHA-256, the row "Log repair <n>" and what was restored (PRO-076). The restored log holds
  the lines before the break as stored and the `repair` entry chained to the last of them. Entries
  after the break count only where the records they cite corroborate them, and an entry that counts
  is appended again after the `repair` entry by its writer, as a new entry citing its `seq` and
  SHA-256 in the broken file, so that no entry is edited (PRO-076); the final report states the
  repair (R16).

```text
proposed ─► entered-d4 ─► scored ─┐       (only candidates entered before the D4 choice)
   │                              ▼
   ├────────────────────────► analysed ─► eligible ─► selected ─► frozen
   │                              │           └─────► not selected
   │                              └─► ineligible or rejected (reason recorded; stays in the log)
   └─► withdrawn (before the first tool run; counts towards the stop rule)
```

## 4. Demonstration record (`fut-sec-8/<record_id>.json`; FR-001 to FR-003)

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
| `supersedes`, `defect` | in a repeat after a tool defect, the earlier record's ID and the ID of the recorded defect it follows (cli contract, `fut_sec8.py`); `none` in the first record |
| `owner_request` | in a repeat after a tool defect, the owner's request, quoted with its date, without which the repeat exits 2, the repeat being a heavy run charged to research R7's feature-wide row (cli contract, `fut_sec8.py`); `none` in the first record. It is the repeat's request: a reproduction's, `fut_sec8.py --reproduce` being a heavy run too, is kept in its `reproduction` record (section 1) |

Each record is named by its `record_id`, which begins with `demonstration`, so that a repeat after a
defect writes beside the first, which stays; a run exits 2 while a record exists and no new defect
is named, or without the owner's request; a repeat, its vector check included, is a heavy run
charged to research R7's feature-wide row, against which it projects first, while the first
record's pass falls under the demonstration's own budget row (cli contract).
The record is the search tool's validation record (security.md §12.5). The
FUT-SEC-8 result review names the record it reviews by ID and SHA-256 in its row, and security.md's
best-attack register row for exhaustive seed search cites that record (FR-003).

`fut_sec8.py --reproduce RECORD`, run only after the FUT-SEC-8 result review and as a heavy run,
reproduces a demonstration record under section 1's rule: it writes a `reproduction` record under
`reproductions/<record_id>/<n>/`, `<record_id>` being the demonstration record's, its outputs placed
as section 1 states, compares the fields section 1's table lists for the demonstration, reports the
timings of `cost` and the binary's hash only, and does not compare `design_sha256`, which no
FUT-SEC-8 code reads. It is not a demonstration attempt: it can neither replace the demonstration
record nor change the review, and a difference is a finding. `fut_sec8.py --verify RECORD` re-checks
every listed match and every recovered seed with `model_v2`, with no sweep. Both take a record by
its ID, so that every earlier record stays reproducible and every run is reported.

## 5. Structural and statistical evidence (`candidates/<id>/<record_id>.json`)

| Kind | Fields beyond section 1 | Verdict computed by code |
|------|-------------------------|--------------------------|
| `inverse` | sizes and variants; the 16 vector inputs and 2¹⁰ test states; both directions | `pass` if 0 mismatches |
| `bijectivity` | variant 2×2, w = 4; 2³² inputs; ones in the output bitmap; bitmap SHA-256 | `pass` if 2³² distinct outputs |
| `dependency` | per round and direction, the bit pairs without dependency; R_f, R_b; per-round summaries committed, full matrices local (R16) | R_f and R_b reported |
| `frequency` | two input sets of N = 2²⁰ (key i with nonce i; key 0 with nonce i), S = 4b per call type's permutation, each permutation at its own threshold 0.005/S; per set, round count and direction the smallest p-value and the fired bits; the critical-count table it used (path and SHA-256) | fires or not, by comparing each count with its integer critical values (R4); raises R_dist |
| `avalanche` | N_a = 2¹³; the flip set F, the 384 key and nonce bits flipped in instantiation states (forward only) and the rotation amounts 1…w − 1; S_A = (2·\|F\| + 384 + 2(w − 1))·b per call type's permutation, each permutation at its own threshold 0.005/(128·S_A); as for `frequency`; the `dependency` record it is cross-checked against, with every disagreement | fires or not; raises R_dist; any disagreement is a tool defect and makes the record `inconclusive` |
| `control` | the test it controls, its counts, its inputs (R3's `control` states, taken as R4 states), whether it fired; `model_id` and `variant_id` null, since it belongs to no candidate. One record per test and size, `controls/<record_id>.json`, written before the test's first use at that size by any candidate, serves every candidate; it writes no candidate-log entry, and every candidate's 12 h row is charged its hours at that size, by projection until it exists (research R7); it is run again, with the same counts, only after a recorded tool defect in the control's own code, and its inputs are never redrawn or replaced | if it fired, that size's bias evidence is `inconclusive` for every candidate, none is eligible at that size, and the feature recommends stopping, citing this record |
| `symmetry` | patterns and symmetries checked, in the stated enumeration order, each pattern on its own (the K sets of amounts placed by their rule among them); symmetries that fix a pattern; the relations checked between the constants of one call (R13); at 2×2 and 3×3, the statement that the placements of the food nodes and of the amounts were checked together with the round constants as one pattern (R13) | `pass` if none |
| `invariant` | the size and variant, at every supported size and every variant used as evidence, after one round and after a full call; forms and differences checked, over the whole state and over each colour class of the size's schedule (two at even n, three at odd n by research R14's colouring), each set with its level, the colour forms at odd n being a new set tested in addition (R13); any kept on every test state; per form and round count, the count of test states on which it holds against its chance rate (R13) | `pass` if none; a form above its chance rate by the binomial test of R13 raises R_dist |
| `degree` | per claimable size, for Π and Π⁻¹: each phase's degree count from the operation list by R13's bottom-up rule (input lanes 1 and a constant 0; XOR, NOT, rotations and shifts the largest of their arguments; a bitwise function the largest sum of its arguments' degrees over its algebraic normal form's monomials, 2 for AND or OR of two lanes; ⊞ and ⊟ w − 1 times the larger operand's, a subtraction counting as an addition; an update its result's; a phase the largest of its updates', an unwritten lane 1), a round's count the product of its phases', a box's truth-table degree being computed only at w = 4 and 8, in the derivation's validation (section 7), never here; the count d for r rounds, the product of the per-round counts capped at b − 1, marked as the rule's count, not an upper bound; beside it an upper bound, by the same rules with w for ⊞ and ⊟, with the round counts at which it is at most 126; the round counts with d ≤ 126; and the inside-out count, the largest r₁ + r₂ with max(d_f(r₁), d_b(r₂)) ≤ 126, with its cost 2^(max(d_f, d_b) + 1) against 2¹²⁸ (R13) | each such round count, and the inside-out count, raises R_dist, since a zero-sum over a cube of dimension d + 1 costs 2^(d + 1) |

- **Exact verdicts.** The critical-count table, `research/004/tools/critical_counts.json`,
  holds per (N, S) and (N_a, S_A) the integer critical counts derived by exact integer
  arithmetic over the binomial distribution (R4). It is code, one of `research/004/ir.py`'s tools in
  every citing record's `code_sha256`, committed at HEAD before a run cites it and pinned to LF with
  every file under `research/004/` (research R18), and append-only: counts for a new (N, S) or
  (N_a, S_A) are added as new entries and existing ones never change, which a test checks against
  the file's history. scipy's p-values are reported only: a reproduction compares them by
  section 1's rule, and counts, critical counts and verdicts byte for byte (section 1).
- **Validation cited.** Every counted record holds `validation`, the ID and SHA-256 of the
  validation record of the tool's exact hash, whose `created_utc` is earlier (FR-039; SC-007).
- **Call types.** Where the call types draw on distinct constant streams (spec FR-023), the
  `inverse`, `symmetry`, `invariant`, `frequency` and `avalanche` records are made for each call
  type's permutation, each naming it in `call_type`, each permutation's bias tests at their own
  thresholds, S and S_A counting its bits only, with the chance of a raise stated beside a firing
  for the T call types tested (research R4), and R is the largest over the call types; a
  `dependency` record and a trail-bound record (section 6) read no constant value, cover one
  permutation for all and state that reason. Where the streams are not distinct, one permutation is
  covered.
- **Constants cited.** Every record whose result depends on the constants names the constant table
  it read by path and SHA-256, so that a result on one table is never cited for another; a rise of R
  makes a new table, and with distinct streams it changes every later call type's constants from
  round 1 (research R15). Before the freeze the table is the candidate's,
  `research/004/candidates/<id>/constants/<variant>.json`, which `gen_constants_v3.py --candidate`
  writes before the first record that reads it (section 11; research R15).
- **Unvalidated tools.** A trail or distinguisher found by a tool not yet validated is recorded
  as an unverified hypothesis (FR-060), with `status` `blocked`, and it blocks the candidate's
  eligibility until a validated tool, or direct evaluation of the trail with the validated
  exact models, settles it. If confirmed, it raises R_dist. A possible weakness can only raise
  R or block, never vanish.

## 6. Trail-bound record (`candidates/<id>/<record_id>.json`, kind `bound`; FR-038)

| Field | Rule |
|-------|------|
| `bound_kind` | `differential` (trail probability) or `linear` (squared trail correlation) |
| `rounds`, `width`, `size` | the variant it bounds |
| `bound` | the weight W, the bound's −log₂, as a rational "p/q" string: a multiple of 2⁻¹⁶ rounded down, never up, which weakens the bound, from the solver's float or from an exact probability (an exhaustive table's entry), which the record holds beside it; for an active-box or active-S-box count, the integer at or below the proven dual bound, with no tolerance (9.9999999 counts as 9), with the dual bound beside it (R12) |
| `method` | for example `active-box count`, `exhaustive table`, `milp`, `branch-and-bound` |
| `tool`, `validation` | the tool, and the ID and SHA-256 of the validation record of its exact hash, whose `created_utc` must be earlier (FR-039; SC-007); a tool used outside its validated kind writes `not evaluated` |
| `solver` | for `milp`, the fixed settings of R12: `mip_rel_gap` 0, the `time_limit`, the solver status, the proven dual bound used (never the best solution found), and HiGHS's built-in tolerances and thread count in the pinned scipy, recorded as such; the record states that its status rests on those tolerances (R12); the raw solver log is an output marked not deterministic, which a reproduction reports only (section 1) |
| `scope` | "single trails under the usual independence assumptions; clustering into differentials and linear hulls, and key-dependent effects, open for feature 005" |
| `cross_check` | for a bound from the ARX search or the active-S-box counter, the ID of the cross-check record of that candidate and that tool's exact hash: before the amounts are chosen, the cross-check on the first amounts of the candidate's space in tie order, which runs first in its trail row; after it, the cross-check of the chosen amounts scaled to w = 4 and 8, which the production-width searches need (R7, R12). The cross-check record lists per r the tool's value beside each exhaustive one, compared as section 7 states: for an ARX-box, equal at w = 4 to the exhaustive internal-trail search's and at w = 4 and 8 at or above the floor of the box's tables; for the active-S-box counter, equal to the exhaustive minimum; a bound without a passed cross-check does not count, and `d4_choice.py` uses none |
| `budget` | hours used, a timing that a reproduction reports only (section 1), and the cap; only a proven result gives a `bound` (R12), and a capped or timed-out search has `status` `inconclusive` and no `bound` |

A bound from a tool not yet validated never counts; a trail it finds is an unverified hypothesis
(section 5).

**Bounds per size.** Before selection, every candidate's R_bound at each claimable size comes from
bound records computed at that size; a proof in the design document that carries a bound to a larger
size serves only as a check beside them, in the rationale (FR-038).

**Trail record** (`candidates/<id>/<record_id>.json`, kind `trail`; FR-038). A trail is a
characteristic of Π exhibited by a validated tool that searches Π at the size
and width the round rule uses: `trail_kind` (`differential` or `linear`),
`characteristic` (the difference or mask after every round), `weight` (the
trail's exact probability or squared correlation as a rational "p/q" string,
with its −log₂), `rounds`, `size`, `width`, `tool` and `validation`, as for a bound;
`round-rule.json` cites it under `R_dist` (section 9). A bound, a box's trail, an active-box or
active-S-box count and a bound search's optimum are bounds, never trail records; an optimal
characteristic that a search of Π returns with its weight is one, written beside its bound record.

## 7. Tool validation record (`validation/<record_id>.json`; FR-039)

`tool`, `version`, `tool_sha256`, `licence`, `source` (in the repository, or an entry of the
downloads manifest `downloads.json`, research R19: a `fetched` file's entry with the paper's table
and value, or the `owner-provided` entry of a value the owner provides, written by the
owner with `scripts/owner_record.py owner-provided` and Approved in its own
Review & Approval row, "Owner-provided value <n>", at HEAD), `validated_kind` (the word widths its
known results cover, the operation set and the kind of model, with each use this plan makes of the
tool and the known result that covers it, a use without one writing `not evaluated`; a search's
results count only at a width so covered, the ARX search's at w = 16 from SPECK32 and at w = 32 only
once it re-finds a known result at 32-bit words, the active-S-box counter's at w = 8, 16 and 32 only
once it re-finds a further known result at that width, since PRESENT's result has no word width w,
the counter's word width being the w of the words whose bit positions a Boolean
layer's S-boxes take (ANA-072), and the cross-checks never widen a kind: a
cross-check is not a use, covers a candidate's operation set only, writes no
`not evaluated` and calls for no validation again; R12), `known_result` (paper,
table and value, or the security.md finding S12–S15 or FUT-SEC-8), `second_known_result` (the second
known result of the record's `known_result`, at its width, fixed before the tool's first validation,
with its source and its provenance-log entry, section 14, or `none`, which the first record
of that known result states; every known result at a validated width, the
first and each further one, has its own, R12; ANA-076), `found`, `outcome`
(`re-found` or `not re-found`). A tool's results count only after a `re-found` record of the
same kind and of the tool's exact hash exists.

- **What must match.** The exact published value over the stated rounds: for a trail search,
  the weight of the optimal trail, not the trail itself; for the S-box tables, every entry; for
  PRESENT, the stated minimum of active S-boxes over 5 rounds. Any difference is `not
  re-found`.
  For the known results that are not published values, what must match is exact equality for every
  deterministic fact: S12's ranges and classes and S15's 16 steps and its bound 2¹²⁸ · (2³¹ + 1)⁴,
  both re-found by the bias test's count on the vein lanes (research R4); S13(a)'s merged pair
  16m + 15 and 16m + 16 and S13(b)'s transport sums, unchanged on every probed state with all four
  veins in class 1, both re-found by the invariant checks (research R13); the
  planted invariants of the invariant checks' stated lists found, and none on
  the list without one; S7's three rotation relations; the planted torus
  symmetries of the stated lists at n = 3 and 4 found, and none on the list without one; each
  structural tool's counts and matrices, entry by entry; the avalanche test's three planted results,
  every bit of each round count's expected set firing at every round count from 1 to its
  variant's R and, at the variant's R, the bits that fire matching the expected
  set bit for bit, any other firing below it reported (research R4); the
  degree derivation's count by research R13's bottom-up rule, exactly, on
  a stated list at w = 4 holding an ARX-box spread over two phases and a bitwise S-box, with the
  exact degree from the truth table reported beside it and the upper bound at
  least that degree, and its hand-derived inside-out count; R5's counts; and FUT-SEC-8's
  three seeds and its vector check. A measured fraction, such as S13's 41%
  and 32% or S14's bit frequencies, matches when the tool's count lies in the binomial interval
  around the recorded fraction, for the tool's sample size, with at most 0.005 in each tail.
  Anything else is `not re-found`.
- **After a failed validation**, the record of the next attempt holds the defect, its cause and the
  fix, and the re-validation, after a failure at any width, re-finds every known result of the tool,
  the first and the second at each of its widths, each fixed before its first validation with its
  source in the provenance log (section 14) and cited by the defect record, so that no use at any
  width counts again on a fix tuned to one value (R12; ANA-076); a tool whose records state that it
  has no second known result at one of its widths stays unvalidated after a failed
  validation, its results `not evaluated`. Every attempt is a record of its own.
  Results of the failed version never count; results already counted from an earlier validated
  version stand, since they cite its hash.
- **The bias test** (R4): S14's bias re-found on `phyco-v2`, with S12's ranges and classes and S15's
  16 steps from its count on the vein lanes, bit 31 of each vein lane set after 16 steps from
  uniform starting states only on a lane equal to 2³¹, and, on each of two families of 100
  sets of synthetic binomial counts with one bit planted at the 90%-power biases, a firing of the
  planted bit in 82 to 97 of the family's 100 sets, a set counting only when its planted bit fires,
  with at most 3 of them holding a firing of an unplanted bit, each reported with its set,
  position and count, more making the validation `not re-found` (research
  R4): class 5 of section 2, j = 0…99, and the second family, a known result
  added, j = 100…199, drawn the same way, each set planting its bit at position ⌊(j − 100)·S/100⌋,
  so that the planted bits spread over all S bits, both sets and both directions (research R4). The
  sets are local-only (section 1, `outputs`) and never replaced; the record commits each set's
  SHA-256 (section 2), the numpy version and a per-set summary, the planted bit's count and every
  fired bit, so a fresh clone recomputes both families' verdicts from committed files and a
  regeneration checks every count. A later draw must reproduce every hash in an environment with
  that numpy version, and a draw that differs is reported and counts for nothing; after an approved
  numpy upgrade the old record stays the validation in the old environment, and a new validation, a
  new record, decides in the new one: outside 82 to 97, or with more than 3 sets holding an
  unplanted firing, in either family the tool is unvalidated there, its results `not evaluated`,
  until a defect is found and fixed.
- **The avalanche test** (R4): R13's three planted results re-found, one per path, each checked at
  every round count from 1 to its variant's R against that round count's expected set, the planted
  bits and every bit that the exact dependency matrices show independent of the flipped bit at that
  round count: every bit of the set fires at every round count, any other firing is reported with
  its round count, position and count and decides nothing below the variant's R, and at the
  variant's R, fixed with the known result as a round count at which every bit outside the set
  depends on the flipped bit, the result is re-found only if exactly that set fires, bit for bit,
  with the chance of a false firing there stated beside it: for the flip set the difference bits of
  the unmixed lane, a lane that no update writes, which others may read; for the related-key and
  related-nonce set the stated lane's bits for the stated key bit and nonce bit that never reach it;
  and for the rotational pairs the bits of the lane that commutes with word rotation, these two with
  their sets from their own dependency matrices; its verdict function, applied to
  every count 0 to N_a of one difference bit, fires exactly on the counts at or beyond the two
  critical values of `critical_counts.json`; and its power at δ_A = 0.0443, 0.0451 and 0.0465,
  computed exactly from the binomial distribution, is at least 0.9. One record per size covers the
  three paths, the flip set, the related-key and related-nonce set and the rotational pairs.
- **Cross-checks between kinds** (R12) check a tool on a candidate's own boxes and layers and are
  not uses of it: their values are compared, by exact equality and against the floor, never counted,
  they write no `not evaluated` and call for no validation again, and they cover the
  candidate's operation set only. They are records of the candidate they run on, of
  kind `cross-check`, written by `evidence_v3.py` into `candidates/<id>/`
  (section 1, Record files), once per candidate and tool version, charged
  to its trail row; a failed one is a tool defect. Each lists, for every r
  from 1 to the largest at which the exhaustive computation finishes within its 8 h cap, the tool's
  value beside the exhaustive ones: for an ARX-box, at w = 4 the optimal single-trail weight over r
  rounds of an exhaustive search over the box's internal trails, run by the exhaustive-tables tool,
  which the ARX search's must equal, and at w = 4 and 8 the best product of one-round entries of the
  box's exhaustive tables over r rounds, a floor, since a table entry sums every trail through the
  box's internal additions, below which no result of the search may lie; and for the
  active-S-box counter, the exhaustive minimum over r rounds at 4×4 from the
  nonlinear layer's tables, which its minimum must equal. They run first in the
  candidate's trail row, on the first amounts of its space in tie order, and again on the
  chosen amounts scaled to w = 4 and 8 (research R7, R12). The validations on
  published values stay validation records, charged to no candidate.
- **Self-written known results.** Each known result this feature writes itself (the small operation
  lists with their hand-derived matrices at 3×3 and 4×4, the lists with planted torus symmetries and
  the one with none, the map with collisions, the variant with a planted gap, the
  instantiation variant with a key bit and a nonce bit that never reach a
  lane, the operation list with a lane that commutes with word rotation, the lists with planted
  invariants and the one with none, R5's hand-counted examples, the small operation list of known
  degree with its inside-out count) is written under `research/004/`, whose files are pinned to
  LF (research R18), with its SHA-256, and entered in the provenance log
  (section 14) before the tool it validates is drafted, so its entry's `seq` comes before the tool's
  first entry. A self-written second known result (above) is written and entered in the same way.
  The validation record cites both entries, and a test checks their order and that the hashes still
  match.
- **A value that cannot be obtained** leaves the tool unvalidated and its results `not
  evaluated`, unless the owner provides the value with its source, recorded as an `owner-provided`
  entry of the downloads manifest, which `source` cites (R12, R19).

## 8. D4 choice record (`d4/choice.json`; R5, R6)

`entered` (candidate IDs with their log `seq`), `outcomes` (per entered candidate, its final
reduced-width outcome for each bound kind at 16 and, where R6 needs it, at 8: a bound record, the
`inconclusive` record of a capped search, or an `ineligible` or `rejected` log decision;
`d4_choice.py` exits 2 until each has one), `width` (16 or 8), `r_star`, with the
statement that r* compares the candidates over the same rounds and is not a rate per round
(R6); per scored candidate `W_D` and `W_L` as rationals, `luts` (R5) and the score;
`representatives`; `outcome` (`chosen`, `chosen by default`, `tie` or `not computable`, R6: `chosen
by default` where no width has a number of rounds common to both families, the family being the one
whose candidate has both bounds at the same number of rounds, at least 2, at the widest width at
which any candidate has them, 16 before 8, and, where both families have one there, the one whose
candidate has them at the larger number of rounds, `width` and `r_star` then being that width and
the largest such number of that family there, and `not computable` only where no candidate of either
family has both bounds at the same number of rounds, at least 2, at 16 or at 8; ANA-082, ANA-084);
`chosen_family`; `tie_breaks_applied`; `bound_records`, each from a tool that
has passed its cross-check on that candidate, which its `cross_check` cites
(section 6): `d4_choice.py` uses no other. Written once by `scripts/d4_choice.py`
from saved bound records; a second run that would change it is refused. After a tie, `d4/tie.json`
is written once by `d4_choice.py --tie`, with both values of R at 4×4, or the ineligibility that
decided it, and `decided_by`: `R at 4×4`, `carry chains`, `ineligible` or `owner`. Where a tie-break
decides, no choice is made: the owner sets the Review & Approval row "D4 tie" to "Not needed",
naming the tie record and its tie-break, and `round_rule.py --select` takes the family from
`tie.json`. If the tie-breaks reach the owner's choice, it is made only after
`d4/tie.json` exists and recorded beside it: `d4_choice.py --choose ID --seen SHA256 --by NAME`, run
by the owner, prints `tie.json`'s SHA-256 and exits 2 unless standard input is an interactive
terminal and the owner types its first 16 hex digits; it writes `d4/tie-choice.json` with the
choice, who, when, `seen_sha256` and `choice_confirmed`, the digits typed, and exits 2 if that hash
differs from `tie.json`'s, if no tie exists, if a tie-break decided it or if a
choice exists, so the choice never changes. Running it is the owner's own
act, which the agent never performs (spec FR-043). `tie.json` stays as the
script wrote it, and the Review & Approval row "D4 tie" holds, where the owner chose, the date, the
choice and both records' SHA-256. The design rationale's Alternatives chapter cites these records by
path and SHA-256 (spec FR-034).

## 9. Round rule, eligibility and selection

`candidates/<id>/round-rule.json`, a fixed-name file (introduction), per claimable size: `R_f`,
`R_b`, `R_bound` (with its bound records, computed at that size; FR-038), `R_dist` (with its
evidence records, the `degree` and `trail` records among them), `delta` = 2, `R`, with each rise and
its cause and the records made again at the new variant in research R7's order
("After a rise of R"), so that R is final at a size once a pass raises it no
further, and `eligible` with each item of FR-018 to FR-031 and FR-037 and its
evidence, decided for every candidate before selection: FR-018's folding rule, longest link, food
nodes with their reason and tree figures from the operation list and its `parameters` entry
(section 3); FR-020's cycles per call, with FR-026's figures, from its `cost` records per claimable
size (`candidates/<id>/<record_id>.json`, kind `cost`, written by `research/004/tools/costmodel.py`
from the operation list, P and R, with the self-test's least k from a run
of the candidate through the self-test's call sequence, its operation list
interpreted by `research/004/ir.py` in the shared mode, and the structure that set
it; spec FR-026, FR-059; REP-097); FR-022's bounds from its bound records
(section 6); FR-023's statement on the streams, with its reason, and FR-024's report
on the ranking after scaling from its log entries; FR-025's stages, chains
per phase and key path from the operation list's declarations, checked by
code; FR-027's semantics from the operation list's own declarations, which the framework requires
for every operation; FR-030's mapping from the candidate's `mapping` log entry. FR-025's interface
formats, call sequence and zeroization rules are properties of the mode, the same for every
candidate, decided once in the mode chapter, and the self-test's expected output (FR-018) is
generated from the selected candidate's vectors and cannot fail. A missing item fails eligibility,
and so does a `reproduction` record of one of the candidate's records that differs on a field that
enters a verdict, or a `recheck` record that disagrees with one of them under the rules in force at
its entry, until a re-run after a recorded tool defect resolves it (section 1; research R7);
`round_rule.py --select` reads the `recheck` records beside the `reproduction` records and
exits 2 while one holds an unresolved disagreement for a record it cites.
The record at every claimable size is an eligible candidate's final decision (section 3); a
candidate of the family D4 did not choose gets it at the production width only if the chosen family
ends with no eligible candidate, and is otherwise `ineligible` (spec "Nonlinearity choice rule").
The design document restates them for the selected candidate, and the owner design review checks
that the two agree. `selection.json`, the first selection record, written once, only after the
candidate log's `set-closed` entry (section 3), and never rewritten: the eligible candidates of the
chosen family, or of the other family if it has none, or of both families if D4 was not
computable; R at 4×4; any tie and the owner's recorded choice; or the stop-rule outcome with its
reason. Any change before the freeze that touches any candidate's eligibility or R at 4×4 after a
selection record exists makes `--select` run again over the whole set and write the next record,
`selection-<k>.json`, k = 2, 3, …, which cites the previous one by path and SHA-256; earlier records
stay. A rise of the selected candidate's R at 8×8 or 16×16 after a selection record exists, one that
leaves every candidate's eligibility and R at 4×4 as they were, also makes `--select` run again over
the whole set and write the next record, citing the previous one, and `--decide` appends
that record's entries, whose `selected` entry's `variant_map` carries the
final R at every claimable size, no entry being edited (ANA-085). After each
selection record, `round_rule.py --decide` appends to the candidate log one
`decision` entry `selected` for the candidate the record selects, with its `variant_map` and the
operation list's SHA-256, and one `not selected` entry for each other candidate the record lists as
eligible, each citing the record by path and SHA-256 and its tie choice where there is one, and
exits 2, appending nothing, while the record's outcome is a stop, while the record has a tie and no
choice whose row, "Selection tie" or "Selection tie <k>", reads Approved at HEAD with the choice
record's SHA-256, or once the record has its entries; a later selection record gets entries of its
own, whether it selects another candidate or the same one, so that no entry is
edited, the latest `selected` entry being the one in force and an earlier one
standing as a decision that a later record superseded, and `design_freeze.py
create` reads it (section 13; spec FR-041, FR-043; ANA-081). A decline's
re-selection is one such record: after a decline at the owner design review that
ends in a further candidate, entered only where the rules can select it (section 3), `--select` runs
again over the whole set, the declined candidate included, and selecting the
declined candidate again is a stop, with the review's reasons (section 3).
The owner's choice in a tie is made only after the selection record exists and recorded beside it:
`round_rule.py --choose ID --seen SHA256 --by NAME`, run by the owner, prints the latest selection
record's SHA-256 and exits 2 unless standard input is an interactive terminal and the owner types
its first 16 hex digits; it writes `freeze/selection-tie-choice.json`, or
`freeze/selection-<k>-tie-choice.json` for `selection-<k>.json`, with the choice, who, when,
`seen_sha256` and `choice_confirmed`, and exits 2 if that hash differs from the record's, if the
record has no tie or if a choice for it exists, so the choice never changes. Running it
is the owner's own act, which the agent never performs (spec FR-043). Every selection record stays
as the script wrote it, and the design rationale's Alternatives chapter cites each with its tie
choice (spec FR-034). A choice binds only the record whose hash it names, so a tie in a later
record needs a new choice, and the Review & Approval row "Selection tie", or "Selection tie <k>" for
`selection-<k>.json`, holds the date, the choice and both records' SHA-256. If a later record
selects another candidate, the security-target review and every later review are held again for it,
each in a row of its own; if it selects the same one, the reviews held stand for what did not change
(spec FR-043).

## 10. Size profile and security target (`security-target/`)

`parameters.json`, a fixed-name file (introduction) written by `scripts/mode_limits_v3.py` beside
`limits.json`, one row per supported size, each from the variant table and the design document's
layout, with FR-010's checks computed by that script, which exits 1 on any violation at a claimable
size. The script reads the variant table, the layout and the limits from three tables of the design
document, each a Markdown table with fixed columns in a section of its own, which the chapters' test
checks: the chapter "Permutation"'s section "Variant table", one row per variant with its ID, n, w,
b, c, r, R and status, and the chapter "Mode"'s sections "Layout", which lanes form the rate part
and which the capacity part at each size, and "Limits", each limit in calls of Π and in bits at
every claimable size, with u and the two ways of choosing nonces; it exits 2 if a table is missing,
appears twice or holds a row it cannot read, and its runs compare `design_sha256` (section 1). The
chapter "Security target"'s parameter table and output limits restate this file and `limits.json`,
and a test compares each with its file row by row and value by value, the key entropy, the reachable
secret state, c, r, R and the bound among them, failing on any difference (spec FR-010, FR-034;
RAT-085). Each row holds:

- `n`, `w`, `lanes_per_node` (2), `b`, `c`, `r`, `variant_id`, and `R`. A research variant's R
  carries its reason: the round rule's value where its inputs exist at that variant, or a
  reduced count chosen for a stated test and marked as reduced; the variant ID carries R.
- `key_entropy_bits` and `nonce_bits`: c and c/2, so 256 and 128 at every claimable size, and 0
  for a keyless variant (R14). `keyed_variants` names each size's keyed variants: the production
  variant at every claimable size, and at 2×2, and at a supported 3×3, at least one keyed reduced
  variant, such as `n2-w16-R8-c64` with an 8-byte key and a 4-byte nonce, each with c a multiple of
  64 and r = b − c a multiple of 32, a supported 3×3's at w = 16 or 32 (spec FR-018; R14; HW-093).
  Keyless variants are listed as permutation-only.
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
  "research variant, no claim", and it is never compared with s = 128 or reported as a strength.
  `bound_bits` is the least of the figures FR-010's checks give, each the cost of a generic attack
  in bits: `key_entropy_bits` (k); half of `reachable_secret_state_bits` at the boundary where it is
  least; k − log₂ u at `limits.json`'s `u`; half of `key_entropy_bits` and `nonce_bits` together;
  c/2; and k/2 (T11, single-target key search only, FR-008), a term below zero counting as zero and
  the checks of output volume and of nonce reuse giving no figure. `bound_terms` holds each term by
  name and the term that sets the least, computed by code, and a test recomputes the least from the
  terms and each term from the row's other fields. A keyed reduced variant, such as `n2-w16-R8-c64`,
  takes the same rule at its own k, nonce bits and c, and a keyless variant, with k = 0, takes
  `none` (spec FR-009, FR-010; SEC-090).
- The generic-bound checks of FR-010, at s = c/2 for a keyed reduced variant, each a check that
  can fail, with 0 violations required at every claimable size: output volume (every limit at
  most what the theorem allows at ε, R9's doubling check), multi-target search, key plus nonce,
  capacity, quantum search (T11 as single-target key search only, FR-008: k/2 ≥ s, which holds with
  equality and no margin at k = 256 and s = 128, recorded as met with equality), and the
  stated behaviour on nonce reuse, with its test.
- At claimable sizes, `throughput_implied`, in 32-bit words per second at 200 MHz (FR-026): computed
  from the per-call rate r/(P·R + ⌈r/i⌉ + t_s + t_o) bits per cycle, on FR-020's formulas, where
  i is the output interface's `interface_bits_per_cycle` and t_s and t_o,
  recorded as `start_tree_latency` and `output_tree_latency` in cycles, are the
  start tree's latency and the output tree's where it is not overlapped,
  since the next call starts only after the consumer has taken the block
  (FR-025), with r/(P·R) and i reported beside it; per stated request size (the 2¹⁹-bit cap and
  4,096 words), counting each request's output calls, its forget call, the trees' latency and the
  clearing at the request's end, with instantiate's calls spread over a stated
  number of requests per instantiation; and `rate_before_forget` beside it as
  an upper bound (R5). Beside them, `throughput_goal` (10⁸; R5), which is reported and never an
  eligibility rule.

`limits.json`, a fixed-name file too: `epsilon` (2⁻⁶⁴), `N` (2¹²⁸), each theorem the mode chapter
uses (the paper, cited by its `fetched` entry in `downloads.json` with that entry's SHA-256, the
theorem's number and page, `verified` or `unverified`, and each precondition with the mode-chapter
section that meets it, marked met or not), which `design_freeze.py create` reads (section 13):
`mode_limits_v3.py` refuses `verified`, exit 2, without such an entry or when the file on disk has
another SHA-256, and the marks count only once the security-target review row, which reviews the
chapter by its version, reads Approved, `create` reading them as `unverified` until then: that
version is the set the spec's notes under the Review & Approval table define, the SHA-256 of the
design document's chapters "Security target" and "Mode", of `rationale.md`'s chapters of
those names (RAT-086) and of this file and `parameters.json`, with the design
document's version read, so that a mark set after the review counts only once
a "Security-target review <k>" naming the changed set reads Approved; the
limits per instantiation, per request and per key, each in calls of Π, the theorem's unit, which is
primary, and in bits at every claimable size (a request of n bits takes ⌈n/r⌉ output calls plus one
forget call, and instantiate's calls are stated); every other online quantity the bound counts with
its limit; `u`; the two allowed ways of choosing nonces, and for random nonces the collision term
q²/2¹²⁹ in the bound and the random-nonce instantiation limit, at most 2³², which the model applies
to every key whatever its nonces (R9); the bound at the limits and the doubling check of R9.

## 11. Vectors (`vectors/phyco-v3/`; FR-036, FR-054)

| File | Content |
|------|---------|
| `pi_<variant>.json` | 16 inputs and their Π and Π⁻¹ outputs, as lanes in hex in the design document's order; the state after every phase of every round for the first 4, as `pi_trace` returns it |
| `mode_<variant>_dev<i>.hex` | header line, then 10,000 lines of `%08X`, as the `phyco-v2` vector files |
| `digest_<variant>.json` | SHA-256 of the first 2²⁰ output words for key and nonce 0, in requests of 4,096 words, over FR-015's canonical serialization as 4·2²⁰ raw bytes, not over the `%08X` text lines |
| `selftest_<variant>.json` | per claimable size and per keyed research variant (spec FR-018; HW-095), the start-up self-test's inputs and every expected block, whole (spec FR-059): key and nonce 0, the empty personalization string with its length word, k, read from the design document's table of k, in the chapter "Hardware structure"'s section "Self-test", with the structure that set it and the least k that the generator's run gives, which a test computes again and checks the file's k against, with the table's, equal unless a structure the design document names, with its reason, raised it (spec FR-034, FR-059; HW-084; REP-097), and the request of k whole blocks (k·r bits), and, where the design has a reseed, reseed input 0 of research R3 with its length word, held among the self-test's constants and fed as the host would (HW-082), and the second request of k whole blocks, written by `gen_vectors_v3.py` in the same generator run as the vectors, from a `ResearchDuplex` object of its own run through the self-test's call sequence alone, each request with its forget call, so that its expected blocks are those that `Generator` and the hardware's self-test compute (spec FR-059; REP-096); `phycoweb/selftest_v3.py` is copied from these files (HW-077) |
| `constructed_<variant>.json` | per edge state: name, `construction`, an object, written by the format rules, that holds the list of calls for a state the normal calls reach or, for a state set by `ResearchDuplex.from_state`, its `lanes` and `counters` as that call takes them (model contract, Research duplex), so that `gen_constructed_v3.py --check` regenerates each vector byte for byte and FR-054's testbench loads the same lanes and counters (REP-087), whether the normal calls reach it from a development key within the number of calls of Π the design document's list states or it is covered only from a chosen state, set by `ResearchDuplex.from_state` (REP-078), inputs, outputs |
| `constants_n<n>_w<w>.json` | the constant table of one supported (n, w), as `phycoweb/constants_v3.py` holds it (R15), with the count of words skipped by the reading order and every repeat of a class where one call needs more constants than there are aperiodic classes (FR-023) |
| `MANIFEST.json` | the sidecar, append-only, its earlier entries never changing: one entry per generator run, citing the `record_id` of that run's `generator-run` record (below), which a generator's `--reproduce` names (cli contract), with the command (script and arguments, relative to the repository root), the interpreter, the model's SHA-256, the platform, the measured speed (calls of Π and words per second) and the generation time; `--check` does not compare it, and the freeze hashes it with the vectors, as the record of the runs that produced them (section 13); after the freeze a generator runs only with `--check`, `--reproduce` or, for `gen_constants_v3.py`, `--exploration`, which write their records under `reports/004-crypto-architecture-v3/`, an exploration run's beside its table (below), and never to the sidecar |

The header of a mode vector file reads, for example:

```text
# model=phyco-v3 variant=phyco-v3/n4-w32-R<R>-c256 key=dev/0 nonce=dev/0 pers=empty requests=1,7,64,1000 schedule=cyclic-truncated count=10000 format=u32-hex
```

The header's fields come in this fixed order, each `key=value`, separated by single spaces.
`schedule=cyclic-truncated` says that the requests cycle in the order given and the last takes what
is left: nine cycles of 1, 7, 64 and 1,000 words, then 1, 7, 64 and 280 words for 10,000 (research
R8). Generated files hold only deterministic content, under the format rules of the introduction,
so that `--check` can compare them byte for byte; everything that differs between runs or
platforms goes to the sidecar `MANIFEST.json` (R8). In the file names above, `<variant>` is the
variant ID with `/` replaced by `_`, for example `mode_phyco-v3_n4-w32-R<R>-c256_dev0.hex`, and
every file sits in the one directory `vectors/phyco-v3/`, with no directory per variant.

**Generator runs** (FR-061). Each run of `gen_constants_v3.py`, `gen_vectors_v3.py` or
`gen_constructed_v3.py` writes, beside its sidecar entry, a `generator-run` record,
`generator-runs/<record_id>.json`, with the common fields of section 1 and each written file's path
and SHA-256, which its reproduction compares in memory (section 1, Reproduction); the sidecar is not
among those files: its entry, appended once the record is written, cites the record's ID, and the
freeze hashes the sidecar with the vectors (section 13; REP-092). The exception is
`gen_constants_v3.py --candidate ID --variant VARIANT`, run before the freeze: it writes that
candidate's table for the variant (n, w, R), with each call type's stream where its streams are
distinct, as `research/004/candidates/<id>/constants/<variant>.json`, `<variant>` being the variant
ID's part after the design, and a `generator-run` record holding each table's path and SHA-256 and
each check's verdict, and adds no sidecar entry; after the freeze it exits 2 (research R15). The
other exception is `gen_constants_v3.py --exploration N W`, run before or after the freeze: it
writes the table of an (n, w) outside the supported sizes as
`research/004/exploration/constants_n<n>_w<w>.json` and, beside it, its check record, a
`generator-run` record with `exploration` true and each check's verdict, adds no sidecar entry,
writes no frozen file and no evidence, and refuses a supported (n, w), exit 2 (research R15).

**Generator checks** (SC-009). `--check` writes a `generator-check` record,
`generator-checks/<record_id>.json`, with the common fields of section 1 (FR-061), each generated
file's path and SHA-256 and the verdict `match` or `differs`, computed by code (FR-065). SC-009's
evidence is each generator's pair of such records, one per platform, which quickstart M1 to M3 and
the final report cite.

**Order of generation** (FR-036, FR-059): four steps, each generator's `--check` passing in this
order. (1) `gen_constants_v3.py` writes the constant tables. (2) `gen_vectors_v3.py` writes the
vectors through `pi` and `ResearchDuplex`, which runs no self-test, and also
writes, in the same generator run, from a `ResearchDuplex` object of its
own run through the self-test's call sequence alone (spec FR-059; REP-096),
each claimable size's and each keyed research variant's `selftest_<variant>.json` (HW-095), the
self-test's inputs and every expected block, whole, and `phycoweb/selftest_v3.py`, copied
from those files (spec FR-059; HW-077); it reads each one's k from the design
document's table of k, in the chapter "Hardware structure"'s section "Self-test",
and computes the least k from its self-test run, exiting 2 if that table is
missing, appears twice or holds a row it cannot read and 1 if the table's k is
below the least or above it with no named structure and reason, its runs and checks
comparing `design_sha256` (section 1; spec FR-034, FR-059; REP-097). (3)
`Generator` imports `phycoweb.selftest_v3` and runs the self-test from it, in
`tests/test_model_v3.py`'s named test `test_generator_selftest`, which builds a `Generator` and runs
that self-test; `gen_constructed_v3.py` and its `--check` run it first, on the platform where they
run, exiting 2 unless it passes and recording its result in the record each writes, so that SC-009's
pair of check records for step (4) shows that step (3) passed on each platform (REP-086). The model
imports that module inside `Generator`'s constructor only, so `pi`, `pi_inv`, `pi_trace` and
`ResearchDuplex` import without it and step (2) runs before it exists; a `Generator` built before
then fails its self-test and leaves no object (model contract, Module rules).
(4) `gen_constructed_v3.py`, once step (3)'s self-test has passed, writes the constructed-state
vectors, running Π, Π⁻¹ and the mode through `pi`, `pi_inv` and `ResearchDuplex` only, its research
path to chosen states, `ResearchDuplex.from_state`, included, so that every generator and module it
reads has passed its check before it runs (REP-077, REP-078). Tests check that
`Generator` reproduces the vectors and that `selftest_v3` equals them, and the freeze hashes
`selftest_v3.py` with the vectors and the three generators (section 13).

## 12. Baseline archive (`baseline/phyco-v2/MANIFEST.json`; FR-042)

As `baseline/float-v0/MANIFEST.json`: `created_utc`, `git_head`, and `files`, each with
`archive_path`, `source` (path and commit), `sha256` and `note`. The archive holds
`phycoweb/model_v2.py`, `phycoweb/lut.py`, `fast/phyco_stream.c`, `fast/lut_table.h`,
`specs/002-core-dynamics-redesign/design.md` and both `vectors/phyco-v2_*.hex`. A test checks each
copy against its manifest hash and its live source (SC-012).

## 13. Design freeze record (`freeze/freeze.json`; FR-043)

- **Hashes**, each with its kind (`raw` or `lf-normalized`, R16): the design document (with its
  version, from its header, which holds its title, the disclaimer and the version line and
  nothing else, `create` exiting 2 on any other header line, the record naming that version 1.0,
  with `reviewed_version`, the header's 0.<k> that the owner design review read and that
  the record hashes, so that no file changes at or after the freeze and the
  reviewed text is the frozen text; spec FR-034; RAT-080); `rationale.md`, versioned with it, its
  header holding its title, the design-form disclaimer and the same version line and nothing else,
  `create` exiting 2 on any other header line there or while its version line differs from the
  design document's, a committed change to either file making the next 0.<k> in both headers (spec
  FR-034; RAT-087), whose SHA-256 the owner design review's row with the highest k names
  beside the design document's version and the selection record and `create` compares with the file
  at HEAD, exiting 2 while they differ, so that a change to `rationale.md` after the review's
  approval counts only once an "Owner design review <k>" naming the changed file reads Approved, as
  a change to the design document does (spec FR-043; RAT-083); `phycoweb/model_v3.py`;
  `phycoweb/constants_v3.py`, with its table per supported (n, w), which `create`
  checks, exit 2 otherwise, to equal the selected candidate's tables at each
  supported (n, w) and its final R (research R15); `phycoweb/selftest_v3.py`
  (section 11); every vector file, including the constructed-state vectors, the constant tables
  beside them and the sidecar `MANIFEST.json`, frozen with them as the record of the runs that
  produced them (section 11); the scripts that generate the constants and the vectors,
  `gen_constants_v3.py`, `gen_vectors_v3.py` and `gen_constructed_v3.py` (REP-077); the selected
  operation list; `research/004/ir.py` with its tools; and the scripts that compute verdicts:
  `evidence_v3.py`, `round_rule.py`, `d4_choice.py`, `mode_limits_v3.py`,
  `validate_tool.py`, `fut_sec8.py`, `recheck_004.py`, `protocol/devinputs_v3.py` and
  `protocol/evidence.py`; the freeze's code, `protocol/design_freeze.py`, and its command,
  `scripts/design_freeze.py`; every module of the repository that a frozen script imports, directly
  or through another module, `protocol/candidates.py` among them and, where a frozen script imports
  them, the log writers `protocol/changelog.py` and `protocol/provenance.py`, which `create` lists
  from the scripts' imports, so that the re-check runs only code whose hashes
  match the freeze and a change after the freeze to a module on the path of a
  verdict makes `validate` exit 1 (REP-091); and the security target's files
  `parameters.json` and `limits.json`, with each theorem's status from `limits.json`,
  every one of which must be `verified`, with each precondition marked met, marks that count only
  under an Approved security-target review row naming the set the record freezes, the SHA-256 of the
  design document's chapters "Security target" and "Mode", of `rationale.md`'s chapters of those
  names (RAT-086) and of these two files, which `create` compares item by item
  (section 10; research R10).
- **Round count**: per claimable size, R with every input of the round rule, and every evidence
  record behind R, by ID and by SHA-256.
- **Logs**: the last `seq` and line SHA-256 of the candidate log, the provenance log and the
  protocol change log.
- **Selection**: the `variant_map` of the candidate log's latest `selected` entry (section 3), with
  the operation list's SHA-256; `create` exits 2 unless that entry cites the latest selection
  record, with that record's tie choice where there is one, and names the candidate that record
  selects, an earlier `selected` entry standing as a decision that a later record superseded
  (section 9; spec FR-043; ANA-081), and unless every variant ID of its `variant_map` carries the
  final R that the candidate's `round-rule.json` gives at its size (ANA-085).
- **External review**: the row of the external design review's family that `create` reads, the one
  with the highest k among the rows that name the latest selection record, its value, done or not
  arranged, the selection record it names, and for done the review package's manifest SHA-256 and
  the design-document version it names, with each version 0.<k> since, and the files each changed,
  where the design document or `rationale.md` changed after that review (RAT-087),
  and each review done for another candidate, cited for the candidate and
  the version it read only, as the final report states them (spec FR-043, SC-013; SEC-078).
- Tool versions; `git_head`; `owner_commit`, the hash of the freeze's step (1), the owner's commit
  of the feature files, which follows the commit that records the owner design review's approval in
  its row with the highest k, `create` exiting 2 unless it is HEAD (spec FR-043;
  PRO-070), and also while `check_claims.py` reports a finding at HEAD (SEC-084);
  `git_dirty`, which must be false; `draft_sha256`, written by `create`: the SHA-256 of the record's
  canonical JSON without that field and the approval fields, `record_id` included, which `create`
  computes first and `approve` keeps, kind `canonical` (introduction; REP-083, REP-092), the
  approval fields being `freeze_status`, `approved_by`, `approved_utc`, `approval_wording` and
  `approval_confirmed`, so that `validate` recomputes the same hash over the approved record and
  exits 1 only if anything else changed (REP-084); and `freeze_status`, `draft` until the owner
  approves and then `approved`, which `approve` sets and `validate` reads, the approval state held
  apart from the common `status`, which code computes as every record's, `pass` once each
  of `create`'s checks holds, as it must for `create` to write the record
  (section 1; REP-093). `design_freeze.py approve --by NAME --wording TEXT`,
  run by the owner, prints `draft_sha256` and refuses unless standard input is an interactive
  terminal and the owner types its first 16 hex digits; it then changes `freeze_status` to
  `approved`, adds `approved_by`, `approved_utc`, `approval_wording` and `approval_confirmed` (the
  digits typed), and changes nothing else.

The freeze runs in five steps (FR-043): (1) the owner commits the feature files, the
owner's next commit after the one that records the owner design review's
approval, the agent committing no file of this feature from the first commit that
records an owner design review's approval to the feature's end, plan phase 9 included, a later row
"Owner design review <k>" and the change it reviews included, which the owner commits (PRO-070;
SEC-084; PRO-072); where the owner must commit a row on its own between that approval and this step,
"Environment record <n>" after a Windows or WSL update or "Log repair <n>", the owner design review
is held again in "Owner design review <k>", naming the same versions where nothing else changed, and
step (1) is then the owner's next commit after the commit that records that
row's approval (PRO-072); (2) `design_freeze.py create` runs with `git_dirty`
false, records that commit as `owner_commit` and writes the record with `freeze_status` `draft`;
(3) the owner runs `design_freeze.py approve --by NAME --wording TEXT`; (4) the owner commits the
record; (5) `validate` exits 0. Steps (1), (3) and (4) are the owner's own acts, which the agent
never performs (spec FR-043). Before step (1), the agent writes the owner design review's review
entries with `provenance.py review`, on the owner's word, after the commit that records that
review's approval, leaving them in the working tree, so that the owner's commit of step (1) holds
them and the frozen provenance log carries the status FR-034 keeps there, and `create` reads the
provenance log at HEAD and exits 2 while an AI-drafted section of the design document or of
`rationale.md` has a latest entry that is not a review entry reading `accepted`, or one that names a
row other than its review's with the highest k, the security-target review's for the design
document's chapters "Security target" and "Mode" and the owner design review's for every other
section, `rationale.md`'s chapters of those names among them (spec FR-034, FR-043;
RAT-082; RAT-086). Dirty means a tracked file modified or an untracked file not
ignored; ignored files (the locks, the local-only outputs under `data/local/`) do not count, and
local-only outputs are in the record by SHA-256 anyway. `validate` recomputes `draft_sha256` and
every hash and checks the format rules; it exits 1 if anything but the approval fields changed or a
hash does not match, and 2 while `freeze_status` is `draft`. After approval the frozen files must
not change: a fix to a verdict script is a new file, so that the re-check (FR-065) runs the code
that produced the verdicts. `protocol/evidence.py` refuses, exit 2, to write
over a fixed-name file the record pins, `parameters.json`, `limits.json` and
the selected candidate's `round-rule.json` among them, and after the freeze
`mode_limits_v3.py` runs only with `--reproduce`, whose record goes under
`$REP/reproductions/`. The approval status of the design document and the rationale stays outside
the frozen files (FR-034). The record is of kind `freeze` (section 1), with the common fields, those
of a run holding `design_freeze.py create`'s and `inputs` and `outputs` `none` (section 1, Kinds
kept under a name of their own; REP-093): `create` writes it through `protocol/evidence.py`, its one
change, the approval, goes through `protocol/design_freeze.py`, and `design_freeze.py` has no
`--reproduce`, since the record holds the owner's commit and approval, which a later run cannot
regenerate (research R16; REP-085).

## 14. Provenance record (`provenance.jsonl`; FR-067)

One line per file drafted or repaired with an AI tool, and per section where a file is
drafted in parts: `seq` and `prev_sha256`, chained as the candidate log is
(section 3: the previous line's UTF-8 bytes as stored, final LF included), `path`, `section`,
`sha256` and `sha256_kind`, `tool` and `model`, `session`, `date_utc`, `task_id`,
`environment`, the platform's environment record in force when the entry was
written, named as in section 1 (REP-082), `review_status`, which is `pending`,
`accepted` or `changes-requested`. An entry's `sha256` is over the named file's
bytes, LF-normalized for an existing `text=auto` file such as security.md or README.md and raw
otherwise, as research R16 hashes, with `sha256_kind` (`raw` or `lf-normalized`) beside it; a
section's text runs from its heading line, included, to the line before the next heading of the same
or a higher level, or to the file's end, each line with its final LF, taken from those bytes, and
`section` names its heading as it stands (REP-079); a heading is an ATX heading outside fenced code
blocks, as CommonMark reads it, that is, one to six `#` at the line's start, after at most three
spaces, followed by a space, a tab or the line's end, and a heading text that occurs more than once
in one file is named in `section` by the texts of the headings that enclose it,
from the highest level down, and its own, joined by " > ", so that `section`
names one section (REP-088). A review is a new entry for the same `path` and
`section`, with `follows`, the `seq` of the entry it follows, and `sha256`,
the SHA-256 of the section text reviewed, computed the same way, with its kind, and with `reviewer`,
the role and name of who reviewed, the owner for the security-target review and the owner design
review and an outside reviewer by name where one took part, never an AI tool or session (spec
FR-064); `row`, the Review & Approval row by name and k; `reviewed_sha256`, the SHA-256 that row
names; and `owner_word`, the owner's explicit word for the entry, quoted with its date, on which
alone the agent runs `provenance.py review`, as for a row's approval (RAT-077). The latest entry for
a path and section gives its status, and no entry changes, and the final report's record of who took
each role of security.md §16.2 is computed from the review entries (spec FR-064; RAT-077). A chapter
of the design document under review carries no mark in the file: its status is
its entries' `review_status`, `pending` from its drafting, with its Review & Approval row, and the
security-target review adds a review entry for each chapter it covers, "Security target"
and "Mode", naming its heading as `section`, so that the file the review
read is the file `design_freeze.py create` compares (spec FR-012, FR-034;
RAT-068). The review of an evidence record is an entry that names the record's ID
and SHA-256, the record's `reviewer` staying as written (section 1). Every append takes
`data/log-append.lock` and checks the chain first (R16), and a broken chain is repaired as in
section 3, its `repair` entry holding the fields that section gives it. Its one writer is
`protocol/provenance.py`, run as `scripts/provenance.py add` for an entry and `review` for a review
entry (cli contract), and as `scripts/repair_log.py` for the `repair` entry, which it admits
while the spec's row "Log repair <n>" reads Approved at HEAD, as the one
append to a broken chain (section 3; PRO-076); it refuses, exit 2, appending
nothing, an entry with a field of its kind missing, a `section` that names no section or more than
one (REP-088) or a `sha256` or `sha256_kind` that is not that of the named file, the
named section's text or the named record, each computed by the writer as
above (REP-079), or a review entry whose `row` does not read at HEAD, with its `reviewed_sha256`,
the decision the entry records, Approved for `accepted` and Declined for `changes-requested`, or
whose `reviewer` names an AI tool or session (RAT-077), or a review entry while the named file, or,
where the row names a chapter by its own SHA-256, the chapter, does not have at that moment the
SHA-256 that the row names for it, while its `follows` is not the latest entry for that path and
section, or while the section's text differs from the text whose `sha256` that entry holds, so that
the status the latest entry gives is that of the text the reviewer read, a section changed
after its last entry getting an `add` entry before its review (RAT-081). The
entries for `phycoweb/model_v3.py` and `tests/v3_reference.py` must name
different sessions (FR-057). A known result this feature writes itself (section 7) has an entry of
its own, with its SHA-256, before the first entry of the tool it validates. Each tool's second known
result (section 7) has an entry of its own before the tool's first validation, with its source: a
second published value from research R19's approved papers (paper, table and value), or a
self-written result with its SHA-256, entered before the tool's first entry. `section` names a part
of a file: each AI-drafted section of the rationale has its own entries, to which the owner design
review adds a review entry for each, so that the frozen text carries no status (FR-034). The owner
design review's review entries, for every AI-drafted section of the design document and of
`rationale.md` but the design document's chapters "Security target" and "Mode", whose
entries the security-target review adds, `rationale.md`'s chapters of those
names taking the owner design review's entries as every other section of
`rationale.md` does, though the security-target review also reads them (RAT-086), are
written by the agent on the owner's word after the commit that records that
review's approval and before the freeze's step (1), which holds them, and `design_freeze.py create`
exits 2 while the latest entry of such a section is not a review entry reading `accepted` that names
its review's row with the highest k (section 13; RAT-082).

Files drafted or repaired before the log exists are in FR-067's scope: the spec, the plan, research,
this data model, the contracts, the quickstart, the checklists and checklist-choices.md, drafted and
repaired with an AI tool over several sessions before any task existed, and the files of plan phase
1 written before the log, and every file outside the feature directory that this feature's sessions
changed, as `git log` from the spec's first commit, 801c6d7, shows, the log read on 2026-11-02
listing `research/004/place_check.py` and `.gitattributes`, entered whole, and
security.md, the constitution, `.specify/memory/constitution.md`, whose amendment to
1.3.0 an AI session drafted for the owner's approval, and the strategy note
`research/security/crypto-redesign-strategy.md`, entered per section changed, as a file drafted in
parts is (REP-089). A file entered per section changed gets one entry per section of the deepest
heading that holds a changed line, its text as above (REP-079), and none for a section only because
a subsection of it changed, so that the level-1 section, whose text is the whole file, gets an entry
only for a changed line outside every subsection, security.md's version line among them; a commit
changed a section when its diff adds, removes or changes a line of that section outside its
subsections, its heading line included; a section whose heading's text changed keeps one series of
entries, named by its heading as it stands, `drafted_from` and `drafted_to` counting the commits
under its earlier texts; and a section that this feature's sessions removed is entered under the
section that held it, with a field `removed` naming the removed heading and the commit that
removed it (REP-095). Right after the log's creation, before any other entry,
`provenance.py add` writes one entry per such file, or per section changed of a file entered per
section, holding `sha256` and its kind (REP-079) of the file or section as committed then,
`date_utc` as the writer adds it, `drafted_from` and `drafted_to`, the dates of the first and
last commits from 801c6d7 on that changed the file or the section, never an
earlier feature's (REP-089), `session` "several, not recorded" unless one is
known, `tool` and `model` as known and otherwise "not recorded", `task_id` `none` for a file drafted
before tasks.md existed and the task's ID for a file of plan phase 1, and `review_status` `pending`
until the owner reviews it, a review entry following then. The entries, not the history, state that
an AI tool drafted them, and a later change to such a file gets an entry as any file does (spec
FR-067; REP-080).

## 15. Claim and evidence register (`protocol/claims.json`; FR-069)

One entry per model ID (`float-v0`, `lut-v1`, `phyco-v2`, `phyco-v3`): `claim_level` (L0…L6, the
ladder of security.md §15), `in_progress`, `claim` (`no claim`), `bound` ("at most 64 bits" for
`float-v0`, `lut-v1` and `phyco-v2`, from their 64-bit seed; for `phyco-v3`, below), `evidence`
(record paths, each with its SHA-256), `updated`, `history` (each earlier level with its
dates and the rows it rested on). `phyco-v3` starts at L0 and moves to L1 only when the spec's "L1
recorded" row, or "L1 recorded <k>" with the highest k, reads Approved and names the highest-k row
of the FUT-SEC-8 result review and of the security-target review, both Approved, security.md §15's
L1 gate since version 2.13 (FR-012); `check_claims.py` reads those rows at HEAD and fails, exit 1,
unless `claim_level` is the level they give, L1 while they do and every hash the two review rows
name matches the file at HEAD, the chapter's version item by item and the demonstration record
(SEC-079), and L0 otherwise, security.md §15's line states the same level, `history` holds every L1
that a later row or a change to the reviewed set ended, with its dates, the rows it rested on and
the version reviewed, and `in_progress` reads `none` while no counted trail-bound record exists at
HEAD and names L2 with the first such record's date and "not reached" once one exists (SEC-080), so
that a register below the rows' level, or one missing a lapsed L1, fails
as one above it does; `tests/test_claims.py` covers each case. The agent
writes `phyco-v3`'s `claim_level`, `updated` and `history`, and its line
in security.md §15 with its row in §1.1 (SEC-095), in a commit of its own
right after the owner's commit that sets "L1 recorded" or "L1 recorded <k>" to Approved, or that
adds a later row of either review family, which makes L1 lapse, and never before that commit, save
inside spec FR-043's window, where the owner's commit holds it (SEC-076; SEC-084). It writes the
return to L0 that a change to the reviewed set brings in the commit that
makes the change, or, where an owner's commit makes it, in a commit of its own right after it
(SEC-079), and `in_progress` in the commit that writes the first counted trail-bound record
(SEC-080). Inside the window in which the agent commits no file of this feature, from the first
commit that records an owner design review's approval to the feature's end (spec FR-043),
`protocol/claims.json` and security.md among those files, it writes each of these changes in the
working tree, once the owner has set the row or made the change there, and the owner's commit holds
it, so that at every commit of the window the register gives the rows' level (SEC-084). Plan phase 1
creates the register, with an entry for each model ID and `phyco-v3` at L0 with "no claim",
`in_progress` `none`, `bound` `none` and `evidence` empty (SEC-089), with
`scripts/check_claims.py` and `tests/test_claims.py`, and adds `phyco-v3`'s line at L0 to
security.md §15, with its row in §1.1, "L0; no claim" under "Claim level (section 15)", in
the same phase, in a security.md version of its own (spec FR-051; SEC-081;
SEC-095). The spec approval recorded no level. The claim test checks README's
status block and security.md's own blocks, the one that opens it and the one that closes it, each of
which must say that PhycoWeb-PRNG, every model included, must not be used to generate secrets and
state no level, claim or bound beyond the register's, against the register: the test finds each
disclaimer by its place, README's status block and security.md's opening block as the first block
quote of each file and security.md's closing block as its last, a block quote being a run of lines
that start with ">", and exits 1 if one is missing, and decides each by one fixed sentence,
"PhycoWeb-PRNG, every model included, must not be used to generate secrets.", which each block holds
word for word beside its own text, and by the rule on a level, claim or bound beyond the register's,
the three blocks gaining that sentence in plan phase 1, before the test's first run, security.md's
two in the version that adds `phyco-v3`'s line to §15, and keeping it through spec FR-051's updates
(SEC-092); and a bound or a claim stated in a disclaimer is compared, line by line, with the
register entries of the models the line names by ID, as the level rule reads a line's `claim_level`,
a disclaimer line that states a bound or a claim naming its models by ID and one that names none
being a finding; a bound is beyond the register's when an entry it names holds `none` or a bound
below the line's, `phyco-v3`'s bound being the least of its sizes' bounds unless the line
names a size by its variant ID, and a claim is beyond it when an entry it
names holds "no claim", README's line on the 64-bit seed naming `float-v0`,
`lut-v1` and `phyco-v2` from plan phase 1 (SEC-091); README's block, written
for the models with a 64-bit seed, gains with spec FR-051's update a sentence on `phyco-v3` that the
test checks against its `claim_level` and `claim`, and the two documents keep their own blocks and
carry no copy of the design-form disclaimer, which every hand-written document of this feature
carries (spec FR-068; SEC-086). The test reads security.md §1.1's table row by row, the model ID of
its first column against the register's entries and the leading level and claim of its cell under
"Claim level (section 15)" against `claim_level` and `claim`, a register entry with no row, a row
with no entry or a cell that differs being a finding, and reads every README line outside the status
block that holds "security level", "strength", "claim" or a level by the rules on a bound and a
claim of a disclaimer's line (spec FR-069; SEC-095).

- `claim_level` holds the level whose gate holds at HEAD (L0 or L1 in this feature): a
  later row of either review family, or a change to what those rows reviewed (SEC-079), makes L1
  lapse, the register returning to L0, until "L1 recorded <k>" records it again, and `history` keeps
  each earlier level with its dates, the rows it rested on and the version
  reviewed. `in_progress` is `none` until the first counted trail-bound record,
  and then names a level started and not reached, L2, with that record's
  date as its start date and "not reached" (SEC-080). The claim test checks that no document states
  a level above `claim_level`, flagging every name of a level above it in every scanned line as a
  whole word, `claim_level` being, for each line, the lowest level the register gives the models the
  line names by ID, and L0 where it names none (spec FR-069; SEC-085), and refuses a value outside
  L0…L6.
- `bound` and `evidence`, for `phyco-v3`: `bound` reads `none` until the size profile
  `security-target/parameters.json` exists, and from then on holds, for each claimable size by its
  variant ID, that size's `bound_bits` (section 10), as "at most <bound_bits> bits", with the
  profile's path and SHA-256; the agent writes it in the commit that commits the profile or its
  change, and inside spec FR-043's window in the working tree, for the owner's commit to hold
  (SEC-084). `evidence` lists, by path and SHA-256, the records the entry's level and bound rest on:
  none at L0 before the profile, the profile and `limits.json` once they exist, and at L1 also the
  demonstration record and the files that the two review rows named by "L1 recorded" name. The claim
  test checks both at HEAD, a `bound` that differs from the profile's `bound_bits` at a claimable
  size, or an `evidence` entry missing at its level or whose file has another SHA-256, being a
  finding; `tests/test_claims.py` covers each case (spec FR-069; SEC-089).
- `fut_sec`, for `phyco-v3`: each FUT-SEC requirement's status in the terms of the spec's
  traceability table. FUT-SEC-4 is met by statement (D7); FUT-SEC-5 is met by specification for
  key loading, and by evidence for diffusion through instantiation (FR-029) and research R4's
  first-order related-key and related-nonce differences, and stays open for feature 005's analysis
  (FR-049). L1's "FUT-SEC-1 to FUT-SEC-6 met by specification" (security.md §15) is decided on this
  one reading: the security-target review accepts the section "Key loading" of
  the design document's chapter "Mode" (spec FR-034) and cites the selected
  candidate's evidence records of the measured part, which exist by then, since
  the review is the first step of plan phase 8, after the selection, so nothing remains to measure.
- `allow_list`: the lines the claim test would flag that may stand, each with its path, its text,
  its reason, its writer and the date it was written. The agent drafts each entry, standing phrase
  or line entry; the test counts an entry from the commit that adds it; `check_claims.py` prints on
  every run each entry added since the last ⛔ gate's approval commit, and the owner's review at each
  ⛔ gate lists those entries with their reasons; an entry the owner declines is removed in the next
  commit, the line it passed then failing the test until its text changes (spec FR-069; SEC-087).
  Inside the three disclaimer blocks no entry passes any finding, of a wording rule, of the level
  rule, of the comparison of a bound or a claim or of the fixed sentence, and nowhere does an entry
  pass a finding of the checks of `claim_level`, `bound`, `evidence`, `in_progress` and `history`
  against the rows and the files; the test exits 1 on an entry that names a line of a block or such
  a finding (spec FR-069; SEC-094). The test flags any strength (a number of bits beside "security",
  "strength" or "secure", or a cost such as 2¹²⁸ beside "security") unless the same sentence or row
  carries "target" or quotes a rule. It also flags "random" with its inflections and "high-entropy"
  in every line it scans, since Principle IV forbids describing the generator so beyond what
  committed evidence supports, and "secure", "securely" and "unbreakable", "cryptographically
  secure" and "proven secure" among their uses, in every line too, since FR-050 forbids them and
  SC-015 counts them, and applies FR-069's other rules, "constant time", "related-key
  analysis" and "weak-key analysis" in every line among them. Every rule matches whole words,
  ignoring case, with the inflections FR-069 lists, each root's forms in full (prove, proves,
  proved, proving, proven and provably; comply, complies, complied, complying, compliant and
  compliance; conform, conforms, conformed, conforming, conformance and conformant; approve,
  approves, approved, approving and approval; random, randomly, randomness, randomize, randomizes,
  randomized, randomizing and randomization, with their spellings in -ise; secure
  and securely; unbreakable), a word being a run of letters and digits, so
  "random-nonce", "random_state" and `numpy.random` hold "random" and `os.urandom` does not. "Near"
  and "beside" in its rules mean the same sentence or table row. A flagged line passes only through
  this list, a rule's own text included, one entry per rule line. A standing entry is one fixed
  phrase with its reason and passes only a line that holds that phrase; each form of an allowed use
  has a phrase of its own: "random permutation" and "ideal permutation" in a bound's statement;
  "random nonce", "random nonces" and "random-nonce", as in "random-nonce limit", in the usage rule
  on nonces; "random baseline" in the tests; "an established cryptographic random-number generator"
  in the disclaimer; "hash randomization" in the rule that nothing depends on it; and every other
  form the test finds gets a phrase of its own, listed here with its reason, or a line entry. The
  project's name holds no flagged word and needs no entry. Standing entries also let these lines
  stand: security.md §6's rows, which state a standard's own status; security.md §15's ladder and
  gate rows, which state each level's requirements, the rows' names "L1 recorded" and "L1 recorded
  <k>", `in_progress`'s "not reached" and section 17's sentence that L2 is never `claim_level` in
  this feature, each of which names a level without stating one for a model, the rule lines that
  move a model between levels, in spec FR-012 and FR-069 and sections 15 and 17, passing
  through one entry per rule line (SEC-085); the spec's rule lines of FR-050
  and SC-015, which name the words they forbid, and the negative statements on "secure"
  and "unbreakable", such as README's "**not** cryptographically secure",
  each through a fixed phrase with its reason; the spec's FR-025 sentence on
  zeroization in the model, which says what the model does not promise; the
  mapping chapter's one fixed negative statement, the chapter's only entry
  (FR-030); the spec's negative statements of FR-011, FR-049, FR-059 and
  the section "Context", which say what no artifact may call a model, a test or a review; and, in
  the checklists and checklist-choices.md, which quote the documents they review, a flagged word
  inside a quotation, in quotation marks or backticks, any other flagged line there needing an entry
  of its own (FR-069). A test runs every rule and every standing phrase on
  sample sentences that must and must not be flagged, with one that must be flagged for each form
  FR-069 lists and "phyco-v3 is unbreakable" among them, "phyco-v3 is at L2" and "the design reaches
  L3" among those that must be flagged and security.md §15's ladder rows among those that must pass
  (SEC-085). Inside the mapping chapter, the design document's section headed
  "Slime-mould mapping" up to the next heading of the same level, the rule matches
  FR-030's list, the words for the arguments it forbids among them, as whole
  words, ignoring case, with their inflections, and the test exits 1 if the
  heading is missing or appears twice. Any other flagged line needs an entry of
  its own.

## 16. Review package (`review-package/MANIFEST.json`; FR-063)

Every item of security.md §14, each with its path, `git_head` and SHA-256 with its kind, plus the
known limitations and the unresolved findings, the entries grouped by §14's six items, each group
listing the files that stand for its item as spec FR-063 states them, and the field `unresolved`
listing every finding that no later record, decision or entry closes, a `confirmed vulnerability` or
`unverified hypothesis`, a re-check disagreement, a claim-test finding and an item the final report
leaves open, each with the record, decision or entry it comes from by ID or by path and SHA-256;
`--check` rebuilds that list from the records, and the test of the spec's User Story 5, scenario 6,
fails a §14 item with no file (spec FR-063; RAT-089). An existing `text=auto` file is hashed over
its LF-normalized content and marked `lf-normalized`, so the hash is the same on every
checkout, and no existing file's pin changes (R18). The manifest is a fixed-name file
(introduction): a rebuilt package keeps the earlier manifest as
`review-package/versions/<sha256>.json`. Assembling the package is in scope; sending it is the
owner's action. Once the external design review is done, its Review & Approval row names the
manifest it read by SHA-256, with the design-document version and the selection record it carried,
and `design_freeze.py create` exits 2 while that manifest is neither `review-package/MANIFEST.json`
nor kept under `versions/` (spec FR-043). The manifest is a record of kind `review-package`
(section 1), with the common fields, those of a run holding `review_package.py`'s and `inputs` and
`outputs` `none` (section 1, Kinds kept under a name of their own; REP-093), written through
`protocol/evidence.py` by `scripts/review_package.py`, which assembles the package through
`protocol/review_package.py`; its `--check` rebuilds the manifest from the files it lists and
compares it (cli contract; REP-085).

## 17. State transitions

- **Candidate**: the diagram in section 3.
- **Claim level of `phyco-v3`**: `claim_level` L0 now; L1 once its gate has passed after the
  review of FUT-SEC-8 and of the security-target chapter (FR-012), recorded in the Review & Approval
  row "L1 recorded", which the owner sets and commits and `check_claims.py` reads at HEAD
  (section 15); back to L0 while a review held again is pending, or while a hash the review rows
  name differs from the file at HEAD, until a row "L1 recorded <k>" names the later reviews; the
  agent writes each change of the register that these rows bring in a commit of its own right after
  the owner's commit that changes them, and the return to L0 that a change to a reviewed file brings
  in the commit that makes the change, or right after an owner's commit that makes
  it, and `check_claims.py` checks it against them both ways (section 15;
  SEC-079). While any theorem the mode chapter uses is "unverified" (R10),
  that row reads "blocked" and names the missing paper. L0 needs no row. L2 is never
  `claim_level` in this feature: `in_progress` is `none` before the first counted trail-bound record
  and names it from that record, with its date as the start date and "not reached", written in the
  commit that writes the record (section 15; SEC-080). Every level carries "no claim". The lines of
  this bullet that move the model between levels pass the claim test's level rule through one entry
  per line, and its sentence that L2 is never `claim_level` through a standing entry (section 15;
  SEC-085).
- **Protocol rules**: as pre-registered; a change is an entry of section 18, only in its stated
  stricter direction (FR-044).
- **Design document**: draft versions 0.<k>, the next with each committed change to it or to
  `rationale.md` before the freeze, both files' headers holding it from the same commit
  (RAT-087); the version the owner design review approves; frozen as 1.0, the
  name the approved freeze record gives that version, whose header and `rationale.md` keep its
  0.<k>, which the record holds as `reviewed_version` (section 13; RAT-080). A revision after a
  decline or after the owner design review is logged under the candidate, in a `review-outcome`
  entry, with its old and new version (section 3; ANA-083), and each version a record cites
  is kept as `design-versions/<sha256>.md` (section 1). After the freeze
  any change is a new model ID (FR-028). A record's `design_sha256` names
  the version its run saw, and a reproduction compares it only for the kinds whose code reads the
  document (section 1), so a later draft does not make an earlier record differ.
- **Gates** (spec Review & Approval table): a row's Decision is `_pending_`, Approved or Declined,
  for every gate; also "Not needed" for the "D4 tie", "Selection tie" and "Selection tie <k>" rows,
  done or not arranged for the external design review, and blocked, naming
  the missing paper, for "L1 recorded" and "L1 recorded <k>". A row goes
  from `_pending_` to another of its values, with date and notes; one row
  per download approval. Each guard opens on Approved alone, except that `design_freeze.py create`
  also takes done, naming the manifest the review read by SHA-256, or not arranged on the external
  review's row, the one with the highest k among the rows of its family that name the latest
  selection record, each row naming the selection record it applies to, so that a new selection
  record needs a row of its own (spec FR-043; SEC-078), and `round_rule.py --select` "Not
  needed" on the "D4 tie" row. A Declined gate ends in one of the outcomes the note under the spec's
  table states for it, logged with its reasons, the owner design review's in a `review-outcome`
  entry of the candidate log (section 3; ANA-083), and a gate held again is a row of its own,
  "FUT-SEC-8 result review <k>", "Security-target review <k>" or "Owner design review <k>" (k = 2,
  3, … in order), naming what it reviews by path and SHA-256, the chapter's version being a set of
  hashes (spec, the notes under the Review & Approval table); each guard reads its family's row with
  the highest k at HEAD, and L1 is recorded again in "L1 recorded <k>" once the later review rows
  read Approved. The comparison of the lists "Rows that change the protocol" is confirmed in the row
  "Place check", and one made again over later commits in "Place check <k>" (k = 2, 3, … in order),
  each naming `research/004/place-check.json` by SHA-256; `protocol_change.py create` reads the one
  with the highest k and opens on Approved alone (section 18; PRO-063). The readings that the
  protocol change log's first entries mark `set_aside` are decided, entry by entry, in the row
  "Readings set aside", which `create` reads at HEAD, opening on Approved alone once the row decides
  every such reading (section 18; PRO-079).
- **Evidence status**: `not evaluated` until a record exists; `inconclusive` for a capped search
  or a fired control; `blocked` while a gate it needs is pending; otherwise the computed verdict.

## 18. Protocol change log (`research/004/protocol-changes.jsonl`; FR-044)

One JSON object per line, append-only, chained and locked as the candidate log is (section 3):
every append takes `data/log-append.lock` and checks the chain first (R16).

| Field | Rule |
|-------|------|
| `seq`, `prev_sha256` | as in section 3 |
| `date_utc` | ISO 8601 |
| `rule` | the pre-registered rule changed, by its name in the spec's protocol or its research section; a first entry (below) holds `rules` instead |
| `rules` | for a first entry only: one object per rule its row is listed under, each with `rule`, `old_text`, `new_text`, `direction` and `readings`, the texts being that rule's text, in each place its heading names, at the commit before the row's round was applied and at the commit that completed it, each commit named by its hash; for an entry made from a place the owner confirmed as an entry of its own, one object per rule whose place the edit changed, its `old_text` and `new_text` at the edit's parent and at its commit, each named by hash (PRO-064) |
| `row`, `granularity` | for a first entry only: the row's ID, question and chosen option; and `round`, since a round's rows were committed together, so that a row's own before and after exist in no commit; for an entry made from a place the owner confirmed, `row` none and `granularity` `commit`, with `commit`, the edit's hash (PRO-064) |
| `place_check` | for a first entry only: the result of the writer's comparison, the one `research/004/place-check.json` holds, for the entry's round, or, for an entry made from a place the owner confirmed, for the pair or span that holds its commit (below; PRO-063, PRO-064): the round's two commits, each place whose text changed between them, and the rows of that round listed under its rule, with each place changed by an edit that no row made, its commit and the owner's confirmation |
| `old_text`, `new_text` | the rule's text before and after; for a first entry, per rule in `rules` |
| `reason` | why it changed; for an entry from the checklist answers, its row ID in checklist-choices.md; for an entry made from a place the owner confirmed, the owner's confirmation with its reason, naming the commit (PRO-064) |
| `direction` | `stricter`, in the rule's stated stricter direction, the one spec FR-044's list gives the rule's heading of the lists "Rows that change the protocol" (PRO-066), or `settled`: a case the protocol leaves open, fixed only before any result it affects exists, with the owner's approval, and never looser than any reading of the existing text (FR-044); under a rule whose direction is "no change", `settled`, with its `readings`, whatever the row's kind; `settled` too, with its `readings`, for a rule whose change sets aside a reading of the old text (`readings`; PRO-079); for a first entry, per rule in `rules` |
| `readings` | for a `settled` entry, each reading of the existing text compared, with why the new text is no looser than it, or, for a reading that the new text sets aside, admitting what that reading refuses, the mark `set_aside`, with the case under which the old text fails, every candidate, every correct tool or a write the protocol needs, and the owner's decision on it, the change kept, with the owner's reason, as a change spec FR-044's words do not allow, or the old text restored (PRO-079); empty for a `stricter` entry, which sets aside no reading |
| `approver` | the owner, with the approval's date, and `approval_confirmed`: the first 16 hex digits of the approved SHA-256 that the owner typed at the approval step (below), `approver` and `prev_sha256` being left out of the hash it confirms (REP-094); checked for every entry, the first entries' together and each later one's alone, the last line included, by the guard "Protocol log", and by `recheck_004.py`, which applies only entries whose digits match (PRO-077) |
| `environment` | the platform's environment record in force when the entry was written, named as in section 1 (REP-082) |
| `last_record_id` | the last evidence record ID that existed when the change was made, so that "before any result it affects" can be checked; `none` while no evidence record exists |
| `results_known` | the results known at the time, by record ID, and for each candidate already evaluated, the verdicts recomputed under the new rule (R7); empty while no result exists |
| `repair` | for a `repair` entry only, the one append to a broken chain, which `scripts/repair_log.py` writes through this log's writer while the spec's row "Log repair <n>" reads Approved at HEAD: the break's `seq`, its cause, the broken file's path and SHA-256, the row and what was restored, the same fields as in sections 3 and 14; it changes no rule and holds no `rule`, `rules`, `old_text`, `new_text`, `direction` or `readings`, and it goes through the approval step as every entry does, later records citing the entries after it (PRO-076) |

A change applies to every candidate, those already evaluated included. Every record cites the log's
last entry when its run started (`protocol_seq`, `protocol_line_sha256`; section 1), and
`recheck_004.py` recomputes each verdict under the rules in force at that entry and, where a later
stricter change applies, also under the current rules, listing both; a disagreement under the rules
in force at the entry blocks the candidate and is a tool defect, and one under a later stricter
change is that change's recomputed verdict, recorded in `results_known` (section 1, Re-check
records). The log's first entries, written when it is created, are the answered rows of every
checklist round answered before the log is created, by the lists "Rows that change the protocol" of
[checklist-choices.md](./checklist-choices.md), in round order: one entry per row listed in a
round's list, whose applied change altered the text of a pre-registered rule, whatever its kind,
every Stricter or Settle row among them, and one per place the owner confirms as an entry of
its own, placed as stated below; `protocol_change.py create` reports their
number from the lists, so that no count in the requirements can disagree
with them (PRO-069). A row is listed under every rule whose text its Changes
cell names or its applied change altered (PRO-058). A change made in the texts of a rule's places
alone is a change of that rule: "Records and their hashes" has research R1 and R16, this file's
introduction and sections 1, 13, 14, 16 and 17, the cli contract and the notes under the spec's
Review & Approval table, and "Protocol changes and their directions" spec FR-044, this section and
the cli contract's `protocol_change.py`, each place delimited as spec FR-044 states; the comparison
below reads them over every pair and span, each rule's `old_text` and `new_text`
taken from them, and each round's list names under those headings every row
of its round whose Changes cell names one of their places or whose applied
change altered one (PRO-067). Each list names its round's two commits by hash,
the commit before the round's first applied row and the commit that completed its alignment, so that
a round's alignment commits fall inside its pair, the first two rounds' pairs being the commits that
hold their rows with their other edits, named as such (PRO-061). Before the tasks approval the agent
makes the comparison with `research/004/place_check.py`, committed for it, standard library only,
which reads the named commits with `git show` and writes `research/004/place-check.json`, over each
round's pair and over every span from the plan-approval commit outside the pairs, up to its
`compared_to`, each rule's text compared in each place its heading names, each place's text
delimited as spec FR-044 states; a round with no alignment commit takes as its second commit the
commit of its last applied row, named as such. The results beside each list restate that file, and a
place changed by an edit that no row made, in a round's commits or between two rounds, is recorded
beside a list with its commit, for the owner to confirm at the tasks approval as an entry of its own
or as no change of rule, with the reason, in the Review & Approval row "Place check", which names
the file's SHA-256 (PRO-063). `scripts/protocol_change.py check`, which writes nothing, makes the
same comparison, and a test checks that it gives that file's result over its commits. Before the log
is created its writer reads that row at HEAD and exits 2, writing nothing, while a place whose text
changed has no row of that round listed under its rule and no such confirmation, while its result up
to `compared_to` differs from the file the row names, or while a place changed after `compared_to`,
until the comparison is made again over the later commits and its file confirmed in
"Place check <k>", read with the highest k; each first entry records that
comparison for its round, or for the pair or span that holds its commit,
in `place_check`. Each entry of a listed row holds `rules`, every rule its row is listed under,
with `old_text` and `new_text` per rule: that rule's text, in each place its heading names, at the
commit before the row's round was applied and at the commit that completed it; with the row's ID,
question and chosen option, marked `granularity: round`. Each rule takes `stricter`, in its stated
direction, or `settled`: under a rule whose direction is "no change" the direction is `settled`,
with its `readings`, whatever the row's kind, and a row listed under several rules has a direction
per rule; a rule's stated direction is the one spec FR-044's list gives its heading (PRO-066). A
place confirmed as an entry of its own is a first entry of its own, with `rules` at the edit's
parent and at its commit, `row` none, `granularity` `commit` with `commit`, and its `reason` naming
the commit (the table above): an edit inside a round's pair is recorded beside that round's list,
and its entry follows the round's row entries; an edit between two rounds is recorded beside the
list of the round before it, as ad2c195's is beside the re-run's, and its entry follows that round's
entries, so that the log keeps the order of the commits (PRO-064). The log is
created, and no evidence run starts, only after the owner has confirmed every
list; a row the owner takes out of a list is recorded beside that list in checklist-choices.md with
the owner's reason, that it changed no rule; the shared guard "Protocol log" enforces it:
`protocol/evidence.py` exits 2, writing nothing, while the log does not exist, its chain does
not check, or its first entries, one per listed row of every round answered
before it was created and one per place the owner confirmed as an entry of
its own, do not all hold the owner's `approval_confirmed`, so that every record cites the log's last
entry (section 1), with two exceptions: a `lock-cleared` record and an environment record written by
`owner_record.py environment` are the two kinds it writes while the log does not exist, each with
`protocol_seq` and `protocol_line_sha256` `none`, and once the log exists each cites the last
entry as every record does (PRO-065, PRO-071). The owner's answer to a round
approves its list; a round answered after the log exists adds entries the usual way, proposed by the
agent and approved by the owner (spec FR-044). The entry for the re-run's REP-029, which added the
synthetic counts as class 5, records the protocol's "Development inputs" paragraph before and after,
with four classes and with five. Among them, the
constant rule's values (research R15) and the SHA-256 of its refused list are `settled` entries
written before the first candidate is scored. Every later addition to the refused list is a
`stricter` entry, proposed by the agent and approved by the owner, with the list's new SHA-256. The
spec's Clarifications point to the log. Its one writer is `protocol/changelog.py`, run as
`scripts/protocol_change.py` (cli contract): `create` writes the first entries, after the comparison
above, and `propose FILE` a later entry, and, as `scripts/repair_log.py`, a broken chain's `repair`
entry (the table above; PRO-076), each ending in the approval step below, and it refuses, exit 2,
appending nothing, an entry, or a rule of a first entry, without `direction`, a `repair` entry
excepted, which changes no rule, a `settled` one without `readings`, an entry without
`last_record_id` or `results_known`, and a `repair` entry without its fields (PRO-076). `create`
also reads the spec's Review & Approval row "Readings set aside" at HEAD and exits 2, writing
nothing, while a first entry would hold a reading marked `set_aside` that the row does not decide,
entry by entry, and records each decision, with its reason, in its reading; `propose` shows each
such reading of a later entry at the approval step, which records the owner's decision and reason in
it; and the guard "Protocol log" exits 2 while a reading marked `set_aside` holds no decision
(PRO-079). The first entries that hold one are those of RAT-036, RAT-052, ANA-062, ANA-068,
PRO-065, PRO-068 and PRO-071, from earlier rounds, and of SEC-093, RAT-086,
ANA-087, PRO-076, REP-100 and REP-101, from the tenth re-run, with every other
entry of that kind that the agent finds before the log is created (PRO-079).
Approving an entry is the owner's own act, which the agent never performs (spec
FR-044): the writer's approval step prints the SHA-256 of the entry, or of the first entries
together when the log is created, taken over one canonical JSON array of the first entries in log
order, or over the later entry alone, each entry without its approval field, `approver` whole, and
without `prev_sha256`, both filled once the owner has typed the digits, `approver` with the owner,
the date and `approval_confirmed`, and `prev_sha256` chaining each line to the one before as stored,
a hash of kind `canonical` (section 1, Hashes; REP-094), and appends nothing unless standard input
is an interactive terminal and the owner types its first 16 hex digits; each entry records that
confirmation in `approver`, and the guard "Protocol log" recomputes that hash for every entry, from
the first entries together for theirs and from each later entry alone for its own, and checks each
one's `approval_confirmed` against its first 16 digits, exit 2 otherwise, the last line included,
which the chain does not protect, as a later reader can; `recheck_004.py` applies only entries
whose digits match, and `tests/test_protocol_004.py` covers a first entry, a
later entry and the last line whose digits do not match (REP-094; PRO-077).
After the approval step `create` writes the first entries to a temporary
file beside the log's path and renames it to that path once all are written, so that a writer that
dies leaves no partial log, only the lock, which `scripts/clear_lock.py` removes
(PRO-065). The history cannot show who acted, so the owner's review at each ⛔ gate
lists these approvals since the last gate.
