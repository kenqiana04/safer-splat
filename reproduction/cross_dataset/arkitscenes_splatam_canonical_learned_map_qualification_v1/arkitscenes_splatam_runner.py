#!/usr/bin/env python3
"""Run the immutable official SplaTAM mapper with the task-owned ARKit adapter."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path


EXPECTED_SOURCE_HEAD = "da6bbcd24c248dc884ac7f49d62e91b841b26ccc"


def source_head(source: Path) -> str:
    import subprocess

    return subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--require-new-output", action="store_true")
    args = parser.parse_args()
    source = args.source.resolve()
    config_path = args.config.resolve()
    if source_head(source) != EXPECTED_SOURCE_HEAD:
        raise RuntimeError("official SplaTAM source identity mismatch")
    if not config_path.is_file():
        raise FileNotFoundError(config_path)

    task_module_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(task_module_dir))
    sys.path.insert(0, str(source))
    from arkitscenes_splatam_dataset import ARKitScenesSplaTAMDataset
    import scripts.gaussian_splatting as official

    original_get_dataset = official.get_dataset

    def task_dataset_dispatch(config_dict, basedir, sequence, **kwargs):
        if config_dict.get("dataset_name", "").lower() == "arkitscenes":
            return ARKitScenesSplaTAMDataset(config_dict, basedir, sequence, **kwargs)
        return original_get_dataset(config_dict, basedir, sequence, **kwargs)

    official.get_dataset = task_dataset_dispatch
    experiment = SourceFileLoader(config_path.stem, str(config_path)).load_module()
    config = experiment.config
    if config["data"]["dataset_name"] != "arkitscenes" or config["data"]["sequence"] != "48018874":
        raise RuntimeError("runner requires canonical ARKitScenes scene configuration")
    if config["use_wandb"] is not False:
        raise RuntimeError("wandb must remain disabled")
    results_dir = Path(config["workdir"]) / config["run_name"]
    if args.require_new_output and results_dir.exists():
        raise FileExistsError(f"refusing to reuse output directory: {results_dir}")

    official.seed_everything(seed=config["seed"])
    results_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(config_path, results_dir / "config.py")
    os.environ.setdefault("WANDB_MODE", "offline")
    official.offline_splatting(config)
    print("OFFICIAL_SPLATAM_ADAPTER_RUN_COMPLETED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
