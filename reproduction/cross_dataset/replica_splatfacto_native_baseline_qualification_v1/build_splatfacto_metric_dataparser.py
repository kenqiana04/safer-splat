#!/usr/bin/env python3
"""Build task-owned, metric-pose Replica transforms without copying assets."""
from __future__ import annotations

from _common import DATASET, PR56_ROOT, ROOT, atomic_json, ensure_dirs, load_json, sha256_path, update_stage


def _symlink(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or target.exists():
        if target.is_symlink() and target.resolve() == source.resolve():
            return
        raise RuntimeError("refusing to overwrite adapter member: " + str(target))
    target.symlink_to(source)


def _source_frames():
    payload = load_json(DATASET / "formal_camera_manifest_v3.json")
    return {row["frame_id"]: row for row in payload["frames"]}


def _order():
    return load_json(PR56_ROOT / "pilot_registry" / "replica_frontend_map_only_order.json")


def _ids(order, candidate_names, expected_count):
    for name in candidate_names:
        value = order.get(name)
        if isinstance(value, list) and len(value) == expected_count:
            if value and isinstance(value[0], dict):
                return [item.get("frame_id") for item in value]
            return value
    raise RuntimeError("missing frozen frame list: " + ", ".join(candidate_names))


def _write_adapter(name, mapping_ids, holdout_ids, source):
    root = ROOT / "pilot_adapter" / name
    images = root / "images"
    frames = []
    for frame_id in mapping_ids + holdout_ids:
        row = source.get(frame_id)
        if row is None:
            raise RuntimeError("frame absent from source manifest: " + str(frame_id))
        source_image = DATASET / "images" / (frame_id + ".png")
        target_image = images / (frame_id + ".png")
        _symlink(source_image, target_image)
        frames.append({
            "file_path": "images/" + frame_id + ".png",
            "transform_matrix": row["camera_to_world"],
        })
    payload = {
        "camera_model": "OPENCV",
        "fl_x": 320.0, "fl_y": 320.0, "cx": 319.5, "cy": 239.5,
        "w": 640, "h": 480,
        "frames": frames,
        "train_filenames": ["images/" + item + ".png" for item in mapping_ids],
        "val_filenames": ["images/" + item + ".png" for item in holdout_ids],
        "test_filenames": ["images/" + item + ".png" for item in holdout_ids],
        "metric_pose_contract": {
            "source": "Replica RGB-D V3",
            "c2w_convention": "V1_VERIFIED_HABITAT_Y_UP_NERFSTUDIO_OPENGL_C2W",
            "orientation_method": "none", "center_method": "none",
            "auto_scale_poses": False, "scale_factor": 1.0, "scene_scale": 1.0,
            "depth_supervision": False,
        },
    }
    path = root / "transforms.json"
    atomic_json(path, payload)
    return {"name": name, "root": str(root), "transforms": str(path), "sha256": sha256_path(path), "mapping_frame_ids": mapping_ids, "holdout_frame_ids": holdout_ids, "symlink_count": len(frames)}


def main():
    ensure_dirs()
    order = _order()
    source = _source_frames()
    smoke_mapping = _ids(order, ("smoke_mapping_frame_ids", "smoke_mapping_frames", "smoke_train_frame_ids"), 16)
    smoke_holdout = _ids(order, ("smoke_holdout_frame_ids", "smoke_holdout_frames", "smoke_eval_frame_ids"), 8)
    pilot_mapping = _ids(order, ("mapping_frame_order", "pilot_mapping_frame_ids", "mapping_frame_ids"), 60)
    pilot_holdout = _ids(order, ("holdout_frame_order", "pilot_holdout_frame_ids", "holdout_frame_ids"), 30)
    checks = {
        "source_frame_ids_unique": len(source) == 300,
        "smoke_disjoint": not set(smoke_mapping).intersection(smoke_holdout),
        "pilot_disjoint": not set(pilot_mapping).intersection(pilot_holdout),
        "pilot_uses_train_only": all(source[item]["split"] == "train" for item in pilot_mapping + pilot_holdout),
        "smoke_uses_train_only": all(source[item]["split"] == "train" for item in smoke_mapping + smoke_holdout),
    }
    if not all(checks.values()):
        raise SystemExit("BLOCKED_BY_SPLATFACTO_ADAPTER_FRAME_CONTRACT")
    adapters = {
        "smoke": _write_adapter("smoke", smoke_mapping, smoke_holdout, source),
        "qualification_pilot": _write_adapter("qualification_pilot", pilot_mapping, pilot_holdout, source),
    }
    out = {"status": "SPLATFACTO_METRIC_DATASET_ADAPTER_BUILT", "source_dataset": str(DATASET), "order_source": str(PR56_ROOT / "pilot_registry" / "replica_frontend_map_only_order.json"), "adapters": adapters, "checks": checks}
    atomic_json(ROOT / "pilot_adapter" / "splatfacto_metric_dataset_adapter_identity.json", out)
    update_stage("DATASET_ADAPTER", "TERMINAL_SCIENTIFIC_RESULT", result_status=out["status"], smoke_frames=24, pilot_frames=90)
    print(out["status"])


if __name__ == "__main__":
    main()
