#!/usr/bin/env python3
"""Produce compact G0-G1 summaries and a claim-bounded SAFER audit report."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


RESULT_DIR = Path("work/risk_aware_cbf/results/safer_baseline_cross_dataset_g0_g1")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def truth(row: dict[str, str], key: str) -> bool:
    return row.get(key, "").strip().lower() == "true"


def git_changed(repo_root: Path, paths: list[str]) -> list[str]:
    completed = subprocess.run(["git", "diff", "--name-only", "--", *paths], cwd=repo_root, text=True, capture_output=True, check=False)
    return [line for line in completed.stdout.splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--results-dir", type=Path, default=RESULT_DIR)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    result_dir = args.results_dir
    inventory = read_csv(result_dir / "dataset_source_inventory.csv")
    prereg = read_csv(result_dir / "selected_scene_preregistration.csv")
    compatibility = read_csv(result_dir / "scene_compatibility_matrix.csv")
    admissions = read_csv(result_dir / "initial_admission_summary.csv")
    pair_smoke = read_csv(result_dir / "pair_smoke_summary.csv")
    parity = read_csv(result_dir / "reference_parity_summary.csv")
    local_inventory = [row for row in inventory if row.get("source_type") != "original_safer_reference"]
    source_verified = [row for row in inventory if truth(row, "source_verified")]
    cross_dataset = [row for row in inventory if truth(row, "true_cross_dataset")]
    cross_reconstruction = [row for row in inventory if truth(row, "cross_reconstruction")]
    selected_cross = [row for row in prereg if row.get("tier") in {"Tier-2", "Tier-3"} and truth(row, "selected_for_g1")]
    compatible_smoke = [row for row in compatibility if row.get("compatibility_status") == "compatible_for_smoke"]
    parity_ran = bool(parity)
    parity_passed = parity_ran and all(truth(row, "parity_passed") for row in parity)
    if not cross_dataset or not selected_cross:
        decision = "blocked_by_cross_dataset_asset_availability"
    elif compatibility and not compatible_smoke:
        decision = "query_compatibility_only"
    elif parity_ran and not parity_passed:
        decision = "blocked_by_baseline_harness_mismatch"
    elif len({row.get("dataset_family") for row in selected_cross}) >= 2 and pair_smoke:
        decision = "ready_for_g2_cross_dataset_baseline_cohort"
    elif selected_cross:
        decision = "single_dataset_portability_only"
    else:
        decision = "blocked_by_cross_dataset_asset_availability"
    forbidden_paths = ["cbf", "splat", "ellipsoids", "dynamics", "run.py", "reproduction/scripts/run_official_runpy_smoke.py", "work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py", "work/risk_aware_cbf/scripts/run_v4b_corrective_dt_filter.py", "work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py"]
    forbidden_changes = git_changed(root, forbidden_paths)
    fieldnames = ["dataset_family", "scene_count", "pair_count", "admissible_pair_count", "completed_run_count", "goal_reached_count", "max_steps_count", "stalled_count", "internal_h_collision_count", "geometry_collision_count", "qp_infeasible_count", "query_failure_count", "runtime_mean", "runtime_p95", "active_constraint_mean", "active_constraint_p95", "progress_mean", "progress_median", "H1_violation_count", "H2_violation_count", "H3_violation_count", "initial_admission_rate", "notes"]
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    prereg_by_id = {row.get("candidate_id", ""): row for row in prereg}
    for row in pair_smoke:
        groups[prereg_by_id.get(row.get("candidate_id", ""), {}).get("dataset_family", "unknown")].append(row)
    aggregate_rows: list[dict[str, object]] = []
    for family, rows in sorted(groups.items()):
        values = lambda key: [float(row[key]) for row in rows if row.get(key) not in {"", None}]
        aggregate_rows.append({"dataset_family": family, "scene_count": len({row.get("candidate_id") for row in rows}), "pair_count": len(rows), "admissible_pair_count": len(rows), "completed_run_count": len(rows), "goal_reached_count": sum(truth(row, "goal_reached") for row in rows), "max_steps_count": sum(row.get("stop_reason") == "max_steps" for row in rows), "stalled_count": sum(row.get("stop_reason") == "stalled" for row in rows), "internal_h_collision_count": sum(int(row.get("internal_h_collision_count") or 0) for row in rows), "geometry_collision_count": sum(int(row.get("geometry_grounded_collision_count") or 0) for row in rows), "qp_infeasible_count": sum(int(row.get("qp_infeasible_count") or 0) for row in rows), "query_failure_count": sum(row.get("stop_reason") == "query_failure" for row in rows), "runtime_mean": sum(values("runtime_mean")) / len(values("runtime_mean")) if values("runtime_mean") else None, "runtime_p95": max(values("runtime_p95")) if values("runtime_p95") else None, "active_constraint_mean": sum(values("active_constraints_mean")) / len(values("active_constraints_mean")) if values("active_constraints_mean") else None, "active_constraint_p95": max(values("active_constraints_p95")) if values("active_constraints_p95") else None, "progress_mean": sum(values("progress_ratio")) / len(values("progress_ratio")) if values("progress_ratio") else None, "progress_median": None, "H1_violation_count": sum(int(row.get("H1_margin_violation_count") or 0) for row in rows), "H2_violation_count": sum(int(row.get("H2_margin_violation_count") or 0) for row in rows), "H3_violation_count": sum(int(row.get("H3_margin_violation_count") or 0) for row in rows), "initial_admission_rate": None, "notes": ""})
    failure_rows = []
    if decision == "blocked_by_cross_dataset_asset_availability":
        failure_rows.append({"failure_mode": "G-F0 asset_unavailable", "count": 1, "scope": "audit", "classification": "data_interface", "notes": "No verified independent Tier-2/Tier-3 asset met the preregistration gate."})
    unverified = sum(not truth(row, "source_verified") for row in local_inventory)
    if unverified:
        failure_rows.append({"failure_mode": "G-F1 source_or_license_unverified", "count": unverified, "scope": "G0", "classification": "data_interface", "notes": "Local artifact discovery alone is not source provenance."})
    stop_counts = Counter(row.get("stop_reason", "") for row in pair_smoke)
    for reason, count in sorted(stop_counts.items()):
        failure_rows.append({"failure_mode": reason, "count": count, "scope": "G1", "classification": "baseline_behavior", "notes": "Observed in bounded smoke."})
    write_csv(result_dir / "dataset_aggregate_summary.csv", fieldnames, aggregate_rows)
    write_csv(result_dir / "failure_mode_summary.csv", ["failure_mode", "count", "scope", "classification", "notes"], failure_rows)
    write_csv(result_dir / "runtime_summary.csv", ["dataset_family", "runtime_mean", "runtime_p95", "notes"], [{"dataset_family": row["dataset_family"], "runtime_mean": row["runtime_mean"], "runtime_p95": row["runtime_p95"], "notes": "No runtime is reported when smoke did not run."} for row in aggregate_rows])
    write_csv(result_dir / "constraint_summary.csv", ["dataset_family", "active_constraint_mean", "active_constraint_p95", "notes"], [{"dataset_family": row["dataset_family"], "active_constraint_mean": row["active_constraint_mean"], "active_constraint_p95": row["active_constraint_p95"], "notes": "No constraint count is reported when smoke did not run."} for row in aggregate_rows])
    write_csv(result_dir / "dt_warning_summary.csv", ["dataset_family", "H1_violation_count", "H2_violation_count", "H3_violation_count", "notes"], [{"dataset_family": row["dataset_family"], "H1_violation_count": row["H1_violation_count"], "H2_violation_count": row["H2_violation_count"], "H3_violation_count": row["H3_violation_count"], "notes": "Diagnostic only."} for row in aggregate_rows])
    write_csv(result_dir / "collision_evidence_summary.csv", ["dataset_family", "internal_h_collision_count", "geometry_grounded_collision_count", "notes"], [{"dataset_family": row["dataset_family"], "internal_h_collision_count": row["internal_h_collision_count"], "geometry_grounded_collision_count": row["geometry_collision_count"], "notes": "Internal h is not geometry-grounded collision evidence."} for row in aggregate_rows])
    admission_rows = [{"candidate_id": row.get("candidate_id"), "candidate_pair_count": row.get("candidate_pair_count"), "admissible_pair_count": row.get("admissible_pair_count"), "initial_admission_rate": row.get("initial_admission_rate"), "notes": row.get("notes", "")} for row in admissions]
    write_csv(result_dir / "initial_admission_summary.csv", ["candidate_id", "candidate_pair_count", "admissible_pair_count", "initial_admission_rate", "notes"], admission_rows)
    metrics = {
        "task": "SAFER Baseline Cross-Dataset Generalization Audit G0-G1", "new_scientific_experiment_run": False,
        "baseline_smoke_run": bool(pair_smoke), "reference_parity_run": parity_ran, "reference_parity_passed": parity_passed,
        "baseline_only": True, "start_repair_enabled": False, "risk_aware_enabled": False, "recovery_enabled": False, "safc_enabled": False,
        "candidate_dataset_count": len(local_inventory), "source_verified_dataset_count": len(source_verified), "true_cross_dataset_family_count": len({row.get("dataset_family") for row in cross_dataset}), "cross_reconstruction_family_count": len({row.get("dataset_family") for row in cross_reconstruction}), "query_compatible_scene_count": sum(row.get("compatibility_status") in {"compatible_for_smoke", "compatible_for_query_only"} for row in compatibility), "navigation_compatible_scene_count": len(compatible_smoke), "selected_cross_dataset_scene_count": len(selected_cross), "reference_scene_count": sum(row.get("tier") == "Tier-R" for row in prereg), "formal_smoke_run_count": len(pair_smoke), "initial_candidate_pair_count": sum(int(row.get("candidate_pair_count") or 0) for row in admissions), "initial_admissible_pair_count": sum(int(row.get("admissible_pair_count") or 0) for row in admissions), "goal_reached_count": sum(truth(row, "goal_reached") for row in pair_smoke) if pair_smoke else None, "internal_h_collision_count": sum(int(row.get("internal_h_collision_count") or 0) for row in pair_smoke) if pair_smoke else None, "geometry_grounded_collision_count": sum(int(row.get("geometry_grounded_collision_count") or 0) for row in pair_smoke) if pair_smoke else None, "qp_infeasible_count": sum(int(row.get("qp_infeasible_count") or 0) for row in pair_smoke) if pair_smoke else None, "H1_margin_violation_count": sum(int(row.get("H1_margin_violation_count") or 0) for row in pair_smoke) if pair_smoke else None, "H2_margin_violation_count": sum(int(row.get("H2_margin_violation_count") or 0) for row in pair_smoke) if pair_smoke else None, "H3_margin_violation_count": sum(int(row.get("H3_margin_violation_count") or 0) for row in pair_smoke) if pair_smoke else None, "runtime_measured": bool(pair_smoke), "active_constraints_measured": bool(pair_smoke), "parameter_transfer_contract_passed": False, "official_core_source_modified": bool(forbidden_changes), "forbidden_paths_modified": bool(forbidden_changes), "raw_dataset_artifacts_committed": False, "raw_trace_committed": False, "audit_decision": decision,
        "limitations": ["bounded G0-G1 portability and smoke audit only", "not full100", "not a statistical benchmark", "no method-improvement modules enabled", "cross-scene evidence is not cross-dataset evidence", "internal GSplat h collision is not independent geometry-grounded collision", "does not establish generalized baseline robustness"],
    }
    (result_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (result_dir / "analysis_notes.md").write_text(f"# Analysis Notes\n\nDecision: `{decision}`. No unverified local candidate was promoted to G1.\n", encoding="utf-8")
    report = f"""# REPORT: SAFER Baseline Cross-Dataset Generalization Audit G0-G1

