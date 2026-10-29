# Tasks: Core Dynamics Redesign

**Input**: Design documents from `specs/002-core-dynamics-redesign/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Included. The spec's acceptance scenarios and SC-001, SC-004, SC-005 and SC-006 need
automated checks, and Principle II requires reproducible tests. Within each story, write the
tests first and confirm they fail before implementing.

**Organization**: Tasks are grouped by user story, and every task cites the requirement it
serves (Principle VII).
- **Phase order follows dependencies, not priority**: US3 (harness, P3) comes before US1 and
  US2, because the harness has to be validated before any design result can count (plan
  Summary, research R1).
- US1 is still the MVP deliverable, and the harness is its prerequisite.

**Authorization**: No task commits, pushes or publishes (Principle IX). At each ⛔ gate, stop and
wait for the owner. Downloading NIST STS 2.1.2 is approved (plan, Owner Decisions Q2). Nothing
else may be downloaded without asking.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on unfinished tasks)
- **[Story]**: US1, US2 or US3 from spec.md
- Commands run from the repository root. `python` is the interpreter that has numpy and scipy
  (Windows 3.10.11). WSL commands go through `wsl.exe -e bash -lc '…'` using
  `~/.venvs/phycoweb`. Tests run with `python -m unittest discover -s tests -v`. On Windows, set
  `PYTHONIOENCODING=utf-8`.

## Path Conventions

The model is in `phycoweb/`, the harness in `sp80022/`, protocol code in `protocol/`, tools in
`scripts/`, the exploration sandbox in `research/002/`, tests in `tests/`, and reports in
`reports/002-core-dynamics-redesign/` (plan, Project Structure).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Package skeletons and storage rules.

- [X] T001 Create the package skeletons:
  - `sp80022/__init__.py` with a docstring and `__version__ = "0.1.0"`.
  - `protocol/__init__.py` with a docstring only.
  - The directories `research/002/variants/`, `reports/002-core-dynamics-redesign/harness/`,
    `reports/002-core-dynamics-redesign/dev/` and `data/controls/`, each with a `.gitkeep`.
  - (FR-010, FR-015, SC-004; Plan: Project Structure)
- [X] T002 [P] In `.gitignore`, ignore positive-control bytes but keep the directory: add
  `data/controls/*` and `!data/controls/.gitkeep` (plan, Owner Decisions Q1). Also add `*.bin binary` to
  `.gitattributes`, so stored bytes are never line-converted. (SC-004; Principle V)
- [X] T003 [P] Add `scipy` to `requirements.txt`, keeping the existing entries. Record the
  installed versions: scipy 1.15.3 on Windows, 1.18.1 in WSL (FR-010, SC-004; plan, Technical Context; Principle V).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Seed sets, the disclaimer, and the first harness change-log entry. Every story
uses these.

**⚠️ CRITICAL**: No story work starts until this phase is done.

- [X] T004 [P] Write `tests/test_protocol.py::TestSeedSets` (it must fail at first):
  - each of the 4 sets has 100 unique seeds;
  - no two sets share a seed;
  - first seeds and canonical SHA-256 values equal the spec table exactly (`dev` 56053 7029 30841
    11050 / `7e7e33c7…950e`; `heldout-1` 44401 31074 35395 61291 / `84a30b2e…a23d`;
    `heldout-2` 61805 51202 28895 20558 / `13120fcb…14ad4`; `heldout-3` 5899 31471 52105 42678 /
    `af3b9b8e…e88f`; full hashes from spec.md);
  - a tampered expected hash raises `ValueError`;
  - `load(name, allow={"dev"})` raises `PermissionError` for `heldout-*`.
  - (FR-015, SC-006, data-model §2)
- [X] T005 Implement `protocol/seedsets.py` so T004 passes. It provides:
  - `derive(name) -> list[tuple[int,int,int,int]]`, where seed *i* is "the first 8 bytes of
    SHA-256(`phycoweb-002/<name>/<i>`) as 4 big-endian u16", for i = 0…99.
  - `canonical_text(seeds)` producing lines `"a b c d\n"`.
  - `FINGERPRINTS`, with the four full hashes copied from spec.md.
  - `load(name, allow)`, which checks the fingerprint (`ValueError` on mismatch) and the
    allow-list (`PermissionError`).
  - `FEATURE001_SEEDS = [(1024,2048,4096,8192), (4660,43981,21845,43690)]`, for dev use.
  - Standard library only. (FR-015, R8)
- [X] T006 [P] Implement `scripts/seedsets.py` per contracts/cli.md (`--set`, `--print`,
  `--check`; exit 0 or 2). (Quickstart D1) (FR-015, SC-006)
- [X] T007 [P] Create `protocol/disclaimer.py` with one constant `DISCLAIMER`. Its text must
  include both "Passing NIST SP 800-22 does not show cryptographic security" and "This generator
  must not be used to generate secrets". Every report writer imports it. (FR-019, SC-007)
- [X] T008 [P] Create `scripts/repro_nistrng_defects.py`:
  - run every nistrng 1.2.3 test on 4 sequences of 2²¹ bits from `os.urandom`;
  - give each test its own copy and call `random.seed(0)`;
  - use a `multiprocessing` Pool for Linear Complexity;
  - print each test's p-values;
  - write `reports/002-core-dynamics-redesign/harness/nistrng-defects.json`, including versions
    and the command.
  - Run it and confirm N4–N8 reproduce (research R1). If any does not reproduce, stop and report
    it. (Quickstart H0) (FR-014, SC-005; Principle IV)
- [X] T009 Create `reports/002-core-dynamics-redesign/harness-changelog.md` per data-model §6.
  - Entry 1: date 2026-10-28; change "replace nistrng 1.2.3 with own SP 800-22 implementation
    `sp80022`"; categories `defect-fix` (N4–N8) and `added-coverage` (147 more template
    sub-tests; OTM eligible at 2²¹); evidence `harness/nistrng-defects.json`.
  - Include the FR-014 statement that it "removes no test or sub-test, does not shorten
    sequences or loosen thresholds". (FR-014, SC-005)

**Checkpoint**: seed sets are guarded, and the move away from nistrng is justified by recorded
evidence.

---

## Phase 3: User Story 3 - Strictly improved, reproducible test harness (Priority: P3, built first)

**Goal**: A validated own implementation of all 15 SP 800-22 tests, with 148 templates,
deterministic and independently cross-checked.

**Independent Test**:
- `python -m unittest tests.test_sp80022 tests.test_assess -v` passes;
- the positive control passes calibration (quickstart H2);
- re-scoring the stored bytes gives identical JSON (H3);
- NIST STS 2.1.2 agrees to ±1e-6.

### Tests for User Story 3 (write first)

- [X] T010 [P] [US3] Write `tests/test_sp80022.py::TestWorkedExamples`. For each of the 15 SP
  800-22 Rev. 1a test sections, encode the section's worked example (input bits, parameters,
  intermediate statistic, p-value) and assert the p-value to the printed decimals.
  - Transcribe them from the published document (NIST SP 800-22 Rev. 1a, April 2010), citing
    the section number in each test's docstring. **Do not type values from memory.**
  - The PDF may be fetched from nist.gov (csrc.nist.gov/pubs/sp/800/22/r1/upd1/final). Read it;
    it is a reference document, not something to execute.
  - (FR-010, FR-013; R3a)
- [X] T011 [P] [US3] Write `tests/test_sp80022.py::TestAppendixB`.
  - Compute the first 10⁶ binary digits of π, e, √2 and √3 with exact integer arithmetic:
    - √2 and √3 with `math.isqrt`;
    - e from the series Σ 1/k! in fixed point;
    - π with a Machin formula in fixed point;
    - in each case, use 64 guard bits and check them against an independent second method on
      the first 10⁴ bits.
  - Assert every Appendix B p-value for those four expansions, to 6 decimals. Transcribe the
    values from the document as in T010.
  - Cache the expansions in `tests/data/expansions/` as packed bytes, with their SHA-256 in the
    test.
  - (FR-010, SC-004; R3b)
- [X] T012 [P] [US3] Write `tests/test_sp80022.py::TestTemplates`:
  - `templates(m)` counts for m = 2…10 are [2, 4, 6, 12, 20, 40, 74, 148, 284];
  - `templates(9)[0] == "000000001"` and `templates(9)[-1] == "111111110"`;
  - the list is in increasing numeric order.
  - (FR-011, R6)
- [X] T013 [P] [US3] Write `tests/test_sp80022.py::TestHarnessContract`:
  - input not modified (the hash of the bytes is the same before and after `battery`);
  - int8 input with n = 2²¹ gives the same p-values as int64 (N1);
  - two runs give identical p-values (FR-013);
  - p-value counts are 1/1/1/1/1/1/148/1/1/1/2/1/2/8/18 in SP 800-22 order (FR-012);
  - excursions with J < 500 give `eligible=False` and `p_values=[]`;
  - every p is in [0, 1].
  - (contracts/sp80022-api.md)
- [X] T014 [P] [US3] Write `tests/test_sp80022.py::TestKnownBad`. These inputs must fail the
  expected tests (R3e):
  - all zeros;
  - `0101…`;
  - a source biased to 51% ones (from a fixed `random.Random(2026)`);
  - 2²¹ bits of lut-v1 seed `[1024,2048,4096,8192]`.
  - For the first three inputs, assert exactly which tests return p < 0.01. For lut-v1, assert
    only that **at least one** test returns p < 0.01. Its exact failures aren't known in advance,
    and taking them from this harness's own output would be circular.
  - (FR-010; Principle IV: the harness must be able to fail.)
- [X] T015 [P] [US3] Write `tests/test_assess.py`:
  - proportion bound 0.96015 and threshold count 97 at m′ = 100;
  - q(100) rounds to 0.01837;
  - k_max table (2→1, 2→1, 8→1, 18→2, 148→7) at m′ = 100;
  - recomputation for m′ = 80 and m′ = 55;
  - m′ = 54 makes uniformity fail;
  - p = 1.0 falls in the last bin;
  - a family fails when its failed sub-tests (proportion **or** uniformity) exceed k_max;
  - the overall rule: PASS / FAIL / INCONCLUSIVE from the 3 source verdicts.
  - (SC-003; spec Pre-registered Protocol incl. Amendment 1; R4)

### Implementation for User Story 3

- [X] T016 [P] [US3] Implement `sp80022/special.py`:
  - `igamc(a, x)` via `scipy.special.gammaincc`, and `erfc` via `math.erfc`;
  - `binom_sf(n, p, k)` = P(X > k), computed exactly with `fractions.Fraction` and
    `math.comb`, then converted to float. (FR-010; spec Pre-registered
    Protocol; R4)
- [X] T017 [P] [US3] Implement `sp80022/tests_basic.py`: `frequency`, `block_frequency`
  (M=128), `runs` (prerequisite τ = 2/√n, which gives p = 0.0 if it fails), `longest_run`
  (M=10000, K=6), `rank` (32×32 over GF(2), N=2048), and `dft` (T = √(ln(1/0.05)·n),
  N₀ = 0.95·n/2). Use int64 counts and never modify the input. (FR-010, R2)
- [X] T018 [P] [US3] Implement `sp80022/tests_template.py`:
  - `templates(m)` per R6;
  - `non_overlapping_template` (m=9, N=8, M=n/8; μ, σ² and p as in R6; restart after each
    match; 148 p-values in template order);
  - `overlapping_template` (m=9, M=1032, K=5, N=n//1032; Rev. 1a π values from R2).
  - Use vectorized window codes (`numpy` sliding 9-bit code array). (FR-011, R2, R6)
- [X] T019 [P] [US3] Implement `sp80022/tests_complex.py`:
  - `universal`: L=8, Q=2560, K = n//8 − Q; expected value and variance from the SP 800-22
    table for L=8; the c coefficient as in §2.9.
  - `linear_complexity`: M=500, K=6; Berlekamp–Massey over all 4,194 blocks at once as numpy
    uint8 arrays (R5).
  - `serial`: m=16; 2 p-values; ψ² computed with `numpy.bincount` over cyclic windows.
  - `approximate_entropy`: m=10.
  - (FR-010; R2, R5)
- [X] T020 [P] [US3] Implement `sp80022/tests_walk.py`:
  - `cumulative_sums` (forward, then reverse);
  - `random_excursions` (8 states, order −4…−1, +1…+4; ineligible if J < 500);
  - `random_excursions_variant` (18 states, −9…−1, +1…+9; ineligible if J < 500).
  - (FR-012, R2)
- [X] T021 [US3] Implement `sp80022/assess.py` (proportion, uniformity, q(m′), k_max, family and
  overall verdicts, per R4).
  - Complete `sp80022/__init__.py` with `battery(bits)`, which runs the 15 tests in SP 800-22
    order, each on a read-only view (`bits.view(); v.flags.writeable = False`).
  - Also add `templates`, `assess` and `source_sha256()` (the SHA-256 over the package `.py`
    files, sorted by path, LF-normalized).
  - T010–T015 must now pass. Fix the implementation, never the expected values. If an expected
    value seems wrong, stop and report it.
  - (contracts/sp80022-api.md) (FR-010, FR-012, FR-013)
- [X] T022 [US3] Implement `scripts/sts_eval.py` per contracts/cli.md:
  - `--source {phyco-v2,lut-v1,os-csprng,file}`, `--set dev | --seed … | --bytes`,
    `--sequences`, `--workers`, `--save-bytes`, `--out`.
  - It refuses `heldout-*` (exit 2), through `protocol.seedsets.load(allow={"dev"})` or explicit
    `--seed`.
  - It uses a spawn-method `multiprocessing.Pool`, one sequence per job, with results sorted by
    index.
  - It writes the evaluation record from data-model §4, with all its fields, including
    `parameters`, provenance and `DISCLAIMER`.
  - Bits come from `gen_vectors.generate`, MSB-first. When `phyco-v2` doesn't exist yet, that
    choice exits 2 with a clear message.
  - (FR-010, FR-013, R5, R7)
- [X] T023 [US3] Measure throughput: one 2²¹-bit urandom sequence through `battery`, timing
  each test. Target under 60 s per sequence (R5). Record the timings in
  `reports/002-core-dynamics-redesign/harness/timing.json`. If over target, optimize the slowest
  test without changing its results (T010–T015 still pass). (FR-010, SC-003; R5)
- [X] T024 [US3] Positive-control calibration (quickstart H2): run `sts_eval.py --source
  os-csprng --sequences 100 --save-bytes data/controls/cal-<k>.bin --out
  reports/002-core-dynamics-redesign/harness/cal-<k>.json` for k = 1, 2, 3.
  - Then pool all 300 sequences' p-values per sub-test and check uniformity.
  - Expected: each run passes, or fails at most one family by chance (about 19%); pooled
    uniformity P-valueᴛ ≥ 0.0001.
  - If the same sub-test fails in 2 or more runs, treat it as a harness defect: stop and
    investigate. (FR-010, FR-014, SC-005; R3c)
- [X] T025 [US3] Re-score `data/controls/cal-1.bin` with `--source file` and assert the p-values
  and verdicts are byte-identical to `cal-1.json`, apart from timestamps. Also run the same
  re-score in WSL and compare: verdicts exact, p-values within 1e-9. Record the result in
  `reports/002-core-dynamics-redesign/harness/reproducibility.md`. (FR-013, SC-004, R7)
- [X] T026 [US3] ⛔ **Owner action**: in WSL, run `sudo apt install build-essential` (gcc and
  make are missing; sudo is not passwordless). Wait for confirmation. (FR-010; plan Q2; Principle IX)
- [X] T027 [US3] Download NIST STS 2.1.2 from the official nist.gov page
  (csrc.nist.gov, "NIST SP 800-22 … Statistical Test Suite" download) into `~/nist-sts/` in WSL,
  outside the repository.
  - Record the URL, file size and SHA-256.
  - Build it with `make`.
  - Save the build log and hashes in `reports/002-core-dynamics-redesign/harness/sts-2.1.2.md`.
  - Approved by the owner (Q2). Do not run anything else from the archive.
  - (FR-010, SC-004; Principle V; R3d)
- [X] T028 [US3] Create `scripts/sts_oracle_compare.py`:
  - write test inputs as binary files (the 4 Appendix B expansions, plus the first 10 sequences
    of `cal-1.bin`);
  - drive the STS `assess` binary non-interactively (scripted stdin) with the R2 parameters
    (block frequency 128, NOT 9, OTM 9, ApEn 10, serial 16, LC 500);
  - parse its `experiments/AlgorithmTesting/*/results.txt`;
  - compare with `sp80022` per p-value at ±1e-6.
  - Write `reports/002-core-dynamics-redesign/harness/oracle-compare.json` and a short `.md`.
  - Any mismatch blocks Phase 4 until it is explained and logged in the change log. (FR-010, FR-014, SC-005; R3d)
- [X] T029 [US3] Add changelog entries for every harness fix made during T021–T028, each with
  its category and evidence.
  - Bump `sp80022.__version__` to `1.0.0` when T024, T025 and T028 all pass.
  - Then write `reports/002-core-dynamics-redesign/harness/phase-report.md` per the
    constitution's Phase Completion Reporting section. (FR-014, SC-005)
- [X] T030 [US3] ⛔ **Owner review of the harness phase report** (Principle VIII). Phase 4 may
  start only after approval. Add a "Harness review" row to spec.md under Review & Approval.
  (FR-014, SC-005; Principle VIII)

**Checkpoint**: the harness is validated and frozen at 1.0.0. From here on, a changelog entry is
required for any change.

---

## Phase 4: User Story 1 - Redesigned, fully specified generator (Priority: P1) 🎯 MVP

**Goal**: The `phyco-v2` design document and reference model meet FR-001 to FR-009, with the
disruption rate in [1%, 50%], and dev evidence from the validated harness.

**Independent Test**:
- static checks pass (`test_purity_v2`, `test_widths_v2`);
- the disruption rate is within bounds on 100 dev seeds × 10⁶ steps;
- every `design.md` step is traced in code (`test_design_trace`).

### Exploration (dev seeds only)

- [X] T031 [US1] Create `research/002/explore.py`:
  - load a variant module from `research/002/variants/<id>.py` (same API as
    contracts/model-v2-api.md);
  - accept only `--set dev` or the `FEATURE001_SEEDS` (through `protocol.seedsets.load(allow=
    {"dev"})`); anything else exits 2;
  - measure the disruption rate (min/max over seeds, 10⁶ steps each), run the `sp80022` battery
    on N sequences (default 100) with `--workers`, and append one line to
    `research/002/runs.jsonl` with the fields from data-model §7. `explore.py` is the only
    writer of `runs.jsonl`. It refuses to run a variant whose file hash differs from the hash
    already logged for that id.
  - (FR-015, FR-005, SC-006; R9; Principle V)
- [X] T032 [P] [US1] Write `tests/test_protocol.py::TestExploreGuard`: `explore.py --set
  heldout-1` exits 2 and appends nothing to `runs.jsonl`. (SC-006)
- [X] T033 [US1] Iterate on design variants in `research/002/variants/`, guided by research R10.
  - Hard constraints on each variant:
    - FR-001 operations only: no `*`, `/`, `%` or `**`, and constant shift amounts only;
    - every value ≤ 32 bits with an explicit mask or wrap;
    - lut-v1 table, `INC_A = 4`, `INC_B = 6`, `COS_OFFSET = 64` unchanged;
    - nodes, veins, pressure-difference flux, growth/decay and threshold disruption all present
      (FR-004);
    - output from state only;
    - nothing that is, or is derived from, a hash, cipher or standard PRNG (FR-007).
  - Log every run. Include the all-equal seeds `(0,0,0,0)` and `(65535,65535,65535,65535)` as
    explicit dev seeds; they must not give constant or short-cycle output.
  - There is no limit on dev iterations (spec Assumptions).
  - Stop when a variant passes all 15 families on the dev set in 2 independent dev runs, with
    the design unchanged: run 1 uses the first 2²¹ bits after warm-up from each of the 100 dev
    seeds, and run 2 uses the **next** 2²¹ bits from the same seeds. If none does, report to the
    owner rather than loosening anything.
  - Variant files are never edited or deleted once a run with them is logged (Principle V). A
    change creates a new variant id and file. `runs.jsonl` records each file's SHA-256.
- [X] T034 [US1] Write `specs/002-core-dynamics-redesign/design.md` (version 1.0) for the chosen
  variant:
  - state table (name, width, signedness, wrap rule, reset value);
  - seed → state derivation;
  - numbered per-step update in order;
  - disruption rule;
  - output function;
  - `WARMUP`;
  - a **Principle III checklist**, each item answered:
    - all state is registered, with one register-transfer step per update;
    - data flows only between direct grid neighbours;
    - how the disruption condition reaches the nodes (any global signal needs a documented
      timing justification);
    - whether the grid size can be changed (2×2 to 16×16) without restructuring;
    - multiplierless, which gives 0 DSP.
    Any item not met is recorded as an RTL-pending exception in plan.md Complexity Tracking.
  - an FR-007 argument for why this is slime-mold dynamics and not a renamed standard
    generator;
  - links to the dev evidence lines in `runs.jsonl`.
  - (FR-002, FR-004, FR-006, FR-008, FR-009)
- [X] T035 [US1] ⛔ **Owner design review** of `design.md` (Principles III, VI and VIII), including its Principle III checklist.
  Record it in spec.md under Review & Approval as a new row "Design review". Wait for approval.
  (FR-001 to FR-009)

### Tests for User Story 1 (write first, after T035)

- [ ] T036 [P] [US1] Write `tests/test_purity_v2.py`. It is an AST check of
  `phycoweb/model_v2.py`:
  - no `Mult`, `Div`, `FloorDiv`, `Mod` or `Pow` nodes anywhere;
  - no float constants;
  - no names `float`, `math`, `sin` or `cos`;
  - every `LShift`/`RShift` right operand is an int constant;
  - imports only from {`typing`, `phycoweb.lut`}.
  - (FR-001, SC-001, data-model §1)
- [ ] T037 [P] [US1] Write `tests/test_widths_v2.py`. Fuzz from 5,000 random states
  (`random.Random(20261029)`) plus edge states (all 0, all max), step once, and assert every state
  element is within its `design.md` width and signedness. (FR-002)
- [ ] T038 [P] [US1] Write `tests/test_design_trace.py`. A step-by-step re-implementation
  transcribed literally from `design.md`'s numbered list must agree with `model_v2` on
  2 dev seeds × 10,000 words and on the 5,000 fuzz states. (FR-004, Principle II)
- [ ] T039 [P] [US1] Write `tests/test_vectors_v2.py`, covering: golden files for dev seeds 0
  and 1; determinism; `ValueError` for seeds outside 0…65535 and for non-int seeds; seeds of
  length < 4. For the all-equal seeds `(0,0,0,0)` and `(65535,65535,65535,65535)`: the first
  2¹⁶ words are not all equal, and no word value repeats at a fixed lag ≤ 2¹⁵ for the whole
  window (no short cycle). (FR-008, FR-009; spec Edge Cases)
- [ ] T040 [P] [US1] Write `tests/test_disruption_v2.py`. The disruption rate must be in
  [0.01, 0.50] for 3 dev seeds over 10⁶ steps (quick check). The full measurement over 100 seeds
  is T044. (FR-005)

### Implementation for User Story 1

- [ ] T041 [US1] Implement `phycoweb/model_v2.py` exactly as `design.md` 1.0 describes, per
  contracts/model-v2-api.md (`MODEL_ID = "phyco-v2"`, `WARMUP`, `PhycoWebEngineV2`,
  `disruptions`, `step_count`). Do not modify `phycoweb/model.py` or `phycoweb/lut.py`. T036–T040
  must pass. (FR-001 to FR-009)
- [ ] T042 [US1] Add `"phyco-v2"` to `MODELS` in `scripts/gen_vectors.py`. Check that the
  `float-v0` and `lut-v1` outputs stay byte-identical (`--verify` against both existing vector
  files). Generate `vectors/phyco-v2_seed-<a>-<b>-<c>-<d>_10000.hex` for dev seeds 0 and 1.
  (FR-008, contracts/cli.md)
- [ ] T043 [US1] Run the full test suite (all feature-001 tests plus the new ones) on Windows
  and in WSL. Record the results in `reports/002-core-dynamics-redesign/dev/test-log.md`. (SC-001, SC-004;
  Principle V)
- [ ] T044 [US1] Measure the disruption rate on all 100 dev seeds × 10⁶ steps. Write
  `reports/002-core-dynamics-redesign/dev/disruption.json` with the min, max and per-seed rates.
  All must be in [1%, 50%]. (FR-005, SC-002)
- [ ] T045 [US1] Write the dev evidence: `python scripts/sts_eval.py --source phyco-v2 --set dev
  --out reports/002-core-dynamics-redesign/dev/dev-final.json`. Also run `--source lut-v1 --set
  dev`, which must fail at least one family (to show the harness can discriminate). This is
  **not** an acceptance result. (Quickstart M3) (FR-015, SC-006; Principle IV)

**Checkpoint**: the reference model is complete and tested. Dev evidence exists. No held-out
seed has been touched.

---

## Phase 5: User Story 2 - Pre-registered statistical verdict (Priority: P2)

**Goal**: A gated acceptance attempt that produces PASS, FAIL or INCONCLUSIVE, with both
controls, and is reproducible.

**Independent Test**: `tests/test_protocol.py` passes (freeze and acceptance refusals). One
attempt record exists, and re-scoring it gives identical results.

### Tests for User Story 2 (write first)

- [ ] T046 [P] [US2] Write `tests/test_protocol.py::TestFreeze`. Use a temporary reports
  directory and patch the path roots. Check:
  - `freeze.py` writes `approved_by` and `approved_on` as empty strings;
  - it refuses if N is not the next attempt, if `attempt-N/` exists, or if the model, design or
    harness has uncommitted changes (mock the git status);
  - the hashes in the record equal the files' SHA-256.
  - (FR-016, data-model §3)
- [ ] T047 [P] [US2] Write `tests/test_protocol.py::TestAcceptanceGuard`. `acceptance.py` exits
  2 in each of these cases, without evaluating anything:
  - the freeze is missing;
  - the approval fields are empty;
  - the model, design or harness hash differs from the freeze;
  - `attempt.json` already exists for that set;
  - N is greater than 3.
  - Also test that the run order is positive, then negative, then candidate (patch the evaluator
    and record the call order).
  - (FR-016, FR-017, FR-018, SC-006)

### Implementation for User Story 2

- [ ] T048 [US2] Implement `protocol/freeze.py` (create, load and validate the freeze record
  from data-model §3) and `scripts/freeze.py` per contracts/cli.md. T046 must pass. The tool
  never writes the approval fields. (FR-016)
- [ ] T049 [US2] Implement `scripts/acceptance.py` per contracts/cli.md and research R8. T047
  must pass.
  - Steps:
    1. Validate the freeze.
    2. Load the set with `allow={f"heldout-{N}"}`.
    3. Positive control: 100 × 2²¹ bits from `os.urandom`, saved to
       `data/controls/attempt-N.bin`, with its SHA-256 recorded.
    4. Negative control: lut-v1 on the 100 held-out seeds.
    5. Candidate: phyco-v2 on the same seeds.
    6. Write `eval-positive.json`, `eval-negative.json`, `eval-candidate.json`, `attempt.json`
       and `summary.md` (with `DISCLAIMER`), and set the overall verdict per the spec. Each
       `summary.md` also states its limitations: positive-control bytes are stored only
       locally (`data/controls/`, Q1), so only this machine can re-score the attempt; only
       SP 800-22 was run.
  - **If the positive control fails**: stop before generating or scoring the candidate. Write
    the attempt as INCONCLUSIVE with `candidate: "not run (positive control failed; spec Edge
    Cases)"`, and count the attempt as used. This follows spec Edge Cases and FR-017 (Amendment 1). The negative control still runs
    and is reported.
  - A sub-test fails on proportion **or** uniformity, and both count toward k_max (Amendment
    1; T015).
  - If the negative control passes: still run the candidate, report all three, and set the
    verdict to INCONCLUSIVE.
  - Exit 0 only for PASS. (FR-017, FR-018, SC-003)
