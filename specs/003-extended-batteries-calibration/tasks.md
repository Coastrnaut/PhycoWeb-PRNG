---

description: "Task list for feature 003, extended batteries and positive-control calibration"
---

# Tasks: Extended Batteries and Positive-Control Calibration

**Input**: Design documents from `/specs/003-extended-batteries-calibration/`

**Prerequisites**: plan.md, spec.md (approved 2026-10-29), research.md (R1–R11), data-model.md,
contracts/cli.md, quickstart.md

**Tests**: included. The constitution requires reproducible automated tests (Principle II) and
guard tests protect the pre-registered protocol (Principle IV). Within each story, tests are
written before the code they test.

**Organization**: grouped by user story. Phases follow priority order except that US3 (fast
streams, P3) comes before US2 (P2): every US2 battery run consumes the US3 stream, so US2 cannot
be tested without it. US1 needs neither and runs first. The spec priorities are unchanged.

⛔ marks a human review gate (Principle VIII): the agent stops and waits for the owner. The
agent never commits, pushes or publishes (Principle IX). `REP` =
`reports/003-extended-batteries-calibration`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1, US2, US3

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: directories and the generated table shared by the C tooling.

- [X] T001 Create `fast/`, `tests/data/batteries/` and `$REP/{calibration/runs,streams,tools,dev}/`;
  confirm the existing `build/` rule in `.gitignore` covers `fast/build/` (`git check-ignore`).
  (plan Project Structure)
- [X] T002 Write `scripts/gen_c_lut.py` (contracts/cli.md) and generate `fast/lut_table.h` from
  `phycoweb/lut.py` with a GENERATED header; `--check` exits 1 on drift. (FR-007, FR-008; R4)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: none new. All stories reuse `scripts/evalcore.py` (`versions`, `write_record`,
`_git`), `protocol/disclaimer.py` and `sp80022` 1.0.0 read-only. No feature-002 file is edited.

- [X] T003 Record the baseline: run `python -W ignore -m unittest discover -s tests -t .` on
  Windows and in WSL, and the SHA-256 of `phycoweb/model_v2.py`, `phycoweb/model.py`,
  `phycoweb/lut.py` and `sp80022` (`source_sha256`), in `$REP/dev/test-log.md`. (FR-005, FR-008;
  Principle V)

**Checkpoint**: baseline green; feature-002 hashes recorded for later comparison.

---

## Phase 3: User Story 1 - Calibration of the SP 800-22 positive control (Priority: P1) 🎯 MVP

**Goal**: measured false-failure rate of a perfect generator under the feature-002 protocol.

**Independent Test**: quickstart C1–C3.

### Tests for User Story 1

- [X] T004 [P] [US1] Write `tests/test_calibration.py`: (a) `calibrate.py` exits 2 on a wrong
  `sp80022` hash, on an existing run file without `--resume`, and resumes at the first missing
  index with `--resume`; (b) record shape matches data-model §1, with a mocked evaluator and a
  temporary output directory, and no byte file is written; (c) `calibration_report.py` exits 2
  when any of runs 0…999 is missing; (d) statistics: Clopper–Pearson against known values,
  expected per-family rates against the feature-002 k_max table, consistency flag, co-failure
  counts and implied PASS probability on synthetic runs. (FR-001 to FR-006, SC-001, SC-002)

### Implementation for User Story 1

- [X] T005 [US1] Implement `scripts/calibrate.py` (contracts/cli.md; research R2): `os.urandom`
  per sequence, running SHA-256 of the run's bytes, `sp80022.battery` + `sp80022.assess` via the
  `evalcore` worker pool, one gzip JSON per run (data-model §1: `run` "0…999; file name matches; never overwritten";
  `input_sha256` "SHA-256 of the run's 100 × 262,144 bytes, in sequence order"; `harness_sha256`
  checked), append-only with `--resume`,
  harness-hash check, disclaimer. (FR-001, FR-002, FR-005, FR-006)
- [X] T006 [US1] Implement `scripts/calibration_report.py` (research R3): all-runs check,
  overall / per-family / per-sub-test rates with Clopper–Pearson intervals, expected rates from the
  feature-002 rules using each run's m′, consistency flags, failing-family histogram, 15×15
  co-failure with Fisher p, implied PASS probability; writes `summary.json` and `summary.md`
  (data-model §2) with recommendations marked "recommendation only". (FR-003, FR-004, FR-005)
- [X] T007 [US1] Smoke run: `calibrate.py --runs 0-1` into the scratchpad (not `$REP`); confirm
  about 60 s per run and a valid record; log in `$REP/calibration/test-log.md`. (FR-001)
