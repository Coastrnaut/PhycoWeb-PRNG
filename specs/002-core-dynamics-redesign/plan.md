# Implementation Plan: Core Dynamics Redesign

**Branch**: `002-core-dynamics-redesign` (spec directory; work is on `main` and no branch has been
created) | **Date**: 2026-10-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-core-dynamics-redesign/spec.md`

## Summary

Redesign the PhycoWeb core dynamics as a new integer-only, multiplierless reference model
(`phyco-v2`), keeping the lut-v1 table, and judge it with a pre-registered SP 800-22 protocol on
held-out seeds.

Planning found that **nistrng 1.2.3 cannot serve as the judge**. On fresh OS-CSPRNG data, 5 of
its 15 tests give impossible results (research R1, defects N4–N8). It also has no 148-template
set. The plan therefore starts with a **self-implemented, validated SP 800-22 harness**
(`sp80022/`). This harness is validated against the specification's worked examples, the
Appendix B reference values and the positive control *before* any design result counts.

After that come:
- dev-only exploration with every run logged;
- a design document reviewed at freeze;
- the `phyco-v2` model with golden vectors;
- up to three gated acceptance attempts.

The same finding means the feature-001 Linear Complexity and Random Excursion failures are
harness artefacts. An erratum is planned, subject to owner approval.

## Technical Context

**Language/Version**: Python 3.10+ (developed on 3.10.11 on Windows; cross-checked on 3.14.4 in
WSL Ubuntu)

**Primary Dependencies**:
- Model: none (standard library only).
- Harness: numpy (2.2.6 / 2.5.4) and scipy (1.15.3 / 1.18.1, for `gammaincc` only).
- Optional: nistrng 1.2.3 (only for the defect reproduction and informative cross-checks), and
  NIST STS 2.1.2 (only if the owner approves downloading it, research R3d).

**Storage**: plain files: JSON records, hex vectors, Markdown reports, `runs.jsonl`, and
positive-control byte files (location: Q1).

**Testing**: standard-library `unittest`, as in feature 001.

**Target Platform**: any OS with CPython. Results do not depend on the platform, with p-values
compared across environments within 1e-9 (research R7).

**Project Type**: reference-model library, statistics harness package, command-line tools.

**Performance Goals**: battery under 60 s per 2²¹-bit sequence; one acceptance attempt (300
sequences) under 1 h on 32 workers (measured baseline: nistrng 128 s/sequence, research R5).

**Constraints**:
- The generator follows FR-001 to FR-009 (no multiplication, division or float; ≤ 32-bit values;
  constant shifts only).
- The harness may only become stricter (FR-014).
- Held-out seeds are untouchable before an approved freeze (FR-015, SC-006).

**Scale/Scope**:
- New: 1 model module; harness package (about 15 test functions plus assessment);
  `protocol/` (seed sets, freeze); 4 CLI tools; exploration sandbox; about 6 new test modules.
- Data: 100 dev seeds; up to 3 × 300 evaluated sequences.

**Known limitations**:
- Only SP 800-22 is run. The broader batteries that Principle IV recommends (SHOULD:
  PractRand, TestU01, Dieharder) are out of scope, and this is reported in the final phase
  report.
- Positive-control bytes are stored only locally (Q1), so only this machine can re-score an
  attempt.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Evidence / Notes |
|---|-----------|--------|------------------|
| I | Integer-domain, fully specified arithmetic | ✅ PASS | FR-001 and FR-002 go further than spec 001: the multiplier is removed, which resolves the spec-001 Complexity exception. Purity AST check without `Mult` anywhere, and constant shifts only (data-model §1). Floats occur only in the harness, which is not hardware (R7). |
| II | Bit-accurate model and differential tests | ✅ PASS (RTL-pending) | Golden vectors for 2 dev seeds. A design-vs-model trace test checks that every `design.md` step matches the code. There is no RTL, so the feature is flagged RTL-pending (FR-008). |
| III | Synchronous, localized RTL | N/A (constrains the design) | No RTL in scope. The design must pass the Principle III checklist in `design.md` (registered state, one register-transfer step per update, neighbour-only data flow, a justified disruption signal path, a parameterizable grid, 0 DSP). Unmet items become RTL-pending exceptions in Complexity Tracking. Reviewed at the design gate (T035). |
| IV | Evidence-based claims | ✅ PASS | Pre-registered protocol with controls. The harness is validated before use (R3), so a broken judge cannot produce a pass or a fail. Every attempt is reported. The FR-019 disclaimer is checked. Correcting feature 001 by erratum, not by silent edit, follows this principle. |
| V | Reproducibility, archival, provenance | ✅ PASS | Seed sets are derived and fingerprinted. Records hold the model, design and harness hashes. Control bytes are saved and hashed (R7). Re-scoring step A4. |
| VI | Specification before implementation | ✅ PASS | Spec approved 2026-10-28. The design is specified in `design.md` before `model_v2.py` is written (R9). |
| VII | Traceability | ✅ PASS (at tasks) | Requirement → artifact map below. |
| VIII | Human review gates | ✅ Spec gate passed / ⏳ 4 gates planned | (1) erratum to feature 001; (2) design review; (3) freeze approval before each attempt, enforced in code; (4) result review. |
| IX | Authorization for outward actions | ✅ PASS | No tool commits or pushes. Downloading NIST STS is an outward action and is held for the owner's decision. |
| Security Policy | | ✅ PASS | The FR-019 disclaimer is in every report, and SC-007 is checked by grep. The positive control uses the OS CSPRNG, in the harness only. |
| Phase Completion Reporting | | ✅ PASS | A phase report goes at the end of the harness phase and after each attempt. |

**Gate result**: PASS. No exceptions.

**Post-design re-check (after Phase 1)**: PASS, with one item raised.
- The design added a harness package and protocol tooling, but no dependency in the model.
- The raised item is the feature-001 erratum. It touches an approved record, so it is listed as
  a Principle VIII gate, not done here.
- The protocol is unchanged. The research parameter choices (R2) are the SP 800-22 / STS
  defaults and do not loosen anything. The template set grows from 1 to 148.

## Project Structure

### Documentation (this feature)

```text
specs/002-core-dynamics-redesign/
├── plan.md              # this file
├── research.md          # R1–R10 (R1: nistrng defects N4–N8)
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── sp80022-api.md
│   ├── cli.md
│   └── model-v2-api.md
├── design.md            # written in the exploration phase; owner-reviewed (not created by /speckit-plan)
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
sp80022/                 # NEW harness: own SP 800-22 Rev. 1a implementation
├── __init__.py          # __version__, battery(), templates(), assess(), source_sha256()
├── tests_basic.py       # frequency, block_frequency, runs, longest_run, rank, dft
├── tests_template.py    # non_overlapping_template (148), overlapping_template
├── tests_complex.py     # universal, linear_complexity, serial, approximate_entropy
├── tests_walk.py        # cumulative_sums, random_excursions, random_excursions_variant
├── assess.py            # proportion, uniformity, q(m′), k_max, verdicts
└── special.py           # igamc / erfc wrappers, binomial helpers
protocol/                # NEW
├── seedsets.py          # derivation + fingerprint guard + allow-list
└── freeze.py            # freeze record read/write/validate
phycoweb/
├── model.py             # lut-v1, unchanged (negative control)
├── lut.py               # unchanged
└── model_v2.py          # NEW phyco-v2 (after design review)
scripts/
├── gen_vectors.py       # + "phyco-v2"
├── seedsets.py, sts_eval.py, freeze.py, acceptance.py   # NEW (contracts/cli.md)
└── nist_eval.py         # unchanged (feature-001 record)
research/002/            # NEW exploration sandbox (dev seeds only)
├── explore.py, variants/
└── runs.jsonl
tests/
├── existing feature-001 tests (unchanged, must keep passing)
├── test_sp80022.py      # worked examples, Appendix B, templates, invariance, determinism
├── test_assess.py       # q, k_max table, proportion/uniformity edge cases
├── test_protocol.py     # fingerprints, held-out refusal, freeze checks
├── test_purity_v2.py, test_widths_v2.py, test_vectors_v2.py, test_design_trace.py
reports/002-core-dynamics-redesign/
├── harness-changelog.md, harness/ (calibration records), dev/ (dev records)
└── attempt-<N>/ (freeze.json, eval-*.json, attempt.json, summary.md)
data/controls/           # positive-control bytes (git-ignored by default; Q1)
```

**Structure Decision**: one repository with three cleanly separated layers: the model
(`phycoweb/`), the judge (`sp80022/`) and the protocol (`protocol/`), plus thin scripts. The
harness never imports the model, and the model never imports numpy. Exploration lives outside
the package, so tuning code cannot leak into the reference model by accident.

## Requirement → Artifact Map

| Requirement | Artifact / check |
|-------------|------------------|
| FR-001, FR-002, SC-001 | `model_v2.py`; `test_purity_v2`, `test_widths_v2` |
| FR-003 | `model_v2.py` imports `phycoweb.lut`; `test_lut` unchanged |
| FR-004, FR-006, FR-009 | `design.md`; `test_design_trace`; seed domain tests |
| FR-005, SC-002 | disruption measurement (quickstart D3) in the dev record |
| FR-007 | import allow-list; design review gate |
| FR-008 | `vectors/phyco-v2_*.hex`; `test_vectors_v2`; `design.md` |
| FR-010 – FR-013, SC-004 | `sp80022/`; `test_sp80022`; quickstart H1–H3, A4 |
| FR-014, SC-005 | `harness-changelog.md` |
| FR-015 – FR-018, SC-003, SC-006 | `protocol/`, `freeze.py`, `acceptance.py`; `test_protocol`; attempt records |
| FR-019, SC-007 | disclaimer constant used by every report writer; grep check |

## Owner Decisions (2026-10-28)

- **Q1 — the default**: positive-control bytes go in a git-ignored `data/controls/`. Only their
  SHA-256 values are committed, inside the records.
- **Q2 — yes**: NIST STS 2.1.2 is downloaded from nist.gov and built in WSL Ubuntu as the
  independent oracle (research R3d).
  - WSL has `curl` and `unzip` but no `gcc` or `make`. Installing them needs
    `sudo apt install build-essential`, which the owner runs (sudo is not passwordless).
  - The download is recorded with its URL, file size and SHA-256. The source tree is unpacked
    outside the repository (`~/nist-sts/`), and only the hash and the build log are kept.
  - An earlier answer named [sts-pylib](https://pypi.org/project/sts-pylib/) 0.0.5. The final
    answer replaces it. It was also unsuitable: it has only Linux wheels for CPython 3.6–3.8,
    and no sdist.
- **Q3 — yes**: an erratum was added to `reports/001-integer-lut-perturbation/summary.md` on
  2026-10-28. The re-score with the new harness (quickstart H5) is still to be done.

## Complexity Tracking

No constitution violations. The spec-001 exception (flux multiplier) is resolved by FR-001 in
this feature.

RTL-pending exceptions from the `design.md` 1.0 Principle III checklist (raised for the owner
at the design review, T035):

| Item | Exception | Why accepted for now | Resolution |
|------|-----------|----------------------|------------|
| Grid parameterization (Principle III: 2×2 to 16×16 without restructuring) | `phyco-v2` is a fixed 4-node ring (the 2×2 grid). Larger grids are not designed | No RTL in scope. The statistical question is answered for the 2×2 core first | Generalization belongs to a later RTL feature |
| Timing (≥ 200 MHz target, a SHOULD) | About 7 serial 32-bit carry chains per step (`design.md` §7) | No RTL in scope | Report at synthesis; restructuring would be a new design version |
| Food source and output tap | The food source drives nodes 0 and 2; the output reads all 4 nodes | Point-to-point signals and an output function, not a grid broadcast (`design.md` §7) | Owner judgment at T035 |
