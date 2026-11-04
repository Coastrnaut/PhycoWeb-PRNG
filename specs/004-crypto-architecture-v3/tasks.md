---

description: "Task list for feature 004, cryptographic architecture and phyco-v3 design"
---

# Tasks: Cryptographic Architecture and phyco-v3 Design

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

**Input**: Design documents from `/specs/004-crypto-architecture-v3/`

**Prerequisites**: spec.md (the owner's spec approval of 2026-11-01, with D1–D10 as clarified),
plan.md (plan approval of 2026-11-01), research.md (R1–R19), data-model.md, contracts/cli.md,
contracts/model-v3-api.md, quickstart.md, checklist-choices.md and the eight checklists, whose
choices from the first run to the tenth re-run are answered and applied. The tenth re-run was the
loop's last round, by the owner's word of 2026-11-03 ("after this iteration, stop the
speckit-checklists loop"), so no checklist runs again without the owner's word.

**Tests**: included. Principle II asks for a bit-accurate reference model with reproducible
automated tests and committed golden vectors, Principle IV forbids weakening an acceptance criterion
to obtain a passing result, which the guard tests of FR-044 hold, and FR-058 lists the model's
tests; plan.md's tests tree names the file of each test a requirement names, and each task below
takes it from there. Within each group, tests come before the code they test. Property tests use
Hypothesis with the deterministic profile of research R17 and skip, naming the open item, until its
wheels are installed (T031).

**Organization**: phase k of this list is plan phase k ("Phases and gates"), so a reference to a
plan phase in the spec, the contracts or the quickstart reads the same here; Phase 0 holds the two
steps before the tasks approval. Phase 1 holds the setup and the foundational writers, plan
phase 1's steps (1) to (9) in their order (REP-081). Stories: US1, FUT-SEC-8 (P1, phase 2, the MVP);
US4's tools, validated in phase 3 before any of their results counts (FR-039); US2, the security
target (P2, drafted in phase 4 and reviewed in phase 8); US3, the permutation, its inverse and the
mode, and US4, the evidence (phases 5 to 7); US5, the reviews and the freeze (phase 8). As plan
phases 3 to 5 state, the operation-list framework `research/004/ir.py` is written at the start of
phase 3, because the known results of research R13 for the structural tools are stated operation
lists that those tools read through it (R11, R13), and phase 5 starts with the cost model; phase 4
writes `scripts/mode_limits_v3.py` and its tests, and the script's first run comes in phase 8,
before the security-target review, since it reads each variant's R from the design document's
variant table (data-model §10), which holds the selected candidate's R only once phase 5 has given
it.

⛔ marks a human review gate (Principle VIII): the agent stops there and waits for the owner.
**Owner** marks a task only the owner performs: `scripts/owner_record.py` (`environment` and
`owner-provided`), `--choose` in `scripts/d4_choice.py` and `scripts/round_rule.py`,
`scripts/design_freeze.py approve`, the approval step of `scripts/protocol_change.py create` (typing
16 hex digits), the owner's commits, freeze steps (1) and (4) among them, and every row of the
spec's Review & Approval table, which the agent writes only on the owner's explicit word for that
row, quoted with its date in the row's notes. **heavy** marks a heavy run (FR-045): it takes
`data/heavy-run.lock`, projects first against its budget row, never overlaps another heavy run, and
starts only on the owner's go-ahead for that run, since the owner's word of 2026-11-01, "No heavy
runs", stands until the owner changes it.

The agent commits locally under the owner's standing authorization (constitution 1.3.0,
Principle IX), after each task or set of related tasks and about every 30 minutes, with no AI
co-author line, and never pushes, tags or publishes; from the first commit that records an owner
design review's approval to the feature's end, it commits no file of this feature (FR-043). Every
download needs the owner's permission for that file, with its name, source, size and licence
(FR-046): the twelve files of research R19 have it, and any other file needs its own row. Exit codes
(contracts/cli.md): 0 success; 1 a failing or non-PASS verdict; 2 refused by a guard, nothing
written; 3 tool or I/O error, a recorded tool defect included.
`REP` = `reports/004-crypto-architecture-v3`; `wpy` = `~/.venvs/phycoweb/bin/python` in WSL, run
from `/mnt/c/GIT/PhycoWeb-PRNG`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel: the task writes no file that another task of its phase writes, and
  depends on no incomplete task
- **[Story]**: US1 to US5 (spec.md, "User Scenarios & Testing")
- Each task ends with the requirements, success criteria and research items it serves.

---

## Phase 0: Before the tasks approval

**Purpose**: the comparison FR-044 asks for before the tasks approval, and the approval itself. No
task of phases 1 to 9 starts before T002.

- [X] T001 Once this file and any change the owner chooses from the `/speckit-analyze` report are
  committed, run `python research/004/place_check.py`, with `--to` at HEAD, which writes
  `research/004/place-check.json` over the commits from the plan approval's commit, `65bcbf2`, to
  HEAD; compare its places with the results written beside each list "Rows that change the protocol"
  in `specs/004-crypto-architecture-v3/checklist-choices.md`; list for the owner every place it
  records as changed by an edit that no row made; and commit the file alone. A later commit that
  changes a place before the protocol change log exists needs the comparison again, confirmed in
  "Place check <k>". (FR-044; PRO-063, PRO-064)
- [X] T002 ⛔ **Tasks approval** (**Owner**), in `specs/004-crypto-architecture-v3/spec.md`'s Review
  & Approval table: review this list with the `/speckit-analyze` findings; review the ticks the
  agent set in the eight checklists on the owner's instructions of 2026-11-01 and 2026-11-02,
  unticking any item not accepted; confirm each list "Rows that change the protocol" of
  `checklist-choices.md`, a row taken out being recorded beside its list with the owner's reason,
  that it changed no rule (data-model §18); set the row "Place check", naming
  `research/004/place-check.json` by SHA-256 with its `compared_to` and each place it records as
  changed by an edit that no row made, confirmed as an entry of its own or as no change of rule,
  with the reason; set the row "Readings set aside", naming each first entry whose `readings` mark a
  reading `set_aside`, with the case under which the old text fails, and deciding each, entry by
  entry, the nineteen readings (RAT-036, RAT-052, ANA-062, ANA-068, PRO-065, PRO-068, PRO-071,
  REP-063, REP-085, SEC-093, RAT-086, ANA-087, PRO-076, REP-100 and REP-101, and those of the
  entries made from ccfd9d1, 5f34d5c, 7a6d0e8 and 57763b5): the change kept, with the reason, as a
  change FR-044's words do not allow, or the old text restored, a restoration being compared again
  in "Place check <k>"; set the row "Tasks approval"; and commit the rows with the spec's Status
  line and the Status of `checklist-choices.md`, which follow the table in the same commit. For this
  review the agent lists the approval commits since the last gate. (FR-044; PRO-063, PRO-079;
  SEC-087; Principle VIII)

**Checkpoint**: tasks approved; "Place check" and "Readings set aside" decided at HEAD, where
`scripts/protocol_change.py create` reads them.

---

## Phase 1: Setup and Foundational Writers (plan phase 1)

**Purpose**: plan phase 1's steps (1) to (9), each after the steps it needs (REP-081): the pins and
ignores, the writers before what they write, the claim register and its test, the first environment
records, the provenance log, the protocol change log, the downloads manifest, the Hypothesis wheels,
the new environment records, the development inputs and the `phyco-v2` archive. No candidate, tool
or key-loading code is written here.

### Step (1): directories, pins, ignores and the line-ending test

- [X] T003 Create the directories of plan.md's source tree as their first files are written:
  `research/004/tools/trails/`, `research/004/candidates/`, `research/004/validation/`,
  `research/004/exploration/`, `vectors/phyco-v3/`, `baseline/phyco-v2/`, `data/local/004/` and
  `reports/004-crypto-architecture-v3/` with the subdirectories plan.md lists; git records a
  directory with its first file, and no placeholder file such as `.gitkeep` is added under `$REP`.
  (FR-053; R16, R18)
- [X] T004 Add to `.gitattributes`, after the line `protocol/*.json text eol=lf` and before the
  `*.hex`, `*.bin` and `*.gz` lines, so that those keep precedence:
  `specs/004-crypto-architecture-v3/**/*.md text eol=lf`, `vectors/phyco-v3/** text eol=lf`,
  `*.mk text eol=lf` and `Makefile text eol=lf`; and, as the last line, `**/build/** binary`, so
  that the C tools' binaries, whose hashes the records hold, read `binary`, under `research/004/**`
  too; keep the pins already there for `reports/004-crypto-architecture-v3/**`, `research/004/**`,
  `protocol/*.json` and `*.gz`. Check with `git ls-files --eol` that every tracked file the new
  lines cover is already stored with LF, `fast/Makefile` among them, so that no frozen file's bytes
  change, with `git ls-files` that no tracked file lies under a `build/` directory, and with
  `git check-attr` that `fast/build/seed_search` and `research/004/tools/trails/build/arx_search`
  read `binary`. (FR-053; R16, R18)
- [X] T005 Add `data/heavy-run.lock`, `data/log-append.lock` and `data/local/` to `.gitignore`, with
  the generic lines `*.o`, `*.obj`, `*.a`, `*.exe`, `*.dll`, `Thumbs.db`, `.DS_Store`, `.vscode/`,
  `.idea/` and `*.swp` (owner, 2026-11-03) and no `*.tmp`, so that the temporary file beside the
  log's path, which `protocol_change.py create` writes before its rename, is never hidden from
  `git status`; and replace the line `build/` with `**/build/**`, followed by
  `!fast/build/seed_search` and `!research/004/tools/trails/build/arx_search`, so that each C tool's
  binary can be committed (research R18). Check with `git check-ignore` that the locks,
  `data/local/` and a file of each generic line are ignored, that every other file under
  `fast/build/` and `research/004/tools/trails/build/`, `fast/build/phyco_stream` among them, stays
  ignored, and that the two binaries are not. (FR-045, FR-053; R16, R18)
- [X] T006 Write research R18's line-ending test in `tests/test_records_004.py`: every path whose
  hash a committed record, manifest or freeze record holds has an explicit `text eol=lf` rule or
  `binary` (`git check-attr text eol`), or its record marks the hash `lf-normalized`, and no hashed
  file starts with a byte-order mark; while no record exists, it checks every tracked file under the
  pinned paths. In the same file, a test checks each `code_sha256` entry of a committed record, a C
  tool's committed binary among them (research R18), against the blob at the record's `git_head`,
  and a second test checks the header of every committed `.gz` file under
  `reports/004-crypto-architecture-v3/`, `research/004/`, `vectors/phyco-v3/` and
  `baseline/phyco-v2/`, which must be the header that
  `gzip.compress(data, compresslevel=9, mtime=0)` writes, feature 003's `.gz` files left out. These
  tests run from this phase on. (FR-053; R18)

### Step (2): the writers before what they write

- [X] T007 Add `DESIGN_DISCLAIMER` to `protocol/disclaimer.py`, holding exactly the design-form
  disclaimer, the block directly under spec.md's title, its lines joined by single spaces;
  `DISCLAIMER` stays byte for byte as it is. (FR-068; R18)
- [X] T008 Write the tests of the evidence writer in `tests/test_protocol_004.py` and
  `tests/test_records_004.py`, before the writer, on temporary directories: record IDs and file
  names (data-model §1, "Record files"); the common fields of FR-061 with `DESIGN_DISCLAIMER`;
  canonical JSON and its `canonical` hashes; `versions/` for fixed-name files; the suffixes allowed
  under `$REP` (`.json`, `.jsonl`, `.md`, `.csv`, `.txt` and `.gz`, and no placeholder such as
  `.gitkeep`); the 10 MB rule, with local-only outputs under `data/local/004/<record_id>/`; and each
  shared guard's refusal, exit 2 with nothing written: Environment, with its one exception, the
  environment record itself, a `lock-cleared` record waiting as every other write does, and its
  approval hash read at HEAD; Committed code, with a source file or a C tool's binary untracked,
  staged but not committed, or modified, and a binary whose `--source-sha256` differs from its
  source's entry in `code_sha256`; Inputs; Operation lists; Heavy runs, with an exclusive create of
  `data/heavy-run.lock` and a held lock named with whether its holder still runs; Protocol log, with
  the two kinds admitted before the log exists and every other kind refused, a first entry whose
  digits do not match, a later entry and the last line whose digits do not match, a reading marked
  `set_aside` with no decision and a `repair` entry whose list differs; Order of sizes, a
  `--project` probe never refused and a run ended from outside not finished; Approvals, the table
  read at HEAD and a working tree that differs refused; Order of US1; Tool validation; Trail tools,
  once the first trail search has started, a tool outside research R12's fixed set or without an
  earlier `re-found` record of its exact hash, for a C tool the pair of its source's and its
  binary's SHA-256, and a search that reached its cap, save research R7's one re-run after a
  recorded tool defect, one ended from outside not having reached it; and Budget, a refusal after a
  probe writing its `projection` record and nothing else, a spent candidate row never refusing a
  reproduction and a heavy reproduction refused once the projections of the runs it will make, after
  any rebuild, do not together fit the hours left in research R7's feature-wide row, its hours used
  being the sum, read from the records, of the time of every `projection` record that names the row
  and of the `hours` used of every other record with `heavy_run` true that charges no candidate, the
  FUT-SEC-8 row's pass excepted. They also test the common part of `--reproduce`, with a mocked C
  tool and build on a temporary repository: the worktree of `git_head` checked against its blobs,
  and the rebuild in a second worktree, the committed binary removed there first, so that a make
  file that would find it up to date compiles it all the same, one run where the rebuild's SHA-256
  equals the committed binary's, a second, compared too, where it differs and has a `re-found`
  record of its own, the outcome `match` only when both runs match, and no second run and a
  difference in every compared field, exit 1 with the record written, where the guards Tool
  validation and Trail tools do not admit the rebuild, whatever the kind of the record reproduced, a
  demonstration, a validation and a cross-check among them, as where it fails; a heavy
  reproduction's exit 2 without `--owner-request`, the request quoted with its date in its record's
  `owner_request`, a light one needing none; exit 2 for a record that holds `ended_outside`; and a
  second run that no longer fits the hours left, the first run's hours counted and the first having
  taken more than its projection, not made, exit 1, the outcome `differs` where the first run
  differs and otherwise the record holding `status` `inconclusive`, with the reason, and neither
  `match` nor `differs`. In `tests/test_protocol_004.py`, FR-045's test also checks that every
  budgeted kind, the FUT-SEC-8 sweep among them, and every script with a worker option takes the
  heavy-run lock, each script as it is added. (FR-038, FR-039, FR-040, FR-044, FR-045, FR-053,
  FR-061; R7, R12, R16; PRO-065, PRO-068, PRO-071, PRO-077, PRO-079; REP-094, REP-101)
- [X] T009 Write `protocol/evidence.py`, the one writer of evidence records (data-model §1; R16):
  IDs and file names, the common fields, `DESIGN_DISCLAIMER` taken from `protocol/disclaimer.py`,
  canonical JSON, the suffix and 10 MB rules, every `.gz` file written by
  `gzip.compress(data, compresslevel=9, mtime=0)` with the SHA-256 of its uncompressed content in
  its record, `versions/` for fixed-name files, the copies under `spec-versions/`,
  `research-versions/` and `design-versions/` of every version a record cites, the `projection`
  record, the shared guards of contracts/cli.md ("Guards shared by every script") with exits 0 to 3,
  each guard that reads the Review & Approval table reading it at HEAD, and the common part of every
  `--reproduce` mode: a worktree of the original's `git_head`, its `code_sha256` checked against
  that commit's blobs, a C tool's committed binary among them, which the reproduction runs from that
  worktree, and its rebuild from that commit's source with its make file in a second worktree, the
  committed binary removed there first, the rebuild's SHA-256 reported only and a second run with
  it, compared too, where that differs from the committed binary's and the guards Tool validation
  and Trail tools admit it, and a difference in every compared field where they do not admit it or
  it fails, output under `$REP/reproductions/<record_id>/<n>/`, the second run's under a further
  `rebuilt/` directory, the design document read from that worktree and checked against
  `design-versions/<sha256>.md`, `--owner-request` for a heavy reproduction, kept in its record as
  `owner_request`, with exit 2 without one, any rebuild made before its projections, which must
  together fit the hours left in research R7's feature-wide row, with exit 2 otherwise, the hours
  left read again before a second run, the first run's hours counted, which is not made where it no
  longer fits, exit 1, with `differs` where the first run differs and otherwise a record of `status`
  `inconclusive`, with the reason, and neither `match` nor `differs`, exit 2 while the environment
  record the original cites is not in force, and exit 2 for a record that holds `ended_outside`.
  (FR-045, FR-053, FR-061, FR-065, FR-068; R1, R7, R16, R18; REP-099, REP-100)
- [X] T010 Write the tests of the hash-chained logs in `tests/test_protocol_004.py`: every append
  takes `data/log-append.lock` by exclusive create, checks the chain to the last line and appends
  one line whose `prev_sha256` is the SHA-256 of the previous line's UTF-8 bytes with its final LF;
  a lock not free within 10 s exits 2, naming it (quickstart P4); a broken chain exits 2, save for
  the one `repair` entry while "Log repair <n>" reads Approved at HEAD and names that log and the
  `seq` of the break; the refusals of the provenance log's and the protocol change log's writers;
  and `create`'s refused-list step, exit 2 while `research/004/refused-constants.json` is missing,
  differs from HEAD or does not parse in R15's entry format, its SHA-256 written as `refused_list`
  in the entry of each row listed under the constant rule, and `propose`'s, exit 2 with nothing
  appended while an addition's `refused_list` differs from the file at HEAD, the list at HEAD does
  not parse in that format, or it drops or changes an entry of the version that the latest
  `refused_list` names, on a stated history in which an entry of that version is dropped and one in
  which a word of one changes, and an entry appended on one in which a word of an entry added since
  that version changes before `propose` runs. (FR-023, FR-041, FR-044, FR-067; R15, R16; PRO-076)
- [X] T011 Write `protocol/provenance.py`, the one writer of `$REP/provenance.jsonl`, and
  `scripts/provenance.py` with `add FILE` and `review FILE` (contracts/cli.md; data-model §14): one
  entry per file or per section, with the tool and model, the date, the task ID and the review
  status; `review` refuses an entry whose `row` does not read at HEAD, with its `reviewed_sha256`,
  the decision the entry records. (FR-067; R16; RAT-077, PRO-074)
- [X] T012 Write `protocol/changelog.py`, the one writer of `research/004/protocol-changes.jsonl`,
  and `scripts/protocol_change.py` with `check`, `create` and `propose FILE` (contracts/cli.md;
  data-model §18): `check` makes FR-044's comparison and writes nothing; `create` runs only while
  the log does not exist, reads the lists "Rows that change the protocol" in round order, the row
  "Place check" with the highest k and the row "Readings set aside" at HEAD, exits 2 while a reading
  marked `set_aside` is not decided or while `research/004/refused-constants.json` is missing,
  differs from HEAD or does not parse in R15's entry format, writes that file's SHA-256 as
  `refused_list` in the entry of each row listed under the constant rule (data-model §18), and ends
  in the approval step, where the owner types the first 16 hex digits of the approval hash it
  prints; `propose` writes one later entry the same way, an addition to the refused list with the
  list's new SHA-256 in its `refused_list`, and exits 2, appending nothing, while the list at HEAD
  does not parse in that format or drops or changes an entry of the version that the latest
  `refused_list` names, which it finds by that SHA-256 in the file's git history, its approval step
  printing the entries added. (FR-023, FR-044; R15; PRO-063, PRO-077, PRO-079; REP-094)
- [X] T013 Write `scripts/repair_log.py --log LOG --approval REF` (contracts/cli.md; R16), which
  appends a broken chain's `repair` entry through that log's one writer only while its row "Log
  repair <n>" reads Approved at HEAD and names the same log and position, with its tests in
  `tests/test_protocol_004.py`; for the candidate log it appends through `protocol/candidates.py`,
  which T076 writes, so that task completes this path and T075 its test. (FR-041, FR-044, FR-067;
  R16; PRO-076, REP-101)
- [X] T014 Write `scripts/clear_lock.py LOCK`, run by the owner or at the owner's request, which
  removes a stale `data/heavy-run.lock` or `data/log-append.lock` only once it shows, in the lock's
  environment, that no process with the lock's PID and start time still runs, and writes a
  `lock-cleared` record, `$REP/locks/<record_id>.json`, and, for the heavy-run lock, the
  `inconclusive` record of the run that died holding it, or FR-053's test's further `projection`
  record, which holds `status` `inconclusive` and says that the test ended there and kept none, the
  `lock-cleared` record naming either, the hours from the time the lock holds to the clearing, that
  record's `created_utc`, being its hours used, or, where the boot time of the lock's environment is
  later than the time the lock holds, a run ended from outside, the hours up to that boot time, the
  record then holding it as `ended_outside` and saying that the outputs the run left under a
  temporary name were discarded unread, with its tests in `tests/test_protocol_004.py`; for a run on
  a candidate it runs `scripts/evidence_v3.py --aborted RECORD` before it removes the lock, which
  T082 writes, so that task completes this path and T081 its test. (FR-041, FR-045; R7, R16;
  PRO-065, PRO-068)
- [X] T015 Write `scripts/owner_record.py` with `environment --platform windows|wsl --by NAME`,
  which checks the running environment against research R1 and the pins of `requirements.txt` for
  that platform and writes `$REP/environment-<platform>.json`, and `owner-provided --known KNOWN_ID
  --value TEXT --source TEXT --words TEXT --by NAME`, which writes an `owner-provided` entry of
  `$REP/downloads.json`; each prints its approval hash, kind `canonical`, writes nothing unless the
  owner types its first 16 hex digits at an interactive terminal, and is tested in
  `tests/test_protocol_004.py`. The agent writes and tests this script and never runs it. (FR-039,
  FR-044, FR-053, FR-058; R1, R19; PRO-068, PRO-071; REP-082, REP-083)
- [X] T016 Write `scripts/downloads.py` with `init`, `approve NAME`,
  `fetched NAME PATH [--pypi-sha256 HEX]` and `not-obtained NAME --reason TEXT`, which keeps
  `$REP/downloads.json` (contracts/cli.md; R19): `init` exits 2 once the manifest exists; `approve`
  writes one `approved` entry for a file outside R19's tables, with the name, source, size and
  licence of its row "Download <n>" and the row's name, only while that row reads Approved at HEAD,
  and exits 2, writing nothing, while no such row names the file or an entry holds the name;
  `fetched` computes the SHA-256 and size from the file, read under `-I` and never run, and refuses
  a size that differs from one R19 or the file's row gives in bytes and, for a wheel, a SHA-256 that
  differs from PyPI's; `fetched` and `not-obtained` refuse a name with no `approved` entry; with its
  tests in `tests/test_protocol_004.py`, each refusal among them, a later copy of a listed file
  refused under the listed name and entered under a name of its own. (FR-046; R19; REP-076)
- [X] T017 Write the claim and evidence register `protocol/claims.json` (data-model §15): one entry
  per model ID, `float-v0`, `lut-v1`, `phyco-v2` and `phyco-v3`, each with its level, its claim or
  "no claim", its `bound` and its `evidence`; `phyco-v3` at L0 with "no claim", `in_progress`
  `none`, `bound` `none`, `evidence` empty and `history` empty; and the `allow_list` holding
  data-model §15's standing entries, each with its reason, its writer and the date. (FR-012, FR-069;
  SEC-089)