- [X] T008 [US1] Full calibration: `python -W ignore scripts/calibrate.py --runs 0-999 --workers 32
  --out-dir $REP/calibration/runs` in the background (~17 h); resume with `--resume` after any
  interruption, and log every interruption. (FR-001, FR-002, FR-006, SC-001)
- [X] T009 [US1] Run `calibration_report.py` → `$REP/calibration/summary.json` and `summary.md`;
  run it again and confirm byte-identical output (quickstart C3); write `runs/SHA256SUMS`.
  (FR-003, FR-004, SC-001, SC-002)
- [X] T010 [US1] Write `$REP/calibration/phase-report.md` (constitution Phase Completion
  Reporting): files, FR/SC addressed, commands and results, comparison with the ~19% assumption,
  what it means for feature-002 `heldout-2`/`heldout-3`, recommendations (stricter-only, for a
  separate amendment), open issues, verbatim disclaimer. (FR-003, FR-004, FR-005, FR-016)
- [X] T011 ⛔ [US1] **Owner calibration result review** (spec gate). Also decide whether
  `$REP/calibration/runs/*.json.gz` (~150 MB) are committed or kept local (research R10; if local,
  add a `.gitignore` rule and keep `SHA256SUMS`). Record in spec.md Review & Approval.
  Required before T034. (FR-005; Principle VIII)

**Checkpoint**: US1 complete and reviewed; no download needed.

---

## Phase 4: User Story 3 - Fast, bit-exact generator streams (Priority: P3)

**Goal**: terabyte-scale streams identical to the reference models. Can be built while T008
runs (light CPU use); the 2 × 100 × 10⁶-word check (T016) waits until T008 finishes.

**Independent Test**: quickstart S1–S3.

### Tests for User Story 3

- [X] T012 [P] [US3] Write `tests/test_fast_stream.py`: `gen_c_lut.py --check` passes; the
  `phyco-v2` function in `fast/phyco_stream.c` contains no `*`, `/` or `%` operator (comments
  stripped); in WSL (skip elsewhere): every word of the three committed golden vector files
  matches `phyco_stream --hex`, seed values outside 0…65535 exit 2, `--reverse` reverses bits,
  `os --words 4` gives 4 words. (FR-007, FR-008, SC-003)

### Implementation for User Story 3

- [X] T013 [US3] Implement `fast/phyco_stream.c` (research R4; contracts/cli.md): `phyco-v2`
  exactly per design.md 1.0 including the 256-step warm-up; `lut-v1` exactly per feature 001
  (64-bit product wrapped to int32, `>> 8`, the second wrap, `D == 0 → 1`, 16-bit masks);
  `os` via `getrandom`; little-endian u32 output, `--words`, `--reverse`, `--hex`; clean exit on
  SIGPIPE. (FR-007, FR-008)
- [X] T014 [US3] Write `fast/Makefile` (`gcc -O2 -std=c99 -Wall -Wextra -Werror`, output in
  `fast/build/`) and build in WSL. (FR-007)
- [X] T015 [US3] Implement `scripts/stream_equiv.py` (contracts/cli.md): golden vectors plus the
  first 10⁶ words of all 100 feature-002 `dev` seeds for both generators against the Python
  models, parallel over seeds; refuses held-out sets (exit 2); writes data-model §3 with the
  binary, source and LUT hashes. (FR-007, FR-010, SC-003)
- [X] T016 [US3] After T008: run `stream_equiv.py` → `$REP/streams/equivalence.json` (0
  mismatches required); measure throughput of each generator and of `os` into `$REP/dev/timing.json`.
  (FR-007, SC-003)

**Checkpoint**: streams proven identical on dev data.

---

## Phase 5: User Story 2 - PractRand and TestU01 verdict (Priority: P2)

**Goal**: pre-registered PASS / FAIL / INCONCLUSIVE / INVALID verdict for `phyco-v2`.

**Independent Test**: quickstart B1–B6.

### Tools (each download needs explicit owner permission)

- [X] T017 ⛔ [US2] **Ask permission** to download the PractRand release archive: file name,
  official SourceForge URL and size, confirmed at the time (research R6, R11). Wait for a yes;
  record the decision in the "Tool acquisition" row of `specs/003-extended-batteries-calibration/spec.md`.
  (FR-009)
- [X] T018 ⛔ [US2] **Ask permission** to download `TestU01.zip` 1.2.3 from the official TestU01
  site, with size (research R7, R11). Wait for a yes; record it in the "Tool acquisition" row of
  `specs/003-extended-batteries-calibration/spec.md`. (FR-009)
