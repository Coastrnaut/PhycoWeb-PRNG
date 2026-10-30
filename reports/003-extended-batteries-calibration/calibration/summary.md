# Calibration Summary: SP 800-22 Positive Control (feature 003, US1)

1000 runs × 100 sequences × 2²¹ bits of os.urandom data, harness `sp80022` 1.0.0, feature-002 rules. SHA-256 of `runs/SHA256SUMS`: `8708246efc94e99a81e2db2284cb1eac68c71b476838a9569bfa9fbd42cd4f62`.

- **Overall false-failure rate**: 207/1000 = 0.2070 (95% CI 0.1823–0.2335); assumed 0.19; consistent.
- **Implied PASS probability** (perfect candidate and control): 0.6288 (95% CI 0.5876–0.6687).

| Family | Failures | Rate | 95% CI | Expected | Consistent |
|--------|----------|------|--------|----------|------------|
| frequency | 16 | 0.0160 | 0.0092–0.0259 | 0.0185 | yes |
| block_frequency | 15 | 0.0150 | 0.0084–0.0246 | 0.0185 | yes |
| runs | 21 | 0.0210 | 0.0130–0.0319 | 0.0185 | yes |
| longest_run | 13 | 0.0130 | 0.0069–0.0221 | 0.0185 | yes |
| rank | 16 | 0.0160 | 0.0092–0.0259 | 0.0185 | yes |
| dft | 32 | 0.0320 | 0.0220–0.0449 | 0.0185 | **no** |
| non_overlapping_template | 12 | 0.0120 | 0.0062–0.0209 | 0.0065 | yes |
| overlapping_template | 20 | 0.0200 | 0.0123–0.0307 | 0.0185 | yes |
| universal | 23 | 0.0230 | 0.0146–0.0343 | 0.0185 | yes |
| linear_complexity | 19 | 0.0190 | 0.0115–0.0295 | 0.0185 | yes |
| serial | 1 | 0.0010 | 0.0000–0.0056 | 0.0003 | yes |
| approximate_entropy | 17 | 0.0170 | 0.0099–0.0271 | 0.0185 | yes |
| cumulative_sums | 5 | 0.0050 | 0.0016–0.0116 | 0.0003 | **no** |
| random_excursions | 0 | 0.0000 | 0.0000–0.0037 | 0.0012 | yes |
| random_excursions_variant | 16 | 0.0160 | 0.0092–0.0259 | 0.0055 | **no** |

Failing families per run: 0: 793, 1: 190, 2: 15, 3: 2

Ten pairs with the smallest Fisher p (co-failure; reported only):

| Pair | Both fail | Expected if independent | Fisher p |
|------|-----------|-------------------------|----------|
| frequency + cumulative_sums | 4 | 0.08 | 2.18e-07 |
| runs + dft | 3 | 0.67 | 2.68e-02 |
| approximate_entropy + cumulative_sums | 1 | 0.09 | 8.23e-02 |
| dft + approximate_entropy | 2 | 0.54 | 1.00e-01 |
| longest_run + non_overlapping_template | 1 | 0.16 | 1.46e-01 |
| block_frequency + non_overlapping_template | 1 | 0.18 | 1.67e-01 |
| block_frequency + longest_run | 1 | 0.19 | 1.79e-01 |
| block_frequency + approximate_entropy | 1 | 0.26 | 2.28e-01 |
| longest_run + overlapping_template | 1 | 0.26 | 2.32e-01 |
| frequency + approximate_entropy | 1 | 0.27 | 2.42e-01 |

## Recommendations

- Family dft: measured 0.0320 vs expected 0.0185 (recommendation only; needs a separate, owner-approved, stricter-only spec amendment (feature 002 FR-014)).
- Family cumulative_sums: measured 0.0050 vs expected 0.0003 (recommendation only; needs a separate, owner-approved, stricter-only spec amendment (feature 002 FR-014)).
- Family random_excursions_variant: measured 0.0160 vs expected 0.0055 (recommendation only; needs a separate, owner-approved, stricter-only spec amendment (feature 002 FR-014)).

## Disclaimer

Passing NIST SP 800-22 does not show cryptographic security. This generator must not be used to generate secrets; use an established cryptographic random-number generator for keys, nonces, tokens and salts.
