#!/usr/bin/env python3
"""Record the immutable Gaussian-SLAM smoke configuration incompatibility.

No source, renderer, CUDA function, input frame, or map is touched.  The
official configuration requests 600000 unique seed pixels while a V3 640x480
frame has at most 307200; changing that core hyperparameter is forbidden.
"""
from __future__ import annotations

from _common import ROOT, atomic_json, load_json, mark_not_authorized, update_stage


def main() -> None:
    summary_path = ROOT / "gaussian_slam" / "smoke_summary.json"
    summary = load_json(summary_path)
    if summary.get("status") != "SMOKE_ALGORITHM_FAILURE":
        raise SystemExit(f"unexpected smoke state: {summary.get('status')}")
    cause = {
        "status": "FRONTEND_CONFIG_NOT_QUALIFIED",
        "frontend": "Gaussian-SLAM",
        "official_config_parameter": "mapping.new_submap_points_num",
        "official_config_value": 600000,
        "replica_v3_adapter_resolution": [640, 480],
        "maximum_available_pixels": 307200,
        "exception": "ValueError: Cannot take a larger sample than population when replace=False",
        "classification": "frozen core frontend hyperparameter incompatible with frozen V3 adapter geometry",
        "retry_authorized": False,
        "reason": "protocol permits a retry only with the same config; changing the core sampling parameter is forbidden",
        "first_failure_log": str(ROOT / "logs" / "gaussian_slam_smoke.log"),
        "no_scientific_rerun": True,
    }
    resolution_path = ROOT / "pilot_registry" / "frontend_config_qualification_resolution.json"
    current = load_json(resolution_path) if resolution_path.exists() else {"frontends": {}}
    current.setdefault("frontends", {})["gaussian_slam"] = cause
    current["frontends"].setdefault("splatam", {"status": "FRONTEND_CONFIG_QUALIFIED"})
    atomic_json(resolution_path, current)
    summary.update({"configuration_qualification": cause["status"], "root_cause": cause["exception"], "retry_authorized": False, "failure_classification": cause["classification"]})
    atomic_json(summary_path, summary)
    update_stage("gaussian_slam", "SMOKE", "TERMINAL_SCIENTIFIC_RESULT", result_status=summary["status"], configuration_qualification=cause["status"])
    mark_not_authorized("gaussian_slam", "SMOKE")
    print(cause["status"])


if __name__ == "__main__":
    main()
