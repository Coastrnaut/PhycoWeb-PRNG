# Research Note: Seed-Entropy Bound on PhycoWeb-PRNG Security

Date: 2026-10-31.

**Status:** a finding of the security review ([security.md](../../security.md) 2.0, §9.2,
S1–S5). It was derived from the specification. No attack has been executed. Since
[constitution](../../.specify/memory/constitution.md) 1.2.0 (approved 2026-10-31), the
requirements in §5 are binding policy (Security Policy).

**Applies to:**
- `phyco-v2`: [design.md](../../specs/002-core-dynamics-redesign/design.md) 1.0, model
  `1260142d…`;
- `lut-v1`: same seed domain.

> Passing statistical batteries does not show cryptographic security. This generator must not be
> used to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts.

## 1. Finding

**phyco-v2's seed is four 16-bit words, 64 bits in total. That caps any security level at 64 bits,
however large the internal state, which is below the 112-bit minimum for approved cryptographic
use.**

- **Why state size doesn't help.** The bound holds whatever the quality of the step function.
  The 272-bit state and the 256-step warm-up are both deterministic functions of the 64-bit seed.
- **Where the minimum comes from.** 112 bits is the minimum security strength for approved use
  (NIST SP 800-57 Part 1 Rev. 5, SP 800-131A Rev. 2). SP 800-57 accepts it for applying
  protection only through 2030; from 2031 the minimum is 128 bits. The constitution therefore
  sets 128 bits as the floor for any claim (FUT-SEC-1).
- **Classification** (security.md §9.1): a confirmed upper bound, derived from the
  specification. The generic attack below has not been run.

## 2. Derivation

1. **Seed domain.** Each seed value s₀…s₃ must be in 0…65535. Anything else is rejected:
   `ValueError` in the model, exit 2 from the C stream (`design.md` §3). That gives 2⁶⁴ seeds.
   Extra values add nothing: the Python models read only the first four values of a longer
   sequence (`seed[:4]`), and the C stream rejects a fifth seed argument.
2. **The initial state is a public function of the seed:**
   - P[k] = (s[k] << 16) | s[(k+1) mod 4];
   - D[k] = 0x00010000 << k, a constant;
   - phase_a = phase_b = 0, a constant;
   - then 256 warm-up steps, which are deterministic.

   The state at any step index t is therefore F_t(seed), and at most 2⁶⁴ distinct states exist
   at that index, out of 2²⁷² nominal ones.
3. **Part of the state is public.** The phase counters advance by fixed amounts (4 and 6, mod
   256), have period 128 and do not depend on the seed. Given t, 16 state bits and the whole food
   sequence are known.
4. **Three output words identify the seed.** Each step outputs one 32-bit word, computed from
   the four P words (`design.md` §5). If the map from seed to output behaves like a random
   function, k observed words leave about 2^(64 − 32k) wrong seeds that still fit: about one for
   k = 2, and 2⁻³² for k = 3. Three consecutive words are therefore expected to identify the seed
   uniquely.
5. **Exhaustive search.** For each candidate seed, run 256 warm-up steps plus 3 output steps (259
   steps) and compare. The total is at most 2⁶⁴ × 259 ≈ 2⁷² steps. Recovering the seed gives
   every earlier and every later output of that stream. Unpredictability and backtracking
   resistance both fail.
6. **Measured cost.**
   - The C stream runs 8.5 × 10⁷ steps/s on one core (feature 003,
     `reports/003-extended-batteries-calibration/dev/timing.json`, measured idle on 2026-10-29).
   - So 2⁶⁴ × 259 / 8.5 × 10⁷ ≈ 5.6 × 10¹³ core-seconds, about **1.8 million core-years**.
   - The search parallelizes perfectly and can be vectorized. The design also targets cheap,
     multiplierless hardware with one register-transfer step per update (`design.md` §7), so
     dedicated hardware would cut the cost by orders of magnitude.
   - Work of this size has been done in public. The 2017 SHA-1 collision took about 2⁶³ SHA-1
     computations.
