# sp80022 vs NIST STS 2.1.2 (T028; FR-010, FR-014, SC-005, research R3d)

Date: 2026-10-28. Harness `sp80022` 1.0.0, source SHA-256
`1563526ed25f695dba223c3d62c8ce900ba4f485dd62f09a694ece0602c41700`. Oracle build:
[sts-2.1.2.md](./sts-2.1.2.md). Full data: [oracle-compare.json](./oracle-compare.json).

Command (WSL, Ubuntu, Python 3.14.4, numpy 2.5.4):
`~/.venvs/phycoweb/bin/python -W ignore scripts/sts_oracle_compare.py` (exit 0).

## Inputs

| Input | Bits | Sequences | Note |
|-------|------|-----------|------|
| π, e, √2, √3 | 10⁶ | 1 each | Our exact expansions (`tests/expansions.py`). Each is bit-identical to the STS `data/data.*` file |
| SHA-1 | 10⁶ | 1 | STS `data/data.sha1` (packed binary), Appendix B example 3 |
| `cal-1` | 2²¹ | first 10 | Positive-control bytes from `data/controls/cal-1.bin` |

STS gets every input as a binary file with its default parameters, which equal research R2.

## Rule

STS prints 6 decimals, so each p-value must agree within ±1e-6. Overlapping Template and Linear
Complexity are compared after recomputing our χ² from **our** counts with **STS's** constants
(research R11). This way the counts must match exactly, while the harness keeps the Rev. 1a
constants. For sequences that are ineligible for Random Excursions, STS writes zeros; the
script checks for those zeros. It also checks that each results file holds a whole number of
values per sequence, so the slices can't be misaligned.

## Result

- **0 mismatches** over 6 inputs × 15 tests: 15 sequences, 188 p-values each, 2,820 p-values in
  all, minus the zeros for ineligible excursion sequences, which are checked separately.
- Largest difference: **5.0e-7**, which is the size of STS's 6-decimal rounding.
- Random Excursions eligibility agrees on all 15 sequences. `data.sha1` and `cal-1` sequences
  3, 4 and 10 are ineligible (J < 500); the others are eligible.

| Input | Largest \|Δp\| | Mismatching tests |
|-------|---------------|-------------------|
| π | 4.8e-7 | none |
| e | 5.0e-7 | none |
| √2 | 5.0e-7 | none |
| √3 | 5.0e-7 | none |
| SHA-1 | 5.0e-7 | none |
| cal-1 (10 sequences) | 5.0e-7 | none |

**Conclusion**: on every test, `sp80022` computes the same statistic as NIST's reference
implementation. The only differences are the two reference constants recorded in research R11,
which the harness deliberately does not copy from STS.
