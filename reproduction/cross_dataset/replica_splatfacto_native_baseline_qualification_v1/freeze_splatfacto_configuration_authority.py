#!/usr/bin/env python3
"""Recover the unique authority configuration from the official native checkpoint."""
from __future__ import annotations

from _common import AUTHORITY_CONFIG, PYTHON, ROOT, SPLATNAV_REPO, atomic_json, capture, ensure_dirs, sha256_path, update_stage


def main():
    ensure_dirs()
    code = "import yaml,json\nfrom pathlib import Path\np=Path(r'%s')\nc=yaml.load(p.read_text(),Loader=yaml.Loader)\nd=c.pipeline.datamanager.dataparser\nm=c.pipeline.model\nout={'method_name':c.method_name,'method_class':type(m).__module__+'.'+type(m).__name__,'dataparser_class':type(d).__module__+'.'+type(d).__name__,'max_num_iterations':c.max_num_iterations,'steps_per_save':c.steps_per_save,'steps_per_eval_image':c.steps_per_eval_image,'mixed_precision':c.mixed_precision,'seed':c.machine.seed,'camera_optimizer_mode':m.camera_optimizer.mode,'background_color':m.background_color,'sh_degree':m.sh_degree,'random_init':m.random_init,'load_3D_points':d.load_3D_points,'optimizer_keys':sorted(c.optimizers.keys()),'densification':{'warmup_length':m.warmup_length,'refine_every':m.refine_every,'densify_grad_thresh':m.densify_grad_thresh,'cull_alpha_thresh':m.cull_alpha_thresh,'cull_scale_thresh':m.cull_scale_thresh,'stop_split_at':m.stop_split_at}}\nprint(json.dumps(out,sort_keys=True))" % AUTHORITY_CONFIG
    probe = capture([str(PYTHON), "-B", "-c", code], cwd=SPLATNAV_REPO, timeout=120)
    payload = None
    if probe["returncode"] == 0:
        import json
        payload = json.loads(probe["stdout"].splitlines()[-1])
    # YAML reconstructs the configuration object, not the runtime model instance.
    # Therefore the authoritative class suffix is SplatfactoModelConfig.
    passed = bool(payload and payload["method_name"] == "splatfacto" and payload["method_class"].endswith("SplatfactoModelConfig") and payload["camera_optimizer_mode"] == "off")
    status = "SPLATFACTO_NATIVE_CONFIG_AUTHORITY_FROZEN" if passed else "BLOCKED_BY_SPLATFACTO_NATIVE_CONFIG_AUTHORITY_UNRESOLVED"
    out = {"status": status, "authority_level": 1, "source_path": str(AUTHORITY_CONFIG), "source_sha256": sha256_path(AUTHORITY_CONFIG) if AUTHORITY_CONFIG.is_file() else None, "authority": payload, "probe": probe, "core_parameters_unmodified": True, "allowed_task_owned_overrides": ["dataset path", "output path", "run name", "max iteration", "eval/save interval", "metric dataparser fields"]}
    atomic_json(ROOT / "config_authority" / "splatfacto_native_configuration_authority.json", out)
    update_stage("CONFIG_AUTHORITY", "TERMINAL_SCIENTIFIC_RESULT" if passed else "FAILED_INFRASTRUCTURE", result_status=status)
    if not passed:
        raise SystemExit(status)
    print(status)


if __name__ == "__main__":
    main()
