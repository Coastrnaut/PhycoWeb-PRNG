# Harness Reproducibility (T025; FR-013, SC-004, research R7)

Date: 2026-10-28. Harness `sp80022` 0.1.0. The first three runs below have the same `harness_sha256` (0.1.0). The fourth uses 1.0.0.

| Run | Command | Environment | Result |
|-----|---------|-------------|--------|
| Original | `python -W ignore scripts/sts_eval.py --source os-csprng --sequences 100 --save-bytes data/controls/cal-1.bin --out reports/002-core-dynamics-redesign/harness/cal-1.json` | Windows 11, Python 3.10.11, numpy 2.2.6, scipy 1.15.3 | 15/15 families pass |
| Same-environment re-score | `python -W ignore scripts/sts_eval.py --source file --bytes data/controls/cal-1.bin --out reports/002-core-dynamics-redesign/harness/cal-1-rescore.json` | same | `sequences`, `subtests`, `families`, `verdict`, `parameters` and `bytes_sha256` are **identical** |
| Cross-environment re-score | `~/.venvs/phycoweb/bin/python -W ignore scripts/sts_eval.py --source file --bytes data/controls/cal-1.bin --workers 16 --out reports/002-core-dynamics-redesign/harness/cal-1-rescore-wsl.json` | Ubuntu (WSL2), Python 3.14.4, numpy 2.5.4, scipy 1.18.1 | All verdicts and eligibility equal; largest p-value difference **3.1e-13**, within the 1e-9 tolerance (R7) |
| Re-score on 1.0.0 (T029) | `python -W ignore scripts/sts_eval.py --source file --bytes data/controls/cal-1.bin --out reports/002-core-dynamics-redesign/harness/cal-1-rescore-1.0.0.json` | Windows, as Original; harness 1.0.0, `harness_sha256` 1563526e… | `sequences`, `subtests`, `families`, `verdict`, `parameters` and `bytes_sha256` are **identical** to `cal-1.json` |

`data/controls/cal-1.bin` has SHA-256 `58ad375ebdd0afb1a8896d92f17e50d2bfcfe26ed412d3a41a4a521a38c00638` (recorded in `cal-1.json`). It is stored locally only (owner decision Q1).

**Conclusion**: FR-013 holds in one environment (bit-identical). Across environments, verdicts are exact and p-values agree to 3e-13. The tiny differences come from floating-point library differences, as R7 expected.