- [ ] T050 [US2] Write `scripts/rescore_attempt.py --attempt N`. It re-scores the saved control
  bytes and regenerates both models from the recorded seeds, then asserts identical p-values and
  verdicts. (SC-004, quickstart A4)
- [ ] T051 [US2] ⛔ **Owner commits** `phycoweb/model_v2.py`, `phycoweb/lut.py`, `design.md`,
  `sp80022/` and the phyco-v2 vectors, so `freeze.py` sees a clean tree and `git_head` identifies
  the frozen design. The agent never commits (Principle IX). Wait for confirmation.
  (FR-016, SC-006)
- [ ] T052 [US2] Create `reports/002-core-dynamics-redesign/attempt-1/freeze.json` with `python
  scripts/freeze.py --attempt 1 --dev-evidence reports/002-core-dynamics-redesign/dev/dev-final.json`.
  Present the record to the owner. (FR-016, SC-006)
- [ ] T053 [US2] ⛔ **Owner design-freeze approval for attempt 1.** The owner fills in
  `approved_by` and `approved_on` in `freeze.json`. Add a "Design freeze 1" row to spec.md under
  Review & Approval. (FR-016)
- [ ] T054 [US2] Run `python scripts/acceptance.py --attempt 1 --workers 32`. Then run `python
  scripts/rescore_attempt.py --attempt 1`. Report the verdict as-is, whatever it is. (SC-003,
  SC-004)
