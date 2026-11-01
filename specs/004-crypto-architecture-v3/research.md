# Research: Cryptographic Architecture and phyco-v3 Design

Feature `004-crypto-architecture-v3`. Date: 2026-11-01. Spec approved 2026-11-01, with D1–D10 as
clarified. Every decision below is fixed before any design result exists. From plan approval,
the values marked **protocol** belong to the pre-registered design protocol and may only become
stricter (FR-044). Each such value states what "stricter" means for it. Where a fact can only be
confirmed once a paper or tool is on disk, the decision says so and states what happens if it
turns out differently. No such fallback may loosen a rule.

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

## R1. Where things run

- **Decision**: the model, the vectors, the evidence scripts and the statistics run on Windows 11
  with Python 3.10.11, numpy 2.2.6 and scipy 1.15.3. C tools (the FUT-SEC-8 search tool, and
  exhaustive checks if Python is too slow) are built and run in WSL2 Ubuntu with gcc 15.2.0, and
  the Linux reproduction of every vector (SC-009) uses the WSL venv `~/.venvs/phycoweb`
  (Python 3.14.4, numpy 2.5.4, scipy 1.18.1). The machine is the i9-14900K with 32 logical CPUs
  and 31 GiB RAM used in feature 003.
- **Rationale**: these are the environments of security.md §19, so no new tool is needed to
  start. There is no C compiler on Windows. Two Python versions on two platforms test FR-035's
  determinism across platforms and versions.
- **Alternatives**: everything in WSL (would lose the Windows half of SC-009); a Windows
  compiler (an extra download for no benefit).

## R2. The FUT-SEC-8 demonstration tool (FR-001 to FR-003)

- **Decision**:
  - A new C program, `fast/seed_search.c`, holds its own copy of the design-1.0 step and reads
    the existing generated `fast/lut_table.h`. `fast/phyco_stream.c` stays unchanged.
  - `--check-vectors` reproduces both committed `phyco-v2` golden vector files, all 10,000 words
    of each, and must pass before any sweep (FR-002). A mismatch stops the run.
  - The sweep splits s₂ = 0…65535 over 32 POSIX threads. For each (s₂, s₃) it initialises the
    state, runs the 256-step warm-up and compares output words 1, 2 and 3 with the target's,
    dropping a candidate at its first mismatch. It counts the matches after one, two and three
    words, lists every match after three, and reports steps, time and steps per second as JSON.
  - `scripts/fut_sec8.py` takes the targets from `protocol.seedsets.load("dev", allow=["dev"])`
    (the first three seeds), computes the attacker's observations with `phycoweb/model_v2.py`,
    runs the tool once per target, separates any extra three-word match with the fourth word
    (Edge Cases), and writes the demonstration record (data-model §5).
  - Expected cost, from the spec: about 2³² × 257 steps per target, 3.6 core-hours at
    8.5 × 10⁷ steps/s, so under an hour of wall time for three targets on 32 threads. It is a
    heavy run (FR-045).
- **Rationale**: the Python model runs at about 2 × 10⁵ steps/s, so one target would take about
  64 days. Changing `fast/phyco_stream.c`, or rebuilding its binary, would touch files whose
  hashes the feature-003 freeze records. The freeze does not hash `fast/Makefile`, but a new
  target there could rebuild the frozen binary, so the tool has its own source and its own build
  file, `fast/seed_search.mk`, and `fast/Makefile` is left alone. The golden-vector check makes
  the copied step trustworthy.
- **Alternatives**: extend `phyco_stream.c` (rejected, as above); a Python sweep (too slow).

## R3. Development inputs (FR-040) — protocol

- **Decision**: every key, nonce, personalization string, reseed input and test state of this
  feature is derived from a public ASCII string by SHA-256, in `protocol/devinputs_v3.py`
  (standard library only):

  | Input | String hashed (i in decimal, no leading zeros) | Value |
  |-------|-----------------------------------------------|-------|
  | Key i | `phycoweb-004/dev/key/<i>` | the 32-byte digest |
  | Nonce i | `phycoweb-004/dev/nonce/<i>` | the first 16 bytes |
  | Personalization string i | `phycoweb-004/dev/pers/<i>` | the first min(m, 32) bytes, where m is the design's maximum length (FR-006); the empty string is a separate, named input |
  | Reseed input i | `phycoweb-004/dev/reseed/<i>` | the 32-byte digest |
  | Test state i at n, w | `phycoweb-004/dev/state/n<n>w<w>/<i>/<j>` for j = 0, 1, … | the digests concatenated; the first b bits, read most significant bit first into w-bit lanes in the design document's lane order |
  | Uniform control | the same strings with `control` in place of `dev` | as above |

  - A measurement with N inputs uses i = 0…N − 1. The fingerprint of each kind (and of the state
    kind at every supported n and w), the SHA-256 of the hex values for i = 0…99, one per line,
    is recorded in the module and checked at load, as `protocol/seedsets.py` does.
  - The loader accepts only the namespaces `dev` and `control`. Every evidence script takes its
    inputs from the loader and records the namespace, kind and index range (FR-061).
  - No held-out set exists. Feature 007 defines held-out keys that cannot be computed before its
    freeze; this requirement is carried to it (FR-040).
  - SHA-256 here is protocol bookkeeping. It never appears in Π, the mode or key loading (D6).
