---

description: "Task list for feature 005, cryptographic architecture, second design round (phyco-v4)"
---

# Tasks: Cryptographic Architecture, Second Design Round (phyco-v4)

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v4` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

**Input**: Design documents from `/specs/005-crypto-architecture-v4/`

**Prerequisites**: spec.md (the owner's spec approval of 2026-11-09, b1b79d8, with D1–D14 as their
defaults), plan.md (plan approval of 2026-11-09, afc6769, with the run limits extended as option E;
the plan's documents as of 74dd867), research.md (R1–R14), data-model.md, contracts/cli.md,
quickstart.md and `research/005/plan-projections.json`, with checklist-choices.md and the six
checklists, whose choices of rounds 1 to 5 were answered in advance on the owner's instruction of
2026-11-09 and applied; round 6 found no new item (ade430c), which ended the checklist loop.
Feature 004's documents at 99e6994, as FR-001 names them, are the baseline: where this list and an
inherited text differ, this feature's documents apply, and an inherited requirement is cited as
"inherited FR-<n>" (FR-001).

**Tests**: included. Principle II asks for a bit-accurate reference model with reproducible
automated tests and committed golden vectors, Principle IV forbids weakening an acceptance criterion
to obtain a passing result, and FR-025 carries feature 004's tests of the model, its vectors and its
freeze for `phyco-v4`. This feature's own tests go to `tests/test_protocol_005.py`, beside the tests
of each changed module (plan, Technical Context); within each group, tests come before the code
they test. Property tests use Hypothesis with the deterministic profile of inherited research R17.

**Organization**: phase k of this list is plan phase k ("Plan Phases"), so a reference to a plan
phase in the spec, the contract or the quickstart reads the same here; Phase 0 holds the steps
before the tasks approval. Phases 2 and 3 run in either order, each after Phase 1 and both before
Phase 5 (spec FR-005; plan, Summary). Stories: US1, every run planned before any candidate (P1: the
plan's numbers, approved, and Phase 2's probes and projection table, the MVP); US2, the security
target first (P2: Phase 3, with the later review of FR-012 in Phase 8); US3, the climb (P3: its code
and runs in Phase 5, the re-check of its records in Phase 1); US4, evidence, selection or a stop
(P4: Phase 5); US5, the model, its vectors, the reviews and the freeze (P5: Phases 6 to 8). Feature
004's scripts keep their names and run for this feature with the setting `PHYCOWEB_FEATURE=005`
(contracts/cli.md, "The feature setting"); the files they write for `phyco-v4` read `v3` as `v4`,
as the contract reads `model_v3` as `model_v4`: `phycoweb/model_v4.py`, `phycoweb/constants_v4.py`,
`phycoweb/selftest_v4.py`, `vectors/phyco-v4/`, `tests/test_model_v4.py`,
`tests/test_vectors_v4.py`, `tests/v4_reference.py` and `tests/test_v4_transcription.py`.

⛔ marks a human review gate (Principle VIII): the agent stops there and waits for the owner.
**Owner** marks a task only the owner performs: `scripts/owner_record.py` (`environment` and
`owner-provided`), `--choose` in `scripts/d4_choice.py` and `scripts/round_rule.py`,
`scripts/design_freeze.py approve`, the approval step of `scripts/protocol_change.py create` and
`propose`, the owner's commits, freeze steps (1) and (4) among them, and every row of the spec's
Review & Approval table but those the spec's notes give the agent ("Checklist choices, round <k>"
and "Analysis remediation <k>", set on the owner's advance approval of 2026-11-09). Where the owner
gives a decision in writing, the agent writes and commits its row, quoting the owner's words with
their date, and performs an approval step only on the owner's written word for that step, the
record quoting it, as in feature 004 from 2026-11-05. **heavy** marks a heavy run (inherited
FR-045): it takes `data/heavy-run.lock`, the one lock of both features, projects first against its
row, runs at one thread (FR-007), never overlaps another heavy run and needs no go-ahead of its own,
by the owner's word of 2026-11-05, "dont wait to start any heavy runs".

The agent commits locally under the owner's standing authorization (constitution, Principle IX),
after each task or set of related tasks and about every 30 minutes, with no co-author line naming
an AI tool, and never pushes, tags or publishes; from the commit that records an owner design
review's approval to the final result review, it commits no file of this feature (inherited
FR-043), except where the owner's written word, recorded and committed by the agent quoting it,
stands in place of the owner's commit (spec, notes under the Review & Approval table). Feature
004's records, logs and documents are read-only (FR-003). No download is planned: a file needs the
owner's permission for that file, with its name, source, size and licence, in a row "Download <n>"
before it is fetched (inherited FR-046). Exit codes (contracts/cli.md): 0 done; 1 a finding or a
failed check; 2 refused by a guard, nothing written; 3 a tool failure.
`$REP` = `reports/005-crypto-architecture-v4`; `wpy` = `~/.venvs/phycoweb/bin/python` in WSL, run
from `/mnt/c/GIT/PhycoWeb-PRNG`. From T007 on, every command of this list runs with
`PHYCOWEB_FEATURE=005` in its environment unless its task says the setting is unset: in PowerShell
`$env:PHYCOWEB_FEATURE = '005'`, in WSL `export PHYCOWEB_FEATURE=005`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel: the task writes no file that another task of its phase writes, and
  depends on no incomplete task
- **[Story]**: US1 to US5 (spec.md, "User Scenarios & Testing")
- Each task ends with the requirements and success criteria it serves, with the research items and
  quickstart scenarios where they apply.

---

## Phase 0: Before the tasks approval

**Purpose**: the place check that the spec's notes ask for at the tasks approval, and the approval
itself. No task of phases 1 to 9 starts before T004.

- [ ] T001 Write `research/005/place_check.py`, feature 004's `research/004/place_check.py`
  (2392150) adapted to this feature's paths and to its lists' table form (spec, notes under the
  Review & Approval table; PRO-029): `FEATURE` `specs/005-crypto-architecture-v4/`, the plan
  approval's commit `afc6769`, the output `research/005/place-check.json`; each list read from its
  heading `### Rows that change the protocol (round <k>)`, or `(analysis remediation <k>)` for a
  section of its own outside a round (FR-031), its two commits from the sentence "The round's two
  commits are <choices> (its choices) and <apply> (its changes applied).", "batch's" for such a
  section, and its rows from the table `| Row | Rule | Direction | Why |`, the places of each row
  being the FR items, the research sections, the data-model sections and the contract's script
  sections, each keyed by its script's name, that its Rule cell names; each place's text read as
  feature 004's tool reads it, with the spec's bullets under "Pre-registered Design Protocol: the
  changed rules" in place of the protocol's paragraphs, the plan's table "Values this plan fixes
  before first use", and `quickstart.md` and `research/005/plan-projections.json`, each whole,
  beside them; standard library only, with the exit statuses of feature 004's tool. Check it on
  rounds 1 to 5: it finds each list's two commits and the places each row's Rule names, and records
  as changed by an edit that no row made the places of round 3 that the row "Checklist choices,
  round 3" names beyond its rows' "Where" (research R8 and R13, data-model §4 and §5, the contract).
  (FR-031; spec notes; PRO-029)
- [ ] T002 Once this file and every change of the `/speckit-analyze` loop are committed, run
  `python research/005/place_check.py --to HEAD`, which writes `research/005/place-check.json` over
  the commits from `afc6769` to HEAD; compare its places with the lists "Rows that change the
  protocol" in `specs/005-crypto-architecture-v4/checklist-choices.md`; list for the owner every
  place it records as changed by an edit that no row made, with its commit and the agent's proposed
  answer (an entry of its own, or no change of rule, with the reason); and commit the file alone. A
  later commit that changes a place before the protocol change log exists needs the comparison
  again, confirmed in "Place check <k>". (FR-031; spec notes)
- [ ] T003 Prepare the tasks approval in the agent's report: the approval commits since the plan
  approval (the rows "Checklist choices, round 1" to "round 5" and each "Analysis remediation <k>"),
  the allow-list entries added to `protocol/claims.json` since the last gate, those of security.md
  2.19 to 2.21 among them, the ticks the agent set in the six checklists on the owner's advance
  approval of 2026-11-09, the readings set aside (none in rounds 1 to 5), and T002's places with
  their proposed answers. (FR-026, FR-031; Principle VIII)
- [ ] T004 ⛔ **Tasks approval** (**Owner**), in `specs/005-crypto-architecture-v4/spec.md`'s Review
  & Approval table: review this list with the `/speckit-analyze` findings and their remediation;
  review the ticks in the six checklists, unticking any item not accepted; confirm each list "Rows
  that change the protocol", a row taken out being recorded beside its list with the owner's reason;
  set the row "Place check", naming `research/005/place-check.json` by SHA-256 with its
  `compared_to` and each place it records as changed by an edit that no row made, confirmed as an
  entry of its own or as no change of rule, with the reason; set the row "Readings set aside",
  reading Not needed where no listed change sets a reading aside; set the row "Tasks approval"; and
  commit the rows with the spec's Status line. (FR-031; spec notes; Principle VIII)
- [ ] T005 In the commit after T004's, write security.md's next version, CRLF kept, with its
  history entry: row 5a.1b's status naming the tasks approval as passed and the next gate, with its
  allow-list entry in `protocol/claims.json` where the claim test asks for one;
  `python -X utf8 scripts/check_claims.py` reports 0 findings. (FR-027; SC-007)

**Checkpoint**: tasks approved; "Place check" and "Readings set aside" decided at HEAD, where the
protocol change log's creation reads them (T015).

---

## Phase 1: Machinery and Logs (plan phase 1)

**Purpose**: plan phase 1 (research R9): the feature as a parameter of the code both features
share, so that this feature writes under its own paths while feature 004's verdicts, records and
re-check stay as they are (FR-003); this feature's environment records, its three logs with the
protocol change log's first entry (FR-031), the claim test's coverage with `phyco-v4`'s `fut_sec`
(FR-026, FR-030), the re-check of sums and trails (FR-016, FR-020), `plan_projections.py` reading
feature 004's records at 99e6994 (FR-004), the refused list's copy (FR-023) and the tests pinned to
their feature (FR-003). No candidate code is written here, and no whole-suite run is made for this
feature before T009 (FR-003).

### Step (1): the feature setting

