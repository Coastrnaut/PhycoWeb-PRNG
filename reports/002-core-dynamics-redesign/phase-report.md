# Final Phase Report: Feature 002, Core Dynamics Redesign

Date: 2026-10-28. Format: constitution, Phase Completion Reporting. Gate: **T061, owner final
result review (Principle VIII)**.

> Passing NIST SP 800-22 does not show cryptographic security. `phyco-v2` must not be used to
> generate secrets.

## 1. Outcome

- **The goal is met under the pre-registered protocol.** Acceptance attempt 1 (`heldout-1`) gave
  an overall verdict of **PASS**:
  - the positive control (OS CSPRNG) passed;
  - the negative control (lut-v1) failed 11 of 15 families;
  - the candidate `phyco-v2` (design.md 1.0) passed 15/15 families.
- The re-score was identical on Windows, and within 1e-15 in WSL.
- One attempt was used; `heldout-2` and `heldout-3` remain unused.

## 2. Files created or modified (whole feature)

- **Harness** (Phase 3; report: [harness/phase-report.md](./harness/phase-report.md)):
  - `sp80022/` (1.0.0);
  - `tests/test_sp80022.py`, `tests/test_assess.py`, `tests/expansions.py`,
    `tests/data/expansions/`;
  - `scripts/sts_eval.py`, `scripts/evalcore.py`, `scripts/repro_nistrng_defects.py`,
    `scripts/sts_oracle_compare.py`;
  - `harness-changelog.md` and `harness/*`.
- **Protocol**:
  - `protocol/seedsets.py`, `protocol/disclaimer.py`, `protocol/freeze.py`;
  - `scripts/seedsets.py`, `scripts/freeze.py`, `scripts/acceptance.py`,
    `scripts/rescore_attempt.py`;
  - `tests/test_protocol.py` (seed sets, explore guard, freeze, acceptance guard, re-score).
- **Design exploration**:
  - `research/002/explore.py`, `research/002/variants/v001–v005.py` (never edited after
    logging);
  - `research/002/runs.jsonl` (12 runs).
- **Model**:
  - `phycoweb/model_v2.py`, `specs/002-core-dynamics-redesign/design.md` 1.0;
  - `scripts/gen_vectors.py` (adds `phyco-v2`), `scripts/disruption_rate.py`;
  - `vectors/phyco-v2_seed-*_10000.hex` (2 files);
  - tests `test_purity_v2`, `test_widths_v2`, `test_design_trace` (with `tests/v2_reference.py`),
    `test_vectors_v2`, `test_disruption_v2`.
- **Evidence**:
  - `dev/` (test-log, disruption, dev-final, dev-lut-v1);
  - `attempt-1/` (freeze, started, the three eval records, attempt, summary, rescore,
    phase-report);
  - `feature001-rescore/` (4 records).
- **Documents**:
  - `spec.md` (Amendment 1, the approval rows), `plan.md` (Complexity Tracking exceptions),
    `research.md` (R1–R11), `tasks.md`;
  - `README.md` (renamed from `readmee.md`; §5 updated);
  - `reports/001-integer-lut-perturbation/summary.md` (erratum and re-score table; the approved
    text is unchanged).
- Not in the repository: `data/controls/*.bin` (git-ignored, owner decision Q1), and NIST STS
  2.1.2 in WSL `~/nist-sts/`.

## 3. Requirements → evidence

| ID | Evidence | Status |
|----|----------|--------|
| FR-001, SC-001 | `test_purity_v2` (AST: no `*`, `/`, `//`, `%`, `**`, floats or non-literal shifts); design.md §6 | Met |
| FR-002 | design.md §2 width table; `test_widths_v2` (5,002 states) | Met |
| FR-003 | `model_v2` imports the lut-v1 table and constants unchanged; `lut.py` hash in the freeze | Met |
| FR-004 | design.md §1, §4 (nodes, veins, pressure-difference flux, growth/decay, threshold disruption); `test_design_trace` | Met |
| FR-005, SC-002 | `dev/disruption.json`: 13.49–13.83% on 100/100 dev seeds and 13.56–13.58% on both feature-001 seeds | Met |
| FR-006 | design.md §5. The output is computed from state only | Met |
| FR-007 | No hash, cipher or standard PRNG; allowed imports only. Argument in design.md §8, owner judgment at the design review | Met (owner judgment) |
| FR-008 | Bit-exact model, deterministic on 2 platforms; 2 golden files × 10,000 words; design.md §2–6 as the RTL description | Met (RTL itself pending) |
| FR-009 | design.md §3; `test_vectors_v2` seed-domain tests | Met |
| FR-010 | `sp80022` 1.0.0: 15 tests at 2²¹ bits, MSB-first, a copy per test. Validated in R3 and against STS | Met |
| FR-011 | 148 templates (`TestTemplates`) | Met |
| FR-012 | Per-sub-test p-values in every eval record (1/1/1/1/1/1/148/1/1/1/2/1/2/8/18) | Met |
| FR-013, SC-004 | `harness/reproducibility.md`; `attempt-1/rescore.json` identical; T059 cross-platform within 1e-12 | Met |
| FR-014, SC-005 | `harness-changelog.md` entries 1–2, categorized, with the FR-014 statement | Met |
| FR-015, SC-006 | Exploration used dev and feature-001 seeds only (`runs.jsonl`). The explore guard is tested. Held-out seeds were first used at 22:26:57, after the freeze approval | Met |
| FR-016 | `attempt-1/freeze.json` (hashes, versions, owner approval). `acceptance.py` checks the hashes | Met |
| FR-017 | Order positive → negative → candidate; a positive-control failure halts the candidate (tested); `heldout-1` used once | Met |
| FR-018 | Attempt 1 of at most 3, reported with all results; the guards are tested | Met |
| FR-019, SC-007 | The disclaimer is verbatim in every `summary.md` and `phase-report.md`, and in every eval and attempt record. See the claims grep below | Met |
| SC-003 | `attempt-1/attempt.json`: overall **PASS** | Met |