- [X] T018 Write a version of `security.md` of its own, with its history entry and its CRLF line
  endings kept: `phyco-v3`'s line at L0 in §15's register and its §1.1 row, "L0; no claim"; the
  opening and the closing block each gaining the fixed sentence "PhycoWeb-PRNG, every model
  included, must not be used to generate secrets." and stating the restriction with "an established
  cryptographic RNG", as README's block does. Edit it with a script that keeps CRLF, never `sed -i`,
  and check the CR count after. (FR-051, FR-069; SEC-092, SEC-094, SEC-095)
- [X] T019 Edit `README.md`, CRLF kept: its status block gains the fixed sentence, and its line on
  the seed names `float-v0`, `lut-v1` and `phyco-v2` and states only their cap at 64 bits, in words
  that no rule flags, the seed's size and the 112-bit minimum standing in README's section 5,
  outside the block, whose lines that FR-069's rules flag are reworded. (FR-069; SEC-091, SEC-092,
  SEC-093, SEC-095)
- [X] T020 [P] Write `tests/test_claims.py` before the script it runs: every case FR-069 names,
  among them the register against README, security.md §1.1 and §15 and the three disclaimer blocks;
  the fixed sentence in each block; a figure that bounds no model; each of the three negated
  phrases, and a negation outside them; a §1.1 row missing, added or differing; the level rule in
  both directions, with `history`; `in_progress`; `bound` and `evidence` against the files; every
  wording rule with its inflections on sample sentences that must and must not be flagged, among
  them those data-model §15 names; an allow-list entry that names a line of a block or a finding of
  the register's checks, exit 1; the mapping chapter's heading missing or found twice; and every
  hand-written document of FR-068 carrying the design-form disclaimer equal to `DESIGN_DISCLAIMER`.
  (FR-050, FR-068, FR-069; SC-015, SC-018; SEC-085)
- [X] T021 Write `scripts/check_claims.py` (contracts/cli.md; data-model §15), FR-069's test as
  written, run by `tests/test_claims.py` from this phase on, which prints on every run each
  allow-list entry added since the last ⛔ gate's approval commit; exit 0 with no finding, 1 on a
  finding. (FR-069; SC-018; SEC-081, SEC-087)
- [X] T022 Draft the `allow_list` line entries in `protocol/claims.json` for the flagged lines of
  the documents in the test's scope (the feature's Markdown files, this one included, `README.md`
  and `security.md`, whose §1.1 lines that the level rule flags are reworded or given entries), each
  with its path and text, its reason, its writer and the date, until
  `python scripts/check_claims.py` reports 0 findings; the owner reviews the entries at the next ⛔
  gate, and an entry the owner declines is removed in the next commit. (FR-069; SC-018; SEC-087)