7. **Precomputation (time–memory trade-off).** The state after warm-up depends only on the seed:
   there is no key, nonce or secret position. A Hellman trade-off therefore applies:
   - one precomputation of about 2⁶⁴ seed evaluations;
   - then about 2⁴³ work and 2⁴³ stored entries per target;
   - every later target of the same design is then cheap.
8. **Known and unknown position.** The bound is for the threat-model attacker T1, who knows the
   position, for example the first words after seeding. An unknown offset adds a search over the
   offset range R, about 2⁶⁴ · R steps in the simplest form, and data from many positions makes
   trade-off attacks cheaper.
9. **lut-v1** has the same seed domain, so the same bound applies. It also fails every
   statistical battery.

## 3. What a cryptographic claim would need

| Requirement | Source | phyco-v2 design 1.0 |
|-------------|--------|---------------------|
| Security strength of at least 112 bits through 2030 and 128 bits from 2031; at least 128 bits for any claim here | SP 800-57 Part 1 Rev. 5 (§5.6.3, Table 4, "Security strength time frames"); SP 800-131A Rev. 2; constitution 1.2.0 (FUT-SEC-1) | **at most 64 bits** (this note) |
| Entropy input with at least as many bits of entropy as the security strength, at instantiation | SP 800-90A Rev. 1 (DRBG instantiation) | 64-bit seed |
| Reachable secret state of at least twice the security strength | Babbage–Golić time–memory–data trade-off | 2⁶⁴ reachable states per step index |
| Nonce or IV to separate streams | SP 800-90A (nonce); stream-cipher practice | none |
| Reseed input, for prediction resistance | SP 800-90A | none |
| An approved mechanism, for FIPS 140-3 | FIPS 140-3; SP 800-90A | not possible for any custom design |

## 4. Consequences

- **No feature-002 or feature-003 result changes.** The statistical evidence is unaffected. The
  bound concerns only cryptographic claims, and none has been made.
- **Removing the bound is an algorithm change.** It needs a new seed (key) interface and
  seed-to-state mapping, and probably changes to the state and the step function. Under the
  constitution, that needs:
  - an approved spec (Principle VI);
  - an owner review (Principle VIII);
  - a new model ID and new golden vectors;
  - a new statistical evaluation on unused held-out sets;
  - requirements FUT-SEC-1 to FUT-SEC-9 (§5) carried in that spec (Security Policy).
- **Why it probably means another core redesign, not just a wider seed:**
  - In design 1.0, the seed fills only the four P words (128 bits); D and the phases start from
    constants.
    - A 128-bit key loaded into P alone would give 2¹²⁸ reachable states per step index. That
      meets the exhaustive-search bound for 128 bits.
    - D would still be public at reset, so the warm-up would have to do all the mixing.
    - Loading key material into D changes the vein dynamics that feature 002 tuned: the
      conductance classes, and the disruption rate required by feature-002 FR-005. That
      behaviour would have to be re-established.
  - The phase counters cannot carry key material without changing the food sequence, which is
    public by design.
  - Using several streams per key needs a nonce or IV. A prediction-resistance claim needs a
    reseed input fed from an entropy source. Neither exists.
  - Key and IV loading is a classic weak point of new stream ciphers. It needs its own analysis,
    including related-key and related-IV attacks.
- **The rest of the programme still applies.** Even with all of these changes:
  - the full validation programme (security.md §8–§15) still has to be carried out;
  - FIPS 140-3 approval stays impossible for a custom generator. A deployment that needs
    approval can only use Option B, an approved DRBG (security.md §21).

## 5. Future feature requirements (conditional; binding since constitution 1.2.0)

These apply **only if the owner decides to pursue a cryptographic claim, evaluation or
certification**. They are not scheduled, and they are not requirements of any current feature.
Since constitution 1.2.0 they are binding: no cryptographic claim, evaluation or certification
may be made or pursued for any model until they are met. The constitution's Security Policy
holds the governing wording and prevails if the two differ.