- [X] T019 [US2] Download each approved archive into its own new empty WSL directory, hash it,
  read its licence, and build outside the repository per `fast/build_tools.sh` (`~/practrand/`,
  `~/testu01/`; record any gcc-15 flags); write `$REP/tools/practrand.json` and
  `$REP/tools/testu01.json` (data-model §5). Record the approvals in spec.md. (FR-009; R6, R7, R11)
- [X] T020 [US2] Implement `fast/testu01_driver.c` and its Makefile target (contracts/cli.md;
  research R7): stdin words, `unif01_CreateExternGenBits`, `swrite_Basic = TRUE`, JSONL of
  `bbattery_NTests` / names / `bbattery_pVal`; exit 3 on early end of input. (FR-009, FR-014)

### Tests for User Story 2 (protocol)

- [X] T021 [P] [US2] Write `tests/test_battery_protocol.py`: battery seed sets reproduce the
  spec's first seeds and fingerprints and share no seed with any feature-001/002 set; freeze
  create/validate (hash change → exit 2; missing approval → exit 2); `battery_run.py --set dev`
  refuses held-out seeds; `--stop-on-fail` refused unless `--role negative`; `battery_attempt.py`
  guards (no freeze, unapproved, `started.json` exists, attempt 2 after FAIL, attempt 3) and run
  order positive → negative → candidate, candidate `not_run` after a positive failure,
  INVALID on an equivalence mismatch, incomplete run → INCONCLUSIVE, using a mocked runner and a
  temporary reports directory. (FR-010 to FR-015, SC-004, SC-005)

### Implementation for User Story 2 (protocol and runner)

- [X] T022 [P] [US2] Implement `protocol/battery_seedsets.py` (research R10): `phycoweb-003/`
  prefix, 10 seeds, fingerprints copied from the spec, `load(name, allow)` like feature 002.
  (FR-010, SC-005)
- [X] T023 [P] [US2] Implement `protocol/battery_freeze.py` and `scripts/battery_freeze.py`
  (data-model §6; contracts/cli.md): `attempt` "1 or 2; 2 only if attempt 1's verdict is
  INCONCLUSIVE or INVALID"; `seed_set` "next unused set"; `approved_by`, `approved_on` "empty until
  approved; the attempt refuses without them"; `threshold` = 0.005 / S. (FR-011, FR-013)
- [X] T024 [US2] Implement `scripts/battery_run.py` (research R5; data-model §7): the
  `phyco_stream | tee >(sha256sum) | consumer` pipeline, raw log and p-value files, exit status,
  timing, `complete` flag, dev-only and attempt-only guards. Parsing is applied in T028. (FR-010,
  FR-012, FR-014)

### Dev rehearsal (feature-002 `dev` seed 0 only)

- [X] T025 [US2] Rehearsal for `phyco-v2` on `(56053, 7029, 30841, 11050)`: PractRand to 1 TiB;
  SmallCrush, Crush and BigCrush in both orientations; plus SmallCrush and a PractRand run of at
  least 2³⁵ bytes for `lut-v1` and `os`. Output in `$REP/dev/rehearsal/`; timings in
  `$REP/dev/timing.json`. All results reported (FR-014). (FR-010; R9)
- [X] T026 [US2] Check PractRand's listing threshold against 0.005/S (research R6) with `-a` if
  available, otherwise from the source; record the finding in `$REP/dev/practrand-listing.md`. If
  unlisted results could meet rule 1, switch all runs to the all-results option (stricter only).
  (FR-015; R6)
- [X] T027 [P] [US2] Copy small excerpts of the rehearsal logs into `tests/data/batteries/` and
  write `tests/test_batteries.py`: PractRand and TestU01 parsers on the fixtures, result counts for
  S, rules 1–3 on constructed edge cases (p exactly at 0.005/S, "eps", "1 − eps", PractRand "FAIL"
  grades), and the verdict table from the spec. (FR-014, SC-006)
- [X] T028 [US2] Implement `protocol/batteries.py` (research R8): parsers, S counting, rules 1–3,
  per-run `fails`, overall verdict; wire into `battery_run.py`. (FR-011, FR-014, SC-004, SC-006)