- [X] T023 Write the document tests in `tests/test_protocol_004.py`: the spec's Status line, the
  Status of `checklist-choices.md` and the Review & Approval table agree; the first list of rows a
  guard reads, its numbered families included, and the contracts' guards agree both ways; no key is
  loaded into a state of `phyco-v3` or of any candidate while the "FUT-SEC-8 result review" row with
  the highest k does not read Approved at HEAD naming the latest demonstration record
  (contracts/cli.md, "Order of US1"); and every call that loads a seed set of feature 002 or 003
  passes `allow=("dev",)`. (FR-001, FR-003, FR-040; spec Review & Approval notes)

### Step (2a): requirements and the first environment records

- [X] T024 Correct `requirements.txt` as research R18 states: the stale header removed;
  `numpy==2.2.6; python_version >= "3.10" and python_version < "3.14"` and
  `numpy==2.5.4; python_version >= "3.14"`; scipy 1.15.3 and 1.18.1 with the same markers;
  `nistrng==1.2.3`; the three Hypothesis pins of R19 commented out, naming the open item; and a
  comment that the analysis tools need Python 3.10 or later, that the model needs only the standard
  library, and that the markers admit Python 3.11 to 3.13 untested. (FR-035, FR-053; R17, R18)
- [X] T025 **Owner**: run `python scripts/owner_record.py environment --platform windows --by NAME`
  on Windows and `wpy scripts/owner_record.py environment --platform wsl --by NAME` in WSL, writing
  `$REP/environment-windows.json` and `$REP/environment-wsl.json`; add a row "Environment record
  <n>" per record to `specs/004-crypto-architecture-v3/spec.md`, naming the platform, the printed
  approval hash and the date, set it to Approved and commit. Every later write names the record in
  force as its `environment`. (FR-053; R1; PRO-068, PRO-071; REP-082, REP-083)

### Step (3): the provenance log

- [ ] T026 Write the first entries of `$REP/provenance.jsonl` with
  `python scripts/provenance.py add FILE`, one per file drafted before the log or per section
  changed: the feature's documents (spec, plan, research, data model, both contracts, quickstart,
  the checklists, `checklist-choices.md` and this file), `research/004/place_check.py`, the files of
  steps (1) to (2a), and every file outside the feature directory that this feature's sessions
  changed, as `git log` from `801c6d7` on shows, `security.md`, `README.md`, `.gitattributes`,
  `requirements.txt` and `.specify/memory/constitution.md` among them, whole or per section changed,
  each with the tool and model, the date, the task ID and its review status. (FR-067; SC-020;
  data-model §14; REP-080, REP-089, REP-095)

### Step (4): the refused list and the protocol change log

- [ ] T027 Write the refused list of research R15 as `research/004/refused-constants.json`, in R15's
  entry format, which `scripts/gen_constants_v3.py` will read, before the protocol change log, so
  that its SHA-256 stands in `refused_list` of each entry that fixes the constant rule
  (data-model §18), the file committed before T028: the standard polynomials of degree 64 and 128
  (CMAC's R₆₄ and R₁₂₈, GCM's and the CRC-64 polynomials of ISO 3309 and ECMA-182) and the
  polynomials and constant sets of every design that the strategy note, the spec, the plan,
  research.md and `security.md` name, research R12's reference designs among them, each with its
  source; each set's source is a file recorded `fetched` in `downloads.json` or the design's
  published derivation, computed by `research/004/refused_sources.py`, committed code that cites the
  derivation of each set it computes. A set with neither waits for a download of its own: the agent
  prepares its request, the file's name, one that no entry of `downloads.json` holds, its source,
  size and licence, from the host's page and a header request with no file body downloaded, as
  research R19's were; then **Owner**: permit it in a row "Download <n>" of the spec's Review &
  Approval table; the agent then runs `python scripts/downloads.py approve NAME`, which enters it in
  `downloads.json` before the file is fetched into its own new directory and recorded with `fetched`
  (FR-046; R19). A set whose file is recorded `not obtained` waits for another copy under a name of
  its own, requested the same way, and where none can be had, no candidate can be scored, so none
  can be eligible, and the feature recommends stopping (stop rule; R15). A set not on the list when
  the log is created, a set from a paper of R19 not yet fetched among them, enters as a `stricter`
  entry with the list's new SHA-256, and no candidate is scored before every set this task names is
  on the list. (FR-023, FR-044, FR-046; R15, R19; RAT-038, RAT-043)
- [ ] T028 After T002, run `python scripts/protocol_change.py check` and report its places beside
  the confirmed rows; then **Owner**: run `python scripts/protocol_change.py create`, which writes
  the first entries of `research/004/protocol-changes.jsonl`, one per listed row of every answered
  round in round order and one per place confirmed as an entry of its own, each reading marked
  `set_aside` decided as the row "Readings set aside" states, and type at its approval step the
  first 16 hex digits of the approval hash it prints; the agent then commits the log. No evidence
  run starts before it. (FR-044; data-model §18; PRO-063, PRO-077, PRO-079)

### Step (5): the downloads manifest

- [ ] T029 Run `python scripts/downloads.py init`, which writes `$REP/downloads.json` with twelve
  `approved` entries, one per file of research R19's two tables, eight papers and four wheels, each
  with its name, source, size and licence, before any download. (FR-046; R19)

### Step (6): the Hypothesis wheels

- [ ] T030 Download each wheel of research R19's software table into its own new, empty directory:
  `hypothesis-6.168.5-cp310-abi3-win_amd64.whl` (684,616 bytes),
  `hypothesis-6.168.5-cp310-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` (1,157,262 bytes),
  `sortedcontainers-2.4.0-py2.py3-none-any.whl` (29,575 bytes) and
  `exceptiongroup-1.3.1-py3-none-any.whl` (16,740 bytes, Windows only); record each in
  `$REP/downloads.json` with `python scripts/downloads.py fetched NAME PATH --pypi-sha256 HEX`, its
  SHA-256 checked against PyPI's, all four recorded `fetched` before any is installed. Nothing runs
  from a download directory. (FR-046; R19)