| ID | Requirement |
|----|-------------|
| FUT-SEC-1 | **Key entropy.** The generator MUST accept a key with at least 128 bits of entropy, and no claimed strength may be below 128 bits. No seed or key search, and no trade-off attack, may cost less than the claimed strength. |
| FUT-SEC-2 | **Reachable secret state.** At least twice the claimed strength, in bits, reachable through key and IV loading (time–memory–data trade-off). |
| FUT-SEC-3 | **Stream separation.** If more than one stream per key is allowed, a nonce or IV with defined uniqueness rules. |
| FUT-SEC-4 | **Reseeding.** If prediction resistance is claimed, a reseed input fed from a validated entropy source (SP 800-90B). |
| FUT-SEC-5 | **Initialization analysis.** Key and IV loading and the warm-up MUST be analysed for related-key, related-IV and weak-key behaviour before any claim. |
| FUT-SEC-6 | **Output limit.** The maximum output per key, and per key and IV, MUST be specified and covered by the analysis. |
| FUT-SEC-7 | **Re-validation.** A new model ID, golden vectors, a design freeze, and the complete statistical programme on unused held-out sets. Results from features 002 and 003 do not carry over. |
| FUT-SEC-8 | **Demonstration first.** Before a redesigned key interface is implemented, reproduce this bound on a reduced seed domain, for example with two seed words fixed (2³² candidates): recover the seed from three words and measure the cost per candidate (security.md §12.3, item 1). |
| FUT-SEC-9 | **Certification route.** State which scheme is targeted, for example independent academic cryptanalysis plus an AIS 20/31-style evaluation. FIPS 140-3 approval is not available to a custom generator; FIPS deployments need an approved DRBG (Option B). No model may be described as FIPS 140-3 approved or as an SP 800-90A DRBG. |

### 5.1 Grid scaling in the key-interface redesign

Design 1.0 is a fixed 4-node ring, the 2×2 grid, which does not meet the constitution's
requirement that grid size be parameterizable from 2×2 to 16×16 (Principle III; feature-002 open
issue O1). The key-interface redesign changes the core anyway, so it should resolve O1 at the
same time. These are design requirements of that redesign. They come from Principle III, which
already binds all RTL, not from the Security Policy, so they are not part of FUT-SEC-1 to
FUT-SEC-9.

| ID | Requirement |
|----|-------------|
| FUT-GRID-1 | **Parameterized size.** Grid size MUST be a parameter covering at least 2×2 to 16×16 without restructuring the core: interior nodes with up to four channels, neighbour-only data flow, a local food source and a registered output tree (Principle III). The supported sizes MUST be listed. |
| FUT-GRID-2 | **Key fills the state at every size.** Key and IV loading MUST be defined for every supported size. Each size's specification MUST state its key entropy, its secret state reachable from the key, and the resulting security bound (Security Policy). FUT-SEC-1 and FUT-SEC-2 MUST hold at every supported size, including the smallest. |
| FUT-GRID-3 | **Mixing across the grid.** Information moves one hop per step, so the warm-up length MUST be derived from the grid diameter and justified by measurement: after warm-up, every state bit depends on every key and IV bit. Output taps MUST NOT depend only on a local neighbourhood. |
| FUT-GRID-4 | **Per-node constants by rule.** Rotation amounts, disruption patterns and food-source placement MUST be generated by a stated rule for every size, not hand-picked, and the rule MUST avoid translational and rotational symmetry between nodes (security.md §9.2, S7: the rotation-structured constants of design 1.0). The disruption behaviour MUST be re-established at each size (as feature-002 FR-005 did for design 1.0). |
| FUT-GRID-5 | **Validation per size, smallest first.** Each supported size MUST be identified by model ID and grid size, with golden vectors and its own statistical evaluation (FUT-SEC-7). Validate an intermediate size, for example 4×4, before 16×16. |

### 5.2 Hardware target: Digilent Arty A7-100T

Security and performance must be testable on hardware the owner has: a Digilent Arty A7-100T.
The board figures below were checked on 2026-10-31 against the Digilent *Arty A7 Reference
Manual* (web page printed to PDF by the owner, 20 pages): the feature list, the variant table,
§3 (power monitoring), §5–§8.

