"""Audit export semantics; never convert maps unless every semantic is proved."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--splatam-output", type=Path, required=True); p.add_argument("--gaussian-slam-output", type=Path, required=True); p.add_argument("--output", type=Path, required=True); a = p.parse_args()
    # SplaTAM names parameters explicitly but its depth renderer and Gaussian-SLAM
    # multi-submap frame/export convention require a separately executable proof.
    out = {"status": "COMMON_ADAPTER_UNRESOLVED", "reason": "no jointly executable export-to-GSplatLoader proof completed",
           "SplaTAM": {"expected_fields": ["means3D", "log_scales", "unnorm_rotations", "logit_opacities", "rgb_colors"], "output_exists": a.splatam_output.exists()},
           "Gaussian-SLAM": {"expected_fields": ["xyz", "features", "scaling", "rotation", "opacity"], "output_exists": a.gaussian_slam_output.exists()},
           "prohibited_without_verification": ["common_expected_depth", "static_SAFER", "frozen908", "gradient", "continuity", "G0"]}
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__": main()
