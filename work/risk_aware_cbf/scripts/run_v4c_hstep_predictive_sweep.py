#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


CONFIGS = [
    {"config_id": "P0_H3_default", "horizon": 3, "num_sequences": 128, "num_elites": 16, "sequence_noise_scale": 0.15, "w_goal": 0.2, "w_safety": 10.0, "use_cem": False, "cem_iters": 2},
    {"config_id": "P1_H5", "horizon": 5, "num_sequences": 128, "num_elites": 16, "sequence_noise_scale": 0.15, "w_goal": 0.2, "w_safety": 10.0, "use_cem": False, "cem_iters": 2},
    {"config_id": "P2_H5_more_sequences", "horizon": 5, "num_sequences": 256, "num_elites": 16, "sequence_noise_scale": 0.15, "w_goal": 0.2, "w_safety": 10.0, "use_cem": False, "cem_iters": 2},
    {"config_id": "P3_H5_more_conservative", "horizon": 5, "num_sequences": 256, "num_elites": 16, "sequence_noise_scale": 0.25, "w_goal": 0.1, "w_safety": 20.0, "use_cem": False, "cem_iters": 2},
    {"config_id": "P4_H3_goal_preserving", "horizon": 3, "num_sequences": 128, "num_elites": 16, "sequence_noise_scale": 0.15, "w_goal": 0.5, "w_safety": 10.0, "use_cem": False, "cem_iters": 2},
    {"config_id": "P5_H5_CEM", "horizon": 5, "num_sequences": 128, "num_elites": 16, "sequence_noise_scale": 0.15, "w_goal": 0.2, "w_safety": 10.0, "use_cem": True, "cem_iters": 2},
]

SWEEP_FIELDS = [
    "config_id",
    "horizon",
    "num_sequences",
    "use_cem",
    "collision_count",
    "qp_infeasible_count",
    "base_horizon_margin_violation_count",
    "exec_horizon_margin_violation_count",
    "horizon_margin_violation_reduction",
    "predictive_recovery_used_count",
    "predictive_recovery_success_count",
    "recovery_failed_count",
    "progress_mean",
    "runtime_mean",
    "runtime_p95",
    "runtime_recovery_mean",
    "control_delta_mean",
    "min_safety_h_min",
    "output_dir",
]


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({f: row.get(f, "") for f in fields})


def json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_ready(v) for v in value]
    return value


def run(args: argparse.Namespace) -> list[dict[str, Any]]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    script = Path(__file__).resolve().with_name("run_v4c_hstep_predictive_recovery.py")
    rows: list[dict[str, Any]] = []
    for cfg in CONFIGS:
        config_dir = output_dir / cfg["config_id"]
        cmd = [
            sys.executable,
            str(script),
            "--scene",
            args.scene,
            "--method",
            args.method,
            "--safety-margin",
            str(args.safety_margin),
            "--dt-margin",
            str(args.dt_margin),
            "--warning-margin",
            str(args.warning_margin),
            "--max-steps",
            str(args.max_steps),
            "--candidate-budget",
            str(args.candidate_budget),
            "--near-distance-threshold",
            str(args.near_distance_threshold),
            "--heading-distance-threshold",
            str(args.heading_distance_threshold),
            "--heading-cos-threshold",
            str(args.heading_cos_threshold),
            "--risk-score",
            args.risk_score,
            "--horizon",
            str(cfg["horizon"]),
            "--num-sequences",
            str(cfg["num_sequences"]),
            "--num-elites",
            str(cfg["num_elites"]),
            "--sequence-noise-scale",
            str(cfg["sequence_noise_scale"]),
            "--control-scale-list",
            args.control_scale_list,
            "--w-base",
            str(args.w_base),
            "--w-goal",
            str(cfg["w_goal"]),
            "--w-smooth",
            str(args.w_smooth),
            "--w-safety",
            str(cfg["w_safety"]),
            "--activation-mode",
            args.activation_mode,
            "--output-dir",
            str(config_dir),
            "--resume",
            "--skip-existing",
            "--device",
            args.device,
        ]
        if args.trial_list:
            cmd.extend(["--trial-list", str(args.trial_list)])
        if args.trial_start is not None and args.trial_end is not None:
            cmd.extend(["--trial-start", str(args.trial_start), "--trial-end", str(args.trial_end)])
        if args.use_startguard:
            cmd.append("--use-startguard")
        if args.startguard_projection_dir:
            cmd.extend(["--startguard-projection-dir", str(args.startguard_projection_dir)])
        if args.include_braking_sequences:
            cmd.append("--include-braking-sequences")
        if args.include_repulsive_sequences:
            cmd.append("--include-repulsive-sequences")
        if args.include_goal_directed_sequences:
            cmd.append("--include-goal-directed-sequences")
        if cfg["use_cem"]:
            cmd.append("--use-cem")
            cmd.extend(["--cem-iters", str(cfg["cem_iters"])])

        log_path = output_dir / f"{cfg['config_id']}.log"
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"[{datetime.now().isoformat(timespec='seconds')}] RUN {' '.join(cmd)}\n")
            log.flush()
            subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)

        summary_rows = read_rows(config_dir / "summary.csv")
        summary = summary_rows[0] if summary_rows else {}
        row = {
            "config_id": cfg["config_id"],
            "horizon": cfg["horizon"],
            "num_sequences": cfg["num_sequences"],
            "use_cem": cfg["use_cem"],
            "output_dir": str(config_dir),
        }
        row.update(summary)
        rows.append(row)

    write_csv(output_dir / "sweep_summary.csv", rows, SWEEP_FIELDS)
    trial_rows = []
    for row in rows:
        for trial in read_rows(Path(row["output_dir"]) / "trials.csv"):
            trial = dict(trial)
            trial["config_id"] = row["config_id"]
            trial_rows.append(trial)
    if trial_rows:
        fields = ["config_id"] + list(trial_rows[0].keys())
        write_csv(output_dir / "sweep_trials.csv", trial_rows, list(dict.fromkeys(fields)))
    (output_dir / "sweep_metrics.json").write_text(json.dumps(json_ready({"configs": CONFIGS, "summary": rows}), indent=2), encoding="utf-8")
    write_plot(output_dir, rows)
    return rows


