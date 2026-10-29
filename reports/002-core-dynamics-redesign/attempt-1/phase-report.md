# Phase Report: Acceptance Attempt 1 (T054)

Date: 2026-10-28. Feature `002-core-dynamics-redesign`. Format: constitution, Phase Completion
Reporting. Gate: **T055, owner result review (Principle VIII)**.

> Passing NIST SP 800-22 does not show cryptographic security. `phyco-v2` must not be used to
> generate secrets.

## Verdict: **PASS** (spec overall-verdict rule)

| Role | Source | Seeds | Verdict | Detail |
|------|--------|-------|---------|--------|
| Positive control | OS CSPRNG, 100 × 2²¹ bits (`data/controls/attempt-1.bin`, SHA-256 `6e188a195dae96bb…`, local only) | — | pass | 15/15 families. Non-Overlapping Template: 3 of 148 sub-tests failed (k_max 7) |
| Negative control | lut-v1 | heldout-1 ×100 | **fail** | 11 of 15 families fail, as expected |
| Candidate | phyco-v2 (design.md 1.0) | heldout-1 ×100 | **pass** | 15/15 families. Non-Overlapping Template: 5 of 148 sub-tests failed proportion (96/100 each, 97 needed), within k_max 7. Their uniformity was fine (P-valueᴛ 0.029–0.88) |

More detail on the candidate:
- The lowest uniformity P-valueᴛ across all 188 sub-tests is 0.0024. The threshold is 0.0001.
- Random Excursions: m′ = 64 eligible sequences (positive control 77), above the minimum of 55.
- Single-sub-test families failed: 0.

## Protocol and provenance

- Freeze `attempt-1/freeze.json` (SHA-256 `fb1be3db…a01`):
  - model `phycoweb/model_v2.py` `1260142d…`, `lut.py` `387a99ed…`;
  - design.md 1.0 `a1109bf1…`;
  - harness `sp80022` 1.0.0 `1563526e…`;
  - written at git `5dd9308` with a clean frozen tree.
  - The owner approved it in session; the agent recorded the approval fields. Spec row "Design
    freeze 1".
- Run order positive → negative → candidate, 22:26:57–22:29:58 (`attempt.json`).
  `acceptance.py` checked every frozen hash before generating anything.
- The owner committed report files while the attempt was running, so the candidate record shows
  git `6fcf046` and the controls show `5dd9308`. Those commits only added files under
  `attempt-1/`. No frozen file changed, and the freeze still validates against the files on disk
  after the run.
- `heldout-1` is now **used**. It is never reused (FR-018).

## Tests run in this phase

| Command | Result |
|---------|--------|
| `python scripts/freeze.py --attempt 1 --dev-evidence reports/002-core-dynamics-redesign/dev/dev-final.json` | draft written, exit 0 |
| `python -W ignore scripts/acceptance.py --attempt 1 --workers 32` | **PASS**, exit 0 |
| `python -W ignore scripts/rescore_attempt.py --attempt 1 --workers 32` | positive, negative and candidate **identical**, exit 0 (`rescore.json`) |
| Full suite before the freeze (T043, and after T050) | 116 tests OK, 3 skipped |

## Requirements addressed

- FR-016: freeze before the attempt.
- FR-017, FR-018: controls, run order, single use of the held-out set.
- SC-003: pre-registered verdict.
- SC-004: identical re-score.
- SC-006: held-out seeds were used only after the freeze approval.

## Open issues and limitations

- **What PASS means**: only that the SP 800-22 battery, under the pre-registered rules, detected
  no defect in 100 held-out sequences of 2²¹ bits. Broader batteries (PractRand, TestU01,
  Dieharder) were not run. Nothing here says anything about unpredictability or cryptographic
  strength.
- **Selection on dev seeds**: 5 variants and 12 runs (design.md §9). The held-out result is the
  unbiased one.
- **Re-scoring**: the positive-control bytes are local only (Q1).
- **RTL-pending exceptions** (plan.md Complexity Tracking): a fixed 2×2 ring, the timing path,
  and the food source/output tap.
- `design.md` still shows its pre-review status line. The approval is recorded in spec.md;
  correcting the line would change the frozen hash.

## Security concerns

None new. The OS CSPRNG is used only as the positive control. The disclaimer is in
`summary.md`, `attempt.json` and every evaluation record.

## Recommendation

**Proceed** to Phase 6 (T057–T061) after the owner's result review (T055).

## Disclaimer

Passing NIST SP 800-22 does not show cryptographic security. This generator must not be used to generate secrets; use an established cryptographic random-number generator for keys, nonces, tokens and salts.
