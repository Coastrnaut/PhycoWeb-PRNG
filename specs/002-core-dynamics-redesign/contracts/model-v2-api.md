# Contract: `phycoweb/model_v2.py`

This mirrors the feature-001 model API ([001 model-api](../../001-integer-lut-perturbation/contracts/model-api.md)),
so tools can treat both models the same way.

```text
MODEL_ID: str = "phyco-v2"
WARMUP: int                      # steps run inside __init__ before the first word
class PhycoWebEngineV2:
    def __init__(self, seed: Sequence[int])   # 4 ints 0..65535, else ValueError
    def compute_block(self) -> int            # 0 <= w < 2**32
    disruptions: int                          # count of disruption firings so far
    step_count: int                           # steps taken, including the warm-up
```

- No other public mutable attributes are needed by the tools. Tests may read internal state to
  check widths.
- Importing the module has no side effects and does not import numpy.
- `phycoweb/model.py` (lut-v1) is not modified. It stays the negative control.
