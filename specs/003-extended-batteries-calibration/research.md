# Research: Extended Batteries and Positive-Control Calibration

Feature `003-extended-batteries-calibration`. Date: 2026-10-29. Every decision below is fixed
before any calibration or battery result exists. Where a fact about a third-party tool can only
be confirmed once the tool is on disk, the decision says so and states what happens if the fact
turns out differently. No such fallback may loosen the spec's rules (FR-015).

## R1. Where things run

- **Decision**: The calibration (US1) runs on Windows with the feature-002 Python environment
  (Python 3.10.11, numpy 2.2.6, scipy 1.15.3, 32 workers). Fast streams, tool builds and every
  battery run (US2, US3) run in WSL2 Ubuntu (gcc/g++ 15.2.0, GNU Make 4.4.1, 32 logical CPUs on
  an i9-14900K with SHA-NI, 31 GiB RAM, 953 GB free on `/`), with the existing venv
  `~/.venvs/phycoweb` (Python 3.14.4) for orchestration.
- **Rationale**: the calibration's 60 s per run figure was measured on Windows
  (`reports/002-core-dynamics-redesign/harness/timing.json`), and `sp80022` 1.0.0 was shown to
  agree across the two environments (feature-002 R7). TestU01 and PractRand are Unix-native and
  no C compiler is installed on Windows.
- **Alternatives**: run everything in WSL (possible; it would need a fresh calibration timing);
  install a Windows compiler (an extra download for no benefit).

## R2. Calibration design (FR-001 to FR-006)

- **Decision**:
  - Run r = 0…999. Each run draws 100 × 2²¹ bits with `os.urandom`, one sequence at a time,
    hashes the run's bytes in order (SHA-256), and evaluates the 100 sequences with
    `sp80022.battery` and `sp80022.assess` exactly as `scripts/evalcore.py` does. No byte is
    written to disk.
  - Each run writes one record (data-model §1) before the next starts. Records are append-only:
    the runner refuses to overwrite an existing run index, and resumes after a crash at the first
    missing index. The analysis refuses to run unless indices 0…999 are all present and uses all
    of them (no early stopping, no discarding).
  - The harness hash and the feature-002 rules are checked at start: `sp80022.source_sha256()`
    must equal `1563526e…0602c41700`.
- **Rationale**: reusing the frozen code path means the measured rate is the rate of the actual
  protocol, not of a re-implementation. A fixed, fully used run count stops "run until the
  number looks right".
- **Alternatives**: store the bytes and score later (26 GB, no benefit); simulate p-values from
  theory (would assume exactly the independence that O3 questions).

## R3. Calibration statistics (FR-003, FR-004)

- **Decision**:
  - Rates (overall, per family, per sub-test, per number of failing families) with exact
    Clopper–Pearson 95% intervals.
  - Pairwise family co-failure: count of runs where both families fail, the expected count under
    independence (n·r_A·r_B), and a two-sided Fisher exact p-value per pair. The p-values are
    reported only, not used for any decision.
  - Expected values from the feature-002 rules, computed exactly: a single-p-value family fails
    with probability 1 − P(Binomial(100, 0.99) ≥ 97) plus the uniformity term; a multi-sub-test
    family with P(Binomial(n_sub, q) > k_max), with q from the same proportion rule. For
    Random Excursions and Random Excursions Variant, m′ varies per run, so the expected value uses
    the run's own m′ and k_max, as the protocol does.
  - **Consistency** per family: "consistent" if the expected rate lies inside the 95% interval.
  - **Implied PASS probability** for a perfect candidate and perfect control:
    (1 − r̂)², with the interval from the endpoints of r̂'s interval. The negative control is
    taken to fail with probability 1 (it failed 11/15 families in attempt 1).
- **Rationale**: exact intervals are simple, and with 1,000 runs at r ≈ 0.2 the half-width is
  about 2.5 points (SC-001 needs ≤ 3).
- **Alternatives**: bootstrap intervals (no gain for binomial counts).

## R4. Fast streams (FR-007, FR-008)