def write_plot(output_dir: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        labels = [r["config_id"] for r in rows]
        base = [float(r.get("base_horizon_margin_violation_count") or 0.0) for r in rows]
        exec_v = [float(r.get("exec_horizon_margin_violation_count") or 0.0) for r in rows]
        runtime = [float(r.get("runtime_mean") or 0.0) for r in rows]
        fig, axes = plt.subplots(1, 2, figsize=(13, 4))
        x = np.arange(len(labels))  # type: ignore[name-defined]
        axes[0].bar(x - 0.15, base, width=0.3, label="base")
        axes[0].bar(x + 0.15, exec_v, width=0.3, label="exec")
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(labels, rotation=25, ha="right")
        axes[0].legend()
        axes[0].set_title("H-step margin violations")
        axes[1].bar(labels, runtime)
        axes[1].tick_params(axis="x", rotation=25)
        axes[1].set_title("runtime mean")
        fig.tight_layout()
        fig.savefig(output_dir / "sweep_plots.png", dpi=170)
        plt.close(fig)
    except Exception:
        return


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="V4-C H-step predictive recovery sweep.")
    parser.add_argument("--scene", choices=["flight", "stonehenge"], required=True)
    parser.add_argument("--trial-list", type=Path, default=None)
    parser.add_argument("--trial-start", type=int, default=None)
    parser.add_argument("--trial-end", type=int, default=None)
    parser.add_argument("--method", choices=["risk_aware_v1_bestD", "safer_splat_filter"], required=True)
    parser.add_argument("--use-startguard", action="store_true")
    parser.add_argument("--startguard-projection-dir", type=Path, default=None)
    parser.add_argument("--safety-margin", type=float, default=0.0005)
    parser.add_argument("--dt-margin", type=float, default=0.0005)
    parser.add_argument("--warning-margin", type=float, default=0.0008)
    parser.add_argument("--max-steps", type=int, default=800)
    parser.add_argument("--candidate-budget", type=int, default=2000)
    parser.add_argument("--near-distance-threshold", type=float, default=0.05)
    parser.add_argument("--heading-distance-threshold", type=float, default=0.25)
    parser.add_argument("--heading-cos-threshold", type=float, default=0.5)
    parser.add_argument("--risk-score", default="risk_v2_hybrid")
    parser.add_argument("--control-scale-list", default="0,0.25,0.5,0.75,1.0")
    parser.add_argument("--include-braking-sequences", action="store_true", default=True)
    parser.add_argument("--include-repulsive-sequences", action="store_true", default=True)
    parser.add_argument("--include-goal-directed-sequences", action="store_true", default=True)
    parser.add_argument("--w-base", type=float, default=1.0)
    parser.add_argument("--w-smooth", type=float, default=0.1)
    parser.add_argument("--activation-mode", choices=["always", "on_margin_violation", "on_warning"], default="on_margin_violation")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    rows = run(args)
    print(json.dumps(json_ready(rows), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