- [ ] T006 Write the feature setting's tests in `tests/test_protocol_005.py` (research R9;
  data-model §1; contracts/cli.md, "The feature setting"): with `PHYCOWEB_FEATURE` unset or `004`,
  `protocol/evidence.py` gives feature 004's paths (`REP_REL`, `FEATURE_REL`, `SPEC_REL`,
  `RESEARCH_REL`, `DESIGN_REL`, `PROTOCOL_LOG_REL`, `CANDIDATE_LOG_REL`, `PROVENANCE_LOG_REL`,
  `DOWNLOADS_REL`, `SIDECAR_REL`, `SUPERSEDED_REL`, `REFUSED_LIST_REL`, `LOCAL_REL`), the model ID
  `phyco-v3`, the namespace `phycoweb-004/`, the candidate IDs `cand-A<k>` and `cand-B<k>` and
  feature 004's disclaimer, each value as at ade430c; with `005`, data-model §1's paths, `phyco-v4`,
  `phycoweb-005/`, `v4-A<k>` and `v4-B<k>`, and the disclaimer naming `phyco-v4`, word for word the
  text that opens the spec; any other value makes every script exit 2; `data/heavy-run.lock` and
  `data/log-append.lock` stay one lock for both features; a writer exits 2, writing nothing, for a
  record whose path and `feature` disagree or whose path lies under another feature's paths; every
  record written under `005` holds `feature` `"005"` and `config.PHYCOWEB_FEATURE`, and a record
  without the field reads as feature 004's; a record that cites the spec, research or design
  document copies the version it cites under `$REP/spec-versions/`, `$REP/research-versions/` or
  `$REP/design-versions/`; the development-input loader under `005` gives `phycoweb-005/` inputs and
  refuses every other namespace, `phycoweb-004/` included; a file of feature 004's downloads
  manifest is read as feature 004's, checked against that manifest's SHA-256 before it is read
  (FR-001); under `005` the validation lookup reads feature 004's validation records beside this
  feature's, a tool matched by its exact hash (`tool_sha256`, and a C tool's binary), so that
  feature 004's validations stay in force for the uses they cover (research R14); and the guard on
  instantiation code reads feature 004's row "FUT-SEC-8 result review" and its demonstration record
  at HEAD, from feature 004's spec and paths, under either setting (FR-030). (FR-001, FR-002,
  FR-003, FR-026, FR-028, FR-030; SC-007; R9, R14)
- [ ] T007 Make the feature a parameter of the shared code (research R9) until T006 passes:
  `protocol/evidence.py` reads `PHYCOWEB_FEATURE` once, `004` by default, and selects from it the
  paths, the model ID, the candidate IDs, the development-input namespace and the disclaimer;
  `protocol/disclaimer.py` gains feature 005's constant, the disclaimer naming `phyco-v4` word for
  word; `protocol/candidates.py`, `protocol/changelog.py`, `protocol/provenance.py`,
  `protocol/devinputs_v3.py` and every script of feature 004's contract read their paths through it,
  none keeping a literal feature-004 path for a write; and each record states its feature. Feature
  004's default keeps its paths, verdicts and re-check unchanged (T008). Under `005` the validation
  lookup reads both features' validation records (research R14). No tool file whose exact hash a
  validation record matches, its `tool_sha256` and a C tool's binary, changes here (T038). (FR-001,
  FR-002, FR-003, FR-026, FR-028; SC-007; R9, R14)
- [ ] T008 Add `--no-record` to `scripts/recheck_004.py`, which prints the result and writes nothing
  (contracts/cli.md, "`scripts/recheck_004.py` for feature 005"), and write FR-003's test in
  `tests/test_protocol_005.py`: with the setting unset, `python scripts/recheck_004.py --no-record`
  at HEAD gives the result that T132's committed record holds,
  `reports/004-crypto-architecture-v3/rechecks/recheck-20261110T010625Z-454c1890.json` (SHA-256
  `d53424fb529ab2254825c107a2f066dab702f46e66c0ef176787b5d5f6526f21`: 160 records, 0
  disagreements), and leaves every file under feature 004's paths as committed (quickstart V2).
  (FR-003; SC-005)
- [ ] T009 Pin each test to its feature (FR-003): each test that reads feature 004's committed
  records pins feature 004 for those reads, in `tests/test_records_004.py`,
  `tests/test_protocol_004.py`, `tests/test_tools_004.py`, `tests/test_claims.py` and every other
  module of `tests/` that reads them; every test that writes a record writes under the active
  feature's paths, feature 004's FR-053 test among them; and a test in `tests/test_protocol_005.py`
  shows that the modules run with `PHYCOWEB_FEATURE=005` write nothing under feature 004's paths.
  Run the changed modules by their test classes on Windows and with `wpy` in WSL, FR-053's
  two-worker test left out. (FR-003; SC-005)

### Step (2): this feature's environment records

- [ ] T010 **Owner**: write this feature's environment records with
  `python scripts/owner_record.py environment --platform windows --by NAME` on Windows and
  `wpy scripts/owner_record.py environment --platform wsl --by NAME` in WSL, into
  `$REP/environment-windows.json` and `$REP/environment-wsl.json`, even where the environment
  equals feature 004's records 3 and 4 (spec, Assumptions); add a row "Environment record <n>" per
  record to the spec's Review & Approval table, naming the platform, the printed approval hash and
  the date, set it to Approved and commit. Every later write of this feature names the record in
  force as its `environment`. (FR-003, FR-007; R9)

### Step (3): the refused list, the plan's numbers and the logs

- [ ] T011 [P] Create `research/005/refused-constants.json` as a byte copy of
  `research/004/refused-constants.json` at 99e6994
  (`git show 99e6994:research/004/refused-constants.json`): 66 entries, SHA-256
  `cdbcb8031d1de839dacd71abcabdec38869fa6b102c6e86f10cfea2eb52a8a95`, checked before the commit; the
  file grows afterwards only by this feature's stricter changes, each entered in the protocol change
  log with the list's new SHA-256; `REFUSED_LIST_REL` under `005` names it. (FR-023; R13)
- [ ] T012 [P] Change `research/005/plan_projections.py` to read feature 004's records as committed
  at 99e6994, through `git show 99e6994:<path>`, never from the working tree, its output unchanged:
  `python -X utf8 research/005/plan_projections.py --check` prints "plan-projections.json matches"
  and exits 0 on Windows and with `wpy` in WSL (quickstart V1), the committed
  `research/005/plan-projections.json` unchanged. (FR-004; SC-001; R1)
- [ ] T013 Adapt `protocol/changelog.py` and `scripts/protocol_change.py` to this feature (research
  R9), with their tests in `tests/test_protocol_005.py`: under `005`, `check` runs
  `research/005/place_check.py`; `create` reads `research/005/place-check.json`, this feature's rows
  "Place check" and "Readings set aside", and the lists of
  `specs/005-crypto-architecture-v4/checklist-choices.md` in their table form, round by round and
  section by section; it writes the first entry that FR-031 names, naming by SHA-256 FR-001's seven
  baseline documents (the committed blobs' bytes, LF, kind `raw`),
  `research/005/plan-projections.json` as committed then, feature 004's refused list, the spec as
  the row "Spec approval" names it and the plan's documents at 74dd867 with the values the row "Plan
  approval" and FR-031 give, then one entry per listed row of each answered round and batch, in
  order, citing its row, with its direction (`stricter`, `settled`, or a reading set aside as
  decided), every clarification row listed by its table; `propose FILE` writes a later entry for a
  row "Protocol change <k>" or "Readings set aside <k>"; an entry that sets a reading aside is
  refused unless its row decides it. Feature 004's mode keeps its behaviour. (FR-001, FR-031)
- [ ] T014 Write the first entries of this feature's provenance log `$REP/provenance.jsonl` with
  `python scripts/provenance.py add FILE`, one per file drafted before the log or per section
  changed: this feature's documents (spec, plan, research, data model, contract, quickstart, the
  seven checklists, `checklist-choices.md` and this file), `research/005/plan_projections.py`,
  `research/005/plan-projections.json`, `research/005/place_check.py`,
  `research/005/place-check.json`, the files of steps (1) to (3), and every file outside this
  feature's paths that this feature changes, from its first change by this feature and entered
  whole: security.md (from 2.18), `protocol/claims.json`, `.gitattributes`, and the shared code with
  its tests (research R9), feature 004's log keeping its last entries for them; each entry with the
  tool and model, the date, the task ID and its review status. (FR-031)
- [ ] T015 After T004, run `python scripts/protocol_change.py check` and report its places beside
  the confirmed rows; then **Owner**: run `python scripts/protocol_change.py create`, which writes
  the first entries of `research/005/protocol-changes.jsonl` (T013), and approve its entries at the
  approval step; the agent then commits the log. No evidence run, a probe included, starts before
  it. (FR-001, FR-005, FR-031)

### Step (4): the claim test and the register

- [ ] T016 Write the claim test's extension tests in `tests/test_claims.py` (research R10):
  `scripts/check_claims.py` scans this feature's documents and reports beside feature 004's, with
  `phyco-v4`, `v4-A<k>` and `v4-B<k>` among its model words; every hand-written document of this
  feature carries the disclaimer naming `phyco-v4`, word for word; this feature's gate rows are read
  from its own spec and feature 004's from feature 004's spec at HEAD, its row "FUT-SEC-8 result
  review" (ffb1425) among them (FR-013); the register gives `phyco-v4` L1 only while "L1 recorded"
  reads Approved and the rows and hashes it rests on hold at HEAD, and L0 otherwise; `phyco-v4`'s
  `fut_sec` holds the expected statuses that FR-030 carries, the later stages named by security.md
  §22's numbers since 2.18; the copies under `spec-versions/`, `research-versions/` and
  `design-versions/` read as the documents they copy (FR-001); each model's `in_progress` counts its
  own feature's searched `pass` bound records citing a validation record, a `split` record never
  counted (data-model §2), `phyco-v4`'s reading `none` until this feature's first such record; the
  code paths scanned gain `research/005/`, read from this feature's first commit; and a generated
  checklist line that a rule flags passes only through an allow-list entry giving FR-026's reason.
  Feature 004's rules and findings are unchanged. (FR-001, FR-013, FR-026, FR-030; SC-007; R10)
