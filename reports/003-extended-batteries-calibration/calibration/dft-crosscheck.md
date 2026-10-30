# DFT Cross-Check (feature 003, US1; follow-up requested at T011)

Date: 2026-10-30. Command (WSL): `python -W ignore scripts/dft_crosscheck.py --fresh 1000`,
exit 0. Data: `dft-crosscheck.json`.

**Question.** The dft family failed in 3.2% of calibration runs, against 1.85% expected. Is that
caused by our port of the test, or by the test itself?

**Answer.** It is caused by the test itself.
- Our harness agrees with NIST STS 2.1.2 on every sequence checked.
- The NIST DFT statistic is standardized with a variance that is about 6% too small. As a
  result, it rejects about 1.23% of random sequences at α = 0.01, where it should reject 1%.
- The amount of the excess explains the measured family rate.

## A. Stored calibration p-values (100,000 sequences per test)

| Test | Rejected at p < 0.01 | Rate (95% CI) |
|------|----------------------|---------------|
| dft | 1,230 | **1.23%** (1.16–1.30%) |
| frequency (control) | 959 | 0.96% (0.90–1.02%) |

E[d²] for dft is recovered from p = erfc(|d| / √2). It should be 1 if the statistic is
standardized correctly. Measured: **1.062 (95% CI 1.053–1.071)**. The test divides by the
variance n·0.95·0.05/4; the data imply a denominator of about 3.77. This is consistent with
published analyses of the SP 800-22 DFT test, which give a denominator of about 3.8.

Predicted effect on the family: with a per-sequence rate of 1.23%, P(96 or fewer of 100 pass)
= **3.5% (CI 3.0–4.2%)**. The measured family rate was **3.2% (CI 2.2–4.5%)**, which agrees.

## B. Fresh data compared with the reference implementation

1,000 new `os.urandom` sequences of 2²¹ bits each were run through both `sp80022.tests.dft` and
NIST STS 2.1.2 (menu test 07 only). The bytes were deleted after the run.

| Check | Result |
|-------|--------|
| p-value agreement with STS (tolerance 1e-6) | **0 mismatches**; largest difference 5.0 × 10⁻⁷ (STS prints 6 decimals) |
| Rejected at p < 0.01 | 11 of 1,000 = 1.1% (CI 0.55–1.96%) |
| Mean N1 − N0 | +13.8 (2.75 standard errors) |
| Variance of N1 | 25,216 (CI 23,143–27,582); the test uses 24,904 |

Part B confirms that the port is exact. With only 1,000 sequences it is too small to measure the
variance error itself, and its interval contains both /4 and /3.8. Part A, with 100× as many
sequences, is what measures it. A small mean offset in N1 also adds to E[d²]. Its contribution
from part B is about 0.008, small next to the measured 0.062.

## Consequences

- **There is no harness defect, and nothing changes.** The port agrees with the reference
  implementation, and the excess is the published test's own behaviour.
- The DFT excess adds about 1.3 points to the 20.7% overall false-failure rate.
- Correcting the constant would make dft fail less often. That is a loosening, which feature
  002 FR-014 forbids. This is recorded for information only.

> Passing NIST SP 800-22 does not show cryptographic security. This generator must not be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts.