- [X] T029 [US2] Count S from the rehearsal (per generator: one seed's runs × 10) and the
  projected attempt time; write `$REP/dev/S.json`. If the projection exceeds 5 days, report it for
  an owner decision at T034 (scale may not shrink, FR-015). (FR-011; R8, R9)
- [X] T030 [US2] Implement `scripts/battery_attempt.py` (contracts/cli.md; data-model §8): guards,
  `started.json`, held-out equivalence (10⁶ words per seed and model), slot scheduler (≤ 32
  slots), order positive → negative → candidate with halting, negative-only early stop,
  `attempt.json` and `summary.md` with the disclaimer. (FR-012, FR-013, FR-014, FR-016, SC-003,
  SC-004)
- [X] T031 [US2] Implement `scripts/battery_rescore.py` (data-model §9). (SC-006)
- [X] T032 [US2] Write `$REP/dev/phase-report.md` for the tools and rehearsal: tool records,
  rehearsal results in full, timings, S, PractRand listing finding, test results, open issues,
  disclaimer. (FR-009, FR-011, FR-014, FR-016)

### Held-out attempt

- [X] T033 [US2] `battery_freeze.py create --attempt 1 --S <S>` → `$REP/attempt-1/freeze.json`
  (draft, empty approval). (FR-011)
- [X] T034 ⛔ [US2] **Owner battery freeze approval** for attempt 1 (requires T011 and T032).
  Record approval in freeze.json and spec.md. (FR-010, FR-011, SC-005; Principle VIII)
- [ ] T035 [US2] Run `battery_attempt.py --attempt 1` in WSL in the background (1–3 days); log
  progress and any interruption in `$REP/attempt-1/` (an interrupted required run makes the
  attempt INCONCLUSIVE; no restart of a run). (FR-012, FR-014, SC-004)
- [ ] T036 [US2] `battery_rescore.py --attempt 1` → `rescore.json`, identical required. (SC-006)
- [ ] T037 [US2] Write `$REP/attempt-1/phase-report.md`: verdict, both controls, every failing
  result, suspicious results, timings, open issues, disclaimer. (FR-014, FR-016, SC-004)
- [ ] T038 ⛔ [US2] **Owner result review** of attempt 1. Record in spec.md. (Principle VIII)
- [ ] T039 [US2] Only if attempt 1 is INCONCLUSIVE or INVALID: repeat T033–T038 for attempt 2 on
  `heldout-2`, writing to `$REP/attempt-2/`. Otherwise mark not applicable. (FR-013)

**Checkpoint**: battery verdict reviewed.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T040 Run the full test suite on Windows and in WSL; record exact commands and results in
  `$REP/dev/test-log.md`; confirm the feature-002 hashes from T003 are unchanged. (FR-005,
  FR-008; Principle V)
- [ ] T041 Claims check: grep `$REP`, README and new code for "cryptographically secure",
  "crypto-grade", "suitable for secrets", "secure"; confirm the verbatim disclaimer in every
  `summary.md`, `phase-report.md` and record. (FR-016, SC-007)
- [ ] T042 Update README §5 with the calibration result and the battery verdict, with what the
  verdict does and does not mean (preserve CRLF line endings). (FR-016, SC-007; Principle IV)
- [ ] T043 Write the final report `$REP/phase-report.md`: FR-001…FR-016 and SC-001…SC-007 →
  evidence, open issues, security concerns, recommendation. (Principle VII)
- [ ] T044 ⛔ **Owner final result review**. Record in spec.md and update its Status line.
  (Principle VIII)

---

## Dependencies & Execution Order

- **Phase 1 → Phase 2 → US1.** US1 needs no download or C code.
- **US3** can start after Phase 2 (T012–T015 while T008 runs); T016 after T008 (CPU).
- **US2**: T017/T018 (permission) → T019 → T020; T021–T024 any time after Phase 2; T025 needs
  T016, T019, T020, T024; T026–T029 need T025; T030–T031 need T028; T034 needs T011, T029, T032;
  T035 → T036 → T037 → T038 → T039.
- **Polish** after T038 (or T039).

### Parallel opportunities

- T004 ∥ T012 ∥ T021 (test files).
- T022 ∥ T023 (different modules).
- T013–T015 while T008 runs in the background.
- T017/T018 can be asked as soon as the owner wishes; they do not block US1.

## Implementation Strategy

1. **MVP = US1** (T001–T011): answers O3 with no downloads, about one day of machine time.
2. **US3** (T012–T016): streams proven on dev data.
3. **US2** (T017–T039): tools, rehearsal, freeze, one attempt (two only if inconclusive/invalid).
4. **Polish** (T040–T044).

Requirement coverage: FR-001…006 (T004–T011), FR-007…008 (T002, T012–T016), FR-009 (T017–T020),
FR-010…015 (T021–T039), FR-016 (T010, T030, T032, T037, T041–T042); SC-001…002 (T008–T009),
SC-003 (T012, T016, T030), SC-004 (T030, T035), SC-005 (T021–T022, T034), SC-006 (T027–T028,
T031, T036), SC-007 (T041–T042).