- [ ] T017 Extend `scripts/check_claims.py` until T016 passes, and give `phyco-v4`'s entry in
  `protocol/claims.json` its `fut_sec`: the statuses of feature 004's table "Security Policy
  traceability" read for `phyco-v4`, FUT-SEC-8 met by feature 004's demonstration and its review,
  FUT-SEC-7 open for the statistical re-validation feature 008, the analysis feature 006 named by
  its number (FR-030); `phyco-v3`'s entry stays as written. (FR-026, FR-030; SC-007; R10)
- [ ] T018 Run `python -X utf8 scripts/check_claims.py` over every document of this feature written
  before T017, the checklists and `checklist-choices.md` included (FR-026): fix each finding in text
  the agent wrote; for a generated checklist line, never rewritten, add an allow-list entry with its
  reason, that the line is a checklist question naming a parameter, a file or a rule, or quoting the
  passage it asks about, and states nothing of its own, naming the line as it reads once its state
  is final; for a line that states a level in a rule, an entry with the policy reason (research
  R10); 0 findings before T025's probes start; list the entries for the owner at the next ⛔ gate.
  (FR-026; SC-007)

### Step (5): the re-check of sums and trails

- [ ] T019 Write the re-check's tests in `tests/test_protocol_005.py` (quickstart V5, V7): a `split`
  record (data-model §2) recomputed from its two parts' committed bytes, as an exact rational sum,
  r₁ + r₂ = r, each part `pass` and established, of the same candidate, kind, size and width, never
  `inconclusive`, with its `alternatives` and the larger of the sum and `searched` checked; a part
  whose SHA-256 differs, or that is not established, gives a disagreement, and so does a part that
  no longer stands, a tool defect recorded against it, a sum standing only while both its parts
  stand (spec, Edge Cases); for a trail record (data-model §3), the exact differential probability
  and squared correlation of a two-input addition or subtraction modulo 2^w, of an addition of a
  committed constant by the carry's two-state automaton over the bits of c, and of an S-box from its
  table, each equal to an exhaustive count at w = 8 over stated inputs, outputs and constants; masks
  passed through the transpose of each linear step; the product as `"p/q"` with its −log₂; the class
  by the 2⁻¹²⁸ threshold, above it `confirmed vulnerability` of the rounds it covers, at or below it
  `none`; a test trail with every nonlinear operation recorded re-checks to its weight, and changing
  one operation's output gives a disagreement; and the operation list is read by a standard-library
  reader of the forms of `research/004/ir.py` under `protocol/`, its evaluation of each linear step
  equal to `ir`'s on the reference designs' committed lists. (FR-016, FR-019, FR-020; SC-005)
- [ ] T020 Extend `scripts/recheck_004.py` for this feature (contracts/cli.md) until T019 passes:
  under `005` it recomputes every `split` bound from its two parts, and every trail's weight,
  transitions and class from its characteristic, the candidate's committed operation list, read by
  T019's standard-library reader and never through `research/004/ir.py` or numpy, so that the
  re-check imports only the standard library and `protocol/` and runs in any environment, as
  inherited, and, where the list holds an addition of a committed constant, the constant table the
  record names by SHA-256; its `recheck` record names the feature; a disagreement is a tool defect
  that blocks the candidate (inherited FR-065). (FR-016, FR-019, FR-020; SC-005)

### Step (6): the phase's closing run

- [ ] T021 **heavy**: after T015, run the whole suite with `PHYCOWEB_FEATURE=005` on Windows,
  `python -W ignore -m unittest discover -s tests -t .`, and with `wpy` in WSL, under the heavy-run
  lock, projected first against the feature-wide row's share for whole-suite runs (two per platform,
  plan, "Values this plan fixes before first use"): every test passes, or skips naming its open
  item, none fails, and nothing is written under feature 004's paths; record the commands and
  results for the phase report. (FR-003, FR-008; SC-008; Principle V)

**Checkpoint**: the setting stands with feature 004's re-check unchanged; this feature's
environment records read Approved; the protocol change log holds its first entries, naming the
baseline documents and `plan-projections.json` by SHA-256; the provenance log and the candidate
log's writer stand under this feature's paths; the claim test covers `phyco-v4` with 0 findings.
The phase ends with the constitution's phase report to the owner.

---

## Phase 2: User Story 1 - Every run planned before any candidate (Priority: P1) 🎯 MVP

**Goal**: the probes of research R5 on the reference designs' committed operation lists, and the
final projection table committed before the candidate log's first `proposed` entry, every value at
most the plan's (FR-005, FR-009; R5).

**Independent Test**: quickstart V1 and V3: `plan_projections.py --check` and
`projection_table.py --check` exit 0 on both platforms; every value in the table is at most the
plan's, and every row holds at least twice the projected needs it holds, the rows of the families
that hold candidates (SC-001).

- [ ] T022 [US1] Write the tests of the probes and the projection table in
  `tests/test_protocol_005.py` (contracts/cli.md, "`scripts/evidence_v3.py … --probe`" and
  "`scripts/projection_table.py [--check]`"; data-model §4): `--probe` exits 2 once any `proposed`
  entry exists; it writes a `projection` record charged to the feature-wide row, at one thread,
  holding `finished` with the hours taken or `reached the probe limit` at 4 h, its outputs other
  than timing discarded unread; a probe that would take the probes past their 40 h share is refused,
  its run keeping the plan's projection (FR-005); before `$REP/projection-table.json` exists, the
  row and the 40 h share are read from `plan-projections.json`'s approved option; a structural or
  bias probe runs at R = 66 rounds (research R5); `projection_table.py` exits 2 once any `proposed`
  entry exists, when `plan-projections.json` fails its `--check`, or when a listed probe record is
  missing; each value is the smaller of the approved option's and the probes', never raised; a
  search probe that reached the limit reads as its search reaching its cap; a structural or bias
  need is the smaller of the provisional need (12 h and 24 h per candidate) and the sum over the
  sizes of each finished probe's hours and each other size's equal share (4 h and 8 h), a probe
  lowering it only by the kinds it covers (research R5); the table holds numbers, record IDs and
  fixed field names and no prose (FR-024), with `plan_projections_sha256` and its kind `raw`;
  `--check` recomputes it and exits 1 on a difference; a probe that shows a need above its row is
  printed and recorded. (FR-005, FR-009, FR-024; SC-001)
- [ ] T023 [P] [US1] Add `--probe` to `scripts/evidence_v3.py` (contracts/cli.md; research R5) until
  T022's probe tests pass: the run itself on a reference design's committed operation list,
  `research/004/candidates/cand-A1.py` or `cand-B1.py`, read and never written, up to 4 h, written
  as a `projection` record charged to the feature-wide row at one thread, the row and the probes' 40
  h share read from `plan-projections.json`'s approved option while the projection table does not
  exist; the guard that refuses an operation list without a `proposed` entry reads, for a probe,
  feature 004's candidate log, where both reference designs hold theirs. (FR-005, FR-007; SC-001;
  R5)
- [ ] T024 [P] [US1] Write `scripts/projection_table.py [--check]` (contracts/cli.md; data-model §4)
  until T022 passes: per family, size and kind, each listed run with `need_h`, its source (a
  feature-004 run or a probe, by `record_id`, path and SHA-256 over the committed bytes, kind `raw`,
  or `cap`) and the value fixed, from the option `plan-projections.json` names as
  `approved_option`; per candidate row, the value the plan fixed and the value that holds; the caps;
  and the sum against the ceiling. (FR-005, FR-009, FR-024; SC-001)
- [ ] T025 [US1] **heavy**: run the probes of research R5 one at a time, each projected first
  against the feature-wide row's 40 h share of probes, a probe being refused once it would pass that
  share: one structural check (one run of every structural kind that inherited FR-037 asks at that
  size, each kind's hours in the record) and one frequency and avalanche measurement per claimable
  size and reference design at w = 32, each at R = 66 rounds, R_max + Δ (research R5), at 4×4, then
  8×8, then 16×16, first, as the kinds feature 004 never ran at that width (research R5's
  rationale); then each listed search of `plan-projections.json`'s approved option that feature 004
  neither made nor ran to its cap (B1's searches at 8×8 and 16×16, A1's differential search at 16×16
  and r = 5), at 16×16, then 8×8, each climb in its listed order; each with
  `python scripts/evidence_v3.py --probe` and the run's design, kind, size and r, into
  `$REP/projections/`. A run feature 004 made is cited, not probed (plan, "Choices for owner
  review"). No order raises a value: a refused probe keeps the plan's need. (FR-005, FR-007, FR-009;
  SC-001, SC-008; R5)
- [ ] T026 [US1] Run `python scripts/projection_table.py`, which writes
  `$REP/projection-table.json`, then `--check` on Windows and with `wpy` in WSL, exit 0 (quickstart
  V3); commit the table before any `proposed` entry; report to the owner, before the first
  `proposed` entry, every probe that shows a need above its row (FR-009). (FR-005, FR-009; SC-001)
- [ ] T027 [US1] ⛔ **Protocol change <k>** (**Owner**), only where T026 reports a need above its
  row: the owner decides under FR-009 before the first `proposed` entry, lowering the candidate
  limit of the family whose row cannot hold the run, to zero where every candidate of that family
  would need it, a stricter change set in a row "Protocol change <k>" and entered with
  `python scripts/protocol_change.py propose FILE`, or leaving the rule, the run then being refused
  when it comes, its cause shared (FR-018); otherwise this task is marked not applicable, naming the
  table by SHA-256. (FR-009, FR-031; SC-001)

**Checkpoint**: the projection table committed before any candidate; every row checked against its
needs at every claimable size (SC-001). The phase ends with the constitution's phase report to the
owner.

---

## Phase 3: User Story 2 - The security target first (Priority: P2)

**Goal**: the design document's and `rationale.md`'s chapters "Security target" and "Mode",
Version 0.5, started from feature 004's Version 0.4 with every change listed; the security target's
files with R as placeholders; the ⛔ security-target review before any candidate is proposed; "L1
recorded" (FR-010 to FR-013, FR-027; R8).

**Independent Test**: the review row, the chapters' SHA-256 and the order of the commits: the
review's approval commit precedes the candidate log's first `proposed` entry (SC-002); quickstart
V4: `scripts/candidate_log.py propose` exits 2 while the row is pending, and appends once it reads
Approved at HEAD with the chapters' SHA-256.

- [ ] T028 [US2] Write the candidate log's tests for this feature in
  `tests/test_protocol_005.py` (quickstart V4; data-model §5; contracts/cli.md,
  "`scripts/candidate_log.py propose …`"): `propose` exits 2, appending nothing, while the row
  "Security-target review" does not read Approved at HEAD with the chapters' SHA-256 it names, or
  while `$REP/projection-table.json` does not exist, for every `proposed` entry, and appends once
  both hold; `--derived-from PATH:SHA256 --relation derived|starting-point [--changes TEXT]` writes
  `derived_from` as `{feature: "004", candidate, oplist_path, oplist_sha256, relation, changes}`,
  `changes` reading `none` for `derived`, and without `--derived-from`, `derived_from` reads `none`;
  a fourth evaluated candidate of one family exits 2, the limit read from the plan approval (three).
  (FR-011, FR-022, FR-023; SC-002)
- [ ] T029 [US2] Extend `protocol/candidates.py` and `scripts/candidate_log.py` until T028 passes
  (contracts/cli.md; data-model §5). (FR-011, FR-022, FR-023; SC-002)
- [ ] T030 [US2] Write the security target's tests for this feature in `tests/test_protocol_005.py`,
  running feature 004's tests of its chapters and security-target files from
  `tests/test_records_004.py` with the feature as their parameter: each document's header (its
  title, the design-form disclaimer naming `phyco-v4` and one line "Version: 0.5"), the two version
  lines equal; the chapters in inherited FR-034's order, each once, those after "Mode" reading "Not
  drafted yet"; `$REP/security-target/parameters.json` and `limits.json` with feature 004's fields,
  computed from the chapter "Security target"'s parameter table while "Permutation" holds no variant
  table (research R8), a placeholder R (`<R4>`, `<R8>`, `<R16>`) read as not yet known and every
  other figure checked; the chapter's parameter table and output limits restating the files;
  `rationale.md`'s chapters "Security target" and "Mode" each with a section "Changes from Version
  0.4", every change with its reason, each value there cited by the design document's chapter and
  section (FR-010); and `phyco-v4`'s register `bound` holding the profile's `bound_bits` by variant
  ID, placeholders included, with its `evidence` naming both files (FR-011). (FR-010, FR-011,
  FR-026; SC-007)
