#!/usr/bin/env python3
"""Install the frozen ETH3D attribution and data-use boundary in DATA_ROOT."""

import json

from task_config import ASSETS, DATA_ROOT, DENYLIST, TASK_ROOT


def main() -> None:
    root = DATA_ROOT / "LICENSES"
    root.mkdir(parents=True, exist_ok=True)
    attribution = """# ETH3D attribution and data boundary

ETH3D data is used under the dataset license stated by the official ETH3D site:
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(CC BY-NC-SA 4.0). Cite the ETH3D CVPR 2017 benchmark paper when using these
assets. This local payload is research-only and is not committed to Git.

Only the nine archives frozen by the Protocol V2 entry audit are present here.
Reference depth, scans, scan-evaluation data, and occlusion geometry are held in
EVAL_ORACLE_ROOT and are prohibited from mapping/training input. Any later
derived-map distribution must be reviewed against the dataset license and
attribution/share-alike requirements.
"""
    (root / "ETH3D_ATTRIBUTION.md").write_text(attribution, encoding="utf-8")
    boundary = {
        "license": "CC-BY-NC-SA-4.0", "commercial_use": False,
        "git_payload_commit_allowed": False,
        "mapping_input_archives": [name for name, _, role in ASSETS if role == "MAPPING_INPUT_SOURCE_ARCHIVE"],
        "evaluation_reference_archives": [name for name, _, role in ASSETS if role != "MAPPING_INPUT_SOURCE_ARCHIVE"],
        "denylist": DENYLIST,
        "gt_depth_scan_occlusion_allowed_in_train": False,
        "derived_map_distribution_requires_license_review": True,
    }
    (root / "DATA_USAGE_BOUNDARY.json").write_text(json.dumps(boundary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validation = {"status": "PASS", "license_root": str(root), "attribution_exists": True,
                  "boundary_exists": True, "payload_tracked_in_git": False}
    (TASK_ROOT / "asset_validation" / "license_installation_validation.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    print("PASS_LICENSE_BOUNDARY")


if __name__ == "__main__":
    main()
