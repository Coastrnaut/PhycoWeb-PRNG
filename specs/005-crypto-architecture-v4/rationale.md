# phyco-v4: design rationale

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v4` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

Version: 0.5

## Security target

This chapter explains the design document's chapter "Security target", which states the properties
sought, the threats, the parameters and the claim template. It states no value of the size profile
or of the limits: each is cited (design document, chapter "Security target"). Each statement carries
one of feature 004's FR-062's seven labels.

**Fact.** The properties sought, the assets and the decision on each threat stand in the design
document (design document, chapter "Security target", section "Properties sought"; section
"Threats"; section "Assets"). No claim exists, and the claim template is a target.

**Argument.** Every bound is stated relative to Π as an ideal permutation because a mode's theorem
can say nothing else: it moves the whole question onto one object. So one assumption, that Π has no
structural distinguisher below the target strength, is what every later analysis attacks, and a
break of Π is a break of that one assumption, not of a chain of them (strategy note §4.2).

**Argument.** The target strength is stated flat, for attacks below it, because the mode's generic
bounds are better at some data and time and worse at others. A flat figure is the one a reader can
hold a design to, and each generic bound of security.md §12.2 is then a check that can fail at a
claimable size (design document, chapter "Security target", section "Generic bounds").

**Argument.** The key has twice the target strength for two reasons that happen to meet. The
multi-target term leaves room for many keys, and single-target quantum key search meets the target
with equality and no margin, which is what sets the bound of a claimable row (design document,
chapter "Security target", section "Generic bounds").

**Argument.** The capacity is above twice the target strength, which the birthday bound on a duplex
would ask. The published result for forget has a term quadratic in the adversary's queries, so that
at twice the target strength it says nothing at the target's own query count. Feature 004's research
R9 says that the capacity rises when no limit reaches the target advantage, and it rose to the least
multiple of 64 that reaches it (design document, chapter "Mode", section "Limits"). This costs rate,
most at the smallest claimable size, and buys a guarantee that rests on a published result and not
on a hope.

**Argument.** The target advantage is far smaller than the one an IV-collision rule would ask for,
because at the limits an attack at the target strength should gain almost nothing, and its time over
advantage then stays well above the target strength. Its value is feature 004's research R9's
(design document, chapter "Security target", section "Target parameters").

**Argument.** T5 is excluded and T7 is stated with no goal for one reason: each is a failure of what
the interface cannot check, the key's entropy and the nonce's uniqueness, and the design document
lists both among the caller's obligations rather than implying a protection that does not exist. A
partial nonce check would make the model differ from the hardware, which keeps no nonce history.

**Residual risk.** Multi-target quantum key search, quantum attacks on the capacity through queries
to the public Π and every other quantum generic attack are excluded from this target and stay open
for feature 006, since the target is a classical one.

**Residual risk.** A state read by a probe, or changed by a fault, in mid-request, and any of the
self-test's selectors held on its constants, stay with feature 009, with the risk the design
document states (design document, chapter "Security target", section "Threats").

**Untested.** No attack on `phyco-v4` has been tried: no candidate of this feature exists yet.
Nothing in this chapter rests on a measurement.

### Changes from Version 0.4

Every entry is a fact: a change made to this chapter of the design document or of this document,
with its reason. The chapters start from feature 004's Version 0.4 of both documents, as feature
005's FR-010 names them by SHA-256, and no figure of the target changed: the key, the nonce, the
capacity, the target strength and every limit stand as Version 0.4 had them (design document,
chapter "Security target", section "Target parameters"; section "Output limits").

- **The model ID.** `phyco-v4` stands where `phyco-v3` stood, in the header, the parameter table's
  variant IDs, the threats, the certification route and the claim template of the design document,
  and in this chapter. Reason: feature 005's D3 gives its design round a model ID of its own, so
  that no record of one feature reads as the other's.
- **Citations of feature 004.** Each requirement, decision and research item of feature 004 that the
  chapters cite is named as feature 004's, in both documents. Reason: the same numbers name other
  rules in feature 005's documents, and feature 005's FR-010 asks for the name.
- **The later features' numbers.** The deferrals of T2 and T11 go to feature 006, and T4's and its
  risk's to feature 009, in the design document's section "Threats" and in this chapter's two
  statements of residual risk. Reason: security.md §22 renumbered the later stages when feature 005
  took its place, and feature 005's FR-010 names these four places.
- **When the two files are written.** The chapter's opening states that the security target's files
  are written from its parameter table before the security-target review, with the round counts as
  placeholders, and written again in the commit that writes them (design document, chapter "Security
  target", section "Parameter table"). Version 0.4 wrote them once the variant table held every
  round count. Reason: feature 005's FR-011 holds the review before the first candidate, so the
  files it names must exist then.
- **The variant table's place.** The sentence under the parameter table names the chapter
  "Permutation" where Version 0.4 named a task of feature 004. Reason: the task number is not this
  feature's.
- **The functionality class.** The section "Certification route" leaves the class to the owner
  design review, as an open item, where Version 0.4 read "here at the security-target review".
  Reason: feature 004 was to close it at a review held after its selection, with the selected
  design's records; this feature's first review comes before any candidate, so the item moves with
  the others that need one (feature 005's FR-012).
- **A section "Open items".** New in the design document, before "Claim template": the round counts
  with every figure computed from them, the margin of instantiation's diffusion, the first-order
  related-key and related-nonce differences, and the functionality class (design document, chapter
  "Security target", section "Open items"). Reason: feature 005's FR-012 asks that every item that
  depends on a selected design be listed in the chapter as open and checked at the owner design
  review.
- **The claim template's first line.** It names no level: the register holds the model with no claim
  at the level its rows record (design document, chapter "Security target", section "Claim
  template"). Version 0.4 named the lowest level. Reason: the level changes when "L1 recorded" reads
  Approved (feature 005's FR-013), and a reviewed chapter should not then state another.
- **The statements on what is untested.** Each says that no candidate of this feature exists yet.
  Reason: feature 004's candidates exist, and none of them is this feature's.
- **This section.** New in both chapters of this document. Reason: feature 005's FR-010 places the
  list of changes here, so that the design document's header and chapters keep their fixed form.

## Mode

This chapter explains the design document's chapter "Mode". It states the theorem the mode rests on
and how each precondition is met by citing them (design document, chapter "Mode", section
"Theorems"), and it states no value of the limits (design document, chapter "Mode", section
"Limits").

**Fact.** Keystream and multi-user security rest on Theorem 1 of Daemen, Mennink and Van Assche,
ASIACRYPT 2017, read in `Daemen.pdf` and listed in `limits.json`. Its entry stays `unverified` until
the security-target review, as feature 004's R10 states.

**Fact.** Backtracking resistance across forget rests on Lemma 12 of Gaži and Tessaro, EUROCRYPT
2016, read in `169.pdf`, with its Lemma 10 and the sum of its Theorem 4, and listed in
`limits.json`. Its entry stays `unverified` until the security-target review. Bertoni et al., CHES
2010, section 4.3, gives the construction and an argument, and no theorem for it.

**Hypothesis.** Several blocks from one `next` affect that bound only marginally. The paper says so
(page 15), and it does not work the change out. Every other precondition of the result is met by the
form of a call; this one rests on the remark (design document, chapter "Mode", section "Forget").

**Argument.** The sum across instantiations and keys, with a nonce the adversary chooses, is the
design document's own hybrid over the calls of `next`, since the paper states its result for one
generator and a state fixed in advance (design document, chapter "Mode", section "Limits").

**Argument.** A keyed duplex was chosen over a stream-cipher construction because every property
then reduces to one assumption, and because a permutation already has Π⁻¹ for its own tests, so that
a forget call is one more call of the same object (strategy note §4.2).

**Argument.** The initial state is K‖iv in that order, with the key in the state's first bits,
because that is the form Theorem 1 takes: Algorithm 1 sets the state so, and the proof reads the key
in the first k bits, which is where its term in min(c, b − k) comes from. Placing the key in the
capacity lanes would look more natural and would not be this theorem. So the key sits in rate lanes
before the first call of Π, which is safe only because no output comes before that call (design
document, chapter "Mode", section "Layout"). The paper's form is taken as feature 004's R10 asks.

**Argument.** Forget is a query with flag true because the theorem counts exactly those, in its Ω.
Algorithm 1's flag overwrites the outer part, and the forget result's `next` zeroes it, so that one
call with an input of zero serves both papers. Each call of `next` has a price in the forget
result's sum, and that price, not the amount of output, is what sets the limits.

**Argument.** The limits are in calls of Π and assume the worst split, half of all calls flagged,
because a caller may make short requests, and a limit that held only for long ones would hold for no
caller who did not. The cost is that a caller of long requests stays well inside the bounds.

**Argument.** Instantiate holds two forget calls, and a reseed one more call of Π than it has
blocks, because the forget result covers exactly these forms: `next` from the key's state, `refresh`
for an input, and `next` again, which runs Π once more before it reads. Generate and forget add
nothing to the state for the same reason, so that the flag, and no domain word, tells them apart.
The mode takes the paper's form, as feature 004's R10 asks, at the cost of more calls per
instantiate.

**Argument.** The three limits share one product, so the choice between them is a trade and no
result. Keys and instantiations are kept equal since neither use dominates, as the design document
states (design document, chapter "Mode", section "Limits").

**Argument.** The call types share one constant stream because both results have one permutation.
Distinct streams would give four, a form neither covers, though strategy note §10 raised them as an
idea. The domain words and the flag carry the separation, and feature 004's FR-014's proof says so
(design document, chapter "Mode", section "Padding and domain separation").

**Argument.** The mode has no seed though the forget result's construction has one, because that
seed serves extraction from weak sources, which this feature does not seek, and Lemma 12's proof
reads only the inner part's secrecy (design document, chapter "Mode", section "Padding and domain
separation").

**Argument.** An input carries its length first because the hardware knows the length before it
pads, feature 004's FR-025 refuses an over-long input before anything changes, and a length prefix
makes the encoding prefix-free with no padding bit to reason about. A block's last word is the
domain word because it then stands at one place at every size.

**Argument.** A reseed holds no forget call because feature 004's FR-013 asks for none, and because
the forget that ended the last request already stops a backward walk: a reseed input is public in
this design (feature 004's FR-016), so that a state compromised after it reveals nothing before that
forget.

**Residual risk.** A result in this chapter bounds the mode with Π ideal, and Π is not ideal. Every
bound here says what a generic attack can do, and nothing about an attack that uses Π's structure.

**Residual risk.** Nonce misuse is stated and not prevented: under a repeated nonce, the blocks the
design document names repeat (design document, chapter "Mode", section "Nonce reuse").

**Untested.** The padding's injectivity has a proof and a committed check; the mode's calls have run
on no permutation of this feature, since no candidate and no model of it exist yet.

### Changes from Version 0.4

Every entry is a fact: a change made to this chapter of the design document or of this document,
with its reason. No call, layout, padding rule, theorem, limit or format of the mode changed (design
document, chapter "Mode", section "Calls"; section "Limits").

- **Citations of feature 004.** Each requirement, decision and research item of feature 004 that the
  chapters cite is named as feature 004's, in both documents. Reason: as in the chapter "Security
  target".
- **The evidence part of key loading.** The section "Key loading" names the diffusion and the
  first-order related-key and related-nonce differences as an open item of the chapter "Security
  target", checked at the owner design review, where Version 0.4 cited them at the security-target
  review (design document, chapter "Mode", section "Key loading"). Reason: the records exist only
  once a candidate is selected (feature 005's FR-012).
- **The margin of instantiation's diffusion.** The section "Diffusion through instantiation" names
  the dependency record and its margin as an open item in the same way (design document, chapter
  "Mode", section "Diffusion through instantiation"). Reason: the same.
- **Whose choice the remark's reading was.** The section "Forget" says that the owner's choice of
  2026-11-05 was made for feature 004. Reason: the date precedes this feature, and its
  security-target review reads the precondition again.
- **Where the papers' downloads stand.** The section "Theorems" names feature 004's downloads
  manifest for both papers. Reason: this feature plans no download and reads feature 004's `fetched`
  entries as feature 005's FR-001 states.
- **The statement on what is untested.** It says that no candidate and no model of this feature
  exist yet. Reason: as in the chapter "Security target".
- **This section.** New. Reason: as in the chapter "Security target".

## Components

Not drafted yet.

## Nonlinearity

Not drafted yet.

## Diffusion

Not drafted yet.

## Constants

Not drafted yet.

## Margin

Not drafted yet.

## Attack classes

Not drafted yet.

## Network questions

Not drafted yet.

## Alternatives

Not drafted yet.
