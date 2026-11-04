"""Disclaimer text that every feature-002 report carries (FR-019, SC-007, Security Policy)."""

DISCLAIMER = (
    "Passing NIST SP 800-22 does not show cryptographic security. "
    "This generator must not be used to generate secrets; use an established cryptographic "
    "random-number generator for keys, nonces, tokens and salts."
)

# The design-form disclaimer of feature 004, the block directly under the title of
# specs/004-crypto-architecture-v3/spec.md, its lines joined by single spaces (FR-068).
DESIGN_DISCLAIMER = (
    "This feature makes no security claim. No PhycoWeb-PRNG model, `phyco-v3` included, may be "
    "used to generate secrets; use an established cryptographic random-number generator for keys, "
    "nonces, tokens and salts. Passing statistical tests does not show cryptographic security."
)
