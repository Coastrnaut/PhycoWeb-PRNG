# Implementation Plan: Integer LUT Perturbation Source

**Branch**: `001-integer-lut-perturbation` (spec directory; work is currently on `main` and no
branch has been created) | **Date**: 2026-10-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-integer-lut-perturbation/spec.md`

## Summary

Replace the floating-point `sin`/`cos` food signals in the PhycoWeb reference model with a
committed 256-entry integer sine table, read through two 8-bit phase counters (increments 4 and
6, cosine at a +64 offset, combined period 128 steps). The model is rewritten as a
pure-integer Python module that makes the existing 32-bit overflow behavior explicit, so every
other stage stays bit-identical (research R1, R2). Before the change, the floating-point variant
and the deleted scripts are archived with SHA-256 hashes and run once to produce baseline
vectors. Afterwards, golden vectors and a NIST SP 800-22 screening are produced for both
variants. RTL is out of scope (RTL-pending), but the table ships as a hex file that RTL can read
directly.

## Technical Context

**Language/Version**: Python 3.8+ (developed and tested on 3.10.11)

**Primary Dependencies**: none in the core model (pure standard library). Tools: numpy 2.2.6
(only to run the archived `float-v0` model), nistrng 1.2.3 (evaluation only).

**Storage**: plain files: hex table, hex vectors, JSON manifest and reports.

**Testing**: standard-library `unittest` (research R5)

**Target Platform**: any OS with CPython; outputs must not depend on the platform.

**Project Type**: reference-model library plus command-line tools

**Performance Goals**: generating 10,000 words takes under 5 s; NIST on 10⁶ bits takes under
10 min per run (not a requirement; it only bounds the size of the evaluation).

**Constraints**: no floating point, trigonometry, or division in `phycoweb/model.py`; the output
must match the archived model on every stage except perturbation; archived files are never
modified.

**Scale/Scope**: 1 model module, 1 generated constants module, 4 CLI scripts, 1 test package;
5 archived files; 2 golden vector files; 4 NIST reports.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Evidence / Notes |
|---|-----------|--------|------------------|
| I | Integer-domain, fully specified arithmetic | ⚠️ PASS with justified exception | The perturbation stage is integer-only (FR-002). Every wrap point is explicit (data-model). **Exception**: the flux stage keeps its variable × variable product, which already existed before this feature; see Complexity Tracking. |
| II | Bit-accurate model & differential tests | ✅ PASS (RTL-pending) | Golden vectors and an equivalence test against the archived model for the unchanged stages. No RTL exists, so the feature is flagged RTL-pending (FR-012). |
| III | Synchronous, localized RTL | N/A | No RTL in scope. The hex table format is chosen so RTL can read it. |
| IV | Evidence-based claims | ✅ PASS | Every battery test is reported, including `not_eligible` (research R6). Limitations are stated. The exit code does not hide failures. |
| V | Reproducibility, archival, provenance | ✅ PASS / ⏳ SC-002 open | Manifest with SHA-256 hashes, immutable archive, reports record commands and versions. A second environment is still needed (research R7). |
| VI | Specification before implementation | ✅ PASS | Spec approved 2026-10-28. |
| VII | Traceability | ✅ PASS (at tasks) | The Requirement → Artifact map below is the basis for `/speckit-tasks`. |
| VIII | Human review gates | ✅ Spec gate passed / ⏳ result gate | The result review is required before completion (quickstart step 7). |
| IX | Authorization for outward actions | ✅ PASS | No step commits or pushes; the tools write only local files. |
| Security Policy | | ✅ PASS | Reports state that a NIST pass is not evidence of security. The `readmee.md` claim is out of scope and tracked. |

**Gate result**: PASS, with one justified exception (I). The SC-001 inconsistency found during
planning was resolved on 2026-10-28: the owner approved amending SC-001 so that the
multiplication ban covers only the perturbation stage. `test_purity` checks the perturbation
stage for no multiplication, and the whole module for no float, trigonometry or division.

**Post-design re-check (after Phase 1)**: unchanged. The design added no dependency in the core
model, no outward action and no new exception.

## Project Structure

### Documentation (this feature)

```text
specs/001-integer-lut-perturbation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── model-api.md
│   ├── cli.md
│   └── file-formats.md
├── checklists/requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks; not created here)
```

### Source Code (repository root)

```text
phycoweb/
├── __init__.py
├── model.py             # PhycoWebEngine (lut-v1), pure integer
└── lut.py               # GENERATED by scripts/gen_lut.py

