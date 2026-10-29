# NIST STS 2.1.2 Oracle Build (T027; FR-010, SC-004, research R3d)

Date: 2026-10-28. Owner approval: plan Owner Decisions Q2. Build tools installed by the owner
(T026). Nothing from the archive was run except `make` and the `assess` binary it built.

## Download

| Item | Value |
|------|-------|
| URL | https://csrc.nist.gov/CSRC/media/Projects/Random-Bit-Generation/documents/sts-2_1_2.zip |
| Local path (WSL, outside the repository) | `~/nist-sts/sts-2_1_2.zip` |
| Size | 43,915,127 bytes |
| SHA-256 | `0238d2f1d26e120e3cc748ed2d4c674cdc636de37fc4027c76cc2a394fff9157` |
| Unpacked to | `~/nist-sts/sts-2.1.2/sts-2.1.2/` |

## Build

- Environment: Ubuntu (WSL2), gcc 15.2.0 (Ubuntu 15.2.0-16ubuntu1), GNU Make 4.4.1.
- Command: `make` in the unpacked directory, using the shipped `makefile` without changes.
- Result: `assess` built (133,496 bytes, SHA-256
  `d839cfd14b75444e7c75c53f03a7abbb1b4ae374493ba1da9cbae6dcd5682d41`).
- Log summary: no errors. Only `-Wall` warnings appeared: a misleading-indentation note in
  `src/matrix.c:78`, and unused variables in `src/generators.c:48` (`counter`) and
  `src/genutils.c:175` (`LA`). None of these is in a test's p-value path; `generators.c` and
  `genutils.c` hold STS's built-in generators, which are not used here.

## Use

`scripts/sts_oracle_compare.py` drives `./assess <n>` through scripted stdin:
`0` (input file), the file path, `1` (all tests), `0` (no parameter changes), the number of
bitstreams, then `1` (binary). The default parameters equal research R2 (block frequency 128,
NOT 9, OTM 9, ApEn 10, serial 16, LC 500). Per-sequence p-values are read from
`experiments/AlgorithmTesting/<Test>/results.txt`.

A trial run on the shipped ASCII `data/data.e` (n = 10⁶) reproduced the SP 800-22 Appendix B
values for e (for example Frequency 0.953749, Linear Complexity 0.826335, Overlapping Template
0.110434).

## Reference constants used by STS (see research R11)

- `src/overlappingTemplateMatchings.c` declares the Rev. 1a π values on line 22, but lines 41–44
  overwrite them with the older `Pr(u, η)` formula (π₀ = 0.367879 …). STS therefore uses the old
  constants.
- `src/linearComplexity.c:13` uses π₀ = 0.01047 (the seven values sum to 1.000053).
