# Implementation Plan: Extended Batteries and Positive-Control Calibration

**Branch**: `003-extended-batteries-calibration` | **Date**: 2026-10-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-extended-batteries-calibration/spec.md`
(approved 2026-10-29).

## Summary

Two pieces of evidence about the feature-002 result, with no change to any generator:

1. **Calibration (US1, O3)**: 1,000 simulated positive-control runs (100 × 2²¹ bits of OS
   random data each) scored by the frozen `sp80022` 1.0.0 harness and the feature-002 rules,
   reusing the feature-002 code path; exact binomial intervals for the overall, per-family and
   per-sub-test false-failure rates, family co-failures, and the implied PASS probability
   (research R2, R3). About 17 h on Windows, no downloads.
2. **Batteries (US2, US3)**: a C fast stream for `phyco-v2`, `lut-v1` and the OS RNG, proven
   word-for-word equal to the Python reference models (R4), piped into PractRand
   (`stdin32 -tlmax 1TB -tf 2`) and TestU01 SmallCrush, Crush and BigCrush in both bit
   orientations (R5–R7), in WSL. The pre-registered failure rule is a two-sided Bonferroni bound
   over all S p-values (R8), with S fixed by a dev rehearsal (R9) before a battery freeze. Order
   positive → negative → candidate on 10 held-out seeds; at most two attempts.

## Technical Context

**Language/Version**: Python 3.10.11 (Windows) and 3.14.4 (WSL venv `~/.venvs/phycoweb`); C99
for the fast stream and the TestU01 driver (gcc 15.2.0 in WSL).

**Primary Dependencies**: existing `sp80022` 1.0.0 (frozen), numpy 2.2.6, scipy 1.15.3 (for
Clopper–Pearson and Fisher, analysis only). Third-party, outside the repository, each download
owner-approved: PractRand (latest SourceForge release, R6), TestU01 1.2.3 (R7).

**Storage**: JSON / gzip JSON records and text logs under
`reports/003-extended-batteries-calibration/`; no generator or control bytes stored. About
150 MB of calibration records (commit-or-local decision at the calibration review, R10) and
under 100 MB of battery logs per attempt.

**Testing**: `python -W ignore -m unittest discover -s tests -t .` on both platforms; C tests
via the equivalence script; WSL-only tests skip cleanly on Windows.

**Target Platform**: Windows 11 (calibration) and Ubuntu on WSL2 (streams, batteries);
i9-14900K, 32 logical CPUs, 31 GiB RAM, 953 GB free.

**Project Type**: research tooling inside the existing single Python project.

**Performance Goals**: calibration ≤ 24 h; fast stream ≥ 10⁸ words/s per core; one battery
attempt ≤ 5 days (measured at the dev rehearsal before the freeze).

**Constraints**: no generator change; feature-002 protocol, harness, seed sets and tools
untouched; all battery rules fixed before held-out use and stricter-only; no download without
per-file permission; no commit or push by the agent.

**Scale/Scope**: 1,000 × 100 SP 800-22 evaluations; per attempt 3 generators × 10 seeds ×
(1 PractRand to 1 TiB + 6 TestU01 runs) = 210 runs, about 90 TiB streamed.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design (below).*

| Principle | Check | Status |
|-----------|-------|--------|
| I. Integer, fully specified arithmetic | No generator changes. The C `phyco-v2` uses only the design's operations (test bans `*`, `/`, `%` in it). The C `lut-v1` contains the recorded feature-001 multiplication, only to reproduce the negative control | Pass (see Complexity Tracking) |
| II. Bit-accurate reference model | Python models stay golden; the C stream is checked against golden vectors, 2 × 100 × 10⁶ dev words, and every held-out seed before each attempt (INVALID on mismatch) | Pass |
| III. RTL | No RTL in scope | N/A |
| IV. Evidence-based claims | Rules fixed in the approved spec; Bonferroni bound independent of test dependence; controls each attempt; every result reported; no re-seeding; FAIL final; disclaimer in every record | Pass |
| V. Reproducibility, provenance | Tool archives and binaries hashed; commands, versions and stream hashes recorded; re-score from logs; deterministic generators regenerable from seeds; calibration bytes identified by hash | Pass |
| VI. Specification before implementation | Spec approved 2026-10-29; no algorithm change | Pass |
| VII. Traceability | Tasks will reference FR/SC; phase report maps FR-001…016, SC-001…007 to evidence | Pass (enforced in tasks) |
| VIII. Human review gates | Gates: tool downloads, calibration result review, battery freeze, result review, final review | Pass |
| IX. Outward actions | Agent never commits, pushes or publishes; downloads only with explicit permission | Pass |
| Security Policy | OS RNG used only as a control; disclaimer everywhere; no claim of security | Pass |
| Technical Constraints | Adds C tooling and two external tools, analysis-only, never imported by the core model | Justified (Complexity Tracking) |

**Post-design re-check**: the design (research R1–R11, data model, contracts) adds no
generator behaviour, keeps the feature-002 modules unchanged (new `protocol/battery_*` modules
instead), and every guard in the contracts maps to a spec rule. No new violations.

## Project Structure

### Documentation (this feature)

```text
specs/003-extended-batteries-calibration/
├── spec.md
├── plan.md              # this file
├── research.md          # R1–R11
├── data-model.md
├── quickstart.md
├── contracts/cli.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
fast/                         # new: C tooling (analysis only, never imported by the model)
├── Makefile                  # builds into fast/build/ (git-ignored by the existing build/ rule)
├── lut_table.h               # GENERATED by scripts/gen_c_lut.py from phycoweb/lut.py
├── phyco_stream.c            # phyco-v2, lut-v1, os → u32 words (R4)
├── testu01_driver.c          # stdin words → TestU01 battery + p-value JSONL (R7)
└── build_tools.sh            # documented PractRand / TestU01 build commands (run outside repo)