- [ ] T055 [US2] ⛔ **Owner result review for attempt 1.** On PASS, go to Phase 6. On FAIL or
  INCONCLUSIVE, the owner chooses one of:
  - (a) redesign: archive first (T056), bump the `design.md` version, return to T033 using **dev seeds only**, then
    T041–T045, then repeat T051–T056 for attempt 2 and then 3 (new freeze, next set);
  - (b) stop and report the goal as not met.
  - A held-out set is never reused. After attempt 3, no further attempts are made without a spec
    amendment. (FR-018, spec Edge Cases)

- [ ] T056 [US2] **Archive before any redesign** (Principle V). If T055 chooses redesign,
  first copy the frozen `phycoweb/model_v2.py`, `design.md` and `vectors/phyco-v2_*.hex` to
  `baseline/phyco-v2.<k>/`, where k is the attempt number. Write `baseline/phyco-v2.<k>/MANIFEST.json`
  with the SHA-256 of each file. Its `model_sha256` and `design_sha256` must equal the values in
  `attempt-<k>/freeze.json`. Extend `tests/test_baseline.py` to check those hashes. The redesigned model
  then gets `MODEL_ID = "phyco-v2.<k+1>"`. Archived files are never modified.
  (FR-018, FR-008; Principle V)

**Checkpoint**: a pre-registered verdict exists, with controls, and is reproducible.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T057 [P] Re-score the four feature-001 inputs with the validated harness: the 10⁶-bit
  sequences for `float-v0` and `lut-v1` × 2 seeds, regenerated from `gen_vectors.generate`. Run
  them with `sts_eval.py --source file`, and note that single sequences give per-test p-values
  only, with no proportion or uniformity. Add a re-score table below the erratum in
  `reports/001-integer-lut-perturbation/summary.md`, leaving the approved text unchanged.
  (FR-010, FR-014; Principle IV; plan Q3, quickstart H5)
