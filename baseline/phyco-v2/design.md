# Design: `phyco-v2` Core Dynamics

**Version**: 1.0 (2026-10-28) | **Status**: awaiting owner design review (T035)
**Feature**: [spec.md](./spec.md) | **Research**: [research.md](./research.md) R9, R10
**Source of the design**: exploration variant `research/002/variants/v005.py`
(SHA-256 `7e729d6bceeee6f0926b7f876d1370e1daaa0f42ce9b3c42183fa0bd395a3932`)

> `phyco-v2` is an experimental, bio-inspired deterministic generator. Passing statistical
> tests is not evidence of cryptographic security, and it must not be used to generate secrets.

## 1. Structure

Four nodes form a ring, which is the 2×2 grid. Channel k joins node k to node k+1 (mod 4).
Each node holds a protoplasm pressure P. Each channel holds a vein thickness (conductance) D.
A food source, the lut-v1 perturbation, feeds nodes 0 and 2.

```text
        food A                  food B
          |                       |
       [P0] ==D0==> [P1] ==D1==> [P2] ==D2==> [P3] ==D3==> (back to P0)
             sup0 -> P1                sup2 -> P3
```

## 2. State (FR-002)

All arithmetic is modulo the stated width. "u32" means unsigned 32-bit, wrapping mod 2³².
Where a value is read as signed, it is two's complement.

| Name | Width | Signedness | Wrap rule | Reset value |
|------|-------|------------|-----------|-------------|
| `P[k]`, k = 0…3 | 32 | unsigned; read as two's complement in step 3 | mod 2³² | see §3 |
| `D[k]`, k = 0…3 | 32 | unsigned | mod 2³² | `0x00010000 << k` = 0x00010000, 0x00020000, 0x00040000, 0x00080000 |
| `phase_a` | 8 | unsigned | mod 2⁸ | 0 |
| `phase_b` | 8 | unsigned | mod 2⁸ | 0 |

Total generator state: 4·32 + 4·32 + 8 + 8 = 272 bits.

The counters `disruptions` and `step_count` are instrumentation for FR-005. They are not
generator state and never affect the output.

**Intermediate values (all within one step)**:

| Name | Width | Meaning |
|------|-------|---------|
| `fa`, `fb` | 16 → 32 | lut-v1 entries, which are 16-bit two's complement, sign-extended to 32 bits: if bit 15 is set, OR with 0xFFFF0000 |
| `d[k]` | 32 | `(P[k] − P[k+1]) mod 2³²`, read as two's complement |
| `c[k]` | 2 | conductance class = `D[k] >> 30` (unsigned) |
| `Q[k]` | 32 | flux = arithmetic right shift of `d[k]` by `SHIFT[c[k]]` |
| `A[k]` | 32 | \|Q[k]\| as unsigned. `Q[k]` is never −2³¹ (shift ≥ 1), so `A[k]` ≤ 2³⁰ |

**Comparisons**: `D[k] > THRESH` is an unsigned 32-bit comparison. There are no other comparisons
apart from the sign tests (bit 31, bit 15) in sign extension, arithmetic shift and absolute value.

## 3. Seed → state (FR-009)

The seed is four ints s₀…s₃, each in 0…65535 (Python `int`, not `bool`). Anything else raises
`ValueError`. If more than four values are given, only the first four are used; fewer than four
raise `ValueError`.

1. `P[k] = (s[k] << 16) | s[(k+1) mod 4]` for k = 0…3.
2. `D[k] = 0x00010000 << k`.
3. `phase_a = phase_b = 0`.
4. Run `WARMUP = 256` steps (§4) and discard their output.

The per-channel D reset values differ, so the all-equal seeds do not start in a symmetric
state.

## 4. Per-step update (FR-001, FR-004)

Constants:

| Name | Value |
|------|-------|
| `INC_A`, `INC_B`, `COS_OFFSET`, `PERTURBATION_LUT` | from `phycoweb.lut`, unchanged (FR-003): 4, 6, 64, the lut-v1 table |
| `SHIFT` | (1, 2, 3, 4), indexed by conductance class 0…3 |
| `ROT` | (5, 11, 19, 27), the peristaltic rotation of node 0…3 |
| `THRESH` | 0x4D000000 |
| `X1`, `X3` | 0x5A5A5A5A, 0xA5A5A5A5 (disruption patterns for nodes 1 and 3) |

Let `P`, `D` be the registered values at the start of the step. Every name with ′ is the new
value. Indices are mod 4.

1. **Phase advance.** `phase_a′ = (phase_a + INC_A) mod 256`, and
   `phase_b′ = (phase_b + INC_B) mod 256`.