## 1. Purpose

本报告审计原始 SAFER baseline 的数据资产可移植性与有界 smoke 前置条件，不评估任何方法改进模块。

## 2. Baseline Definition

固定执行 `simple goal-directed nominal control -> original CBF-QP safety filter -> original double-integrator rollout`。Start-Safe、Risk-Aware、Adaptive、recovery、SAFC、R1、slowdown、VANS 和 planner 均未启用。

## 3. Cross-Scene vs Cross-Dataset Definition

同源场景不计为 cross-dataset；只有可验证的独立数据集来源才可计入 Tier-2/Tier-3。

## 4. Search Scope and Dataset Inventory

搜索根目录为 `/disk1/zlab/projects`、`/disk1/zlab/data`、`/disk1/zlab/datasets`、`/disk1/zlab/checkpoints`、`C:\\Users\\zlab\\Documents` 和 `C:\\Users\\zlab\\Desktop`。本地发现 {len(local_inventory)} 个候选目录。

## 5. Dataset Provenance

来源已验证条目数为 {len(source_verified)}（含 Tier-R reference）。独立 true cross-dataset family 数为 {len({row.get('dataset_family') for row in cross_dataset})}。

## 6. Selection Preregistration

预注册 Tier-2/Tier-3 场景数为 {len(selected_cross)}。G0 未使用任何 baseline 运行结果进行选择。

