# phyco-v3: design document

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

Version: 0.4

## Security target

Every figure of this chapter is a target, not a claim. The parameter table and the output limits
restate `security-target/parameters.json` and `limits.json`, which `scripts/mode_limits_v3.py`
writes from this document's tables once the variant table holds every R (tasks T107), and a test
compares them value by value. Until then R stands as `<R4>`, `<R8>` and `<R16>`.

### Properties sought

Each property is a bound on an adversary's advantage, in the definitions of security.md §3, relative
to Π as an ideal permutation and limited to attacks below the target strength, as in a flat sponge
claim (strategy note §2.1). An adversary has N evaluations of Π or Π⁻¹, with every data block it
observes counted as at least one evaluation, and its data is also bounded by the output limits.

- **Keystream security.** For nonces never repeated under a key, the output is within ε of uniform
  bits at the limits, ε being the target advantage 2⁻⁶⁴ at N = 2¹²⁸ (research R9). Status: the
  theorem named in the chapter "Mode", section "Theorems", read and unverified until its review.
- **Multi-user security.** The same bound holds for u keys, the adversary choosing the key of each
  query: the theorem is multi-user as it stands.
- **Backtracking resistance across each forget call.** A state compromised between calls reveals
  nothing about output delivered before the last forget call, within ε at the limits. A state
  compromised within a request reveals, through Π⁻¹, only that request's earlier blocks back to its
  last forget call, at most the per-request cap of 2¹⁹ bits. Instantiate ends with a forget call, so
  no such walk reaches the key. Status: the result named in the same section, read and unverified
  until its review, one precondition of it resting on a remark of the paper, which that section marks.

Prediction resistance is not sought (D7; FUT-SEC-4): this feature has no validated entropy source.

The one assumption every bound rests on is that Π has no structural distinguisher below 2¹²⁸
evaluations. That assumption is what the cryptanalysis attacks. A claim built on it could state only
that no attack on the real permutation below the target strength is known, never that Π is ideal.

### Target parameters

| Parameter | Target at every claimable size | Rule |
|-----------|--------------------------------|------|
| Target strength s | 128 bits | FR-005, FUT-SEC-1 |
| Key | 256 bits | FR-006, D2 |
| Nonce | 128 bits, used at most once per key | FR-006, FUT-SEC-3 |
| Capacity c | 384 bits | FR-015, R9: the forget result's term in N² needs it |
| Rate r | b − c | FR-015 |
| Target advantage ε | 2⁻⁶⁴ at N = 2¹²⁸ | R9 |

A keyed variant's key has k = min(c, 256) bits and its nonce k/2 (R14). So a keyed reduced variant
takes a c-bit key and a c/2-bit nonce, and its row states its bound on that variant only, at status
`research` and "no claim", with its checks made at s = c/2, which is the level of those checks and
no field of the row (FR-006).

### Parameter table

| Variant | n | w | b | c | r | R | Key entropy | Reachable secret state | Bound | Status |
|---------|---|---|---|---|---|---|-------------|------------------------|-------|--------|
| phyco-v3/n4-w32-R<R4>-c384 | 4 | 32 | 1024 | 384 | 640 | <R4> | 256 | 384 | 128 | claimable |
| phyco-v3/n8-w32-R<R8>-c384 | 8 | 32 | 4096 | 384 | 3712 | <R8> | 256 | 384 | 128 | claimable |
| phyco-v3/n16-w32-R<R16>-c384 | 16 | 32 | 16384 | 384 | 16000 | <R16> | 256 | 384 | 128 | claimable |
| phyco-v3/n2-w16-R8-c64 | 2 | 16 | 128 | 64 | 64 | 8 | 64 | 64 | 32 | research |

The Bound column is the size profile's `bound_bits`, the least of the figures of "Generic bounds"
below, a target at a claimable size and "research variant, no claim" at a research one, where it is
never compared with s = 128. The reachable secret state is the capacity part, counted from the
layout and recorded "by specification", not measured, at every call boundary: after instantiate,
after each generate with its forget call and after each reseed. The variant table (tasks T095) adds
every other supported variant, a supported 3×3's keyed variant and the keyless variants, listed as
permutation-only with a key entropy of 0 and no bound.

### Output limits

| Limit | Size | Calls of Π | Bits |
|-------|------|------------|------|
| per instantiation | 4×4 | 2^22 | 2,684,354,560 |
| per instantiation | 8×8 | 2^22 | 15,569,256,448 |
| per instantiation | 16×16 | 2^22 | 67,108,864,000 |
| per key | 4×4 | 2^42 | 2,814,749,767,106,560 |
| per key | 8×8 | 2^42 | 16,325,548,649,218,048 |
| per key | 16×16 | 2^42 | 70,368,744,177,664,000 |
| per request | 4×4 | 821 | 524,288 |
| per request | 8×8 | 143 | 524,288 |
| per request | 16×16 | 34 | 524,288 |

