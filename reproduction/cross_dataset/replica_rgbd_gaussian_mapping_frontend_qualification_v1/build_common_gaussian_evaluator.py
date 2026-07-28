#!/usr/bin/env python3
"""Freeze the one shared Gaussian rasterizer contract before any frontend result exists."""
from __future__ import annotations

from _common import FRONTENDS, ROOT, atomic_json, ensure_dirs, sha256_path


def main() -> None:
    ensure_dirs(); source = FRONTENDS["gaussian_slam"]["repo"] / "src" / "utils" / "utils.py"
    contract = {"status": "COMMON_EVALUATOR_READY", "implementation": "task-owned wrapper around Gaussian-SLAM GaussianRasterizer for both canonical map schemas", "renderer_source": str(source), "renderer_source_sha256": sha256_path(source), "renderer_environment": str(FRONTENDS["gaussian_slam"]["python"].parent.parent), "rasterization_backend": "shared diff-gaussian depth-plus-alpha rasterizer", "depth_mode": "shared alpha-composited camera-z depth returned by GaussianRasterizer", "opacity_accumulation": "backend alpha compositing", "transmittance_threshold": "depth>0 and finite", "near_m": 0.05, "far_m": 20.0, "background": [0, 0, 0], "pixel_center_convention": "frozen V3 integer pixel centers", "intrinsics_source": "replica_mapping_input_contract.json", "pose_source": "frozen V3 holdout c2w transformed by fixed OpenGL-to-OpenCV camera transform", "resolution": [640, 480], "deterministic_flags": {"seed": 0, "cudnn_benchmark": False, "shared_evaluator": True}, "method_native_metric_selection_forbidden": True}
    atomic_json(ROOT / "common_evaluator" / "common_gaussian_evaluator_contract.json", contract); print(contract["status"])


if __name__ == "__main__": main()