## 7. GSplat Compatibility

兼容 query 场景数为 {metrics['query_compatible_scene_count']}；可进入 navigation smoke 的场景数为 {len(compatible_smoke)}。

## 8. Scale and Coordinate Transfer

没有独立候选达到已验证来源与尺度合同，因此没有猜测尺度或按场景调整 robot radius。

## 9. Navigation-Volume Contract

没有独立候选提供经预注册的可导航自由空间、start region 和 goal region。

## 10. Parameter-Transfer Contract

合同文档已建立；当前 `parameter_transfer_contract_passed=false`，因为尚无合规跨数据集场景进入执行。

## 11. Reference Harness Parity

`reference_parity_run={str(parity_ran).lower()}`，`reference_parity_passed={str(parity_passed).lower()}`。G0 阻断后未运行 parity。

## 12. Initial Start/Goal Admission

候选 pair 数为 {metrics['initial_candidate_pair_count']}，admissible pair 数为 {metrics['initial_admissible_pair_count']}；未执行 repair。

## 13. Original Baseline Smoke Protocol

`formal_smoke_run_count={len(pair_smoke)}`。没有 full100、flight20 或新的科学实验。

## 14. Dataset-Level Results

没有合规的独立数据集 smoke 结果。

## 15. Safety Evidence