protocol/
├── battery_seedsets.py       # new: phycoweb-003 held-out sets (R10)
├── batteries.py              # new: PractRand/TestU01 parsers, rules 1–3, verdict (R8)
└── battery_freeze.py         # new: freeze create/validate for battery attempts

scripts/
├── calibrate.py              # US1 runner (reuses scripts/evalcore.py)
├── calibration_report.py     # US1 analysis
├── gen_c_lut.py
├── stream_equiv.py           # US3 equivalence
├── battery_run.py            # one battery run
├── battery_freeze.py
├── battery_attempt.py
└── battery_rescore.py

tests/
├── test_calibration.py       # runner guards, record shape, statistics on synthetic runs
├── test_fast_stream.py       # LUT header check, op ban in phyco-v2 C, golden vectors (WSL; skip otherwise)
├── test_batteries.py         # parsers on rehearsal fixtures, rules 1–3, S, verdict table
├── test_battery_protocol.py  # seed sets, freeze, attempt/run guards (mocked runner)
└── data/batteries/           # small real-output fixtures from the dev rehearsal

reports/003-extended-batteries-calibration/
├── calibration/ (runs/, summary.json, summary.md, phase-report.md)
├── streams/equivalence.json
├── tools/ (practrand.json, testu01.json)
├── dev/ (rehearsal runs, timing, S count, test-log.md)
└── attempt-1/ (freeze.json, started.json, positive/, negative/, candidate/, attempt.json, summary.md, rescore.json, phase-report.md)
```

**Structure Decision**: extend the existing single project. Feature-002 files
(`protocol/seedsets.py`, `protocol/freeze.py`, `scripts/acceptance.py`, `sp80022/`) are reused
read-only or not at all, so no frozen feature-002 hash changes.

## Phases and gates (for /speckit-tasks)

1. **Setup**: directories, `.gitignore` check, generated LUT header.
2. **US1 calibration** (can start at once; ~17 h background run) → calibration phase report →
   ⛔ **calibration result review**.
3. **US3 fast streams** (in parallel with the calibration run): C stream, equivalence on dev.
4. **Tools**: ⛔ **download permission** per archive → build outside repo → tool records.
5. **Dev rehearsal**: one seed, all batteries, timings, S, parser fixtures, protocol code and tests.
6. **Freeze**: ⛔ **battery freeze approval** (requires the calibration review).
7. **Attempt 1** → re-score → phase report → ⛔ **result review**; attempt 2 only if INCONCLUSIVE or INVALID.
8. **Polish**: README §5 update, claims check (SC-007), final report → ⛔ **final review**.

## Risks

- **PractRand tail accuracy**: some PractRand p-values are approximate in the far tails. A
  positive-control failure from that makes the attempt INCONCLUSIVE; the rule cannot be loosened.
  The rehearsal reports the smallest p-values seen on `os` data.
- **TestU01 build with gcc 15**: may need old-standard flags (R7); recorded, not a rule change.
- **Run time** above 5 days per attempt: reported at the rehearsal for an owner decision before
  the freeze; scale can only stay the same or grow (FR-015).
- **CPU contention**: calibration (US1) and the rehearsal both use all cores; they run one after
  the other.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| C tooling and external tools beyond the Python/numpy stack (Technical Constraints) | ≈ 2.4 × 10¹³ words per generator per attempt; PractRand and TestU01 are C/C++ | Python models run at ~10⁵ words/s (years per attempt) |
| C `lut-v1` contains a multiplication (Principle I) | Exact reproduction of the recorded feature-001 negative control | Any multiplierless rewrite would not be `lut-v1` and would invalidate the control |
