"""Per-frame metric, encoding, and atomic PNG helpers for formal V3 rendering."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Tuple

import imageio.v3 as iio
import numpy as np

from _common import fsync_directory, sha256_path


def rgb_stats(value: np.ndarray) -> Dict[str, Any]:
    return {"shape": list(value.shape), "dtype": str(value.dtype), "min": int(value.min()), "max": int(value.max()), "mean": float(value.mean()), "std": float(value.std()), "nonzero_fraction": float((value > 0).mean()), "v1_black": not (int(value.max()) > 0 and float((value > 0).mean()) > .01), "v3_threshold_failure": float((value > 0).mean()) < .05, "sha256_raw": hashlib.sha256(value.tobytes()).hexdigest()}


def depth_stats(metric: np.ndarray) -> Dict[str, Any]:
    finite = np.isfinite(metric)
    positive = metric > 0
    valid = metric[finite & positive]
    return {"shape": list(metric.shape), "dtype": str(metric.dtype), "finite_fraction": float(finite.mean()), "zero_fraction": float((metric == 0).mean()), "positive_fraction": float(positive.mean()), "min_positive_m": float(valid.min()) if valid.size else None, "median_positive_m": float(np.median(valid)) if valid.size else None, "max_m": float(metric[finite].max()) if finite.any() else None, "v1_all_zero": not bool(positive.any()), "v3_threshold_failure": float(positive.mean()) < .10, "sha256_raw": hashlib.sha256(metric.tobytes()).hexdigest()}


def frame_valid(rgb: Dict[str, Any], depth: Dict[str, Any]) -> bool:
    return bool(rgb["shape"] == [480, 640, 3] and rgb["dtype"] == "uint8" and not rgb["v1_black"] and not rgb["v3_threshold_failure"] and depth["shape"] == [480, 640] and depth["dtype"] in {"float32", "float64"} and depth["finite_fraction"] == 1.0 and not depth["v1_all_zero"] and not depth["v3_threshold_failure"])


def atomic_png(path: Path, array: np.ndarray) -> Tuple[np.ndarray, str]:
    if path.exists():
        raise RuntimeError("final_frame_path_exists:" + str(path))
    temporary = path.with_name("." + path.stem + ".tmp.png")
    if temporary.exists():
        raise RuntimeError("temporary_frame_path_exists:" + str(temporary))
    iio.imwrite(temporary, array)
    with temporary.open("rb") as handle:
        os.fsync(handle.fileno())
    reread = iio.imread(temporary)
    os.replace(temporary, path)
    fsync_directory(path.parent)
    final = iio.imread(path)
    if not np.array_equal(reread, final):
        raise RuntimeError("temporary_final_png_mismatch:" + str(path))
    return final, sha256_path(path)