- [ ] T031 [US2] Make `scripts/mode_limits_v3.py` read for this feature (research R8) until T030's
  file tests pass: under `005` it reads `specs/005-crypto-architecture-v4/design.md`, taking the
  variant rows from the chapter "Security target"'s parameter table until the chapter "Permutation"
  holds its variant table (research R8), takes a placeholder R as not yet known, computes every
  figure that does not depend on R and writes the placeholder where one does, and writes
  `$REP/security-target/parameters.json` and `limits.json`; a theorem stays `unverified` until its
  paper is read, feature 004's `fetched` entries read as FR-001 states; feature 004's mode is
  unchanged. (FR-001, FR-010, FR-011; SC-007; R8)
- [ ] T032 [US2] Write `specs/005-crypto-architecture-v4/design.md`, Version 0.5 (FR-010; research
  R8): its header (the title "phyco-v4: design document", the design-form disclaimer naming
  `phyco-v4`, "Version: 0.5"); the chapters "Security target" and "Mode" copied from feature 004's
  `design.md`, Version 0.4, its SHA-256 as FR-010 names it, read with `phyco-v4` for `phyco-v3`,
  citing feature 004's requirements, decisions and research items as "feature 004's FR-<n>" (D<n>
  and R<n> alike) and naming the later features by security.md §22's numbers, T2's and T11's
  deferrals going to feature 006 and T4's and its risk's to feature 009; the key of 256 bits, the
  capacity of 384 bits at every claimable size and the bound of 128 bits as FR-010 states them,
  targets and a ceiling; FR-012's open items under a heading of their own in "Security target": the
  round counts `<R4>`, `<R8>` and `<R16>` with every figure computed from them, the margin of
  instantiation's diffusion over R_f, the first-order related-key and related-nonce differences, and
  the functionality class, which moves there from Version 0.4's "here at the security-target
  review"; the chapter "Security target"'s parameter table with R as the placeholders, from which
  the security target's files are computed (research R8); the chapters after "Mode" reading "Not
  drafted yet" until Phase 6; each section entered in `$REP/provenance.jsonl` as it is drafted.
  (FR-010, FR-012, FR-026; SC-002, SC-007; R8)
- [ ] T033 [US2] Write `specs/005-crypto-architecture-v4/rationale.md`, Version 0.5: its header (the
  title, the design-form disclaimer naming `phyco-v4`, "Version: 0.5"); its chapters "Security
  target" and "Mode" copied from feature 004's `rationale.md`, Version 0.4, its SHA-256 as FR-010
  names it, read and changed the same way, each statement with one of inherited FR-062's seven
  labels, and in each a section "Changes from Version 0.4" listing every change made in both
  documents' chapters with its reason, each value cited by the design document's chapter and
  section; the later chapters "Not drafted yet"; each section entered in the provenance log.
  (FR-010, FR-026; SC-002, SC-007; R8)
- [ ] T034 [US2] Run `python scripts/mode_limits_v3.py --out $REP/security-target/limits.json`,
  which writes `parameters.json` beside it with R as the placeholders; in the same commit, write
  `phyco-v4`'s `bound` in `protocol/claims.json` from the profile's `bound_bits` by variant ID,
  placeholders included, and its `evidence`, both files by path and SHA-256 (FR-011);
  `python -X utf8 scripts/check_claims.py` reports 0 findings. (FR-011; SC-007)
- [ ] T035 [US2] Prepare the security-target review: compute the set the row will name, the SHA-256
  of each of the four chapters ("Security target" and "Mode" of both documents), each from its
  heading line to the next heading of the same or a higher level, and of `parameters.json` and
  `limits.json`, with the version read; and list for the owner the approval commits and the
  allow-list entries added since T004, and the open items the chapter lists. (FR-011, FR-012;
  SC-002)
- [ ] T036 [US2] ⛔ **Security-target review** (**Owner**), in the spec's Review & Approval table,
  before any candidate is proposed: the row names T035's set by SHA-256 with the version read. A
  decline ends in chapters revised and reviewed again in "Security-target review <k>", no candidate
  proposed meanwhile; a parameter change found needed is made only in the stricter direction, a
  larger capacity with the key and the nonce unchanged, as a change to FR-010 listed under FR-031
  before the review's approval, the output limits recomputed (spec, Edge Cases). In the commit after
  the row's, the agent writes security.md's next version recording the gate in row 5a.1b's status,
  CRLF kept. (FR-010, FR-011, FR-027, FR-031; SC-002; Principle VIII)
- [ ] T037 [US2] ⛔ **L1 recorded** (**Owner**), once the claim test covers `phyco-v4` (T017) and
  the row "Security-target review" reads Approved: the row "L1 recorded" names that row and feature
  004's row "FUT-SEC-8 result review" (ffb1425), each with what it reviewed by path and SHA-256; in
  the same commit (FR-013), the agent sets `phyco-v4`'s `claim_level` and `history` in
  `protocol/claims.json` to the level the rows give, with its `evidence` listing feature 004's
  demonstration record
  (`reports/004-crypto-architecture-v3/fut-sec-8/demonstration-20261104T165604Z-4406adb9.json`, by
  path and SHA-256) and the files the two rows name, and security.md §1.1 and §15 with a version of
  the family that records `phyco-v4`'s level and its history entry, CRLF kept;
  `python -X utf8 scripts/check_claims.py` reports 0 findings. (FR-013, FR-027, FR-030; SC-007)

**Checkpoint**: the security target reviewed before any candidate, the level recorded, and the
candidate log's guard open. The phase ends with the constitution's phase report to the owner.

---

## Phase 4: Tool Validation where a tool changed or is new (plan phase 4)

**Goal**: every tool whose results count holds a validation record of its exact hash (inherited
FR-039; research R14 on inherited R12): the ARX search's companion of research R7, which writes the
state at every addition (FR-019), written and validated, feature 004's tools unchanged (FR-003),
and any tool that changes validated again before its first counted use (spec, Edge Cases, "A
feature-004 tool changed").

- [ ] T038 For each tool of feature 004's validation records that Phase 5 uses, the trail tools,
  the structural and bias tools and the cost model among them, compare its exact hash at HEAD with
  the hash its validation record names, and record for the phase report each tool with its record
  ID, the result and whether its validation covers additions of committed constants (FR-016);
  feature 004's records stay in force for the uses they cover while the hash is unchanged. (FR-016,
  FR-022; R14)
- [ ] T039 Write research R7's companion of the ARX search,
  `research/005/tools/trails/arx_search_ops.c` with its build file, a copy of feature 004's
  `research/004/tools/trails/arx_search.c` whose trail output adds the state after every step of
  every round, feature 004's tool unchanged (FR-003), with its tests first in
  `tests/test_tools_005.py`: on the ARX search's known results
  (`research/004/tools/trails/arx_search_known.py`) it finds the optimum weights and round-boundary
  states that feature 004's tool finds, and each step's printed input and output give that step's
  exact weight, the weights summing to the trail's; then validate it with
  `python scripts/validate_tool.py` on those known results under this feature's paths, **heavy**
  where its run is, before its first counted use. Validate the same way each tool whose hash differs
  (T038), a tool that Phase 5 changes later and one written for additions of committed constants
  (FR-016), each before its first counted use, the evidence runner refusing it meanwhile. (FR-003,
  FR-016, FR-019; SC-005; R7, R14)

**Checkpoint**: every tool of Phase 5 holds a validation record of its exact hash. The phase ends
with the constitution's phase report to the owner.

---

## Phase 5: User Stories 3 and 4 - Candidates and Evidence (plan phase 5)

**Goal**: the round rule's sums and its 16×16-first order, the trail records at every nonlinear
operation, the candidates entered, the D4 choice made once, then the production-width climbs at
16×16, 8×8 and 4×4, the structural checks and the bias tests at 4×4, 8×8 and 16×16, until the round
rule gives R and the rules select a candidate or stop; the selection-bias statement over features
004 and 005 (FR-014 to FR-024; R6, R7, R11 to R13).

**Independent Test**: quickstart V5 to V7 and V9: from a candidate's committed records alone, the
re-check recomputes every sum, every trail's weight and R_bound at each size (SC-003, SC-005);
every candidate without R_bound at 16×16 decided with no hour at 8×8 or 4×4 (SC-004); the
selection-bias statement checked against both features' candidate logs (SC-006).