- FPGA: AMD (Xilinx) Artix-7 XC7A100TCSG324-1, speed grade −1. 15,850 slices, each with four
  6-input LUTs and 8 flip-flops: 63,400 LUTs and 126,800 flip-flops. 4,860 Kb
  (607.5 KB) of block RAM (135 blocks of 36 Kb, derived), 6 clock management tiles (PLL and
  MMCM each), XADC. The manual's variant table labels the 15,850 figure "Look-up Tables"; its
  feature list shows that this is the slice count.
- Board: 100 MHz crystal oscillator (pin E3), 256 MB DDR3L (16-bit bus, 333 MHz), 16 MB
  Quad-SPI flash, 10/100 Mb/s Ethernet (TI DP83848J PHY, MII), FTDI FT2232HQ USB-UART and
  USB-JTAG, 4 Pmod connectors.
- Power monitoring on the board (manual §3): a 10 mΩ sense resistor and INA199A1 amplifier on
  the FPGA core supply VCCINT (500 mV/A, 0–2 A, XADC auxiliary channel 10), and voltage and
  current sensing on the 5 V supply (XADC channels 1 and 9). The XADC samples at most
  1 MSPS, so this measures average power, not per-cycle side-channel traces.

The design uses LUTs, flip-flops and block RAM only, with 0 DSP blocks, as the constitution
requires (Principle III, Technical Constraints). DSP blocks were considered on 2026-10-31 and
rejected by the owner: the add-rotate-XOR step has no multiplication, its critical path is a
serial feedback loop that DSP pipeline registers would lengthen, the 240 DSP slices cover only
a small fraction of a large grid's additions, and their fixed columns break the neighbour-only
layout.

| ID | Requirement |
|----|-------------|
| FUT-HW-1 | **Generic VHDL.** The RTL MUST be behavioural and vendor-neutral (Principle III): no instantiated vendor primitives, with grid size and word width as generics. The build MUST use 0 DSP blocks. It MUST simulate in GHDL and match the Python model bit for bit (Principle II). |
| FUT-HW-2 | **Efficient on the Arty A7-100T.** The spec MUST give, for the XC7A100T-1: the largest supported grid that fits, LUT/FF/BRAM use (0 DSP) and timing at that size and at 4×4, from Vivado post-route reports. Target ≥ 200 MHz, from the 100 MHz oscillator through an MMCM (Principle III). The step MUST be designed for this from the start (see §5.3, carry chains). |
| FUT-HW-3 | **Performance measured on the board.** On-chip counters MUST measure words per second at the achieved clock, per supported grid size, and the result MUST be compared with the C stream (8.5 × 10⁷ words/s for design 1.0). Power MUST be measured with the board's VCCINT current sensor through the XADC, alongside the Vivado estimate. |
| FUT-HW-4 | **Equivalence and statistics from hardware output.** The board MUST show bit-exact equivalence with the golden vectors, either checked on chip against vectors in block RAM or by exporting the stream. Stream export for statistical tests uses Ethernet (100 Mbit/s, about 12 MB/s) or UART: 2³² bytes per seed take about 6 minutes, but PractRand's 2⁴⁰ bytes take about 25 hours. The spec MUST state which battery levels run on captured hardware data and which on the bit-exact C stream. |
| FUT-HW-5 | **Hardware security tests within reach.** The spec MUST list the security tests this board and the owner's equipment can support: constant-time behaviour (no data-dependent cycle count), a key interface that cannot be read back, key zeroization on reset, and fault behaviour on reset and clock glitches. The board's VCCINT current sensor gives average power only, enough for a coarse check that power does not vary with key or data, but not for per-cycle side-channel traces. Power or EM side-channel analysis needs external measurement equipment; the spec MUST say whether it is available, and if not, record side channels as untested. |

### 5.3 Redesign inputs checklist

Open issues and research items from features 001–003 and the security review that the next
redesign must address. Tick an item only when the redesign's spec, plan or evidence covers it,
and cite where. Sources: feature-002 final report (O1–O6), feature-003 phase reports,
security.md §9.2 (S1–S14) and §12.3, and the two repository reviews of 2026-10-31 (groups E
and F).

