# Research Note: Strategy for a Cryptographic Redesign of PhycoWeb-PRNG

Date: 2026-10-31.

**Status:** a proposal for owner review, drafted by the AI coding agent. It is not independent
cryptographic advice (security.md §16), makes no security claim and changes no requirement. It
builds on [security.md](../../security.md) 2.6 and [seed-entropy-bound.md](seed-entropy-bound.md),
and is meant as the input for the next Spec Kit feature (§9.2). Once approved, it supersedes the
suggested feature description in §6 of that note. security.md 2.7 applies §7.3 of this note and
records S15 (§3.3); the prompts to run next are in [next.md](../../next.md). Outline A of
[`research/assertion-outlines.md`](../assertion-outlines.md) restates this note's argument as an
assertion outline: three claims, four reasons each, one piece of evidence per reason. Outline D
there, with the hardware note
[`research/hardware/vhdl-genai.md`](../hardware/vhdl-genai.md), proposes rules for AI-assisted
VHDL, which security.md 2.8 adopts in its section 13.

**Governed by:** the [constitution](../../.specify/memory/constitution.md) 1.2.0, above all its
Security Policy. Where this note and the constitution differ, the constitution applies.

> Passing statistical batteries does not show cryptographic security. This generator must not be
> used to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts.

## 1. Summary

- **phyco-v2 cannot be shown secure, whatever further tests it passes.** Its 64-bit seed caps any
  security level at 64 bits (S1–S3). Its step merges states (S13), its vein values are confined
  and biased (S12, S14, S15), and its statistical quality comes from two ARX terms added to the
  slime-mould dynamics (S11). A cryptographic route therefore needs a new primitive with a new
  model ID (FUT-SEC-7). The verdict of battery attempt 1 does not change this.
- **"Proving" a generator secure has a precise and limited meaning.** No practical symmetric
  design can be proven secure outright: such a proof would show that one-way functions exist, and
  hence that P ≠ NP. The accepted standard is a layered argument (§2):
  - a mode whose security is proven relative to one stated assumption about its primitive;
  - a primitive whose resistance to the main attack classes is bounded by proofs where possible;
  - years of public, independent cryptanalysis with a documented security margin;
  - implementations shown to compute the specified function.

  Statistical batteries only screen for defects.
- **Recommended architecture** (§4): a keyless, bio-inspired permutation Π on the grid, bijective
  by construction, used inside a keyed duplex mode (instantiate, generate, forget, optional
  reseed). The security argument then reduces to one falsifiable statement: Π has no structural
  distinguisher within the claimed limits. Every analysis in §6 tries to falsify it.
- **Parameters** (§4.4): a target strength of 128 bits; a 256-bit key (128 bits plus a 128-bit
  nonce is the minimum the constitution allows); a capacity of at least 256 bits; 4×4 as the first
  size that could carry a claim. With two 32-bit words per node, the 2×2 ring cannot meet
  FUT-SEC-2, so it becomes a reduced research variant (§3.3).
- **Programme** (§8): six Spec Kit features, 004 to 009, from design to an owner decision on a
  claim, each with ⛔ gates. The first prompt is in §9.2. A claim, if one is ever made, would come
  years after the design freeze and only after independent review.

## 2. What "proving security" can mean

### 2.1 Kinds of evidence

| Evidence | What it establishes | Example | phyco-v2 |
|----------|---------------------|---------|----------|
| Unconditional proof | Security with no assumption | none exists for any practical cipher | — |
| Reduction (mode proof) | The construction is as secure as its primitive, up to a stated bound | sponge and keyed-duplex bounds; counter mode from a pseudorandom function | none: there is no mode |
| Proven bounds for attack classes | No differential or linear trail above a stated probability over r rounds; no invariant of a stated kind | wide-trail strategy (AES); long-trail strategy (ARX designs such as Sparx and SPARKLE) | none |
| Structural proofs | Bijectivity, exact diffusion rounds, absence of symmetries | an explicit inverse; a bit-dependency matrix | S12 and S13 show defects |
| Cryptanalysis record | The best attack in each class reaches r of R rounds | ChaCha20: the best published attacks reach about 7 of its 20 rounds | not started |
| Implementation proofs | Code and RTL compute the specified function | formal equivalence; exhaustive checks on reduced widths | three in-project implementations agree |
| Statistical batteries | No defect found by these tests at this sample size | SP 800-22, PractRand, TestU01 | SP 800-22 passed; battery attempt 1 running |

Two cautions apply to the reduction and bound rows:

- A mode proof assumes an ideal primitive, and no real permutation is ideal: even the full-round
  Keccak-f permutation has zero-sum distinguishers of very high complexity (Boura, Canteaut and
  De Cannière, 2011). A claim is therefore stated relative to a random permutation **and limited to
  attacks below the claimed strength**, as in the Keccak team's "flat sponge claim". A
  distinguisher above that limit does not contradict the claim; one below it breaks it.
- Trail bounds bound single trails under the usual independence assumptions. Clustering into
  differentials and linear hulls, and key-dependent effects, need a separate argument.

### 2.2 Claim ladder (proposed for security.md)

Each model carries one level. A level is reached only when its evidence is recorded and its gate
is passed.

| Level | Name | Evidence required | Gate |
|-------|------|-------------------|------|
| L0 | Research candidate | specification; no claim | — |
| L1 | Security target specified | security target, threat model, mode, parameters and generic bounds; FUT-SEC-1 to FUT-SEC-6 met by specification; FUT-SEC-8 done; certification route named (FUT-SEC-9) | spec approval |
| L2 | Internally analysed | design rationale; structural proofs; proven trail bounds; internal attack campaign with validated tools; reduced-round statistical margin | design freeze; result review |
| L3 | Statistically re-validated | the complete statistical programme on unused held-out key sets, per supported size (FUT-SEC-7) | battery freeze; result review |
| L4 | Implementations verified | an implementation from outside the project; VHDL equivalent to the model (FUT-HW-1, FUT-HW-4) | RTL start (Principle VIII gate 2) |
| L5 | Independently reviewed | review by independent experts recorded in the repository (Security Policy (b)); a public analysis period with no attack below the claimed strength on the full rounds | external review |
| L6 | Scoped claim | an owner-approved claim stating version, configuration, property, strength, limits and assumptions | Principle VIII gate 3 |