**Rules**: one heavy run at a time, each projected first, at one thread (FR-007), within its size's
cap and its candidate's row as `$REP/projection-table.json` fixes them, at most the plan's (caps of
8 h at 4×4, 24 h at 8×8 and 48 h at 16×16; an ARX candidate's row 267.5 h, a Boolean candidate's
425.3 h), all heavy runs within the ceiling of 2,200 h (FR-008); at most three evaluated candidates
per family; D4 chooses the family, the other analysed at the production width only if the chosen
one ends with no eligible candidate (D14).

- [ ] T040 [US3] Write the round rule's tests for this feature in `tests/test_protocol_005.py`
  (quickstart V5, V6; contracts/cli.md, "`scripts/round_rule.py --candidate ID`"; data-model §2): at
  the production width the climbs run at 16×16, then 8×8, then 4×4; a size-independent search, such
  as an ARX box's bound over one call, runs first under the 4×4 cap, charged to the trail row, its
  bound read at every size and its hours counted at no size, and if it is capped or refused it ends
  that kind's searches at every size, the candidate decided at 16×16; at a size r ascends from 1,
  the linear search before the differential at each r, each kind independent; the first capped or
  refused search of a kind ends that kind's searches at that size, the refusal written in its
  `projection` record; after each r a `split` record is written where the largest sum W(r₁) + W(r₂),
  r₁ + r₂ = r with r₁ and r₂ at least 1, of that kind's established bounds at that size, sums
  included, exceeds the searched bound or stands where none ran: exact rationals, its two parts
  cited by record ID and SHA-256, `alternatives`, `searched`, `tool` and `validation` `none`,
  `budget` `{cap_hours: none, hours_used: 0}`, feature 004's scope statement word for word; a sum
  never cites an `inconclusive`, capped, refused or blocked record; a kind's climb at a size ends at
  the first r whose established bound has weight above 128, with no search of that kind at that r or
  beyond, and continues by sums after its searches end, up to R_max = 64; a design whose rounds
  repeat in no cycle, or that holds an addition of a committed constant, takes no sum and no other
  bound resting on the repetition, and a design holding such an addition has each call type's
  permutation covered by its bounds, each round's constants modelled (FR-016); where a cycle spans
  more than one round, searches and sums come at whole cycles; R_bound is the smallest r at which
  both kinds' bounds have weight above 128, never lowered by a later search; on a test operation
  list with no size-independent search, whose first linear search at 16×16 reaches a tiny cap, the
  candidate is decided `ineligible` with the cause `no R_bound at 16×16`, the record that ends the
  climb and the statement that no hour was charged at 8×8 or 4×4 (quickstart V6); the decision comes
  as soon as either kind's established bounds at 16×16 cannot pass weight 128 by R_max, a running
  search of the other kind then stopped, its record `inconclusive` and its hours charged; R =
  max(2·R_dist, R_bound + Δ, 2·max(R_f, R_b)), Δ = 2; and `round-rule.json` names, per size and
  kind, the record that sets R_bound, searched or `split`, the last searched record and the r of the
  first capped or refused search. (FR-014, FR-015, FR-016, FR-017, FR-018, FR-022; SC-003, SC-004)
- [ ] T041 [US3] Change `scripts/round_rule.py` for this feature (contracts/cli.md; data-model §2;
  research R6, R12) until T040 passes; feature 004's mode keeps its rule. (FR-014, FR-015, FR-016,
  FR-017, FR-018; SC-003, SC-004)
- [ ] T042 [US3] Write the trail record's and the evidence runner's tests in
  `tests/test_protocol_005.py` (data-model §3; quickstart V7): a `trail` record that
  `scripts/evidence_v3.py` writes under `005` holds the characteristic at every nonlinear operation
  of every round, `round`, `state_in`, `operations` with
  `{op_index, position, inputs, output, weight}` in the operation list's order, and `state_out`,
  with `weight` at the top as `"p/q"` and its −log₂; a bitwise Boolean function recorded as the
  S-boxes the validated tool counts (feature 004's four-update NOR network as one 4-bit S-box per
  bit position, table 9 c 3 0 2 5 4 7 6 1 a b 8 d e f); an addition of a committed constant naming
  the constant table by SHA-256; an operation list holding any other nonlinear operation gets no
  trail search, the candidate `blocked` for that cause (FR-020); under `005` the runner refuses a
  bound search at 8×8 or 4×4 before the candidate's 16×16 climb has ended, and a structural or bias
  run out of the order 4×4, 8×8, 16×16; every search records thread count 1 and its size's cap from
  the projection table, and every other record states its thread or worker count (FR-007); a search
  whose projection does not fit its row is refused, the refusal in its `projection` record. (FR-006,
  FR-007, FR-014, FR-015, FR-019, FR-020; SC-005)
- [ ] T043 [US3] Change `scripts/evidence_v3.py` for this feature until T042 passes: the trail
  record's characteristic from the output of T039's companion and the candidate's committed
  operation list, its class by FR-020, the order of sizes per kind, the caps and rows from
  `$REP/projection-table.json`, and the thread count; no tool file whose exact hash a validation
  record matches (`tool_sha256`, and a C tool's binary) changes here, and a change that would reach
  one goes through T039 before the tool's first counted use. (FR-006, FR-007, FR-014, FR-019,
  FR-020; SC-005; R7)
- [ ] T044 [US4] Write the selection-bias statement's tests in `tests/test_protocol_005.py`
  (data-model §6; quickstart V9): from the candidate logs of both features, one row per design with
  `feature`, `id`, `family`, `outcome` (`ineligible`, `proposed and declined`, `selected`,
  `not selected`, `withdrawn`, `rejected`), the decision's log entry (feature and `seq`) and
  `derived_from` with its relation; B1 and A1 `ineligible` (entries 47 and 107), B2 and A2 proposed
  and declined (entries 49 and 109); feature 004's D4 record and selection record by path and
  SHA-256; the bias rule's family-wise rate over this feature's tests, feature 004 having run none
  at w = 32; and no line that the claim test flags. (FR-024; SC-006; R11)
- [ ] T045 [US4] Write `research/005/selection_bias.py [--check FILE]` (contracts/cli.md) until T044
  passes: it generates the statement as a Markdown table from `research/004/candidates.jsonl` and
  `research/005/candidates.jsonl`, reading both and writing neither, and `--check FILE` compares the
  table FILE holds with its output, exit 1 on a difference. (FR-024; SC-006; R11)
- [ ] T046 [US3] Write each candidate as an operation list of invertible updates with its reference
  outputs under `research/005/candidates/`, `v4-A<k>.py` (ARX) or `v4-B<k>.py` (Boolean), meeting
  every inherited design rule FR-001 lists, a new design or a feature-004 design entered again under
  D1 (FR-023); generate its constant tables with
  `python scripts/gen_constants_v3.py --candidate ID --variant VARIANT` into
  `research/005/candidates/<id>/constants/<variant>.json`, the constant rule read as research R15
  fixed it at 99e6994 with `research/005/refused-constants.json`; and, after T026 and T036, append
  its `proposed` entry with `python scripts/candidate_log.py propose FILE`, with
  `--derived-from PATH:SHA256 --relation derived|starting-point [--changes TEXT]` for a design that
  names a feature-004 design, before any tool runs on it, an unchanged re-entered design's entry
  stating that its permutation and constants equal feature 004's. At least one candidate per family
  enters before the D4 choice, at most three evaluated per family in all. (FR-001, FR-002, FR-011,
  FR-022, FR-023; SC-002; R13)
- [ ] T047 [US3] Append each candidate's `mapping` entry with
  `python scripts/candidate_log.py mapping FILE` before its first score, and record the entered set
  with `python scripts/candidate_log.py enter`, one `entered-d4` entry per candidate, before the
  first score. (FR-022, FR-023)
- [ ] T048 [US4] **heavy**: for each entered candidate, at 4×4 and at the widest reduced width that
  inherited research R6's rule fixes, compute the D4 score's inputs with
  `python scripts/evidence_v3.py`: the cross-checks between kinds, the rotation search (an unchanged
  re-entered design keeping feature 004's amounts at width 16, searched again at 8 where R6's rule
  fixes that width, FR-023), the trail bounds over r* rounds with the validated trail tools, and the
  cost from `research/004/tools/costmodel.py`, every reduced-width score before the first
  production-width search; each run projected first. In the commit that holds this feature's first
  counted trail-bound record, set `phyco-v4`'s `in_progress` in `protocol/claims.json` to L2, not
  reached, from that record's date, as the register's rule has it (T016);
  `python -X utf8 scripts/check_claims.py` reports 0 findings. (FR-022, FR-023, FR-026; SC-007,
  SC-010)
- [ ] T049 [US4] Run
  `python scripts/d4_choice.py --log research/005/candidates.jsonl --out $REP/d4/choice.json` once;
  after an exact tie, the two representatives go on at the production width in FR-014's order, 16×16
  first, and only as far as R at 4×4 needs, and `--tie` writes `$REP/d4/tie.json` once both have R
  at 4×4 or one is `ineligible`, a decision at 16×16 included (FR-022; contracts/cli.md); D4's cost
  model scores this feature's candidates unchanged, its direction kept. (FR-014, FR-018, FR-022;
  SC-010)
- [ ] T050 [US4] ⛔ **D4 tie** (**Owner**), only where the tie-breaks reach the owner's choice: run
  `python scripts/d4_choice.py --choose ID --seen SHA256 --by NAME --out $REP/d4/tie-choice.json`,
  then set and commit the row "D4 tie" in the spec; where a tie-break decides it, the row reads Not
  needed, naming `d4/tie.json` and its tie-break. (FR-022; SC-010; Principle VIII)
- [ ] T051 [US3] **heavy**: for the chosen family's candidates in turn, run the production-width
  trail-bound climbs with `python scripts/round_rule.py --candidate ID`, which drives
  `scripts/evidence_v3.py` (quickstart V5 to V7): a size-independent search first; then at 16×16, r
  from 1, the linear search then the differential at each r, each within the 16×16 cap and the
  candidate's trail row, the `split` records written after each r, until both kinds' weights exceed
  128 or r reaches 64; a candidate without R_bound at 16×16 decided `ineligible` at once with the
  cause `no R_bound at 16×16` and no hour at 8×8 or 4×4, a replacement then entered by T046 under
  the inherited stop rule, within its family's limit and while its family's row holds the recorded
  need of each run the rules require at every size; then 8×8 and 4×4 the same way under their caps;
  every trail recorded at every nonlinear operation. (FR-014, FR-015, FR-016, FR-017, FR-018,
  FR-019, FR-022; SC-003, SC-004, SC-008)
