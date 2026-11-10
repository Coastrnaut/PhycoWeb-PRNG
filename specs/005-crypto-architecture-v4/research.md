# Research: Cryptographic Architecture, Second Design Round (phyco-v4)

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v4` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

Feature 004's research (`specs/004-crypto-architecture-v3/research.md` at 99e6994, SHA-256
`614afc499c5941ccb5284ca1baafbe0055f011b6dde1bf816127884e2c66da0a`) is this feature's baseline (spec FR-001): its R1 to R19
apply as written, with `phyco-v3` read as `phyco-v4` and its paths as this feature's, except where an item below changes them
(R14 lists them). The figures here come from `research/005/plan_projections.py` over feature 004's committed records and are
held in `research/005/plan-projections.json`.

## R1. The calibration (FR-004) — protocol

- **Decision**: a factor per tool and size for the bound searches, and per kind for the other evidence, each F = max(1, the
  largest ratio of measured to projected hours among feature 004's pairs projected at 0.001 h or more and below its 8 h cap);
  a pair whose run ended at its cap gives its ratio as a lower bound, used as it is. A tool with no pair at a size takes the
  largest factor of any tool at that size, and failing that its own largest factor at any size. The factors are fixed:

  | Tool or kind | Size | F |
  |--------------|------|---|
  | active-box count (cand-A1) | 4×4 | 1.000 |
  | active-box count | 8×8 | 7.447 |
  | active-box count | 16×16 | 2274 (the capped run at r = 5) |
  | active-S-box count (cand-B1) | 4×4 | 1.000 |
  | branch-and-bound (the box over one call) | 4×4 | 1.006 |
  | control (the uniform controls) | every size | 3.867 |
  | validation | — | 1.186 |
  | cross-check, demonstration, rotation ranking | — | 1.000 |

  The bound tools' factors come from 37 usable pairs; the other kinds' from the 6, 6, 2, 1 and 2 feature-004 records that
  hold their own projected and used hours.

- **What the pairs show**: feature 004 paired 90 bound searches with projections. Measured over projected ran from 0.00021 to
  2274, median 0.10: 27 projections were the 8 h cap itself, written where the probe gave no estimate; 26 read below 0.001 h,
  the Windows clock's tick; the rest missed both ways, overestimating every search that finished and underestimating the one
  that stopped feature 004, cand-A1's linear search at 16×16 and r = 5, projected at 0.004 h and stopped at its cap after
  8.17 h. No constant factor makes feature 004's projection formula reliable for bound searches, so this feature projects them
  from the hours that feature 004's runs took (R2), and uses F only where a run was projected and never made. The other kinds'
  projections stayed within a factor of 3.9 of their runs.
- **Rationale**: FR-004 asks for the calibration and its use; a factor of at least 1 never lets a projection shrink below
  feature 004's own, and the largest ratio is the worst miss recorded.
- **Alternatives considered**: the median ratio (rejected: it would scale the 16×16 searches down by a factor of ten);
  refitting feature 004's formula to its pairs (rejected: the misses span seven orders of magnitude with no trend in r that a
  fit could hold).

## R2. Projected needs and the listed climbs (FR-005) — protocol

- **Decision**: the projected need of a reference design's search is its measured hours where feature 004 made it, this
  plan's cap where that run ended at its cap, its projection times F where feature 004 projected it without making it (the cap
  where that projection was 8 h or the product is not below the cap), and the cap where feature 004 neither made nor projected
  it. For cand-A1, r = 1 is the box's own bound over one call, searched once at 4×4 in 1.085 h (differential) and read at
  every size. The table lists each design's searches per size and kind from r = 1, ending after the first search projected to
  reach its cap (FR-015), at the first r whose bound, searched or summed by FR-016, has weight above 128, or at R_max = 64.
- **What it gives under option E**, the caps the plan approval fixed (R3), with option A's need, the planner's recommendation,
  after each:

  | Design and size | Linear: need, R_bound | Differential: need, R_bound |
  |-----------------|-----------------------|-----------------------------|
  | cand-A1 16×16 | 48.184 h (r = 2 to 4 measured, r = 5 at the cap); 8 by sums. Option A: 12.184 h | 48.116 h (r = 5 never made, at the cap); 6 by sums. Option A: 12.116 h |
  | cand-A1 8×8 | 0.180 h; 9. Option A: the same | 0.099 h; 6. Option A: the same |
  | cand-A1 4×4 | 0.065 h; 17. Option A: the same | 1.093 h; 11. Option A: the same |
  | cand-B1 16×16 | 48 h (r = 1 at the cap); none. Option A: 12 h | 48 h (r = 1 at the cap); none. Option A: 12 h |
  | cand-B1 8×8 | 33.303 h (r = 1 projected to finish in 9.303 h, r = 2 at the cap); none. Option A: 4 h, r = 1 at the cap | 29.953 h (r = 1 projected to finish in 5.953 h, r = 2 at the cap); none. Option A: 4 h, r = 1 at the cap |
  | cand-B1 4×4 | 8.470 h (r = 5 at the cap); 17 by sums. Option A: 4.470 h | 8.921 h (r = 5 at the cap); 17 by sums. Option A: 4.920 h |

  An ARX design like A1 is projected to have R_bound at every claimable size; a Boolean design like B1 is projected to end at
  16×16, at its first search, which the order of R12 makes the cheapest place to end.
- **Rationale**: a measured hour of the same tool on the same operation list is the best projection there is; where none
  exists the cap is the most a search can charge.
- **Alternatives considered**: projecting every search by feature 004's formula times F (rejected by R1); listing searches
  past a cap (rejected: FR-015 ends a kind's searches there).

## R3. Caps, rows, the ceiling and FR-008's case (FR-005, FR-006, FR-008) — protocol

- **Decision (option E, the owner's at the plan approval of 2026-11-09)**: caps of 8 h at 4×4, 24 h at 8×8 and 48 h at
  16×16, for each kind; rows per candidate from its family's reference design, each at least twice its projected needs: ARX
  267.5 h, Boolean 425.3 h, the provisional structural (12 h) and bias (24 h) needs included and doubled; the feature-wide row
  102 h, holding probes of up to 4 h each (R5); three evaluated candidates per family, as inherited; 2,180.4 h in all, and the
  ceiling raised from D7's 720 h to 2,200 h, as FR-008 lets the owner raise it at the plan approval. The planner had
  recommended option A, 700.9 h within 720 h; the owner asked to "extend run limits even more to ensure we find a good
  candidate also".
- **FR-006's floors**: a cap must be at least twice the longest listed search projected to finish under it. At 8×8, B1's
  calibrated projections at r = 1, 5.95 h and 9.30 h, allow a cap below 5.95 h, under which both are projected to reach it,
  or a cap of 18.6 h or more; feature 004's 8 h lies between and fails FR-006. Under option A the floors are 2.17 h at 4×4,
  0.17 h at 8×8 and 0.34 h at 16×16; under option E, where B1's two searches at 8×8 and r = 1 are projected to finish under
  the 24 h cap, they are 2.17 h, 18.61 h and 0.34 h.
- **The options** (plan, "Choices for owner review"):

  | Option | Caps 4×4, 8×8, 16×16 | Per family | ARX row | Boolean row | Sum | Within 720 h |
  |--------|----------------------|------------|---------|-------------|-----|--------------|
  | A (recommended) | 4, 4, 12 h | 3 | 87.5 h | 118.8 h | 700.9 h | yes |
  | B | 8, 20, 20 h | 2 | 119.5 h | 261.3 h | 843.6 h | no |
  | C | 4, 4, 24 h | 3 | 135.5 h | 166.8 h | 988.9 h | no |
  | Feature 004's caps | 8, 8, 8 h | 3 | 71.5 h | 146.7 h | 736.6 h | no, and FR-006 fails at 8×8 |
  | E (the owner's) | 8, 24, 48 h | 3 | 267.5 h | 425.3 h | 2,180.4 h | the ceiling raised to 2,200 h |

- **Rationale**: every search feature 004 finished at 4×4 and 8×8 at w = 32 took at most 1.085 h, so option A's 4 h held
  each more than 3.6 times over and kept both the candidate limit and the ceiling the spec approved. Option E gives each size
  more room where feature 004 ran out or never ran: 8 h at 4×4, over seven times the longest search that finished there; 24 h
  at 8×8, above the floor that B1's projections set; 48 h at 16×16, six times feature 004's cap, where both its candidates
  ended or were projected to end. Under FR-016 a capped search costs exactly its cap and ends no climb, so a larger cap buys a
  stronger searched bound, and for a design whose first searches at a size are slow, any bound at all. Since every limit may
  only fall after the plan approval (FR-009), a generous start can still be lowered later, never raised.
- **Alternatives considered**: options B and C, which need the ceiling raised; rows at the larger family's size for every
  candidate (rejected: 794.8 h, above the ceiling, for no projected need).

## R4. The thread count (FR-007) — protocol

- **Decision**: one thread for every search, recorded in each record's `parallelism`. The kinds that already ran on worker
  processes in feature 004 (the uniform controls and the bias tests, 30 workers; the rotation search) keep their workers.
- **Rationale**: the calibration holds only one-thread searches, so no other count has a factor; scipy 1.15.3's `milp` passes
  no thread setting to HiGHS; and under FR-016 the searches that would need more compute end in a sum instead.
- **Alternatives considered**, each a tool change validated again before its first use (inherited R12): the MILP split by
  first-round activity over worker processes, the minimum over the parts being the minimum over the whole; a solver that runs
  threads, named here only as candidates, OR-Tools CP-SAT and HiGHS through `highspy`, each a download that needs the owner's
  permission for that file, with its name, source, size and licence.

## R5. Probes before any candidate (FR-005, FR-009) — protocol

- **Decision**: after plan phase 1 and before the candidate log's first `proposed` entry, each listed run that feature 004
  neither made nor ran to its cap is probed on the reference design's committed operation list, as a `projection` record charged
  to the feature-wide row: B1's searches at 8×8 and 16×16, A1's differential search at 16×16 and r = 5, and one structural check
  and one frequency and avalanche measurement per size and design at w = 32. A probe is the run itself, up to 4 h (option E; 1 h
  under option A); a run that finishes gives its hours, a bound search that does not is projected to reach its cap, and a
  structural check or a frequency and avalanche measurement that does not keeps the plan's provisional need for its kind (12 h
  and 24 h per candidate). "One structural check" is one run of every structural kind that inherited FR-037 asks at that size
  (the inverse tests, the dependency matrices, the symmetry and invariant checks), each kind's hours in the probe's record, and
  a probe lowers the provisional need only by the kinds it covers. The provisional needs are split equally over the three
  claimable sizes (4 h structural and 8 h bias per size): a probe that finishes at a size gives that size its hours, a size
  whose probe did not finish keeps its share, and a candidate's need is the smaller of the provisional need and that sum. A run
  feature 004 made is not probed again: its record, the same tool on the same operation list, size, width, kind and r, on the
  same machine at one thread, is the measurement, cited in the table by record ID. `projection_table.py` then writes the final
  table from the plan's rules and the probes; each value is the smaller of the plan's and the probes', so that every value only
  falls, and a probe that shows a need above its row is reported before any candidate, its run refused when it comes (inherited
  ANA-078).
- **Rationale**: the probes measure what feature 004 never ran at w = 32, the structural and bias kinds above all, and an
  upper limit of 4 h lets more of them finish while keeping them inside the feature-wide row's 40 h of probes.
- **Alternatives considered**: probing every listed run again (rejected: it repeats feature 004's measurements on the same
  machine); 60-second probes extrapolated by feature 004's formula (rejected by R1).

## R6. Sums of shorter spans (FR-016, FR-017) — protocol

- **Decision**: `round_rule.py` writes a `bound` record with method `split` for every r at which the largest sum of two
  established bounds exceeds the searched bound or stands where no search ran (data-model §2), computed in exact rational
  arithmetic from the two parts it cites; the climb continues by sums after a kind's searches end, until both kinds' weights
  exceed 128 or r reaches 64. The re-check recomputes every sum from its parts. Feature 004's tools already compute the same
  sums inside a search (`largest_sum` in `active_sbox.py` and `long_trail.py`); a sum outside a search is new and needs no tool,
  since it adds two committed weights.
- **Rationale**: every trail over r₁ + r₂ rounds is a trail over r₁ rounds followed by one over r₂, so under the single-trail
  assumptions each bound states, the weights add.
- **Alternatives considered**: a size-carrying proof as a source of R_bound (rejected by D11, kept as a check).

## R7. Trail characteristics at every nonlinear operation (FR-019, FR-020) — protocol

- **Decision**: a `trail` record holds, for every round, the state's difference or mask at the round's boundary and at the
  input and output of each nonlinear operation in the order of the candidate's operation list (data-model §3). The re-check
  recomputes the weight as the product of each operation's exact transition probability or squared correlation (for a
  modular addition the exact differential probability and linear correlation of its inputs and output; for an S-box its table
  entry), checks every linear step between recorded points by evaluating it, and classes the trail by the 2⁻¹²⁸ threshold:
  above it a confirmed vulnerability of the rounds it covers, at or below it `none`.
- **Rationale**: a difference held only after each round cannot fix the differences between two nonlinear layers of one round
  (feature 004, T131); held at every operation, the weight follows from the record alone.
- **Alternatives considered**: feature 004's per-round format (rejected by D9).

## R8. The security target first (FR-010 to FR-013) — protocol

- **Decision**: plan phase 3 copies the chapters "Security target" and "Mode" of feature 004's `design.md` and `rationale.md`,
  Version 0.4, into this feature's `design.md` and `rationale.md` as Version 0.5 with `phyco-v4` for `phyco-v3`, listing each
  change in `rationale.md` (spec FR-010); the security target's files are written by `mode_limits_v3.py` read for this feature,
  before the review with R as `<R4>`, `<R8>` and `<R16>`, and again once every R is known, when the family's next row,
  "Security-target review <k>", reviews the round counts, the figures computed from them and the open items (spec FR-012). The
  row "Security-target review" names both documents' chapters' SHA-256 and the files'; `candidate_log.py propose` exits 2 while
  that row does not read Approved at HEAD or the projection table does not exist, for every `proposed` entry. The open items of
  FR-012 are listed under a heading of their own in the chapter, and the owner design review's row names them.
  "L1 recorded" names this review's row and feature 004's FUT-SEC-8 result review row (ffb1425).
- **Rationale**: no candidate's result can reach the target before it is reviewed, and the review's row is a guard, not a
  note.
- **Alternatives considered**: the review after the selection (rejected by D4).

## R9. Machinery for feature 005 — protocol

- **Decision**: `protocol/evidence.py` and the writers read the active feature from one setting, `PHYCOWEB_FEATURE` (`004`
  by default, `005` for this feature), which selects the paths (`FEATURE_REL`, `REP_REL`, `RESEARCH_REL`, the spec and design
  paths), the model ID, the namespace of the development inputs and the disclaimer; every record states its feature. Feature
  004's default keeps its verdicts, paths and re-check unchanged, and a test runs feature 004's re-check at HEAD before and
  after the change with the same result. Feature 005's three logs (protocol changes, candidates, provenance) start fresh under
  `research/005/` and `reports/005-crypto-architecture-v4/`; its environment records are new, each with its row.
- **Rationale**: one code path for both features keeps feature 004's validated tools and verdict functions in force, and a
  default of `004` keeps feature 004 reproducible from HEAD.
- **Alternatives considered**: copies of the modules for feature 005 (rejected: two copies of every verdict function to keep
  in step).

## R10. The claim test for feature 005 (FR-026) — protocol

- **Decision**: `check_claims.py` adds `phyco-v4` to its model IDs and scans feature 005's documents and reports beside
  feature 004's, each hand-written document carrying the disclaimer naming `phyco-v4`; the register's rule that every other
  model stays at L0 reads "in this feature" for each feature's own model; feature 005's gate rows are read from its own spec.
  The lines of this feature's documents that state a level in a rule get allow-list entries with the policy reason.
- **Rationale**: FR-026, with feature 004's rules unchanged.
- **Alternatives considered**: a second claim test for feature 005 (rejected: two registers of one claim ladder).

## R11. The selection-bias statement (FR-024) — protocol

- **Decision**: the final report and the design rationale hold a table of every design considered in features 004 and 005, by
  family: B1 and A1 `ineligible`, with their decisions' entries (47 and 107); B2 and A2 proposed and declined, never evaluated
  (entries 49 and 109); feature 004's D4 record (`d4-choice-20261108T110819Z-b980295b`) and its selection record; and every
  design of this feature with its last decision and the feature-004 design it derives from, if any. The bias rule's
  family-wise rate is stated over this feature's tests; feature 004 ran none at w = 32.
- **Rationale**: feature 004's stop rule asks a later feature to count its candidates, results and stop.
- **Alternatives considered**: counting evaluated candidates only (rejected by D10).

## R12. The order and the decision at 16×16 (FR-014, FR-015, FR-018) — protocol

- **Decision**: per candidate, the production-width climbs run at 16×16, then 8×8, then 4×4; at each size r ascends from 1, the
  linear search before the differential at each r, as feature 004 ran them. A kind whose first search at 16×16 is capped or
  refused, with no size-independent bound read there (spec FR-015), has no established bound there, and `round_rule.py` decides
  the candidate `ineligible` at once, its other kind's searches at 16×16 included, no hour charged at 8×8 or 4×4; so does a kind
  whose sums do not pass weight 128 by R_max, as soon as the sums show it. The structural checks and bias tests keep 4×4, 8×8,
  16×16.
- **Rationale**: the size that stopped feature 004 decides first, at the least cost.
- **Alternatives considered**: 4×4 first for every kind (rejected by D6).

## R13. A feature-004 design entered again (D1, FR-023) — protocol

- **Decision**: a feature-004 design may be proposed as `v4-A<k>` or `v4-B<k>`, its `proposed` entry naming the feature-004
  candidate and operation list it derives from by path and SHA-256; it counts as evaluated, runs every kind of evidence again
  under this protocol with the constants the inherited rule gives, which for an unchanged design at an unchanged variant are
  feature 004's exactly, the rule reading one fixed stream and holding no ID, and cites its feature-004 records only as prior
  results. Its rotation amounts are those feature 004's ranking chose, its rotation search not run again, and the refused list
  it is checked against is this feature's byte copy of feature 004's (spec FR-023).
- **Rationale**: feature 004's records were made under another protocol and another model ID, and FR-023 keeps them out of
  this feature's evidence.
- **Alternatives considered**: new designs only (rejected by D1).

## R14. What is inherited unchanged

Feature 004's research items apply with the reading rules of FR-001, except: R5 (the cost model, unchanged) and R6 (the D4
choice, unchanged) read this feature's candidates; R7 (the budget) is replaced by R1 to R5 above for its values, its rules on
re-runs, tool defects and runs ended from outside kept; R12 (tool validation) keeps every feature-004 validation record in
force for the uses it covers while the tool's exact hash is unchanged; R16 (records and their hashes) gains the fields of
data-model §2 and §3; R19 (downloads) is unchanged, no download being planned. Every other item, R1 to R4, R8 to R11, R13 to
R15, R17 and R18, applies as written.