The order matters under the Security Policy: no evaluation *intended to support a claim* may be
pursued until FUT-SEC-1 to FUT-SEC-9 are met. Work at L1 and L2 is therefore design work and
weakness search, which the policy allows and requires to be reported. External review meant to
support a claim (L5) starts only after L1–L4 have recorded evidence.

## 3. Evaluation of security.md and the repository

### 3.1 What to keep

security.md 2.6 and the repository already do much that a cryptographic programme needs. The
redesign should keep all of it:

- an honest status everywhere, with a verbatim disclaimer generated by code;
- pre-registered protocols frozen before data exists, with seed separation and limited attempts;
- verdicts computed by code and re-scored from saved logs, with positive and negative controls;
- calibration of the decision rule itself (feature 003), and validation of the test harness
  against an oracle (features 001–002);
- binding requirements FUT-SEC-1 to FUT-SEC-9, a threat model, an attack-report template and the
  AI-assistance caveats;
- structural facts recorded with proofs, committed scripts and deterministic outputs (S12–S15).

### 3.2 Gaps for a cryptographic route

| ID | Gap | Where | Proposed change |
|----|-----|-------|-----------------|
| G1 | Nothing defines the content of the "documented, defensible design rationale" the Security Policy requires | §4, §8 | Design-rationale requirements (§7.2 below) |
| G2 | The security definitions are informal; there is no claim template with an advantage bound, data limits per key, a multi-user setting or nonce-misuse behaviour | §3 | Formal definitions and a claim template |
| G3 | The threat model is seed-centric | §5 | Add chosen nonces, nonce misuse, many users, chosen absorbed input, state compromise around forget and reseed, and optionally quantum attackers |
| G4 | Attack classes are missing: slide, invariant subspace and nonlinear invariants, integral and division property, cube, impossible differential, boomerang, differential-linear, rotational-XOR, attacks in the inverse direction, attacks on the mode | §12.1 | Extend the table |
| G5 | The generic bounds omit multi-target key search, the capacity (birthday) bound, quantum search and nonce reuse | §12.2 | Extend |
| G6 | There is no best-attack register and no definition of security margin | §12 | A register: class, rounds reached, complexity, source, date, margin (§6.3) |
| G7 | "Cryptographically evaluated" asks for "substantial cryptanalysis", which cannot be checked | §15 | The claim ladder of §2.2, with measurable criteria |
| G8 | §21 offers a new primitive (A) or an approved DRBG (B), but neither the recommended middle route, a new permutation in a mode with a security proof, nor the option to stop | §21 | Options A2 and C (§4.1) |
| G9 | Analysis tools have no validation plan, although `nistrng` showed that tools can be wrong | §12, §19 | Every tool first re-finds known results (§6.1) |
| G10 | No external design review happens before a design freeze, so a flaw a cryptographer would see at once is found only after implementation and batteries | §7, §14 | An external design-review gate before the freeze of any design meant for a claim (optional amendment, §9.1) |
| G11 | The roadmap does not reflect the Security Policy's order (no evaluation to support a claim before FUT-SEC-1 to FUT-SEC-9) | §22 | Sequence the features as in §8 |
| G12 | FUT-SEC-2 and FUT-GRID-2 conflict at 2×2 | §20.1 | Owner decision (§3.3) |
| G13 | The cryptanalysis instructions name phyco-v2 design 1.0 | §16.4 | One set of instructions per model ID |
| G14 | §1.3 lists Phase 1 as "Not started", although S12–S14 are structural results | §1.3 | "Started: S12–S14 recorded, not yet reviewed" |
| G15 | The AIS 20/31 row says "check the current BSI version", yet FUT-SEC-9 names an AIS 20/31-style evaluation as the example route | §6 | Check the current BSI documents before FUT-SEC-9 is answered |
| G16 | security.md mixes policy, plan, evidence and per-model analysis in 1,360 lines | whole | Keep policy, status and registers in security.md; move per-model detail to research notes |

### 3.3 New finding: the 2×2 ring cannot meet FUT-SEC-2 with design-1.0 veins

FUT-SEC-2 requires a reachable secret state of at least twice the claimed strength: 256 bits for a
128-bit claim. A 2×2 grid with one 32-bit pressure and one 32-bit vein per node has exactly 256
secret bits, so it meets FUT-SEC-2 only if **every** state is reachable.

With the design-1.0 vein update it cannot be, whatever the key interface:

- While D > 2³¹ (class 2 or 3), the decay D >> 4 is at least 2²⁷ and the growth A >> 2 at most
  2²⁶, so D falls by at least 2²⁶ per step and never wraps (D′ ≥ D − (D >> 4)). Within 32 steps
  every vein is at most 2³¹, from any starting value.
- From then on the induction of S12 keeps every D in 0…2³¹.
- After 32 steps the secret state therefore takes at most 2¹²⁸ · (2³¹ + 1)⁴ ≈ 2²⁵² values. The
  measured range of S14 (about 0.80 × 2³⁰ values per vein) suggests about 2²⁴⁷.

More generally, at 2×2 with two 32-bit words per node a 128-bit claim leaves no slack: the map
from key and nonce to state must reach all 2²⁵⁶ states, and a duplex with a 256-bit capacity has
no rate left. FUT-GRID-2 requires FUT-SEC-1 and FUT-SEC-2 at every supported size, including the
smallest. The owner must choose one of:

1. **Recommended:** sizes too small for the claim, 2×2 included, are reduced research variants
   outside every claim, and the claimable sizes start at 4×4. This narrows what can be claimed, so
   it is consistent with "stricter only".
2. Wider node state, for example four 32-bit lanes per node, so that 2×2 holds 512 bits.

Recorded as S15 in security.md 2.7 §9.2, with the check script
[`vein_descent.py`](vein_descent.py): from every start, every vein is at most 2³¹ within 16
steps, a sharper bound than the 32 above.

### 3.4 Lessons from phyco-v2 as requirements for the new design

