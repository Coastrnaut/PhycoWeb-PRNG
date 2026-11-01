# Implementation Plan: Cryptographic Architecture and phyco-v3 Design

**Branch**: `004-crypto-architecture-v3` (directory only; no git branch, as in the spec's
Assumptions) | **Date**: 2026-11-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-crypto-architecture-v3/spec.md` (approved
2026-11-01, with D1–D10 as clarified).

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

## Summary

The feature runs in the spec's order, and each step needs the one before it:

1. **FUT-SEC-8 first (US1)**: a new C tool, `fast/seed_search.c`, checked word for word against
   both `phyco-v2` golden vector files, sweeps all 2³² candidates for the last two seed words of
   three development targets, under an hour on 32 threads (research R2). The owner reviews the
   result (⛔) before any `phyco-v3` key-loading code exists.
2. **Security target (US2)**: chapter 1 of the design document states the properties sought,
   s = 128, the 256-bit key and 128-bit nonce, threats T1–T11, every generic bound per size, and
   the keyed-duplex theorem with its preconditions. The output limits follow from the theorem at
   a target advantage of 2⁻⁶⁴ (R9, R10). Reading each theorem paper is a download that needs
   permission; R19 lists each file with its source, size and licence.
3. **Design (US3)**: every candidate Π is written once as an operation list made only of
   invertible updates, so it is bijective by construction (R11). From that list come the
   evaluators, the inverse, dependency matrices, the cost model and the trail models. After
   selection come a hand-written standard-library model, `phycoweb/model_v3.py`, constants from
   a committed script, vectors at every size (R8), constructed-state vectors and a second
   transcription from a separate session (R17).
4. **Evidence (US4)**: tools first re-find known results (S12–S15 and the FUT-SEC-8 recovery on
   `phyco-v2`; published SPECK32, PRESENT and SPARKLE values, R12). Then structural checks
   (R13), the frequency and avalanche tests (R4) and trail bounds within a fixed budget per
   candidate (R7). The D4 score (R5, R6), the round rule and the stop rule decide.
5. **Review and freeze (US5)**: design rationale, review package, ⛔ owner design review,
   external review recorded as done or not arranged, ⛔ design freeze, then the final report
   with FUT-SEC-7 open for feature 007.

### Values this plan fixes before first use

The spec leaves these values to the plan. From plan approval they belong to the pre-registered
design protocol and may only become stricter (FR-044).

| Item left to the plan | Value fixed here | Research | Stricter means |
|-----------------------|------------------|----------|----------------|
| Development inputs (FR-040) | Key, nonce, personalization string, reseed input and test state i = SHA-256 of the ASCII string `phycoweb-004/dev/<kind>/<i>` (test states: `phycoweb-004/dev/state/n<n>w<w>/<i>/<j>`); uniform controls under `phycoweb-004/control/`; the loader refuses every other namespace; fingerprints checked at load; no held-out set | R3 | no change at all |
| Inputs per bias measurement (bias rule) | N = 2²⁰ instantiation states per claimable size, through Π and Π⁻¹, S = 2b bits per round count; the avalanche measurement of FR-037 also feeds R_dist: N_a = 2¹³ states per flipped bit, threshold 0.005/(128·S_A) with S_A = 2·\|F\|·b, so it adds at most 0.005 per size to the chance of a false firing; controls with the same counts | R4 | N, N_a and F only grow |
| Operation-count cost model (D4) | 6-input LUTs per node and round: 0 for rotations, constant shifts and wiring; w per bitwise word operation with fan-in k ≤ 6; w·⌈(k − 1)/5⌉ above; w and one carry chain per addition or subtraction; no fusion | R5 | no change after the first score |
| Analysis budget per candidate (stop rule) | 48 h of trail searches (at most 8 h per search instance), 6 h of structural checks, 12 h of frequency and avalanche tests; one re-run per evidence kind, only after a recorded tool defect, inside the budget | R7 | every budget only falls |
| Vector lengths at large sizes (FR-036) | The same at every size: 16 Π and Π⁻¹ inputs with 4 traced round by round; 2 development keys × 10,000 words for the mode; a SHA-256 digest of 2²⁰ words; no shortening at 8×8 or 16×16 | R8 | lengths only grow |
| Target advantage for the output limits (FR-007) | ε = 2⁻⁶⁴ at N = 2¹²⁸ offline evaluations of Π or Π⁻¹, with every online quantity at its limit; per-request cap 2¹⁹ bits | R9 | ε and the cap only fall; N only rises |

### Other choices, answered on review

On 2026-11-01 the owner asked the planner to settle the five choices the first draft flagged for
checking. All five are kept, and three gain rules:

| Choice | Answer | Research |
|--------|--------|----------|
| Per-request cap | Kept: the smaller of the per-instantiation limit and 2¹⁹ bits, SP 800-90A's largest request. A state compromised in mid-request exposes the request's earlier blocks through Π⁻¹, back to the last forget call, and the cap bounds that window | R9 |
| One moment for the D4 choice | Kept: once, by code, over the entered set recorded before the first score. Added: an exact tie waits for R at 4×4 of both representatives, because the spec's first tie-break needs it; if neither family has a scored candidate, selection takes the eligible candidate with the smallest R at 4×4 from either family | R6 |
| One key per `Generator` | Kept and tightened: zeroize is final, and every online quantity the bound counts has a limit and a counter. Across objects, processes and devices, the per-key limits and u are usage rules the design document states for the caller | R9; model contract |
| Checks beyond the spec | Kept. The avalanche measurement is FR-037's own; feeding R_dist is the stricter part. Its threshold now covers up to 128 round counts per size, with N_a = 2¹³, so it fires by chance less often (a false raise of R at R = 32 falls from about 38% to 23%) and still detects smaller biases (0.037 instead of 0.047 at 4×4). The symmetry check keeps reflections and compositions and adds word rotations | R4, R13 |
| A separate build file | Kept: `fast/seed_search.mk`. The feature-003 freeze hashes the stream's source and binary, not `fast/Makefile`, but a new target there could rebuild the frozen binary | R2 |

The same review fixed the set of trail tools when the first trail search starts (R12), added a
projection before every heavy run (R7), listed every download with its name, source, size and
licence (R19), and brought the status of the strategy note and of security.md §22 up to date
(security.md 2.10).

The plan also settles the spec's edge case on large records: up to 10 MB compressed is
committed, larger outputs stay local with their SHA-256 and the regenerating command (R16).

## Technical Context

**Language/Version**: Python 3.10.11 (Windows) and 3.14.4 (WSL venv `~/.venvs/phycoweb`). The
model `phycoweb/model_v3.py` and `protocol/devinputs_v3.py` use the standard library only and
keep to Python 3.8 grammar. C99 for `fast/seed_search.c` and any exhaustive check too slow in
Python (gcc 15.2.0 in WSL).

**Primary Dependencies**: no new ones. numpy 2.2.6 / 2.5.4 for batch evaluation and dependency
matrices (explicit `uint64` dtypes); scipy 1.15.3 / 1.18.1 for exact binomial tails and
`scipy.optimize.milp` (HiGHS) for active-box counting, analysis only. Optional tools and papers
are candidates only (R19); each download needs the owner's permission for that file.

**Storage**: JSON and gzip JSON records under `reports/004-crypto-architecture-v3/`; the
hash-chained candidate log `research/004/candidates.jsonl`; vectors under `vectors/phyco-v3/`;
local-only large outputs listed by hash (R16).

**Testing**: `python -W ignore -m unittest discover -s tests -t .` on both platforms; WSL-only
tests (the C tool) skip cleanly on Windows; property-based tests only if Hypothesis 6.168.5 is
approved (R19; FR-058).

**Target Platform**: Windows 11 and Ubuntu on WSL2, i9-14900K, 32 logical CPUs, 31 GiB RAM.
The design targets the Arty A7-100T at 200 MHz, which this feature does not build for.

**Project Type**: design and research tooling inside the existing single Python project; no
RTL.

**Performance Goals**: FUT-SEC-8 under 1 h of wall time for three targets; each candidate
within the 66 h of R7; each vector file in at most an hour; model speed measured and recorded
(FR-036).

**Constraints**: no change to `phyco-v2`, `lut-v1`, `sp80022`, the feature-002 and feature-003
protocols, their seed sets, or any frozen file, `fast/phyco_stream.c` and `fast/Makefile`
included; development inputs only; the protocol only becomes stricter; no key-loading code
before the FUT-SEC-8 review; heavy runs never overlap; no download without per-file permission;
the agent never commits or pushes.

**Scale/Scope**: three claimable sizes (b = 1,024, 4,096 and 16,384 bits at w = 32), research
size 2×2 (3×3 only with a three-colour schedule); at most six candidates; 3 × 2³² sweep
candidates; 69 functional requirements and 20 success criteria.

No item is left as NEEDS CLARIFICATION: research R1–R19 settle every open choice.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design (below).*

| Principle | Check | Status |
|-----------|-------|--------|
| I. Integer, fully specified arithmetic | Π and the mode use only addition and subtraction modulo 2^w, XOR, AND, OR, NOT, constant rotations and logical shifts (re-decided feature-002 FR-001), all sign-free (FR-055). The 32-bit unsigned lanes are ratified by the spec (D3, FR-018), as Principle I allows. No floating point in the model; numpy and scipy only in analysis. The design document states width, signedness, wrap rule, shift kind and order of every operation (FR-027) | Pass |
| II. Bit-accurate reference model | `phycoweb/model_v3.py` is the golden model, marked model-only, RTL-pending (FR-035); golden vectors and known-answer tests per size, 2 keys × 10,000 words for the mode (R8); a second transcription agrees step by step (FR-057) | Pass |
| III. Synchronous, localized RTL | No RTL. The design rules serve it: all state registered, neighbour links only on a folded torus, no multiplication (0 DSP), generics n and w, at most two carry chains per stage (FR-018, FR-025) | N/A (designed for; see Complexity Tracking for the absorption and output trees) |
| IV. Evidence-based claims | No claim. The bias rule, its control and its counts are fixed before any measurement (R4); every result is reported; no re-run except after a recorded tool defect; findings classified (FR-060); disclaimer everywhere. SP 800-22 and the held-out programme belong to feature 007, so FUT-SEC-7 stays open | Pass |
| V. Reproducibility, archival, provenance | Inputs from public strings (R3); every record holds the §17.2 fields (R16); `phyco-v2` archived with SHA-256 in `baseline/phyco-v2/` (FR-042); pinned requirements and line endings (R18); a re-check script recomputes every verdict | Pass |
| VI. Specification before implementation | Spec approved 2026-11-01; this plan awaits approval. Candidates are research objects under the approved rules; the reference model is written from the design document after selection, and the design is frozen only after the owner design review | Pass |
| VII. Requirements traceability | Tasks will cite FR and SC identifiers; the spec's traceability tables map FUT-SEC, FUT-GRID and FUT-HW; the final report lists every requirement without evidence as open | Pass (enforced in tasks) |
| VIII. Human review gates | Plan approval, each download, FUT-SEC-8 review, go-ahead for the second transcription, owner design review, design freeze, final result review | Pass |
| IX. Outward actions | The agent never commits, pushes or publishes; downloads only with per-file permission; sending the review package is the owner's action | Pass |
| Security Policy | FUT-SEC-1 to FUT-SEC-9 carried and traced (FR-049); key 256 bits and reachable secret state ≥ 256 bits at every claimable size (FR-009, FR-010); no claim, only a target at L1; restriction stated wherever use is described (FR-050) | Pass |
| Technical constraints | Python 3.8+ for the model (standard library only); numpy with explicit dtypes; scipy for analysis only; a test checks that the model imports no analysis dependency. Adds C tooling for the sweep | Justified (Complexity Tracking) |
| Workflow and phase reporting | This plan has its Constitution Check; the change-completion items still open at the end (statistical evaluation, RTL) are reported (FR-052); every phase ends with the constitution's report | Pass |

**Post-design re-check**: research R1–R19, the data model and the contracts add no new
violation. What they add is stricter than the spec or settles what it leaves open: the avalanche
measurement as a source of R_dist (R4); reflections, compositions and word rotations in the
symmetry check (R13); a fixed moment for the D4 choice, with rules for a tie and for no scored
family (R6); a per-request cap, a final zeroize and a counter for every online quantity (R9); a
fixed set of trail tools (R12); and a projection before every heavy run (R7). The numpy
interpreter of the operation lists is analysis code that the model never imports (R11, R17).

## Project Structure

### Documentation (this feature)

```text
specs/004-crypto-architecture-v3/
├── spec.md                  # approved 2026-11-01
├── plan.md                  # this file
├── research.md              # R1–R19
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── model-v3-api.md      # the model's interface, call sequence and refusals
│   └── cli.md               # every new script and tool, with exit codes
├── checklists/requirements.md
├── design.md                # written in tasks; the phyco-v3 design document, frozen
├── rationale.md             # written in tasks; the design rationale (security.md §8)
└── tasks.md                 # /speckit-tasks
```

### Source Code (repository root)

```text
fast/
├── seed_search.c             # new: FUT-SEC-8 sweep with its own design-1.0 step (R2)
└── seed_search.mk            # new: builds fast/build/seed_search; fast/Makefile unchanged