- **Decision**: one C99 program, `fast/phyco_stream.c`, built with
  `gcc -O2 -std=c99 -Wall -Wextra -Werror`:
  - generators `phyco-v2` (design.md 1.0, including the 256-step warm-up), `lut-v1` (feature 001,
    no warm-up) and `os` (Linux `getrandom`, the positive control);
  - output: unsigned 32-bit words in **little-endian** byte order (the order PractRand `stdin32`
    and the TestU01 driver read), to stdout, unbounded or for `--words N`;
  - `--reverse` writes each word bit-reversed (bit 0 ↔ bit 31), for the TestU01 second
    orientation; `--hex` writes one upper-case hex word per line for equivalence tests.
  - The perturbation table comes from `fast/lut_table.h`, generated from `phycoweb/lut.py` by
    `scripts/gen_c_lut.py` and checked by a test, so the table cannot drift.
  - `lut-v1` in C mirrors the feature-001 behaviour exactly: the 64-bit product
    `D[i] · (P[i] − P[j])`, wrapped to signed 32-bit, arithmetic shift right by 8, the no-op
    second wrap (feature-002 O4), the `D == 0 → 1` rule and the 16-bit masks. This multiplication
    is recorded lut-v1 behaviour, kept only to reproduce the negative control.
  - `phyco-v2` in C uses only the operations the design allows (no `*`, `/`, `%`); a test greps
    the `phyco-v2` function for them.
- **Equivalence** (US3): every word of the committed golden vectors (2 × `phyco-v2`, 1 ×
  `lut-v1`); the first 10⁶ words of all 100 feature-002 `dev` seeds for both generators against
  the Python reference models; and, inside each attempt, the first 10⁶ words of every held-out
  seed (candidate and negative control) before any battery runs.
- **Rationale**: the Python models run at roughly 10⁵ words/s; an option-A attempt needs about
  2.4 × 10¹³ words per generator. A C loop of this size runs at well over 10⁸ words/s.
- **Alternatives**: numpy vectorisation (the update is sequential, so it does not vectorise);
  PyPy (still far too slow and adds a toolchain).

## R5. One pipeline for every battery run

- **Decision**: every battery run is
  `phyco_stream <gen> [seed] [--reverse] | tee >(sha256sum > <run>.sha256) | <consumer>`, where
  the consumer is PractRand `RNG_test stdin32 …` or the TestU01 driver reading 32-bit words from
  stdin. The stream hash is recorded for all three generators, so the positive-control input is
  identified even though it is not stored.
- **Rationale**: one code path for candidate, controls and both tools; the tool never sees which
  generator it is testing; hashing costs little with SHA-NI.
- **Alternatives**: link generators into the TestU01 driver (faster, but a second code path and
  no stream hash).

## R6. PractRand

- **Decision**:
  - Version: the latest official release on the PractRand SourceForge project, confirmed at the
    download request (expected 0.95, or 0.94 if 0.95 is not published there). Built from source
    with g++ `-O3 -pthread` as its documentation describes; archive and binary SHA-256 recorded.
  - Command: `RNG_test stdin32 -tlmax 1TB -tf 2 -multithreaded`. `-tlmax 1TB` is 2⁴⁰ bytes;
    `-tf 2` selects the expanded test set, which is stricter than the default `-tf 1`.
  - Parsing: at each checkpoint PractRand lists every result with an anomaly (test name, raw
    statistic, p-value, grade) and the count of results without anomalies. S for PractRand is the
    sum, over checkpoints, of listed results plus the unlisted count. An unlisted result is
    treated as not meeting rule 1, which is valid only if PractRand's listing threshold is far less
    extreme than 0.005/S (about 5 × 10⁻⁸ for the expected S): this is checked on the dev rehearsal
    with `-a` (show all results) if the build supports it, otherwise from the PractRand source.
    If it does not hold, every run uses the all-results option, which can only add failures.
- **Rationale**: `-tf 2` is the strictest standard setting. Counting unlisted results keeps S, and
  so the Bonferroni bound, honest.
- **Alternatives**: `-tf 1` (weaker); stopping at the first FAIL for the candidate (not allowed;
  only the negative control may stop early, spec Edge Cases).

## R7. TestU01

- **Decision**:
  - Version 1.2.3 from the official TestU01 site, built in WSL with
    `./configure --prefix=$HOME/testu01 && make && make install`. gcc 15 treats old implicit
    declarations as errors, so `CFLAGS="-O2 -std=gnu89"` (or `-Wno-error=…`) may be needed; the
    exact flags are recorded. Archive and library SHA-256 recorded.
  - Driver `fast/testu01_driver.c`: an external generator (`unif01_CreateExternGenBits`) that
    returns the next 32-bit word read from stdin; runs `bbattery_SmallCrush`, `bbattery_Crush` or
    `bbattery_BigCrush`; with `swrite_Basic = TRUE` the full text log is kept. After the battery
    it writes `bbattery_NTests`, every test name and every `bbattery_pVal` entry as one JSON line,
    so rule 1 uses the battery's own p-values, not text scraping.
  - Rule 3 ("eps"/"1 − eps"): TestU01 prints these for p-values beyond its epsilon (10⁻³⁰⁰), so
    rule 3 is always contained in rule 1; it is still checked from the text log.