2. **Food injection (perturbation).**
   `fa = sext16(LUT[phase_a′])` and `fb = sext16(LUT[(phase_b′ + COS_OFFSET) mod 256])`.
   `P0* = (P[0] + fa) mod 2³²`, `P2* = (P[2] + fb) mod 2³²`, `P1* = P[1]`, `P3* = P[3]`.
3. **Flux (pressure-driven, multiplierless).** For k = 0…3:
   `d[k] = (P{k}* − P{k+1}*) mod 2³²`, `c[k] = D[k] >> 30`,
   `Q[k] = asr(d[k], SHIFT[c[k]])`.
   A thick vein (low class) passes a larger share of the pressure difference. Choosing among
   four constant shifts with a 4:1 select is FR-001's "constant shifts + conditional selection".
4. **Vein growth and decay.** For k = 0…3: `A[k] = |Q[k]|`, and
   `D′[k] = (D[k] + (A[k] >> 2) − (D[k] >> 4)) mod 2³²`.
5. **Transport, vein tone and peristalsis.** For k = 0…3:
   `T[k] = (P{k}* − Q[k] + Q[k−1]) mod 2³²` (outflow on channel k, inflow from channel k−1;
   pressure is conserved apart from food), then `P′[k] = rotl32(T[k] XOR D′[k], ROT[k])`.
6. **Frustrated Foraging disruption (registered, neighbour-local supervisors).**
   - `fire1 = D[0] > THRESH` and `fire3 = D[2] > THRESH`, using the **registered**
     start-of-step D.
   - If `fire1`, then `P′[1] = P′[1] XOR X1`. If `fire3`, then `P′[3] = P′[3] XOR X3`.
   - `disruptions` increases by 1 if `fire1 OR fire3`.
7. **Commit.** All primed values become the registered state. `step_count` increases by 1.

`compute_block()` performs one step and then returns the output (§5). One step produces one
32-bit word.

## 5. Output (FR-006)

From the committed state only:

`w = ((P[0] + rotl32(P[2], 16)) mod 2³²) XOR rotl32((P[1] + rotl32(P[3], 16)) mod 2³², 8)`

Every output bit depends on all four nodes. The output is an unsigned 32-bit int, and the
harness serializes it MSB-first (FR-010).

## 6. Operations used (FR-001)

The step uses only these operations:
- add and subtract mod 2³²;
- XOR and OR with constants;
- a constant left shift (seed, reset);
- logical and arithmetic right shifts by constants (1, 2, 3, 4, 30);
- constant rotations;
- unsigned compare against a constant;
- the sign tests for sext16, asr and abs (bit test plus select);
- a 4:1 select among constant shifts;
- a table lookup (the lut-v1 table).

It uses no multiplication (including by constants), division, modulo or power. The "mod 2ⁿ"
above is a mask (AND with 2ⁿ − 1), not a modulo operation. Shift amounts are never data
values; the class only selects among four fixed shifters.

## 7. Principle III checklist (synchronous, localized RTL)

| Item | Answer |
|------|--------|
| All state registered, one register-transfer step per update | **Met.** P, D and the phases are registers, and steps 1–6 form one combinational next-state function of the registered values. The supervisors (step 6) compare registered D values. **Timing risk**: the longest path is food add → subtract → 4:1 shift select → abs → D update (2 adds) → transport (2 adds) → XOR → rotate (wiring) → XOR, about 7 serial 32-bit carry chains. The ≥ 200 MHz target (a SHOULD) may not be met without restructuring. **RTL-pending**: report at synthesis. |
| Data flows only between direct neighbours | **Met for the grid.** Channel k reads only P{k}, P{k+1} and D[k]. Node k reads only channels k−1 and k. Supervisor 0 reads D[0] and acts on node 1; supervisor 2 reads D[2] and acts on node 3. Both are adjacent. |
| How the disruption reaches the nodes | Local, with no global signal. Each supervisor is one comparator next to its vein, driving the XOR enable of the adjacent downstream node. |
| Signals that are not neighbour-to-neighbour | (a) The food source: the phase registers and LUT drive nodes 0 and 2, as in feature 001. That is one shared source with two point-to-point signals, not a grid-wide broadcast. (b) The output tap reads all four nodes. It is an output function, not node-to-node communication, and can be registered without changing the sequence. Both are recorded for the owner's judgment. |
| Grid size parameterizable (2×2 to 16×16) without restructuring | **Not met.** The design is a fixed 4-node ring, which is the 2×2 grid. For larger grids, multi-channel nodes, per-node constants and the output tap are not designed. **RTL-pending exception**, recorded in plan.md Complexity Tracking. |
| Multiplierless, 0 DSP | **Met.** See §6. The automatic check is `test_purity_v2` (T036). |

