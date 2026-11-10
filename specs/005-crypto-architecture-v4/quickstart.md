# Quickstart: Cryptographic Architecture, Second Design Round (phyco-v4)

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v4` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

Validation scenarios for this feature's changes. Feature 004's quickstart (`specs/004-crypto-architecture-v3/quickstart.md` at
99e6994, SHA-256 `ed2ca406e19bc96f0b22e6200b20c054a34c0be9b0e57b8627ada5f25047b2d4`) applies for everything else, run with
`PHYCOWEB_FEATURE=005`. Commands run from the repository root, on Windows with `python` and in WSL with `wpy` (feature 004's
P0). Heavy runs are projected first and run one at a time.

## Before any candidate

**V1. The plan's numbers reproduce.** `python -X utf8 research/005/plan_projections.py --check` prints
"plan-projections.json matches" and exits 0, on both platforms.

**V2. Feature 004 is untouched.** `PHYCOWEB_FEATURE` unset, `python scripts/recheck_004.py` in a fresh clone gives 0
disagreements, as T132's record did, and `python scripts/check_claims.py` gives 0 findings.

**V3. The probes and the table.** Each probe of research R5 runs with `--probe`, writing a `projection` record charged to the
feature-wide row; then `python scripts/projection_table.py` writes `$REP/projection-table.json`, and `--check` exits 0. Every
value in it is at most the plan's (spec SC-001).

**V4. The security target first.** With the row "Security-target review" still pending, `candidate_log.py propose` exits 2;
once the row reads Approved at HEAD with the chapters' SHA-256, it appends the entry (SC-002).

## During the climbs

**V5. A capped search does not end the climb.** On a test operation list whose search at some r is made to reach a tiny cap,
`round_rule.py` writes no further search of that kind at that size and writes `split` records for the larger r, each citing
two parts; the re-check recomputes each sum (SC-003, SC-005).

**V6. 16×16 decides first.** On a test operation list whose first linear search at 16×16 reaches its cap, the candidate is
decided `ineligible` with the cause `no R_bound at 16×16`, and its rows show no hour charged at 8×8 or 4×4 (SC-004).

**V7. Trails recompute.** A test `trail` record with every nonlinear operation recorded re-checks to its weight; changing one
operation's output makes the re-check report a disagreement; a weight at or below 2⁻¹²⁸ classes the trail `none` (SC-005).

## At the end

**V8. The claim test covers phyco-v4.** `python scripts/check_claims.py` scans this feature's documents and reports, finds the
disclaimer naming `phyco-v4` in each, and gives 0 findings (SC-007).

**V9. The selection-bias statement.** The final report's table lists B1, A1, B2 and A2 with their outcomes and every design of
this feature, each with its log entry (SC-006).

**V10. The hours.** The final report gives, for every heavy run, its projected and measured hours and their ratio, and the sum
within the ceiling (SC-008, SC-009).