- **Rationale**: the official batteries unchanged; machine-readable p-values make the rule exact.
- **Alternatives**: parse the text summary only (it lists only p outside [0.001, 0.999], so the
  count and the in-range p-values would be missing).

## R8. Failure rule, S and verdict (spec Pre-registered Battery Protocol)

- **Decision**:
  - S is counted per generator on the dev rehearsal (R9): all PractRand results at all
    checkpoints to 1 TiB for one seed, plus all TestU01 p-values of the three batteries in both
    orientations for one seed, times 10 seeds. This S is written into the freeze and used
    unchanged for all three generators.
  - If a held-out run reports more p-values than its share of S (e.g. a PractRand result count
    differing by checkpoint), the attempt uses the larger, actual count, which only lowers the
    threshold (stricter).
  - Rules 1–3 are applied by one pure function (`protocol/batteries.py`) to the saved logs, so
    the attempt and the re-score (SC-006) use the same code.
- **Rationale**: the bound 2 · S · 0.005/S = 1% holds under any dependence between p-values
  (union bound), which is exactly the property O3 shows is needed.
- **Alternatives**: per-battery k_max rules like feature 002 (need an independence assumption);
  a battery-level calibration (unnecessary with a union bound, and very expensive).

## R9. Dev rehearsal and timing

- **Decision**: before the freeze, one full rehearsal of all batteries for `phyco-v2` on the
  first feature-002 `dev` seed `(56053, 7029, 30841, 11050)`, plus a short run of each battery on
  `lut-v1` and `os`. It measures run times, counts S, confirms the parsers on real output, and
  provides the parser test fixtures. Its results are reported in full (FR-014); they do not
  change any rule.
- **Scheduling**: the runner keeps at most 32 runs in progress; a PractRand run with
  `-multithreaded` counts as 4 slots. Generators run strictly in the order positive, negative,
  candidate (FR-012). Expected per generator (to be replaced by the rehearsal's measurements):
  BigCrush 3–5 h per run on one core; PractRand to 1 TiB several hours per run; about half a day
  to a day per generator, so 1–3 days per attempt.
- **Alternatives**: no rehearsal (S would be guessed, which the spec does not allow).

## R10. Records, storage and seeds

- **Decision**:
  - Battery seed sets live in a new module `protocol/battery_seedsets.py` (prefix
    `phycoweb-003/`, 10 seeds per set, fingerprints copied from the spec). The feature-002
    `protocol/seedsets.py` is not changed, so no feature-002 hash changes.
  - Calibration records: `reports/003-extended-batteries-calibration/calibration/runs/` — one
    gzip-compressed JSON per run, about 150 KB, about 150 MB in total, holding every per-sequence
    p-value (FR-002). Whether these files are committed or kept local (like the feature-002
    control bytes) is an owner decision at the calibration result review; the summary record and
    a SHA-256 list of all run files are committed either way.
  - Battery logs: PractRand text, TestU01 text and JSON-lines output, stream hash, exit status
    and timing per run, under `reports/003-extended-batteries-calibration/attempt-<n>/`. Expected
    under 100 MB per attempt.
  - Tools live outside the repository: `~/practrand/`, `~/testu01/` in WSL; downloads go to a new
    empty directory and are extracted there (untrusted input), and the build scripts are kept in
    the repository, not in the download directory.
- **Rationale**: matches feature-002 practice; keeps the repository free of third-party code
  (GPL-3.0, constitution Technical Constraints).

## R11. Licences and downloads

- **Decision**: no third-party source is committed. Each download is requested separately with
  file name, source URL and size (constitution IX, spec FR-009): the PractRand release archive and
  `TestU01.zip`. Their licences are read at download and recorded in `tools/` in the reports;
  because nothing is vendored or linked into repository code that is distributed, they do not
  affect the repository licence. The TestU01 driver is repository code that links TestU01 only
  locally; it is not distributed as a binary.