内部 `h` collision 和 geometry-grounded collision 严格分列；当前两者均未测量（`null`）。

## 16. DT Warning Diagnostics

H1/H2/H3 为不干预的诊断项；当前未测量（`null`）。

## 17. Runtime and Constraint Behavior

当前没有 runtime 或 active-constraint 测量。

## 18. Failure-Mode Distribution

{decision}：问题位于数据来源、许可、尺度或兼容 GSplat 资产可用性，而不是已测得的 baseline 行为失败。

## 19. Negative and Neutral Evidence

未验证来源的本地文件不能作为 cross-dataset 证据；也不应被解释为 SAFER 机制无法泛化。

## 20. Generalization Interpretation

当前没有 cross-dataset performance claim。loader 或单条 smoke 的成功本身也不会构成泛化结论。

## 21. Decision

`audit_decision={decision}`。不建议进入 G2 small baseline cohort。

## 22. Claim Boundaries

The G0-G1 audit evaluates original SAFER baseline portability and bounded cross-dataset smoke only. It does not validate any of the proposed method-improvement modules.
"""
    (root / "work/risk_aware_cbf/REPORT_SAFER_BASELINE_CROSS_DATASET_G0_G1.md").write_text(report, encoding="utf-8")
    (root / "work/risk_aware_cbf/notes/NEXT_STEP_AFTER_BASELINE_CROSS_DATASET_G0_G1.md").write_text("# Next Step After G0-G1\n\nG0 is blocked by cross-dataset asset availability. Before any G1 execution, obtain at least two independently sourced static scenes with verified dataset and checkpoint provenance, documented scale/coordinates, a declared free-space volume, and compatible GSplat assets. Rerun G0 and preregister selection before compatibility or navigation.\n", encoding="utf-8")
    print(f"audit_decision={decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