- [ ] T058 [P] SC-007 check: grep every file under `reports/002-core-dynamics-redesign/`, plus
  `design.md`, for "cryptographically secure", "secure", "crypto-grade" and "suitable for
  secrets" used as claims. Every `summary.md` and `phase-report.md` must contain `DISCLAIMER`.
  Record the result in the final phase report. (FR-019, SC-007)
- [ ] T059 Run quickstart.md end to end (H1–H5, D1, M1–M3, A4 for each completed attempt) on
  Windows and in WSL. Append the results to `reports/002-core-dynamics-redesign/dev/test-log.md`. (SC-001 to SC-007)
- [ ] T060 Write `reports/002-core-dynamics-redesign/phase-report.md` per the constitution's
  Phase Completion Reporting section. It covers: files changed; requirements → evidence
  (FR-001 to FR-019, SC-001 to SC-007); tests actually run; every attempt and its verdict; open
  issues (including the `wrap32(abs(Q))` no-op from feature 001; check that `README.md` section 5
  still matches the evidence and update it with this feature's verdict);
  security concerns; known limitations (including that the broader batteries recommended by
  Principle IV, such as PractRand, TestU01 and Dieharder, were not run, and that
  positive-control bytes are local only); and a recommendation (proceed, revise or stop). (FR-001 to FR-019, SC-001 to SC-007;
  Principle VII)
- [ ] T061 ⛔ **Owner final result review** (Principle VIII). Record it in spec.md under Review &
  Approval, and update the spec Status line. (SC-003; Principle VIII)

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1) → Foundational (Phase 2) → US3 harness (Phase 3, ends at gate T030)
  → US1 (Phase 4, gate T035 before T036) → US2 (Phase 5, gates T051, T053, T055) → Polish (Phase 6).