- [ ] T052 [US4] **heavy**: before any candidate's first frequency or avalanche run at a size, run
  the uniform controls there with
  `python scripts/evidence_v3.py --kind control --test frequency --size N --out-dir $REP/controls`,
  first with `--project` and then the run, and the same with `--test avalanche`; a control that
  fires makes that size's bias evidence inconclusive for every candidate, and the feature recommends
  stopping. (FR-022; SC-008)
- [ ] T053 [US4] **heavy**: for each candidate with R_bound at every claimable size, run with
  `python scripts/evidence_v3.py --candidate ID --kind KIND --size N --out-dir $REP/candidates/<ID>`
  the structural checks, the inverse on the 16 vector inputs and 2¹⁰ test states at every supported
  size and variant, the 2×2 variant's exhaustive bijectivity at w = 4, the dependency matrices with
  R_f, R_b and the propagation through instantiate, the symmetry and invariant checks, and the
  `degree` records last; then the frequency test on both input sets, N = 2²⁰ through Π and Π⁻¹, and
  the avalanche test on the flip set, the related-key and related-nonce set and the rotational
  pairs, N_a = 8,256, as inherited; each kind at 4×4, then 8×8, then 16×16, within its row,
  projected first, at the thread or worker count its record states (FR-007). (FR-007, FR-014,
  FR-022; SC-008)
- [ ] T054 [US4] Run `python scripts/round_rule.py --candidate ID` per candidate once its evidence
  stands at every claimable size, R by the round rule with every input cited, a table for a larger R
  generated and checked as inherited FR-023 asks of every rise; after a rise of R, repeat the
  inverse tests, the invariant checks and the new constant table's checks at the new variant before
  the bias tests are extended; write each candidate's `cost` record at every size where it has R, at
  that R, with feature 004's FR-026 figures beside the goal of 10⁸ words per second and the
  constants' ROM size per food node, a candidate decided `ineligible` at 16×16 having no R and no
  `cost` record, its decision entry saying so; then `--close`, `--select` (exit 1 for a stop) and
  `--decide`, the selection reading R as established, whatever its route. (FR-017, FR-022; SC-003,
  SC-010)
- [ ] T055 [US4] ⛔ **Selection tie** (**Owner**), only where eligible candidates tie: run
  `python scripts/round_rule.py --choose ID --seen SHA256 --by NAME`, which writes
  `$REP/freeze/selection-tie-choice.json`, then set and commit the row "Selection tie" in the spec,
  or "Selection tie <k>" for a later selection record; otherwise the row reads Not needed. (FR-022;
  SC-010; Principle VIII)
- [ ] T056 [US4] Generate the selection-bias statement with `research/005/selection_bias.py` over
  both features' candidate logs as they stand after T054, for the final report and, where a
  candidate is selected, for `rationale.md`; and run `python scripts/recheck_004.py --no-record`
  under `005`, 0 disagreements over every `split` bound and trail of this feature. (FR-020, FR-024;
  SC-005, SC-006)

**Checkpoint**: a selection record with its decision entries in `research/005/candidates.jsonl`, or
a stop with what was reached, which skips to Phase 9, the tasks of Phases 6 to 8 marked not
applicable with that reason (User Story 4, scenario 2). The phase ends with the constitution's
phase report to the owner.

---

## Phase 6: User Story 5 - The model, its constants and its vectors (plan phase 6)

**Goal**: the design document complete; `phycoweb/constants_v4.py`, `phycoweb/model_v4.py`, the
vectors and known-answer tests, the constructed-state vectors and the self-test's copy of the
vectors, each reproduced on Windows and in WSL, as feature 004's requirements ask, for `phyco-v4`
(FR-025).

**Independent Test**: each generator's `--check` exits 0 on both platforms with its
`generator-check` record; every reduced variant and every request beyond a limit is refused
(SC-010).

- [ ] T057 [US5] Complete `specs/005-crypto-architecture-v4/design.md` for the selected candidate,
  as a new version, its chapters after "Security target" and "Mode" in inherited FR-034's order:
  "Permutation", with its sections "Variant table" (every variant's R), "Round counts" (each
  R_bound's route per size and kind, the searched records up to the first cap, then the `split`
  records with their parts, each bound marked searched or `split` and cited by ID and SHA-256),
  "Inverse" and "Network questions"; "Hardware structure", with its section "Self-test" and its
  table of k; "Replaced mechanisms"; and "Slime-mould mapping", holding the fixed negative statement
  and no other wording of that kind; every operation's width, signedness, wrap rule, shift kind and
  comparison semantics, the update order, every data-flow direction, the edge states, the colour
  schedule, the reduced variants and the production parameter sets, the constant rule's values and
  every inherited hardware rule with its figure; each section entered in `$REP/provenance.jsonl` as
  it is drafted; the chapters test (T030) extended to require every section named here, "Round
  counts" among them (FR-025). (FR-010, FR-025, FR-026; SC-010)
- [ ] T058 [P] [US5] Write `tests/test_model_v4.py` from feature 004's model contract read for
  `model_v4` ("Tests that hold the model to this contract"): inherited FR-058's list, minimum,
  maximum and boundary values, all-zero and all-one keys and nonces, single-bit keys, overflow and
  truncation, shift and rotation boundaries, reset, zeroization and repeated instantiation, long
  runs with the 2²⁰-word digest and invalid parameters; every reduced variant refused by `Generator`
  with `VariantRefused`; every request beyond each limit refused; every call-sequence error;
  `ResearchDuplex`'s key and nonce lengths; every failure path; the model importing no analysis
  dependency; `phyco-v4` reproducing the selected candidate's outputs through the `selected` entry's
  variant map; property tests with Hypothesis. (FR-025; SC-010)
- [ ] T059 [US5] Run `python scripts/gen_constants_v3.py`, which writes `phycoweb/constants_v4.py`
  with its GENERATED header for every supported (n, w) at its final R; then `--check` on Windows and
  with `wpy` in WSL, each writing a `generator-check` record with verdict `match` under
  `$REP/generator-checks/`. (FR-023, FR-025; SC-010)
- [ ] T060 [US5] Write `phycoweb/model_v4.py` from the design document: standard library only, its
  source parsing under Python 3.8's grammar, integer-only and branch-free on data,
  `MODEL_ID = "phyco-v4"` with `PRODUCTION_VARIANTS`, `parse_variant` and `is_production`; `pi`,
  `pi_inv` and `pi_trace`, research-only; `Generator(variant_id, key)` with
  `instantiate(nonce, pers=b"")`, `generate(nbits)`, `reseed(data)` and `zeroize()`, the start-up
  self-test imported only in its constructor, every limit with its counter and every refusal of the
  contract; `ResearchDuplex` for the keyed reduced variants; marked model-only, RTL-pending.
  (FR-025; SC-010)
- [ ] T061 [P] [US5] Write `tests/test_vectors_v4.py`: Π and Π⁻¹ known-answer tests at every
  supported size and every reduced variant used as evidence, 16 inputs with 4 traced phase by phase;
  the mode at every claimable size with 2 development keys × 10,000 words in requests that cycle
  through the stated lengths; the SHA-256 digest of 2²⁰ words; the sidecar
  `vectors/phyco-v4/MANIFEST.json`; `phycoweb/selftest_v4.py` equal to the vectors it copies; each
  `selftest_<variant>.json` from the self-test's call sequence alone; and each file's k against the
  least k of the model's run and the design document's table of k. (FR-025; SC-010)
- [ ] T062 [US5] Write `scripts/gen_vectors_v3.py [--check] [--variant ID ...]` with
  `--reproduce RECORD`, feature 004's contract read for this feature, and run it into
  `vectors/phyco-v4/`, writing in the same run each claimable size's and each keyed research
  variant's `selftest_<variant>.json` and `phycoweb/selftest_v4.py` (GENERATED), each vector file in
  at most an hour and the model's speed recorded; then `--check` on Windows and with `wpy` in WSL,
  each writing a `generator-check` record. (FR-025; SC-010)
- [ ] T063 [US5] Write `scripts/gen_constructed_v3.py [--check]` with `--reproduce RECORD`: a
  constructed-state vector for every edge state the design document lists, all-zero and all-one
  lanes, every addition driven to a carry out of its top bit and every shift and rotation at its
  boundary among them, into `vectors/phyco-v4/`; run it, then `--check` on Windows and with `wpy` in
  WSL, the pair of `generator-check` records also showing that `Generator`'s self-test passed on
  each platform. (FR-025; SC-010)
- [ ] T064 [US5] Run `python -W ignore -m unittest tests.test_model_v4 tests.test_vectors_v4` on
  Windows and with `wpy` in WSL, and record the commands and results; no expected value is ever
  edited to make a test pass, a disagreement going back to the design document or the model as a
  finding. (FR-025; SC-010)

**Checkpoint**: the model, constants, vectors and constructed states reproduced on both platforms.
The phase ends with the constitution's phase report to the owner.

---

## Phase 7: User Story 5 - The second transcription (plan phase 7)

**Goal**: a second transcription of Π, Π⁻¹ and the mode, written from the design document alone in a
separate session, agreeing with the model at every step of every committed vector (FR-025).

**Independent Test**: the transcription test agrees at 100% of the steps, with the common-mode
caveat beside it (SC-010).

- [ ] T065 [US5] ⛔ **Second transcription go-ahead** (**Owner**): the row "Second transcription
  go-ahead" in the spec set to Approved and committed before the separate session starts; the agent
  lists the approval commits and the allow-list entries added since the last gate. (FR-025; SC-010;
  Principle VIII)
- [ ] T066 [P] [US5] Write `tests/test_v4_transcription.py`: `phycoweb/model_v4.py` and
  `tests/v4_reference.py` agree after every phase of every round on the committed vectors, for Π,
  Π⁻¹ and the mode, with the common-mode caveat of security.md §10.2 beside the result; and the
  provenance test: the go-ahead row reads Approved at HEAD with a date no later than the first
  provenance entry of `tests/v4_reference.py`, and the two files come from different sessions.
  (FR-025; SC-010)
- [ ] T067 [US5] In a separate session that has not read `phycoweb/model_v4.py` and imports no code
  from it, write `tests/v4_reference.py` from the design document alone, with its entries in
  `$REP/provenance.jsonl` naming that session. (FR-025; SC-010)