- [ ] T031 Install the wheels from outside their directories: on Windows with
  `<python> -I -m pip install --user --no-index --no-deps` and the three Windows wheels, `<python>`
  being the full path of research R1's Store Python, and in WSL with `~/.venvs/phycoweb/bin/python
  -I -m pip install --no-index --no-deps` and the two WSL wheels; if pip refuses a user install
  under `-I`, stop for the owner's decision. Compare `pip freeze` with R18's pins on each platform,
  then write the Hypothesis pins into `requirements.txt`, each marked for its platform. (FR-046,
  FR-058; R18, R19)

### Step (7): the new environment records

- [ ] T032 **Owner**: write each platform's new environment record with
  `scripts/owner_record.py environment`, as in T025, matching the pins, into
  `$REP/environment-windows.json` and `$REP/environment-wsl.json`, and set its row "Environment
  record <n>" in `specs/004-crypto-architecture-v3/spec.md` to Approved before any later write; the
  property tests stop skipping from then on. (FR-058; R1; REP-082)

### Step (8): development inputs

- [ ] T033 [P] Write `tests/test_devinputs_v3.py` (data-model §2; R3): each input is the SHA-256 of
  `phycoweb-004/dev/<kind>/<i>`, test states of `phycoweb-004/dev/state/n<n>w<w>/<i>/<j>`, and the
  uniform controls come from `phycoweb-004/control/`; the loader refuses every other namespace,
  `control` for any kind but a control, and any index outside the use's declared range; fingerprints
  are checked at load for every allowed (n, w), at most 16 pairs, and for the synthetic seeds; the
  closed class of constructed inputs holds only its listed members; quickstart P2 and P3. (FR-040;
  SC-011; R3)
- [ ] T034 Write `protocol/devinputs_v3.py`, standard library only, giving every input and the
  synthetic seeds through `load`, as quickstart P2 and contracts/cli.md call it, with the
  fingerprints, until `tests/test_devinputs_v3.py` passes. (FR-040; SC-011; R3)

### Step (9): the phyco-v2 archive

- [ ] T035 [P] Write `tests/test_baseline_v2.py`: every file under `baseline/phyco-v2/` matches its
  `MANIFEST.json` SHA-256 and its live source, and every frozen file of features 002 and 003 still
  hashes as its freeze records it. (FR-042; SC-012)
- [ ] T036 Write `scripts/archive_phyco_v2.py [--check]` (contracts/cli.md; R18), which copies
  `phycoweb/model_v2.py`, `phycoweb/lut.py`, `fast/phyco_stream.c`, `fast/lut_table.h`,
  `specs/002-core-dynamics-redesign/design.md` and both `vectors/phyco-v2_*.hex` byte for byte into
  `baseline/phyco-v2/`, with `MANIFEST.json` holding each file's SHA-256, source path and
  `git_head`; run it, then `--check`, 0 mismatches (quickstart P1). The live files stay unchanged.
  (FR-042; SC-012; R18)
- [ ] T037 Run the whole suite under `tests/` on Windows,
  `python -W ignore -m unittest discover -s tests -t .`, and in WSL with `wpy`: every test passes,
  or skips naming its open item, and none fails (quickstart P0); record the commands and results for
  the phase report. The suite is light until T081 adds FR-053's test with two worker counts, marked
  heavy; from then on a run of the whole suite, or of `tests/test_records_004.py`, is a heavy run
  and waits for the owner's go-ahead, and T125 makes that run before the final report. (FR-053,
  FR-058; Principle V)

**Checkpoint**: the writers, the three logs, the register and the archive stand; the claim test and
the line-ending test pass at HEAD; each platform's environment record in force reads Approved. The
phase ends with the constitution's phase report to the owner.

---

## Phase 2: User Story 1 - The 64-bit seed bound of phyco-v2, reproduced (Priority: P1) 🎯 MVP

**Goal**: FUT-SEC-8 first: each of three development targets' seeds recovered from three output
words by trying all 2³² candidates for its last two words, with the cost measured and scaled to all
2⁶⁴ seeds (FR-001, FR-002; R2).

**Independent Test**: quickstart U1 to U5: each recovered seed equals its target; the one-word
false-match count of each target is tested against a Poisson distribution of mean (2³² − 1)/2³², and
the three targets pooled against three times that mean, two-sided at level 0.01; any false match
after two or three words is reported as a deviation; the cost is recorded with its commands and
hashes.

**Order**: no key-loading code for `phyco-v3` or any candidate exists before T045 reads Approved
(FR-001, FR-003; contracts/cli.md, "Order of US1").

### Tests for User Story 1

- [ ] T038 [P] [US1] Write `tests/test_seed_search.py`, WSL only, skipping on Windows with its
  reason: `make -C fast -f seed_search.mk` builds `fast/build/seed_search` with `-Werror`, and its
  `--source-sha256` prints the SHA-256 of `fast/seed_search.c` (quickstart U1); a build of the same
  source in a second directory gives a binary of the same SHA-256 (research R16);
  `fast/build/seed_search --check-vectors vectors/phyco-v2_*.hex` compares 2 × 10,000 words and
  exits 0 (quickstart U2); `fast/build/phyco_stream` and `fast/Makefile` hash the same before and
  after the build; only the main thread writes progress lines. (FR-001, FR-002, FR-053; R2, R16)
- [ ] T039 [P] [US1] Write the tests of `scripts/fut_sec8.py` in `tests/test_protocol_004.py`, on a
  mocked tool and a temporary reports directory: the targets are
  `protocol.seedsets.load("dev", allow=("dev",))[:3]`, and a held-out set exits 2; a second run
  exits 2 unless `--repeat-after-defect` names a recorded defect, or `--repeat-after-end` the record
  of a pass ended from outside, that no earlier record names, and `--owner-request` quotes the
  owner's request with its date (quickstart U4); `--reproduce` exits 2 before the FUT-SEC-8 result
  review and without `--owner-request`; `--verify` exits 1 on a disagreement; the record holds every
  field of data-model §4; and the Poisson tests on constructed counts. (FR-001, FR-002, FR-040,
  FR-053; R2, R7)

### Implementation for User Story 1

- [ ] T040 [US1] Write `fast/seed_search.c` (C99) and `fast/seed_search.mk` (contracts/cli.md; R2):
  its own copy of `phyco-v2`'s design-1.0 step; `--check-vectors FILE ...`, exit 0 only if all
  10,000 words of every file match; `--source-sha256`, which prints the SHA-256 of the
  `fast/seed_search.c` it was built from, which `fast/seed_search.mk` builds into it, compiling with
  relative paths and no debug information; and `--s0 S0 --s1 S1 --words W1 W2 W3 [--threads 32]
  [--progress SECONDS]`, which exits 2 on any other argument, runs the 256-step warm-up for every
  (s₂, s₃), drops a candidate at its first mismatch, and prints one JSON object with the counts
  after one, two and three words, every three-word match, total steps, seconds, steps per second and
  threads, the progress going to stderr from the main thread only, from counters that the workers
  update; built in WSL into `fast/build/`, with `fast/phyco_stream.c` and `fast/Makefile` unchanged.
  (FR-001, FR-002, FR-053; R2, R16)
- [ ] T041 [US1] Write `scripts/fut_sec8.py` (WSL; contracts/cli.md): the observations from
  `phycoweb/model_v2.py`, its SHA-256 `1260142d…` checked; the vector check; then one sweep per
  target under the heavy-run lock, any extra three-word match separated by the fourth word; the
  demonstration record `$REP/fut-sec-8/<record_id>.json` with every field of data-model §4, its
  `report` holding the nine items of security.md §12.4 with T1 as the attacker, the Poisson tests
  and `DESIGN_DISCLAIMER`; and `--verify RECORD` and `--reproduce RECORD` as their section states.
  (FR-001, FR-002, FR-060, FR-061; SC-001; R2)
- [ ] T042 [US1] In WSL, build with `make -C fast -f seed_search.mk` and run `fast/build/seed_search
  --check-vectors vectors/phyco-v2_*.hex`, exit 0; run
  `python -W ignore -m unittest tests.test_seed_search` with `wpy`; commit `fast/build/seed_search`,
  so that the demonstration record's `code_sha256` entry for it has a blob at its `git_head`
  (research R18); then ask the owner's go-ahead for the sweep, with its expected cost, about
  2³² × 257 steps per target and under an hour of wall time on 32 threads. (FR-002, FR-045, FR-053;
  R2, R18)
- [ ] T043 [US1] **heavy**: run `wpy scripts/fut_sec8.py --binary fast/build/seed_search --out-dir
  $REP/fut-sec-8` once, under the heavy-run lock: all three targets recovered, the matches after
  one, two and three words beside about 1, 2⁻³² and 2⁻⁶⁴, in under an hour (quickstart U3); then
  `wpy scripts/fut_sec8.py --verify RECORD`; commit the record. A disagreement with the expected
  counts is a finding (FR-060), analysed as the protocol says, and never a reason to sweep again.
  (FR-001, FR-002, FR-045, FR-060; SC-001)
- [ ] T044 [US1] Cite the demonstration record by ID and SHA-256 in the best-attack register row for
  exhaustive seed search, in a version of `security.md` of its own with its history entry, CRLF
  kept. (FR-003; data-model §4)
- [ ] T045 [US1] ⛔ **FUT-SEC-8 result review** (**Owner**), in
  `specs/004-crypto-architecture-v3/spec.md`'s Review & Approval table: review the demonstration
  record with its report; the row names `fut-sec-8/<record_id>.json` by ID and SHA-256 and is
  committed by the owner. The agent lists the approval commits and the allow-list entries added
  since the last gate. A decline ends in a corrected report, reviewed in "FUT-SEC-8 result review
  <k>", or a stop, and key loading stays refused until such a row reads Approved (quickstart U5).
  (FR-003; SC-001; Principle VIII)

**Checkpoint**: FUT-SEC-8 done in the sense of the spec's table "Security Policy traceability";
key-loading code may now be written. US1 stands on its own and is the MVP. The phase ends with the
constitution's phase report to the owner.

---

## Phase 3: Tool Validation (plan phase 3)

**Goal**: every tool whose results count re-finds a known result of its kind first (FR-039; SC-007),
as research R12 and R13 and data-model §7 state. Validations charge no candidate; each instance has
a cap of 8 h, and a heavy one projects first against the feature-wide 66 h row (R7).

**Independent Test**: quickstart V1 and V2: every counted tool has a `re-found` record of its exact
hash, older than its first counted result.

- [ ] T046 [P] [US4] Write `tests/test_ir.py` (R11, R14): the three-colour schedule is a proper
  colouring at every odd n from 3 to 15 (FR-018); the loader's phase rule holds on every operation
  list at every supported size, `research/004/candidates/` included as it fills, and a stated list
  that breaks the rule at one size only is refused there (FR-019); the scalar and batch interpreters
  agree, and the derived inverse undoes Π, on stated lists. (FR-018, FR-019; R11, R13, R14)
- [ ] T047 [US4] Write `research/004/ir.py` (R11): operation lists made only of invertible updates,
  each a word update from other lanes or a constant rotation, grouped into the colour phases with
  the loader's check; the neighbourhood resolved per size (R14); a scalar interpreter on Python
  integers and a batch interpreter on numpy arrays with explicit `uint64` dtypes; the inverse
  derived from the list; and each list's SHA-256 for the candidate log. Analysis code only, never
  imported by the model. (FR-018, FR-019, FR-020, FR-032; R11, R17)
- [ ] T048 [US4] Fix each tool's known results before the tool is drafted, as research R13 lists
  them: write the known results this feature writes itself under `research/004/validation/`, the
  small operation lists with their hand-derived matrices at 3×3 and 4×4, the lists with planted
  symmetries and the one with none, the map with collisions, the variant with a planted gap, the
  instantiation variant with a key bit and a nonce bit that never reach a lane, the operation list
  with a lane that commutes with word rotation, the lists with planted invariants and the one with
  none, research R5's hand-counted examples and the small operation list of known degree with its
  hand-derived inside-out count, and each structural tool's second known result, self-written in the
  same way; enter each with its SHA-256 in `$REP/provenance.jsonl` before the tool it validates is
  drafted, so that its entry's `seq` comes before the tool's first entry. (FR-039; data-model §7,
  §14; R5, R12, R13)
- [ ] T049 [P] [US4] Write `tests/test_tools_004.py` (data-model §5, §7): the validation record's
  fields; a counted record cites a validation of the tool's exact hash with an earlier
  `created_utc`, a C tool's hash being the pair of its source's and its binary's SHA-256, so that a
  change to either counts only after a validation of its own; a result without one is written
  `not evaluated` and counts for nothing; the known results' provenance entries come before the
  tool's first entry and their hashes still match; `research/004/tools/critical_counts.json` is only
  appended to, its entries never changed, and its counts are recomputed exactly; and
  `scripts/validate_tool.py` exits 2 without a recorded source for a published value, or with an
  `owner-provided` entry whose row does not read Approved at HEAD; and, in WSL, skipping on Windows
  and until the file exists, `research/004/tools/trails/arx_search.mk` builds a binary of the same
  SHA-256 in a second directory. (FR-039, FR-053, FR-065; SC-007; R4, R12, R16)
- [ ] T050 [US4] Write `scripts/validate_tool.py` (contracts/cli.md; data-model §7) with
  `--tool NAME --known KNOWN_ID --out-dir $REP/validation` and `--reproduce RECORD`: the source
  guard for published values and `owner-provided` entries; the second known result cited; after a
  failed validation, a re-validation that re-finds every known result of the tool; and, for the bias
  test, the two synthetic families of 100 sets each, drawn with numpy's `Generator(PCG64(s))` from
  the `synthetic` seeds, kept local-only under `data/local/004/<record_id>/`, each set's SHA-256 and
  summary committed. (FR-039, FR-053; R4, R12, R19)
- [ ] T051 [US4] Write `research/004/tools/bias.py`, the frequency test and the uniform controls'
  counts (R4): verdicts from integer critical counts, compared exactly, p-values reported only; and
  `research/004/tools/critical_counts.json`, the critical counts per (N, S) and (N_a, S_A), derived
  by exact integer arithmetic and committed. Validate it with `scripts/validate_tool.py` on its
  known results `s12`, `s14` and `s15` (quickstart V1; S12's ranges and classes, S14's bias, and
  S15's 16 steps with its bound 2¹²⁸ · (2³¹ + 1)⁴, from the count on the vein lanes after 16 steps),
  its records showing the planted bit of each synthetic family firing in 82 to 97 of the family's
  100 sets, with at most 3 sets holding an unplanted firing. (FR-021, FR-037, FR-039, FR-065;
  SC-007; R4, R13)
- [ ] T052 [US4] Write the validation record of `fut_sec8.py`'s tools on their known result
  `fut-sec-8` with `scripts/validate_tool.py`, from the reviewed demonstration record: its three
  seeds and its vector check (data-model §7). (FR-003, FR-039; SC-007; R2)
- [ ] T053 [P] [US4] Write `research/004/tools/invariants.py` (R13): the sums modulo 2^w and the
  XORs of the pressure lanes and of the vein lanes, over the whole state and over each colour class,
  after one round and after a full call, on 2¹⁰ test states, with the binomial test at the bias
  rule's level for probabilistic invariants. Its difference mode takes the S13 transport difference
  of `research/security/step_probes.py` as an input difference. Validate it on `s13-decay` and
  `s13-transport` on `phyco-v2` and on its stated lists at 4×4 and 3×3. (FR-037, FR-039; SC-007;
  R13)
- [ ] T054 [P] [US4] Write `research/004/tools/symmetry.py` (R13): every composition of torus
  translations, rotations by 90°, 180° and 270° and reflections that moves a node, and word
  rotations by k = 1…w − 1, against each round's constants, the food-node placement and every
  per-node constant, each pattern on its own; validate it on S7's three rotation relations of
  `phyco-v2`'s constants and on its stated lists at n = 3 and 4, the planted symmetries found and
  none on the list without one. (FR-023, FR-024, FR-039; SC-006, SC-007; R13)
- [ ] T055 [P] [US4] Write `research/004/tools/dependency.py` (R13): exact structural dependency
  through an operation list, XOR, AND, OR and NOT uniting bit sets, rotations and shifts moving
  them, and bit i of an addition or subtraction depending on bits 0…i of both operands; R_f and R_b
  round by round; and the propagation through instantiate with its margin over R_f; validate it on
  the hand-derived matrices at 3×3 and 4×4. (FR-029, FR-037, FR-039; SC-005, SC-007; R13)
- [ ] T056 [P] [US4] Write `research/004/tools/degree.py` (R13), the degree derivation: the
  bottom-up count of research R13 per phase and round, capped at b − 1, beside its upper bound with
  w for each addition and subtraction, and the inside-out count; validate it on its stated list at
  w = 4, an ARX-box spread over two phases and a bitwise S-box, the exact degree from the truth
  table reported beside the count, and on its hand-derived inside-out count. (FR-037, FR-039;
  SC-007; R13)
- [ ] T057 [P] [US4] Write `research/004/tools/bijectivity.py` (R13): all 2³² inputs of the 2×2
  variant at w = 4 through the batch interpreter into a 2³²-bit bitmap of outputs; validate it,
  **heavy**, each run projected first against the feature-wide row, on a known permutation and on
  the stated map with collisions. (FR-019, FR-037, FR-039; SC-004, SC-007; R13)
- [ ] T058 [US4] Write `research/004/tools/avalanche.py` (R4, R13): the flip set, the related-key
  and related-nonce set and the rotational pairs, N_a = 2¹³ states per flipped bit, the threshold
  0.005/(128·S_A), and every run cross-checked against the exact dependency matrices, a disagreement
  being a tool defect (exit 3); validate it on its three planted results at every round count from 1
  to the variant's R, and on its verdict code for every count 0 to N_a with its exact power at
  research R4's δ_A. (FR-029, FR-037, FR-039; SC-007; R4, R13)
- [ ] T059 [US4] Fetch the trail papers of research R19 when this task is reached, each into its own
  new directory: `automatic-search-arx-trails.pdf` and COSIC's article 2657 (SPECK32, and SPECK64
  where the papers give optimal trails, for w = 32), `main.pdf` (SPARKLE), and `47270450.pdf`
  (PRESENT) through the owner's browser into a folder the owner names; record each in
  `$REP/downloads.json` with `python scripts/downloads.py fetched NAME PATH` or
  `not-obtained NAME --reason TEXT`, and read each with Python under `-I` only. In place of a paper,
  the owner may provide a value (**Owner**: run `python scripts/owner_record.py owner-provided`, its
  row "Owner-provided value <n>" Approved); without either, the tool it validates stays unvalidated.
  (FR-046; R12, R19)
- [ ] T060 [P] [US4] Write `research/004/tools/trails/tables.py`, exhaustive difference and linear
  tables of every distinct box and S-box of up to 16 bits; validate it on every entry of the PRESENT
  S-box's published difference and linear tables. (FR-038, FR-039; SC-007; R12)
- [ ] T061 [P] [US4] Write `research/004/tools/trails/active_sbox.py`, MILP counting of active
  S-boxes with `scipy.optimize.milp` (HiGHS) at research R12's fixed settings (`mip_rel_gap` 0, the
  8 h `time_limit`, and only the solver's dual bound used, rounded down, never the best solution
  found); validate it on `present-5r`, PRESENT's 5-round minimum of 10 active S-boxes. (FR-038,
  FR-039; SC-007; R12)
- [ ] T062 [P] [US4] Write `research/004/tools/trails/long_trail.py`, MILP counting of active
  ARX-boxes at the same settings; validate it on `sparkle-box`, SPARKLE's published long-trail bound
  from its box bounds. (FR-038, FR-039; SC-007; R12)
- [ ] T063 [P] [US4] Write `research/004/tools/trails/arx_search.c`, a branch-and-bound search for
  ARX differential and linear trails with the exact models of addition (Lipmaa and Moriai; Wallén),
  with `research/004/tools/trails/arx_search.mk` (C99, WSL), which builds
  `research/004/tools/trails/build/arx_search`, committed after each build and before the run that
  uses it, its `--source-sha256` printing the SHA-256 of the `arx_search.c` it was built from and
  its make file compiling with relative paths and no debug information, each as for
  `fast/build/seed_search` (research R16, R18); validate it on `speck32-diff` and `speck32-lin`, the
  weights of SPECK32's optimal trails over the first rounds, and at w = 32 on its known result from
  the same papers, each run over 10 minutes **heavy**. (FR-038, FR-039, FR-053; SC-007; R12, R16,
  R18)
- [ ] T064 [US4] Run `tests/test_tools_004.py` and `tests/test_ir.py`, `python -W ignore -m unittest
  tests.test_tools_004 tests.test_ir`, on both platforms and list for the owner every tool without a
  `re-found` record, whose results stay `not evaluated`. The trail tools are fixed when the first
  trail search starts (T088): the rows of research R12's table that then have a `re-found` record,
  none added afterwards. (FR-039; SC-007; R12)

**Checkpoint**: every tool of phases 5 and 6 but the cost model has its validation record, or is
listed as unvalidated. The phase ends with the constitution's phase report to the owner.

---

## Phase 4: User Story 2 - A security target the design must meet (Priority: P2)

**Goal**: the design document's chapters "Security target" and "Mode", with `rationale.md`'s
chapters of those names, drafted and recorded as under review; the output limits follow from the
mode theorem at the target advantage ε = 2⁻⁶⁴ (FR-004 to FR-016; R9, R10).

**Independent Test**: without running code, a reviewer checks FUT-SEC-1 to FUT-SEC-9, threats
T1 to T11 and the generic bounds of security.md §12.2 against the parameter table and the mode
chapter; the tests of `scripts/mode_limits_v3.py` pass on stated tables, and quickstart T1 and T2
run with T107.

- [ ] T065 [US2] Fetch the theorem papers of research R19 when this task is reached, each into its
  own new directory: `Daemen.pdf`, `SpongePRNG.pdf` and `169.pdf`, the last through the owner's
  browser into a folder the owner names, and the AIS 20/31 version 3.0 proposal of R19's paper
  table; record each in `$REP/downloads.json` with `python scripts/downloads.py fetched NAME PATH`
  or `not-obtained NAME --reason TEXT`, and read each with Python under `-I` only. A theorem paper
  not obtained leaves the mode chapter "unverified" (R10). (FR-011, FR-013, FR-046; R10, R19)
- [ ] T066 [US2] Write the security-target tests in `tests/test_records_004.py`, skipping, with
  their reason, until the two files exist (T107): `$REP/security-target/parameters.json` and
  `limits.json` hold data-model §10's fields; the chapter "Security target"'s parameter table and
  output limits restate them row by row and value by value; each row's `bound_bits` is recomputed
  from its `bound_terms`, and each term from the row's other fields (SEC-090); and `rationale.md`
  holds no line that writes a field of either file, or a symbol FR-010 gives one, with a value
  outside a citation of the design document's chapter and section or of a record's ID and SHA-256
  (RAT-090). (FR-010, FR-034, FR-065; SC-003; RAT-085)
- [ ] T067 [US2] Write `scripts/mode_limits_v3.py` with `--out $REP/security-target/limits.json` and
  `--reproduce RECORD` (contracts/cli.md; data-model §10), with its tests in
  `tests/test_records_004.py` on stated tables: it reads the design document's three tables, the
  chapter "Permutation"'s section "Variant table" and the chapter "Mode"'s sections "Layout" and
  "Limits", exit 2 if one is missing, appears twice or holds a row it cannot read; evaluates the
  theorem's bound at the limits the "Limits" table states, the per-request cap of 2¹⁹ bits and at
  most 2³² instantiations per key among them, with ε = 2⁻⁶⁴ and N = 2¹²⁸ (research R9), exit 1 if
  the bound exceeds ε there, and the doubling check; keeps `theorem` `unverified` until its paper is
  read, refusing `verified`, exit 2, without the paper's `fetched` entry in `downloads.json`; and
  writes the size profile `parameters.json` beside `limits.json`, one row per supported size with
  its key entropy, its reachable secret state, c, r, R, `bound_bits` and `bound_terms`, FR-010's
  generic-bound checks computed by code, the keyed reduced variants with a c-bit key and a c/2-bit
  nonce checked at s = c/2. (FR-007, FR-009, FR-010, FR-015; SC-003; R9, R14)
- [ ] T068 [US2] Write FR-034's chapters' test in `tests/test_records_004.py`, skipping, with its
  reason, until `specs/004-crypto-architecture-v3/design.md` and `rationale.md` exist: the design
  document's level-2 chapters "Security target", "Mode", "Permutation", "Hardware structure",
  "Replaced mechanisms" and "Slime-mould mapping", each once and in this order; each section FR-034
  names, in its chapter: "Key loading", "Diffusion through instantiation", "Layout" and "Limits" in
  "Mode", "Variant table", "Inverse" and "Network questions" in "Permutation", and "Self-test" in
  "Hardware structure"; the four tables that `scripts/mode_limits_v3.py` and
  `scripts/gen_vectors_v3.py` read, the variant table, with its columns ID, n, w, b, c, r, R and
  status, the tables of "Layout" and "Limits" and the table of k, each a Markdown table with fixed
  columns, once in its section, every row readable; `rationale.md`'s chapters "Security target",
  "Mode", "Components", "Nonlinearity", "Diffusion", "Constants", "Margin", "Attack classes",
  "Network questions" and "Alternatives", each once and in this order; and each file's header, its
  title, its disclaimer and one "Version: 0.<k>" line and nothing else, the two version lines equal.
  (FR-034, FR-059; SC-013; RAT-074, RAT-084, RAT-085, RAT-087)
- [ ] T069 [US2] Draft `specs/004-crypto-architecture-v3/design.md` with its header, which holds
  only the title, the design-form disclaimer and "Version: 0.<k>", and its chapter "Security
  target", first in FR-034's order: the properties sought as bounds on an adversary's advantage
  (keystream under nonces never repeated, multi-user for u keys, backtracking across each forget
  call; prediction resistance not sought, D7); the security target's parameters, s = 128, a 256-bit
  key with its assumptions and a 128-bit nonce used once per key, c = 256 at every claimable size;
  the output limits; threats T1 to T11, each adopted or excluded with its reason, and the assets of
  a keyed design; every generic bound at every supported size, with the parameter table; the
  claimable sizes and the 2×2 decision; the certification route with "class unconfirmed" beside it
  until the class is confirmed or changed; and the claim template, marked "target, not a claim".
  (FR-004 to FR-012, FR-017, FR-034; R9, R14)
- [ ] T070 [US2] Draft the design document's chapter "Mode", with its sections "Key loading",
  "Diffusion through instantiation", "Layout" and "Limits": the keyed duplex over Π with
  instantiate, generate, forget and the optional reseed, forget after every request and at the end
  of instantiate in the form the theorem covers; the theorem with every precondition and the design
  feature that meets it; padding and domain separation with their injectivity shown both ways; the
  reseed input taken as chosen by the attacker (T9); the rate, the capacity and the canonical
  serialization; and the limits from `limits.json`. (FR-013 to FR-016, FR-034; R10)
- [ ] T071 [US2] Draft `specs/004-crypto-architecture-v3/rationale.md` with its header (title,
  design-form disclaimer, the design document's "Version: 0.<k>") and its chapters "Security target"
  and "Mode", which explain the design document's chapters, each statement carrying one of FR-062's
  seven labels. (FR-034, FR-062; RAT-086, RAT-087)
- [ ] T072 [US2] Record the four chapters as under review in `$REP/provenance.jsonl`, one entry per
  section drafted with the tool and model, the date, the task ID and the status, and no mark in
  either file; the security-target review of phase 8 reads them once the records of phase 5 that it
  cites exist. (FR-034, FR-067; RAT-068, RAT-069, RAT-086)

**Checkpoint**: the security target stands as a draft under review, with `scripts/mode_limits_v3.py`
and its tests and the chapters' test (T068); the script's first run, and the register's `bound` and
`evidence` with it, follows the variant table (T107). The phase ends with the constitution's phase
report to the owner.

---

## Phase 5: User Stories 3 and 4 - Candidates and Evidence (plan phase 5)

**Goal**: the candidates written as operation lists with their constants, the entered set recorded,
the D4 choice made once, then at the production width the trail bounds, the structural checks with
the `degree` records, and the frequency and avalanche tests, in that order at each size and size by
size from 4×4, until the round rule gives R and the rules select a candidate or stop (FR-018 to
FR-033, FR-037, FR-038, FR-041; R4 to R7, R11 to R15).

**Independent Test**: quickstart E1 to E7; every counted result cites a validation record older than
it; the re-check of FR-065 recomputes every verdict from the saved outputs.

**Rules**: one heavy run at a time, each projected first; each kind of evidence at 4×4, then 8×8,
then 16×16; the budget rows of research R7 per candidate; at most three candidates per family, a
fourth `proposed` entry exiting 2 (SC-011). The production-width analysis covers the chosen family;
the other family is analysed there only if the chosen one ends with no eligible candidate, and its
candidates are otherwise `ineligible` (R6, R7).

- [ ] T073 [P] [US4] Write `tests/test_costmodel.py` (R5): research R5's hand-counted examples
  reproduced exactly; 0 LUTs for rotations, constant shifts and wiring; w per bitwise word operation
  with fan-in k ≤ 6 and w·⌈(k − 1)/5⌉ above; w and one carry chain per addition or subtraction; no
  fusion. (FR-022, FR-026; R5)
- [ ] T074 [US4] Write `research/004/tools/costmodel.py` (R5) and validate it with
  `scripts/validate_tool.py` on R5's hand-counted examples, entered in the provenance log by T048;
  the implied throughput is reported beside the goal of 10⁸ words per second at 200 MHz, never an
  eligibility rule. (FR-022, FR-026, FR-039; SC-007; R5)
- [ ] T075 [US3] Write the candidate log's tests in `tests/test_protocol_004.py`: each mode of
  `scripts/candidate_log.py` and its refusals; a fourth `proposed` entry of one family exits 2
  (quickstart E6); every tool refuses an operation list whose hash has no `proposed` or `correction`
  entry; no entry is ever deleted; `scripts/repair_log.py`'s `repair` entry on this log (T013); the
  budget rows, the order of sizes (quickstart E7) and the stop rule. (FR-041; SC-011; R7; ANA-080,
  ANA-083)
- [ ] T076 [US3] Write `protocol/candidates.py`, the one writer of `research/004/candidates.jsonl`,
  and `scripts/candidate_log.py` with `propose`, `mapping`, `enter`, `decide`, `correct`, `replace`
  and `outcome` (contracts/cli.md; data-model §3), through which `scripts/repair_log.py` (T013)
  appends this log's `repair` entry. (FR-041; SC-011; R16)
- [ ] T077 [US3] Write `scripts/gen_constants_v3.py` (contracts/cli.md, "Generators of constants and
  vectors"; R15): the constant rule as fixed (degree 64, the first primitive polynomial in the
  stated order not on `research/004/refused-constants.json`, Fibonacci form seeded with ASCII
  `PhycoWeb`, each table read w bits per word in the stated order, skipping periodic and related
  words, every repeat recorded where a call needs more constants than there are aperiodic classes);
  the refused list's check under its 2w transforms over every table and each call type's stream; the
  refused list's guard, which writes the list's path and SHA-256 as `refused_list` in every record
  the script writes, exits 2, writing nothing, while that SHA-256 differs from the `refused_list` of
  the protocol change log's latest entry that holds one, or no entry holds one, and has a
  `--reproduce` run compare the list at the record's `git_head` with the record's `refused_list`;
  the checks within a call; the rotation amounts and every other per-node constant by their stated
  rules; and the modes `--candidate ID --variant VARIANT`, `--exploration N W` into
  `research/004/exploration/`, `[--check]` for `phycoweb/constants_v3.py` and `--reproduce RECORD`,
  each run writing its record, a `generator-run` record, a `generator-check` record for `--check` or
  a `reproduction` record for `--reproduce`. Its tests, in `tests/test_protocol_004.py`, cover that
  guard: exit 2 with nothing written for a list that differs from the latest `refused_list` and for
  a log in which no entry holds one, `refused_list` in the record of each mode, and a `--reproduce`
  run reading the list at the record's `git_head`; and the list and its match: the committed
  `research/004/refused-constants.json` parses in R15's entry format, each word within its
  `word_bits`, each version that a `refused_list` of the protocol change log names keeps every entry
  of each earlier named version unchanged, checked against the file's history, and a set of a stated
  list, planted in a stated table, is found under each of the 2w transforms and not found when the
  planted run is one word short of 64 bits. (FR-023, FR-024, FR-044, FR-047; SC-006; R13, R15)
- [ ] T078 [US3] Write candidate A1, the 64-bit ARX-box over a node's pressure and vein lanes (D10),
  as `research/004/candidates/cand-A1.py`, an operation list of invertible updates with its
  reference outputs, and append its `proposed` entry with
  `python scripts/candidate_log.py propose FILE` before any tool runs on it; a replaced list stays
  unchanged as `research/004/candidates/cand-A1/superseded/<sha256>.py`, listed in
  `research/004/candidates/superseded.json`. (FR-019, FR-020, FR-021, FR-022, FR-041; R6, R11)
- [ ] T079 [US3] Write at least one Boolean candidate, `research/004/candidates/cand-B1.py`, the
  same way, with its `proposed` entry; a further candidate, at most three per family, is entered
  only where the rules can select it. (FR-022, FR-041; SC-011; R6)
- [ ] T080 [US3] Generate each candidate's constant tables with `python scripts/gen_constants_v3.py
  --candidate ID --variant VARIANT` into `research/004/candidates/<id>/constants/<variant>.json`
  before its first tool run, and append its `mapping` entry with
  `python scripts/candidate_log.py mapping FILE` before its first score. (FR-023, FR-024, FR-041;
  R15)
- [ ] T081 [US4] Write the evidence-run tests in `tests/test_protocol_004.py` and
  `tests/test_records_004.py`: `scripts/evidence_v3.py` refuses a candidate not in the log, a spent
  budget row, a size out of order and a `bound` without a validated tool; an `avalanche` run without
  the candidate's `dependency` record at its size exits 2; every run started writes a record;
  `--aborted RECORD` appends the `evidence` entry of a record that `scripts/clear_lock.py` wrote,
  with its `hours` in `budget_used_h`, whatever the row holds, and exits 2 for any other record or
  one that has its entry; a `control` run exits 2 once its record exists, unless that record holds
  `ended_outside`, when it runs again with the same counts and the same inputs and no test of its
  kind starts at that size before it has; `--reproduce` of a light run of each kind, its latest and
  one older, matches (R7); and FR-053's test with two worker counts, marked heavy, which writes,
  when it ends, a further `projection` record naming research R7's feature-wide row, whose time is
  the time the test took and which says that the test compared the outputs of its stated test
  operation list and kept none. (FR-037, FR-041, FR-045, FR-053, FR-065; R4, R7, R16)
- [ ] T082 [US4] Write `scripts/evidence_v3.py` (contracts/cli.md; data-model §5, §6) with the kinds
  `inverse`, `bijectivity`, `dependency`, `frequency`, `avalanche`, `control`, `symmetry`,
  `invariant`, `degree`, `bound` (with `--bound-kind differential|linear --method M`) and
  `cross-check` (with `--tool NAME`); the counts of research R4 and R13, which no option lowers;
  `--project`, which writes only a `projection` record; an `evidence` entry in the candidate log per
  record; a `trail` record beside each bound run of a tool that searches Π; `--aborted RECORD`,
  which makes no run and appends the `evidence` entry of a record that `scripts/clear_lock.py` wrote
  (T014); and `--reproduce RECORD`. Every finding carries one of the four classes of
  security.md §9.1, and every other record `none`. (FR-037, FR-038, FR-041, FR-060, FR-061; SC-017;
  R4, R7, R12, R13)
- [ ] T083 [US4] Write the tests of `scripts/d4_choice.py` and `scripts/round_rule.py` in
  `tests/test_protocol_004.py`: a second D4 run exits 2 (quickstart E4); `--tie` only after an exact
  tie, once both values of R at 4×4 exist; `--choose` writes nothing unless the owner types 16 hex
  digits at an interactive terminal; R by the round rule with every input cited, eligibility, a
  record that holds `ended_outside` deciding nothing, selection and the stop rule; `--select`
  exits 2 after a D4 tie until its row reads Approved or "Not needed"; `--decide` exits 2 while the
  latest selection record has a tie and no choice whose row reads Approved. (FR-022, FR-028, FR-041;
  SC-005; R6, R7; PRO-074)
- [ ] T084 [US4] Write `scripts/d4_choice.py` (contracts/cli.md; data-model §8; R5, R6): the score
  (min(W_D, W_L)/r*)/L over the entered set recorded before the first score, at 4×4 and at the
  widest reduced width, 16 or else 8, with a common r* ≥ 2, compared exactly; `--tie`;
  `--choose ID --seen SHA256 --by NAME`, the owner's; and `--reproduce RECORD`. (FR-022; R5, R6)
- [ ] T085 [US4] Write `scripts/round_rule.py` (contracts/cli.md; data-model §9): `--candidate ID`,
  R per claimable size with every input cited, into `$REP/candidates/<ID>/round-rule.json`;
  `--close`; `--select`, into `$REP/freeze/selection.json` and later `selection-<k>.json`;
  `--decide`; `--choose ID --seen SHA256 --by NAME`, the owner's; and `--reproduce RECORD`, with
  eligibility, selection and the stop rule as the spec's "Pre-registered Design Protocol" states.
  (FR-028, FR-041, FR-043; SC-005, SC-008; R6, R7)
- [ ] T086 [US4] Write `scripts/recheck_004.py [--kind KIND]` and `--reproduce RECORD`
  (contracts/cli.md; R16), standard library and `protocol/` only, which recomputes every verdict of
  FR-065 from committed files, the `trail` records' weights and classifications among them, and
  writes a `recheck` record naming the interpreter, the platform and its `pip freeze`; a record that
  `scripts/clear_lock.py` wrote for a run that died holding the lock is no disagreement, its
  `status`, `classification` and hours used, or a `projection` record's time, checked against it and
  the `lock-cleared` record that names it, exit 1 on any other; with its tests, this case among
  them, and its import test in `tests/test_records_004.py`. (FR-065; SC-017; ANA-086)
- [ ] T087 [US4] Record the entered set with `python scripts/candidate_log.py enter`, one
  `entered-d4` entry per candidate of the set, before the first score. (FR-022, FR-041; R6)
- [ ] T088 [US4] For each entered candidate, at 4×4 and at the widest reduced width, compute the
  inputs of the D4 score with `python scripts/evidence_v3.py`: the trail bounds over r* rounds with
  the validated trail tools and the cross-checks between kinds, the first trail search fixing the
  trail tools, and the cost from `research/004/tools/costmodel.py`; each heavy run **heavy**,
  projected first. (FR-022, FR-038, FR-039; R5, R6, R7, R12)
- [ ] T089 [US4] Run `python scripts/d4_choice.py --log research/004/candidates.jsonl --out
  $REP/d4/choice.json` once (quickstart E4); after an exact tie, `--tie` writes `$REP/d4/tie.json`
  once both values of R at 4×4 exist. (FR-022; R6)
- [ ] T090 [US4] ⛔ **D4 tie** (**Owner**), only where the tie-breaks reach the owner's choice: run
  `python scripts/d4_choice.py --choose ID --seen SHA256 --by NAME --out $REP/d4/tie-choice.json`,
  then set and commit the row "D4 tie" in `specs/004-crypto-architecture-v3/spec.md`; where a
  tie-break decides it, the row reads "Not needed", naming `d4/tie.json` and its tie-break. (FR-022;
  R6; PRO-074)
- [ ] T091 [US4] Before any candidate's first frequency or avalanche run at a size, run the uniform
  controls there, `python scripts/evidence_v3.py --kind control --test frequency --size N --project
  --out-dir $REP/controls` and then the run, and the same for `avalanche`, each **heavy**; a control
  that fires makes that size's bias evidence inconclusive for every candidate, and the feature
  recommends stopping. (FR-037; R4, R7; ANA-074)
- [ ] T092 [US4] For each candidate of the chosen family, at 4×4, then 8×8, then 16×16, with `python
  scripts/evidence_v3.py --candidate ID --kind KIND --size N --out-dir $REP/candidates/<ID>`: the
  differential and linear trail bounds at the production width, with the cross-checks between kinds;
  then the structural checks, the inverse on the 16 vector inputs and 2¹⁰ test states at every
  supported size and variant, the 2×2 variant's exhaustive bijectivity at w = 4 (quickstart E2), the
  dependency matrices with R_f, R_b and the propagation through instantiate, the symmetry and
  invariant checks, and the `degree` records last; then the frequency test on both input sets,
  N = 2²⁰ through Π and Π⁻¹, and the avalanche test on the flip set, the related-key and
  related-nonce set and the rotational pairs, N_a = 2¹³, from the R the earlier kinds give and
  extended to every later rise of R; each heavy run **heavy**, projected first (quickstart E1 to
  E3). (FR-019, FR-021, FR-029, FR-037, FR-038; SC-004, SC-005, SC-008; R4, R7, R12, R13)
- [ ] T093 [US4] Run `python scripts/round_rule.py --candidate ID` per candidate once its evidence
  stands at every claimable size; after a rise of R, repeat the inverse tests, the invariant checks
  and the new constant table's checks at the new variant before the bias tests are extended (R7,
  "After a rise of R"); then run `--close`, `--select` (exit 1 for a stop) and `--decide`
  (quickstart E5). (FR-028, FR-041; SC-005, SC-008; R7)
- [ ] T094 [US4] ⛔ **Selection tie** (**Owner**), only where eligible candidates tie: run `python
  scripts/round_rule.py --choose ID --seen SHA256 --by NAME`, which writes
  `$REP/freeze/selection-tie-choice.json`, then set and commit the row "Selection tie" in
  `specs/004-crypto-architecture-v3/spec.md`, or "Selection tie <k>" for a later selection record;
  otherwise the row reads "Not needed". (FR-041; data-model §9; PRO-074)

**Checkpoint**: a selection record with its decision entries in `research/004/candidates.jsonl`, or
a stop with what was reached, which skips to T126. The phase ends with the constitution's phase
report to the owner.

---

## Phase 6: User Story 3 - The model, its constants and its vectors (plan phase 6)

**Goal**: the design document complete; `phycoweb/constants_v3.py`, `phycoweb/model_v3.py`, the
vectors and known-answer tests, the constructed-state vectors and the self-test's copy of the
vectors, each reproduced on Windows and in WSL (FR-018 to FR-036, FR-054 to FR-059).

**Independent Test**: quickstart M1 to M6: each generator's `--check` exits 0 on both platforms with
its `generator-check` record; every reduced variant and every request beyond a limit is refused
(SC-010).

- [ ] T095 [US3] Complete `specs/004-crypto-architecture-v3/design.md` for the selected candidate,
  its chapters after "Security target" and "Mode" in FR-034's order: "Permutation", with its
  sections "Variant table", "Inverse" and "Network questions"; "Hardware structure", with its
  section "Self-test" and its table of k; "Replaced mechanisms", which shows how each failed
  `phyco-v2` mechanism is replaced and removes Frustrated Foraging (D5); and "Slime-mould mapping",
  holding FR-030's one fixed negative statement and no other security wording. It states the width,
  signedness, wrap rule, shift kind and comparison semantics of every operation, the update order
  and every data-flow direction, the edge states, the colour schedule, the reduced variants and the
  production parameter sets, the constant rule's values, every hardware rule of FR-025 with its
  figure, the output bits per call and per round and the throughput implied at 200 MHz; each section
  entered in `$REP/provenance.jsonl` as it is drafted. (FR-017 to FR-032, FR-034, FR-054, FR-055,
  FR-059; R5, R11, R14, R15)
- [ ] T096 [P] [US3] Write `tests/test_model_v3.py` (contracts/model-v3-api.md, "Tests that hold the
  model to this contract"): FR-058's list, minimum, maximum and boundary values, all-zero and
  all-one keys and nonces, single-bit keys, overflow and truncation, shift and rotation boundaries,
  reset, zeroization and repeated instantiation, long runs with the 2²⁰-word digest and invalid
  parameters; every reduced variant refused by `Generator` with `VariantRefused` (quickstart M4);
  every request beyond each limit refused, reached through `ResearchDuplex.from_state` from chosen
  counter values (REP-078); every call-sequence error, any call after `zeroize` among them;
  `ResearchDuplex`'s key and nonce lengths (quickstart M6); every failure path; the model importing
  no analysis dependency; `phyco-v3` reproducing the selected candidate's outputs through the
  `selected` entry's variant map; property tests with Hypothesis; and `test_generator_selftest`
  (REP-086). (FR-033, FR-035, FR-058, FR-059; SC-010; R17)
- [ ] T097 [US3] Run `python scripts/gen_constants_v3.py`, which writes `phycoweb/constants_v3.py`
  with its GENERATED header for every supported (n, w) at its final R; then `--check` on Windows and
  with `wpy` in WSL, each writing a `generator-check` record with verdict `match` under
  `$REP/generator-checks/` (quickstart M1). (FR-023, FR-024; SC-006, SC-009; R15)
- [ ] T098 [US3] Write `phycoweb/model_v3.py` from the design document (contracts/model-v3-api.md;
  R17): standard library only, its source parsing under Python 3.8's grammar, integer-only and
  branch-free on data, `MODEL_ID = "phyco-v3"` with `PRODUCTION_VARIANTS`, `parse_variant` and
  `is_production`; `pi`, `pi_inv` and `pi_trace`, research-only; `Generator(variant_id, key)` with
  `instantiate(nonce, pers=b"")`, `generate(nbits)`, `reseed(data)` and `zeroize()`, the start-up
  self-test imported only in its constructor, every limit with its counter and every refusal of the
  contract; `ResearchDuplex` for the keyed reduced variants; marked model-only, RTL-pending.
  (FR-013, FR-015, FR-020, FR-033, FR-035, FR-055, FR-059; SC-010; R9, R14, R17)
- [ ] T099 [P] [US3] Write `tests/test_vectors_v3.py` (data-model §11; R8): Π and Π⁻¹ known-answer
  tests at every supported size and every reduced variant used as evidence, 16 inputs with 4 traced
  phase by phase; the mode at every claimable size with 2 development keys × 10,000 words in
  requests that cycle through the stated lengths; the SHA-256 digest of 2²⁰ words over their 4·2²⁰
  raw bytes; the sidecar `vectors/phyco-v3/MANIFEST.json`; `phycoweb/selftest_v3.py` equal to the
  vectors it copies; each `selftest_<variant>.json`, one per claimable size and per keyed research
  variant (HW-095), from the self-test's call sequence alone, each request with its forget call
  (REP-096); and each file's k against the least k computed again from the model's run and against
  the design document's table of k, equal unless a named structure with its reason raised it
  (REP-097). (FR-036, FR-059; SC-009; R8; HW-095, REP-096, REP-097)
- [ ] T100 [US3] Write `scripts/gen_vectors_v3.py [--check] [--variant ID ...]` with
  `--reproduce RECORD` (contracts/cli.md; R8) and run it into `vectors/phyco-v3/`, writing in the
  same run, from a `ResearchDuplex` object of its own run through the self-test's call sequence
  alone, each request with its forget call (REP-096), each claimable size's and each keyed research
  variant's `selftest_<variant>.json` (HW-095), with k read from the design document's table of k,
  exit 2 if that table is missing, appears twice or holds a row it cannot read, exit 1 if its k is
  below the least k of the run, or above it with no named structure and reason, and k, the structure
  that set it and the run's least k written into each file (REP-097), and `phycoweb/selftest_v3.py`
  (GENERATED) copied from those files, each vector file in at most an hour and the model's speed
  measured and recorded; then `--check` on Windows and with `wpy` in WSL, each writing a
  `generator-check` record (quickstart M2). (FR-036, FR-059; SC-009; R8; HW-095, REP-096, REP-097)
- [ ] T101 [US3] Write `scripts/gen_constructed_v3.py [--check]` with `--reproduce RECORD`
  (contracts/cli.md): a constructed-state vector for every edge state the design document lists,
  from chosen states and from development keys, all-zero and all-one lanes, every addition driven to
  a carry out of its top bit and every shift and rotation at its boundary among them, into
  `vectors/phyco-v3/`; run it, then `--check` on Windows and with `wpy` in WSL, the pair of
  `generator-check` records also showing that `Generator`'s self-test passed on each platform
  (quickstart M3). (FR-054, FR-056; SC-009, SC-016; REP-086)
- [ ] T102 [US3] Run `tests/test_model_v3.py` and `tests/test_vectors_v3.py`, `python -W ignore -m
  unittest tests.test_model_v3 tests.test_vectors_v3`, on Windows and with `wpy` in WSL
  (quickstart M5), and record the commands and results. No expected value is ever edited to make a
  test pass: a disagreement goes back to the design document or the model as a finding. (FR-035,
  FR-036, FR-056, FR-058; SC-009, SC-010)

**Checkpoint**: the model, constants, vectors and constructed states reproduced on both platforms.
The phase ends with the constitution's phase report to the owner.

---

## Phase 7: User Story 3 - The second transcription (plan phase 7)

**Goal**: a second transcription of Π, Π⁻¹ and the mode, written from the design document alone in a
separate session, agreeing with the model step by step (FR-057).

**Independent Test**: quickstart X1 and X2.

- [ ] T103 [US3] ⛔ **Second transcription go-ahead** (**Owner**): the row "Second transcription
  go-ahead" in `specs/004-crypto-architecture-v3/spec.md` set to Approved and committed before the
  separate session starts; the agent lists the approval commits and the allow-list entries added
  since the last gate. (FR-057; Principle VIII)
- [ ] T104 [P] [US3] Write `tests/test_v3_transcription.py`: `phycoweb/model_v3.py` and
  `tests/v3_reference.py` agree after every phase of every round on the committed vectors, for Π,
  Π⁻¹ and the mode, with the common-mode caveat of security.md §10.2 beside the result
  (quickstart X1); and the provenance test: the go-ahead row reads Approved at HEAD with a date no
  later than the first provenance entry of `tests/v3_reference.py`, and the two files come from
  different sessions (quickstart X2). (FR-057, FR-067; SC-016)
- [ ] T105 [US3] In a separate session that has not read `phycoweb/model_v3.py` and imports no code
  from it, write `tests/v3_reference.py` from the design document alone, with its entries in
  `$REP/provenance.jsonl` naming that session. (FR-057, FR-064, FR-067; R17)
- [ ] T106 [US3] Run `tests/test_v3_transcription.py`,
  `python -W ignore -m unittest tests.test_v3_transcription`, on both platforms; a disagreement is
  reported against the design document, corrected as a new version of it and compared again, never
  by editing either side to agree. (FR-056, FR-057; SC-016)

**Checkpoint**: agreement at 100% of the steps of the committed vectors, with the caveat stated. The
phase ends with the constitution's phase report to the owner.

---

## Phase 8: User Stories 2 and 5 - Reviews and Freeze (plan phase 8)

**Goal**: the security-target review, which closes US2, then the rest of the rationale, the review
package, the owner design review, the external review recorded, and the design freeze (FR-043,
FR-063).

**Independent Test**: check the rationale against every item of security.md §8 and the review
package against §14; compare the candidate log with the model's variant IDs; recompute the freeze
hashes and the baseline manifest; run the claim-register test.

- [ ] T107 [US2] Once the design document holds the three tables the script reads, the "Variant
  table" with every variant's R from T093 (T095) and the mode chapter's "Layout" and "Limits", run
  `python scripts/mode_limits_v3.py --out $REP/security-target/limits.json` (quickstart T1 and T2)
  and commit both files; in the same commit, write `phyco-v3`'s `bound` in `protocol/claims.json`
  from the profile, "at most <bound_bits> bits" per claimable size by its variant ID, with the
  profile's path and SHA-256, and its `evidence`, the profile and `limits.json`. (FR-007, FR-010,
  FR-069; SC-003; SEC-089)
- [ ] T108 [US2] Prepare the security-target review in `specs/004-crypto-architecture-v3/design.md`,
  `rationale.md` and `$REP/security-target/`: cite the selected candidate's records of FR-029's
  diffusion through instantiation and of research R4's first-order related-key and related-nonce
  differences; confirm or change FR-011's functionality class in the design document once the AIS
  20/31 3.0 proposal is read; mark each theorem `verified` in `limits.json` with
  `scripts/mode_limits_v3.py` once its paper is read, its entry citing the paper's `fetched` entry
  in `downloads.json` by SHA-256 with the theorem's number and page, and each precondition met,
  naming the mode chapter's section that meets it; and compute the set the row will name: the
  SHA-256 of each of the four chapters, from its heading line to the next heading of the same or a
  higher level, and of `parameters.json` and `limits.json`, with the design document's "Version:
  0.<k>". (FR-011, FR-012, FR-029; RAT-086; SEC-075)
- [ ] T109 [US2] ⛔ **Security-target review** (**Owner**), in
  `specs/004-crypto-architecture-v3/spec.md`'s Review & Approval table: the row names the set by
  SHA-256 with the version read and is committed by the owner; the agent lists the approval commits
  and the allow-list entries added since the last gate. A decline ends in a revised chapter,
  reviewed in "Security-target review <k>", its security-target parameters changing only in their
  stricter direction, or a stop. (FR-012, FR-043, FR-044; SEC-075; Principle VIII)
- [ ] T110 [US2] ⛔ **L1 recorded** (**Owner**), in `specs/004-crypto-architecture-v3/spec.md`'s
  Review & Approval table: set the row "L1 recorded" once the FUT-SEC-8 result review and the
  security-target review both read Approved, naming both rows by family and k with what each
  reviewed by path and SHA-256, the row reading "blocked" and naming the missing paper while a
  theorem the mode chapter uses is "unverified"; then the agent, in a commit of its own right after
  the owner's commit, changes `phyco-v3`'s entry in `protocol/claims.json`, its §15 line and its
  §1.1 row in `security.md` to the level the rows give, with `python scripts/check_claims.py`
  reporting 0 findings. (FR-012, FR-069; SEC-076, SEC-079, SEC-081, SEC-095)
- [ ] T111 [US5] Write the rest of `specs/004-crypto-architecture-v3/rationale.md`, its chapters in
  FR-034's order, "Components", "Nonlinearity", "Diffusion", "Constants", "Margin" and "Attack
  classes", then "Network questions" and "Alternatives", each statement with one of FR-062's seven
  labels: every rationale item of security.md §8, the hardware structures of plan.md's Complexity
  Tracking with their functional need, and every candidate considered with the reason it was kept or
  dropped. (FR-030, FR-034, FR-062; SC-013; RAT-084)
- [ ] T112 [US5] Write the version of `security.md` that FR-051 asks for, CRLF kept, with its
  history entry: `phyco-v3`'s own section, a table of structural facts, the best-attack register
  rows of its first bounds and the lessons table that links S1 to S15 to the rules or parts of the
  design that answer them, each with its evidence; the §1.1 row of phase 1 and the fixed sentence in
  both blocks kept; and what feature 005's cryptanalysis instructions need. (FR-051, FR-066;
  SEC-095)
- [ ] T113 [P] [US5] Write the freeze tests in `tests/test_protocol_004.py`:
  `scripts/design_freeze.py create` exits 2 before the owner design review (quickstart F1), on every
  condition of its section in contracts/cli.md, a change to `rationale.md` or to the reviewed set
  after its review among them (RAT-083), unless HEAD is the owner's commit of step (1), and while
  `scripts/check_claims.py` reports a finding; `approve` writes nothing unless the owner types the
  first 16 hex digits of `draft_sha256` at an interactive terminal; `validate` exits 2 while
  `freeze_status` is `draft` and 1 if anything but the approval fields changed. (FR-043; PRO-070,
  PRO-073; REP-092, REP-093)
- [ ] T114 [US5] Write `protocol/design_freeze.py`, with create, approve and validate as functions,
  and `scripts/design_freeze.py`, the command that calls it (contracts/cli.md; data-model §13): the
  record holds the design document's version 1.0 with `reviewed_version`, `rationale.md`, the
  selected operation list, `research/004/ir.py` with its tools, the verdict scripts,
  `validate_tool.py` and `fut_sec8.py` among them, both freeze files, every module a frozen script
  imports, listed from the scripts' imports with `research/004/` loaded by path, every evidence
  record behind R by ID and SHA-256, and the last `seq` and line SHA-256 of the three logs. (FR-043;
  REP-091, REP-092)
- [ ] T115 [US5] Write `protocol/review_package.py` and `scripts/review_package.py [--check]` with
  `--reproduce RECORD` (contracts/cli.md; data-model §16), and assemble `$REP/review-package/` with
  its `MANIFEST.json`: the spec, the design document and the rationale with exact revisions, the
  model source and vectors, the evidence records, the threat model, the security target marked as
  targets, and the known limitations and open questions, every item of security.md §14 by the files
  of its group; `--check` fails an item with no file. (FR-063; SC-020; RAT-089, REP-085)
- [ ] T116 [US5] ⛔ **Owner design review** (**Owner**), in
  `specs/004-crypto-architecture-v3/spec.md`'s Review & Approval table: the design document, the
  rationale, the candidate log and the evidence; "no security statement rests on the mapping"
  recorded among its items; the row naming `rationale.md` by path and SHA-256 beside the design
  document's version and the selection record. Before it, every file of this feature that the freeze
  hashes is committed. The agent lists the approval commits and the allow-list entries added since
  the last gate. A decline ends in one of the outcomes the row states, logged with
  `python scripts/candidate_log.py outcome FILE` after the row's commit. From the commit that
  records the approval, the agent commits no file of this feature (FR-043). (FR-043, FR-064; SC-013;
  ANA-083, RAT-083; SEC-084)
- [ ] T117 [US5] Right after the commit that records the owner design review's approval, write its
  review entries in `$REP/provenance.jsonl` with `python scripts/provenance.py review FILE`, one per
  AI-drafted section, `rationale.md`'s chapters "Security target" and "Mode" among them, and the
  `review-outcome` entry with `python scripts/candidate_log.py outcome FILE`, leaving them in the
  working tree for the owner's commit of step (1), before the owner sets any row for that step.
  (FR-043, FR-067; PRO-075; RAT-082, RAT-086)
- [ ] T118 [US5] ⛔ **External design review** (**Owner**), arranged by the owner where possible,
  from `$REP/review-package/`; its row "External design review" in
  `specs/004-crypto-architecture-v3/spec.md` reads done, naming the package's manifest by SHA-256,
  or "not arranged", naming the latest selection record by path and SHA-256; no AI session is
  recorded as an independent or external reviewer. (FR-043, FR-063, FR-064; SC-013, SC-020; SEC-077,
  SEC-078)
- [ ] T119 [US5] Run the five freeze steps (contracts/cli.md; quickstart F2): (1) **Owner**: commit
  the feature files, the owner's next commit after the one that records the owner design review's
  approval, with the review entries and step (1)'s rows; (2) the agent runs
  `python scripts/design_freeze.py create` on a clean tree with that commit as HEAD, writing
  `$REP/freeze/freeze.json` with `freeze_status` `draft` and `owner_commit`; (3) **Owner**: `python
  scripts/design_freeze.py approve --by NAME --wording TEXT`; (4) **Owner**: commit the record; (5)
  the agent runs `python scripts/design_freeze.py validate`, exit 0. Where the owner commits
  "Environment record <n>" or "Log repair <n>" on its own between the approval and step (1), the
  owner design review is held again in "Owner design review <k>" first. (FR-043; SC-013; PRO-070,
  PRO-072, REP-092, REP-093)
- [ ] T120 [US5] ⛔ **Design freeze** (**Owner**): the row "Design freeze" in
  `specs/004-crypto-architecture-v3/spec.md` names the approved freeze record by path and SHA-256
  and its `owner_commit`, set and committed by the owner. (FR-043; Principle VIII)

**Checkpoint**: `phyco-v3` frozen with its hashes; features 005 to 007 analyse one fixed object. The
phase ends with the constitution's phase report to the owner.

---

## Phase 9: Polish and Final Report (plan phase 9)

**Purpose**: inside FR-043's window, so the agent writes each file and the owner commits it
(SEC-084).

- [ ] T121 Update `README.md`, CRLF kept: the status of `phyco-v3` with FR-051's sentence on it
  beside the line on the seed, and the documentation drift of checklist group F corrected. (FR-051,
  FR-069; SC-018; SEC-086)
- [ ] T122 Append an addendum to `reports/002-core-dynamics-redesign/phase-report.md`, after
  checking that no freeze record of features 002 and 003 hashes it, stating that S13 contradicts its
  "invertible-looking ARX" and pointing to `phyco-v3`'s evidence. (FR-051; SC-012)
- [ ] T123 Run `python scripts/check_claims.py` and `python -W ignore -m unittest tests.test_claims`
  over the final documents: 0 findings (quickstart F4). (FR-050, FR-069; SC-015, SC-018; SEC-081)
- [ ] T124 Run `python scripts/recheck_004.py` in a fresh clone, on a machine of the owner's choice:
  0 disagreements, its `recheck` record under `$REP/rechecks/` naming the interpreter, the platform
  and its `pip freeze`, and saying when that environment is not one of research R1's
  (quickstart F3). (FR-065; SC-017)
- [ ] T125 **heavy**, on the owner's go-ahead: run the whole suite under `tests/` on Windows,
  `python -W ignore -m unittest discover -s tests -t .`, and with `wpy` in WSL (quickstart P0),
  FR-053's two-worker test among it, under the heavy-run lock and projected first against
  research R7's feature-wide row, charging no candidate: every test passes, or skips naming its open
  item, and none fails; any record it writes stays in the working tree for the owner's commit
  (FR-043), and the commands and results go to the final report. (FR-045, FR-053, FR-058;
  Principle V)
- [ ] T126 Write the final report `$REP/phase-report.md` with `DESIGN_DISCLAIMER`, as the
  constitution's Phase Completion Reporting asks: every FR and SC with its evidence or listed as
  open; FUT-SEC-1 to FUT-SEC-9 with the statuses of the spec's table, FUT-SEC-7 open for feature
  007, and the FUT-GRID and FUT-HW rows; the evidence of every redesign-checklist item this feature
  covers; the re-decided feature-002 requirements; the input coverage, with 12 of 12 rules R1 to R12
  of the hardware note; who took each role; the classes of findings and the facts kept apart from
  arguments, observations and hypotheses; the risks of strategy note §11 as they stand, selection
  among up to six candidates on development inputs, the chance of a false raise of R and the
  common-mode caveat among them; the change-completion items still open, the statistical evaluation
  and the RTL; and the recommendation, to go on to feature 005 or to stop, a stop ending FR-043's
  window at the same commit. (FR-041, FR-047, FR-048, FR-049, FR-052, FR-060, FR-062, FR-064,
  FR-066; SC-002, SC-014, SC-019, SC-020)
- [ ] T127 ⛔ **Final result review** (**Owner**), in `specs/004-crypto-architecture-v3/spec.md`'s
  Review & Approval table: the owner's commit that records the decision, with the spec's Status
  line, ends FR-043's window; the standing authorization covers this feature's files again from the
  next commit, for the features that follow. (FR-043, FR-052; PRO-080; Principle VIII)

---

## Dependencies & Execution Order

- **Phase 0 → Phase 1**: T002 comes before every other task; T001 before it.
- **Phase 1**, in step order: (1) T003–T006; (2) T007–T023, each writer after its tests; (2a)
  T024 → T025, before every other write through `protocol/evidence.py` or a log writer; (3) T026;
  (4) T027 → T028, after T002; (5) T029; (6) T030 → T031; (7) T032; (8) T033 → T034; (9)
  T035 → T036; then T037.
- **Phase 2 (US1)** needs Phase 1; T043 is heavy and needs the owner's go-ahead; T045 comes before
  every task that writes key-loading code, from Phase 3 on (FR-001, FR-003).
- **Phase 3** needs T045, since its tools hold instantiation code (the propagation through
  instantiate, the related-key and related-nonce set); T048 comes before every tool it validates;
  the trail papers (T059) before their validations.
- **Phase 4 (US2)** needs Phase 1 only and may overlap Phase 3, having no heavy run; its review
  waits for Phase 8.
- **Phase 5** needs Phases 3 and 4: the security target fixes s, the key, the nonce and c before any
  score (FR-005, FR-006, FR-015); T087 before T088; T089 before the production-width analysis; T091
  before each size's first bias test; sizes in order.
- **Phase 6** needs the selection of T093; **Phase 7** needs Phase 6; **Phase 8** needs Phases 5 to
  7, with T107 before T108, T109 before T116 and every freeze step in order; **Phase 9** needs T120,
  or a stop from Phase 5, and T125 comes before T126.

### Parallel opportunities

- Phase 1: T020 beside the other test tasks, which share `tests/test_protocol_004.py` and
  `tests/test_records_004.py` and run in turn, as the scripts tested in `tests/test_protocol_004.py`
  (T013, T014, T015, T016) do; T033 ∥ T035.
- Phase 2: T038 ∥ T039.
- Phase 3: T046 ∥ T049; once T050 stands, T053 ∥ T054 ∥ T055 ∥ T056 ∥ T057 and T060 ∥ T061 ∥ T062 ∥
  T063 as code; their heavy validations still run one at a time.
- Phase 4 drafting (T069–T071) beside Phase 3's light tasks; its tests (T066, T067, T068) share
  `tests/test_records_004.py` and run in turn.
- Phase 5: T073 beside T075, T077, T081 and T083, which share `tests/test_protocol_004.py` and run
  in turn; the candidates' modules (T078, T079) may be drafted side by side, their `proposed`
  entries appended in turn under the log's lock.
- Phase 6: T096 ∥ T099; Phase 7: T104 beside T105, which runs in its own session.
- Phase 8: T113 beside T111 and T112.

## Implementation Strategy

1. **MVP = US1** (Phases 0 to 2, T001–T045): FUT-SEC-8 reproduced and reviewed, with the writers,
   logs and register it needs; one heavy run of under an hour.
2. **Tools** (Phase 3): every counted tool validated on known results.
3. **Security target** (Phase 4): the target fixed before any candidate is scored.
4. **Candidates and evidence** (Phase 5): the D4 choice, R by the round rule, selection or stop; a
   stop is a valid outcome, reported with what was reached.
5. **Model, vectors and transcription** (Phases 6 and 7).
6. **Reviews, freeze and final report** (Phases 8 and 9).

## Requirement Coverage

Every functional requirement and success criterion, with the tasks that cite it (Principle VII):

- FR-001: T023, T038, T039, T040, T041, T043
- FR-002: T038, T039, T040, T041, T042, T043
- FR-003: T023, T044, T045, T052
- FR-004: T069
- FR-005: T069
- FR-006: T069
- FR-007: T067, T069, T107
- FR-008: T069
- FR-009: T067, T069
- FR-010: T066, T067, T069, T107
- FR-011: T065, T069, T108
- FR-012: T017, T069, T108, T109, T110
- FR-013: T065, T070, T098
- FR-014: T070
- FR-015: T067, T070, T098
- FR-016: T070
- FR-017: T069, T095
- FR-018: T046, T047, T095
- FR-019: T046, T047, T057, T078, T092, T095
- FR-020: T047, T078, T095, T098
- FR-021: T051, T078, T092, T095
- FR-022: T073, T074, T078, T079, T083, T084, T087, T088, T089, T090, T095
- FR-023: T010, T012, T027, T054, T077, T080, T095, T097
- FR-024: T054, T077, T080, T095, T097
- FR-025: T095
- FR-026: T073, T074, T095
- FR-027: T095
- FR-028: T083, T085, T093, T095
- FR-029: T055, T058, T092, T095, T108
- FR-030: T095, T111
- FR-031: T095
- FR-032: T047, T095
- FR-033: T096, T098
- FR-034: T066, T068, T069, T070, T071, T072, T095, T111
- FR-035: T024, T096, T098, T102
- FR-036: T099, T100, T102
- FR-037: T051, T053, T055, T056, T057, T058, T081, T082, T091, T092
- FR-038: T008, T060, T061, T062, T063, T082, T088, T092
- FR-039: T008, T015, T048, T049, T050, T051, T052, T053, T054, T055, T056, T057, T058, T060, T061,
  T062, T063, T064, T074, T088
- FR-040: T008, T023, T033, T034, T039
- FR-041: T010, T013, T014, T075, T076, T078, T079, T080, T081, T082, T083, T085, T087, T093, T094,
  T126
- FR-042: T035, T036
- FR-043: T085, T109, T113, T114, T116, T117, T118, T119, T120, T125, T126, T127
- FR-044: T001, T002, T008, T010, T012, T013, T015, T027, T028, T077, T109
- FR-045: T005, T008, T009, T014, T042, T043, T081, T125
- FR-046: T016, T027, T029, T030, T031, T059, T065
- FR-047: T077, T126
- FR-048: T126
- FR-049: T126
- FR-050: T020, T123
- FR-051: T018, T112, T121, T122
- FR-052: T126, T127
- FR-053: T003, T004, T005, T006, T008, T009, T014, T015, T024, T025, T037, T038, T039, T040, T042,
  T049, T050, T063, T081, T125
- FR-054: T095, T101
- FR-055: T095, T098
- FR-056: T101, T102, T106
- FR-057: T103, T104, T105, T106
- FR-058: T015, T031, T032, T037, T096, T102, T125
- FR-059: T068, T095, T096, T098, T099, T100
- FR-060: T041, T043, T082, T126
- FR-061: T008, T009, T041, T082
- FR-062: T071, T111, T126
- FR-063: T115, T118
- FR-064: T105, T116, T118, T126
- FR-065: T009, T049, T051, T066, T081, T086, T124
- FR-066: T112, T126
- FR-067: T010, T011, T013, T026, T072, T104, T105, T117
- FR-068: T007, T009, T020
- FR-069: T017, T018, T019, T020, T021, T022, T107, T110, T121, T123
- SC-001: T041, T043, T045
- SC-002: T126
- SC-003: T066, T067, T107
- SC-004: T057, T092
- SC-005: T055, T083, T085, T092, T093
- SC-006: T054, T077, T097
- SC-007: T049, T051, T052, T053, T054, T055, T056, T057, T058, T060, T061, T062, T063, T064, T074
- SC-008: T085, T092, T093
- SC-009: T097, T099, T100, T101, T102
- SC-010: T096, T098, T102
- SC-011: T033, T034, T075, T076, T079
- SC-012: T035, T036, T122
- SC-013: T068, T111, T116, T118, T119
- SC-014: T126
- SC-015: T020, T123
- SC-016: T101, T104, T106
- SC-017: T082, T086, T124
- SC-018: T020, T021, T022, T121, T123
- SC-019: T126
- SC-020: T026, T115, T118, T126

FUT-SEC traceability (spec, "Security Policy traceability"), through the requirements the table
names:

- FUT-SEC-1, key entropy (FR-005, FR-006, FR-010): T066, T067, T069, T107
- FUT-SEC-2, reachable secret state (FR-009, FR-010, FR-015, FR-017): T066, T067, T069, T070, T095,
  T098, T107
- FUT-SEC-3, stream separation (FR-006, FR-014): T069, T070
- FUT-SEC-4, reseeding (FR-004, FR-016): T069, T070
- FUT-SEC-5, initialization analysis (FR-013, FR-014, FR-029, FR-049): T055, T058, T065, T070, T092,
  T095, T098, T108, T126
- FUT-SEC-6, output limit (FR-007): T067, T069, T107
- FUT-SEC-7, re-validation (FR-035, FR-036, FR-043): T024, T085, T096, T098, T099, T100, T102, T109,
  T113, T114, T116, T117, T118, T119, T120, T125, T126, T127
- FUT-SEC-8, demonstration first (FR-001 to FR-003): T023, T038, T039, T040, T041, T042, T043, T044,
  T045, T052
- FUT-SEC-9, certification route (FR-011): T065, T069, T108

## Notes

- Never edit an expected value to make a test pass (FR-056); a disagreement is a finding, analysed
  as the protocol says.
- Downloads are untrusted: each goes into its own new directory, nothing runs from inside it, and
  Python reads it with `-I`; `169.pdf` and `47270450.pdf` come only through the owner's browser.
- `README.md` and `security.md` keep CRLF and are edited only by scripts that keep it; the feature's
  Markdown files, this one included, are LF.
- No document of this feature uses the wording FR-050 forbids; `scripts/check_claims.py` and its
  allow-list decide, and every new entry is listed for the owner at the next ⛔ gate (SEC-087).
- Every phase ends with the constitution's phase report: files created or modified, requirements
  addressed, tests run with their exact commands, open issues, security concerns and a
  recommendation to proceed, revise or stop.
- The protocol only becomes stricter (FR-044): a change is proposed by the agent with
  `scripts/protocol_change.py propose FILE` and made only with the owner's approval, before any
  result it affects.
- Test runs at a phase's checkpoint are light: until T081 adds FR-053's two-worker test, the whole
  suite on both platforms, as T037 runs it; from then on, the phase's own test modules by their test
  classes, FR-053's two-worker test left out. A run that includes that test, the whole suite or
  `tests/test_records_004.py` among them, is a heavy run that waits for the owner's go-ahead
  (FR-045), and T125 is that run before the final report.
