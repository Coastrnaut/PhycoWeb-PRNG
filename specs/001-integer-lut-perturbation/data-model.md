# Data Model: Integer LUT Perturbation Source

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-10-28

## Generator State (`PhycoWebEngine`, model id `lut-v1`)

| Field | Width / range | Initial value | Notes |
|-------|---------------|---------------|-------|
| `P[0..3]` | integer 0 … 65535 (16-bit pattern) | `seed[0..3] & 0xFFFF` | Node pressures |
| `D[0..3]` | integer 1 … 65535 | 256 | Vein thickness; 0 is replaced by 1 |
| `phase_a` | 0 … 255 | 0 | `food_a` phase counter (FR-007b) |
| `phase_b` | 0 … 255 | 0 | `food_b` phase counter (FR-007b) |
| `step_count` | unbounded, ≥ 0 | 0 | Diagnostic only; not used in any computation |

**Validation**:
- `seed` must contain at least 4 integers; elements beyond 4 are ignored (current behavior).
  Fewer than 4 raises `ValueError`.
- Seed values are masked to 16 bits at construction. The current model stores them unmasked in
  int32 until the first update; no seed in use exceeds 16 bits, so this is a no-op for existing
  vectors. A test covers it.

**State transition (one `compute_block()` call)**: exactly the eight stages of spec FR-007c.
Wrap points are explicit:

| Stage | Operation | Rule |
|-------|-----------|------|
| 2 | `phase ← (phase + inc) & 0xFF` | 8-bit wrap |
| 4 | `P ← (P + food) & 0xFFFF` | 16-bit wrap |
| 5 | `Q ← wrap32(D[i] × (P[i] − P[j])) >> 8` | 32-bit two's-complement wrap, then arithmetic shift (research R1) |
| 6 | `growth ← wrap32(abs(Q)) >> 2`; `D ← (D + growth − (D >> 4)) & 0xFFFF`; `0 → 1` | `wrap32(abs(−2³¹)) = −2³¹`, as in numpy |
| 7 | `D[0] > 4096 or D[2] > 4096` → `P[1] ^= 0x5A5A`, `P[3] ^= 0xA5A5` | unsigned comparison |
| 8 | `out ← (D0&0xFF)<<24 \| (D1&0xFF)<<16 \| (D2&0xFF)<<8 \| (D3&0xFF)` | **unsigned** 0 … 2³²−1 (research R2) |

`wrap32(x) = ((x + 2³¹) mod 2³²) − 2³¹`.

## Perturbation Table

| Attribute | Value |
|-----------|-------|
| Length | 256 |
| Entry | `trunc0(sin(2π·i/256) × 1024) & 0xFFFF` (FR-007a) |
| Encoding | 16-bit two's-complement bit pattern held as 0 … 65535 |
| Increments | `food_a` 4, `food_b` 6, `food_b` read at `+64` offset |
| Combined period | 128 steps |
| Artifacts | Python constants module + RTL hex file ([file-formats](./contracts/file-formats.md)) |

**Validation**: recomputing the formula reproduces every entry; both artifacts are identical;
`T[0]=0x0000`, `T[64]=0x0400`, `T[128]=0x0000`, `T[192]=0xFC00`.

## Archived Variant (manifest entry)

| Field | Description |
|-------|-------------|
| `archive_path` | Path under `baseline/float-v0/` |
| `source` | `readmee.md@<commit>` (extracted listing) or `<path>@<commit>` |
| `sha256` | Hex digest of the archived bytes |
| `note` | How it differs from the reference behavior (research R4) |

**Validation**: every manifest entry exists and its recomputed SHA-256 matches (SC-006).
Archived files are never edited.

## Golden Vector File

| Field | Description |
|-------|-------------|
| `model` | `float-v0` (archived `readmee.md` model) or `lut-v1` |
| `seed` | four integers |
| `count` | number of words, ≥ 10,000 |
| words | one unsigned 32-bit word per line, 8-digit uppercase hex |

**Relationships**: `lut-v1` vectors are checked against the current model on every test run
(SC-002); `float-v0` vectors are the baseline for comparison (FR-014).

## Statistical Results Record

| Field | Description |
|-------|-------------|
| `model`, `seed`, `n_bits`, `bit_order` | Sample definition (`bit_order = "msb-first"`) |
| `git_head`, `git_dirty` | Provenance |
| `versions` | Python, numpy, nistrng |
| `command` | Exact command line run |
| `tests[]` | `{name, status: pass\|fail\|not_eligible, p_value \| null, elapsed_ms}` |
| `limitations[]` | Includes the single-sequence limitation and that a pass is not evidence of cryptographic security |

**Validation**: every test in `SP800_22R1A_BATTERY` appears exactly once in `tests[]`.
