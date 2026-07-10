#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd


SUMMARY_FIELDS = [
    "source",
    "config_id",
    "scene",
    "method",
    "rows",
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


def parse_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def collect_result_dirs(args: argparse.Namespace) -> list[Path]:
    if args.result_dirs:
        return [Path(p) for p in args.result_dirs]
    base = Path("work/risk_aware_cbf/results")
    dirs: list[Path] = []
    for pattern in (
        "v4c_hstep*_flight_repair_needed_v1_bestD",
        "v4c_hstep_predictive_sweep_flight_repair_needed_v1_bestD",
        "v4c_*flight20*_v1_bestD",
    ):
        dirs.extend(sorted(p for p in base.glob(pattern) if p.is_dir()))
    return list(dict.fromkeys(dirs))


def collect_rows(result_dirs: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result_dir in result_dirs:
        summary_path = result_dir / "summary.csv"
        if summary_path.exists():
            for row in read_rows(summary_path):
                out = {"source": "summary", "config_id": result_dir.name, "output_dir": str(result_dir)}
                out.update(row)
                rows.append(out)
        sweep_path = result_dir / "sweep_summary.csv"
        if sweep_path.exists():
            for row in read_rows(sweep_path):
                out = {"source": "sweep_summary"}
                out.update(row)
                rows.append(out)
    return rows


def select_best(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    eligible = [
        r
        for r in rows
        if parse_float(r.get("collision_count")) == 0.0
        and parse_float(r.get("qp_infeasible_count")) == 0.0
        and parse_float(r.get("exec_horizon_margin_violation_count")) < parse_float(r.get("base_horizon_margin_violation_count"))
    ]
    if not eligible:
        return None
    return sorted(
        eligible,
        key=lambda r: (
            -parse_float(r.get("horizon_margin_violation_reduction")),
            parse_float(r.get("exec_horizon_margin_violation_count")),
            parse_float(r.get("runtime_mean")),
        ),
    )[0]


def write_plot(rows: list[dict[str, Any]], path: Path) -> None:
    if not rows:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    df = pd.DataFrame(rows)
    df["label"] = df["config_id"].fillna(df["output_dir"])
    df["base"] = pd.to_numeric(df["base_horizon_margin_violation_count"], errors="coerce").fillna(0.0)
    df["exec"] = pd.to_numeric(df["exec_horizon_margin_violation_count"], errors="coerce").fillna(0.0)
    df["runtime"] = pd.to_numeric(df["runtime_mean"], errors="coerce").fillna(0.0)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    x = range(len(df))
    axes[0].bar([i - 0.15 for i in x], df["base"], width=0.3, label="base")
    axes[0].bar([i + 0.15 for i in x], df["exec"], width=0.3, label="exec")
    axes[0].set_xticks(list(x))
    axes[0].set_xticklabels(df["label"], rotation=35, ha="right")
    axes[0].set_title("H-step margin violations")
    axes[0].legend()
    axes[1].bar(df["label"], df["runtime"])
    axes[1].tick_params(axis="x", rotation=35)
    axes[1].set_title("runtime mean")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=170)
    plt.close(fig)


def markdown_table(rows: list[dict[str, Any]]) -> str:
    columns = [
        "config_id",
        "rows",
        "collision_count",
        "qp_infeasible_count",
        "base_horizon_margin_violation_count",
        "exec_horizon_margin_violation_count",
        "horizon_margin_violation_reduction",
        "runtime_mean",
        "min_safety_h_min",
    ]
    lines = ["|" + "|".join(columns) + "|", "|" + "|".join(["---"] * len(columns)) + "|"]
    for row in rows:
        lines.append("|" + "|".join(str(row.get(c, "")) for c in columns) + "|")
    return "\n".join(lines)


def write_reports(rows: list[dict[str, Any]], best: dict[str, Any] | None) -> None:
    notes_path = Path("work/risk_aware_cbf/notes/V4C_ANALYSIS.md")
    report_path = Path("work/risk_aware_cbf/REPORT_V4C_HSTEP_PREDICTIVE_RECOVERY.md")
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    best_text = "No eligible configuration reduced H-step margin violations with zero collisions and zero QP infeasibility."
    if best is not None:
        best_text = (
            f"Best eligible configuration: `{best.get('config_id')}` with "
            f"base={best.get('base_horizon_margin_violation_count')}, "
            f"exec={best.get('exec_horizon_margin_violation_count')}, "
            f"reduction={best.get('horizon_margin_violation_reduction')}."
        )
    body = "\n".join(
        [
            "# V4-C H-Step Predictive Recovery Analysis",
            "",
            "This report covers only the V4-C H-step predictive recovery experiment under `work/risk_aware_cbf/`.",
            "It does not claim a full SAFER-Splat paper reproduction.",
            "",
            "## Best Eligible Configuration",
            "",
            best_text,
            "",
            "## Summary Table",
            "",
            markdown_table(rows),
            "",
            "## Output Files",
            "",
            "- `work/risk_aware_cbf/results/v4c_analysis_summary.csv`",
            "- `work/risk_aware_cbf/figures/v4c_hstep_predictive_plots.png`",
            "- `work/risk_aware_cbf/notes/V4C_ANALYSIS.md`",
            "- `work/risk_aware_cbf/REPORT_V4C_HSTEP_PREDICTIVE_RECOVERY.md`",
        ]
    )
    notes_path.write_text(body, encoding="utf-8")
    report_path.write_text(body, encoding="utf-8")


def run(args: argparse.Namespace) -> list[dict[str, Any]]:
    result_dirs = collect_result_dirs(args)
    rows = collect_rows(result_dirs)
    rows = sorted(rows, key=lambda r: str(r.get("config_id", "")))
    write_csv(Path("work/risk_aware_cbf/results/v4c_analysis_summary.csv"), rows, SUMMARY_FIELDS)
    best = select_best(rows)
    Path("work/risk_aware_cbf/results/v4c_best_config.json").write_text(json.dumps({"best": best}, indent=2), encoding="utf-8")
    write_plot(rows, Path("work/risk_aware_cbf/figures/v4c_hstep_predictive_plots.png"))
    write_reports(rows, best)
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze V4-C H-step predictive recovery results.")
    parser.add_argument("--result-dirs", nargs="*", default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    rows = run(args)
    print(json.dumps({"rows": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