**A. Fix in the design**

- [ ] Key of at least 128 bits; no strength claimed below 128 (FUT-SEC-1; S1, S3).
- [ ] Secret state reachable from the key at least twice the claimed strength, probably with key
  material in D as well as P (FUT-SEC-2; S1).
- [ ] Public parts of the state (phase counters, food sequence) excluded from the secret-state
  count (FUT-SEC-2; S2).
- [ ] Nonce or IV for stream separation, and a reseed input if prediction resistance is claimed
  (FUT-SEC-3, FUT-SEC-4; S4).
- [ ] Key loading that creates no related states, e.g. no shared seed halves between nodes or
  rotation-equivalent keys (FUT-SEC-5; S8).
- [ ] Specified output limit per key and per key and IV (FUT-SEC-6).
- [ ] Parameterized grid, 2×2 to 16×16, with key loading at every size (FUT-GRID-1, FUT-GRID-2;
  O1).
- [ ] Warm-up derived from the grid diameter and measured full diffusion (FUT-GRID-3).
- [ ] Per-node constants generated by a rule with no translational or rotational symmetry
  (FUT-GRID-4; S7).
- [ ] Step designed for the 200 MHz target: pipelined or shorter than the ~7 serial 32-bit carry
  chains of design 1.0 (O1; feature-002 plan.md Complexity Tracking).
- [ ] Local food source and registered output tree, no grid-wide signals (O1; Principle III).
- [ ] Invertibility of the step decided by design, with its consequence for backtracking
  resistance stated. phyco-v2's step is not one-to-one (S9, S13).
- [ ] Generic, vendor-neutral VHDL with grid size and word width as generics; builds with 0 DSP
  blocks (FUT-HW-1; Principle III).
- [ ] Fits and meets timing on the Arty A7-100T (XC7A100T-1): largest grid, resource use and
  Fmax from Vivado post-route reports (FUT-HW-2).

**B. Analyse before or during the design**

- [ ] Seed bound reproduced on a reduced seed domain, before implementation (FUT-SEC-8;
  security.md §12.3 item 1).
- [ ] Guess-and-determine and SAT/SMT state recovery on 8- and 16-bit variants (§12.3 item 2;
  S6).
- [ ] Slow-variable leakage: whether conductance classes are visible in the output; hide or speed
  up those control bits if so (§12.3 item 3; S6, S12).
- [ ] Related-seed and rotational experiments; results feed the key-loading and constant rules
  (§12.3 item 4; S7, S8).
- [ ] Functional graph and cycle structure on reduced variants, including how far states
  merge (§12.3 item 5; S9, S10, S13).
- [ ] Linear, differential and machine-learning distinguishers on reduced-step variants
  (§12.3 item 6).
- [ ] Initialization analysis of key and IV loading and warm-up: related-key, related-IV, weak
  keys (FUT-SEC-5).

**C. Answer explicitly in the spec**

- [ ] Where the mixing comes from: the slime-mould dynamics or the added ARX terms (S11). This
  sets the cryptanalysis target.
- [ ] Rule for which operations count as "no hash, cipher or standard PRNG" (feature-002 O2,
  FR-007), including key and nonce loading, and whether a plain counter counts as a standard
  PRNG.
- [ ] Throughput goal and measured result (design 1.0: 8.5 × 10⁷ words/s against 10⁸;
  feature-003 dev report, open issue 4).
- [ ] Certification route named; no FIPS 140-3 or SP 800-90A wording (FUT-SEC-9).
- [ ] Which battery levels run on captured hardware output and which on the bit-exact C stream
  (FUT-HW-4).
- [ ] Hardware security tests possible with the owner's equipment, and side channels recorded as
  untested if no measurement equipment is available (FUT-HW-5).

**D. Carry into the protocol and tooling**

- [ ] Every variant logged; dev seeds for tuning, held-out sets only after the freeze (O6;
  FUT-SEC-7).