The bounds also cover u = 2²⁰ keys, 2²⁰ instantiations per key and 2²¹ reseeds per instantiation.
Calls of Π are the theorem's unit and the primary one; the bits are the calls times r, an upper
figure, since calls also go to instantiate and to forget. The per-request cap is the value SP 800-90A
uses for its largest request. The derivation stands in the chapter "Mode", section "Limits".

### Caller's obligations

The interface cannot check these, and the bound holds only where they hold.

- **The key** has full entropy, is uniform and secret, and comes from an established cryptographic
  generator of keys, never from a PhycoWeb-PRNG model. Its entropy exceeds the target strength, as
  SP 800-90A asks of entropy input. A key with less entropy caps the strength at that entropy.
- **The nonce** is used at most once per key, in one of the two ways of "Limits": a counter per key,
  never repeated or wrapped, kept across objects and devices, or uniform 128-bit values.
- **The per-key limits and u** are usage rules across objects, processes and devices, and across
  resets of a device, since one object enforces them only within itself and a reset restarts the
  counters of a device.

### Threats

| Threat | Decision | Reason or restatement |
|--------|----------|-----------------------|
| T1 Known output | Adopted | Restated for `phyco-v3`: the attacker sees any output blocks and knows the position of every block it observes |
| T2 Related seeds | Adopted | As related keys and related nonces: the theorem takes independent keys, and research R4's first-order differences observe the loading; attacks beyond first order are deferred to feature 005 (FR-049) |
| T3 State compromise | Adopted | Across forget, by the property above; a later output is not protected after a compromise, this feature having no validated entropy source (D7) |
| T4 Implementation access | Adopted in part | Timing, by fixed operations with no secret-dependent branch, index or amount (FR-020). Power, electromagnetic and fault-injection attacks and the behaviour on reset and clock glitches are deferred to feature 008, with the risk below |
| T5 Seed influence | Excluded | The key is an input of stated entropy (Caller's obligations); a key with less caps the strength, and no property is sought for it |
| T6 Chosen nonces | Adopted | The adversary chooses each nonce and personalization string, the nonce unique per key |
| T7 Nonce misuse | Stated, no goal | The behaviour is stated in the chapter "Mode", section "Nonce reuse"; the bound covers a repeated nonce only through the collision term of uniform nonces, and no goal of T7 is claimed for a nonce repeated by error or by force |
| T8 Many users | Adopted | Within u, by the theorem's terms; see "Generic bounds" |
| T9 Chosen absorbed input | Adopted | Personalization strings and reseed inputs are chosen by the adversary in the theorem's absorption |
| T10 Compromise around forget and reseed | Adopted | The state just after a forget or reseed call reveals no output before the last forget call; a later output is not protected |
| T11 Quantum | Adopted in part | Single-target key search only, k/2 ≥ s, met with equality and no margin. Multi-target quantum key search, quantum attacks on the capacity through queries to the public Π and every other quantum generic attack are excluded, the target being a classical one, and stay open for feature 005 |

**The risk of T4.** A state read by a probe, or changed by a fault, in mid-request exposes that
request back to its last forget call. Any of the self-test's selectors, at the key chain's input, at
the nonce chain's input or at the absorption interface, held on its constants by a design error or a
fault, alone or with the others, would run every instantiate on the self-test's key, a public
development input, in place of the host's, on nonce 0, or on the self-test's input words in place of
the host's at the absorption interface, with no sign at the ports. Feature 008's tests cover it by
matching the output, block by block, with the model's after a passed self-test, a key load and an
instantiate with the host's key, nonce and personalization string, each other than the self-test's,
and after a reseed with an input other than the self-test's and a second request, so that each
selector held alone, as well as all of them, gives an output that differs from the model's.

### Assets

The key; the capacity part at every moment; the whole state within a request, whose earlier blocks
Π⁻¹ recovers back to the last forget call; every output block delivered to the caller; the integrity
of the limit counters; and the caller's record of nonces used.

### Generic bounds

Each row of security.md §12.2 is a check of the size profile that can fail, computed by code, which
exits 1 on any violation at a claimable size. The keyed reduced variant is checked at s = c/2.

| Bound | Rule | Claimable sizes, target s = 128 | `n2-w16-R8-c64`, at s = c/2 |
|-------|------|---------------------------------|-----------------------------|
| Key size | k ≥ s | 256 ≥ 128 | 64 ≥ 32 |
| Reachable secret state | at least 2s at every call boundary | 384 ≥ 256 | 64 ≥ 64 |
| Output volume | every limit at most what the theorems allow at ε, by R9's doubling check | held at the limits | no claim, limits stated at claimable sizes only |
| Multi-target search | k − log₂ u ≥ s | 236 ≥ 128 | 44 ≥ 32 |
| Key and nonce | k + nonce bits ≥ 2s | 384 ≥ 256 | 96 ≥ 64 |
| Capacity | c ≥ 2s | 384 ≥ 256 | 64 ≥ 64 |
| Quantum search, single target | k/2 ≥ s | 128 ≥ 128, met with equality and no margin | 32 ≥ 32 |
| Nonce reuse | behaviour stated, with its test | chapter "Mode", section "Nonce reuse" | the same |

The bound of a row is the least of k, half the reachable secret state at the boundary where it is
least, k − log₂ u at the stated u, half of k and the nonce bits together, c/2 and k/2, a term below
zero counting as zero. At a claimable size that is k/2. A keyless variant takes `none`.

### Claimable sizes and the 2×2 decision

The claimable sizes are 4×4, 8×8 and 16×16, at w = 32 and c = 384 with the frozen R (D3; R9). 2×2 and,
where this document specifies its three-colour schedule, 3×3 are reduced research variants outside
every claim. This resolves the FUT-SEC-2 and FUT-GRID-2 conflict at 2×2 and weakens neither, as
security.md §20.1 records: FUT-SEC-1 and FUT-SEC-2 bound a claimed strength, no claim covers a
research size, each research row states its key entropy, its bound and the status `research`, and the
production interface refuses every research variant (FR-033).

### Certification route

The route is independent academic cryptanalysis plus an AIS 20/31-style evaluation (D8; FUT-SEC-9).
Functionality class: class unconfirmed, until the AIS 20/31 version 3.0 proposal is read and the
class is confirmed or changed here at the security-target review. `phyco-v3` conforms to no standard.
A value taken from a standard is cited as that standard's value.

### Claim template

Target, not a claim. No claim exists: the register holds `phyco-v3` at L0, with "no claim".

```text
Model:        phyco-v3, this document's version, n x n for n = 4, 8 and 16, rounds R; SHA-256 of the design
Property:     keystream security, multi-user security and backtracking resistance across forget
Attacker:     T1 to T11 as this chapter adopts them; a nonce at most once per key
Limits:       this chapter's output limits, per key and nonce and per key; u keys
Strength:     target 128 bits, from the theorems of the chapter "Mode" and their bound at the limits,
              assuming no attack on the permutation below 2^128 (security.md section 12.6)
Assumptions:  the key is uniform and secret, with 256 bits of entropy; no entropy source for reseeds
Not claimed:  everything else, any standard's approval and any side-channel resistance that was not
              measured
Evidence:     none yet
```

## Mode

The generator is a keyed duplex over Π with the calls instantiate, generate, forget and an optional
reseed (D1; FR-013). All of this chapter is the same for every candidate.

### Calls

The state s is one bit string of b bits: the lanes in order of their numbers ("Layout"), and in each
lane bit 0 first. Its outer part is its first r bits and its inner part its last c bits. Every call of
Π is one call of the full-state keyed duplex KD of Algorithm 1 of the keystream theorem's paper, the
same permutation throughout, in that paper's order: Π first, then the outer part read as Z, then σ
added. A σ of 0 adds nothing.

```text
instantiate(nonce, pers), with p the blocks of pers (Padding and domain separation):
    s <- key || nonce || 0... || V                                 the initial state (Layout)
    s <- Pi(s)                                                     KD.Init(i, iv, 0, false)
    forget
    for j = 1 to p:  s <- Pi(s);  s <- s xor block j               KD.Duplexing(block j, false)
    s <- Pi(s)                                                     KD.Duplexing(0, false)
    s <- Pi(s)                                                     KD.Duplexing(0, false)
    forget

generate(n), with m = ceil(n / r):
    for j = 1 to m:  s <- Pi(s);  Z[j] <- outer(s)                 KD.Duplexing(0, false)
    the first n bits of Z[1] || ... || Z[m] are the output
    forget

forget:
    s <- Pi(s);  outer(s) <- 0                                     KD.Duplexing(0, true)

reseed(input), with p the blocks of input:
    for j = 1 to p:  s <- Pi(s);  s <- s xor block j               KD.Duplexing(block j, false)
    s <- Pi(s)                                                     KD.Duplexing(0, false)
```

Z is released only in generate; in every other call the paper's interface returns it and this mode
withholds it, which gives an adversary less than the theorem's. A reseed input is taken as chosen by
the attacker (T9; FR-016), given before the call that absorbs it, and a reseed never resets a counter.

**In the forget result's terms.** A block added and then a call of Π is that paper's `refresh`, and a
call of Π with the outer part read, then a forget, is its `next` at t = 1. So a reseed is a `refresh`
of a zero block and then its blocks, and it ends with one more call of Π because `refresh` runs Π
after its last input and `next` runs Π again before it reads. Instantiate is a `next` from the key's
state, a `refresh` of the personalization string and a `next` whose output is withheld.

| Call on the interface | Calls of Π | Flagged calls |
|-----------------------|------------|---------------|
| instantiate | p + 5 | 2 |
| generate of n bits | ⌈n/r⌉ + 1 | 1 |
| reseed | p + 1 | 0 |

**Constant streams (FR-023).** The four call types draw on one constant stream, t = 1 in FR-023's
count of call types, as R15 fixes. Both results have one permutation in both directions, and distinct
streams would make four, which is neither's form, and R10 adopts no mode without a matching theorem.
So the start tree carries no call-type field, and each food node's ROM holds R entries.

### Layout

A node (i, j) holds two lanes, numbered ℓ = 2(n·i + j) + e, with e = 0 for pressure and e = 1 for
vein, so that the state's lanes run through the nodes row by row. The rate lanes are the first r/w
lanes and the capacity lanes the last c/w. A keyed variant's key has k = min(c, 256) bits. The key
fills the first k/w lanes and the nonce the next k/(2w). Every other lane is 0 in the initial state,
but for the last 32 bits of the state, which hold the variant word V, and at w = 16 that word fills
the last two lanes.

This is the theorem's form and not a free choice: Algorithm 1 sets the state to K‖iv with the outer
part its first r bits, and the paper's proof reads the key in the first k bits and iv in the last
b − k. So at every keyed variant the key sits in rate lanes, and at 2×2 at w = 16, where it fills the
rate, the nonce sits in capacity lanes, reached by the nonce chain of FR-025. The capacity lanes hold
public values until the first call of Π; every boundary that FR-009 counts comes after it.

| Size | w | c | Rate lanes | Capacity lanes | Key lanes | Nonce lanes |
|------|---|---|------------|----------------|-----------|-------------|
| 4×4 | 32 | 384 | 0-19 | 20-31 | 0-7 | 8-11 |
| 8×8 | 32 | 384 | 0-115 | 116-127 | 0-7 | 8-11 |
| 16×16 | 32 | 384 | 0-499 | 500-511 | 0-7 | 8-11 |
| 2×2 | 16 | 64 | 0-3 | 4-7 | 0-3 | 4,5 |

**The variant word.** V = n + 2⁸·w + 2¹⁶·(c/8) + 2²⁴·R, a 32-bit word, so a keyed variant has R below
256. It separates the variants one key might serve; its reason is that and nothing more, and no
bound reads it. A variant with no room for the key, the nonce and V is keyless (R14).

**No call writes the capacity lanes after the first call of Π, and none outputs them.** Absorption
and output use the rate lanes only. So the reachable secret state is c bits at every call boundary.

### Key loading

**In the model** the key is given once, when the object is constructed, and held until zeroization:
each instantiate takes the nonce and the personalization string and loads the stored key into the
state, so no key is ever compared with another. **In hardware** the key is loaded once, along a
registered shift chain through the nodes that hold key bits, into a key register at each of them,
and zeroized with the state, and at every instantiate the host gives the nonce on the absorption
interface. Once the personalization string's length word is taken and found within its maximum, a
selector at every lane sets the lane in one cycle from one of four sources: a key register, the nonce
chain, the nonce register of a rate lane that holds nonce bits, or its stated constant, never as an
XOR. So the initial state is exactly the one "Layout" states.

The keys of u users are drawn independently and uniformly, so that the keystream theorem's H_min and
H_coll are both k; two keys that happen to be equal cost its last term. The same draw gives the key's
state its min-entropy k, independently of Π, which is what the forget result's Lemma 10 asks of it.
This is FUT-SEC-5's part that is met by specification. Its part by evidence, the diffusion below and
research R4's first-order related-key and related-nonce differences, is cited at the security-target
review once those records exist.

### Padding and domain separation

**The domain words** are two constants of the mode, one for each kind of block that holds an input.

| Kind of block | Domain word |
|---------------|-------------|
| a block of a personalization string | 1 |
| a block of a reseed input | 2 |

Rule and reason: the two smallest positive integers, since any two distinct values separate the
inputs and nothing else asks of them. Zero is left out so that a block is never all zero. Generate
and forget absorb nothing: `next`, in the form the forget result covers, has no input between its
calls of Π, and its forget writes zeros. So their σ is 0, and the theorem's flag tells a forget call
from a generate call.

**An input's blocks.** A block is r bits, the last 32 of which are the domain word, so that a block
holds r/32 − 1 data words. An input x of ℓ bytes is encoded as one 32-bit word holding ℓ, then x, then
zero bytes up to a whole word. That encoding is cut into blocks in order, and zero words fill the last
block. An empty input is one block, holding its length word, so every instantiate has one. In each
block the inner part is zero. A personalization string and a reseed input each hold at most 4,096
bytes, so that the longest takes 1,025 words.

**Injectivity (FR-014), the proof.** A sequence of calls is encoded by what each call of Π adds, a block
or nothing, and whether it is flagged, the key and nonce standing in the initial state at fixed
positions. A decoder reads it from the start. An instantiate is two calls, then its blocks, then three
calls. The first data word of a run of blocks gives ℓ, which fixes the number of words and of blocks of
that input, so that the encoding is prefix-free and the decoder never has to guess where an input ends.
Then ℓ bytes are read back and the padding bytes are dropped. After the instantiate, a block starts a
reseed, whose input ends as above and which adds one plain call, and a plain call starts a generate,
whose run of plain calls ends at the flagged call and gives its count of blocks. Domain word 1 and 2
tell the inputs apart, and the flag ends a request, so two sequences that differ in a call type, in ℓ
or in a byte of an input give different encodings. So the map is injective. The domain words and the
flag carry the separation, and the constant streams carry none, there being one.

**The committed check.** `absorbed_blocks`, `decoded_input`, `call_blocks` and `decoded_calls` in
`scripts/mode_limits_v3.py`, with `PaddingInjective` in `tests/test_records_004.py`, cover every input
length from 0 to the maximum and every call type at each keyed rate, with 0 collisions required, and
show that distinct development inputs give distinct block sequences.

**Absorption over the rate is a special case of the theorem's.** The theorem's σ has b bits. A block
here is such a σ with its inner part zero, and that is all this mode ever gives it.

**No seed.** The forget result's construction adds a seed to its inputs. Its seed serves extraction from
weak sources, which this mode does not seek. Lemma 12's proof reads only that the inner part
is secret, and this mode takes every input as chosen by the adversary, so that its inputs stand for
the paper's inputs with the seed already added.

### Forget

Forget follows every generate request and ends every instantiate, in one form: a call of Π, then the
outer part set to zero. It is `KD.Duplexing(0, true)`, the keystream theorem's query with flag true,
so each forget counts once in that theorem's Ω and no other call does, and it is the step
`S_i[1...r] ← 0^r` of the forget result's `next`, at t = 1. The overwritten Z is never released. It is
also the construction of section 4.3 of Bertoni et al., CHES 2010: output fed straight back, so that
the outer part is set to a known value and the step cannot be undone. A keyed variant has r ≥ c, so
one forget call leaves at least c bits to guess going backwards; a variant with r < c would take ⌈c/r⌉
of them, its t in the forget result.

After a forget the state is zeros in the outer part and a secret inner part, the state Lemma 12 starts
from and ends at, which is why the second forget of instantiate stands where it does, and the first
takes the key's state there.

**Several blocks in one request.** The forget result's `next` is stated for one block. A request here
gives several before its forget, as FR-007 states. The paper says that it is not hard to allow
several, that its bounds "would only be marginally affected", and that it would point out the changes
(page 15), and no such passage follows. So this precondition rests on that remark and on no worked
statement, as the owner chose on 2026-11-05 and as the security-target review reads it. The strict form
would be a forget after every block, at half the rate.

In the model forget runs inside every `generate`, after the last output block, so it can never be
skipped. In hardware the output buffer and the registers of both trees are cleared with or before it,
so the rest of a partial last block is discarded by clearing and not left in place.

### Theorems

**Keystream and multi-user security.** Daemen, Mennink and Van Assche, "Full-State Keyed Duplex With
Built-In Multi-User Support", ASIACRYPT 2017, Theorem 1, pages 619–620, `Daemen.pdf`, its `fetched`
entry in `downloads.json`. For f an ideal permutation, an ideal oracle RO behind IXIF, a key array drawn
from D_K, and an adversary with N primitive queries and M construction queries, q initialization
tuples, iv multiplicity q_iv, Ω queries with flag true and L repeated paths, with N + M ≤ 0.1·2^c, the
advantage in telling KD from IXIF is at most

```text
(L + W) N / 2^c  +  2 v (N + 1) / 2^c  +  C(L + W + 1, 2) / 2^c  +  (M - q - L) q / (2^b - q)
  +  M (M - L - 1) / 2^b  +  (M - q - L) q / 2^(H_min + min(c, b - k))
  +  q_iv N / 2^H_min  +  C(u, 2) / 2^H_coll
```

with W for Ω and v for the multicollision limit of Definition 2 at 2(M − L) balls in 2^r bins. A new
path gets uniform output from IXIF, so at L = 0 the theorem gives keystream security for u keys.

| Precondition of Theorem 1 | The feature that meets it | Section |
|---------------------------|---------------------------|---------|
| One ideal permutation f of b bits, in both directions | Π in every call, one constant stream; the assumption FR-004 names | Calls |
| r < b and k ≤ b | every keyed variant | Layout |
| The first call applies f to K‖iv, the key in the state's first k bits | the initial state | Layout |
| Every later call is f, then the outer part returned, then σ added | each call of "Calls" | Calls |
| N + M ≤ 0.1·2^c at the limits | computed by the script | Limits |
| Keys drawn independently and uniformly, so H_min and H_coll are k | a caller's obligation | Key loading |
| No path repeats, L = 0: a nonce is used once per key | the nonce rule, with the collision term for uniform nonces | Nonce reuse |
| Each forget is one query with flag true, and no other call is | forget's one form | Forget |
| Inputs absorbed over the rate are σ with its inner part zero | the blocks | Padding and domain separation |
| A reseed input is σ chosen by the adversary before that call's Z | reseed | Calls |
| Output is the outer part of the state after a full call of f | generate | Serialization |

**Backtracking resistance.** Gaži and Tessaro, EUROCRYPT 2016, ePrint 2016/169, `169.pdf`, its `fetched`
entry in `downloads.json`: Lemma 12, page 25, preserving security, with Lemma 10, page 22, and the sum
of Theorem 4, page 14. Theorem 1 does not cover this property: its adversary never sees the state.
In Lemma 12 the state starts as zeros in the outer part and a uniform inner part, the adversary chooses
the inputs, and the new state and the output together are told from zeros in the outer part, a uniform
inner part and a uniform output with advantage at most, for q queries and d′ blocks,

```text
(2d' + 2)(q + d') / 2^b  +  q / 2^((r - 1) t)  +  (4 (q + t)^2 + q) / 2^c
```

and Lemma 10 gives, from any state S independent of the permutation,

```text
q / 2^H(S)  +  q / 2^((r - 1) t)  +  4 (q + t)^2 / 2^c  +  1 / 2^b
```

Bertoni et al., CHES 2010, `SpongePRNG.pdf`, section 4.3, gives forget's construction and its argument,
and states no theorem for it.

| Precondition of the forget result | The feature that meets it | Section |
|-----------------------------------|---------------------------|---------|
| One ideal permutation of b bits, in both directions | as for Theorem 1 | Calls |
| `next`: f, the outer part read, then t times f and the outer part set to zero | generate with its forget, t = 1 | Forget |
| `refresh`: an input added to the outer part, then f | reseed, and instantiate's string | Calls |
| Before each `next`, zeros in the outer part and a secret inner part | every forget, and Lemma 10 from the key's state | Forget |
| The key's state has min-entropy k, independently of f, for Lemma 10 | the key | Key loading |
| No seed: every input is taken as chosen by the adversary | the inputs | Padding and domain separation |
| Several blocks from one `next`: the paper's remark on page 15, which it does not work out | a request | Forget |
| The sum over the calls of `next` stays within ε at the limits | computed by the script | Limits |
| The sum across instantiations and keys, with a nonce the adversary chooses: this chapter's own hybrid, which the paper does not state | an argument, for the review to read | Limits |

Both entries of `limits.json` stay `unverified`, with no precondition marked met, until the
security-target review (R10).

### Limits

Every limit is derived from the two bounds above at N = 2¹²⁸ and ε = 2⁻⁶⁴, in calls of Π.

| Limit | Size | Value | Bits |
|-------|------|-------|------|
| keys u | all | 2^20 | none |
| instantiations per key | all | 2^20 | none |
| reseeds per instantiation | all | 2^21 | none |
| personalization string, bytes | all | 4,096 | none |
| reseed input, bytes | all | 4,096 | none |
| nonces, first way | all | a counter per key, never repeated or wrapped | none |
| nonces, second way | all | uniform 128-bit values, with the collision term q^2/2^129 | none |
| calls of Π per instantiation | 4×4 | 2^22 | 2,684,354,560 |
| calls of Π per instantiation | 8×8 | 2^22 | 15,569,256,448 |
| calls of Π per instantiation | 16×16 | 2^22 | 67,108,864,000 |
| calls of Π per key | 4×4 | 2^42 | 2,814,749,767,106,560 |
| calls of Π per key | 8×8 | 2^42 | 16,325,548,649,218,048 |
| calls of Π per key | 16×16 | 2^42 | 70,368,744,177,664,000 |
| calls of Π per request | 4×4 | 821 | 524,288 |
| calls of Π per request | 8×8 | 143 | 524,288 |
| calls of Π per request | 16×16 | 34 | 524,288 |
| calls of Π per instantiate | 4×4 | 59 | 37,760 |
| calls of Π per instantiate | 8×8 | 14 | 51,968 |
| calls of Π per instantiate | 16×16 | 8 | 128,000 |

Bits are calls times r. A request of n bits takes ⌈n/r⌉ output calls and one forget call, and an
instantiate p + 5 calls, the last rows at the longest personalization string.

**The worst case at the limits.** With u keys, Q instantiations per key and C calls per instantiation,
M = uQC and q = uQ, and q_iv ≤ u, since a key uses a nonce once. L = 0. A `next` takes at least two
calls, one to read and one to forget, so at most M/2 calls are flagged, Ω = M/2, and there are at
most M/2 calls of `next`.

**Keystream.** The first term of Theorem 1 is uQC·N/2^(c + 1), far below ε at c = 384. The second way
of choosing nonces adds at most uQ²/2¹²⁹, since a collision can only matter under one key. That term
leads, and the bound stays well within ε.

**Backtracking.** Theorem 4 sums Lemma 12 over the calls of `next`, each with q = N + M, and Lemma 10
adds once per instantiation. At N = 2¹²⁸ Lemma 12's quadratic term is 2⁻¹²⁶ at c = 384. So M/2 may
reach 2⁶¹ and no more, which is u·Q·C ≤ 2⁶². This is what sets the limits, and it is why c is 384: at
c = 256 that term is 4, which is no bound, and at c = 320 it is 2⁻⁶², which misses ε (R9).

**What the paper does not state.** Theorem 4 is stated for one generator, and Lemma 10 for a state fixed
before the adversary's queries, while here the adversary chooses each nonce. The sum across
instantiations and keys is this chapter's own hybrid: step by step, each `next` is replaced by the ideal
one, every query of every step counted, and a key stays uniform given what the adversary has seen,
since each earlier step's output has already been replaced. That is an argument and no published
statement, and it stands in the theorems' table as a precondition for the security-target review.

**The choice.** Three limits share that one product, so they trade against one another, and R9 asks
for the choice and its reason. u = 2²⁰, Q = 2²⁰ and C = 2²² give about a million keys, each with about
a million instantiations, each of up to about 335 MB of output at 4×4. Keys and instantiations are
kept equal since neither use dominates, and the nonce term asks log₂ u + 2 log₂ Q ≤ 63, which this
choice meets with room. The per-key limit is their product, 2⁴², so that doubling it is doubling C.

**The bounds at the limits.** At every claimable size log₂ of the keystream bound is −69.000000, the
nonce term leading, and log₂ of the backtracking bound is −64.999999, so that each is within ε = 2⁻⁶⁴.
Doubling u, Q, C or the per-key limit passes ε at every claimable size. The script computes this in
whole numbers and fractions.

**Two rows stand outside the doubling check** (R9), since no term of either bound moves with them: the
per-request cap, which R9 fixes and allows only to fall, and the reseeds, each of which takes calls of
Π, so that the limit on calls holds them. Each is still evaluated in the bounds at its limit.

**Counters.** The object and the core count calls of Π per instantiation, calls per key, instantiations
per key and reseeds per instantiation, FR-007 asking a counter of each, though the limit on calls is
reached first. A call that would pass a limit raises `LimitExceeded`, with no output and no state
change, except at a per-key limit, which also ends the object. A reseed never resets a counter.
Counters wider than 32 bits are held as 32-bit words.

### Nonce reuse

The behaviour is stated, not detected, within one object or across objects, and no goal of T7 is
claimed for a nonce repeated by error or by force. Under one key and nonce, two instantiations agree
until the first call or input word that differs takes effect, and the output blocks given while they
agree repeat. These follow from "Calls", in order of the first difference between instantiations A and B.

| First difference | Blocks that repeat |
|------------------|--------------------|
| None: the same personalization string and the same calls | every block |
| The personalization string | none: no block precedes it, and the difference reaches every lane by the forget call's Π |
| The first request's length, A taking m blocks and B more | A's m blocks, as B's first m; A's forget call is B's block m + 1, whose Z A withholds; nothing after |
| A later request's length | every block before that request, and that request's first m blocks, as above |
| A reseed's input | every block before the reseed; none after |
| The order of calls: one generates where the other reseeds | every block before that call; none after |

**The collision term.** Uniform nonces under one key collide with probability at most q²/2¹²⁹ for q
instantiations, which the bound counts, and which is the only way it covers a repeated nonce.

### Diffusion through instantiation

Between key loading and the first output there are p + 6 calls of Π, at least 7: instantiate's p + 5
and generate's first, each of R rounds, so at least 7R rounds. FUT-GRID-3 asks that every state bit
depends on every key and nonce bit before the first output. The dependency propagation through
instantiate as a whole shows that, and its record, with the margin of 7R over R_f, is cited here at the
security-target review, once the selected candidate has one (FR-029).

### Serialization

The state's bit order fixes every serialization. A byte is 8 consecutive bits, bit 0 of the byte first,
so that lane words are little-endian, and a 32-bit word is 4 consecutive bytes. The key and the nonce
are byte strings placed from the state's first bit (key) and from bit k (nonce). Output is the first n
bits of Z[1]‖…‖Z[m], n a positive multiple of 32, as `n/8` bytes; a request whose length is no multiple
of r keeps the first bits of its last block in that order and discards the rest. Every digest of
output is taken over these bytes, never over a text rendering of them. Output comes only from the
outer part, after a full call of Π.

### Interface formats

Each interface (command, key loading, absorption, output) uses valid and ready, with 32-bit transfers
on the first three. The command interface takes one word per call, with the command in bits 0 to 3.

| Command | Field | Other bits |
|---------|-------|------------|
| key load | 1 | zero |
| instantiate | 2 | zero |
| generate | 3 | bits 4 to 31: the length in 32-bit words, not zero |
| reseed | 4 | zero |
| zeroize | 5 | any |

A word whose field names no command, or a key load, instantiate, reseed or generate word with a bit set
outside its fields, is refused before anything changes, while a word whose field names zeroize
zeroizes in every state that accepts one, whatever its other bits hold. An instantiate's input on the
absorption interface is the nonce's words, then the personalization string's length word, then the
string's words, if any; a reseed's is its length word, then its words. The length word gives bytes, a
length over the maximum is refused before the lanes, the key or a counter changes, and the unused bytes
of a last partial word must be zero. A reseed input's length is public even when its content is secret. The key and the nonce are whole 32-bit words in the order of
"Serialization". Output leaves through a buffer of one block, read out to the interface width i in
⌈r/i⌉ transfers, and the next call starts only after the consumer has taken the block, so that a stall
holds only the buffer and no cycle count depends on secret data.

### Call sequence

| State | From | Calls accepted | Leaves on |
|-------|------|----------------|-----------|
| `not-reset` | configuration | none | reset |
| `resetting` | reset released | none; only here do the self-test's selectors take its constants | the self-test's end |
| `failed` | a failed self-test | none | reset |
| `no-key` | a passed self-test, or a zeroization | key load | the command word |
| `loading` | a key load's command word | the key's words, zeroize | the key held |
| `key-held` | the key held | instantiate, zeroize | the command word |
| `instantiating` | an instantiate's command word | its input's words, zeroize | instantiate done |
| `instantiated` | instantiate or reseed done, or a request's end | instantiate, generate, reseed, zeroize | the command word |
| `generating` | a generate's command word | zeroize | its forget call's end |
| `reseeding` | a reseed's command word | its input's words, zeroize | its end |
| `zeroizing` | a zeroize or a zeroizing refusal | none | `no-key` |

A refused instantiate leaves the state it would have replaced and the core in `key-held` or
`instantiated`. From any call's command word to its end the command interface accepts zeroize only, save
in `zeroizing`, which accepts none, and every other word is refused with its code and changes
nothing. The model's calls follow the same table where it has the state: `generate` or `reseed`
before `instantiate`, and any call after `zeroize`, raise `CallSequenceError`.

| Code | Refusal | Zeroizes |
|------|---------|----------|
| 1 | a length over its maximum | no |
| 2 | a call out of sequence | no |
| 3 | a malformed command word | no |
| 4 | a limit other than a per-key one | no |
| 5 | a per-key limit | yes |
| 6 | a last partial word with a nonzero unused byte, an error path | yes |

Zero means no error. A code stays valid from the refusal until the next command word is accepted or
a reset, and a zeroizing refusal's zeroization keeps it readable.

### Zeroization

One list, cleared for every trigger and from every state: the lanes, every pipeline register, the
registers of the absorption, output and start trees, the key chain's and nonce chain's registers, the
rate lanes' nonce registers, the held key and its copies and the one-block output buffer, and every
counter returns to zero. Its triggers are reset, an explicit zeroize, a failed self-test, an error path
and a call refused at a per-key limit, the call that would pass the limit, nothing happening when a
counter merely reaches it. Every trigger drives the reset's registered fan-out tree. Output-valid stays
low throughout, and after a reset or zeroization until an instantiate requested by the host completes
after a passed self-test. In the model, zeroization overwrites the object's copy of the key in place
and drops the state; that is a discipline over what the object keeps, not a statement about what
Python's memory may still hold, and the caller's own copy of the key is outside it.

## Permutation

Not drafted yet.

## Hardware structure

Not drafted yet.

## Replaced mechanisms

Not drafted yet.

## Slime-mould mapping

Not drafted yet.
