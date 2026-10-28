# Contract: File Formats

## `data/lut/perturbation_lut.hex` (RTL-consumable table, FR-012)

- ASCII, LF line endings, exactly 256 lines, no header or comments.
- Line *i* holds `T[i]` as 4 uppercase hex digits (e.g., `0000`, `0400`, `FC00`).
- Loadable by VHDL `textio` `hread` and Verilog `$readmemh`.
- `.gitattributes` must keep LF endings for `*.hex` so the hash stays stable across platforms.

## `vectors/<model>_seed-<s0>-<s1>-<s2>-<s3>_<count>.hex` (golden vectors)

- ASCII, LF line endings.
- Line 1: `# model=<id> seed=<s0>,<s1>,<s2>,<s3> count=<n> format=u32-hex`
- Lines 2 … n+1: one word per line, 8 uppercase hex digits, in generation order.
- Committed files:
  - `vectors/lut-v1_seed-1024-2048-4096-8192_10000.hex`
  - `vectors/float-v0_seed-1024-2048-4096-8192_10000.hex`

## `baseline/float-v0/MANIFEST.json`

```json
{
  "created_utc": "<ISO-8601>",
  "git_head": "<sha>",
  "files": [
    {"archive_path": "baseline/float-v0/readmee_model.py",
     "source": "readmee.md@<sha> (listing in section 2)",
     "sha256": "<hex>", "note": "Reference behavior preserved by lut-v1 except the perturbation source"}
  ]
}
```

## `reports/001-integer-lut-perturbation/nist_<model>_seed-<…>_<bits>.json`

- Statistical results record as defined in [data-model](../data-model.md#statistical-results-record).
- `reports/001-integer-lut-perturbation/summary.md`: a side-by-side table of `float-v0` and
  `lut-v1` per test, written by hand from the JSON records and stating the limitations.