phycoweb/
├── model_v3.py               # new: phyco-v3 model, standard library only (R17)
└── constants_v3.py           # GENERATED by scripts/gen_constants_v3.py (R15)

protocol/
├── devinputs_v3.py           # new: development inputs and uniform controls (R3)
├── evidence.py               # new: the one writer of evidence records (R16)
├── candidates.py             # new: append-only, hash-chained candidate log (FR-041)
├── design_freeze.py          # new: freeze create and validate (FR-043)
├── claims.json               # new: claim and evidence register (FR-069)
└── disclaimer.py             # gains DESIGN_DISCLAIMER; DISCLAIMER unchanged (FR-068)

research/004/
├── ir.py                     # operation lists, interpreters, inverse (R11)
├── candidates/               # A1–A3 and B1–B3 at most, one module each
├── tools/                    # bijectivity, dependency, bias, symmetry, invariants, costmodel
│   └── trails/               # box tables, MILP active-box counting, ARX branch-and-bound
├── validation/               # re-finding S12–S15, FUT-SEC-8, published trail values
└── candidates.jsonl          # the candidate log

scripts/
├── archive_phyco_v2.py       # baseline/phyco-v2/ and its MANIFEST.json (R18)
├── fut_sec8.py               # US1 driver (R2)
├── validate_tool.py          # one tool validation record (FR-039)
├── evidence_v3.py            # one evidence kind for one candidate (R4, R12, R13)
├── d4_choice.py              # the D4 score and choice (R5, R6)
├── round_rule.py             # R, eligibility, selection, stop rule
├── mode_limits_v3.py         # the theorem's bound at the limits (R9)
├── gen_constants_v3.py       # constants and their checks (R15)
├── gen_vectors_v3.py         # vectors and known-answer tests (R8)
├── gen_constructed_v3.py     # constructed-state vectors (FR-054)
├── design_freeze.py          # create and validate the freeze
├── recheck_004.py            # recomputes every verdict (FR-065)
└── check_claims.py           # register against README, security.md, disclaimers

