"""Run Gaussian-SLAM map construction without the native aligned trajectory evaluator."""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--python", type=Path, required=True); p.add_argument("--repo", type=Path, required=True); p.add_argument("--config", type=Path, required=True); p.add_argument("--output", type=Path, required=True); p.add_argument("--log", type=Path, required=True); a = p.parse_args()
    if a.output.exists():
        raise RuntimeError(f"GAUSSIAN_SLAM_OUTPUT_MUST_BE_NEW:{a.output}")
    a.output.parent.mkdir(parents=True, exist_ok=True); a.log.parent.mkdir(parents=True, exist_ok=True)
    launcher = a.output.parent / "run_official_gaussian_slam_map_only.py"
    launcher.write_text("import sys\nfrom pathlib import Path\nrepo=Path(sys.argv[1]); config_path=sys.argv[2]\nsys.path.insert(0,str(repo))\nfrom src.utils.io_utils import load_config, save_dict_to_ckpt\nfrom src.utils.utils import setup_seed\nfrom src.entities.gaussian_slam import GaussianSLAM\nc=load_config(config_path); setup_seed(c['seed']); g=GaussianSLAM(c)\noriginal_map=g.mapper.map\ndef capture_last_model(frame_id, estimate_c2w, gaussian_model, is_new_submap):\n    g._task_last_gaussian_model=gaussian_model\n    return original_map(frame_id, estimate_c2w, gaussian_model, is_new_submap)\ng.mapper.map=capture_last_model\ng.run()\n# Export-only task hook: the official loop persists completed submaps but not its final live submap.\n# Capture the exact post-map object without changing a mapping update or optimizer decision.\nmodel=g._task_last_gaussian_model\nsave_dict_to_ckpt({'gaussian_params': model.capture_dict(), 'submap_keyframes': sorted(g.keyframes_info)}, 'final_submap.ckpt', directory=g.output_path/'submaps')\n", encoding="utf-8")
    env = os.environ.copy(); env.update({"CUDA_VISIBLE_DEVICES": "1", "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    with a.log.open("w", encoding="utf-8") as log:
        result = subprocess.run([str(a.python), str(launcher), str(a.repo), str(a.config)], cwd=a.repo, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"GAUSSIAN_SLAM_STAGE_FAILED:{result.returncode}")
    print("GAUSSIAN_SLAM_STAGE_PASS")


if __name__ == "__main__": main()
