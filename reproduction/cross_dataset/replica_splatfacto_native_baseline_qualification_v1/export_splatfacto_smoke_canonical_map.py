#!/usr/bin/env python3
"""Losslessly export native Splatfacto Gaussian parameters from its checkpoint."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from _common import PYTHON, ROOT, SPLATNAV_REPO, atomic_json, ensure_dirs, load_json, sha256_path, task_env, update_stage


def _export(stage):
    import torch
    from nerfstudio.utils.eval_utils import eval_setup
    summary_path = ROOT / stage / ("splatfacto_smoke_summary.json" if stage == "smoke" else "splatfacto_pilot_summary.json")
    required = "SPLATFACTO_SMOKE_OPERATIONAL_PASS" if stage == "smoke" else "SPLATFACTO_PILOT_COMPLETE"
    output_summary = ROOT / "canonical_export" / ("splatfacto_smoke_canonical_export_summary.json" if stage == "smoke" else "splatfacto_pilot_canonical_export_summary.json")
    if not summary_path.is_file() or load_json(summary_path).get("status") != required:
        atomic_json(output_summary, {"status": "NOT_AUTHORIZED_DUE_TO_" + stage.upper(), "required": required})
        print("NOT_AUTHORIZED_DUE_TO_" + stage.upper()); return 1
    summary = load_json(summary_path); config_path = Path(summary["runtime_config"])
    config, pipeline, checkpoint, step = eval_setup(config_path, test_mode="inference")
    model = pipeline.model
    means = model.means.detach().float().cpu().numpy()
    scales = torch.exp(model.scales.detach()).float().cpu().numpy()
    quats = model.quats.detach().float().cpu().numpy(); quats /= np.linalg.norm(quats, axis=1, keepdims=True)
    opacities = torch.sigmoid(model.opacities.detach()).float().cpu().numpy().reshape(-1)
    sh = torch.cat((model.features_dc.detach().unsqueeze(1), model.features_rest.detach()), dim=1).float().cpu().numpy()
    values = {"means_world_m": means, "scales_linear_m": scales, "quaternions_wxyz": quats, "opacities": opacities, "sh_coefficients": sh}
    n = int(means.shape[0]); valid = n > 0 and means.shape == (n, 3) and scales.shape == (n, 3) and quats.shape == (n, 4) and opacities.shape == (n,) and sh.shape[0] == n and all(np.isfinite(item).all() for item in values.values()) and bool((scales > 0).all())
    target = ROOT / "canonical_export" / stage
    if target.exists():
        raise RuntimeError("canonical export target already exists; refusing to overwrite: " + str(target))
    target.mkdir(parents=True)
    arrays = {}
    for name, value in values.items():
        path = target / (name + ".npy")
        np.save(path, np.ascontiguousarray(value.astype(np.float32, copy=False)), allow_pickle=False)
        arrays[name] = {"shape": list(value.shape), "dtype": "float32", "sha256": sha256_path(path)}
    identity = {"stage": stage, "source_checkpoint": str(checkpoint), "source_checkpoint_sha256": sha256_path(checkpoint), "runtime_config": str(config_path), "runtime_config_sha256": sha256_path(config_path), "checkpoint_step": step, "source_representation": "Nerfstudio Splatfacto means/log-scales/quaternions/logit-opacities/features_dc/features_rest", "coordinate_transform": "identity: metric V3 world and Nerfstudio dataparser transform are identity", "scale_conversion": "exp(log scales)", "quaternion_conversion": "source WXYZ normalized", "opacity_conversion": "sigmoid(logit opacities)", "sh_conversion": "concatenate DC then remaining SH coefficients", "gaussian_index_order": "native checkpoint parameter order; no filtering, pruning, downsampling, merging, or reordering", "world_units": "metres", "arrays": arrays, "gaussian_count": n, "valid": bool(valid), "no_filtering": True, "no_scale_fitting": True}
    atomic_json(target / "canonical_map_identity.json", identity)
    status = "SPLATFACTO_" + ("SMOKE" if stage == "smoke" else "PILOT") + "_CANONICAL_EXPORT_PASS" if valid else "SPLATFACTO_" + ("SMOKE" if stage == "smoke" else "PILOT") + "_EXPORT_FAILURE"
    out = {"status": status, "canonical_root": str(target), "identity": str(target / "canonical_map_identity.json"), "gaussian_count": n, "arrays": arrays, "valid": bool(valid), "no_filtering": True}
    atomic_json(output_summary, out)
    update_stage("SMOKE_EXPORT" if stage == "smoke" else "PILOT_EXPORT", "TERMINAL_SCIENTIFIC_RESULT" if valid else "FAILED_INFRASTRUCTURE", result_status=status, summary=str(output_summary))
    print(status)
    return 0 if valid else 1


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--stage", choices=("smoke", "qualification_pilot"), default="smoke"); args = parser.parse_args()
    raise SystemExit(_export(args.stage))


if __name__ == "__main__":
    main()