| Source | Lesson | Requirement for the new design |
|--------|--------|--------------------------------|
| S1–S3 | A 64-bit seed caps everything | Key and nonce sizes from §4.4 (FUT-SEC-1, FUT-SEC-2) |
| S2, group F (slides) | The public forcing repeats every 128 steps | Round constants that never repeat inside Π, and calls separated by domain separators |
| S5 | Every output word is a function of the whole pressure state | Output only the rate part, after a full call of Π |
| S6, S12 | Data-selected shifts gave one effective control bit, and they defeat automated bound tools | Fixed operations only: no data-dependent control flow or shift amounts |
| S7, S8 | Rotation-structured constants and shared seed halves | Constants by a stated rule that breaks rotation and translation symmetry; key loading only through the mode |
| S9, S13 | The step merges states, through the vein decay and a transport zero mode | Π bijective by construction, with a specified inverse, at every size |
| S10 | No period guarantee | The period comes from the mode, not from the dynamics |
| S11 | The mixing came from added terms, not from the model | The rationale names the nonlinear components and gives their bounds |
| S12, S14 | Veins confined below 2³¹ and biased in their top five bits | Every state word full-range; a permutation keeps a uniform state uniform |
| security.md §13; `fast/phyco_stream.c` lines 40–45 and 76 | The class `switch` and the conditional absolute value are branches in software | Constant time by construction in every implementation |
| O1; design.md §7 | About 7 serial carry chains per step | At most one or two 32-bit carry chains per pipeline stage |
| groups E and F | Hand-picked constants; output rotations that align | Every constant generated by a rule and justified by the bounds it gives |

## 4. Recommended security architecture

### 4.1 Options

| Option | Construction | Security comes from | Assessment |
|--------|--------------|---------------------|------------|
| A1 | A new state-evolving keystream generator, as phyco-v2 is today | the whole update, analysed as a stream cipher | Hardest to analyse; no reduction; phyco-v2 shows the failure modes |
| **A2 (recommended)** | A new keyless permutation Π in a mode with a security proof | the proof, plus cryptanalysis of Π | One clear assumption to attack; state rules become parameter rules; mature tools |
| A3 | A new block cipher in counter mode | the cipher's pseudorandomness | Adds a key schedule, a second source of weakness |
| B | An approved DRBG (SP 800-90A) with a validated entropy source | the approved mechanism | The only route to FIPS 140-3; PhycoWeb then adds no security (security.md §21) |
| C | Stop: keep PhycoWeb as a documented non-cryptographic generator | — | A legitimate outcome; the research value remains |

### 4.2 Why A2

- **One assumption.** The mode proof reduces every security property to "Π behaves like a random
  permutation against attacks below the claimed strength". The cryptanalysis has a single target.
- **State rules become parameter rules.** FUT-SEC-2 becomes a capacity of at least 256 bits.
- **Bijectivity is needed anyway**, which removes S13 by construction.
- **Backtracking resistance and reseeding are part of the mode.** A forget call after each request
  gives backtracking resistance. Absorbing fresh entropy gives prediction resistance once a
  validated entropy source exists (FUT-SEC-4).
- **The same architecture as NIST's current draft.** SP 800-90A Rev. 2 (initial preliminary draft,
  2025) proposes an XOF-based DRBG, which is a sponge construction. A PhycoWeb permutation still
  can never be approved (FUT-SEC-9).
- **Hardware fit.** A fixed number of rounds gives constant time, there is no feed-forward state to
  store, and the output is a slice of the state register.
- **Tools exist** for permutations: trail search, division property, algebraic degree.

### 4.3 The construction: PhycoWeb-Duplex (illustrative)

```text
state (b bits) = outer part (rate r) | inner part (capacity c); every bit is secret

Instantiate(K, N, pers): state <- 0; absorb pad(K | N | pers) with its domain separator; Pi
Generate(n):             repeat until n bits: output the outer r bits; Pi
Forget:                  after each request: Pi; overwrite the outer part; Pi
Reseed(E):               absorb pad(E) with its own domain separator; Pi   (only with FUT-SEC-4)
```

The spec must take the security bound from a published theorem for the exact mode it adopts, for
example the keyed-duplex bounds of Daemen, Mennink and Van Assche (2017) or the sponge-based
generator of Bertoni et al. (2010). It must check every precondition of that theorem (padding,
domain separation, key and nonce handling) and derive the output limit per key from it
(FUT-SEC-6). This note states no bound.

**Alternative:** counter mode with feed-forward, block i = Π(x_i) ⊞ x_i with x_i = (K, N, i,
constants), plus fast key erasure (Bernstein, 2017) for backtracking resistance. It gives a
seekable keystream and a guaranteed period, but the input must be kept for the feed-forward.

### 4.4 Parameter rules

| Parameter | Rule | Reason |
|-----------|------|--------|
| Target strength s | 128 bits | FUT-SEC-1 floor |
| Key | 256 bits recommended; at least 128 | 256 bits meets FUT-SEC-2 with the key alone, covers multi-target key search and keeps a margin against quantum search |
| Nonce | at least 128 bits if the key has 128; uniqueness rules stated | key plus nonce must reach 256 bits (FUT-SEC-2; Hong and Sarkar, 2005) |
| Capacity c | at least 2s = 256 bits | generic sponge and duplex bounds |
| Rate r | b − c | output per call of Π |
| Rounds R | a pre-registered rule (§5.5) | margin over the best distinguisher |
| Output limit | from the mode's bound | FUT-SEC-6 |
| Word width | 32 bits; reduced variants at 8 and 16 | the 32-bit limit of feature-002 FR-002; analysis on reduced widths |

### 4.5 Grid sizes

With two 32-bit lanes per node (pressure and vein), b = 64 · n² bits:

| Grid | b (bits) | Rate with c = 256 | Status |
|------|----------|-------------------|--------|
| 2×2 | 256 | 0 | reduced research variant only (§3.3) |
| 3×3 | 576 | 320 | odd torus: needs a three-colour update schedule (§5.1) |
| 4×4 | 1,024 | 768 | first claimable size; validated first (FUT-GRID-5) |
| 8×8 | 4,096 | 3,840 | — |
| 16×16 | 16,384 | 16,128 | rounds grow with the diameter (§5.4) |

Information moves one hop per update (FUT-GRID-3), so full diffusion takes at least about the grid
diameter, and R grows with n. The output per round, r/R, still grows with n.

## 5. Design rules for the permutation Π

### 5.1 Keep the metaphor, replace the mechanisms that failed

