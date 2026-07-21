"""Create a compact, non-payload record of task-owned server artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    build = root / "build"
    paths = {"splatam_params": build / "runs/splatam_full240/params.npz", "splatam_config": build / "splatam_full240_config.py",
             "gaussian_slam_config": build / "gaussian_slam_full240.yaml", "splatam_result": build / "splatam_result_summary.json",
             "gaussian_slam_result": build / "gaussian_slam_result_summary.json", "frame_registry": build / "frozen_frame_registry_summary.json"}
    runs = {"splatam_full240": build / "runs/splatam_full240", "gaussian_slam_full240": build / "runs/gaussian_slam_full240"}
    gpu = subprocess.check_output(["nvidia-smi", "-i", "1", "--query-gpu=index,name,uuid,driver_version", "--format=csv,noheader"], text=True).strip()
    conda = subprocess.check_output([str(root / "envs/tum_gaussian_slam_baseline_v1_conda/bin/python"), "-c", "import torch,faiss; print(torch.__version__,torch.version.cuda,faiss.__version__)"], text=True).strip()
    out = {"status": "PASS", "gpu_1": gpu, "gaussian_slam_runtime": conda,
           "artifacts": {label: {"path": str(path), "sha256": digest(path), "size": path.stat().st_size} for label, path in paths.items()},
           "runs": {label: {"path": str(path), "mapping_vis_count": len(list((path / "mapping_vis").glob("*.jpg"))),
                             "submap_checkpoint_count": len(list((path / "submaps").glob("*.ckpt")))} for label, path in runs.items()}}
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
