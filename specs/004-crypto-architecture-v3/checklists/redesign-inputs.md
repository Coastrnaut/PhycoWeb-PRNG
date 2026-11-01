# Redesign Inputs Checklist: the seed-entropy note's §5.3, item by item

**Purpose**: Verify that every item of the redesign checklist of
[`seed-entropy-bound.md`](../../../research/security/seed-entropy-bound.md) §5.3 is handled by
this feature's spec and plan (FR-048), and that the requirements behind it are traced.
**Created**: 2026-11-01, by the AI coding agent, and updated the same day after the owner chose
every recommended option of research.md's "Choices for owner review". The owner's review of
this file is pending.
**Feature**: [spec.md](../spec.md). Its table "Redesign checklist" gives the dispositions group
by group; this file checks them one item at a time against the requirements and the plan.

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

A ticked item has a disposition that meets its wording, of one of four kinds: **Covered** by a
requirement of this feature, **By design** (the form of `phyco-v3` removes the issue),
**Carried** to a named later feature, whose spec must take it up, or **Owner** (the owner's
action). Carried and owner items are not done, and the final report cites the evidence for every
covered item (FR-048). Four items, A7, A11, B4 and C3, were only partly met until the owner chose
every recommended option of [research.md](../research.md), "Choices for owner review", on
2026-11-01; each note names the choice that settled it.

## A. Fix in the design

- [x] A1 Key of at least 128 bits; no strength claimed below 128. Covered: FR-005 (s = 128 at
  every claimable size), FR-006 (a 256-bit key).
- [x] A2 Reachable secret state at least twice the claimed strength; the 2×2 conflict decided.
  Covered: FR-009, FR-010; FR-017 (D3: 2×2 and 3×3 are research variants outside every claim),
  recorded in security.md §20.1 in plan phase 8.
- [x] A3 Public parts of the state not counted as secret. Covered: FR-009.
- [x] A4 Nonce for stream separation; a reseed input if prediction resistance is claimed.
  Covered: FR-006 (a 128-bit nonce, once per key); FR-013 and FR-016 (an optional reseed,
  treated as attacker-chosen); FR-004 (prediction resistance not sought, D7).