**SC-007 claims check (T058)**: `grep -rniE "cryptographically secure|crypto-grade|suitable for
secrets|\bsecure\b"` over `reports/002-core-dynamics-redesign/**/*.md|json` and `design.md`
finds **no match**. All 3 `summary.md` and `phase-report.md` files contain `DISCLAIMER`
verbatim. The two phase reports that only paraphrased it had the verbatim text appended in T058.
This report contains it too (§8).

## 4. Tests run (this phase, recorded in `dev/test-log.md`)

- Full suite: `python -W ignore -m unittest discover -s tests -t .` gives **116 OK, 3 skipped**
  on Windows and in WSL.
- Quickstart end to end (T059), on both platforms: H1, H2, H3, H5, D1, D2, D3, M1, M2, M3 and A4
  all agree with the recorded evidence.
  - Windows is exact.
  - WSL agrees within 3.1e-13, with identical verdicts.
- One fresh Windows positive control (H2) failed one family by chance (see O3).
- Attempt 1: `acceptance.py --attempt 1` gave PASS; `rescore_attempt.py --attempt 1` was
  identical.

## 5. Attempts

| Attempt | Set | Design | Positive | Negative | Candidate | Overall |
|---------|-----|--------|----------|----------|-----------|---------|
| 1 | heldout-1 | design.md 1.0 (`model_v2.py` 1260142d…) | pass | fail (11/15) | pass (15/15; NOT 5/148 sub-tests failed, k_max 7) | **PASS** |

## 6. Open issues and unresolved assumptions

- **O1 RTL-pending exceptions** (plan.md Complexity Tracking, accepted at the design review):
  - a fixed 4-node ring (no 2×2 to 16×16 parameterization);
  - about 7 serial 32-bit carry chains per step (the 200 MHz target is at risk);
  - the food source and output tap.
- **O2 FR-007 is a judgment.** The update uses generic add-rotate-XOR operations. The
  peristaltic rotation is essential: without it, the faithful dissipative model fails all 15
  families (variant v001).
- **O3 Positive-control false-failure rate.** Over 5 positive-control runs of 100 sequences, 2
  failed one family:
  - cal-3: Linear Complexity;
  - the T059 Windows run: Random Excursions Variant, with 3 of 18 sub-tests failing together.
  - That is consistent with chance (P(≥2 of 5 at about 19%) ≈ 0.25).
  - However, k_max assumes independent sub-tests. The RE and REV sub-tests share one random
    walk, so they fail together, and the real per-run false-failure rate is probably above 19%.
  - Under the protocol, a failed positive control makes an attempt INCONCLUSIVE and still uses
    the held-out set.
  - This affects only future attempts. It cannot be fixed by loosening k_max (FR-014); a
    stricter or better-calibrated rule would need a spec amendment.
- **O4 Feature-001 `wrap32(abs(Q))` no-op.** In lut-v1 stage 6, `Q` is already `wrap32(·) >> 8`,
  so `|Q| < 2²³`, and the second `wrap32` never changes a value. It is kept as recorded
  behaviour of lut-v1, which is not modified. phyco-v2 has no such construct.
- **O5 design.md status line.** It still reads "awaiting owner design review"; the approval is
  in spec.md. Correcting the line would change the frozen design hash, so it is left as is.
- **O6 Selection on dev seeds.** 5 variants and 12 runs were tried. The held-out PASS is the
  unbiased result, but it is a single attempt.
- **README.md §5** has been checked and updated to match this evidence.

## 7. Security concerns and known limitations

- No cryptographic analysis or review exists. There is no keying. The state is 272 bits, and
  the step function is invertible-looking ARX, with no claim made about it.
- Only NIST SP 800-22 was run. The broader batteries recommended by Principle IV (PractRand,
  TestU01, Dieharder) were not.
- The positive-control bytes are local only (Q1). Others can re-run the controls but cannot
  re-score these exact bytes.
- The OS CSPRNG is used only as the positive control, never in the generator.

## 8. Recommendation

**Proceed**: accept feature 002 as complete at the owner's final review (T061), with O1–O6
recorded. Suggested follow-ups, each a separate feature:
- run broader batteries (PractRand, TestU01) on phyco-v2;
- calibrate the positive-control false-failure rate (O3) before any further attempt;
- RTL and synthesis (O1).

## Disclaimer

Passing NIST SP 800-22 does not show cryptographic security. This generator must not be used to generate secrets; use an established cryptographic random-number generator for keys, nonces, tokens and salts.