| Physarum element | phyco-v2 mechanism and its problem | Rule for Π |
|------------------|------------------------------------|------------|
| Pressure at nodes, conductance on channels | P and D words; D confined and biased (S12, S14) | Two full-range 32-bit lanes per node |
| Flux driven by pressure differences | asr of the difference, then T = P − Q[k] + Q[k−1]: a diffusion step with zero modes (S13b) | Feistel-type coupling: a lane gains F(neighbour lanes), where F does not read that lane, so each update is invertible whatever F is |
| Synchronous update | every node at once, which allows the zero modes | Updates by colour class: red-black (checkerboard) on even tori, as in red-black Gauss–Seidel, and three colours otherwise. Each class update is invertible and local |
| Vein growth and decay | D′ = D + \|Q\|/4 − D/16: many-to-one (S13a) and confining (S12) | An invertible accumulator: the vein lane gains a function of its node's flux, with no lossy self-term. A kept decay must be an invertible self-map |
| Food forcing | a public 128-step table (S2) | Round constants injected at food nodes by a stated rule, different in every round and at every food node |
| Peristaltic rotation | constants 5, 11, 19, 27, which align in the output (group F) | Rotations by a rule, chosen by the trail bounds they give |
| Frustrated Foraging | a threshold-triggered XOR: data-dependent, hard to analyse, a fault-injection target (security.md §13) | Removed from Π, or replaced by a fixed constant schedule; feature-002 FR-004 and FR-005 re-decided |
| Conductance classes | data-selected shifts (S6, S12) | Fixed operations only |
| Output tap | a function of all four pressures (S5) | The rate part of the duplex state |

The rationale may explain Π through this mapping, but no security argument may rest on it.
Chaos-based designs have a long record of failure for exactly that reason (Alvarez and Li, 2006),
and the cellular-automaton generator Rule 30 (Wolfram, 1986) was attacked successfully by Meier
and Staffelbach (1991).

### 5.2 The nonlinear component

S11 showed that the mixing must be designed, not hoped for. Two families fit the grid:

- **ARX** (add, rotate, XOR): the carries of modular addition are the only nonlinearity. It suits
  FPGA carry chains and the current design vocabulary, and exact differential and linear models of
  addition exist (Lipmaa and Moriai, 2001; Wallén, 2003).
- **Boolean** (AND-based, χ-like maps on bit slices): degree 2, no carry chains, very low latency,
  analysed with S-box models. The algebraic degree grows slowly and needs its own margin.

Explore both on reduced widths during the design, with development keys only. Choose by the proven
bound per round and per unit of hardware cost. Either choice must keep to the operation limits of
feature-002 FR-001 (no multiplication), and must not reuse a published primitive or its constants
(FR-007).

### 5.3 Proven bounds by construction

The strongest proof component available is a trail bound that follows from the design strategy:

- **Long-trail strategy for ARX** (Dinu et al., 2016; the Alzette ARX-box of SPARKLE, Beierle et
  al., 2020): a small ARX-box per node, whose best trail probabilities over a few rounds are
  computed exhaustively; a local linear layer between nodes; a bound for the whole permutation by
  counting active boxes. A node's pressure and vein lanes form a natural 64-bit box.
- **Wide-trail strategy** for S-box designs (Daemen and Rijmen, 2002).
- **Solver search** (SAT, SMT or MILP) for the best trails over the first rounds of the whole
  permutation, as a cross-check.

The methods are reusable; the published components are not (FR-007).

### 5.4 Diffusion

- Compute the exact bit-dependency matrix of Π and of Π⁻¹, round by round. Report R_f and R_b, the
  rounds after which every output bit depends on every input bit, in each direction.
- Locality bounds R_f below by about the grid diameter. Lay out a torus as a folded torus so that
  the wrap-around links stay short (Principle III).
- Report the avalanche on development keys, and the bit bias of every state word, as S14 did.

### 5.5 Round count by a pre-registered rule

Fix the rule before the design freeze, for example R = max(2 · R_dist, R_bound + Δ,
2 · max(R_f, R_b)), where:

- R_dist is the largest number of rounds on which the internal campaign found any distinguisher,
  including reduced-round batteries;
- R_bound is the number of rounds after which the proven trail bound falls below 2⁻ˢ;
- Δ is a margin of at least 2 rounds.

Rounds are added by the rule and never removed once results exist. Any change is a new model ID.

### 5.6 Constants, hardware and variants

- **Constants** (FUT-GRID-4): generated by a committed script from a stated rule, for example an
  LFSR or the digits of a mathematical constant. Tests check that no non-trivial translation or
  rotation of the grid preserves the constant pattern.
- **Hardware co-design** (FUT-HW-1, FUT-HW-2): at most one or two 32-bit carry chains per pipeline
  stage; fixed latency and constant time; zeroization of the whole state; no key read-back.
  Absorption and output use a registered input and output tree over the rate lanes, as
  FUT-GRID-1 already allows for the output.
- **Specified for translation** (security.md 2.8 §13): the design document states the width,
  signedness and shift kind of every operation and lists the model's edge states, so that an RTL
  draft, by a person or an AI tool, has nothing to guess
  ([hardware note](../hardware/vhdl-genai.md) §5).
- **Reduced variants**: word widths 8, 16 and 32, fewer rounds and smaller grids, all from the same
  generics, each with its own variant ID. The production interface refuses them, as the
  development tools refuse held-out seeds.

## 6. Analysis programme

### 6.1 Validate every tool first

Before its negative results count, every analysis tool must re-find known results:

- on phyco-v2 and its reduced variants: the 64-bit seed bound on a reduced domain (FUT-SEC-8,
  about 2³² × 259 steps, 3.6 core-hours of the C stream), the merging of S13, the bounded veins
  of S12 and S15 and the bias of S14;
- for trail search: a published optimal trail result for a reference cipher.

This is the lesson of `nistrng` and of the STS oracle comparison (security.md §11.2).

### 6.2 Campaign

Each investigation is pre-registered (security.md §12.3: observations, budget, success metric,
random baseline) and reported as security.md §12.4 requires.