- T057 needs only Phase 3 to be done, so it can run in parallel with Phase 4.
- T026 (owner installs build tools) can be requested at the start, so T027 and T028 aren't
  blocked later.

### User Story Dependencies

- **US3** depends only on Foundational.
- **US1** needs the validated harness (US3) for dev evidence. Its static and model tests
  (T036–T044) do not need the harness.
- **US2** needs US1 (a frozen design) and US3 (the validated judge).

### Within Each Story

- Tests before implementation. In US1, exploration and the design review come before tests,
  because the tests encode the reviewed design.

### Parallel Opportunities

- Phase 1: T002 and T003.
- Phase 2: T004, T006, T007 and T008 (T005 after T004; T009 after T008).
- US3: test-writing tasks T010–T015 together, then implementation tasks T016–T020 together.
  T021 merges them.
- US1: T036–T040 together after T035.
- US2: T046 and T047 together.
- Polish: T057 and T058.

## Parallel Example: User Story 3

```text
# Write all harness tests at once:
T010 worked examples · T011 Appendix B · T012 templates · T013 contract · T014 known-bad · T015 assess
# Then implement the test modules at once:
T016 special.py · T017 tests_basic.py · T018 tests_template.py · T019 tests_complex.py · T020 tests_walk.py
```

## Implementation Strategy