- [ ] T068 [US5] Run `python -W ignore -m unittest tests.test_v4_transcription` on both platforms; a
  disagreement is reported against the design document, corrected as a new version of it and
  compared again, never by editing either side to agree. (FR-025; SC-010)

**Checkpoint**: agreement at 100% of the steps of the committed vectors, with the caveat stated. The
phase ends with the constitution's phase report to the owner.

---

## Phase 8: User Stories 2 and 5 - Reviews and Freeze (plan phase 8)

**Goal**: the later security-target review with every R known, then the rest of the rationale, the
review package, the owner design review, the external review recorded, and the design freeze
(FR-012, FR-013, FR-025).

**Independent Test**: the rationale checked against every item of security.md §8 and the review
package against §14; the candidate log compared with the model's variant IDs; the freeze hashes
recomputed; the claim test's register checks pass (SC-007, SC-010).

- [ ] T069 [US2] With every R known, write the chapters "Security target" and "Mode" of both
  documents and the security target's files again (FR-012): run
  `python scripts/mode_limits_v3.py --out $REP/security-target/limits.json` with the variant table's
  R, and in the same commit write `phyco-v4`'s `bound` and `evidence` in `protocol/claims.json`
  again (FR-011); in that commit, which writes R into the reviewed chapters, return `phyco-v4`'s
  level to L0, dropping the `evidence` entries the level rested on, with security.md §1.1 and §15
  and a version of the level family with its history entry, CRLF kept (FR-013); cite the selected
  candidate's records for the open items, the margin of instantiation's diffusion over R_f from the
  same dependency measurement as FUT-GRID-3's warm-up and the first-order related-key and
  related-nonce differences, and confirm or change the functionality class with the selected
  design's records; mark each theorem `verified` once its paper is read, as inherited; compute the
  set the later review names, as T035 computed it; `python -X utf8 scripts/check_claims.py` reports
  0 findings. (FR-011, FR-012, FR-013, FR-027; SC-007)
- [ ] T070 [US2] ⛔ **Security-target review <k>** (**Owner**), k the family's next number, after the
  selection and before the owner design review: the round counts, the figures computed from them and
  the open items as the chapters then state them, the row naming T069's set by SHA-256 with the
  version read; a decline ends as T036 states. (FR-012; SC-007, SC-010; Principle VIII)
- [ ] T071 [US2] ⛔ **L1 recorded <k>** (**Owner**), once T070's row reads Approved: the row names
  it and feature 004's row "FUT-SEC-8 result review", each with what it reviewed by path and
  SHA-256; in the same commit the agent sets `phyco-v4`'s level, `history` and `evidence` in
  `protocol/claims.json` as T037 does, with security.md §1.1 and §15 and a version of the level
  family; `python -X utf8 scripts/check_claims.py` reports 0 findings. (FR-013, FR-027, FR-030;
  SC-007)
- [ ] T072 [US5] Write the rest of `specs/005-crypto-architecture-v4/rationale.md`, its chapters in
  inherited FR-034's order, "Components", "Nonlinearity", "Diffusion", "Constants", "Margin" and
  "Attack classes", then "Network questions" and "Alternatives", each statement with one of
  inherited FR-062's seven labels: in "Margin", each R_bound's route per size and kind, a searched
  bound and a `split` bound each labelled "fact" and citing its record by ID and SHA-256, with
  FR-016's condition on a sum stated beside each `split` bound as an "argument" (FR-025), and a
  proof that carries a bound to a larger size, where one is written, standing as a check beside the
  computed bounds (FR-021); the selection-bias statement of T056 (FR-024); for an unchanged
  re-entered design, the statement that its permutation and constants equal feature 004's (FR-023);
  and every candidate considered with the reason it was kept or dropped; the chapters test (T030)
  extended to require the routes in "Margin", each `split` bound with its "argument" (FR-025).
  (FR-021, FR-023, FR-024, FR-025, FR-026; SC-006)
- [ ] T073 [US5] Write the version of security.md that inherited FR-051 asks for, CRLF kept, with
  its history entry: `phyco-v4`'s own section, a table of structural facts, the best-attack register
  rows of its first bounds, each R_bound's route among them, and the lessons table, each with its
  evidence; and what the analysis feature 006 needs. (FR-025, FR-027; SC-007)
- [ ] T074 [P] [US5] Write the freeze tests for this feature in `tests/test_protocol_005.py`:
  `scripts/design_freeze.py create` exits 2 before the owner design review, on every condition of
  feature 004's contract for it, a change to `rationale.md` or to the reviewed set after its review
  among them, unless HEAD is the owner's commit of step (1), and while `scripts/check_claims.py`
  reports a finding; `approve` writes nothing without the owner's approval of the first 16 hex
  digits of `draft_sha256`; `validate` exits 2 while `freeze_status` is `draft` and 1 if anything
  but the approval fields changed. (FR-025; SC-010)
- [ ] T075 [US5] Write `protocol/design_freeze.py`, with create, approve and validate as functions,
  and `scripts/design_freeze.py`, the command that calls it, taking the feature: the record holds
  the design document's version 1.0 with `reviewed_version`, `rationale.md`, the selected operation
  list, `research/004/ir.py` with its tools, the verdict scripts, both freeze files, every module a
  frozen script imports, every evidence record behind R by ID and SHA-256, the `split` records and
  their parts among them, and the last `seq` and line SHA-256 of this feature's three logs. (FR-025;
  SC-010)
- [ ] T076 [US5] Write `protocol/review_package.py` and `scripts/review_package.py [--check]` with
  `--reproduce RECORD`, and assemble `$REP/review-package/` with its `MANIFEST.json`: the spec, the
  design document and the rationale with exact revisions, the model source and vectors, the evidence
  records, the threat model, the security target marked as targets, each R_bound's route per size
  and kind with each bound marked searched or `split` (FR-025), and the known limitations and open
  questions, every item of security.md §14 by the files of its group; `--check` fails an item with
  no file. (FR-025; SC-010)
- [ ] T077 [US5] ⛔ **Owner design review** (**Owner**), in the spec's Review & Approval table,
  after T070's row reads Approved: the design document, the rationale, the candidate log and the
  evidence, with the candidate-dependent open items checked against the selected candidate's records
  (FR-012), an open item that fails failing the candidate's eligibility item; "no security statement
  rests on the mapping" recorded among its items; the row naming `rationale.md` by path and SHA-256
  beside the design document's version and the selection record. Before it, every file of this
  feature that the freeze hashes is committed; the agent lists the approval commits and the
  allow-list entries added since the last gate. From the commit that records the approval, the agent
  commits no file of this feature but on the owner's written word (inherited FR-043; spec notes);
  the next commit writes security.md's version recording the gate in row 5a.1b's status. (FR-012,
  FR-025, FR-027; SC-010)
- [ ] T078 [US5] Right after the commit that records the owner design review's approval, write its
  review entries in `$REP/provenance.jsonl` with `python scripts/provenance.py review FILE`, one per
  AI-drafted section, `rationale.md`'s chapters "Security target" and "Mode" among them, and the
  `review-outcome` entry with `python scripts/candidate_log.py outcome FILE`, for the owner's commit
  of step (1). (FR-025, FR-031; SC-010)
- [ ] T079 [US5] ⛔ **External design review** (**Owner**), arranged by the owner where possible,
  from `$REP/review-package/`: its row reads done, naming the package's manifest by SHA-256, or "not
  arranged", naming the latest selection record by path and SHA-256; no AI session is recorded as an
  independent or external reviewer. (FR-025; SC-010)
- [ ] T080 [US5] Run the five freeze steps of feature 004's contract: (1) **Owner**: commit the
  feature files, the owner's next commit after the one that records the owner design review's
  approval, with the review entries and step (1)'s rows; (2) the agent runs
  `python scripts/design_freeze.py create` on a clean tree with that commit as HEAD, writing
  `$REP/freeze/freeze.json` with `freeze_status` `draft` and `owner_commit`; (3) **Owner**:
  `python scripts/design_freeze.py approve --by NAME --wording TEXT`; (4) **Owner**: commit the
  record; (5) the agent runs `python scripts/design_freeze.py validate`, exit 0. (FR-025; SC-010)
- [ ] T081 [US5] ⛔ **Design freeze** (**Owner**): the row "Design freeze" in the spec names the
  approved freeze record by path and SHA-256 and its `owner_commit`; the next commit writes
  security.md's version recording the gate in row 5a.1b's status. (FR-025, FR-027; SC-010;
  Principle VIII)

**Checkpoint**: `phyco-v4` frozen with its hashes; the later features analyse one fixed object. The
phase ends with the constitution's phase report to the owner.

---

## Phase 9: Polish and Final Report (plan phase 9)

**Purpose**: the closing checks and the final report, inside inherited FR-043's window where a
freeze was reached, so that the agent writes each file and the owner commits it, or the agent
commits on the owner's written word (spec notes).

- [ ] T082 Update `README.md`, CRLF kept, with its line on `phyco-v4` at the end of the feature: its
  status, frozen or stopped, and that it makes no claim (FR-027; inherited FR-051). (FR-027; SC-007)
- [ ] T083 Run `python -X utf8 scripts/check_claims.py` and
  `python -W ignore -m unittest tests.test_claims` over the final documents: 0 findings, every
  hand-written document of this feature carrying the disclaimer naming `phyco-v4`, and security.md
  §1.1, §15 and the register agreeing on `phyco-v4`'s level, the one its rows give. (FR-026, FR-027;
  SC-007)
- [ ] T084 In a fresh clone, run `python scripts/recheck_004.py` under `005`: 0 disagreements, 100%
  of the `split` bounds and of the trail weights, transitions and classes recomputed, its `recheck`
  record under `$REP/rechecks/` naming the interpreter, the platform and its `pip freeze`; run
  `python scripts/projection_table.py --check` there, the probes re-checked and never re-run
  (FR-001); and, with the setting unset, `python scripts/recheck_004.py --no-record`, giving T132's
  result and writing nothing (FR-003). (FR-001, FR-003, FR-020; SC-005)