| Area | Method | Targets | Output |
|------|--------|---------|--------|
| Generic bounds | Written derivations; preconditions of the mode theorem checked | full design | rationale |
| Bijectivity | Explicit Π⁻¹ in the model; tests of Π⁻¹(Π(x)) = x; exhaustive bijectivity on the smallest variant | all sizes; 2×2 at 4-bit words (2³² states) | S-facts |
| Diffusion | Exact dependency matrix in both directions; avalanche; per-word bias | all sizes | R_f, R_b |
| Differential and linear | Proven bounds (§5.3); solver search for best trails and for clustering | 1…k rounds; reduced widths | R_bound |
| Algebraic and integral | Division property, degree growth, cube and zero-sum distinguishers | reduced rounds | rounds reached |
| Invariants and symmetry | Invariant subspaces, nonlinear invariants, rotational and rotational-XOR pairs, slides, grid symmetries | full design | S-facts |
| State recovery | Guess-and-determine; SAT state recovery from outputs | reduced variants, then the scaling | complexity trend |
| Key and nonce loading | Related-key and related-nonce differentials through instantiation; weak keys (FUT-SEC-5) | full design | rounds reached |
| Machine learning | Distinguishers as in Gohr (2019), confirmed on fresh data | reduced rounds | rounds reached |
| Statistics | Reduced-round sweep on development keys, to find the last round the batteries detect; then the held-out programme (FUT-SEC-7) | all sizes | R_dist input; L3 |
| Side channels and faults | Constant time by construction; the board tests of FUT-HW-5 | C, VHDL, board | FUT-HW-5 record |
| Implementations | Independent C; VHDL in GHDL, and in NVC if approved; mutation-checked testbenches (security.md §13); formal or exhaustive equivalence on reduced widths; long-run CRC on the board | all sizes | L4 |

### 6.3 Best-attack register

security.md keeps one row per attack class for the current model: rounds reached out of R,
complexity, data, source (internal or external, with a reference), date and margin. The margin is
R divided by the rounds of the best attack. A claim is never stronger than the weakest row.

### 6.4 Candidate tools

Each download needs the owner's permission (name, source, size), and its licence must allow use in
a GPL-3.0 project. Candidates: the SAT solvers CaDiCaL, Kissat and CryptoMiniSat; Z3; OR-Tools
CP-SAT; HiGHS or SCIP for MILP; CryptoSMT and CASCADA for ARX trail search; SageMath for algebra;
Hypothesis for property tests; Cryptol and SAW for a formal specification and code equivalence.
For VHDL ([hardware note](../hardware/vhdl-genai.md) §3): GHDL and NVC for simulation, VUnit or
cocotb for testbenches, VHDL-LS for analysis while editing, the GHDL plugin for Yosys with
SymbiYosys for synthesis checks and formal properties, and openXC7 as an open cross-check of fit
beside Vivado. Solver, synthesis, place-and-route and formal runs are heavy and must never
overlap battery runs.

## 7. Guidelines for security.md updates

### 7.1 Rules

1. **One claim register.** Each model ID has a level from §2.2 and a one-line claim, or "none".
   Claim wording appears nowhere else.
2. **Facts are not claims.** S-entries record facts: proofs, measurements, bounds. "No attack found
   within budget B" is a fact about an investigation, never a claim.
3. **Every entry is reproducible**: a committed script, a deterministic output, the model hash and
   the command, as S12–S14 already are.
4. **One section per model.** phyco-v2's S-table stays as history. The new model gets its own
   S-table and best-attack register, and the lessons table (§3.4) links the two.
5. **Downgrade at once.** An attack below the claimed strength withdraws the claim immediately,
   with a history entry and a README update. Upgrades follow the ladder and its gates.
6. **Stricter only**, for claims too: a later version may narrow a claim, never widen it without
   new evidence.
7. **Precise vocabulary**: "proven bound", "best known attack", "no attack found within budget",
   "not evaluated". Never "secure", "unbreakable" or "proven secure".
8. **Dated status.** Re-check the standards at every version, as §6 does now.

### 7.2 Design-rationale requirements (Security Policy (a))

The rationale of any model meant for a claim states:

- the security target, the threat model and the claim template (G2, G3);
- the mode, the theorem it relies on, and how each precondition is met;
- the role of every component and why it is there, including what the slime-mould mapping does and
  does not contribute;
- the source of nonlinearity and its proven bounds;
- diffusion in both directions;
- every constant, with its generating rule;
- the round-count rule and the resulting margin;
- the known limitations and the attacks it was designed against.

### 7.3 Changes for security.md 2.7 (applied on 2026-10-31)

| Section | Change |
|---------|--------|
| §1.1, §1.3 | Claim level per model; Phase 1 "started" (G14) |
| §3 | Formal definitions and a claim template (G2) |
| §5 | Threat-model extensions (G3) |
| §6 | Add NIST SP 800-232 (Ascon, 2025), the eSTREAM portfolio, ISO/IEC 29192 and BSI TR-02102-1 as comparison references; check the current AIS 20/31 documents (G15) |
| §7 | A design phase and the external design-review gate (G10) |
| §8 | The design-rationale requirements (§7.2) |
| §9.2 | S15 (§3.3) |
| §12 | New attack classes, generic bounds and the best-attack register (G4–G6) |
| §15 | The claim ladder in place of the classification (G7) |
| §16.4 | Instructions per model ID (G13) |
| §20.1 | The FUT-SEC-2 and FUT-GRID-2 decision (G12) |
| §21 | Options A2 and C (G8) |
| §22 | Stage 5a expanded into features 004–009 (§8) |

Applied in security.md 2.7, which also adds S15 to the priorities table (§20) and points §24 to
the next feature. The new standards rows were checked on 2026-10-31. Version 3.0 of the AIS 20/31
functionality classes (2024) was found but not read, so its list of classes is unconfirmed.

## 8. Spec Kit programme

### 8.1 Before the first prompt

1. Finish feature 003: T035–T044, including the owner reviews ⛔ T038 and ⛔ T044.
2. Run `/speckit-converge` on feature 003; it runs automatically at that point.
3. The owner decides the questions in §8.4, or leaves them to `/speckit-clarify`.
4. Optionally, amend the constitution (§9.1).
5. The owner approves this note and the security.md 2.7 to 2.9 changes.

### 8.2 Features

