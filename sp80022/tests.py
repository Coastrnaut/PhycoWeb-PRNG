"""All 15 SP 800-22 tests under one namespace, in SP 800-22 order (contracts/sp80022-api.md)."""
from .tests_basic import block_frequency, dft, frequency, longest_run, rank, runs
from .tests_complex import approximate_entropy, linear_complexity, serial, universal
from .tests_template import non_overlapping_template, overlapping_template
from .tests_walk import cumulative_sums, random_excursions, random_excursions_variant

ORDER = (frequency, block_frequency, runs, longest_run, rank, dft, non_overlapping_template,
         overlapping_template, universal, linear_complexity, serial, approximate_entropy,
         cumulative_sums, random_excursions, random_excursions_variant)