- [ ] T085 **heavy**: run the whole suite with `PHYCOWEB_FEATURE=005` on Windows,
  `python -W ignore -m unittest discover -s tests -t .`, and with `wpy` in WSL, under the heavy-run
  lock and projected first against the feature-wide row's share for whole-suite runs, charging no
  candidate: every test passes, or skips naming its open item, and none fails; the commands and
  results go to the final report. (FR-003, FR-008; SC-008; Principle V)
- [ ] T086 Write the final report `$REP/phase-report.md` with the disclaimer naming `phyco-v4`, as
  inherited FR-052 and the constitution's Phase Completion Reporting ask: every FR and SC of this
  feature with its evidence or listed as open; FUT-SEC-1 to FUT-SEC-9 with their statuses, FUT-SEC-7
  open for feature 008, and the FUT-GRID and FUT-HW rows (FR-030); the projection table beside the
  measured hours of every heavy run, with each run's ratio of measured to projected hours
  (quickstart V10), the misses reported with both figures, and the sum within the ceiling; each
  R_bound's route, the sums it rests on, one resting on r·W(1) alone named as such (FR-029); the
  selection-bias statement (FR-024), with the statement that every result of a frozen candidate is
  on development inputs chosen among up to eight evaluated candidates, feature 004's two and up to
  six of this feature's, beside the two declined proposals, so that feature 008's held-out
  evaluation is the unbiased test; and the recommendation to proceed, revise or stop, a stop ending
  inherited FR-043's window at the same commit. (FR-024, FR-029, FR-030; SC-006, SC-008, SC-009,
  SC-010)
- [ ] T087 ⛔ **Final result review** (**Owner**), in the spec's Review & Approval table: the
  owner's commit that records the decision, with the spec's Status line, ends inherited FR-043's
  window; the next commit writes security.md's version recording the gate in row 5a.1b's status.
  (FR-027, FR-029; SC-010; Principle VIII)

---

## Dependencies & Execution Order

- **Phase 0 → Phase 1**: T004 comes before every task of phases 1 to 9; T001 → T002 → T003 before
  it; T005 right after it.
- **Phase 1**, in step order: (1) T006 → T007 → T008 → T009; (2) T010, before every later write
  through `protocol/evidence.py` or a log writer; (3) T011 ∥ T012, then T013 → T014 → T015; (4)
  T016 → T017 → T018; (5) T019 → T020; (6) T021, after T015.
- **Phase 2 (US1)** needs Phase 1, T015 and T018 above all (no probe before the protocol change log
  and the claim test's first scan): T022 → T023 ∥ T024 → T025 → T026 → T027.
- **Phase 3 (US2)** needs Phase 1 (T017 before T037) and may run before, beside or after Phase 2,
  having one heavy run at most; T028 → T029, T030 → T031 → T032 → T033 → T034 → T035 → T036 →
  T037.
- **Phase 4** needs Phase 1; T038 → T039.
- **Phase 5** needs Phases 2, 3 and 4: no `proposed` entry before T026 and T036 (FR-011); T040 →
  T041, T042 → T043 and T044 → T045 before T046; T046 → T047 → T048 → T049 (→ T050) → T051, the
  production-width climbs; T052 before each size's first bias test; T053 after T051 for each
  candidate with R_bound at every claimable size; T054 → (T055) → T056.
- **Phase 6** needs a selection from T054; **Phase 7** needs Phase 6; **Phase 8** needs Phases 5 to
  7, with T069 → T070 → T071, T070 before T077, and every freeze step in order (T077 → T078 → T080
  → T081); **Phase 9** needs T081, or a stop from Phase 5, and T086 comes before T087.

### Parallel opportunities

- Phase 1: T011 ∥ T012; the test tasks share `tests/test_protocol_005.py` and run in turn.
- Phase 2: T023 ∥ T024 as code; the probes still run one at a time.
- Phase 3: its drafting (T032, T033) beside Phase 2's probes, which hold the heavy-run lock; its
  test tasks (T028, T030) share `tests/test_protocol_005.py` and run in turn.
- Phase 5: its test tasks (T040, T042, T044) share `tests/test_protocol_005.py` and run in turn; the
  candidates' modules may be drafted side by side, their `proposed` entries appended in turn under
  the log's lock.
- Phase 6: T058 ∥ T061; Phase 7: T066 beside T067, which runs in its own session.
- Phase 8: T074 beside T072 and T073.

## Implementation Strategy

1. **MVP = US1** (Phases 0 to 2, T001–T027): the machinery and logs for feature 005, and every run
   the rules require of one candidate planned and probed at every claimable size before any
   candidate exists.
2. **Security target first** (Phase 3): the target reviewed before any candidate, L1 recorded.
3. **Tools** (Phase 4): every counted tool's validation in force for its exact hash, and the ARX
search's companion of research R7 validated.
4. **Candidates and evidence** (Phase 5): the climbs at 16×16 first, continued by sums; R by the
   round rule; a selection or a stop, a stop being a valid outcome, reported with what was reached.
5. **Model, vectors and transcription** (Phases 6 and 7).
6. **Reviews, freeze and final report** (Phases 8 and 9).

## Requirement Coverage

Every functional requirement and success criterion, with the tasks that cite it (Principle VII):

- FR-001: T006, T007, T013, T015, T016, T031, T046, T084
- FR-002: T006, T007, T046
- FR-003: T006–T010, T021, T039, T084, T085
- FR-004: T012
- FR-005: T015, T022–T026
- FR-006: T042, T043
- FR-007: T010, T023, T025, T042, T043, T053
- FR-008: T021, T085
- FR-009: T022, T024–T027
- FR-010: T030–T033, T036, T057
- FR-011: T028–T031, T034–T036, T046, T069
- FR-012: T032, T035, T069, T070, T077
- FR-013: T016, T037, T069, T071
- FR-014: T040–T043, T049, T051, T053
- FR-015: T040–T042, T051
- FR-016: T019, T020, T038–T041, T051
- FR-017: T040, T041, T051, T054
- FR-018: T040, T041, T049, T051
- FR-019: T019, T020, T039, T042, T043, T051
- FR-020: T019, T020, T042, T043, T056, T084
- FR-021: T072
- FR-022: T028, T029, T038, T040, T046–T055
- FR-023: T011, T028, T029, T046–T048, T059, T072
- FR-024: T022, T024, T044, T045, T056, T072, T086
- FR-025: T057–T068, T072–T081
- FR-026: T003, T006, T007, T016–T018, T030, T032, T033, T048, T057, T072, T083
- FR-027: T005, T036, T037, T069, T071, T073, T077, T081–T083, T087
- FR-028: T006, T007
- FR-029: T086, T087
- FR-030: T006, T016, T017, T037, T071, T086
- FR-031: T001–T004, T013–T015, T027, T036, T078
- SC-001: T012, T022–T027
- SC-002: T028, T029, T032, T033, T035, T036, T046
- SC-003: T040, T041, T051, T054
- SC-004: T040, T041, T051
- SC-005: T008, T009, T019, T020, T039, T042, T043, T056, T084
- SC-006: T044, T045, T056, T072, T086
- SC-007: T005–T007, T016–T018, T030–T034, T037, T048, T069–T071, T073, T082, T083
- SC-008: T021, T025, T051–T053, T085, T086
- SC-009: T086
- SC-010: T048–T050, T054, T055, T057–T068, T070, T074–T081, T086, T087

## Security Policy traceability

FUT-SEC-1 to FUT-SEC-9 for `phyco-v4`, with the tasks that carry each (FR-030), the statuses as
feature 004's table "Security Policy traceability" gives them for `phyco-v3`, read with FR-001's
numbering of the later features:

- FUT-SEC-1 Key entropy: T032, T034, T036, T069, T070
- FUT-SEC-2 Reachable secret state: T032, T034, T069
- FUT-SEC-3 Stream separation: T032 (the nonce rule, domain separation), T060
- FUT-SEC-4 Reseeding: T032 (the chapter "Mode" as Version 0.4 states it)
- FUT-SEC-5 Initialization analysis: T032 (key loading), T053 (the propagation through instantiate,
  the related-key and related-nonce set), T069 (the open items cited)
- FUT-SEC-6 Output limit: T031, T034, T058, T060
- FUT-SEC-7 Re-validation: T057–T064, T080, T081; the statistical programme open for feature 008
- FUT-SEC-8 Demonstration first: met by feature 004's demonstration and its review (ffb1425), not
  repeated; T006 (the guard reads them), T037 and T071 (the register's `evidence`)
- FUT-SEC-9 Certification route: T032 (the functionality class an open item), T069 (confirmed or
  changed with the selected design's records)
- FUT-GRID-1 to FUT-GRID-5 and FUT-HW-1 to FUT-HW-5: as feature 004's table traces them, through
  T053 (R_f, R_b), T057 (the design document's chapters), T059 to T063 (constants, model and vectors
  per size) and T076 (the review package); FUT-GRID-5's statistics per size open for feature 008,
  FUT-HW-3 and FUT-HW-4 open for the hardware features 007 and 009

## Notes

- Never edit an expected value to make a test pass; a disagreement is a finding, analysed as the
  protocol says.
- No download is planned. A file the owner permits goes into its own new directory, nothing runs
  from inside it, and Python reads it with `-I`.
- `README.md`, `security.md` and `requirements.txt` keep CRLF and are edited only by scripts that
  keep it; this feature's Markdown files, this one included, the files under `research/005/` and
  `$REP`, and `protocol/*.json` are LF.
- No document of this feature uses the wording the claim test forbids; `scripts/check_claims.py`
  and its allow-list decide, and every new entry is listed for the owner at the next ⛔ gate
  (FR-026).
- Every phase ends with the constitution's phase report: files created or modified, requirements
  addressed, tests run with their exact commands, open issues, concerns and a recommendation to
  proceed, revise or stop.
- The protocol only becomes stricter (inherited FR-044; FR-009): a change after the tasks approval
  and before any result is made in a row "Protocol change <k>" that the owner approves in writing
  before it takes effect, entered with `python scripts/protocol_change.py propose FILE`; a
  claim-test finding answered by an allow-list entry alone needs no row (spec notes; FR-031).
- Test runs at a phase's checkpoint are light: the phase's own test modules by their test classes,
  FR-053's two-worker test left out; a run that includes that test is a heavy run, and T021 and
  T085 are those runs.
- A reproduction uses its original's thread count (FR-007); the probes and the projection table are
  re-checked, never re-run (FR-001); a run whose measured hours miss its projection is reported with
  both figures, no decision already made changes, and the calibration is not refitted (spec, Edge
  Cases).