### MVP

Phases 1–3, then Phase 4 up to T045. This delivers a validated harness and a fully specified,
tested, multiplierless `phyco-v2` with dev evidence. It is useful even if no attempt passes.

### Incremental Delivery

1. Harness phase report (T029, T030). This alone corrects the feature-001 record (T057).
2. Design review (T035), then the model.
3. Acceptance attempts, each behind its own freeze gate.

## Requirement Coverage (Principle VII)

| Requirement | Tasks |
|-------------|-------|
| FR-001, SC-001 | T033, T036, T041 |
| FR-002 | T034, T037, T041 |
| FR-003 | T033, T041 (lut unchanged; existing `test_lut`) |
| FR-004 | T033, T034, T038 |
| FR-005, SC-002 | T031, T040, T044 |
| FR-006 | T034, T041 |
| FR-007 | T033, T034, T035, T036 (imports) |
| FR-008 | T034, T039, T042 |
| FR-009 | T034, T039 |
| FR-010 | T017–T022 |
| FR-011 | T012, T018 |
| FR-012 | T013, T020, T021 |
| FR-013, SC-004 | T013, T025, T050, T054 |
| FR-014, SC-005 | T009, T029 |
| FR-015, SC-006 | T004, T005, T031, T032, T047 |
| FR-016 | T046, T048, T051, T052, T053 |
| FR-017, FR-018, SC-003 | T047, T049, T054, T055, T056 |
| FR-019, SC-007 | T007, T049, T058 |
| Principle V (archive superseded variants) | T031, T033, T056 |
| Q1 (control storage) | T002, T049 |
| Q2 (NIST STS oracle) | T026–T028 |
| Q3 (feature-001 erratum) | erratum added 2026-10-28; T057 re-score |

## Notes

- **O1 (resolved)**: the positive-control halt rule and the counting of uniformity failures
  toward k_max are now in the spec (Amendment 1, approved 2026-10-28). T049 implements them.
- The harness becomes authoritative only after gate T030. Dev results produced earlier are
  exploratory and are labeled as such.
- Never edit an expected value (worked example, Appendix B, oracle) to make a test pass.
  Mismatches are investigated and logged.