- [x] A5 Key loading that creates no related states. Covered: FR-013 (how the key enters the
  state, with the theorem's preconditions), FR-014 (injective padding and domain separation);
  FR-023, FR-024 and research R13 (no symmetry that relates shifted or rotated states).
- [x] A6 Output limit per key and per key and nonce. Covered: FR-007; research R9.
- [x] A7 Parameterized grid, 2×2 to 16×16, with key loading at every size. Covered: FR-018,
  FR-032; research R14, where a keyed variant of capacity c takes a c-bit key and a c/2-bit
  nonce, and a variant with no room for them is keyless (choice R14.2). The first draft gave
  every keyed variant a 256-bit key and a 128-bit nonce, which a 2×2 state of 256 bits at
  w = 32, or 32 bits at w = 4, cannot hold.
- [x] A8 Warm-up derived from the grid diameter and measured full diffusion. Covered: FR-029
  (exact R_f and R_b; instantiation makes every state bit depend on every key and nonce bit),
  FR-028 (the round rule); research R13.
- [x] A9 Per-node constants by rule, with no translational or rotational symmetry. Covered:
  FR-023, FR-024; research R13 and R15.
- [x] A10 Step designed for 200 MHz. Covered: FR-025 (at most two serial w-bit carry chains per
  pipeline stage, and each stage's estimated delay against the 5 ns of 200 MHz and the LUT levels
  on its longest path, as estimates that feature 008's post-route timing checks); research R5.
- [x] A11 Local food source and registered output tree; no grid-wide signals. Covered: FR-018
  (constants enter at local food nodes; registered absorption and output trees); plan, Complexity
  Tracking; research R15, where each food node holds its own constants in a ROM indexed by the
  round counter (choice R15.2). The clock uses the device's clock network; reset and the start
  signal reach the nodes through registered fan-out trees, and the round and phase counters are
  replicated and run in lockstep, so no counter value crosses the grid (FR-025). The first draft
  implied one central LFSR, whose output would cross the grid.
- [x] A12 Invertibility decided, with its consequence for backtracking. Covered: FR-019
  (bijective by construction), FR-013 (forget after every request), FR-004 (backtracking
  resistance across forget).
- [x] A13 Generic, vendor-neutral VHDL with 0 DSP blocks. Carried to 006; prepared by FR-018,
  FR-020, FR-027, FR-055 and FR-056.
- [x] A14 Fit and timing on the Arty A7-100T. Carried to 008; prepared by FR-025 and FR-026.

## B. Analyse before or during the design

- [x] B1 Seed bound reproduced on a reduced seed domain first. Covered: FR-001 to FR-003;
  research R2.
- [x] B2 Guess-and-determine and SAT/SMT state recovery on 8- and 16-bit variants. Carried to
  005. The variants are defined here (FR-032), and their key loading by choice R14.2.
- [x] B3 Slow-variable leakage through conductance classes. By design: Π has no classes and no
  data-dependent operation (FR-020), and every word is full-range (FR-021).
- [x] B4 Related-seed and rotational experiments, whose results feed the key-loading and constant
  rules. Covered before the freeze: the avalanche test of research R4 includes related-key,
  related-nonce and rotational differences, whose firings raise R (choice R4.5), beside the
  symmetry checks with word rotations (research R13). Carried to 005: the full experiments.
- [x] B5 Functional graph and cycle structure, merging included. By design: Π is a permutation
  (FR-019), checked exhaustively at 2×2, w = 4 (FR-037), so no states merge; the generic bound
  covers its cycles, which are not measured (choice R13.2).
- [x] B6 Linear, differential and machine-learning distinguishers on reduced-step variants.
  Covered for trails: FR-038; research R12. Carried to 005: clustering, linear hulls and
  machine-learning distinguishers.
- [x] B7 Initialization analysis: related keys, related nonces, weak keys. Covered by
  specification: FR-013, FR-014, FR-029. Carried to 005: the attack analysis, before any claim,
  as FUT-SEC-5 asks (FR-049). A first-order test runs here: the related-key and related-nonce
  differences of research R4 (choice R4.5).

## C. Answer explicitly in the spec

- [x] C1 Where the mixing comes from. Covered: FR-022 (the nonlinear component designed, named
  and bounded), FR-030 (no security argument rests on the slime-mould mapping).
- [x] C2 Which operations count as "no hash, cipher or standard PRNG", key loading and plain
  counters included. Covered: FR-047, whose table re-decides feature-002 FR-007 (D6): it allows
  published design methods and a plain counter, which is not a PRNG, and forbids any published
  permutation, cipher, hash, MAC or standard PRNG in Π, the mode and key loading. Research R15
  classes its LFSR under that rule as a published design method (choice R15.1).
- [x] C3 Throughput goal and measured result. Covered: FR-026 (the throughput implied at
  200 MHz), stated beside a goal of 10⁸ 32-bit words per second at 200 MHz, the goal feature 003
  set for the C stream; reported, not an eligibility rule (research R5; choice R5.2). Carried to
  006 and 008: the measurement.
- [x] C4 Certification route named; no FIPS 140-3 or SP 800-90A wording. Covered: FR-011 (D8).
- [x] C5 Battery levels on hardware output and on the C stream. Carried to 008 (the FUT-HW-4 row
  of the spec's traceability table).
- [x] C6 Hardware security tests; side channels untested without equipment. Carried to 008 (the
  FUT-HW-5 row).

## D. Carry into the protocol and tooling

- [x] D1 Every variant logged; development inputs for tuning; held-out sets only after the
  freeze. Covered: FR-040, FR-041; research R3; data-model §2 and §3.
- [x] D2 Positive-control false-failure rate calibrated before the acceptance rules freeze.
  Carried to 007. Here: the bias rule's uniform control and its computed false-firing rates
  (research R4).
- [x] D3 Stream byte counts record the bytes consumed. Carried to 007; this feature streams
  nothing to a battery.
- [x] D4 Single-writer progress logs. Carried to 007. This feature applies the rule to its own
  sweep and hash-chained logs: research R2 and R16 (choices R2.2 and R16.2).
- [x] D5 Feature files committed before the freeze. Covered: FR-043; `design_freeze.py create`
  exits 2 while `git_dirty` is true (contracts/cli.md).
- [x] D6 Every role timed before run times are projected. Carried to 007. Here: the projection
  before every heavy run (research R7).
- [x] D7 Approval status kept outside frozen files. Covered: FR-034. The freeze hashes no file
  that holds an approval (data-model §13); approvals live in the spec's Review & Approval table.
- [x] D8 Vectors and statistics per size, 4×4 before 16×16. Covered for vectors: FR-036;
  research R8. Carried to 007: the statistics per size. Research R7 runs this feature's evidence
  in that order (choice R7.3).
- [x] D9 On-board counters and equivalence, with power from the board's sensor. Carried to 008.

## E. From the repository review of 2026-10-31

- [x] E1 Conductance classes; range and occupancy of every state variable. By design: Π has no
  classes. Covered: the frequency test measures every state bit (FR-037; research R4).
- [x] E2 Feature-002 FR-002, FR-003, FR-005 and FR-009 re-decided. Covered: FR-047 and its table.
- [x] E3 A rationale for every constant and for the warm-up length. Covered: FR-023, FR-024,
  FR-028, FR-034.
- [x] E4 Conserved sum in the transport stage. Covered: FR-037 (no conserved sum or zero mode of
  `phyco-v2` survives); research R13 (invariant checks).
- [x] E5 A guaranteed minimum period. By design, in a weaker form: no period is guaranteed;
  within the output limits a repeated state is covered by the theorem's bound (FR-007, FR-013),
  and a permutation merges no states.
- [x] E6 One canonical output serialization. Covered: FR-015; contracts/model-v3-api.md.
- [x] E7 Inter-stream tests on related keys or nonces. Carried to 007. A first-order
  related-key and related-nonce test on Π runs here (research R4; choice R4.5).
- [x] E8 Reduced widths from the same generic, with shifts and rotations scaled. Covered: FR-024,
  FR-032; research R14.
- [x] E9 Full-speed capture into the DDR3L. Carried to 008.
- [x] E10 Test-time budget per grid size. Carried to 007.
- [x] E11 Dieharder. Carried to 007.
- [x] E12 RTL key-loading interface and reset sequence. Covered: FR-025 and FR-059, specified
  here and built in 006 and 008.
- [x] E13 Branch-free selections in the C stream and the model. Covered for `phyco-v3`: FR-020
  (no selection on secret data); any C evaluator is generated from an operation list that holds
  no selection (research R11). Carried to 006: the check of the compiled code.
- [x] E14 Principle I's default width. Owner: the constitution still reads "16-bit signed state,
  32-bit output words unless a ratified spec says otherwise", and the PATCH amendment is the
  owner's (spec, Assumptions). Every width is stated here (FR-027).
- [x] E15 TestU01's licence. Carried to 007.

## F. From the second repository review of 2026-10-31

- [x] F1 Backtracking: a permutation with an explicit one-way output. Covered: FR-019, FR-013.
- [x] F2 Transport invertible, or its zero modes analysed, at every size. Covered: FR-019
  (bijective by construction), FR-037.
- [x] F3 Mixing that does not rely on biased top bits; bit frequencies measured. Covered: FR-021,
  FR-037; research R4.
- [x] F4 Output rotations that do not align; a rule for every size. Covered: FR-024 (rotation
  amounts by a stated rule, chosen by the trail bounds). `phyco-v3` outputs the rate lanes after
  a full call of Π (FR-015), so `phyco-v2`'s output rotations have no counterpart.
- [x] F5 Slide resistance. Covered: FR-023 (constants differ in every round and at every food
  node within a call), FR-014.
- [x] F6 Warm-up margin from measured diffusion. Covered: FR-028, FR-029; the round rule doubles
  R_dist and max(R_f, R_b).
- [x] F7 Held-out sets that cannot be computed before the freeze. Carried to 007 (FR-040).
- [x] F8 A reproducible positive control. Carried to 007. Here: the uniform controls come from
  public strings (research R3).
- [x] F9 Graded negative controls. Carried to 007. Here: tool validation on known results
  (FR-039), and inside every avalanche run a check of detection power against the exact
  dependency matrices (research R4; choice R4.6).
- [x] F10 SP 800-22 decision rule. Carried to 007.
- [x] F11 PractRand length. Carried to 007.
- [x] F12 Line endings for every hashed file. Covered: FR-053; research R18, which pins every
  Markdown file of this feature, the spec among them, since every record holds the spec's
  SHA-256, the hash-chained logs and the makefiles (choice R18.2). Carried to 006: VHDL, XDC and
  Tcl.
- [x] F13 Pinned dependencies. Covered: FR-053; research R18.
- [x] F14 Full-length hardware equivalence, CRC-32 at 2³² and 2⁴⁰ words. Carried to 008. For
  008: the Python model would need about 50 h for 2³² words at 4×4, so the expected values need
  a fast model checked against the frozen one.
- [x] F15 Reference-model speed. Covered: FR-036; research R8 (about 1 ms per call at 4×4 and
  16 ms at 16×16, so the vectors keep their full length at every size).
- [x] F16 Invariants as tests; every data-flow direction tested. Covered: FR-037, FR-058;
  property tests in Hypothesis, whose download the owner approved on 2026-11-01 (research R17,
  R19).
- [x] F17 Archive `phyco-v2`. Covered: FR-042; research R18.
- [x] F18 Record storage. Covered for this feature: Edge Cases; research R16. Carried to 007: the
  feature-003 records.
- [x] F19 Output bits per step for every size. Covered: FR-018 (b, c, r and R per supported
  size), FR-026.
- [x] F20 Documentation drift. Covered: FR-051; plan phase 9 names the README corrections and the
  addendum to the feature-002 phase report.

## G. Pending input

- [x] G1 Feature-003 battery attempt 1. Covered: PASS, accepted by the owner on 2026-11-01
  (security.md 2.9); a reference only, which does not carry over (FUT-SEC-7).

## Requirements behind the checklist

| Requirement | Spec | Verdict |
|-------------|------|---------|
| FUT-SEC-1 Key entropy | FR-005, FR-006, FR-010 | Covered |
| FUT-SEC-2 Reachable secret state | FR-009, FR-010, FR-015, FR-017 | Covered at every claimable size; 2×2 is outside every claim (D3) |
| FUT-SEC-3 Stream separation | FR-006, FR-014 | Covered |
| FUT-SEC-4 Reseeding | FR-004, FR-016 | Not applicable: prediction resistance is not sought (D7) |
| FUT-SEC-5 Initialization analysis | FR-013, FR-014, FR-029, FR-049 | Specified; the attack analysis carried to 005 |
| FUT-SEC-6 Output limit | FR-007 | Covered |
| FUT-SEC-7 Re-validation | FR-035, FR-036, FR-043 | Partly; the statistical programme carried to 007 |
| FUT-SEC-8 Demonstration first | FR-001 to FR-003 | Covered |
| FUT-SEC-9 Certification route | FR-011 | Covered |
| FUT-GRID-1 Parameterized size | FR-018, FR-032 | Partly: the generics cover n = 2…16 in the model and the supported sizes are listed; n = 5, 6, 7 and 9…15 are open items with their reason (FR-018) |
| FUT-GRID-2 Key fills the state at every size | FR-009, FR-017; research R14 | Covered: a 256-bit key at every claimable size, and a c-bit key with a c/2-bit nonce at every keyed reduced variant (choice R14.2) |
| FUT-GRID-3 Mixing across the grid | FR-015, FR-029 | Covered, output taps included: the output is the whole rate part after a full call of Π |
| FUT-GRID-4 Per-node constants by rule | FR-023, FR-024, FR-031 | Covered; the clause on the disruption does not apply, since the disruption is removed (D5) |
| FUT-GRID-5 Validation per size | FR-032, FR-033, FR-036, FR-052, FR-056 | Covered for variant IDs and vectors; the statistics per size carried to 007, and the validation of 4×4 first carried to 006 (in simulation, before 8×8 and 16×16) and 008 (on the board, before each larger claimable size that fits the XC7A100T) |
| FUT-HW-1 Generic VHDL | FR-018, FR-020, FR-027, FR-055, FR-056 | Prepared; carried to 006 |
| FUT-HW-2 Efficient on the Arty A7-100T | FR-025, FR-026 | Designed for; carried to 008 |
| FUT-HW-3 Performance on the board | FR-026 | Carried to 006 and 008 |
| FUT-HW-4 Equivalence and statistics from hardware output | FR-036, FR-054, FR-056 | Carried to 008 |
| FUT-HW-5 Hardware security tests | FR-020, FR-025, FR-059 | Specified; carried to 008 |

## Result

All 72 items have a disposition in the spec (FR-048), and all 72 are met by the spec and plan
as they stand after the owner's answers of 2026-11-01. A7, A11, B4 and C3 were partly met until
choices R14.2, R15.2, R4.5 and R5.2 were applied. Every FUT requirement is traced in the spec.
"Met" includes the items carried to features 005 to 008, whose specs must take them up, and
E14, which is the owner's.

Re-checked on 2026-11-01 after the answers to both checklist runs: every item still holds. The
notes of A10 and A11 now follow FR-025 as it stands, FUT-GRID-1 reads Partly, as in the spec's
table "Security Policy traceability", and FUT-GRID-5 names the order carried to 006 and 008.