- [ ] Positive-control false-failure rate calibrated before the acceptance rules are frozen
  (feature-002 O3; feature-003 calibration, about 21%).
- [ ] Stream byte counts record bytes consumed, not only bytes written (feature-003 dev report,
  open issue 1).
- [ ] Single-writer progress logs (feature-003 dev report, open issue 2).
- [ ] Feature files committed before the freeze, so `git_head` is meaningful (feature-003 dev
  report, open issue 3).
- [ ] Every role timed in the rehearsal, including the negative control, before projecting run
  time (feature-003 attempt 1).
- [ ] Approval status kept outside frozen files (feature-002 O5).
- [ ] Vectors and statistical evaluation per supported size, 4×4 before 16×16 (FUT-GRID-5,
  FUT-SEC-7).
- [ ] On-board throughput counters and bit-exact equivalence with the golden vectors on the Arty
  A7-100T, with power from the board's sensor (FUT-HW-3, FUT-HW-4).

**E. From the repository review of 2026-10-31**

- [ ] Every conductance class reachable, or the class logic cut to the classes in use: today
  classes 2 and 3 are in effect unused, because a larger D gets a smaller flux (S12). State which
  direction the shift table is meant to have. Measure the range and occupancy of every state
  variable on development seeds: class occupancy, D range, disruption rate and how long each
  control bit stays fixed.
- [ ] Carried-over feature-002 requirements re-decided in the new spec, not inherited silently:
  FR-002 (widths of at most 32 bits; a long counter would exceed it), FR-003 (the public `lut-v1`
  food table and phase increments, period 128; S2), FR-005 (disruption on 1–50% of steps: keep
  it, and measured on which keys?) and FR-009 (the 64-bit seed domain, replaced by FUT-SEC-1).
  FR-007 is in group C.
- [ ] A written rationale for every constant (ROT, SHIFT, X1 and X3, and THRESH, which was set
  from measured D quantiles on development seeds) and for the warm-up length; extends FUT-GRID-3
  and FUT-GRID-4.
- [ ] Conserved sum in the transport stage: the fluxes cancel around the ring, so
  Σ T[k] = Σ P{k}* (mod 2³²) before the vein-tone XOR and rotation. Analyse it as a structural
  relation for cryptanalysis, or remove it by design.
- [ ] A guaranteed minimum period, for example by widening the phase counters into a long
  counter, if the FR-007 rule allows it (S9, S10).
- [ ] One canonical output serialization (word width, byte order, bit order) for every tool and
  the hardware export. Today the SP 800-22 harness reads big-endian words, most significant bit
  first, while the C stream writes little-endian words for PractRand and TestU01, plus a
  bit-reversed copy for TestU01's second orientation.
- [ ] Inter-stream tests: interleave the outputs of related keys or nonces into one stream and
  run PractRand on it (FUT-SEC-3, FUT-SEC-5).
- [ ] Reduced-width versions (8- and 16-bit words) defined by the spec from the same word-width
  generic in the model and RTL, including how shift and rotation amounts scale, so that results
  on them transfer (FUT-HW-1; security.md §12.3 items 2 and 5).
- [ ] Full-speed capture on the board into the 256 MB DDR3L, in bursts: one 32-bit word per clock
  at 200 MHz is 800 MB/s, against about 12 MB/s over Ethernet. The DDR3L peak is about 1.3 GB/s
  (16 bits at 333 MHz, double data rate); whether sustained writes keep up is unverified
  (FUT-HW-4).
- [ ] Test-time budget: feature-003 attempt 1 streams about 38.5 TiB for each full role and
  28.4 TiB for the negative control, about 105 TiB in all; the positive control took 7.3 h and
  the negative 20.1 h on 32 threads. Decide before the freeze which grid sizes get the full
  batteries and which a reduced set (FUT-GRID-5).
- [ ] Dieharder: the constitution names it among the broader batteries (Principle IV), and
  feature 003 left it out of scope. Include it, or record why not.
- [ ] RTL key-loading interface and reset sequence: serial or parallel key loading, warm-up
  latency, an output-valid signal, and zeroization of key and state (FUT-HW-5).
