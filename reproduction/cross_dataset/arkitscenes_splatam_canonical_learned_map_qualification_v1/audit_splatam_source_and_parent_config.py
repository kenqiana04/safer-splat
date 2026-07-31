#!/usr/bin/env python3
"""Fail-closed static audit for the canonical-input ARKitScenes SplaTAM run.

This intentionally audits the exact external authority checkout without modifying
it.  The resulting JSON is evidence that the task-owned adapter is necessary and
that the selected parent configuration is the official ScanNet++ RGB-D mapping
configuration, not an iPhone/NeRF-only path.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_SOURCE_HEAD = "da6bbcd24c248dc884ac7f49d62e91b841b26ccc"
PARENT_CONFIG_REL = "configs/scannetpp/gaussian_splatting.py"
DRIVER_REL = "scripts/gaussian_splatting.py"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True, encoding="utf-8"
    ).strip()


def literal_assignments(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: dict[str, Any] = {}
    for item in tree.body:
        if isinstance(item, ast.Assign) and len(item.targets) == 1:
            target = item.targets[0]
            if isinstance(target, ast.Name):
                try:
                    found[target.id] = ast.literal_eval(item.value)
                except (ValueError, TypeError):
                    pass
    return found


def static_config_value(node: ast.AST) -> Any:
    """Extract inspectable config literals without executing an experiment file."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return {"symbol": node.id}
    if isinstance(node, ast.JoinedStr):
        return {"expression": "f_string"}
    if isinstance(node, ast.List):
        return [static_config_value(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return [static_config_value(item) for item in node.elts]
    if isinstance(node, ast.Dict):
        return {
            str(static_config_value(key)): static_config_value(value)
            for key, value in zip(node.keys, node.values)
        }
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
        return {
            keyword.arg: static_config_value(keyword.value)
            for keyword in node.keywords
            if keyword.arg is not None
        }
    return {"expression": type(node).__name__}


def config_assignment(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for item in tree.body:
        if isinstance(item, ast.Assign) and len(item.targets) == 1:
            target = item.targets[0]
            if isinstance(target, ast.Name) and target.id == "config":
                value = static_config_value(item.value)
                if isinstance(value, dict):
                    return value
    raise RuntimeError("parent config dict assignment unavailable")


def function_source(path: Path, name: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    for item in tree.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == name:
            return "".join(lines[item.lineno - 1 : item.end_lineno])
    raise RuntimeError(f"function {name!r} not found in {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    source = args.source.resolve()
    output_root = args.output_root.resolve()
    parent = source / PARENT_CONFIG_REL
    driver = source / DRIVER_REL
    common_utils = source / "utils/common_utils.py"
    gs_helpers = source / "utils/gs_helpers.py"

    source_head = git(source, "rev-parse", "HEAD")
    assignments = literal_assignments(parent)
    parent_bytes = parent.read_bytes()
    driver_text = driver.read_text(encoding="utf-8")
    dispatch = function_source(driver, "get_dataset")
    offline = function_source(driver, "offline_splatting")
    initialize = function_source(driver, "initialize_first_timestep")
    save_params = function_source(common_utils, "save_params")
    render_params = function_source(gs_helpers, "params2rendervar")

    config_value = config_assignment(parent)
    data = config_value.get("data")
    train = config_value.get("train")
    if not isinstance(data, dict) or not isinstance(train, dict):
        raise RuntimeError("parent config data/train dictionaries unavailable")

    checks = {
        "source_head_exact": source_head == EXPECTED_SOURCE_HEAD,
        "parent_config_exists": parent.is_file(),
        "parent_dataset_is_scannetpp": data.get("dataset_name") == "scannetpp",
        "parent_uses_train_split": data.get("use_train_split") is True,
        "parent_is_rgbd_mapping_config": all(
            key in data
            for key in (
                "basedir",
                "sequence",
                "desired_image_height",
                "desired_image_width",
                "desired_image_height_init",
                "desired_image_width_init",
            )
        ),
        "parent_checkpoint_load_disabled": config_value.get("load_checkpoint") is False,
        "parent_checkpoint_save_disabled": config_value.get("save_checkpoints") is False,
        "parent_camera_rotation_lr_zero": train.get("lrs_mapping", {}).get("cam_unnorm_rots") == 0.0,
        "parent_camera_translation_lr_zero": train.get("lrs_mapping", {}).get("cam_trans") == 0.0,
        "driver_initializes_first_timestep": "initialize_first_timestep(" in offline,
        "driver_c2w_to_w2c": "w2c = torch.linalg.inv(pose)" in initialize,
        "driver_metric_rgbd_backprojection": "get_pointcloud(color, depth, intrinsics, w2c" in initialize,
        "driver_saves_final_params": "save_params(params, output_dir)" in offline
        and "np.savez(save_path, **to_save)" in save_params,
        "renderer_expands_log_scales_once": "torch.exp(torch.tile(params['log_scales'], (1, 3)))" in render_params,
        "renderer_sigmoids_logits_once": "torch.sigmoid(params['logit_opacities'])" in render_params,
        "renderer_normalizes_wxyz_rotations": "F.normalize(params['unnorm_rotations'])" in render_params,
        "driver_has_scannetpp_dispatch": "ScannetPPDataset" in dispatch,
        "driver_has_no_native_arkitscenes_dispatch": "arkitscenes" not in dispatch.lower(),
        "driver_uses_adapter_compatible_dataset_contract": all(
            marker in driver_text
            for marker in (
                "dataset = get_dataset(",
                "mapping_dataset = get_dataset(",
                "eval_dataset = get_dataset(",
            )
        ),
    }
    if not all(checks.values()):
        failures = [name for name, passed in checks.items() if not passed]
        raise RuntimeError("SOURCE_CONFIG_AUDIT_FAILURE=" + ",".join(failures))

    output_root.mkdir(parents=True, exist_ok=True)
    parent_identity = {
        "source_head": source_head,
        "source_path": str(source),
        "parent_config_path": PARENT_CONFIG_REL,
        "parent_config_sha256": sha256_bytes(parent_bytes),
        "selection": "OFFICIAL_SCANNETPP_RGBD_GAUSSIAN_SPLATTING_PARENT",
        "rejected_parent_classes": [
            "iphone_or_nerf_only_configuration",
            "checkpoint_or_resume_configuration",
            "unrelated_dataset_configuration",
        ],
    }
    semantics = {
        "status": "PASS_SPLATAM_SOURCE_AND_PARENT_CONFIG_STATIC_AUDIT",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": parent_identity,
        "checks": checks,
        "parent_semantics": {
            "dataset_name": data["dataset_name"],
            "use_train_split": data["use_train_split"],
            "load_checkpoint": config_value["load_checkpoint"],
            "save_checkpoints": config_value["save_checkpoints"],
            "gaussian_distribution": config_value["gaussian_distribution"],
            "camera_learning_rates": {
                key: train["lrs_mapping"][key]
                for key in ("cam_unnorm_rots", "cam_trans")
            },
        },
        "adapter_requirement": {
            "required": True,
            "reason": "official driver has no ARKitScenes dataset dispatch",
            "permitted_integration": "task_owned_wrapper_monkeypatches_only_get_dataset",
            "official_source_modified": False,
        },
    }
    (output_root / "official_parent_config_identity.json").write_text(
        json.dumps(parent_identity, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_root / "splatam_source_semantics_audit.json").write_text(
        json.dumps(semantics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(semantics["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