scripts/
├── phase0_audit.py      # existing; unchanged
├── archive_baseline.py
├── gen_lut.py           # offline table generator (float allowed here only)
├── gen_vectors.py
└── nist_eval.py

baseline/float-v0/       # immutable archive (FR-013)
├── readmee_model.py
├── MycoPRNG.py
├── nist_bench.py
├── nistrng_bench.py
├── phycoweb_nist_eval.py
└── MANIFEST.json

data/lut/perturbation_lut.hex
vectors/
├── float-v0_seed-1024-2048-4096-8192_10000.hex
└── lut-v1_seed-1024-2048-4096-8192_10000.hex
reports/001-integer-lut-perturbation/   # NIST JSON records + summary.md

tests/
├── test_purity.py       # AST check (SC-001, FR-002)
├── test_lut.py          # formula, reference values, artifact parity (FR-003, FR-007a, SC-004)
├── test_period.py       # 128-step period over 1,280 steps (FR-007, SC-003)
├── test_equivalence.py  # unchanged stages vs archived model (FR-008)
├── test_vectors.py      # golden vectors (FR-010, SC-002)
└── test_baseline.py     # manifest hashes (FR-013, SC-006)
```

**Structure Decision**: a top-level `phycoweb/` package, so `unittest` and the scripts import it
with no installation step. The scripts add the repository root to `sys.path`, following the
`ROOT` pattern in `scripts/phase0_audit.py`.

**Equivalence-test method (FR-008)**: `test_equivalence.py` injects the same food values into
both models (the LUT values, fed to the archived numpy model by monkey-patching its `np.sin` and
`np.cos` lookups in a test-only copy of the module namespace, never editing the file) and checks
that 10,000 words match. This isolates the perturbation stage as the only difference.

## Requirement → Artifact Map

| Requirement | Artifact(s) | Verification |
|-------------|-------------|--------------|
| FR-001, FR-002, FR-006, FR-007b/c | `phycoweb/model.py` | `test_purity`, `test_period`, `test_vectors` |
| FR-003, FR-004, FR-007a | `scripts/gen_lut.py`, `phycoweb/lut.py` | `test_lut`, `gen_lut.py --check` |
| FR-005, FR-007 | `phycoweb/lut.py` constants | `test_lut`, `test_period` |
| FR-008 | `phycoweb/model.py` | `test_equivalence` |
| FR-009 | `phycoweb/model.py`, `readmee.md` §2 listing | review; listing matches the module |
| FR-010 | `vectors/lut-v1_…hex`, `gen_vectors.py` | `test_vectors` |
| FR-011 | `scripts/nist_eval.py`, `reports/…` | report completeness check in `nist_eval.py` |
| FR-012 | `data/lut/perturbation_lut.hex`, spec status | `test_lut` (format), RTL-pending flag |
| FR-013 | `scripts/archive_baseline.py`, `baseline/float-v0/` | `test_baseline` |
| FR-014 | `vectors/float-v0_…hex`, float-v0 NIST reports | quickstart steps 2 and 6 |
| SC-001 … SC-006 | as above | SC-002 needs a second environment (R7) |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle I: variable × variable product in the flux stage (`D × ΔP`) remains | FR-008 requires the non-perturbation stages to stay unchanged; the product predates this feature | Removing it changes the algorithm. That needs its own spec and human review (spec Open Issue 1) |
| Principle I: explicit 32-bit wrap that reproduces numpy overflow | Required for FR-008 bit-exactness; overflow does happen (research R1) | Wider arithmetic changes outputs; implicit numpy wrap is unspecified behavior (spec Open Issue 2) |
| Principle III: no RTL change in the same change set | No RTL exists yet | Flagged RTL-pending as Principle II allows |