| Feature | Goal | Main outputs | Gates | Exit |
|---------|------|--------------|-------|------|
| 004 Cryptographic architecture and phyco-v3 design | Reach L1, start L2 | FUT-SEC-8 demonstration; security target; mode; Π with its inverse; reduced variants; rationale; Python model; vectors and known-answer tests; structural evidence; first proven bounds | spec, plan, tasks; design review; ⛔ design freeze | a frozen design, or stop |
| 005 Internal cryptanalysis | Complete L2 | validated tools; the pre-registered campaign (§6.2); best-attack register; reduced-round battery sweep; margin | campaign freeze; ⛔ result review | margin rule met, or a new model ID, or stop |
| 006 Implementations and equivalence | L4 for software and RTL | independent C, from outside the project if possible; generic VHDL (FUT-HW-1), under the AI-assisted RTL rules of security.md §13; GHDL equivalence, and NVC if approved; mutation-checked testbenches; long-run CRC; formal equivalence where feasible | ⛔ RTL start (Principle VIII gate 2) | equivalence evidence |
| 007 Statistical re-validation | L3 | held-out key sets per size; calibrated rules; a deterministic positive control; graded negative controls (group F) | ⛔ battery freeze; ⛔ result review | a verdict per size |
| 008 Hardware validation | FUT-HW-2 to FUT-HW-5 | Arty A7-100T fit, timing, throughput, power, on-board equivalence, board security tests | ⛔ RTL review | board evidence |
| 009 External review and claim decision | L5, then L6 | review package (security.md §14); independent review recorded; publication and reduced-round challenges, if the owner authorizes each (Principle IX); a public analysis period; the claim decision | ⛔ publication; ⛔ claim (gate 3) | a scoped claim, or none |

The order is 004, 005, 006, 007, 008, 009; 008 can run alongside 007. An attack on the full
rounds at any point sends the work back to 004 with a new model ID, or stops it.

The Security Policy requires the spec that introduces the new key interface (feature 004) to carry
FUT-SEC-1 to FUT-SEC-9 as requirements traced to tasks and evidence. Those that later features
deliver, such as FUT-SEC-7's held-out statistical programme, stay open in feature 004's phase
report (Principle VII).

### 8.3 Checklist focus prompts for feature 004 (`/speckit-checklist`, after the plan)

- security: "security: key, nonce, capacity, reachable state, FUT-SEC-1..9 by specification,
  claim wording, the Security Policy's order";
- design rationale: "design rationale: every component, constant and round count justified;
  inverse specified; no security argument resting on the slime-mould mapping";
- analysis: "analysis: tools validated on known results first; pre-registered metrics, budgets and
  baselines; reduced variants from the same generics";
- protocol: "protocol: development keys only before the freeze; every variant logged;
  stricter-only";
- hardware readiness: "hardware: carry chains per stage, constant time, zeroization, grid
  generics, the width, signedness and shift kind of every operation, FUT-GRID-1..5,
  FUT-HW-1..5";
- reproducibility: "reproducibility: commands, versions, hashes, deterministic outputs, line
  endings".

### 8.4 Decisions for the owner or `/speckit-clarify`

1. Mode: keyed duplex (recommended), or counter mode with feed-forward and fast key erasure.
2. Key: 256 bits (recommended), or 128 bits plus a 128-bit nonce.
3. Claimable sizes: from 4×4, with 2×2 as a research variant (recommended), or wider nodes.
4. Nonlinearity: ARX, Boolean, or both explored and one chosen by a stated rule.
5. Frustrated Foraging: removed from Π (recommended), or kept and analysed (FR-004, FR-005).
6. The FR-007 rule: standard modes allowed, standard primitives and their constants forbidden
   (recommended).
7. Prediction resistance: out of scope until a validated entropy source exists (recommended), or a
   separate entropy-source feature.
8. Certification route for FUT-SEC-9: independent academic cryptanalysis plus an AIS 20/31-style
   evaluation, after version 3.0 of the BSI functionality classes (2024) has been read
   (security.md §6).
9. External expertise: who reviews the design before the freeze, and who reviews the evidence for
   L5.

## 9. Prompts

### 9.1 Optional constitution amendment (`/speckit-constitution`)

```text
Amend the constitution for the cryptographic redesign. MINOR: add a review gate to Principle VIII:
before the design freeze of any model intended to support a cryptographic claim, a review of its
specification and design rationale by an independent cryptographer MUST be recorded in the
repository. PATCH: clarify that Principle I's widths (16-bit signed state, 32-bit output words)
are defaults that a ratified spec may change, as phyco-v2's 32-bit state already does. The
Security Policy and FUT-SEC-1 to FUT-SEC-9 are unchanged, and may only become stricter.
```

### 9.2 Feature 004 (`/speckit-specify`)

The same text is in [next.md](../../next.md) §4, which is the copy to use if the two ever
differ. It was updated for security.md 2.7 (S15, and the sections it adds), and cites 2.9.

```text
Cryptographic redesign of PhycoWeb-PRNG, part 1: the security target, a permutation-based
architecture and the phyco-v3 design, up to a frozen design. This feature makes no security
claim; it prepares the evidence a later claim would need (constitution 1.2.0, Security Policy).
It aims at claim level L1 and starts L2 (security.md section 15).

Why: phyco-v2 cannot support any cryptographic claim. Its 64-bit seed caps security at 64 bits
(security.md S1-S3), its step merges states (S13), its veins are confined and biased (S12, S14),
a 2x2 ring that keeps its vein update cannot reach the 2^256 secret states FUT-SEC-2 requires for
a 128-bit claim (S15), and its mixing came from added terms rather than a designed component
(S11).

Scope, in order:
1. Reproduce phyco-v2's 64-bit seed bound on a reduced seed domain before any new key interface
   is implemented (FUT-SEC-8).
2. Specify the security target as requirements, not claims: the properties sought
   (indistinguishability and backtracking resistance; prediction resistance only with a
   validated entropy source, otherwise out of scope), a 128-bit target strength, key and nonce
   sizes, output limits per key and per key and nonce, a threat model extended for keys, nonces,
   multiple users and state compromise, and the generic bounds every parameter must respect.
3. Specify a keyless, bio-inspired permutation on a parameterised grid (FUT-GRID-1 to
   FUT-GRID-5): bijective by construction with a specified inverse; fixed operations only (no
   data-dependent control or shift amounts); full-range state words; round constants and
   rotations generated by stated rules that break grid symmetry and never repeat inside a call;
   at most one or two 32-bit carry chains per pipeline stage; and a round count fixed by a
   pre-registered rule from diffusion, proven trail bounds and a margin. Document the slime-mould
   mapping, but rest no security argument on it.
4. Specify a mode with a published security proof that reduces the generator to the permutation
   (keyed duplex recommended: instantiate, generate, forget, optional reseed), with padding and
   domain separation, and state which grid sizes are claimable, deciding the FUT-SEC-2 and
   FUT-GRID-2 conflict at 2x2 (security.md section 20.1); 2x2 is expected to become a reduced
   research variant.
5. Define reduced variants (word widths 8, 16 and 32, fewer rounds, small grids) from the same
   generics, which the production interface refuses.
6. Deliver: a design document with its design rationale (security.md section 8); a Python
   reference model of the permutation, its inverse and the mode; golden vectors and known-answer
   tests per size; structural evidence (inverse tests, exhaustive bijectivity on the smallest
   variant, exact diffusion in both directions, per-word bias, symmetry checks on the constants);
   and first proven or solver-computed trail bounds on reduced rounds, from tools first validated
   on known results, including re-finding S12-S15 on phyco-v2.
7. Use development keys only, log every candidate design, archive phyco-v2 in baseline/
   (Principle V), and end with an owner design review, an external design review if one can be
   arranged (security.md section 7), and the design freeze.

Carry FUT-SEC-1 to FUT-SEC-9 as requirements traced to tasks and evidence (Security Policy);
FUT-SEC-7's held-out statistical programme is delivered by a later feature and stays open in this
feature's report. Re-decide every carried-over feature-002 requirement (FR-001 to FR-009),
including the FR-007 rule on standard primitives and standard modes. Out of scope: RTL, the
held-out statistical programme, the full cryptanalysis campaign, external review, publication and
any security claim. Inputs: research/security/crypto-redesign-strategy.md, security.md 2.9
(sections 3, 5, 8, 9.2, 12, 15, 20.1 and 21), and research/security/seed-entropy-bound.md
section 5 with the section 5.3 checklist groups A to G.
```

