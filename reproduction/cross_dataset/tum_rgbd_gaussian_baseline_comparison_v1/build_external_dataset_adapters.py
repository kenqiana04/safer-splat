"""Build task-owned TUM-format symlink adapters from the frozen 240/60 registry."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def quat_xyzw(matrix: list[list[float]]) -> tuple[float, float, float, float]:
    m = np.asarray(matrix, dtype=np.float64)[:3, :3]
    q = np.empty(4, dtype=np.float64)
    trace = float(np.trace(m))
    if trace > 0:
        s = np.sqrt(trace + 1.0) * 2.0; q[3] = 0.25 * s
        q[0] = (m[2, 1] - m[1, 2]) / s; q[1] = (m[0, 2] - m[2, 0]) / s; q[2] = (m[1, 0] - m[0, 1]) / s
    else:
        i = int(np.argmax(np.diag(m)))
        j, k = (i + 1) % 3, (i + 2) % 3
        s = np.sqrt(1.0 + m[i, i] - m[j, j] - m[k, k]) * 2.0
        q[i] = 0.25 * s; q[3] = (m[k, j] - m[j, k]) / s; q[j] = (m[j, i] + m[i, j]) / s; q[k] = (m[k, i] + m[i, k]) / s
    q /= np.linalg.norm(q)
    return tuple(float(x) for x in q)


def write_adapter(records: list[dict], out: Path, name: str) -> dict:
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"ADAPTER_OUTPUT_NOT_EMPTY:{out}")
    (out / "rgb").mkdir(parents=True, exist_ok=True)
    (out / "depth").mkdir(parents=True, exist_ok=True)
    rgb, depth = [], []
    poses = ["# timestamp tx ty tz qx qy qz qw"]
    for local, record in enumerate(records):
        stamp = f"{local * 0.04:.8f}"
        image, dep = Path(record["image"]), Path(record["depth"])
        if sha256(image) != record["rgb_sha256"] or sha256(dep) != record["depth_sha256"]:
            raise RuntimeError(f"FROZEN_FILE_HASH_MISMATCH:{record['frame_index']}")
        rgb_rel, dep_rel = f"rgb/{local:06d}.png", f"depth/{local:06d}.png"
        os.symlink(image, out / rgb_rel)
        os.symlink(dep, out / dep_rel)
        rgb.append(f"{stamp} {rgb_rel}"); depth.append(f"{stamp} {dep_rel}")
        c2w = record["transform_matrix"]; qx, qy, qz, qw = quat_xyzw(c2w)
        tx, ty, tz = (float(c2w[i][3]) for i in range(3))
        poses.append(f"{stamp} {tx:.12g} {ty:.12g} {tz:.12g} {qx:.12g} {qy:.12g} {qz:.12g} {qw:.12g}")
    for filename, lines in (("rgb.txt", rgb), ("depth.txt", depth), ("groundtruth.txt", poses)):
        (out / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"name": name, "path": str(out), "frames": len(records), "timestamp_step_seconds": 0.04,
            "rgb_list_sha256": sha256(out / "rgb.txt"), "depth_list_sha256": sha256(out / "depth.txt"),
            "groundtruth_sha256": sha256(out / "groundtruth.txt"), "symlink_only": True}


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--registry", type=Path, required=True); p.add_argument("--output-root", type=Path, required=True); p.add_argument("--summary", type=Path, required=True); a = p.parse_args()
    registry = json.loads(a.registry.read_text(encoding="utf-8"))
    if len(registry["train_frames"]) != 240 or len(registry["eval_frames"]) != 60:
        raise RuntimeError("FROZEN_SPLIT_CONTRACT_MISMATCH")
    train = write_adapter(registry["train_frames"], a.output_root / "train_240" / "rgbd_dataset_freiburg1_room", "train_240")
    # Official TUMDataset normalizes all poses to its first entry.  Prefixing the
    # first train frame preserves the map's origin while the evaluator explicitly
    # discards index zero and reports metrics over the remaining fixed 60 only.
    eval_anchor = write_adapter([registry["train_frames"][0], *registry["eval_frames"]],
                                a.output_root / "eval_anchor_61" / "rgbd_dataset_freiburg1_room", "eval_anchor_61")
    eval_anchor["metric_frame_count"] = 60
    eval_anchor["anchor_frame_index"] = registry["train_frames"][0]["frame_index"]
    out = {"status": "PASS", "source_registry_sha256": sha256(a.registry), "depth_scale": 0.0002, "adapters": [train, eval_anchor]}
    a.summary.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__": main()
