# Battery Attempt 1 (heldout-1)

**Verdict: PASS** (candidate did not fail).

S (frozen) = 101210; equivalence: all match.

| Role | Generator | Status | Runs failing | Incomplete | p-values | Threshold |
|------|-----------|--------|--------------|------------|----------|-----------|
| positive | os | run | 0 | 0 | 101210 | 4.940e-08 |
| negative | lut-v1 | run | 70 | 0 | 10242 | 4.940e-08 |
| candidate | phyco-v2 | run | 0 | 0 | 101210 | 4.940e-08 |

## Disclaimer

Passing NIST SP 800-22 does not show cryptographic security. This generator must not be used to generate secrets; use an established cryptographic random-number generator for keys, nonces, tokens and salts.