### 9.3 Later features (`/speckit-specify`, one per feature)

- **005**: "Internal cryptanalysis of the frozen phyco-v3 design: validate every analysis tool on
  known results first (phyco-v2 S12-S15 and the FUT-SEC-8 search; a published optimal trail for a
  reference cipher), then run a campaign pre-registered before results exist over the classes in
  research/security/crypto-redesign-strategy.md section 6.2, on the full design and reduced
  variants, with budgets, success metrics and random baselines; keep a best-attack register;
  measure the last round the batteries detect on development keys; apply the round-count rule. An
  attack on the full design below the target strength stops the claim route or returns to design
  with a new model ID. Weakness search only; no security claim."
- **006**: "Implementations and equivalence for phyco-v3: an independent C implementation, written
  outside the project if possible, and a generic, vendor-neutral VHDL core with grid size and word
  width as generics and 0 DSP blocks (FUT-HW-1), bit-exact with the Python model in GHDL on the
  golden vectors and known-answer tests (Principle II), plus formal or exhaustive equivalence on
  reduced widths and a long-run CRC check. Any RTL or testbench drafted with an AI tool follows
  security.md section 13 and research/hardware/vhdl-genai.md section 5: expected values only
  from the Python model, the golden vectors and the C implementation; numeric_std types of
  explicit width and signedness, never INTEGER, for state words; every draft analysed, checked
  for synthesis and simulated bit-exact, in NVC as well as GHDL if the owner approves its
  download; testbenches shown to fail on a recorded catalogue of seeded mutants before their
  passes count; the drafting session never writing the only testbench that judges its design;
  and provenance recorded for every drafted file. RTL starts only after the owner's approval
  (Principle VIII gate 2). No security claim."
- **007**: "Statistical re-validation of phyco-v3 (FUT-SEC-7): the complete programme (SP 800-22,
  PractRand, TestU01, and Dieharder or a recorded reason) on unused held-out key sets per supported
  size, 4x4 first, with decision rules calibrated before the freeze, a deterministic positive
  control (for example ChaCha20 with a published key) and graded negative controls; pre-registered
  and stricter-only; with the open items of the 003 attempt-1 phase report (runs scheduled from
  any role as slots free up, with times projected per role and generator; the freeze's status set
  on approval; the lut-v1 close-pairs times explained or bounded; a disclaimer in every provenance
  record, a battery form of the generated disclaimer, and `git_head`, `git_dirty`, `versions` and
  `command` in every record, all fixed before the next freeze).
  Passing shows that no defect was found, not security."
- **008**: "Hardware validation of phyco-v3 on the Arty A7-100T (FUT-HW-2 to FUT-HW-5): Vivado
  post-route resources and timing at 4x4 and at the largest grid that fits, with an optional
  open-flow fit (openXC7) as a cross-check that never replaces Vivado's timing; on-board
  throughput and power, on-board equivalence with the golden vectors and a long-run CRC, and the
  board security tests (constant time, no key read-back, zeroization, fault behaviour), with side
  channels recorded as untested without measurement equipment. Synthesis and place-and-route
  runs never overlap battery runs."
- **009**: "External review and claim decision for phyco-v3: assemble the review package of
  security.md section 14, obtain and record review by independent experts (Security Policy (b)),
  and, only if the owner authorizes each outward action, publish the design and reduced-round
  challenges and open a public analysis period. At its end the owner decides on a scoped claim
  (Principle VIII gate 3) under the route named for FUT-SEC-9, or records that none is made."

## 10. Further ideas

