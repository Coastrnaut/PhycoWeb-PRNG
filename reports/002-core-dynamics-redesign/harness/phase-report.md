# Phase Report: Phase 3 (US3), Evaluation Harness `sp80022` 1.0.0

Date: 2026-10-28. Feature `002-core-dynamics-redesign`. Format: constitution, Phase Completion
Reporting. Gate: **T030, owner review (Principle VIII)**. Phase 4 must not start before it.

Harness `sp80022` 1.0.0, source SHA-256
`1563526ed25f695dba223c3d62c8ce900ba4f485dd62f09a694ece0602c41700`.

> This phase validates a **statistical test harness**. Passing NIST SP 800-22 is not evidence
> of cryptographic security, and nothing in this report claims it.

## 1. Files created or modified

Harness package: `sp80022/__init__.py`, `special.py`, `tests_basic.py`, `tests_template.py`,
`tests_complex.py`, `tests_walk.py`, `assess.py`, `tests.py`.

Protocol and tools: `protocol/__init__.py`, `protocol/seedsets.py`, `protocol/disclaimer.py`,
`scripts/seedsets.py`, `scripts/evalcore.py`, `scripts/sts_eval.py`,
`scripts/repro_nistrng_defects.py`, `scripts/sts_oracle_compare.py`.

Tests: `tests/test_protocol.py`, `tests/test_assess.py`, `tests/test_sp80022.py`,
`tests/expansions.py`, `tests/data/expansions/{pi,e,sqrt2,sqrt3}_1000000.bin`.

Evidence (`reports/002-core-dynamics-redesign/`): `harness-changelog.md` (entries 1 and 2),
`harness/nistrng-defects.json`, `harness/timing.json`, `harness/cal-1.json`, `cal-2.json`,
`cal-3.json`, `cal-1-rescore.json`, `cal-1-rescore-wsl.json`, `cal-1-rescore-1.0.0.json`,
`harness/reproducibility.md`, `harness/sts-2.1.2.md`, `harness/oracle-compare.json`,
`harness/oracle-compare.md`, and this report.

Spec documents: `research.md` (R1 N9, new R11), `tasks.md` (T001–T029 marked), `spec.md`
(pending "Harness review" row). Feature-001 erratum: `reports/001-integer-lut-perturbation/summary.md`.

Local only, not in the repository: `data/controls/cal-{1,2,3}.bin` (git-ignored, owner
decision Q1), and the NIST STS 2.1.2 build in WSL `~/nist-sts/`.

## 2. Requirements addressed

- **FR-010**: all 15 SP 800-22 tests, R2 parameters.
- **FR-011**: all 148 Non-Overlapping templates; OTM eligible at 2²¹ bits.
- **FR-012**: p-value counts and eligibility.
- **FR-013, SC-004**: reproducibility.
- **FR-014, SC-005**: change log.
- **SC-003**: verdict rules (spec Pre-registered Protocol, including Amendment 1).
- **Principle IV**: the harness is shown to be able to fail (T014).

## 3. Tests run and results

All of these were run in this phase. Their output is recorded in the files named.

| Check | Command | Result |
|-------|---------|--------|
| Unit tests (worked examples, Appendix B, templates, contract, known-bad, assess, protocol) | `python -W ignore -m unittest discover -s tests -t .` | **80 OK, 3 skipped**: the §2.6.8 DFT example, whose stated N₁ is inconsistent with its input, and the two G-SHA-1 examples, §2.7.8 and §2.9.8 (R11) |
| nistrng defects N4–N9 | `python -W ignore scripts/repro_nistrng_defects.py` | all 6 reproduced → `nistrng-defects.json` |
| Throughput (T023) | see `timing.json` | 1.44 s per 2²¹-bit sequence; 60 s for 100 sequences on 32 workers |
| Positive-control calibration (T024) | `scripts/sts_eval.py --source os-csprng --sequences 100 …` ×3 | cal-1 15/15, cal-2 15/15, cal-3 14/15 (one LC proportion failure, shown to be chance by a 2,000-sequence diagnostic). Pooled over 300 sequences: 0/188 sub-tests fail uniformity |
| Reproducibility (T025) | see `reproducibility.md` | same environment identical; Windows vs WSL p-values within 3.1e-13; 1.0.0 re-score identical to 0.1.0 |
| Independent oracle (T028) | `scripts/sts_oracle_compare.py` (WSL) | **0 mismatches** vs NIST STS 2.1.2 on π, e, √2, √3, SHA-1 and 10 cal-1 sequences; largest difference 5.0e-7 |

Appendix B: 56 of 64 published values match directly. The other 8 (OTM and LC for the four
expansions) match when recomputed from our counts with the constants NIST used (R11).

## 4. Open issues and unresolved assumptions (owner decisions at T030)

1. **OTM reference π (R11)**: the harness uses the Rev. 1a π from the document text. NIST STS
   2.1.2 and the published example values use the older Poisson π. Under STS's π, truly random
   2²¹-bit data fails OTM (p < 0.01) on 1.23% of sequences instead of 1.00%. Over 4 × 10⁶
   urandom blocks, the old π is rejected at p ≈ 1e-70; Rev. 1a fits (p = 0.74).
   - **Recommendation**: keep Rev. 1a.
   - Choosing STS's constants instead would not loosen anything, but it would add a known
     calibration error. **Owner to confirm.**
2. **LC π₀ = 0.010417 vs STS 0.01047**: negligible effect (λ ≈ 0.001). Keep the document value.
3. **Document inconsistencies** in §2.6.8 and §2.14.8. Our values agree with Appendix B and
   with STS. No action needed.
4. **3 skipped worked examples**:
   - §2.7.8 and §2.9.8 need G-SHA-1 generator output. Appendix B example 3 (the SHA-1 data) is
     covered by the STS comparison instead.
   - §2.6.8 is skipped because of the inconsistency in item 3. DFT is still covered by
     Appendix B (4/4) and by STS.
5. **Control bytes are local only** (Q1). A third party can re-run the controls but cannot
   re-score these exact bytes unless the owner shares them. Their SHA-256 values are recorded.
6. **About 25% of 2²¹-bit sequences are ineligible for Random Excursions**, as expected
   (P(J < 500) ≈ 0.27). With 100 sequences, m′ is about 75, above the m′ ≥ 55 uniformity
   minimum. The k_max values for those families are recomputed for the actual m′.
7. **phyco-v2 does not exist yet**. `sts_eval.py --source phyco-v2` exits 2 until Phase 4.

## 5. Security concerns

- No secrets are handled. Held-out seed sets cannot be loaded by the dev tools: they exit 2
  (`protocol.seedsets.load(allow={"dev"})`, tested in `tests/test_protocol.py`).
- The STS archive was downloaded from csrc.nist.gov (owner-approved), hashed, and built outside
  the repository. Only `make` and the resulting `assess` were run.
- A statistical pass does not imply cryptographic security. Every evaluation record carries the
  `DISCLAIMER` text.

## 6. Recommendation

**Proceed**, subject to owner approval at T030. Approving means:

- the harness `sp80022` 1.0.0 (hash above) is frozen, and any later change needs a change-log
  entry under FR-014;
- decisions 4.1 and 4.2 (the Rev. 1a constants) are accepted;
- Phase 4 (design exploration, T031 onward) may start.

## Disclaimer

Passing NIST SP 800-22 does not show cryptographic security. This generator must not be used to generate secrets; use an established cryptographic random-number generator for keys, nonces, tokens and salts.
