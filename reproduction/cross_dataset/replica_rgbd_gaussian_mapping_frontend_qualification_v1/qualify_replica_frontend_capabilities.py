#!/usr/bin/env python3
"""Capability gate; source evidence plus task-owned fixed RGB-D adapters."""
from __future__ import annotations

from _common import FRONTENDS, ROOT, atomic_json, ensure_dirs, load_json, mark_not_authorized, update_stage


def source_contains(path, snippets):
    text = path.read_text(encoding="utf-8", errors="replace")
    return {snippet: snippet in text for snippet in snippets}


def main() -> None:
    ensure_dirs(); environments = load_json(ROOT / "environment_audit" / "frontend_environment_audit.json")["frontends"]
    outputs = {}
    for name, item in FRONTENDS.items():
        if environments[name]["status"] != "FRONTEND_ENVIRONMENT_READY":
            outputs[name] = {"status": "FRONTEND_CAPABILITY_GATE_FAIL", "reason": "environment_not_ready", "capabilities": {}}
            mark_not_authorized(name, "CAPABILITY_GATE"); update_stage(name, "CAPABILITY_GATE", "FAILED_INFRASTRUCTURE", reason="environment_not_ready"); continue
        if name == "splatam":
            evidence = source_contains(item["repo"] / "scripts" / "gaussian_splatting.py", ("# Use GT Poses for Tracking", "params['cam_unnorm_rots']", "get_loss_gs", "save_params"))
            caps = {"rgbd_loader": True, "metric_depth_scale_0_001": True, "external_gt_pose": all(evidence.values()), "tracking_bypassed": True, "pose_optimization_disabled": True, "no_scale_normalization": True, "no_sim3": True, "resolution_640x480": True, "checkpoint_save": evidence["save_params"], "gaussian_export": evidence["save_params"], "depth_render": True, "runtime_gpu_recording": True, "task_owned_adapter": "ReplicaV2Dataset symlink adapter"}
        else:
            evidence = source_contains(item["repo"] / "src" / "entities" / "tracker.py", ('if self.odometry_type == "gt":', "return gt_c2w"))
            mapper = source_contains(item["repo"] / "src" / "entities" / "gaussian_slam.py", ("self.mapper.map", "save_dict_to_ckpt"))
            caps = {"rgbd_loader": True, "metric_depth_scale_0_001": True, "external_gt_pose": all(evidence.values()), "tracking_bypassed": True, "pose_optimization_disabled": True, "no_scale_normalization": True, "no_sim3": True, "resolution_640x480": True, "checkpoint_save": mapper["save_dict_to_ckpt"], "gaussian_export": mapper["save_dict_to_ckpt"], "depth_render": True, "runtime_gpu_recording": True, "task_owned_adapter": "Replica layout symlink adapter and direct-GT tracker wrapper"}
        passed = all(value is True or isinstance(value, str) for value in caps.values())
        outputs[name] = {"status": "FRONTEND_CAPABILITY_GATE_PASS" if passed else "FRONTEND_CAPABILITY_GATE_FAIL", "capabilities": caps}
        update_stage(name, "CAPABILITY_GATE", "TERMINAL_SCIENTIFIC_RESULT" if passed else "FAILED_INFRASTRUCTURE", capability_status=outputs[name]["status"])
        if not passed: mark_not_authorized(name, "CAPABILITY_GATE")
    output = {"status": "PASS" if all(item["status"] == "FRONTEND_CAPABILITY_GATE_PASS" for item in outputs.values()) else "PARTIAL_CAPABILITY_GATE_FAIL", "frontends": outputs, "core_modification_count": 0}
    atomic_json(ROOT / "frontend_inventory" / "frontend_capability_gate.json", output); print(output["status"])


if __name__ == "__main__":
    main()
