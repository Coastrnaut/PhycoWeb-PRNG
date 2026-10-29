# Acceptance Attempt 1: PASS

Date: 2026-10-28. Seed set `heldout-1`; freeze `attempt-1/freeze.json` (SHA-256 `fb1be3dba203d154d9af8a1f3b4a467ddefe5988fafac6b10d989c16a4d45a01`).

| Role | Source | Verdict | Families failed |
|------|--------|---------|-----------------|
| positive | os-csprng | pass | none |
| negative | lut-v1 | fail | frequency, block_frequency, runs, longest_run, dft, non_overlapping_template, overlapping_template, universal, serial, approximate_entropy, cumulative_sums |
| candidate | phyco-v2 | pass | none |

**Overall verdict (spec rule): PASS**

## Limitations

- Passing SP 800-22 shows only that these tests detected no statistical defect; it is not evidence of cryptographic security.
- Positive-control bytes are stored only locally (data/controls/, owner decision Q1); only this machine can re-score them.
- Only the NIST SP 800-22 battery is run; broader batteries (PractRand, TestU01, Dieharder) are not.

## Disclaimer

Passing NIST SP 800-22 does not show cryptographic security. This generator must not be used to generate secrets; use an established cryptographic random-number generator for keys, nonces, tokens and salts.
