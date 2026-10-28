# Research: Integer LUT Perturbation Source

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-10-28

All findings below came from commands run on 2026-10-28 on Windows 11, Python 3.10.11,
numpy 2.2.6, scipy 1.15.3, nistrng 1.2.3. Probe scripts were kept in the session scratchpad and
are not part of the repository.

## R1. Overflow in the flux stage: does it happen in practice?

- **Finding**: Yes. Running the `readmee.md` model for 200,000 steps (seed
  `[1024, 2048, 4096, 8192]`), the largest flux product `|D × ΔP|` reached 4,150,546,056,
  beyond the 32-bit signed maximum (2,147,483,647). The LUT variant reached 4,150,314,063.
  numpy wraps the result modulo 2³² and emits `RuntimeWarning: overflow encountered in scalar
  multiply`.
- **Decision**: The new model reproduces the current behavior exactly through an explicit
  `wrap32()` (two's-complement 32-bit wrap) at the two points numpy wraps implicitly: the flux
  product, and `abs()` of the flux. This is frozen behavior pending spec Open Issue 2. It is
  written out explicitly so that it is defined (Principle I), not because it is the intended
  design.
- **Rationale**: FR-008 requires the other stages to stay behaviorally unchanged. Relying on
  numpy's overflow-with-warning is implicit and could change between numpy releases.
- **Alternatives considered**: (a) Keep numpy int32 scalars. Rejected: behavior is implicit,
  emits warnings, and numpy's scalar promotion rules changed in 2.0 (NEP 50). (b) Use 64-bit
  or unbounded arithmetic. Rejected: that changes outputs, so it is a behavior change outside
  this feature.

## R2. Can a pure-integer Python model match the numpy model exactly?

- **Finding**: Yes. A pure-`int` model with `wrap32()` matched the numpy `readmee.md` model
  (float perturbation in both) for all 100,000 words compared, once the output was taken as an
  unsigned 32-bit value.
- **Finding (defect)**: The `readmee.md` model returns **signed** output words. The value
  `(D[0] & 0xFF) << 24` is a numpy int32 and overflows when bit 31 is set; the first word for
  the reference seed is `-0x29120C2A` rather than `0xD6EDF3D6`. The bits are identical; only
  the integer interpretation differs.
- **Decision**: The output word is defined as **unsigned 32-bit (0 … 2³²−1)**. Baseline vectors
  from the archived model are masked with `& 0xFFFFFFFF` by the vector tool, which does not edit
  the archived file. This is recorded in the baseline manifest.
- **Rationale**: Hardware outputs a 32-bit bit pattern; a negative Python integer is an artifact
  of numpy, and hex vector files must be unambiguous.

## R3. LUT generation and encoding

- **Finding**: `T[i] = trunc0(sin(2π·i/256) × 1024) & 0xFFFF` gives `T[0]=0x0000`,
  `T[64]=0x0400`, `T[128]=0x0000`, `T[192]=0xFC00`. The largest truncation error is 0.997, and
  the shortest repeat period of (`food_a`, `food_b`) is exactly 128 steps (checked over
  1,280 steps).
- **Decision**: An offline generator script computes the table using floating point (allowed
  offline by Principle I). It writes (a) a Python constants module with 256 hex literals and
  (b) a plain-text hex file with one 4-digit hex value per line, for RTL to read. Both are
  committed. A test recomputes the formula and checks that both artifacts match it exactly.
- **Rationale**: Committed constants are authoritative (FR-007a); the hex file satisfies FR-012
  and loads directly with VHDL `textio` or Verilog `$readmemh`.
- **Alternatives considered**: (a) A quarter-wave table (64 entries plus symmetry logic).
  Rejected: it adds sign/mirror logic that has to be specified and verified, to save 192 entries
  of a 4 Kbit ROM. (b) Computing the table at import time. Rejected: violates FR-003.

## R4. Archived variants: what is in history

- **Finding**: The archived files are **not** the same algorithm as the `readmee.md` model:
  - `MycoPRNG.py`: takes the food signals as arguments, saturation threshold `D[0] > 2000`,
    `max(1, …)` floor.
  - `phycoweb_nist_eval.py`: initial `D = 512`, injects `food_b` into `P[1]`, disruption on
    `D[0] or D[1]`, XOR into `P[0]`/`P[2]`.
  - `nistrng_bench.py`: a different engine built on xorshift128+.
- **Decision**: All are archived as provenance (FR-013). Only `readmee.md` defines the
  behavior that this feature preserves (spec Assumption 1). The manifest records each variant's
  source commit and a one-line note on how it differs.
- **Rationale**: Principle V forbids discarding variants. Recording the differences stops anyone
  treating the archived scripts as the reference.

## R5. Test framework

- **Finding**: `pytest` is not installed; only the Python standard library, numpy, scipy and
  nistrng are available.
- **Decision**: Use the standard-library `unittest` (`python -m unittest discover -s tests`).
- **Rationale**: Adds no dependency (Technical Constraints: new dependencies need
  justification). The tests are simple equality and AST checks.
- **Alternatives considered**: pytest. Rejected because it would be a new dependency with no
  capability this feature needs.

## R6. NIST SP 800-22 evaluation method

- **Finding**: The deleted `nistrng_bench.py` used
  `nistrng.run_all_battery(bits, SP800_22R1A_BATTERY)` and **silently skipped** tests that
  returned `None` (ineligible for the sequence length). That conflicts with Principle IV.
- **Decision**:
  - Bit order is MSB-first within each 32-bit word, applied identically to the baseline and the
    LUT model.
  - Sample: 1,000,000 bits (31,250 words) per seed, for the reference seed and the old bench seed
    `[0x1234, 0xABCD, 0x5555, 0xAAAA]`.
  - Every test in the battery is reported as `pass`, `fail` or `not_eligible`, with its p-value.
  - The report records the commands run, the nistrng/numpy/Python versions and the git HEAD.
- **Rationale**: 10⁶ bits meets the minimum length that SP 800-22 recommends for most tests.
  Including ineligible tests keeps the report complete.
- **Limitation (recorded in the report)**: This is a single sequence per seed, not the
  multi-sequence proportion and uniformity analysis of the full NIST procedure. Results are a
  screening signal, not a certification, and say nothing about cryptographic security
  (Principle IV, Security Policy).

## R7. Second environment for SC-002

- **Finding**: Only Python 3.10.11 is installed (no `py` launcher, no other interpreters).
- **Decision**: The golden-vector check runs on 3.10.11 locally. The second environment needs a
  different Python minor version or OS, supplied by the repository owner (e.g., a 3.12 venv or
  a Linux machine). Until it runs, SC-002 stays **open**, not passed.
- **Rationale**: Principle V and the Phase Completion rules forbid claiming a test that was not
  run.

## R8. Behavior observation (not acted on)

- **Finding**: With either perturbation source, the Frustrated Foraging disruption fired on
  about 99.5% of steps (199,049 of 200,000 for float; 199,106 for LUT), and `D` reached its
  ceiling of 65,535. The "threshold supervisor" is effectively always on.
- **Decision**: No change in this feature (FR-008). Recorded as spec Open Issue 4 for the owner
  to review, since it suggests the dynamics may be degenerate.
