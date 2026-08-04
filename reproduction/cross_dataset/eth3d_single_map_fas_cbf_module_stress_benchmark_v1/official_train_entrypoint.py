#!/usr/bin/env python3
"""External seed wrapper for the immutable official 3DGS train.py.

The upstream entrypoint hard-codes seed zero.  The frozen protocol requires
20260804, so this wrapper replaces only the RNG initialization callback and then
executes the exact upstream train.py without editing its source.
"""

from __future__ import annotations

import argparse
import random
import runpy
import sys
from pathlib import Path

import numpy as np
import torch


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--official-source", type=Path, required=True)
    parser.add_argument("--frozen-seed", type=int, required=True)
    known, remaining = parser.parse_known_args()

    source = known.official_source.resolve(strict=True)
    train_py = source / "train.py"
    if not train_py.is_file():
        raise RuntimeError(f"official train.py unavailable: {train_py}")
    sys.path.insert(0, str(source))

    from utils import general_utils  # pylint: disable=import-outside-toplevel

    original_safe_state = general_utils.safe_state

    def frozen_safe_state(silent: bool) -> None:
        original_safe_state(silent)
        random.seed(known.frozen_seed)
        np.random.seed(known.frozen_seed)
        torch.manual_seed(known.frozen_seed)
        torch.cuda.manual_seed_all(known.frozen_seed)

    general_utils.safe_state = frozen_safe_state
    sys.argv = [str(train_py), *remaining]
    print(f"FROZEN_TRAIN_SEED={known.frozen_seed}")
    print(f"OFFICIAL_TRAIN_SOURCE={train_py}")
    runpy.run_path(str(train_py), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
