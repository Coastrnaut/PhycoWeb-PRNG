# Tasks: Integer LUT Perturbation Source

**Input**: Design documents from `specs/001-integer-lut-perturbation/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Included. The spec requires automated verification (FR-010, SC-001 to SC-006) and
Constitution Principle II requires reproducible reference-model tests. Within each story, write
the tests first and confirm they fail before implementing.

**Organization**: Tasks are grouped by user story. Every task cites the requirement IDs it
addresses (Constitution Principle VII).

**Authorization**: No task commits, pushes, or publishes (Principle IX). Stop at each ⛔ gate
and wait for the owner.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on unfinished tasks)
- **[Story]**: US1, US2 or US3 from spec.md
- Commands run from the repository root. `python` means the interpreter that has `numpy` and
  `nistrng` installed (3.10.11 in the dev environment). Tests run with
  `python -m unittest discover -s tests -v`.

## Path Conventions

Top-level package `phycoweb/`, tools in `scripts/`, tests in `tests/`, per the plan's
Project Structure section.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Package skeleton and line-ending rules that keep hashes and vectors stable

- [X] T001 Create the package skeleton: `phycoweb/__init__.py` (docstring only; `MODEL_ID` lives in `model.py`) and an empty `tests/__init__.py`. Create the empty directories `baseline/float-v0/`, `data/lut/`, `vectors/` and `reports/001-integer-lut-perturbation/` by adding a `.gitkeep` to each. (Plan: Project Structure)
- [X] T002 [P] Append to `.gitattributes`: `baseline/** -text` (stops git converting line endings in archived bytes, which would change their SHA-256, FR-013/SC-006) and `*.hex text eol=lf` (contracts/file-formats.md: LF endings). Keep the existing `* text=auto` line first.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Archive the floating-point variant and capture its baseline **before** any model change (FR-013, FR-014; Constitution Principle V)

**⚠️ CRITICAL**: Phases 3–5 must not start until T007 passes. FR-013 requires archiving before the model changes.

- [X] T003 Implement `scripts/archive_baseline.py` per contracts/cli.md.
  - Use the `ROOT = Path(__file__).resolve().parents[1]` and `git_output()` pattern from `scripts/phase0_audit.py`.
  - (a) Read `readmee.md` from git at the pinned commit `0522cbc` (the last commit that changed it) with `git show 0522cbc:readmee.md`, **not** from the working tree. That way T023's later edit to `readmee.md` cannot change the archive or make a re-run fail. Extract the section-2 model listing: the lines after the line `python` that follows the heading `2. Complete Bit-Accurate Python Verification Model`, up to but excluding the next line `Use code with caution.`. Write them byte-for-byte to `baseline/float-v0/readmee_model.py` with LF endings. Define the pinned commit as one constant, `READMEE_COMMIT = "0522cbc"`.
  - (b) Write `git show 290e563^:MycoPRNG.py` to `baseline/float-v0/MycoPRNG.py`.
  - (c) Write `git show d6980eb^:<name>` for `nist_bench.py`, `nistrng_bench.py` and `phycoweb_nist_eval.py` into `baseline/float-v0/`. Use `subprocess` with `capture_output=True` and write raw `stdout` bytes; do not decode and re-encode.
  - (d) Write `baseline/float-v0/MANIFEST.json` with `created_utc`, `git_head` and `files[]` (`archive_path`, `source`, `sha256`, `note`). Use the notes from research R4; all five files, including `nist_bench.py`, have an R4 entry. The `readmee.md` entry's source is `readmee.md@0522cbc (listing in section 2)`.
  - If a target file exists with a different SHA-256, exit 2 without writing anything. If it exists with the same hash, skip it, so the script can be re-run safely. (FR-013)
- [X] T004 Run `python scripts/archive_baseline.py`, then run it a second time. Record both exit codes (expected 0 and 0) and confirm that `MANIFEST.json` lists 5 files. Do not edit any archived file afterwards. (FR-013)
- [X] T005 [P] Write `tests/test_baseline.py`. It loads `baseline/float-v0/MANIFEST.json`, asserts there are exactly 5 entries, and that each `archive_path` exists and its recomputed SHA-256 equals `sha256`. It also asserts `readmee_model.py` contains `class PhycoWebEngine` and `np.sin(self.step_count * 0.1)`. (FR-013, SC-006)
- [X] T006 Implement `scripts/gen_vectors.py` per contracts/cli.md and contracts/file-formats.md, with `--model float-v0` only for now.
  - Load `baseline/float-v0/readmee_model.py` with `importlib.util.spec_from_file_location` (never modify or copy it).
  - Inside a `warnings.catch_warnings()` block that ignores `RuntimeWarning` (numpy int32 overflow, research R1), call `compute_block()` `--count` times and mask each word with `& 0xFFFFFFFF` (research R2).
  - Write the header `# model=float-v0 seed=s0,s1,s2,s3 count=N format=u32-hex`, then one 8-digit uppercase hex word per line, opening the file with `newline="\n"`.
  - `--verify PATH`: regenerate, compare, exit 1 printing the index of the first mismatch, else exit 0.
  - `--seed` takes exactly 4 integers; `--count` must be ≥ 1. (FR-014)
- [X] T007 Run `python scripts/gen_vectors.py --model float-v0 --seed 1024 2048 4096 8192 --count 10000 --out vectors/float-v0_seed-1024-2048-4096-8192_10000.hex`, then the same command with `--verify` in place of `--out`. Confirm line 2 is `D6EDF3D6` and the verify exits 0. Run `python -m unittest tests.test_baseline -v` (expected: pass). (FR-014, SC-006)

**Checkpoint**: The baseline is archived with hashes and has reference vectors. Model work can begin.

---

## Phase 3: User Story 1 - Integer-only reference model (Priority: P1) 🎯 MVP

**Goal**: A pure-integer reference model whose perturbation comes from a committed 256-entry sine table (FR-001 to FR-008)

**Independent Test**: `python -m unittest tests.test_lut tests.test_purity tests.test_period tests.test_equivalence -v` passes.

### Tests for User Story 1 (write first; confirm they fail before T012–T014)

- [X] T008 [P] [US1] Write `tests/test_lut.py`.
  - Recompute `T[i] = int(math.sin(2*math.pi*i/256)*1024) & 0xFFFF` for i = 0…255 and assert it equals `phycoweb.lut.PERTURBATION_LUT`.
  - Assert `T[0]==0x0000`, `T[64]==0x0400`, `T[128]==0x0000`, `T[192]==0xFC00`.
  - Assert every entry, read as signed 16-bit, is within ±1024, has magnitude ≤ `|sin×1024|`, and differs from it by less than 1 (SC-004).
  - Assert `data/lut/perturbation_lut.hex` has exactly 256 lines of 4 uppercase hex digits, LF endings, no header, and matches the tuple entry by entry.
  - Assert `LUT_BITS==8`, `INC_A==4`, `INC_B==6`, `COS_OFFSET==64`.
  - Assert `python scripts/gen_lut.py --check` exits 0 (run it with `subprocess` and `sys.executable`).
  - (FR-003, FR-004, FR-005, FR-007, FR-007a, FR-012, SC-004)
- [X] T009 [P] [US1] Write `tests/test_purity.py` as an AST check of `phycoweb/model.py` and `phycoweb/lut.py`.
  - No `import`/`from` other than `typing` and `phycoweb.lut` / `.lut`.
  - No float `Constant` nodes.
  - No `Div`, `FloorDiv`, `Mod` or `Pow` operators.
  - No calls to any name or attribute `sin`, `cos`, `float` or `math`.
  - No `Mult` inside the method `_perturb` (data-model stages 1–4).
  - `lut.py` contains only int literals.
  - (FR-001, FR-002, SC-001 as amended)
- [X] T010 [P] [US1] Write `tests/test_period.py`.
  - Instantiate `PhycoWebEngine([1024, 2048, 4096, 8192])` and record `(food_a, food_b)` from `_perturb()` for 1,280 steps (SC-003: 10 periods).
  - Assert step 1 reads indices 4 and 70 (FR-007c).
  - Assert step *n* uses `T[(4n) & 0xFF]` and `T[(6n+64) & 0xFF]`.
  - Assert the sequence has period exactly 128, and that no period p < 128 dividing 1,280 satisfies `seq[i] == seq[i+p]` for every i.
  - Assert `food_a` ≠ `food_b` for at least one step in every period (edge case: distinct signals).
  - Set the private `step_count` to `2**32 + 5` and confirm the perturbation still follows the phase counters, not the step count (edge case: counter overflow).
  - (FR-006, FR-007, FR-007b, FR-007c, SC-003)
- [X] T011 [P] [US1] Write `tests/test_equivalence.py` (plan: equivalence-test method).
  - Load `baseline/float-v0/readmee_model.py` with `importlib`, without editing it.
  - Replace the module's global `np` with a shim object. Its `sin(x)` returns `s16(T[(4*round(x/0.1)) & 0xFF]) / 1024` and its `cos(x)` returns `s16(T[(6*round(x/0.15)+64) & 0xFF]) / 1024`, where `s16` reads a 16-bit pattern as signed. All other attributes are delegated to real `numpy`.
  - Run both models for 10,000 words with seed `[1024, 2048, 4096, 8192]` and a second seed `[0x1234, 0xABCD, 0x5555, 0xAAAA]`, suppressing `RuntimeWarning`. Assert `(archived & 0xFFFFFFFF) == new` for every word.
  - Skip with a clear message if `numpy` is not importable.
  - (FR-008)

### Implementation for User Story 1

- [X] T012 [US1] Implement `scripts/gen_lut.py` per contracts/cli.md (floating point is allowed here only; it is offline, Principle I).
  - Compute the table with `int(math.sin(2*math.pi*i/256)*1024) & 0xFFFF` (truncation toward zero, FR-007a).
  - Write `phycoweb/lut.py` with a header comment `# GENERATED by scripts/gen_lut.py — do not edit`, `LUT_BITS = 8`, `INC_A = 4`, `INC_B = 6`, `COS_OFFSET = 64`, and `PERTURBATION_LUT` as a tuple of 256 `0xNNNN` literals, 8 per line.
  - Write `data/lut/perturbation_lut.hex` with 256 lines, 4 uppercase hex digits each, `newline="\n"`.
  - `--check` regenerates both files in memory and exits 1 if either differs from what is on disk, else 0.
  - (FR-003, FR-007a, FR-012)
- [X] T013 [US1] Run `python scripts/gen_lut.py`, then `python scripts/gen_lut.py --check` (expected exit 0). Confirm line 65 of the hex file is `0400` and line 193 is `FC00`. (FR-003)
- [X] T014 [US1] Implement `phycoweb/model.py` per contracts/model-api.md and data-model.md.
  - `MODEL_ID = "lut-v1"`.
  - `wrap32(x)` returns `((x + 0x80000000) & 0xFFFFFFFF) - 0x80000000`, with no `**` or `%`.
  - `class PhycoWebEngine(seed)`:
    - Raise `ValueError` if `len(seed) < 4`, or if any of `seed[0..3]` is not an `int` (a `bool` counts as not an int) or lies outside 0…65535 (FR-008b; data-model: "Values are not masked").
    - Set `P = list(seed[:4])`, `D = [256]*4`, `phase_a = phase_b = 0`, `step_count = 0`.
  - `_perturb()` performs data-model stages 1–4 with no multiplication: increment `step_count`; `phase_a = (phase_a + INC_A) & 0xFF`; `phase_b = (phase_b + INC_B) & 0xFF`; `food_a = PERTURBATION_LUT[phase_a]`; `food_b = PERTURBATION_LUT[(phase_b + COS_OFFSET) & 0xFF]`; `P[0] = (P[0] + food_a) & 0xFFFF`; `P[2] = (P[2] + food_b) & 0xFFFF`. It returns `(food_a, food_b)`.
  - `compute_block()` calls `_perturb()`, then performs stages 5–8:
    - Flux: `Q[k] = wrap32(D[i] * (P[i] - P[j])) >> 8` for (i,j) in (0,1), (1,2), (2,3), (3,0).
    - Growth and decay: `growth = wrap32(abs(Q[k])) >> 2`; `D[k] = (D[k] + growth - (D[k] >> 4)) & 0xFFFF`; if 0 then 1.
    - Disruption: if `D[0] > 4096 or D[2] > 4096`, then `P[1] ^= 0x5A5A` and `P[3] ^= 0xA5A5`.
    - Return the unsigned word `(D0&0xFF)<<24 | (D1&0xFF)<<16 | (D2&0xFF)<<8 | (D3&0xFF)`.
  - Add a comment on the flux line citing spec Open Issues 1 and 2 (the multiplication and wrap are kept on purpose).
  - Stages 5–8 must implement the FR-008a table exactly.
  - (FR-001, FR-002, FR-006, FR-007b, FR-007c, FR-008, FR-008a, FR-008b)
- [X] T015 [US1] Run `python -m unittest tests.test_lut tests.test_purity tests.test_period tests.test_equivalence -v` and record the full output in `reports/001-integer-lut-perturbation/test-log.md` (exact command, Python version, results). Fix the code, not the tests, if anything fails (Principle IV). (SC-001, SC-003, SC-004, FR-008)

**Checkpoint**: The integer-only model works and matches the archived model on every stage except perturbation.

---

## Phase 4: User Story 2 - Deterministic, reproducible sequences (Priority: P2)

**Goal**: Committed golden vectors for `lut-v1` that can be re-verified on any environment (FR-010, SC-002)

**Independent Test**: `python -m unittest tests.test_vectors -v` passes, and `gen_vectors.py --verify` exits 0 on two environments.

### Tests for User Story 2

- [X] T016 [P] [US2] Write `tests/test_vectors.py`.
  - Parse `vectors/lut-v1_seed-1024-2048-4096-8192_10000.hex`: assert the header is exactly `# model=lut-v1 seed=1024,2048,4096,8192 count=10000 format=u32-hex` and there are 10,000 data lines of 8 uppercase hex digits.
  - Assert `PhycoWebEngine([1024,2048,4096,8192])` reproduces every word.
  - Assert two fresh engines with the same seed produce identical 10,000-word sequences.
  - Assert every word is in `0 … 0xFFFFFFFF`.
  - Assert `ValueError` is raised for each of: `[1,2,3]`, `[0,0,0,65536]`, `[-1,0,0,0]`, `[0,0,0,1.0]` and `[True,0,0,0]`.
  - Assert `[65535,0,65535,0]` and `[0,0,0,0]` are accepted (boundaries).
  - Assert a 5-value seed gives the same output as its first four values.
  - (FR-008b, FR-010, SC-002, User Story 2 scenarios 1–2)

### Implementation for User Story 2

- [X] T017 [US2] Extend `scripts/gen_vectors.py` with `--model lut-v1`, using `phycoweb.model.PhycoWebEngine`. Insert the repository root into `sys.path`, use the same output format and `--verify` behavior, and use `MODEL_ID` in the header. (FR-010)
- [X] T018 [US2] Run `python scripts/gen_vectors.py --model lut-v1 --seed 1024 2048 4096 8192 --count 10000 --out vectors/lut-v1_seed-1024-2048-4096-8192_10000.hex`, then the `--verify` form, then `python -m unittest tests.test_vectors -v`. Append the commands and outputs to `reports/001-integer-lut-perturbation/test-log.md`. (FR-010, SC-002)
- [ ] T019 [US2] ⛔ **Owner action**: on a second environment (a different Python minor version or OS, research R7), run the `--verify` command from T018 and `python -m unittest discover -s tests -v`. Record the environment (OS, Python version) and results in `reports/001-integer-lut-perturbation/test-log.md`. SC-002 stays open until this is done. (SC-002)

**Checkpoint**: The golden vectors are committed-ready and checked locally. Cross-environment parity is waiting on the owner.

---

## Phase 5: User Story 3 - Statistical quality is re-measured and reported (Priority: P3)

**Goal**: NIST SP 800-22 screening of `float-v0` and `lut-v1` with complete, honest records (FR-011, FR-014, SC-005)

**Independent Test**: four JSON reports exist, each listing every `SP800_22R1A_BATTERY` test once with a status, plus a `summary.md`.

- [ ] T020 [US3] Implement `scripts/nist_eval.py` per contracts/cli.md and the data-model "Statistical Results Record".
  - Generate `--bits` bits from `--model` (reuse the model loaders from `gen_vectors.py` by importing them; do not duplicate them). Emit each word MSB-first. `--bits` must be a multiple of 32; otherwise exit 2.
  - Convert to a `numpy.int64` array (**not** `int8`: nistrng's Cumulative Sums test overflows on `int8` input and returns a meaningless p-value, analysis finding N1) and run each test in `nistrng.SP800_22R1A_BATTERY` individually on its own `bits.copy()`, checking `is_eligible` first. *(Amended during implementation, finding N2: `run_all_battery` shares one array and Binary Matrix Rank modifies it in place, which corrupts later tests. See research R6.)* The text below about `run_all_battery` return values describes the original approach and no longer applies. Ineligible tests are not run and come back as `None` (or as an entry whose result is `None`). Pair the returned list with `list(nistrng.SP800_22R1A_BATTERY)` by position, and record each `None` as `status: "not_eligible"`, `p_value: null`, `elapsed_ms: null`. Never run an ineligible test. If the returned list length differs from the battery length, exit 2 with an error rather than guessing the pairing.
  - Each record holds `name`, `status` (`pass`/`fail`/`not_eligible`), `p_value` (from `result.score`) and `elapsed_ms`.
  - Write the JSON with: `model`, `seed`, `n_bits`, `bit_order: "msb-first"`; `git_head` and `git_dirty` (from `git status --porcelain`); `versions` (Python, numpy, nistrng from `importlib.metadata`); `command` (`sys.argv` joined); `tests[]`; and `limitations` with at least these two entries:
    - "Single sequence per seed; not the multi-sequence proportion/uniformity analysis of SP 800-22."
    - "Passing statistical tests is not evidence of cryptographic security."
  - Before writing, assert every battery test name appears exactly once.
  - Exit 0 whenever the evaluation ran, regardless of pass/fail.
  - (FR-011, FR-014, SC-005; Principle IV)
- [ ] T021 [US3] Run `scripts/nist_eval.py` four times with `--bits 1000000`: models `float-v0` and `lut-v1` × seeds `1024 2048 4096 8192` and `4660 43981 21845 43690`. Write to `reports/001-integer-lut-perturbation/nist_<model>_seed-<s0>-<s1>-<s2>-<s3>_1000000.json`. Record each command and its wall time in `test-log.md`. If any run takes longer than 10 minutes, say so; do not reduce `--bits` without first amending the spec (Principle IV). (FR-011, FR-014)
- [ ] T022 [US3] Write `reports/001-integer-lut-perturbation/summary.md`.
  - A per-test table with columns test, float-v0 p / status, lut-v1 p / status, for each seed, copied from the JSON files and not rounded beyond 6 decimals.
  - Counts of pass, fail and not_eligible per run.
  - Both limitation statements, verbatim.
  - Any failure listed explicitly, with no interpretation that downplays it.
  - No wording that implies randomness quality or security beyond the numbers.
  - (SC-005; Principle IV, Security Policy)

**Checkpoint**: All three user stories are complete, pending the owner reviews.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T023 [P] Update `readmee.md` section 2. Replace the listing with the contents of `phycoweb/model.py` (or a pointer to it plus a verbatim copy), and add one sentence: "The previous floating-point listing is archived at `baseline/float-v0/readmee_model.py`." Do not change any other section; the "cryptographically secure" wording is a separate item. Verify the archive hash in `MANIFEST.json` still matches (the archive is a copy, so this edit must not affect it). (FR-009)
- [X] T024 [P] Add the line `**Implementation status**: Reference model complete; RTL-pending (Constitution Principle II).` under the Status line in `specs/001-integer-lut-perturbation/spec.md`. (FR-012)
- [ ] T025 Run every quickstart.md step 1–6 in order and `python -m unittest discover -s tests -v`. Append the outputs to `test-log.md`. (All FR/SC)
- [ ] T026 Write `reports/001-integer-lut-perturbation/phase-report.md` per the constitution's Phase Completion Reporting section. It must include: files created or modified; FR/SC IDs, each with its evidence path or marked **open** (SC-002 until T019 is done); the exact commands run and their pass/fail results; open issues (spec Open Issues 1–5); security concerns (the `readmee.md` claim); and a recommendation to proceed, revise or stop. (Principles V, VII)
- [ ] T027 ⛔ **Owner gate (Principle VIII)**: the owner reviews the vectors, `summary.md` and `phase-report.md`, then fills in the "Result review" row in `specs/001-integer-lut-perturbation/spec.md`. The feature is not complete until this is done. Committing any of these files requires separate explicit authorization (Principle IX).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none.
- **Foundational (Phase 2)**: needs T001–T002. Within the phase, T003 → T004 → T005 can run alongside T006; then T007.
- **US1 (Phase 3)**: needs Phase 2. Tests T008–T011 → T012 → T013 → T014 → T015.
- **US2 (Phase 4)**: needs T014 (the model) and T006 (the vector tool).
- **US3 (Phase 5)**: needs T014 and T006, and is independent of US2. T020 imports the loaders from T006/T017; if US2 is not done, it uses the `float-v0` loader plus `phycoweb.model` directly.
- **Polish (Phase 6)**: needs all stories. T027 comes last.

### User Story Dependencies

- **US1**: the MVP, and the foundation for US2 and US3.
- **US2**: needs US1.
- **US3**: needs US1; can run in parallel with US2.

### Parallel Opportunities

- T002 with T001.
- T005 with T006.
- T008, T009, T010 and T011 (separate test files).
- T016 alongside Phase 5 work.
- T023 with T024.

## Parallel Example: User Story 1

```text
# Write all US1 tests together (separate files):
T008 tests/test_lut.py
T009 tests/test_purity.py
T010 tests/test_period.py
T011 tests/test_equivalence.py
# Then, in order: T012 gen_lut.py → T013 run → T014 model.py → T015 run tests
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phases 1–2: archive and baseline (required first by FR-013/FR-014).
2. Phase 3: integer model and tests.
3. **Stop and validate**: T015 passes. This alone removes the Principle I violation in the perturbation stage.

### Incremental Delivery

1. MVP (US1) → 2. golden vectors (US2) → 3. NIST screening (US3) → 4. polish, phase report and owner review.

## Requirement Coverage (Principle VII)

| Requirement | Tasks |
|-------------|-------|
| FR-001 | T009, T014 |
| FR-002 | T009, T014 |
| FR-003 | T008, T012, T013 |
| FR-004 | T008 |
| FR-005 | T008 |
| FR-006 | T010, T014 |
| FR-007 / 007a / 007b / 007c | T008, T010, T012, T014 |
| FR-008 | T011, T014, T015 |
| FR-008a | T011, T014 |
| FR-008b | T014, T016 |
| FR-009 | T023 |
| FR-010 | T016, T017, T018 |
| FR-011 | T020, T021 |
| FR-012 | T008, T012, T024 |
| FR-013 | T002, T003, T004, T005 |
| FR-014 | T006, T007, T020, T021 |
| SC-001 | T009, T015 |
| SC-002 | T016, T018, T019 |
| SC-003 | T010, T015 |
| SC-004 | T008, T015 |
| SC-005 | T020, T021, T022 |
| SC-006 | T005, T007 |

## Notes

- Archived files under `baseline/float-v0/` are immutable once T004 runs.
- If a test fails, fix the implementation. Changing a test or an acceptance criterion requires a spec amendment and owner approval first (Principle IV).
- Record actual commands and outputs in `test-log.md` as you go (Principle V).
