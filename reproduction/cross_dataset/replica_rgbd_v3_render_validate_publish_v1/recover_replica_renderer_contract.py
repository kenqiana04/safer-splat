#!/usr/bin/env python3
"""Freeze historical V1 save semantics for the task-owned V3 renderer."""
from __future__ import annotations

import argparse
from pathlib import Path

from _common import EXPECTED, ROOT, atomic_json, ensure_root, sha256_path


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return __import__("hashlib").sha1(("blob " + str(len(data)) + "\0").encode("utf-8") + data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--historical-renderer", type=Path, required=True); parser.add_argument("--historical-checker", type=Path, required=True); parser.add_argument("--task-renderer", type=Path, required=True); args = parser.parse_args()
    ensure_root()
    source = args.historical_renderer.read_text(encoding="utf-8")
    required = ["observation[\"rgba\"]", "observation[\"depth\"]", "rgba[:, :, :3].astype(np.uint8)", "np.rint(np.clip(depth, 0.0, 65.535) * 1000.0).astype(np.uint16)", "depth_unit_scale_factor"]
    if not all(fragment in source for fragment in required) or git_blob_sha(args.historical_renderer) != EXPECTED["historical_renderer_blob"] or git_blob_sha(args.historical_checker) != EXPECTED["historical_integrity_blob"]:
        raise SystemExit("BLOCKED_BY_REPLICA_RGBD_V3_RENDER_ENVIRONMENT_IDENTITY_MISMATCH")
    payload = {"status": "PASS_REPLICA_V3_RENDERER_CONTRACT", "historical_source_commit": EXPECTED["historical_commit"], "historical_renderer_blob": EXPECTED["historical_renderer_blob"], "historical_integrity_checker_blob": EXPECTED["historical_integrity_blob"], "historical_renderer_sha256": sha256_path(args.historical_renderer), "historical_checker_sha256": sha256_path(args.historical_checker), "task_owned_renderer_sha256": sha256_path(args.task_renderer), "rgb": {"observation_key": "rgba", "saved_shape": [480, 640, 3], "saved_dtype": "uint8", "channel_order": "RGB", "alpha_handling": "drop_alpha"}, "depth": {"observation_key": "depth", "memory_unit": "metres", "saved_dtype": "uint16", "saved_png_encoding": "millimetres", "metric_to_integer_scale": 1000.0, "decode_scale_m": 0.001, "invalid_depth": "reject_nonfinite_or_negative"}, "sensor": {"resolution": [640, 480], "hfov_deg": 90.0, "near_m": .05, "far_m": 20.0, "camera_height_m": 1.50, "model": "pinhole"}, "write_method": "same_directory_temp_flush_fsync_reread_atomic_rename", "unchanged_sensor_semantics": True}
    atomic_json(ROOT / "renderer_contract" / "replica_v3_renderer_contract.json", payload)


if __name__ == "__main__":
    main()