| Idea | Value | Note |
|------|-------|------|
| Validate the new tools on phyco-v2's known defects | high | §6.1; turns S12–S15 into a test set |
| Public reduced-round challenges with stated targets | high | Concrete targets attract outside cryptanalysis; an outward action for the owner (Principle IX) |
| A machine-readable claim and evidence register, with a test that README, security.md and the disclaimers agree with it | high | Automates the claims check (feature-003 T041) |
| A formal specification (for example in Cryptol) from which vectors are generated and code is checked | medium | Reduces the common-mode risk of security.md §10.2 |
| Node pressure and vein lanes as one 64-bit ARX-box per node | medium | Keeps the metaphor inside a provable-bound strategy (§5.3) |
| Food schedule as round constants and domain separators | medium | Different constant streams for instantiate, generate, forget and reseed |
| Known-answer self-test at start-up in the RTL | medium | Common practice; not a FIPS claim |
| Benchmark against Ascon, Trivium and Grain-128AEAD on the same board | high | Tests the project's premise: LUTs, flip-flops and throughput per bit of security. If PhycoWeb needs many times the resources for the same security, record it |
| Pre-registered stop rules in the spec | high | For example: an attack below the target on the full rounds, or bounds unobtainable beyond k rounds |
| An entropy-source feature for reseeding (FUT-SEC-4) | low now | A large separate effort (SP 800-90B); out of scope until a claim is near |
| Fault countermeasures in hardware (duplicated rounds, state parity) | later | With FUT-HW-5 |
| Nonce-misuse behaviour documented | medium | Two streams with the same key and nonce are identical |
| A scenario game on public scrutiny, with humor and emotional intelligence (experiment E1) | medium | Could help find and keep the reviewers that L5 needs; makes no claim; involves people, so ethics approval comes first ([next.md](../../next.md) §7) |
| Two simulators must agree (GHDL and NVC) | high | A simulator bug then has to repeat itself in an independent tool to hide an RTL bug ([hardware note](../hardware/vhdl-genai.md) §6) |
| Mutation-checked testbenches | high | A testbench counts only after it fails on seeded mutants of the design, as in AutoBench's Eval2; the kill rate goes into the phase report (security.md §13) |
| cocotb with the Python model as the live oracle | high | No expected value is copied by hand; GHDL support is experimental, NVC from 1.11.0 |
| Constructed-state vectors for the corners of phyco-v2: D = 2³¹ and the class-3 states | high | For roadmap stage 7: at D = 2³¹ a VHDL-2008 INTEGER overflows, a signed comparison flips and class 2 is used ([hardware note](../hardware/vhdl-genai.md) §5.2) |
| Formal properties on reduced widths (SymbiYosys, with PSL through the GHDL plugin for Yosys) | medium | Zeroization, fixed latency and equivalence; PSL support is partial |
| An open-flow fit (openXC7) beside Vivado | medium | Vivado stays the reference for FUT-HW-2; a disagreement is a finding to explain |
| An E1 card from the first RTL-versus-model mismatch | low | Written only after the cause is found and recorded ([scrutiny game](../engagement/scrutiny-game.md) §3) |

Rejected ideas, with reasons:

- **Key-dependent topology or wiring**: makes automated analysis and constant-time hardware much
  harder, for no provable gain.
- **Data-dependent rotations or shifts** (as in RC5): the same objections; S12 showed how little
  control they add here.
- **Chaos or Lyapunov-exponent arguments** as security evidence (Alvarez and Li, 2006).
- **Choosing rounds or constants from held-out results**: selection bias (feature-002 O6).
- **Emotion recognition from faces or voices to steer E1**: not valid (Barrett et al., 2019),
  biased (Rhue, 2018), and prohibited in education institutions by the EU AI Act; players report
  their own feelings instead ([assertion outlines](../assertion-outlines.md), Claim C1).
- **Accepting AI-drafted RTL because it compiles and its own testbench passes**: compiling proves
  only that it is a design, and a testbench from the same session shares its misreading of the
  specification ([hardware note](../hardware/vhdl-genai.md) §2;
  [assertion outlines](../assertion-outlines.md), Claim D2).

## 11. Risks and expectations

- Most new symmetric designs are broken or never reviewed. Public review takes years: the eSTREAM
  project ran from 2004 to 2008, and NIST's lightweight-cryptography process from 2018 to the
  selection of Ascon in 2023, with SP 800-232 following in 2025.
- FIPS 140-3 approval stays impossible (FUT-SEC-9), and the outcome of an AIS 20/31-style
  evaluation of a custom generator is uncertain.
- The programme needs cryptographers. An AI assistant can draft, implement and search for
  weaknesses, but cannot provide independent review (security.md §2.1, §16).
- A good outcome would read roughly: "phyco-v3, 4×4: a published permutation-based generator with
  proven trail bounds over r rounds and a best known attack on q of R rounds after N years of
  public analysis, under an owner-approved scoped claim; not FIPS-approved." Option C, stopping
  with a well-documented research generator, is also an honest result.

## 12. References

- Alvarez, G. and Li, S. Some basic cryptographic requirements for chaos-based cryptosystems.
  International Journal of Bifurcation and Chaos 16(8), 2006.
- Beierle, C. et al. Alzette: a 64-bit ARX-box. CRYPTO 2020; and the SPARKLE submission to the
  NIST lightweight-cryptography process.
- Bernstein, D. J. Fast-key-erasure random-number generators. Blog post, 2017.
- Bertoni, G., Daemen, J., Peeters, M. and Van Assche, G. Sponge-based pseudo-random number
  generators. CHES 2010; and Cryptographic sponge functions (the flat sponge claim), 2011.
- Biryukov, A. and Wagner, D. Slide attacks. FSE 1999.
- Boura, C., Canteaut, A. and De Cannière, C. Higher-order differential properties of Keccak and
  Luffa. FSE 2011.
- Daemen, J., Mennink, B. and Van Assche, G. Full-state keyed duplex with built-in multi-user
  support. ASIACRYPT 2017.
- Daemen, J. and Rijmen, V. The Design of Rijndael. Springer, 2002 (wide-trail strategy).
- Dinu, D. et al. Design strategies for ARX with provable bounds: Sparx and LAX. ASIACRYPT 2016.
- Dinur, I. and Shamir, A. Cube attacks on tweakable black box polynomials. EUROCRYPT 2009.
- Gohr, A. Improving attacks on round-reduced Speck32/64 using deep learning. CRYPTO 2019.
- Hong, J. and Sarkar, P. New applications of time memory data tradeoffs. ASIACRYPT 2005.
- Khovratovich, D. and Nikolić, I. Rotational cryptanalysis of ARX. FSE 2010; Ashur, T. and
  Liu, Y. Rotational cryptanalysis in the presence of constants. ToSC 2016.
- Leander, G. et al. A cryptanalysis of PRINTcipher: the invariant subspace attack. CRYPTO 2011;
  Todo, Y., Leander, G. and Sasaki, Y. Nonlinear invariant attack. ASIACRYPT 2016.
- Lipmaa, H. and Moriai, S. Efficient algorithms for computing differential properties of
  addition. FSE 2001; Wallén, J. Linear approximations of addition modulo 2ⁿ. FSE 2003.
- Meier, W. and Staffelbach, O. Analysis of pseudo random sequences generated by cellular
  automata. EUROCRYPT 1991.
- Todo, Y. Structural evaluation by generalized integral property. EUROCRYPT 2015 (division
  property).
- NIST SP 800-90A Rev. 2 (initial preliminary draft, 2025) and SP 800-232 (final, 13 August 2025;
  checked on the NIST CSRC page on 2026-10-31, security.md 2.7 §6).
- For VHDL and AI-assisted design, the sources in §9 of the
  [hardware note](../hardware/vhdl-genai.md).
