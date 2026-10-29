# Quickstart / Validation Guide: Core Dynamics Redesign

Prerequisites: Python 3.10+, numpy, scipy (installed: 2.2.6 / 1.15.3 on Windows; 2.5.4 / 1.18.1
in the WSL venv). nistrng 1.2.3 is only needed for H0. Run from the repository root.
Set `PYTHONIOENCODING=utf-8` on Windows.

Gates are marked 🔒. A step after a gate must not run until the owner has approved that gate.

## H. Harness (before any design work counts)

| Step | Command | Expected |
|------|---------|----------|
| H0 | Reproduce the nistrng defects (research R1): run each nistrng test on 4 urandom sequences of 2²¹ bits | NOT p = 1.0; OTM, RE, LC p ≈ 0; Universal p ≈ 0.998. Recorded as the first changelog entry |
| H1 | `python -m unittest tests.test_sp80022 -v` | All worked examples, the Appendix B values (π, e, √2, √3) and the template counts match (research R3a, R3b, R6) |
| H2 | `python scripts/sts_eval.py --source os-csprng --sequences 100 --save-bytes data/controls/cal-1.bin --out reports/002-core-dynamics-redesign/harness/cal-1.json` (3 runs) | Each run passes, or fails at most one family by chance (about 19% of runs, spec Assumptions). Pooled p-values over all 300 sequences pass uniformity (R3c). The same sub-test failing in 2 or more runs counts as a harness defect and blocks progress (T024) |
| H3 | Re-score `cal-1.bin` with `--source file` | Identical JSON p-values (FR-013, SC-004) |
| H4 | Known-bad inputs (R3e) | Each fails its expected tests |
| H5 | Re-score the 4 feature-001 inputs with `--source file` (erratum already added 2026-10-28, owner-approved) | A re-score table of old and new verdicts for each test, added below the erratum (T057) |

## D. Design exploration (dev seeds only)

| Step | Command | Expected |
|------|---------|----------|
| D1 | `python scripts/seedsets.py --check` | All 4 fingerprints match the spec |
| D2 | `python research/002/explore.py --variant <id> --set dev` | Adds a line to `runs.jsonl`. A held-out set is refused (exit 2) |
| D3 | Disruption rate check on 100 dev seeds × 10⁶ steps | Rate in [1%, 50%] for every seed (SC-002) |
| D4 | Write `design.md` | 🔒 **Design review** (owner) |

## M. Reference model

| Step | Command | Expected |
|------|---------|----------|
| M1 | `python -m unittest discover -s tests -v` | All feature-001 tests still pass. New: purity v2, widths, design-vs-model trace, golden vectors |
| M2 | `python scripts/gen_vectors.py --model phyco-v2 --seed …` for 2 dev seeds | 10,000-word vectors, verified with `--verify` (FR-008) |
| M3 | `python scripts/sts_eval.py --source phyco-v2 --set dev --out …/dev-final.json` | The dev evidence for the freeze. Not an acceptance result |

## A. Acceptance attempt N (N = 1, 2, 3)

| Step | Command | Expected |
|------|---------|----------|
| A1 | `python scripts/freeze.py --attempt N --dev-evidence …/dev-final.json` | Draft `freeze.json` with empty approval fields |
| A2 | 🔒 The owner reviews and fills in `approved_by` and `approved_on` | **Design freeze approval** (FR-016) |
| A3 | `python scripts/acceptance.py --attempt N` | Order: positive, negative, candidate. Writes `attempt.json` and `summary.md`. Verdict PASS / FAIL / INCONCLUSIVE |
| A4 | Re-run the scoring of attempt N from the saved bytes and seeds | Same p-values and verdicts (SC-004) |
| A5 | 🔒 Owner result review | On FAIL or INCONCLUSIVE, either redesign (new design.md version, back to D) or stop. Attempts are never repeated on the same set |

Every report carries the FR-019 disclaimer. Check with `grep -L "must not be used" reports/002-*/**/summary.md`,
which must print nothing.
