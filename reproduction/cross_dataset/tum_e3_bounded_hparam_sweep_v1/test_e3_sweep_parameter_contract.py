"""Static/dynamic guard for the only three allowed E3 sweep parameters."""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import sys
from pathlib import Path


def load_launch(path: Path):
    spec = importlib.util.spec_from_file_location("sweep_launch", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"LAUNCHER_LOAD_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def comparison_contract(model_path: Path) -> dict[str, bool]:
    tree = ast.parse(model_path.read_text(encoding="utf-8"))
    text = ast.unparse(tree)
    weighted_depth_assignments = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.BinOp) or not isinstance(node.value.op, ast.Mult):
            continue
        target_text = " ".join(ast.unparse(target) for target in node.targets)
        value_text = ast.unparse(node.value)
        if "loss_depth_metric" in target_text and "effective_lambda" in value_text and "depth_loss" in value_text:
            weighted_depth_assignments += 1
    return {
        "late_lambda_applies_from_step_3000": "int(self.step) >= self.config.late_depth_hold_start" in text,
        "refinement_lock_applies_at_configured_step": "step >= self.config.refinement_lock_step" in text,
        "smooth_l1_uses_configured_beta": "metric_depth_huber_loss(prediction, target, accumulation, self.config.depth_loss_beta_m)" in text,
        "single_weighted_metric_depth_loss": weighted_depth_assignments == 1,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--launcher", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root))
    module = load_launch(args.launcher)
    cases = [
        ("lambda_low", .20, 3000, .10), ("lambda_high", .50, 3000, .10),
        ("lock_early", .30, 2000, .10), ("lock_late", .30, 4000, .10),
        ("beta_low", .30, 3000, .05), ("beta_high", .30, 3000, .20),
    ]
    dynamic = {}
    for label, late_lambda, lock_step, beta_m in cases:
        cfg = module.prepare_config(args.source_root, label, Path("/tmp/nonexistent_sweep_contract") / label, 100, late_lambda, lock_step, beta_m)
        model = cfg.pipeline.model
        dynamic[label] = {
            "late_depth_hold_start": int(model.late_depth_hold_start), "late_depth_hold_lambda": float(model.late_depth_hold_lambda),
            "refinement_lock_step": int(model.refinement_lock_step), "depth_loss_beta_m": float(model.depth_loss_beta_m),
            "depth_loss_lambda": float(model.depth_loss_lambda), "seed": int(cfg.machine.seed),
            "load_dir_is_none": cfg.load_dir is None, "load_checkpoint_is_none": cfg.load_checkpoint is None,
        }
    expected = {label: {"late_depth_hold_start": 3000, "late_depth_hold_lambda": late_lambda, "refinement_lock_step": lock_step, "depth_loss_beta_m": beta_m, "depth_loss_lambda": .10, "seed": 20260716, "load_dir_is_none": True, "load_checkpoint_is_none": True} for label, late_lambda, lock_step, beta_m in cases}
    static = comparison_contract(args.source_root / "tum_metric_depth_splatfacto.py")
    pass_dynamic = dynamic == expected
    result = {"static_contract": static, "dynamic_contract": dynamic, "expected": expected, "all_pass": all(static.values()) and pass_dynamic, "status": "PASS" if all(static.values()) and pass_dynamic else "BLOCKED_BY_E3_SWEEP_CONFIG_CONTRACT", "step_boundary_contract": {"step_2999": "base depth_loss_lambda (no late hold)", "step_3000": "late_depth_hold_lambda", "lock": "step >= configured refinement_lock_step"}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if not result["all_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
