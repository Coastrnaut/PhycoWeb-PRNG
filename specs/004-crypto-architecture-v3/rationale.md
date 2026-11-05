# phyco-v3: design rationale

> This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be used
> to generate secrets; use an established cryptographic random-number generator for keys,
> nonces, tokens and salts. Passing statistical tests does not show cryptographic security.

Version: 0.1

## Security target

This chapter explains the design document's chapter "Security target", which states the properties
sought, the threats, the parameters and the claim template. It states no value of the size profile
or of the limits: each is cited (design document, chapter "Security target"). Each statement carries
one of FR-062's seven labels.

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
with equality and no margin. The capacity has twice the target strength because of the birthday
bound on a duplex, so that the capacity sets the bound of a claimable row, with half the key and half
the reachable state beside it (design document, chapter "Security target", section "Generic bounds").

**Argument.** The target advantage is far smaller than the one an IV-collision rule would ask for,
because at the limits an attack at the target strength should gain almost nothing, and its time
over advantage then stays well above the target strength. Its value is research R9's (design document,
chapter "Security target", section "Target parameters").

**Argument.** T5 is excluded and T7 is stated with no goal for one reason: each is a failure of what
the interface cannot check, the key's entropy and the nonce's uniqueness, and the design document
lists both among the caller's obligations rather than implying a protection that does not exist. A
partial nonce check would make the model differ from the hardware, which keeps no nonce history.

**Residual risk.** Multi-target quantum key search, quantum attacks on the capacity through queries
to the public Π and every other quantum generic attack are excluded from this target and stay open
for feature 005, since the target is a classical one.

**Residual risk.** A state read by a probe, or changed by a fault, in mid-request, and any of the
self-test's selectors held on its constants, stay with feature 008, with the risk the design document
states (design document, chapter "Security target", section "Threats").

**Untested.** No attack on `phyco-v3` has been tried: no candidate exists yet. Nothing in this chapter
rests on a measurement.

## Mode

This chapter explains the design document's chapter "Mode". It states the theorem the mode rests on
and how each precondition is met by citing them (design document, chapter "Mode", section
"Theorems"), and it states no value of the limits (design document, chapter "Mode", section
"Limits").

**Fact.** Keystream and multi-user security rest on Theorem 1 of Daemen, Mennink and Van Assche,
ASIACRYPT 2017, read in `Daemen.pdf` and listed in `limits.json`. Its entry stays `unverified` until
the security-target review, as R10 states.

**Hypothesis.** Backtracking resistance across forget rests on a theorem not yet read. Bertoni et al.,
CHES 2010, section 4.3, gives the construction and an argument, and no theorem for it. Gaži and
Tessaro, EUROCRYPT 2016, may give one, and `169.pdf` has not been fetched. Until then the design
document marks this `unverified`, and the form of forget may change to the paper's (R10).

**Argument.** A keyed duplex was chosen over a stream-cipher construction because every property then
reduces to one assumption, and because a permutation already has Π⁻¹ for its own tests, so that a
forget call is one more call of the same object (strategy note §4.2).

**Argument.** The initial state is K‖iv in that order, with the key in the state's first bits, because
that is the form Theorem 1 takes: Algorithm 1 sets the state so, and the proof reads the key in the
first k bits, which is where its term in min(c, b − k) comes from. Placing the key in the capacity
lanes would look more natural and would not be this theorem. So the key sits in rate lanes before the
first call of Π, which is safe only because no output comes before that call (design document,
chapter "Mode", section "Layout"). The paper's form is taken as R10 asks.

**Argument.** Forget is a query with flag true because the theorem counts exactly those, in its Ω.
Algorithm 1's flag overwrites the outer part, which is what section 4.3 of Bertoni et al. asks of a
forget, so the one call serves both papers. Each forget has a price in the bound, and that price, not
the amount of output, is what sets the limits: the theorem's first term grows with the flagged calls,
while output calls alone cost far less.

**Argument.** The limits are in calls of Π and assume the worst split, half of all calls flagged,
because a caller may make short requests, and a limit that held only for long ones would hold for no
caller who did not. The cost is that a caller of long requests stays well inside the bound.

**Argument.** The three limits share one product, so the choice between them is a trade and no result.
Keys and instantiations are kept equal since neither use dominates, as the design document states
(design document, chapter "Mode", section "Limits").

**Argument.** The call types share one constant stream because the theorem has one permutation.
Distinct streams would give four, a form it does not cover, though strategy note §10 raised them as an
idea. The domain words carry the separation, and FR-014's proof says so (design document, chapter
"Mode", section "Padding and domain separation").

**Argument.** An input carries its length first because the hardware knows the length before it pads,
FR-025 refuses an over-long input before anything changes, and a length prefix makes the encoding
prefix-free with no padding bit to reason about. A block's last word is the domain word because it
then stands at one place at every size.

**Argument.** A reseed ends with no forget call because FR-013 asks for none, and because the forget
that ended the last request already stops a backward walk: a reseed input is public in this design
(FR-016), so that a state compromised after it reveals nothing before that forget.

**Residual risk.** A theorem in this chapter bounds the mode with Π ideal, and Π is not ideal. Every
bound here says what a generic attack can do, and nothing about an attack that uses Π's structure.

**Residual risk.** Nonce misuse is stated and not prevented: under a repeated nonce, the blocks the
design document names repeat (design document, chapter "Mode", section "Nonce reuse").

**Untested.** The padding's injectivity has a proof and a committed check; the mode's calls have run
on no permutation, since no candidate and no model exist yet.

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