- [ ] State-dependent selections written without branches (masks rather than conditionals) in
  the C stream and the Python model, with the compiled C checked; the C stream now uses
  conditional expressions that a compiler may turn into branches (security.md §13).
- [ ] Principle I's default width ("16-bit signed state, 32-bit output words unless a ratified
  spec says otherwise") predates the 32-bit state of `phyco-v2`, which its ratified spec allows.
  Update it by constitution amendment (a PATCH, as a clarification), and state every width in
  the new spec (FR-002).
- [ ] TestU01's licence allows non-commercial research use only (security.md §6); a commercial
  route would need another battery or a licence.

**F. From the second repository review of 2026-10-31**

- [ ] Backtracking: decide between a permutation update with an explicit one-way output, or a
  many-to-one step whose merging is analysed. Today two local mechanisms merge states (S13); say
  which is intended and what it gives.
- [ ] Transport invertible, or its zero modes analysed, at every grid size: the class-1 transport
  is a diffusion step with a zero mode on the ring, and even-sided grids keep zero modes (S13;
  FUT-SEC-2, FUT-GRID-1).
- [ ] Mixing that does not rely on the top bits of D: they are strongly biased (bit 31 never set,
  bit 30 set 90.6% of the time), so the vein-tone XOR barely changes the top five bits of T[k]
  (S14). Measure the bit frequencies of every state variable on development seeds.
- [ ] Output rotations chosen so that the two halves of the output do not align: ROT[1] = 11 and
  ROT[3] + 16 ≡ 11 (mod 32), so outside disruptions the second half is a sum of two words both
  rotated by 11, and both of S12's untouched bits land on output bit 10. Nodes 0 and 2 are offset
  by only 2. State the rule for every grid size (FUT-GRID-4).
- [ ] Slide resistance: the food phases repeat every 128 steps, so a keyed design that loads key
  material into D could allow slid pairs. phyco-v2 avoids this only because D never returns to
  its reset values. A non-repeating counter removes the issue (S2, S10).
- [ ] Warm-up margin justified: a one-bit seed change reaches its plateau in the state after
  about 4 steps and in the output after 2, against a warm-up of 256 (about 64×). Derive the new
  warm-up from measured diffusion with a stated margin (FUT-GRID-3; S14).
- [ ] Held-out seed sets that cannot be computed before the freeze: today each is SHA-256 of a
  public string such as "phycoweb-003/heldout-1/i". Use a committed salt revealed after the
  freeze, or a public randomness-beacon value fixed by date (FUT-SEC-7).
- [ ] A reproducible positive control: today it is `getrandom`, so its runs cannot be repeated.
  Add a deterministic control, for example ChaCha20 or AES-CTR with a published key, and keep
  the OS source as a second control if wanted.
- [ ] Graded negative controls that show detection power: `lut-v1` fails so grossly that it
  shows only that the harness runs. Add known-weak generators of increasing quality, for example
  MT19937, which fails LinearComp in Crush and BigCrush.
- [ ] SP 800-22 decision rule set to a target false-failure rate: a perfect candidate passes an
  attempt with probability about 0.629, because of the positive control's 20.7% false failures,
  the CUSUM and RE/REV correlations and the DFT excess. Any change must keep the rule stricter
  for the candidate (protocol rules may only become stricter).
- [ ] PractRand length: every run stops at 2⁴⁰ bytes. Include at least one longer run per grid
  size, or record why not.
- [ ] Line endings fixed for every hashed file, extended to VHDL, XDC and Tcl. `.gitattributes`
  now pins every file with a recorded hash (checked on 2026-10-31); new tools should write
  explicit LF and, where possible, hash line-ending-normalized content, as
  `sp80022.source_sha256()` does.
- [ ] Pinned dependencies: `requirements.txt` still names "Aetheris-PRNG", claims Python 3.8 to
  3.11+ compatibility, marks scipy optional although `sp80022/special.py` imports it, lists the
  replaced `nistrng`, and pins nothing.
