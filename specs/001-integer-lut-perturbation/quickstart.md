# Quickstart: Validating the Integer LUT Perturbation Source

**Prerequisites**: Python 3.8+ with `numpy`, `nistrng` (`pip install -r requirements.txt`); git
history containing commits `290e563` and `d6980eb`. Run everything from the repository root.

## 1. Archive the floating-point variant (FR-013, SC-006)

```text
python scripts/archive_baseline.py
```

Expected: five files under `baseline/float-v0/` and a `MANIFEST.json` listing five SHA-256
hashes. Running it a second time changes nothing and exits 0.

## 2. Produce the baseline vectors from the old model (FR-014)

```text
python scripts/gen_vectors.py --model float-v0 --seed 1024 2048 4096 8192 --count 10000 \
  --out vectors/float-v0_seed-1024-2048-4096-8192_10000.hex
```

Expected first data line: `D6EDF3D6` (research R2).

## 3. Generate and check the table (FR-003, FR-007a, SC-004)

```text
python scripts/gen_lut.py
python scripts/gen_lut.py --check
```

Expected: `--check` exits 0; line 65 of `data/lut/perturbation_lut.hex` is `0400` and line 193
is `FC00`.

## 4. Produce and verify the LUT golden vectors (FR-010, SC-002)

```text
python scripts/gen_vectors.py --model lut-v1 --seed 1024 2048 4096 8192 --count 10000 \
  --out vectors/lut-v1_seed-1024-2048-4096-8192_10000.hex
python scripts/gen_vectors.py --model lut-v1 --seed 1024 2048 4096 8192 --count 10000 \
  --verify vectors/lut-v1_seed-1024-2048-4096-8192_10000.hex
```

Expected: verify exits 0. Repeat the verify step on a second environment (research R7) and
record the result.

## 5. Run the unit tests (SC-001, SC-003, SC-004, SC-006)

```text
python -m unittest discover -s tests -v
```

Expected: all tests pass, covering the AST purity check, table formula and reference values,
128-step period over 1,280 steps, unchanged non-perturbation stages, manifest hashes, and
golden vectors.

## 6. Statistical evaluation (FR-011, SC-005)

```text
python scripts/nist_eval.py --model float-v0 --seed 1024 2048 4096 8192 --bits 1000000 \
  --out reports/001-integer-lut-perturbation/nist_float-v0_seed-1024-2048-4096-8192_1000000.json
python scripts/nist_eval.py --model lut-v1 --seed 1024 2048 4096 8192 --bits 1000000 \
  --out reports/001-integer-lut-perturbation/nist_lut-v1_seed-1024-2048-4096-8192_1000000.json
```

Repeat with `--seed 4660 43981 21845 43690` (`0x1234 0xABCD 0x5555 0xAAAA`). Expected: each
report lists every battery test with a status. Record the outcomes as they are in
`summary.md`, whatever they are.

## 7. Human result review (Principle VIII)

The repository owner reviews the vectors and NIST summary and fills in the "Result review" row
in spec.md. Only then is the feature complete.
