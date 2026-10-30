# T026: PractRand listing threshold (research R6)

Date 2026-10-29. PractRand 0.96, `~/practrand/RNG_test` (SHA-256 `7ae4a26b…de874f`).

**Question.** By default RNG_test lists only results with anomalies (`-e 0.1`, "intelligent"
thresholds). Rule 1 needs every p-value, or at least every p-value that could reach
0.005 / S (about 5 × 10⁻⁸ for the expected S).

**Finding.** `RNG_test --help` documents `-a`: "no threshold - display all test results". The
0.96 build supports it; a 2²⁸-byte run on OS data with `-a` printed 937 results at the 2²⁷ and
2²⁸ checkpoints, each with a p-value (`tests/data/batteries/pr-os/log.txt`).

**Decision.** Every PractRand run uses `-a` (research R6's stricter branch), so S is the exact
count of printed p-values and rule 1 sees all of them. No result is unlisted, so the question of
the listing threshold no longer arises.

**Two other defaults found and fixed before any held-out use** (both make the protocol stricter
or deterministic, FR-015):

| Default | Problem | Setting used |
|---------|---------|--------------|
| `-tlfail` | Halts the run after a checkpoint that contains a failure | `-tlmaxonly` for the positive control and candidate; `-tlfail` only for the negative control (spec Edge Cases) |
| `-tlmin 1.5s` | First checkpoint depends on machine speed, so S would too | `-tlmin 27` (2²⁷ bytes) |

**Printed precision** (from `tools/RNG_test.cpp`): p-values with |p − 0.5| > 0.49 are printed
as `Ne-D` or `1-Ne-D` with the mantissa rounded down, so a printed tail value is never larger
than the true one; rule 1 on printed values can only flag more, never fewer, results. Results of
pass/fail type print `"pass"` / `"fail"`; a `"fail"` counts under rule 2.

Full command (positive, candidate):
`RNG_test stdin32 -tf 2 -te 0 -a -tlmin 27 -tlmax 40 -tlmaxonly -multithreaded`