- **Stricter means**: nothing may change; the rule is frozen at plan approval.
- **Rationale**: the same pattern as feature 002 (`phycoweb-002/<set>/<i>`), with a feature prefix
  that keeps the two families of inputs apart. Public strings make every input reproducible and
  show that no input was chosen after a result.
- **Alternatives**: OS random keys (not reproducible); one stream cut into fields (a change to one
  field length would shift every later input).

## R4. Inputs per bias measurement; the frequency and avalanche tests (bias rule; FR-037)

- **Decision** (**protocol**):
  - **Frequency test (the spec's bias rule).** At each claimable size (4×4, 8×8, 16×16; w = 32),
    N = 2²⁰ development inputs: for i = 0…2²⁰ − 1, the state that instantiate gives to its first
    call of Π for key i and nonce i with the empty personalization string. Each input runs
    through rounds 1…R_cur of Π, and separately of Π⁻¹. After every round the ones in each state
    bit are counted. At a size and round count, the bits tested are the b bits after Π and the b
    bits after Π⁻¹, so S = 2b. A bit fires if its two-sided binomial p-value (p = 1/2; twice the
    smaller tail, at most 1, computed exactly) is at most 0.005/S.
  - **Avalanche test.** FR-037 asks for it; using it as a source of R_dist is stricter than the
    spec. For each flipped input bit j in a set F, N_a = 2¹³ test states x (kind `state`, R3);
    after every round r = 1…R_cur the difference Π^r(x) ⊕ Π^r(x ⊕ e_j) is counted bit by bit,
    and the same for Π⁻¹. F holds every state bit at 4×4 (|F| = 1,024) and the 2w = 64 bits of
    each node on the main diagonal at 8×8 and 16×16 (|F| = 512 and 1,024). With S_A = 2·|F|·b,
    a difference bit fires if its two-sided binomial p-value is at most 0.005/(128·S_A). The
    factor 128 spreads the test's 0.005 over up to 128 round counts at a size, so this extra test
    adds at most 0.005 per size, not per round count, to the chance of a false firing (below). A
    difference bit that never flips fires, so a dependency that is never observed raises R_dist.
  - **Rounds measured.** R_cur is the candidate's current value of the round rule. If a test
    fires at a round count r with 2r > R_cur, R_cur becomes 2r and the measurement extends to it,
    until no firing round count raises R.
  - **Uniform control.** Before its first use at each size, each test is applied once, with the
    same counts and the same threshold, to uniform control inputs: 2²⁰ control states, and
    N_a·|F| XOR differences of two independent control states. If a test fires on its control,
    the bias evidence of that size is inconclusive and the rule is not loosened (Edge Cases).
    Inconclusive bias evidence leaves R_dist unestablished at that size, which makes the
    candidate ineligible unless a recorded tool defect is fixed and the one re-run that R7 allows
    is conclusive.
  - **Sensitivity**, computed for this plan with scipy 1.15.3, for the bias |f − 1/2| of one bit
    that fires with probability 1/2 (and 0.9):

    | Size | Frequency, N = 2²⁰, threshold 0.005/S | Avalanche, N_a = 2¹³, threshold 0.005/(128·S_A) |
    |------|---------------------------------------|-------------------------------------------------|
    | 4×4 | 0.0023 (0.0029), S = 2¹¹ | 0.037 (0.044), S_A = 2²¹ |
    | 8×8 | 0.0024 (0.0031), S = 2¹³ | 0.038 (0.045), S_A = 2²² |
    | 16×16 | 0.0026 (0.0032), S = 2¹⁵ | 0.039 (0.046), S_A = 2²⁵ |

    The first draft's avalanche test, N_a = 2¹² at 0.005/S_A, caught 0.047 (0.057) at 4×4, so the
    test now detects smaller biases as well as firing by chance less often.

  - **Engine.** The counts come from the batch interpreter of R11 on numpy `uint64` arrays in
    batches of 2¹⁶. The verdict is computed by code from the saved counts (FR-065).
  - **False firing.** On uniform inputs the frequency test fires at a size and round count with
    probability at most 0.005 (the spec's rule), and the avalanche test at most 0.005 per size
    over all its round counts. A false firing can only raise R, but it does raise it. Only round
    counts r with 2r > R matter, ⌈R/2⌉ of them per size, so a Π whose outputs look uniform after
    a few rounds has R raised by chance with probability about 1 − 0.995^(3⌈R/2⌉): 11% at
    R = 16 and 21% at R = 32, or 23% with the avalanche test. With the avalanche threshold at
    0.005/S_A per round count, as first drafted, it would be 38% at R = 32. A raised R adds round
    counts, so a raise can repeat, and repeated raises can use up the budget of R7, which ends
    the measurement as inconclusive. The spec's rule cannot be loosened (FR-044), so this cost is
    accepted and stated in the final report.
- **Stricter means**: N and N_a may only rise, and F may only grow; S and S_A always count the
  bits tested; the thresholds stay 0.005/S and 0.005/(128·S_A).
- **Rationale**: Π maps uniform inputs to uniform outputs at every round count, so a frequency
  test needs structured inputs. Instantiation inputs are the structured inputs an attacker
  actually gets (FUT-SEC-5): about 384 varying key and nonce bits, the rest fixed. A timing probe
  on this machine (2026-11-01; Python 3.10.11, numpy 2.2.6) measured 0.21 ns per numpy word
  operation in batches of 2¹⁶ and 0.66 ns per counted bit. At R = 32 and 64 numpy operations per
  node and round, the frequency test then takes about 0.4 h per candidate over the three sizes
  and both directions, and the avalanche test about 2.6 h, mostly counting bits; a raise of R to
  64 doubles both, still inside the 12 h of R7. The avalanche test complements the exact
  dependency matrices (R13), and its budget sets N_a and F.
- **Alternatives**: uniform inputs (no information for a permutation); N = 2¹⁶ (detects only
  biases 4 times larger); N = 2²⁴ (16 times the cost); every input bit at 16×16 (2²⁷ pairs per
  direction, 16 times the diagonal set, which would not fit the 12 h of R7); the avalanche test
  at 0.005/S_A per round count, as first drafted (38% instead of 23% at R = 32); N_a = 2¹² at
  the per-size threshold (half the cost, but 0.053 instead of 0.037 at 4×4).

## R5. The operation-count cost model (D4; FR-026) — protocol

- **Decision**: LUTs per node and round are counted from the candidate's operation list (R11) on
  6-input LUTs, the Arty A7-100T's fabric, with no packing or fusion between listed operations:

  | Operation on w-bit words | LUTs | Carry chains |
  |--------------------------|------|--------------|
  | Rotation or shift by a constant; wiring between nodes; a register stage | 0 | 0 |
  | Bitwise function in which each output bit depends on k ≤ 6 input bits (constant bits count as inputs), such as XOR, AND-NOT or a χ-like row | w | 0 |
  | Bitwise function with k > 6 input bits per output bit | w · ⌈(k − 1)/5⌉ | 0 |
  | Addition or subtraction modulo 2^w of two words | w | 1, of w bits |

  - The source of the round constants (a counter or an LFSR) is not counted.
  - An operation shared by two nodes counts once, at the node that computes it.
  - Serial carry chains per round = the most additions on any dependency path within one round
    (the D4 tie-break). Per pipeline stage, the same count must be at most 2 (FR-025).
  - Flip-flops (2w per node, plus pipeline registers) are reported but not scored.
  - Cost per output bit (FR-026) = LUTs per node and round × n² × R / r, in LUT-cycles per
    output bit, for an implementation that computes one round per clock cycle.
  - `research/004/tools/costmodel.py` computes every number from the operation list, and a test
    checks the table above on hand-counted examples.
- **Stricter means**: the model cannot change once the first candidate is scored.
- **Rationale**: the model must be fixed before scoring and simple enough to compute by code. Both
  families are counted by the same table, so neither gains from a counting choice. Packing and
  fusion depend on synthesis; Vivado post-route numbers belong to feature 008 (FUT-HW-2).
- **Alternatives**: a LUT6_2 packing model (closer to the real fabric, but more rules to argue
  about before any result); gate-equivalent counts (not the FPGA's resource).

## R6. The D4 score and the candidates (FR-022)

- **Decision** (**protocol**):
  - Families: A = ARX, B = Boolean. Candidates are A1…A3 and B1…B3, no more (stop rule).
    Candidate A1 is the long-trail design: each node's two lanes form one 2w-bit ARX-box (64 bits
    at w = 32), with a local linear layer between nodes and the bound for Π from counting active
    boxes (FR-022; Dinu et al., 2016). Only the method is reused (D6).
  - **When**: the choice is computed once, by code, after every candidate entered for it has
    been scored, and before the production-width analysis of the chosen family starts. At least
    one candidate per family is entered, and the entered set is recorded in the candidate log
    before the first score. A candidate added later counts towards the stop rule but does not
    change the recorded choice.
  - **Where**: at 4×4, at the widest reduced width, 16 or else 8, at which at least one entered
    candidate of each family has both a differential and a linear trail bound for a common
    number of rounds of at least 2; r* is the largest such common number. Only candidates with
    both bounds at r* rounds are scored.
  - **Score**: with W_D and W_L the −log₂ of the bounds on the best differential trail
    probability and on the best linear trail's squared correlation over r* rounds, and L the
    LUTs per node and round of R5 at that width:

    ```text
    score = (min(W_D, W_L) / r*) / L
    ```

  - Each family's representative is its scored candidate with the highest score, and the family
    with the higher representative is chosen. Scores are compared exactly, without logarithms:
    bounds are kept as rational numbers, and candidate A scores higher than B when
    p_A^(L_B) < p_B^(L_A), where p is the weaker (larger) of a candidate's two bounds.
  - **Exact tie.** The spec's first tie-break, the smaller R, needs R_bound at the production
    width, which does not exist yet at the moment of the choice. The choice then waits: both
    representatives go on to the production-width analysis within their own budgets, and
    `d4_choice.py --tie` applies the spec's tie-breaks in order (the smaller R at 4×4, then fewer
    serial carry chains per round, then the owner's recorded choice) once both values of R at 4×4
    exist. A representative found ineligible first loses the tie.
  - **One family scored.** That family is chosen by default, and the record says so.
  - **Neither family scored.** No family is chosen, and the record says that D4 was not
    computable. Selection then takes the eligible candidate with the smallest R at 4×4 from
    either family, with a tie going to the owner's recorded choice; the stop rule still applies.
- **Stricter means**: nothing may change after the first score.
- **Rationale**: the D4 rule says "on reduced widths" but not when, at which width or over how
  many rounds, and without a common round count the weights per round are not comparable. The
  widest width both families reach is the closest to production, and fixing the moment of the
  choice keeps a later candidate from reopening it.
- **Alternatives**: w = 32 directly (bounds may not exist there for both families early);
  scoring at 2×2 (a research size whose diffusion differs from the claimable sizes).

## R7. The analysis budget per candidate (stop rule) — protocol

- **Decision**: per candidate, in wall-clock hours on the machine of R1, one heavy run at a time
  (FR-045):

  | Work | Budget |
  |------|--------|
  | Trail-bound searches of every kind, width and size together (box tables, box-trail searches, active-box or active-S-box counting, solver cross-checks) | 48 h; each search instance at most 8 h |
  | Structural checks (inverse tests, exhaustive bijectivity, dependency matrices, symmetry and invariant checks) | 6 h |
  | Frequency and avalanche tests with their controls (R4) | 12 h |

  - A search that reaches its cap gives no bound, and its record says "inconclusive"
    (security.md §16.3). A candidate without an established R_bound at every claimable size
    within its budget is ineligible.
  - A run may be repeated only after a tool defect is found and recorded, once per kind of
    evidence, and its time counts against the same budget.
  - Each candidate's log entry records the hours used per row (data-model §3).
  - **Projection before every heavy run.** A timing run of at most 60 s on the candidate itself
    projects the run's hours from the counts of R4, R8 and R13. The run starts only if the
    projection fits the hours left in its budget row. Otherwise the engine is made faster first,
    with more worker processes or with a C evaluator generated from the same operation list and
    checked against the numpy interpreter on the committed vectors. Counts and budgets never
    change to make a run fit, and the record keeps the projection beside the time used.
  - The most the feature can spend is six candidates × 66 h, about 16.5 days of runs.
- **Stricter means**: every budget may only be lowered (stop rule).
- **Rationale**: the stop rule needs a budget that ends "evaluated". Solver time dominates; 8 h
  per instance keeps one stuck search from consuming a candidate's budget. A cap on the feature
  as a whole follows from the three-candidate limit.
- **Alternatives**: no budget (the stop rule could never fire); a budget in core-hours
  (multithreaded and single-threaded solvers would not compare).

## R8. Vector lengths at every size, large sizes included (FR-036, FR-054, FR-058) — protocol

- **Decision**:

  | Vectors | Every supported size and evidence variant | Every claimable size |
  |---------|------------------------------------------|----------------------|
  | Π and Π⁻¹ | 16 inputs: all-zero, all-one, alternating `0x55…`, a counting pattern and test states 0…11; the state after every round for the first 4 inputs; the output for all 16 | — |
  | Mode | — | 2 development keys (key and nonce 0, key and nonce 1) × 10,000 32-bit words, in generate requests of 1, 7, 64 and 1,000 words, repeated, then the remainder, with forget after each request |
  | Long run | — | the SHA-256 of the first 2²⁰ words for key and nonce 0, in requests of 4,096 words (FR-058 "long runs") |
  | Constructed states | the edge states the design document lists (FR-054) | the same |

  - Lengths are the same at 4×4, 8×8 and 16×16. The output per call of Π grows with n² (r = 768,
    3,840 and 16,128 bits), so the 320,000 bits of a 10,000-word vector take at least 417, 84
    and 20 calls of Π, plus one forget call per request. The timing probe of R4 measured 60 ns per
    pure-Python word operation, so at R = 32 and 32 word operations per node and round a call
    takes about 1 ms at 4×4 and 16 ms at 16×16, and the 2²⁰-word digest under a minute at every
    claimable size.
  - Each vector file records the measured speed (calls of Π and words per second) and the
    generation time (FR-036). If generating a file takes over an hour, it is generated once and
    its time recorded; its length is not reduced.
- **Stricter means**: lengths may only grow.
- **Rationale**: the spec allows shorter vectors at large sizes "where the model's speed limits a
  size". Because a call's output grows with the grid, speed does not limit the 10,000-word
  vectors at 16×16, so they stay full length. Traces are kept for step-by-step comparison
  (FR-057) and for the later RTL (FR-056).
- **Alternatives**: 10⁶-word mode vectors at every size (large files for little extra coverage;
  the long-run digest covers long runs); traces for every input (the files grow with R × b).

## R9. The target advantage for the output limits (FR-007, FR-010) — protocol

- **Decision**: the output limits per instantiation and per key, and the number of keys u, are
  powers of two at which the mode theorem's bound (R10), with Π modelled as a random
  permutation (FR-004), is at most

  ```text
  ε = 2⁻⁶⁴, evaluated at N = 2¹²⁸ offline evaluations of Π or Π⁻¹
  and with every online quantity (data, calls, instantiations, reseeds, keys) at its limit.
  ```

  - A committed script evaluates the bound at the limits and checks that doubling any one limit
    would push it above ε. Where limits trade against one another, the design document states
    its choice and the reason.
  - The bound is increasing in N, so it then holds for every adversary below the target strength.
  - The per-request limit is the smaller of the per-instantiation limit and 2¹⁹ bits, the largest
    request SP 800-90A allows its DRBGs. Within one request, a compromised state reveals the
    request's earlier blocks through Π⁻¹, so the request size bounds what a state compromise
    exposes before the next forget call. The design document may lower it, never raise it.
  - Every online quantity the bound counts (output, calls of Π, instantiations per key, reseeds)
    has a limit and a counter, and the model refuses any call that would pass one (FR-007). One
    `Generator` object is bound to one key and cannot be used after zeroize, so it enforces the
    per-key limits for its key. Across objects, processes and devices, the per-key limits and u
    are usage rules that the design document states for the caller; no single object sees them.
  - If no positive limit reaches ε (a term such as N/2^c needs c ≥ 192), the mode or the
    capacity changes (c may only rise); ε does not.
- **Stricter means**: ε may only fall, N may only rise, and the per-request cap may only fall.
- **Rationale**: at the limits, an attack with 2¹²⁸ evaluations gains at most 2⁻⁶⁴, so its time
  over advantage stays at least 2¹⁹², well above 2¹²⁸. ε = 2⁻¹²⁸ is unreachable: a term such as
  N/2^c alone is 2⁻¹²⁸ at c = 256. 2⁻⁶⁴ is stricter than the 2⁻³² of SP 800-38D's IV-collision
  rule. Terms of the form M·N/2^c and u·N/2^k, typical of keyed-duplex bounds, would give limits
  of the order of 2⁶⁴ blocks per key and 2⁶⁴ keys at c = k = 256; the values come from the
  theorem once its paper is read (R10).
- **Alternatives**: ε = 2⁻³² (looser); stating the bound without ε (FR-007 asks for it); a limit
  set by hand (it must follow from the theorem).

## R10. The mode theorem and the reading list (FR-013, FR-004, FR-016)

- **Decision**: the mode chapter adopts the full-state keyed duplex of Daemen, Mennink and Van
  Assche (ASIACRYPT 2017) for keystream and multi-user security. For backtracking resistance
  across forget, it uses the result for exactly its forget construction: the sponge-based PRNG of
  Bertoni et al. (CHES 2010) or the forward security of Gaži and Tessaro (EUROCRYPT 2016),
  whichever matches it. Each call (instantiate, generate, forget, reseed) is mapped to the
  theorem's calls, and each precondition is listed with the design feature that meets it.
- **Reading the papers is a download**, one permission per file (FR-046). Until a paper is
  approved and read, the mode chapter marks its use of that theorem "unverified", and the
  security-target chapter cannot pass the review that records L1 (FR-012).
- **If a call does not match a theorem exactly**, the call is changed to the theorem's form
  (forget as a duplexing call that overwrites the outer part, reseed as a domain-separated
  absorption), or the feature stops (Edge Cases). A mode without a matching theorem is never
  adopted.
- **Rationale**: one assumption, Π, for every property (strategy note §4.2). Two of the three
  properties sought need different theorems, so the plan names both and makes the match a check.
- **Alternatives**: counter mode with feed-forward (D1 alternative; no forget call, and the input
  must be stored); one theorem for all properties (no single paper is known here to cover
  keystream, multi-user and backtracking for this exact mode).

## R11. One operation list per candidate

- **Decision**: each candidate is written once as an operation list, `research/004/ir.py`, from
  which every tool derives what it needs:
  - Only two operation forms exist: `dst ← dst ⊙ F(srcs)` with ⊙ ∈ {⊕, ⊞, ⊟}, dst ∉ srcs, and F
    built from rotations, shifts, bitwise functions and round constants; and `dst ← rotl(dst, k)`
    with k fixed. Both are invertible whatever F is, so a list made of them is bijective by
    construction (FR-019), and the inverse list is generated mechanically.
  - A round is a sequence of phases (colour classes), and the updates within one phase read no
    lane that another update of the same phase writes. A phase is a pipeline stage for FR-025.
  - From the list: a scalar interpreter (Python integers) and a batch interpreter (numpy
    `uint64`, masked to w bits after every operation), the inverse, the dependency propagation
    (R13), the cost model (R5) and the bit-level trail models (R12).
  - Every rotation, shift and constant is a fixed value of the list (FR-020); nothing in the list
    can read data to choose an operation.
  - After selection, `phycoweb/model_v3.py` is written by hand from the design document for
    readability, and a test checks it against the interpreter on every committed vector.
- **Rationale**: evaluation, inverse, diffusion, cost and trail bounds then describe one object,
  so a bound cannot drift from the code it bounds. The Feistel-type form is the strategy note's
  rule for invertible coupling (§5.1).
- **Alternatives**: hand-written code per candidate and per tool (several copies that can
  disagree); an external framework such as CASCADA (a download; its IR would not match the
  model).

## R12. Trail-bound tools and their validation (FR-038, FR-039)

- **Decision**:
  - Without any download: scipy's HiGHS solver (`scipy.optimize.milp`, present in scipy 1.15.3)
    for active-box and active-S-box counting and for bit-level models at small widths;
    self-written exhaustive tables (differential and linear) for boxes and S-boxes at reduced
    widths, in numpy or C; a self-written branch-and-bound trail search for ARX in C (WSL), with
    the exact models of addition (Lipmaa and Moriai, 2001; Wallén, 2003).
  - With an approved download (R19): a SAT solver with Python bindings, or CryptoSMT or CASCADA,
    as a faster or independent cross-check.
  - **Fixed tool set** (**protocol**): the trail tools are those with a `re-found` validation
    record when the feature's first trail search starts. None is added afterwards, so a search
    that reaches its cap is never retried with another tool (R7). This plan requests no solver
    download (R19), so the set is HiGHS and the self-written searches unless the owner approves
    one before that moment.
  - Each tool re-finds a published result of its kind before any of its results counts, and its
    validation record cites the paper, table and value, taken from a copy the owner provides or a
    download approved for it:

    | Tool | Known result to re-find |
    |------|-------------------------|
    | ARX differential and linear search | the optimal trails of SPECK32 over the first rounds (Biryukov and Velichkov, 2014; Liu, Wang and Rijmen, 2016) |
    | Active S-box counting | PRESENT: every 5-round differential characteristic has at least 10 active S-boxes (Bogdanov et al., 2007) |
    | Long-trail active-box counting | a published long-trail bound of SPARKLE (Beierle et al., 2020), from its published box bounds |
    | Exhaustive box and S-box tables | the PRESENT S-box's published difference and linear tables |

  - Every bound record says it bounds single trails under the usual independence assumptions;
    clustering, hulls and key-dependent effects are open for feature 005 (FR-038).
- **Rationale**: re-finding a known value is the lesson of `nistrng` (security.md §11.2). The
  reference designs are used only inside validation tools, never in Π (D6).
- **Alternatives**: trusting a published tool without re-finding a result (FR-039 forbids it).

## R13. Structural checks (FR-019, FR-029, FR-037)

- **Decision** (**protocol** for the counts):
  - **Inverse**: Π⁻¹(Π(x)) = x and Π(Π⁻¹(x)) = x for the 16 vector inputs and 2¹⁰ test states at
    every supported size and variant.
  - **Exhaustive bijectivity**: 2×2 at w = 4 (b = 32), all 2³² inputs, through the batch
    interpreter, with a 2³²-bit (512 MiB) bitmap of outputs; the variant is bijective if the
    bitmap holds 2³² ones. A heavy run: about 1 h at R = 16 and 64 numpy operations per node and
    round, from the timing probe of R4, plus the bitmap.
  - **Dependency**: exact structural dependency, propagated through the operation list: XOR, AND,
    OR and NOT unite bit sets; rotations and shifts move them; output bit i of an addition or
    subtraction depends on bits 0…i of both operands. R_f and R_b are the first round counts at
    which every output bit depends on every input bit. A structural dependency that the avalanche
    test (R4) never observes fires there and raises R_dist, so a dependency that always cancels
    cannot pass silently.
  - **Symmetry**: at every supported size, no symmetry of the torus that moves a node may map a
    constant pattern to itself: no composition of translations, rotations by 90°, 180° and 270°,
    and reflections. Nor may rotating every word by the same amount k = 1…w − 1 map a round's
    constants to themselves: XOR, AND, NOT and rotations commute with that rotation and additions
    keep it with a fixed probability, so without shifts only the constants break it (rotational
    cryptanalysis). The spec names translations and rotations; reflections, compositions and
    word rotations are added. The patterns checked are each round's constants, the placement of
    the food nodes and every per-node constant, such as the rotation amounts.
  - **Invariants**: on 2¹⁰ test states, after one round and after a full call: the sums modulo
    2^w and the XORs of the pressure lanes and of the vein lanes, and the same over each colour
    of the checkerboard (even n); and the S13 transport mode of
    `research/security/step_probes.py`, which adds 2 and −2 alternately to the pressure lanes,
    as an input difference. A form that keeps its value on every test state, or a difference that
    comes out unchanged on every test state, fails the check.
- **Stricter means**: counts may only rise; more symmetries may be added.
- **Rationale**: structural dependency is the standard full-diffusion measure. Checking that it
  is observed as well rules out a dependency that always cancels.
- **Alternatives**: dependency estimated by sampling only (not exact, as FR-029 requires).

## R14. Supported sizes and variants (FR-017, FR-018, FR-032, FR-033)

- **Decision**:
  - Claimable sizes: 4×4, 8×8 and 16×16, at w = 32 and c = 256 with the frozen R (D3). Research
    sizes: 2×2, at every width with reduced capacity, and 3×3 if the design document specifies a
    three-colour schedule from the same generics; otherwise 3×3 is unsupported with that reason.
  - The research interface accepts every n from 2 to 16 for exploration, but n = 5, 6, 7 and
    9…15 have no vectors, R_f, R_b or bounds in this feature. Each is listed as an open item
    against FUT-GRID-1, with that reason (FR-018).
  - Widths: 4 (exhaustive checks, at 2×2 only), 8, 16 and 32. Rotation amounts scale with w by
    the design document's rule (FR-024).
  - Variant ID: `<design>/n<n>-w<w>-R<R>-c<c>`, for example `cand-A1/n2-w16-R8-c64`, where the
    design is a candidate ID or, after selection, `phyco-v3`. The production interface accepts
    only the three production IDs and refuses every other ID with an error (FR-033).
- **Rationale**: the strategy note's table (§4.5). Every claimable size needs an established
  R_bound at the production width, so each one added costs trail searches. Powers of two keep
  the folded-torus layout regular.
- **Alternatives**: every n from 2 to 16 supported (each claimable size needs its own R_bound,
  which would multiply the solver budget).

## R15. Constants (FR-023, FR-024)

- **Decision**: round constants come from a maximal-length LFSR whose polynomial and seed the
  design document states. `scripts/gen_constants_v3.py` checks that the polynomial is primitive,
  reads the sequence in a stated order over (round, food node), checks that no value repeats
  within one call of Π, runs the symmetry checks of R13, and writes `phycoweb/constants_v3.py`.
  Rotation amounts come from a stated search over the possible amounts, ranked by the trail
  bounds they give, with ties to the smallest amounts in a stated order. The design document
  states whether the call types draw on distinct constant streams (FR-023).
- **Rationale**: an LFSR is a stated rule that reproduces no published primitive's constants
  (D6) and is cheap in hardware. The script records which polynomials published designs use and
  refuses them.
- **Alternatives**: the digits of a mathematical constant (several published primitives use
  them); SHA-256 output (a value derived from a published primitive).

## R16. Records, storage and re-checks (FR-053, FR-061, FR-065; Edge Cases)

- **Decision**:
  - Every evidence record is JSON with the fields of security.md §17.2, the §11.6 items for
    statistical measurements, and the design-form disclaimer (FR-068), written by one module,
    `protocol/evidence.py`. Paths are under `reports/004-crypto-architecture-v3/`.
  - Records up to 10 MB, compressed with gzip, are committed. Larger outputs, such as full
    dependency matrices at 16×16 (about 32 MB per round and direction), stay local. Their
    SHA-256 and the regenerating command are committed, together with per-round summaries.
  - `scripts/recheck_004.py` recomputes every verdict from the saved outputs and compares it with
    the recorded verdict (FR-065, SC-017).
  - Heavy runs take an exclusive lock, `data/heavy-run.lock`, which `.gitignore` gains, and
    refuse to start while another process holds it (FR-045).
- **Rationale**: the edge case on large records leaves the choice to the plan. 10 MB keeps the
  repository small; hashes keep every local record checkable.
- **Alternatives**: commit everything (hundreds of MB of matrices); keep only summaries (the
  verdicts could not be re-checked).

## R17. The model, the second transcription and the tests (FR-035, FR-057, FR-058)

- **Decision**:
  - `phycoweb/model_v3.py` imports only the standard library and `phycoweb/constants_v3.py`. It is
    integer-only and branch-free on data. It is marked model-only, RTL-pending, with model ID
    `phyco-v3` and the variant IDs of R14. A test parses it with
    `ast.parse(source, feature_version=(3, 8))`, a best-effort check of the constitution's
    Python 3.8+.
  - The second transcription is `tests/v3_reference.py`, written from the design document alone in
    a separate session. That session starts only after the owner's recorded go-ahead. A person
    may write it, or a fresh agent session that the owner starts or authorizes; the provenance
    records name the session of each file (FR-057, FR-067). `tests/test_v3_transcription.py`
    compares the two step by step on every committed vector.
  - Tests use `unittest`, as in features 001–003: `python -W ignore -m unittest discover -s tests
    -t .`. The new tests cover FR-058's list. Hypothesis is added only if its download is
    approved (R19: version 6.168.5, the last release that supports Python 3.10); otherwise its
    absence is an open item (FR-058).
- **Rationale**: the precedent of `tests/v2_reference.py`. A separate session is what makes the
  check more than a re-reading of one's own code, and the common-mode caveat stays with the
  result.
- **Alternatives**: pytest (not installed; a download).

## R18. Repository hygiene (FR-042, FR-053, FR-068, FR-069)

- **Decision**:
  - `baseline/phyco-v2/` receives byte-exact copies of `phycoweb/model_v2.py`, `phycoweb/lut.py`,
    `fast/phyco_stream.c`, `fast/lut_table.h`, `specs/002-core-dynamics-redesign/design.md` and
    both `vectors/phyco-v2_*.hex`, with `MANIFEST.json` holding each file's SHA-256, source path
    and `git_head`. A new `scripts/archive_phyco_v2.py` writes it; the feature-001 script is left
    unchanged. `baseline/** -text` already keeps the copies byte-exact.
  - `.gitattributes` gains `text eol=lf` for `specs/004-crypto-architecture-v3/design.md`,
    `rationale.md`, `vectors/phyco-v3/**`, `research/004/**/*.jsonl`,
    `reports/004-crypto-architecture-v3/**/*.json` and `protocol/claims.json`.
  - `requirements.txt` loses its stale header and pins the two tested environments with
    markers: `numpy==2.2.6; python_version < "3.14"`, `numpy==2.5.4; python_version >= "3.14"`,
    the same for scipy (1.15.3 and 1.18.1), and `nistrng==1.2.3` in both. If Hypothesis is
    approved, it adds `hypothesis==6.168.5`, `sortedcontainers==2.4.0` and
    `exceptiongroup==1.3.1; python_version < "3.11"`. The analysis tools need Python 3.10 or
    later; the model needs only the standard library (R17).
  - `protocol/disclaimer.py` gains `DESIGN_DISCLAIMER`, the text at the top of the spec;
    `DISCLAIMER` stays unchanged. No freeze of features 002 or 003 pins this file.
  - The claim and evidence register is `protocol/claims.json`. `tests/test_claims.py` checks
    README, security.md §1.1 and §15, and the disclaimers against it, and scans for the wording
    FR-050 forbids outside the rules that forbid it.
- **Rationale**: these are the spec's named fixes (checklist groups E and F). Markers keep one
  file correct for both environments.
- **Alternatives**: two requirements files (more drift).

## R19. Downloads: candidates only, each needing permission (FR-046)

Nothing below is downloaded without the owner's permission for that file. Nothing in this plan
depends on any of them; without them the work uses the tools of R12 and records each gap as an
open item. The requests below were prepared on 2026-11-01 from the hosts' pages and from header
requests, with no file body downloaded. A size comes from the server's header where it gave one,
and otherwise as the host lists it. The IACR ePrint archive, the IACR conference archive and the
ToSC journal site refused scripted requests (HTTP 403 or a bot check), and nothing was done to
get around that: for those papers the table names a copy elsewhere, or the owner downloads the
file in a browser into a new folder and gives its path.

**Papers.** Each is read and cited, kept locally with its SHA-256 and never committed, so its
licence does not touch the project's GPL-3.0.

| File | Source | Size | Licence | Use | If not approved |
|------|--------|------|---------|-----|-----------------|
| `Daemen.pdf`: Daemen, Mennink and Van Assche, "Full-State Keyed Duplex With Built-In Multi-User Support", ASIACRYPT 2017 | https://ir.cwi.nl/pub/27254/Daemen.pdf (CWI repository, final version) | 604 kB, as CWI lists it | none stated by CWI; the ePrint version, 2017/498, is CC BY 4.0 | the mode theorem (R10) | the mode chapter stays "unverified"; L1 cannot be recorded |
| `SpongePRNG.pdf`: Bertoni, Daemen, Peeters and Van Assche, "Sponge-Based Pseudo-Random Number Generators", CHES 2010 | https://keccak.team/files/SpongePRNG.pdf | 238,714 bytes | none stated (authors' copy) | forget (R10) | as above |
| `169.pdf`: Gaži and Tessaro, "Provably Robust Sponge-Based PRNGs and KDFs", EUROCRYPT 2016 | https://eprint.iacr.org/2016/169.pdf; refused scripted requests, so the owner's browser | not given | CC BY 4.0 | forget (R10) | as above |
| `automatic-search-arx-trails.pdf`: Biryukov and Velichkov, "Automatic Search for Differential Trails in ARX Ciphers", CT-RSA 2014 | https://orbilu.uni.lu/bitstream/10993/17183/1/automatic-search-arx-trails.pdf (author postprint) | about 383 kB, as ORBilu lists it | none stated; the extended ePrint version, 2013/853, is CC BY 4.0 | SPECK32 differential trails (R12) | the owner provides the values with their source, or the tool stays unvalidated |
| `2657`, a PDF: Liu, Wang and Rijmen, "Automatic Search of Linear Trails in ARX with Applications to SPECK and Chaskey", ACNS 2016 | https://www.esat.kuleuven.be/cosic/publications/article-2657.pdf, redirected to the COSIC database | 458,069 bytes | none stated (COSIC copy) | SPECK32 linear trails (R12) | as above |
| `47270450.pdf`: Bogdanov et al., "PRESENT: An Ultra-Lightweight Block Cipher", CHES 2007 | https://www.iacr.org/archive/ches2007/47270450/47270450.pdf; refused scripted requests, so the owner's browser | not given | © IACR; no open licence stated | PRESENT's 5-round bound and S-box tables (R12) | as above |
| `main.pdf`: Beierle et al., "Lightweight AEAD and Hashing using the Sparkle Permutation Family", ToSC 2020(S1) | https://orbilu.uni.lu/bitstream/10993/41993/1/main.pdf (author preprint) | 1.02 MB, as ORBilu lists it | none stated on the record | the SPARKLE long-trail bound (R12) | as above |
| `AIS_31_Functionality_classes_for_random_number_generators_e_2024.pdf`: BSI, "A proposal for: Functionality classes for random number generators", version 3.0, 17 September 2024 | https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/Certification/Interpretations/AIS_31_Functionality_classes_for_random_number_generators_e_2024.pdf?__blob=publicationFile&v=3 | 6 MB, as BSI lists it | © BSI, under BSI's terms of use | D8's functionality class | the class stays unconfirmed, as an open item |

**Software.** Installed from the downloaded files into the two existing environments. The
licences allow use in a GPL-3.0 project, and nothing here is committed or distributed. Each
file's SHA-256 is checked against PyPI's after download and recorded.

| File | Source | Size | Licence | Use | If not approved |
|------|--------|------|---------|-----|-----------------|
| `hypothesis-6.168.5-cp310-abi3-win_amd64.whl` | PyPI | 684,616 bytes | MPL-2.0 | property tests (FR-058) on Windows; 6.168.5 is the last release for Python 3.10 | an open item (FR-058) |
| `hypothesis-6.168.5-cp310-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` | PyPI | 1,157,262 bytes | MPL-2.0 | the same in WSL (Python 3.14) | as above |
| `sortedcontainers-2.4.0-py2.py3-none-any.whl` | PyPI | 29,575 bytes | Apache-2.0 | a Hypothesis dependency, both environments | as above |
| `exceptiongroup-1.3.1-py3-none-any.whl` | PyPI | 16,740 bytes | MIT | a Hypothesis dependency, Windows only (Python < 3.11) | as above |

**Not requested.** A SAT solver with PySAT (CaDiCaL or Kissat), Z3, OR-Tools CP-SAT, SCIP,
CryptoSMT and CASCADA. HiGHS in scipy and the self-written searches cover every validation
target of R12, a further tool would need its own validation, and the tool set is fixed when the
first trail search starts (R12). For a SAT cross-check before then, the files would be
`python_sat-1.9.dev17-cp310-cp310-win_amd64.whl` (1,924,781 bytes) and
`python_sat-1.9.dev17-cp314-cp314-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl`
(4,063,894 bytes), MIT, with their dependency `six`.

Every downloaded file is treated as untrusted: it goes into its own new directory, it is never
run from inside that directory, Python reading it runs with `-I`, and its SHA-256 is recorded.