- [ ] Full-length hardware equivalence: equivalence covers the first 10⁶ words, while a BigCrush
  run reads about 3.6 × 10¹¹. Add an on-board CRC-32 fixture checked against the model at 2³²
  and 2⁴⁰ words; streaming 2⁴⁰ bytes over Ethernet takes about 25 h (FUT-HW-3, FUT-HW-4).
- [ ] Reference-model speed: the Python model gives about 2 × 10⁵ words/s on 2×2 (measured under
  load) and would give about 3 × 10³ at 16×16, so the equivalence practice would take about 9 h
  per size. Plan a faster checked model or a shorter practice (FUT-GRID-5).
- [ ] Invariants as tests (S12's D bound, S13's merging, conserved sums), and each feedback
  direction stated and tested, so that a common-mode error in the model and the C stream is
  caught (security.md §10.2; property-based tests with Hypothesis are not yet done).
- [ ] Archive `phyco-v2` in `baseline/` when it is superseded (Principle V); `baseline/` holds
  only `float-v0`.
- [ ] Record storage: `reports/003-extended-batteries-calibration` is 194 MB in 2,268 files.
  Decide what is committed, what is compressed and what is kept outside git, before the next
  attempt.
- [ ] Output bits per step stated for every grid size (FUT-GRID-1).
- [ ] Documentation drift corrected: README §1.2 gives Poiseuille flow (Q = D·ΔP/L), which holds
  for `lut-v1` and is the opposite of `phyco-v2`; §2 presents `lut-v1` as the reference model;
  the diagram feeds nodes 00 and 01, while `phyco-v2` feeds nodes 0 and 2. The feature-002 phase
  report (§7) calls the step "invertible-looking ARX", which S13 contradicts; correct it by an
  addendum.

**G. Pending input**

- [ ] Feature-003 battery attempt 1 (PractRand, TestU01) verdict and any failing tests, after the
  owner's result review. Results are a reference only and do not carry over (FUT-SEC-7).

## 6. Suggested feature description, for `/speckit-specify` when the owner decides

```text
Cryptographic key interface for PhycoWeb-PRNG: replace the 64-bit seed with a key of at least
128 bits, plus a nonce for stream separation and, if claimed, a reseed input, so that seed
search no longer caps security at 64 bits. Make the grid size a parameter (2×2 to 16×16),
with key loading that fills the state at every size, so that feature-002 open issue O1 is
resolved in the same redesign. First demonstrate the current 64-bit bound on a reduced seed
domain. Treat the change as a core redesign (new model id), re-run the statistical programme on
unused held-out sets for each supported size, starting with an intermediate size such as 4×4,
build generic VHDL that runs efficiently on the owner's Arty A7-100T with 0 DSP
blocks, and make no security claim before independent review. Requirements
FUT-SEC-1 to FUT-SEC-9 (constitution Security Policy 1.2.0), FUT-GRID-1 to FUT-GRID-5,
FUT-HW-1 to FUT-HW-5 and the §5.3 checklist, in research/security/seed-entropy-bound.md.
```

## 7. Where this finding is recorded

- `.specify/memory/constitution.md` 1.2.0: Security Policy (the binding wording of §5).
- `security.md` 2.6: §1.2, §4, §5, §6, §9.2 (S1–S5), §12.2, §20 and §20.1, §21, §22, §24.
- `README.md`: §1.1 status and §5.
- `reports/002-core-dynamics-redesign/phase-report.md`: addendum dated 2026-10-31.
- `specs/003-extended-batteries-calibration/tasks.md`: T041, T042 and T043 (the feature-003
  claims check, README update and final report).

## 8. Reproducing the numbers

- **The bound** follows from `design.md` §3–§5.
- **The throughput** comes from `reports/003-extended-batteries-calibration/dev/timing.json`.
  It was measured in WSL on an idle machine on 2026-10-29 with:
  `phyco_stream phyco-v2 56053 7029 30841 11050 --words 1000000000 > /dev/null`.
- **The arithmetic:** 2⁶⁴ × 259 / 85,375,305 s⁻¹ = 5.60 × 10¹³ s ≈ 1.77 × 10⁶ years.