tests/
├── test_devinputs_v3.py
├── test_ir.py
├── test_costmodel.py
├── test_tools_004.py         # tool validations on known results
├── test_seed_search.py       # WSL; skips on Windows
├── test_model_v3.py          # FR-058's list, refusals, call sequences
├── test_vectors_v3.py
├── test_v3_transcription.py  # model against tests/v3_reference.py, step by step
├── v3_reference.py           # second transcription, separate session (FR-057)
├── test_protocol_004.py      # candidate log, budgets, stop rule, freeze
├── test_baseline_v2.py       # archive against manifest and live files
└── test_claims.py            # FR-069

vectors/phyco-v3/             # Π and Π⁻¹ KATs, mode vectors, digests, constructed states
baseline/phyco-v2/            # byte-exact copies and MANIFEST.json (FR-042)

reports/004-crypto-architecture-v3/
├── fut-sec-8/                # demonstration record, tool check, review
├── validation/               # tool validation records
├── candidates/<id>/          # evidence per candidate
├── d4/                       # the D4 choice and its inputs
├── security-target/          # bound at the limits, generic-bound table
├── freeze/                   # freeze record
├── review-package/
├── provenance.jsonl          # FR-067
└── phase-report.md
```

**Structure Decision**: extend the single project. Feature-002 and feature-003 files are used
read-only: `phycoweb/model_v2.py`, `protocol/seedsets.py` for the FUT-SEC-8 targets, the golden
vectors and `fast/lut_table.h`. `fast/phyco_stream.c`, `fast/Makefile` and the built
`fast/build/phyco_stream` stay untouched, because the feature-003 freeze hashes the stream's
source and binary.

## Phases and gates (for /speckit-tasks)

1. **Setup**: directories; `.gitattributes` pins and the `.gitignore` lock entry; corrected
   `requirements.txt`; `DESIGN_DISCLAIMER`; `protocol/devinputs_v3.py` with fingerprints;
   `protocol/evidence.py`; the provenance log; the `phyco-v2` archive (FR-042). (The status of
   the strategy note and of security.md §22 rows 5a and 5a.1 was updated during planning, in
   security.md 2.10.)
2. **US1 FUT-SEC-8**: `fast/seed_search.c` and its vector check; the sweep, a heavy run →
   demonstration record → ⛔ **FUT-SEC-8 result review**. No key-loading code before it.
3. **Tool validation**: re-find S12–S15 and the FUT-SEC-8 recovery on `phyco-v2`; trail tools
   on published values, ⛔ **download permission** for each paper of R19 unless the owner
   provides the values. The set of trail tools is fixed when the first trail search starts (R12).
4. **US2 security target**: design document chapter 1, the mode chapter with every
   precondition, `mode_limits_v3.py` at ε = 2⁻⁶⁴. ⛔ **download permission** for the theorem
   papers and AIS 20/31 3.0 (R19).
5. **US3 and US4 candidates**: operation-list framework and cost model; A1 (the ARX-box design)
   and at least one Boolean candidate; the entered set recorded; reduced-width bounds; the D4
   choice; production-width bounds, structural checks, frequency and avalanche tests; R by the
   round rule; eligibility; the stop rule. One heavy run at a time, each projected first (R7).
6. **US3 model and vectors**: the design document complete; constants; `model_v3.py`; vectors
   and known-answer tests on Windows and Linux; constructed states; refusals; tests.
7. **Second transcription**: ⛔ **owner go-ahead**; a separate session writes
   `tests/v3_reference.py`; step-by-step agreement with the common-mode caveat.
8. **US5**: rationale; security.md 2.11 with the §20.1 decision; review package; ⛔ **owner
   design review**; external review recorded as done or not arranged; the owner commits the
   feature files (Principle IX); ⛔ **design freeze**; L1 recorded when its gate passes.
9. **Polish**: README; claim-register test; re-check of every verdict; final phase report → ⛔
   **final result review**.

## Risks

- **Stop**: no candidate may establish R_bound at the production width within its budget, most
  likely at 16×16 where the trail models are largest. A stop is a valid outcome and is reported
  with what was reached (stop rule).
- **Theorem mismatch**: forget or reseed may not match a published theorem exactly. The call
  then takes the theorem's form, or the feature stops; a mode without a theorem is never adopted
  (R10).
- **Downloads not approved**: without the papers the mode chapter stays "unverified" and L1
  cannot be recorded; without published values the trail tools stay unvalidated (R19). Two of
  the papers sit on hosts that refuse scripted requests, so they need the owner's browser.
- **Run times**: from a timing probe (R4), the frequency and avalanche tests take about 3 h per
  candidate at R = 32, exhaustive bijectivity about 1 h and a long-run digest under a minute.
  Each heavy run is projected on the candidate itself first and starts only if it fits its
  budget row (R7); counts and lengths are never reduced to fit.
- **False raises of R**: the spec's bias rule bounds its error per size and round count, so on a
  sound Π a chance firing raises R with probability about 21% at R = 32, or 23% with the
  avalanche test (R4). It can only raise R, and the rule cannot be loosened (FR-044); the final
  report states it.
- **Selection bias**: choosing among up to six candidates on development inputs is stated in the
  final report (FR-041).
- **Common mode**: the model and the second transcription both read one design document, and
  both may be written by AI sessions; agreement is reported with the caveat of security.md §10.2.
- **A coarse cost model**: no packing or fusion; it serves only the D4 choice and the FR-026
  estimate, and the board numbers belong to feature 008.
- **Run contention**: every heavy run takes the lock (R16) and runs alone.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| C tooling beyond the Python and numpy stack (Technical Constraints) | The sweep costs about 2³² × 257 steps per target; a C evaluator generated from an operation list is added only if a heavy run's projection does not fit its budget (R7) | The Python model runs at about 2 × 10⁵ steps/s, about 64 days per target; lowering counts to fit a budget is not allowed |
| A second copy of the design-1.0 step, in `fast/seed_search.c` | `fast/phyco_stream.c` stays unchanged, because the feature-003 freeze hashes its source and binary | Editing or rebuilding it would touch frozen evidence; the copy is checked against both golden vector files before any sweep |
| Absorption and output trees over the rate lanes, which are not neighbour links (Principle III) | FR-018 requires registered trees for absorption and output | Neighbour-only paths would take about n steps per block; the trees are fully registered, and the design document gives the timing justification Principle III asks for |