## 8. FR-007: why this is slime-mold dynamics, not a renamed standard generator

- **Components and their Physarum counterparts**:
  - pressure nodes and pressure-difference flux through conductances (discretized Tero et al.
    flow, with the conductance quantized into 4 classes);
  - vein adaptation (dD/dt = f(|Q|) − γD, with f = |Q|/4 and γ = 1/16);
  - periodic food forcing (the lut-v1 table);
  - a threshold-triggered Frustrated Foraging disruption;
  - rhythmic peristaltic contraction (shuttle streaming), modelled as a per-node constant
    rotation;
  - feedback of vein tone onto the upstream node.
- **The rotation and vein-tone feedback are essential, and the evidence shows it.** Without
  them (variant v001), the dissipative network locks onto the periodic food forcing and fails
  all 15 families, just as lut-v1 does. That is the physically expected attractor. The
  peristaltic term keeps the pressure field from collapsing.
- **Resemblance to standard designs**: the update uses add, rotate and XOR, which are generic
  ARX operations. It is not the structure of any named generator or primitive:
  - it has no xorshift triple (shift-XOR of a word with itself);
  - it has no LCG/MCG multiplier, and no Mersenne-Twister, PCG, ChaCha/Salsa quarter-round or
    hash round;
  - its distinctive parts (data-selected flux shifts, conserved transport, decaying vein
    accumulators, LUT forcing, threshold XOR) come from the model.
  - No constant is taken from a published PRNG or cipher. 0x5A5A/0xA5A5 are the feature-001
    disruption patterns, widened to 32 bits.
- **Not provable automatically.** This is the owner's judgment at this review (data-model §1).

## 9. Dev evidence (FR-015; dev seeds only; not an acceptance result)

All runs used `research/002/explore.py` with harness `sp80022` 1.0.0, and are logged in
`research/002/runs.jsonl` (line numbers below). Held-out seeds were not used. Every
exploration run is listed here, including the failures.

| Line | Variant | Window | Seeds | Families failed | Disruption rate | Note |
|------|---------|--------|-------|-----------------|-----------------|------|
| 1 | v001 | 0 | dev ×100 | all 15 | 99.99–100% | Dissipative baseline; collapses to the periodic attractor |
| 2 | v002 | 0 | dev ×100 | none | 0% | + peristaltic rotation and vein tone; threshold never reached (fails FR-005) |
| 3 | v003 | 0 | dev ×100 | approximate_entropy (96/100, needs 97) | 13.4–13.9% | Threshold 0x4D000000, set from measured D quantiles |
| 4–6 | v003 | 1, 2, 3 | dev ×100 | none | — | Diagnostic windows. Pooled ApEn p < 0.01: 6/400 (chance) |
| 7, 8 | v004 | 0, 1 | dev ×100 | none, none | 13.4–13.9% | Output from the 4 pressure nodes. Not chosen: unregistered, two-hop supervisor (Principle III) |
| 9 | v004 | 0 | feature-001 ×2 | (n = 2) | 13.7% | FR-005 rate only |
| **10** | **v005** | **0** | dev ×100 | **none** | **13.49–13.83%** | **Chosen**: registered, local supervisors |
| **11** | **v005** | **1** | dev ×100 | **none** | — | T033 run 2: the next 2²¹ bits from the same seeds |
| **12** | **v005** | **0** | feature-001 ×2 | (n = 2, by rule) | 13.56–13.58% | FR-005 rate on the feature-001 seeds |

- v005 meets the T033 stop rule: all 15 families pass in 2 independent dev runs, with the design
  unchanged.
- FR-005 holds on all 102 development seeds, measured over 10⁶ steps after warm-up.
- Both all-equal seeds, (0,0,0,0) and (65535,…), give non-constant output with no period
  ≤ 2¹⁵ in the first 2¹⁶ words (`edge_seeds_ok` on every line).
- **Selection caveat**: 5 variants and 12 runs were tried on the dev set. The dev passes are
  therefore optimistic. Only the pre-registered held-out attempt (Phase 5) is evidence for
  acceptance.

## 10. RTL-consumable description (FR-008)

Sections 2–6 are the RTL description: the registers, their reset values, and the next-state
and output functions written with fixed-width operations only. Golden vectors come with
`phycoweb/model_v2.py` (T042). RTL itself is out of scope (RTL-pending).

## 11. What the reference model must match

`phycoweb/model_v2.py` (T041) implements §2–§5 exactly, with `MODEL_ID = "phyco-v2"` and
`WARMUP = 256`. For every seed, its output must equal variant v005's output word for word. The
literal transcription test `test_design_trace` (T038) checks the model against the numbered
steps of §4.
