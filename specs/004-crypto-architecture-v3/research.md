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

## Choices for owner review

Each row is a choice the owner could confirm or change before approving the plan, with the
recommended option first. "As decided" keeps the decision of the section the ID names.
"Answered" rows were settled on review on 2026-11-01 (plan.md, "Other choices, answered on
review"). "Change" rows alter a decision. They come from developing these choices and from an
item-by-item check of the seed-entropy note's redesign checklist
([checklists/redesign-inputs.md](./checklists/redesign-inputs.md)). Every change is stricter or
adds a check, as FR-044 allows.

**Answered 2026-11-01.** The owner chose every recommended option ("all recommended") and
approved every download in R19's two tables (R19.1). The eleven changes are applied in the
sections below, in plan.md, data-model.md, both contracts, quickstart.md and the checklist. The
rows stay as they were offered, and the sections they name hold the decisions. One row's wording
was corrected after the answer, not its choice: R5.2 now credits the 10⁸ words/s goal to feature
003, which set it for the C stream.

| ID | Choice | Recommended | Other options |
|----|--------|-------------|---------------|
| R1.1 | Where things run | As decided: Python work on Windows 11 with Python 3.10.11; C tools and the Linux reproduction in WSL2; the i9-14900K, one heavy run at a time | Everything in WSL: loses the Windows half of SC-009. A Windows C compiler: a download for no gain. A cloud machine: an outward action, and the code and inputs leave the machine |
| R2.1 | The FUT-SEC-8 search tool | Answered: `fast/seed_search.c` with its own copy of the step, built by its own `fast/seed_search.mk` | Extending `fast/phyco_stream.c`: touches files the feature-003 freeze hashes. A Python sweep: about 64 days per target |
| R2.2 | Progress output of the 32-thread sweep | Change: only the main thread writes progress lines; the workers update counters that it reads (checklist D4) | As decided, unspecified: lines from 32 threads can interleave, as in feature-003 open issue 2 |
| R3.1 | How development inputs are derived | As decided: SHA-256 of one public string per input, `phycoweb-004/dev/<kind>/<i>` | One SHA-256 stream cut into fields: a change to one field's length shifts every later input. OS random values, recorded: no rule recomputes them, which FR-040 needs |
| R3.2 | Source of the uniform controls | As decided: the same strings under `control`, so every control run can be repeated | OS random controls: unrepeatable, the weakness of feature 003's `getrandom` control (checklist F8) |
| R4.1 | Inputs per frequency measurement | As decided: N = 2²⁰ per claimable size | 2¹⁶: needs biases 4 times larger. 2²⁴: 16 times the cost, about 5.6 h per candidate at R = 32 |
| R4.2 | Instantiation states for the frequency test | Change: two sets per size, key i with nonce i as now, and key 0 with nonce i, the many-nonces-under-one-key case an attacker sees (FUT-SEC-3); S = 4b; 0.35 h more at R = 32; the bias found at 50% power moves from 0.0023 to 0.0024 at 4×4 | As decided, key i with nonce i only. Uniform states: no information, since Π maps uniform inputs to uniform outputs |
| R4.3 | Avalanche counts and threshold | Answered: N_a = 2¹³ per flipped bit; threshold 0.005/(128·S_A) | The first draft, N_a = 2¹² at 0.005/S_A per round count: a false raise of R at R = 32 about 38% instead of 23%. N_a = 2¹² at the per-size threshold: catches 0.053 instead of 0.037 at 4×4 |
| R4.4 | Flip set F at 8×8 and 16×16 | As decided: the 2w = 64 bits of each node on the main diagonal (\|F\| = 512 and 1,024) | Every state bit: 2²⁷ pairs per direction at 16×16, 16 times the diagonal set, beyond the 12 h of R7 |
| R4.5 | Related-key, related-nonce and rotational differences before the freeze | Change: add to the avalanche measurement every key and nonce bit flipped in 2¹³ instantiation states, run forward as instantiate runs Π, and rotational pairs, every lane of 2¹³ test states rotated by each k = 1…w − 1, in both directions. Both count in S_A = (2·\|F\| + 384 + 2(w − 1))·b under the same threshold, so the chance of a false firing does not change; 0.6 h more at R = 32; sensitivity changes by under 1%. Their results can then still raise R before the freeze (checklist B4) | As decided, left to feature 005: after the freeze, a weakness found there can only lead to a new model ID |
| R4.6 | Detection power shown inside each avalanche run | Change: wherever the exact dependency matrices (R13) show an output bit independent of a flipped bit, that difference bit must never flip, and so must fire; any disagreement is recorded as a tool defect (checklist F9) | As decided: only the tools' validation on `phyco-v2` (FR-039) shows detection power |
| R5.1 | Cost model for D4 | As decided: 6-input LUTs per node and round, with carry chains counted, and no packing or fusion | A LUT6_2 packing model: closer to the fabric, but more rules to argue before any result. Gate equivalents: not the FPGA's resource |
| R5.2 | Throughput goal (checklist C3) | Change: state a goal of 10⁸ 32-bit words per second at the 200 MHz target for every claimable size, the goal feature 003 set for the C stream, which design 1.0 missed at 8.5 × 10⁷, and report FR-026's implied throughput beside it; not an eligibility rule | An eligibility rule: a slow candidate becomes ineligible, which could end the feature in a stop. As decided, no goal: C3 stays half answered |
| R6.1 | Width and rounds at which D4 is scored | As decided: the widest reduced width, 16 or else 8, at which both families have both bounds over a common r* ≥ 2 | w = 32 directly: bounds may not exist there for both families early. 2×2: a research size whose diffusion differs from the claimable sizes |
| R6.2 | When D4 is decided, ties, and no scored family | Answered: once, by code, over the entered set recorded before the first score; an exact tie waits for R at 4×4 of both representatives; with no scored family, selection takes the eligible candidate with the smallest R at 4×4 from either family | A second D4 run after more candidates: reopens the choice. A stop when no family is scored: discards the evidence of both. The owner's free choice: no rule behind it |
| R7.1 | Budget per candidate | As decided: 48 h of trail searches (8 h per instance), 6 h of structural checks, 12 h of statistics; at most about 16.5 days of runs for six candidates | Half: more searches end inconclusive, and stops come sooner. Double: up to about 33 days of runs |
| R7.2 | Re-runs | As decided: one per kind of evidence, only after a recorded tool defect, inside the budget | None: one tool bug decides a candidate. More: invites running again until a result pleases |
| R7.3 | Order of sizes | Change: each kind of evidence runs at 4×4, then 8×8, then 16×16; a larger size starts only when the smaller one's run of that kind has finished without making the candidate ineligible (FUT-GRID-5; checklist D8) | As decided, any order: a candidate that fails at 4×4 may already have spent its 16×16 hours |
| R7.4 | Projection before heavy runs | Answered: a timing run of at most 60 s on the candidate; the run starts only if the projection fits the hours left in its row; counts never change to fit | No projection: a run can use up a budget row before anyone notices |
| R8.1 | Mode vectors | As decided: 2 development keys × 10,000 words at every claimable size, in requests of 1, 7, 64 and 1,000 words | 10⁶ words: large files for little extra coverage. Shorter at 16×16: the spec allows it, but the model's speed does not need it |
| R8.2 | Long-run digest | As decided: SHA-256 of the first 2²⁰ words, under a minute per size | 2²⁴ words: about 30 min in all, still far short of feature 008's 2³²-word check, which needs a fast checked model anyway |
| R9.1 | Target advantage ε | As decided: 2⁻⁶⁴ at N = 2¹²⁸ evaluations of Π or Π⁻¹ | 2⁻³²: larger limits, a looser target. 2⁻⁸⁰: smaller limits; with a bound linear in the data, the per-key limit falls by 2¹⁶ |
| R9.2 | Per-request cap; one key per `Generator` | Answered: the smaller of the per-instantiation limit and 2¹⁹ bits; zeroize final, a counter for every online quantity, and per-key limits and u across objects stated as usage rules | No cap: a state compromised mid-request exposes everything since the last forget, up to the per-instantiation limit. A smaller cap: more forget calls per output bit |
| R10.1 | Mode theorem | As decided: the full-state keyed duplex of Daemen, Mennink and Van Assche (2017), with the forget result of Bertoni et al. (2010) or Gaži and Tessaro (2016), whichever matches forget exactly | The earlier single-user analysis of the full-state keyed duplex (Mennink, Reyhanitabar and Vizár, 2015): another paper to request, and u keys would need a hybrid argument. Counter mode with feed-forward: not D1, and no forget call |
| R11.1 | One operation list per candidate | As decided: only two invertible update forms, so a list is bijective by construction, and every tool derives from it | Hand-written code per tool: copies that can disagree. CASCADA's representation: a download, and it would not match the model |
| R11.2 | When to build a C evaluator | As decided: only when a heavy run's projection does not fit its row; generated from the operation list and checked on the committed vectors | From the start: faster runs, but more code to check before the first result |
| R12.1 | Trail tools | As decided: HiGHS in scipy and self-written searches; no solver download | PySAT with CaDiCaL (wheels of 1.9 and 4.1 MB, MIT, plus `six`): an independent cross-check that needs its own validation and approval before the first trail search. CryptoSMT or CASCADA: larger downloads, more to validate |
| R12.2 | Fixing the tool set | Answered: the tools with a `re-found` record when the first trail search starts; none added later | An open set: a search that reached its cap could be retried with a friendlier tool |
| R13.1 | Symmetries checked | Answered: translations, rotations by 90°, 180° and 270°, reflections and their compositions, and word rotations | The spec's translations and rotations only: misses mirror images and rotational cryptanalysis |
| R13.2 | Cycle structure of Π (checklist B5) | As decided, not measured: a permutation merges no states, and the generic bound covers its cycles | Count the cycles of the 2×2, w = 4 variant: about 2 h in C on one thread, against the about 23 cycles of a random permutation of 2³² points; weak evidence for the cost |
| R14.1 | Research sizes | As decided: 2×2 at every width with reduced capacity, and 3×3 only if the design document gives a three-colour schedule from the same generics | Even sizes only: 3×3 listed as unsupported, with its reason |
| R14.2 | Key and nonce of keyed reduced variants (FUT-GRID-2; checklist A7) | Change: a c-bit key and a c/2-bit nonce, so 256 and 128 bits at every claimable size, and FR-010's relations at s = c/2; c a multiple of 16; a variant whose key and nonce leave no room for padding and domain bits is keyless. The model contract and data-model §10 take these lengths. This removes a contradiction: the plan now gives every keyed variant a 256-bit key and a 128-bit nonce, which a 2×2 state, 256 bits at w = 32 and 32 bits at w = 4, cannot hold | A 256-bit key and 128-bit nonce everywhere, absorbed over several blocks where they do not fit: the construction changes at small sizes, so results transfer less. Keyless reduced variants only: key loading stays undefined at 2×2, against FUT-GRID-2 |
| R15.1 | The rule for round constants (checklist C2) | Change in wording only: the maximal-length LFSR, as decided, classed as a published design method that yields a fixed table, not as a standard PRNG in Π, under feature-002 FR-007 as the spec re-decides it (D6): no key, nonce or state enters it, and polynomials of published designs are refused | A plain counter formula, which that rule allows by name: simpler, but successive constants differ in few bits. Digits of a mathematical constant: several published primitives use them |
| R15.2 | How constants reach the food nodes (checklist A11) | Change: each food node holds its own constants in a small ROM indexed by the round counter, so no data signal crosses the grid; only the clock, reset and the round and phase counters are global. The cost model still does not count the ROMs | One central LFSR with a registered distribution tree: a grid-wide data path, to be justified like the output tree. A copy of the LFSR at each food node: local, but each copy must start at its own offset |
| R15.3 | Rotation amounts | As decided: a stated search over every amount, ranked by the trail bounds it gives, with ties to the smallest amounts in a stated order | Hand-picked amounts: FUT-GRID-4 forbids them. Amounts drawn from the LFSR: a rule, but not chosen by the bounds as FR-024 asks |
| R16.1 | What is committed | As decided: records up to 10 MB, compressed with gzip; larger outputs stay local with their SHA-256 and the command that regenerates them | Everything: hundreds of MB of matrices. Summaries only: verdicts could not be re-checked (FR-065) |
| R16.2 | Writers of the hash-chained logs (checklist D4) | Change: every append to `research/004/candidates.jsonl` and `provenance.jsonl` takes a short exclusive lock and checks the chain first, so two scripts never chain to the same last line | As decided: only heavy runs are serialized, so a light script appending during a heavy run could break the chain |
| R17.1 | How the model is written | As decided: by hand from the design document after selection, then checked against the operation-list interpreter on every vector | Generated from the operation list: one source, but harder to read as the oracle for the RTL (FR-056), and its check against the interpreter becomes circular |
| R17.2 | Test framework | As decided: `unittest`, as in features 001–003; Hypothesis 6.168.5 only if its download is approved | pytest: a download, with no gain in coverage |
| R18.1 | `requirements.txt` | As decided: one file pinning both tested environments with markers | Two files: two places to drift |
| R18.2 | Line endings of makefiles (checklist F12) | Change: pin `*.mk` and `Makefile` with `text eol=lf`, which covers the new `fast/seed_search.mk` and keeps feature 003's `fast/Makefile` LF on a fresh checkout without changing its bytes | Only `fast/seed_search.mk`. No pin: this machine's `core.autocrlf=true` writes CRLF on a fresh checkout, and the repository pins every script that runs in WSL |
| R19.1 | Downloads | The owner approves each file of R19's tables separately; `169.pdf` and `47270450.pdf` need the owner's browser | Values with their source from the owner instead. None: the mode chapter stays "unverified", L1 cannot be recorded, and the trail tools stay unvalidated |

Of the 42 rows, 23 keep a decision as made, 7 were answered on review, 11 changes were chosen
and applied, and R19.1's downloads were approved, all on 2026-11-01.

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
  - Only the main thread writes progress lines, to stderr; the workers update counters that it
    reads, so no two threads write to one stream (checklist D4).
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
  | Key i | `phycoweb-004/dev/key/<i>` | the 32-byte digest; for a keyed reduced variant of capacity c < 256, its first c/8 bytes (R14) |
  | Nonce i | `phycoweb-004/dev/nonce/<i>` | the first 16 bytes; for a keyed reduced variant, the first c/16 bytes |
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
    two sets of N = 2²⁰ development inputs: for i = 0…2²⁰ − 1, the state that instantiate gives
    to its first call of Π for key i and nonce i, and for key 0 and nonce i, the many nonces under
    one key that an attacker sees (FUT-SEC-3), both with the empty personalization string. Each
    input runs through rounds 1…R_cur of Π, and separately of Π⁻¹. After every round the ones in
    each state bit are counted, per set. At a size and round count, the bits tested are the b
    bits after Π and the b bits after Π⁻¹ in each set, so S = 4b. A bit fires if its two-sided
    binomial p-value (p = 1/2; twice the smaller tail, at most 1, computed exactly) is at most
    0.005/S.
  - **Avalanche test.** FR-037 asks for it; using it as a source of R_dist is stricter than the
    spec. For each flipped input bit j in a set F, N_a = 2¹³ test states x (kind `state`, R3);
    after every round r = 1…R_cur the difference Π^r(x) ⊕ Π^r(x ⊕ e_j) is counted bit by bit,
    and the same for Π⁻¹. F holds every state bit at 4×4 (|F| = 1,024) and the 2w = 64 bits of
    each node on the main diagonal at 8×8 and 16×16 (|F| = 512 and 1,024). Two further sets test
    related inputs before the freeze (checklist B4). Related keys and nonces: each of the 384 key
    and nonce bits is flipped in the first 2¹³ instantiation states of the frequency test (key i,
    nonce i), and the difference is counted after every round of Π only, as instantiate runs Π.
    Rotational pairs: for each k = 1…w − 1, the difference Π^r(rot_k(x)) ⊕ rot_k(Π^r(x)) over
    the N_a test states, rot_k rotating every lane by k, and the same for Π⁻¹. With
    S_A = (2·|F| + 384 + 2(w − 1))·b, a difference bit fires if its two-sided binomial p-value is
    at most 0.005/(128·S_A). The factor 128 spreads the test's 0.005 over up to 128 round counts
    at a size, so this extra test adds at most 0.005 per size, not per round count, to the chance
    of a false firing (below). A difference bit that never flips fires, so a dependency that is
    never observed raises R_dist.
  - **Cross-check in every avalanche run.** Wherever the exact dependency matrices (R13) show an
    output bit independent of every input bit that a flip changes, that difference bit must never
    flip, and so must fire. Any disagreement is recorded as a tool defect, and the run's status is
    `inconclusive` (checklist F9).
  - **Rounds measured.** R_cur is the candidate's current value of the round rule. If a test
    fires at a round count r with 2r > R_cur, R_cur becomes 2r and the measurement extends to it,
    until no firing round count raises R.
  - **Uniform control.** Before its first use at each size, each test is applied once, with the
    same counts and the same threshold, to uniform control inputs: two sets of 2²⁰ control
    states, and N_a·(|F| + 384 + w − 1) XOR differences of two independent control states, N_a
    for each flipped bit, key or nonce bit and rotation amount. If a test fires on its control,
    the bias evidence of that size is inconclusive and the rule is not loosened (Edge Cases).
    Inconclusive bias evidence leaves R_dist unestablished at that size, which makes the
    candidate ineligible unless a recorded tool defect is fixed and the one re-run that R7 allows
    is conclusive.
  - **Sensitivity**, computed for this plan with scipy 1.15.3, for the bias |f − 1/2| of one bit
    that fires with probability 1/2 (and 0.9):

    | Size | Frequency, N = 2²⁰ per set, threshold 0.005/S | Avalanche, N_a = 2¹³, threshold 0.005/(128·S_A) |
    |------|-----------------------------------------------|-------------------------------------------------|
    | 4×4 | 0.0024 (0.0030), S = 2¹² | 0.0373 (0.0443), S_A = 2,494·b |
    | 8×8 | 0.0025 (0.0031), S = 2¹⁴ | 0.0380 (0.0451), S_A = 1,470·b |
    | 16×16 | 0.0026 (0.0033), S = 2¹⁶ | 0.0395 (0.0465), S_A = 2,494·b |

    Against one input set (S = 2b) and F alone, the values were 0.0023, 0.0024 and 0.0026 for the
    frequency test and 0.0372, 0.0377 and 0.0394 for the avalanche test, so the added sets cost
    little sensitivity, under 1% for the avalanche test. The first draft's avalanche test,
    N_a = 2¹² at 0.005/S_A, caught 0.047 (0.057) at 4×4, so the test now detects smaller biases as
    well as firing by chance less often.

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
- **Stricter means**: N and N_a may only rise, and F and the sets of inputs and differences may
  only grow; S and S_A always count the bits tested; the thresholds stay 0.005/S and
  0.005/(128·S_A); the cross-check stays.
- **Rationale**: Π maps uniform inputs to uniform outputs at every round count, so a frequency
  test needs structured inputs. Instantiation inputs are the structured inputs an attacker
  actually gets (FUT-SEC-5): about 384 varying key and nonce bits, the rest fixed. A timing probe
  on this machine (2026-11-01; Python 3.10.11, numpy 2.2.6) measured 0.21 ns per numpy word
  operation in batches of 2¹⁶ and 0.66 ns per counted bit. At R = 32 and 64 numpy operations per
  node and round, the frequency test then takes about 0.7 h per candidate over its two input
  sets, the three sizes and both directions, and the avalanche test about 3.1 h with its related
  and rotational sets, mostly counting bits: 3.8 h in all. A raise of R to 64 doubles that to
  7.7 h, still inside the 12 h of R7. The avalanche test complements the exact dependency
  matrices (R13), which also check it, and its budget sets N_a and F. The second input set holds
  the key fixed, as the many nonces under one key do, and the related and rotational sets let
  their results raise R before the freeze instead of only in feature 005 (checklist B4).
- **Alternatives**: uniform inputs (no information for a permutation); N = 2¹⁶ (detects only
  biases 4 times larger); N = 2²⁴ (16 times the cost); every input bit at 16×16 (2²⁷ pairs per
  direction, 16 times the diagonal set, which would not fit the 12 h of R7); the avalanche test
  at 0.005/S_A per round count, as first drafted (38% instead of 23% at R = 32); N_a = 2¹² at
  the per-size threshold (half the cost, but 0.053 instead of 0.037 at 4×4); key i with nonce i
  only (no many-nonces case); related and rotational differences left to feature 005 (a weakness
  found after the freeze can only lead to a new model ID); detection power shown only by the
  tools' validation on `phyco-v2` (FR-039).

## R5. The operation-count cost model (D4; FR-026) — protocol

- **Decision**: LUTs per node and round are counted from the candidate's operation list (R11) on
  6-input LUTs, the Arty A7-100T's fabric, with no packing or fusion between listed operations:

  | Operation on w-bit words | LUTs | Carry chains |
  |--------------------------|------|--------------|
  | Rotation or shift by a constant; wiring between nodes; a register stage | 0 | 0 |
  | Bitwise function in which each output bit depends on k ≤ 6 input bits (constant bits count as inputs), such as XOR, AND-NOT or a χ-like row | w | 0 |
  | Bitwise function with k > 6 input bits per output bit | w · ⌈(k − 1)/5⌉ | 0 |
  | Addition or subtraction modulo 2^w of two words | w | 1, of w bits |

  - The round constants, held in a small ROM at each food node (R15), are not counted.
  - An operation shared by two nodes counts once, at the node that computes it.
  - Serial carry chains per round = the most additions on any dependency path within one round
    (the D4 tie-break). Per pipeline stage, the same count must be at most 2 (FR-025).
  - Flip-flops (2w per node, plus pipeline registers) are reported but not scored.
  - Cost per output bit (FR-026) = LUTs per node and round × n² × R / r, in LUT-cycles per
    output bit, for an implementation that computes one round per clock cycle.
  - **Throughput goal** (checklist C3): 10⁸ 32-bit words per second at the 200 MHz target, at
    every claimable size. It is the goal feature 003 set for the C stream, which design 1.0
    missed at 8.5 × 10⁷. The design document reports FR-026's implied throughput beside it; the
    goal is reported, not an eligibility rule. At one round per clock cycle the implied rate is
    r/R bits per cycle: at 4×4, 1.5 × 10⁸ words per second at R = 32 and 0.75 × 10⁸ at R = 64,
    before forget calls.
  - `research/004/tools/costmodel.py` computes every number from the operation list, and a test
    checks the table above on hand-counted examples.
- **Stricter means**: the model cannot change once the first candidate is scored.
- **Rationale**: the model must be fixed before scoring and simple enough to compute by code. Both
  families are counted by the same table, so neither gains from a counting choice. Packing and
  fusion depend on synthesis; Vivado post-route numbers belong to feature 008 (FUT-HW-2).
- **Alternatives**: a LUT6_2 packing model (closer to the real fabric, but more rules to argue
  about before any result); gate-equivalent counts (not the FPGA's resource); the throughput
  goal as an eligibility rule (a slow candidate would become ineligible, which could end the
  feature in a stop).

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
  - **Order of sizes.** Each kind of evidence runs at 4×4, then 8×8, then 16×16. A larger size
    starts only when the smaller one's run of that kind has finished without making the
    candidate ineligible, so a candidate that fails at 4×4 spends none of its 16×16 hours
    (FUT-GRID-5; checklist D8).
  - **Projection before every heavy run.** A timing run of at most 60 s on the candidate itself
    projects the run's hours from the counts of R4, R8 and R13. The run starts only if the
    projection fits the hours left in its budget row. Otherwise the engine is made faster first,
    with more worker processes or with a C evaluator generated from the same operation list and
    checked against the numpy interpreter on the committed vectors. Counts and budgets never
    change to make a run fit, and the record keeps the projection beside the time used.
  - The most the feature can spend is six candidates × 66 h, about 16.5 days of runs.
- **Stricter means**: every budget may only be lowered (stop rule); the order of sizes stays.
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
- **Reading the papers is a download** (FR-046); the owner approved each file of R19 on
  2026-11-01. Until a paper is on disk and read, the mode chapter marks its use of that theorem
  "unverified", and the security-target chapter cannot pass the review that records L1 (FR-012).
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
  - Only with a separate approval, since R19 requests none: a SAT solver with Python bindings,
    or CryptoSMT or CASCADA, as a faster or independent cross-check.
  - **Fixed tool set** (**protocol**): the trail tools are those with a `re-found` validation
    record when the feature's first trail search starts. None is added afterwards, so a search
    that reaches its cap is never retried with another tool (R7). This plan requests no solver
    download (R19), so the set is HiGHS and the self-written searches unless the owner approves
    one before that moment.
  - Each tool re-finds a published result of its kind before any of its results counts, and its
    validation record cites the paper, table and value, taken from a copy the owner provides or
    from the paper's download, approved on 2026-11-01 (R19):

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
    cannot pass silently. Where the matrices show no dependency, the avalanche test must observe
    no flip; a disagreement is a tool defect (R4).
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
  - **Keys of reduced variants** (FUT-GRID-2; checklist A7): a keyed variant of capacity c takes
    a c-bit key and a c/2-bit nonce, so 256 and 128 bits at every claimable size, and its row of
    the size profile checks FR-010's relations at s = c/2. c is a multiple of 16 as well as of w,
    so both lengths are whole bytes. A variant whose key and nonce leave no room in the state for
    the padding and domain bits is keyless: the research duplex refuses it, and only the
    permutation interface applies. The model contract and data-model §10 take these lengths.
- **Rationale**: the strategy note's table (§4.5). Every claimable size needs an established
  R_bound at the production width, so each one added costs trail searches. Powers of two keep
  the folded-torus layout regular. A key of c bits keeps key loading the same construction at
  every size, so evidence on reduced variants transfers, and a 2×2 state, 256 bits at w = 32
  and 32 bits at w = 4, could not hold a 256-bit key and a 128-bit nonce.
- **Alternatives**: every n from 2 to 16 supported (each claimable size needs its own R_bound,
  which would multiply the solver budget); a 256-bit key and 128-bit nonce everywhere, absorbed
  over several blocks where they do not fit (the construction changes at small sizes); keyless
  reduced variants only (key loading stays undefined at 2×2, against FUT-GRID-2).

## R15. Constants (FR-023, FR-024)

- **Decision**: round constants come from a maximal-length LFSR whose polynomial and seed the
  design document states. `scripts/gen_constants_v3.py` checks that the polynomial is primitive,
  reads the sequence in a stated order over (round, food node), checks that no value repeats
  within one call of Π, runs the symmetry checks of R13, and writes `phycoweb/constants_v3.py`.
  Rotation amounts come from a stated search over the possible amounts, ranked by the trail
  bounds they give, with ties to the smallest amounts in a stated order. The design document
  states whether the call types draw on distinct constant streams (FR-023).
  - **Where the constants live** (checklist A11): each food node holds its own constants, its
    column of the table, in a small ROM indexed by the round counter, so no data signal crosses
    the grid. Only the clock, reset and the round and phase counters are global. The LFSR exists
    only in the script; the hardware holds its output as a fixed table.
  - **How the LFSR is classed** (checklist C2): under feature-002 FR-007 as the spec re-decides
    it (D6), the LFSR is a published design method that yields a fixed table, not a standard
    PRNG in Π: no key, nonce or state enters it.
- **Rationale**: an LFSR is a stated rule that reproduces no published primitive's constants
  (D6). The script records which polynomials published designs use and refuses them. A ROM per
  food node keeps every data path local (Principle III; FR-018), where one central LFSR would
  need a grid-wide distribution tree; the cost model does not count the ROMs (R5).
- **Alternatives**: the digits of a mathematical constant (several published primitives use
  them); SHA-256 output (a value derived from a published primitive); a plain counter formula,
  which the re-decided rule allows by name (simpler, but successive constants differ in few
  bits); one central LFSR with a registered distribution tree (a grid-wide data path, to be
  justified like the output tree); a copy of the LFSR at each food node (local, but each copy
  must start at its own offset).

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
  - **Writers of the hash-chained logs** (checklist D4): `research/004/candidates.jsonl` and
    `provenance.jsonl` are both chained, each line holding the SHA-256 of the line before it
    (data-model §3 and §14). Every append takes a second lock, `data/log-append.lock`, by
    exclusive create, which `.gitignore` also gains. Holding it, the writer checks the chain up
    to the last line, appends one line chained to it and releases the lock. A writer that cannot
    take the lock within 10 s, or finds the chain broken, exits 2 and appends nothing, so two
    scripts never chain to the same last line.
- **Rationale**: the edge case on large records leaves the choice to the plan. 10 MB keeps the
  repository small; hashes keep every local record checkable.
- **Alternatives**: commit everything (hundreds of MB of matrices); keep only summaries (the
  verdicts could not be re-checked); serializing only heavy runs (a light script appending during
  a heavy run could break a chain).

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
    -t .`. The new tests cover FR-058's list, with property-based tests in Hypothesis 6.168.5,
    the last release that supports Python 3.10, whose download the owner approved on 2026-11-01
    (R19). If it cannot be obtained, its absence is an open item (FR-058).
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
  - `.gitattributes` gains `text eol=lf` for every Markdown file under
    `specs/004-crypto-architecture-v3/` and `reports/004-crypto-architecture-v3/`, the spec among
    them, since every record holds the spec's SHA-256 (data-model §1); and for
    `vectors/phyco-v3/**`, `research/004/**/*.jsonl`, `protocol/claims.json`,
    `reports/004-crypto-architecture-v3/**/*.json` and
    `reports/004-crypto-architecture-v3/**/*.jsonl`, the provenance log among them.
  - `.gitattributes` also gains `*.mk text eol=lf` and `Makefile text eol=lf`, which cover the new
    `fast/seed_search.mk` and keep feature 003's `fast/Makefile` LF on a fresh checkout. Its bytes
    do not change: Git already holds it with LF line endings (checklist F12).
  - `requirements.txt` loses its stale header and pins the two tested environments with
    markers: `numpy==2.2.6; python_version < "3.14"`, `numpy==2.5.4; python_version >= "3.14"`,
    the same for scipy (1.15.3 and 1.18.1), and `nistrng==1.2.3` in both. With Hypothesis
    approved (R19), it adds `hypothesis==6.168.5`, `sortedcontainers==2.4.0` and
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

## R19. Downloads, approved by the owner on 2026-11-01 (FR-046)

On 2026-11-01 the owner approved every file in the two tables below, each as listed with its
source, size and licence ("Tool acquisition" in the spec's Review & Approval table). Nothing
else is covered: a file not listed here, the tools under "Not requested", or a file whose source
or licence differs from its row, or whose size differs from a size given in bytes, needs its own
permission. Each file is fetched when the task that uses it is reached. Nothing in this plan
depends on any of them; without them the work uses the tools of R12 and records each gap as an
open item. The requests below were prepared on 2026-11-01 from the hosts' pages and from header
requests, with no file body downloaded. A size comes from the server's header where it gave one,
and otherwise as the host lists it. The IACR ePrint archive, the IACR conference archive and the
ToSC journal site refused scripted requests (HTTP 403 or a bot check), and nothing was done to
get around that: for those papers the table names a copy elsewhere, or the owner downloads the
file in a browser into a new folder and gives its path.

**Papers.** Each is read and cited, kept locally with its SHA-256 and never committed, so its
licence does not touch the project's GPL-3.0.

| File | Source | Size | Licence | Use | Without it |
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

| File | Source | Size | Licence | Use | Without it |
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
run from inside that directory, Python reading it runs with `-I`, and its SHA-256 and size are
recorded against its row.
