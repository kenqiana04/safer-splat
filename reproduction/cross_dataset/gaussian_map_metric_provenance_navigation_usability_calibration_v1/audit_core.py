#!/usr/bin/env python3
"""Deterministic core for the Gaussian-map metric provenance audit.

Every phase consumes only tracked compact evidence or read-only availability
observations.  It never writes outside this task root and never opens a map in
write mode.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
ALPHA_GRID = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
TOLERANCE_GRID_M = [0.01, 0.02, 0.03, 0.05, 0.10, 0.20]

FORMULA_SOURCES = {
    "THEORY_DEFINITION", "DATASET_OFFICIAL_DEFINITION",
    "PAPER_OR_BENCHMARK_METRIC_DEFINITION", "OFFICIAL_CODE_SEMANTICS",
    "PROJECT_DEFINED_METRIC",
}
THRESHOLD_SOURCES = {
    "THEORY_DERIVED_HARD_REQUIREMENT", "PHYSICAL_CONTRACT_DERIVED",
    "DATASET_OFFICIAL_THRESHOLD", "PAPER_BENCHMARK_REPORTING_POINT",
    "INDEPENDENT_EMPIRICAL_CALIBRATION", "PROJECT_HEURISTIC",
    "RESOURCE_BUDGET", "SOFTWARE_NUMERICAL_TOLERANCE",
    "UNDOCUMENTED_OR_UNRESOLVED",
}
DECISION_ROLES = {
    "DESCRIPTIVE_ONLY", "DIAGNOSTIC_WARNING", "INTEGRITY_HARD_GATE",
    "PHYSICAL_SAFETY_HARD_GATE", "EMPIRICALLY_CALIBRATED_GATE",
    "LEGACY_UNCALIBRATED_HARD_GATE", "RESOURCE_EXECUTION_GATE",
}

LEGACY_STATUS = "NO_ARKITSCENES_M1_LEARNED_GAUSSIAN_MAP_QUALIFIED_UNDER_FROZEN_CONTRACT"
LEGACY_INTERPRETATION = "FAILED_GLOBAL_DENSE_QUALIFICATION_UNDER_LEGACY_UNCALIBRATED_COVERAGE_GATE"
GLOBAL_DECISION = "NO_UNIVERSAL_NUMERIC_GATE_JUSTIFIED_BY_CURRENT_EVIDENCE"


def run(args: list[str], cwd: Path = REPO, check: bool = True) -> str:
    p = subprocess.run(args, cwd=cwd, text=True, encoding="utf-8", errors="replace",
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode:
        raise RuntimeError(f"command failed {args!r}: {p.stderr.strip()}")
    return p.stdout


def dump_json(name: str, value: Any) -> Path:
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")
    return path


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_csv(name: str, rows: list[dict[str, Any]], columns: list[str]) -> Path:
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def tracked_files() -> list[str]:
    return [x for x in run(["git", "ls-tree", "-r", "--name-only", "HEAD"]).splitlines() if x]


def first_commit_map() -> dict[str, str]:
    raw = run(["git", "log", "--all", "--reverse", "--format=@@%H", "--name-only"])
    commit = ""
    result: dict[str, str] = {}
    for line in raw.splitlines():
        if line.startswith("@@"):
            commit = line[2:]
        elif line and commit:
            result.setdefault(line.replace("\\", "/"), commit)
    return result


def source_inventory() -> dict[str, Any]:
    files = tracked_files()
    relevant = [f for f in files if f.startswith("reproduction/") or f.startswith("REPORTS/")]
    text_ext = {".md", ".json", ".csv", ".py", ".yaml", ".yml", ".toml", ".txt", ".sh"}
    file_rows = []
    for rel in relevant:
        p = REPO / rel
        if p.is_file() and p.suffix.lower() in text_ext:
            file_rows.append({"path": rel, "bytes": p.stat().st_size, "sha256": sha256(p)})
    summary = {
        "schema": "gaussian-map-source-inventory/v1",
        "git_head": run(["git", "rev-parse", "HEAD"]).strip(),
        "branch": run(["git", "branch", "--show-current"]).strip(),
        "ref_count": len(run(["git", "for-each-ref", "--format=%(refname)"]).splitlines()),
        "commit_count": int(run(["git", "rev-list", "--all", "--count"]).strip()),
        "head_file_count": len(files),
        "reproduction_file_count": sum(f.startswith("reproduction/") for f in files),
        "report_count": sum(bool(re.search(r"(^|/)REPORT[^/]*\.md$", f)) for f in files),
        "text_candidate_count": len(file_rows),
        "generated_utc": utc_now(),
        "read_only": True,
    }
    dump_json("source_inventory/source_inventory_summary.json", summary)
    dump_json("source_inventory/source_file_registry.json", {"files": file_rows})
    return summary


METRIC_ALIASES: list[tuple[str, str]] = [
    (r"valid(?:_predicted_depth)?(?:_fraction)?|global[_ -]?coverage|coverage", "coverage"),
    (r"opacity|alpha|silhouette", "renderer_acceptance_alpha"),
    (r"absrel|abs[_ -]?rel", "AbsRel"), (r"sqrel|sq[_ -]?rel", "SqRel"),
    (r"rmse[_ -]?log", "RMSE-log"), (r"rmse", "RMSE"),
    (r"delta[_ -]?1|delta1", "delta1"), (r"delta[_ -]?2|delta2", "delta2"),
    (r"delta[_ -]?3|delta3", "delta3"),
    (r"median(?:_depth)?[_ -]?(?:pred[_ -]?gt[_ -]?)?ratio|depth[_ -]?ratio", "median_depth_ratio"),
    (r"psnr", "PSNR"), (r"ssim", "SSIM"), (r"lpips", "LPIPS"),
    (r"point[_ -]?to[_ -]?mesh|mesh[_ -]?distance", "point_to_mesh"),
    (r"accuracy", "geometry_accuracy"), (r"completeness", "geometry_completeness"),
    (r"f[_ -]?score", "geometry_F_score"),
    (r"gaussian[_ -]?count", "gaussian_count"), (r"nonfinite|nan|inf", "nonfinite_count"),
    (r"one[_ -]?sided|clearance", "one_sided_clearance"),
    (r"epsilon[_ -]?map", "epsilon_map"), (r"false[_ -]?free", "false_free"),
    (r"cluster[_ -]?diameter", "false_free_cluster_diameter"), (r"\bg0\b", "G0"),
    (r"runtime|wall[_ -]?time", "runtime"), (r"gpu|vram", "GPU_memory"),
    (r"\bram\b|rss", "RAM"), (r"route[_ -]?retention", "route_retention"),
    (r"path[_ -]?stretch", "path_stretch"), (r"group[_ -]?support", "group_support"),
    (r"frame[_ -]?support", "frame_support"), (r"keyframe[_ -]?spacing", "keyframe_spacing"),
    (r"train[_ -]?(?:size|count)|train[_ -]?frames", "train_size"),
    (r"heldout[_ -]?(?:size|count)|heldout[_ -]?frames", "heldout_size"),
    (r"robot[_ -]?radius|r_robot", "robot_radius"), (r"epsilon[_ -]?base", "epsilon_base"),
    (r"vmax|velocity[_ -]?(?:max|bound)", "vmax"), (r"umax|acceleration[_ -]?(?:max|bound)", "umax"),
    (r"\bdt\b|time[_ -]?step", "dt"), (r"success[_ -]?(?:threshold|tolerance)", "success_tolerance"),
    (r"deadline|timeout", "deadline"), (r"collision[_ -]?oracle", "collision_oracle"),
    (r"planner|route[_ -]?criteria", "planner_route_criteria"),
]


def metric_for_line(line: str) -> str | None:
    low = line.lower()
    for pattern, metric in METRIC_ALIASES:
        if re.search(pattern, low, re.I):
            return metric
    return None


def formula_source(metric: str) -> str:
    if metric in {"AbsRel", "SqRel", "RMSE", "RMSE-log", "delta1", "delta2", "delta3", "PSNR", "SSIM", "LPIPS", "geometry_accuracy", "geometry_completeness", "geometry_F_score"}:
        return "PAPER_OR_BENCHMARK_METRIC_DEFINITION"
    if metric in {"robot_radius", "epsilon_base", "vmax", "umax", "dt"}:
        return "THEORY_DEFINITION"
    if metric in {"renderer_acceptance_alpha", "G0"}:
        return "OFFICIAL_CODE_SEMANTICS"
    return "PROJECT_DEFINED_METRIC"


def classify_threshold(metric: str, line: str) -> tuple[str, str, bool, str]:
    low = line.lower()
    if any(x in low for x in ("atol", "rtol", "tolerance=1e", "nonfinite", "nan", "finite")):
        return "SOFTWARE_NUMERICAL_TOLERANCE", "INTEGRITY_HARD_GATE", True, "retain_as_integrity_gate"
    if any(x in metric for x in ("GPU", "RAM", "runtime")) or "budget" in low and "error" not in low:
        return "RESOURCE_BUDGET", "RESOURCE_EXECUTION_GATE", True, "retain_only_as_execution_gate"
    if metric in {"robot_radius", "vmax", "umax", "dt", "epsilon_base"}:
        return "PHYSICAL_CONTRACT_DERIVED", "PHYSICAL_SAFETY_HARD_GATE", True, "retain_only_inside_frozen_physical_contract"
    if metric in {"coverage", "renderer_acceptance_alpha", "AbsRel", "delta1", "median_depth_ratio", "point_to_mesh", "one_sided_clearance", "false_free_cluster_diameter", "G0", "route_retention", "path_stretch", "group_support", "frame_support"}:
        return "PROJECT_HEURISTIC", "LEGACY_UNCALIBRATED_HARD_GATE", False, "downgrade_to_descriptive_or_conditionally_calibrated"
    if "threshold" not in low and not any(x in line for x in (">=", "<=", ">", "<")):
        return "UNDOCUMENTED_OR_UNRESOLVED", "DIAGNOSTIC_WARNING", False, "resolve_provenance_before_reuse"
    return "PROJECT_HEURISTIC", "DIAGNOSTIC_WARNING", False, "descriptive_only_pending_calibration"


def threshold_candidates(line: str) -> list[tuple[str, float]]:
    found: list[tuple[str, float]] = []
    for comp, number in re.findall(r"(>=|<=|==|>|<)\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)", line):
        try: found.append((comp, float(number)))
        except ValueError: pass
    key = re.search(r"[\"']?[A-Za-z0-9_-]*(min|gte|max|lte|threshold|tolerance|radius|budget|deadline|timeout)[A-Za-z0-9_-]*[\"']?\s*[:=]\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)", line, re.I)
    if key:
        word = key.group(1).lower()
        comp = ">=" if word in {"min", "gte"} else "<=" if word in {"max", "lte", "tolerance", "radius", "budget", "deadline", "timeout"} else "=="
        found.append((comp, float(key.group(2))))
    if "range" in line.lower():
        values = re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", line)
        if len(values) >= 2:
            found.extend([(">=", float(values[-2])), ("<=", float(values[-1]))])
    dedup = []
    for item in found:
        if item not in dedup and math.isfinite(item[1]): dedup.append(item)
    return dedup


def unit_for(metric: str) -> str:
    if metric in {"point_to_mesh", "one_sided_clearance", "epsilon_map", "false_free_cluster_diameter", "robot_radius", "epsilon_base", "success_tolerance"}: return "m"
    if metric in {"vmax"}: return "m/s"
    if metric in {"umax"}: return "m/s^2"
    if metric in {"dt", "deadline", "runtime"}: return "s"
    if metric in {"coverage", "renderer_acceptance_alpha", "delta1", "delta2", "delta3", "median_depth_ratio", "AbsRel", "SqRel", "SSIM", "LPIPS", "route_retention", "path_stretch"}: return "ratio"
    return "count_or_native_unit"


def scan_thresholds() -> list[dict[str, Any]]:
    files = tracked_files()
    first = first_commit_map()
    allowed = {".md", ".json", ".py", ".yaml", ".yml", ".toml", ".txt", ".sh"}
    rows: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for rel in files:
        if not (rel.startswith("reproduction/") or rel.startswith("REPORTS/")) or (REPO / rel).suffix.lower() not in allowed:
            continue
        p = REPO / rel
        try: text = p.read_text(encoding="utf-8-sig", errors="replace")
        except OSError: continue
        for line_no, line in enumerate(text.splitlines(), 1):
            metric = metric_for_line(line)
            if not metric or not re.search(r"threshold|gate|tolerance|min|max|budget|deadline|timeout|>=|<=|_gte|_lte|_min|_max|range|radius", line, re.I):
                continue
            for comp, value in threshold_candidates(line):
                key = (metric, comp, value, rel)
                if key in seen: continue
                seen.add(key)
                ts, role, defensible, rec = classify_threshold(metric, line)
                task = rel.split("/")[2] if rel.startswith("reproduction/") and len(rel.split("/")) > 2 else rel.split("/")[0]
                rows.append({
                    "row_id": f"T{len(rows)+1:05d}", "metric_name": metric,
                    "formula": metric_formula(metric), "formula_source": formula_source(metric),
                    "threshold": format(value, ".12g"), "units": unit_for(metric), "comparator": comp,
                    "threshold_source": ts, "first_introduced_task": task,
                    "first_commit": first.get(rel.replace("\\", "/"), "UNRESOLVED_FROM_AVAILABLE_HISTORY"),
                    "source_file": rel, "source_line": line_no, "rationale_text": line.strip()[:500],
                    "affected_maps": infer_affected_maps(task), "later_versions": "computed_in_threshold_version_history.json",
                    "changed_without_calibration": ts in {"PROJECT_HEURISTIC", "UNDOCUMENTED_OR_UNRESOLVED"},
                    "decision_role": role, "scientifically_defensible": defensible,
                    "current_recommendation": rec,
                    "failure_implication": failure_implication(metric),
                    "non_implication": non_implication(metric),
                })
    # Canonical legacy entries must be explicit even if older syntax evaded regex.
    canonical = [
        ("renderer_acceptance_alpha", ">=", 0.5, "ratio", "PROJECT_HEURISTIC", "LEGACY_UNCALIBRATED_HARD_GATE"),
        ("coverage", ">=", 0.95, "ratio", "PROJECT_HEURISTIC", "LEGACY_UNCALIBRATED_HARD_GATE"),
        ("AbsRel", "<=", 0.20, "ratio", "PROJECT_HEURISTIC", "LEGACY_UNCALIBRATED_HARD_GATE"),
        ("delta1", ">=", 0.75, "ratio", "PROJECT_HEURISTIC", "LEGACY_UNCALIBRATED_HARD_GATE"),
        ("median_depth_ratio", ">=", 0.80, "ratio", "PROJECT_HEURISTIC", "LEGACY_UNCALIBRATED_HARD_GATE"),
        ("median_depth_ratio", "<=", 1.25, "ratio", "PROJECT_HEURISTIC", "LEGACY_UNCALIBRATED_HARD_GATE"),
    ]
    for metric, comp, value, unit, ts, role in canonical:
        if not any(r["metric_name"] == metric and r["comparator"] == comp and float(r["threshold"]) == value for r in rows):
            rows.append({"row_id": f"T{len(rows)+1:05d}", "metric_name": metric,
                         "formula": metric_formula(metric), "formula_source": formula_source(metric),
                         "threshold": format(value, ".12g"), "units": unit, "comparator": comp,
                         "threshold_source": ts, "first_introduced_task": "historical_cross_dataset_protocols",
                         "first_commit": "UNRESOLVED_FROM_AVAILABLE_HISTORY", "source_file": "multiple_historical_records",
                         "source_line": 0, "rationale_text": "Canonical historical hard gate recovered from repeated protocol records.",
                         "affected_maps": "multiple", "later_versions": "computed_in_threshold_version_history.json",
                         "changed_without_calibration": True, "decision_role": role,
                         "scientifically_defensible": False,
                         "current_recommendation": "downgrade_to_descriptive_or_conditionally_calibrated",
                         "failure_implication": failure_implication(metric), "non_implication": non_implication(metric)})
    rows.sort(key=lambda r: (r["metric_name"].lower(), float(r["threshold"]), r["source_file"], r["source_line"]))
    for i, row in enumerate(rows, 1): row["row_id"] = f"T{i:05d}"
    cols = list(rows[0]) if rows else []
    write_csv("legacy_threshold_ledger/legacy_metric_threshold_ledger.csv", rows, cols)
    dump_json("legacy_threshold_ledger/legacy_metric_threshold_ledger.json", {"rows": rows})
    return rows


def metric_formula(metric: str) -> str:
    formulas = {
        "coverage": "accepted_target_count / target_count",
        "renderer_acceptance_alpha": "accumulated compositing opacity compared with tau_alpha",
        "AbsRel": "mean(|d_pred-d_ref|/d_ref) on accepted target support",
        "SqRel": "mean((d_pred-d_ref)^2/d_ref) on accepted target support",
        "RMSE": "sqrt(mean((d_pred-d_ref)^2)) on accepted target support",
        "RMSE-log": "sqrt(mean((log d_pred-log d_ref)^2)) on accepted target support",
        "delta1": "mean(max(d_pred/d_ref,d_ref/d_pred)<1.25)",
        "delta2": "mean(max ratio<1.25^2)", "delta3": "mean(max ratio<1.25^3)",
        "median_depth_ratio": "median(d_pred/d_ref) on accepted target support",
        "point_to_mesh": "distance from sampled map geometry to independent reference surface",
        "one_sided_clearance": "e_plus=max(0,d_map-d_ref)",
        "geometry_accuracy": "fraction or distance of prediction supported by reference at tolerance t",
        "geometry_completeness": "fraction of reference supported by prediction at tolerance t",
        "geometry_F_score": "2*accuracy*completeness/(accuracy+completeness)",
        "false_free": "known-free map claim where independent reference is occupied",
        "G0": "static query/interface and numerical compatibility checks; no rollout",
    }
    return formulas.get(metric, "project-recorded scalar or contract field; see source row")


def infer_affected_maps(task: str) -> str:
    low = task.lower()
    labels = []
    for token, label in (("tum", "TUM"), ("replica", "Replica"), ("arkit", "ARKitScenes"), ("safer", "SAFER official")):
        if token in low: labels.append(label)
    return ";".join(labels) if labels else "cross_dataset_or_unspecified"


def failure_implication(metric: str) -> str:
    if metric == "nonfinite_count": return "integrity failure when nonfinite values enter required outputs"
    if metric in {"coverage", "renderer_acceptance_alpha"}: return "support is missing or rejected under one renderer working point"
    if metric in {"AbsRel", "delta1", "median_depth_ratio", "RMSE", "SqRel"}: return "conditional depth geometry is weak under the stated support and aggregation"
    if metric in {"false_free", "one_sided_clearance"}: return "potentially dangerous obstacle-distance overestimation in the evaluated domain"
    if metric == "G0": return "query/interface qualification failed under the frozen static probe"
    return "the named diagnostic or contract condition failed in its stated domain"


def non_implication(metric: str) -> str:
    if metric in {"coverage", "renderer_acceptance_alpha", "AbsRel", "delta1", "median_depth_ratio", "RMSE", "SqRel", "PSNR", "SSIM", "LPIPS"}:
        return "does not alone prove or disprove route-conditioned navigation safety"
    if metric == "G0": return "a pass does not prove collision-free navigation; a fail may be interface rather than geometry"
    return "does not establish universal cross-dataset navigation usability without authority, domain, and physical contract"


def build_threshold_history(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows: groups[row["metric_name"]].append(row)
    history = []
    conflicts = []
    for metric, items in sorted(groups.items()):
        variants = sorted({(r["comparator"], r["threshold"], r["units"]) for r in items})
        record = {"metric_name": metric, "variant_count": len(variants),
                  "variants": [{"comparator": c, "threshold": t, "units": u} for c, t, u in variants],
                  "source_row_ids": [r["row_id"] for r in items]}
        history.append(record)
        if len(variants) > 1:
            conflicts.append({**record, "conflict_type": "MULTIPLE_NUMERIC_OR_COMPARATOR_VARIANTS",
                              "resolution": "retain provenance and applicability; no universal gate inferred"})
    undocumented = [r for r in rows if r["threshold_source"] == "UNDOCUMENTED_OR_UNRESOLVED"]
    dump_json("legacy_threshold_ledger/threshold_version_history.json", {"metrics": history})
    dump_json("legacy_threshold_ledger/threshold_conflict_registry.json", {"conflicts": conflicts})
    dump_json("legacy_threshold_ledger/undocumented_threshold_registry.json", {"rows": undocumented})
    return {"versioned_metric_count": sum(x["variant_count"] > 1 for x in history),
            "conflict_count": len(conflicts), "undocumented_count": len(undocumented)}


def primary_sources() -> list[dict[str, Any]]:
    src = [
        ("3DGS", "3D Gaussian Splatting", "https://arxiv.org/abs/2308.04079", "paper", "Gaussian parameters and alpha compositing", False, False),
        ("Gaussian-SLAM", "Gaussian-SLAM", "https://arxiv.org/abs/2312.10070", "paper", "frontend and reported reconstruction metrics", False, False),
        ("Splatfacto", "Nerfstudio Splatfacto", "https://docs.nerf.studio/nerfology/methods/splat.html", "official_docs", "implementation semantics and defaults", False, False),
        ("NerfstudioDepth", "Nerfstudio depth conventions", "https://docs.nerf.studio/quickstart/data_conventions.html", "official_docs", "depth and camera conventions", False, False),
        ("SplaTAMCode", "SplaTAM official repository", "https://github.com/spla-tam/SplaTAM", "official_code", "native mapping and renderer semantics", False, False),
        ("SplaTAMPaper", "SplaTAM", "https://arxiv.org/abs/2312.02126", "paper", "mapping and evaluation metrics", False, False),
        ("TUMTools", "TUM RGB-D evaluation tools", "https://cvg.cit.tum.de/data/datasets/rgbd-dataset/tools", "dataset_official", "ATE and RPE trajectory metrics", False, False),
        ("TUMDataset", "TUM RGB-D dataset", "https://cvg.cit.tum.de/data/datasets/rgbd-dataset", "dataset_official", "RGB-D units, associations, and trajectory authority", False, False),
        ("ReplicaPaper", "Replica", "https://arxiv.org/abs/1906.05797", "paper", "photorealistic indoor dataset and geometry", False, False),
        ("ReplicaRepo", "Replica Dataset", "https://github.com/facebookresearch/Replica-Dataset", "dataset_official", "asset distribution and dense mesh authority", False, False),
        ("ARKitData", "ARKitScenes DATA", "https://github.com/apple/ARKitScenes/blob/main/DATA.md", "dataset_official", "depth uint16 millimetres, confidence 0..2, trajectory metres", False, False),
        ("ARKitPaper", "ARKitScenes", "https://arxiv.org/abs/2111.08897", "paper", "dataset capture and benchmark scope", False, False),
        ("ETH3D", "ETH3D high-resolution multi-view benchmark", "https://eth3d.ethz.ch/high_res_multi_view?metric=f1-score&set=test&sortby=g1&tolerance_id=2", "benchmark_official", "accuracy, completeness, F1 and tolerance reporting", False, False),
        ("SAFER", "SAFER-Splat", "https://arxiv.org/abs/2409.09868", "paper", "Gaussian ellipsoid safety query and control formulation", False, True),
        ("SplatNav", "Splat-Nav", "https://arxiv.org/abs/2403.02751", "paper", "Gaussian-map navigation pipeline", False, True),
        ("OctoMap", "OctoMap official documentation", "https://octomap.github.io/octomap/doc/index", "official_docs", "occupied, free, and unknown occupancy semantics", False, True),
        ("Selective", "Selective Classification for Deep Neural Networks", "https://arxiv.org/abs/1705.08500", "paper", "risk-coverage analysis", False, False),
        ("SelectiveNet", "SelectiveNet", "https://arxiv.org/abs/1901.09192", "paper", "coverage-risk trade-off", False, False),
        ("SampledCBF", "Control Barrier Functions for Sampled-Data Systems", "https://arxiv.org/abs/2103.03677", "paper", "sampled-data safety margins", False, True),
        ("HoldCBF", "Sample-and-hold safety with CBFs", "https://arxiv.org/abs/2304.08685", "paper", "inter-sample safety", False, True),
    ]
    rows = []
    for sid, title, url, kind, scope, universal, nav in src:
        rows.append({"source_id": sid, "title": title, "url": url, "authority_type": kind,
                     "audited_scope": scope, "metric_formula_or_semantics": scope,
                     "official_reporting_method": "source-specific; no experimental mean promoted to a gate",
                     "universal_pass_fail_threshold_provided": universal,
                     "direct_navigation_safety_relevance": nav,
                     "claim_boundary": "No source establishes alpha=0.5, global coverage=0.95, AbsRel=0.20, or delta1=0.75 as a universal navigation-safety gate."})
    dump_json("reference_authority/primary_source_registry.json", {"sources": rows, "source_count": len(rows), "secondary_sources_used": 0})
    return rows


def write_primary_source_docs(sources: list[dict[str, Any]]) -> None:
    lines = ["# Metric Formula Provenance", "", "Metric definitions and decision thresholds are separate provenance objects.", "",
             "| Source | Formula or semantic contribution | Universal pass gate? |", "|---|---|---|"]
    for s in sources:
        lines.append(f"| [{s['title']}]({s['url']}) | {s['metric_formula_or_semantics']} | {'yes' if s['universal_pass_fail_threshold_provided'] else 'no'} |")
    lines += ["", "## Audit conclusion", "", "Standard formulas do not make project-selected numeric cutoffs universal. Dataset units and confidence labels define input semantics; they do not certify navigation. The physically relevant bridge is an explicit robot/route/reference error budget, not a global image metric."]
    (ROOT / "reference_authority/metric_formula_provenance.md").write_text("\n".join(lines)+"\n", encoding="utf-8", newline="\n")
    (ROOT / "reference_authority/literature_threshold_claim_audit.md").write_text(
        "# Literature Threshold Claim Audit\n\n"
        "The audited primary sources define algorithms, units, metrics, benchmark reporting points, occupancy semantics, or sampled-data safety conditions. None supplies a universal navigation hard gate at `tau_alpha=0.5`, global coverage `0.95`, AbsRel `0.20`, delta1 `0.75`, median ratio `[0.80,1.25]`, or the historical project clearance percentiles. Experimental means and benchmark tolerances are not promoted into qualification cutoffs.\n\n"
        "Opacity in Gaussian compositing is neither a calibrated occupancy probability nor a calibrated probability of correct depth. TUM's official evaluation is trajectory-focused. ETH3D tolerances are reporting coordinates. Replica and ARKitScenes provide reference semantics, not project-independent navigation thresholds. Occupancy mapping keeps UNKNOWN distinct from FREE. Selective-prediction literature motivates full risk-coverage characterization. Sampled-data CBF work requires explicit inter-sample and uncertainty allowances.\n",
        encoding="utf-8", newline="\n")


def metric_semantics() -> list[dict[str, Any]]:
    metrics = [
        ("coverage", "accepted reference support", "correctness and free-space truth", True, True, True, False, False, False, True, False, False),
        ("renderer_acceptance_alpha", "renderer support at a working point", "calibrated occupancy/correctness probability", False, False, False, False, False, False, True, False, False),
        ("AbsRel", "relative accepted-pixel depth error", "missing geometry and route clearance", True, True, True, False, False, False, False, False, False),
        ("delta1", "fraction of accepted depth ratios within 1.25", "spatial continuity and safety margin", True, True, True, False, False, False, False, False, False),
        ("median_depth_ratio", "central multiplicative depth bias", "tails, gaps, and local false-free errors", True, True, True, False, False, False, False, False, False),
        ("PSNR_SSIM_LPIPS", "appearance fidelity", "metric obstacle clearance", True, True, True, False, False, False, False, False, False),
        ("point_to_mesh", "surface proximity under chosen direction", "free-space overestimation unless one-sided", False, False, False, True, True, True, False, False, False),
        ("accuracy_completeness_F", "multi-tolerance bidirectional surface support", "robot-conditioned risk", False, False, False, True, True, True, False, False, False),
        ("one_sided_clearance", "dangerous distance overestimation", "unobserved space outside reference domain", False, False, False, True, True, True, False, True, False),
        ("false_free", "map-free claim conflicting with obstacle reference", "safety outside sampled/query domain", False, False, False, True, True, True, True, True, False),
        ("G0", "static query and numerical compatibility", "closed-loop navigation", False, False, False, False, False, False, False, True, True),
        ("route_success_progress", "outcome under one frozen route/controller", "global reconstruction quality", False, False, False, True, True, True, True, True, True),
    ]
    rows=[]
    for m, measures, notm, dep, pixel, dominated, asym, thin, wall, unk, robot, rend in metrics:
        rows.append({"metric_name":m,"measures":measures,"does_not_measure":notm,"depends_on_coverage_mask":dep,
                     "depth_weighting_or_support_sensitive":dep,"pixel_weighted":pixel,"may_be_dominated_by_large_frames_groups":dominated,
                     "distinguishes_dangerous_overestimate":asym,"can_detect_thin_obstacle":thin,"can_detect_contiguous_missing_wall":wall,
                     "can_identify_unknown":unk,"robot_geometry_linked":robot,"renderer_semantics_dependent":rend,
                     "single_failure_implies_not_navigable":False,"single_pass_implies_safe":False,
                     "cross_dataset_comparable":"ONLY_WITH_MATCHED_FORMULA_SUPPORT_REFERENCE_AND_AGGREGATION"})
    write_csv("metric_semantic_scope_matrix.csv", rows, list(rows[0]))
    implication=[{"metric_name":r["metric_name"],"failure_can_imply":failure_implication(r["metric_name"]),
                  "failure_cannot_imply":non_implication(r["metric_name"]),
                  "pass_cannot_imply":"collision-free or physically certified navigation by itself"} for r in rows]
    write_csv("metric_failure_implication_matrix.csv", implication, list(implication[0]))
    (ROOT / "metric_cross_dataset_comparability.md").write_text(
        "# Metric Cross-Dataset Comparability\n\n"
        "A numeric metric is comparable across datasets only when formula, depth convention, target mask, renderer acceptance semantics, aggregation unit, reference authority, spatial domain, and scale are matched. Historical TUM, Replica, and ARKitScenes summaries do not satisfy all of these conditions jointly. Therefore their values are evidence profiles, not a pooled leaderboard or a basis for a universal cutoff. Native/common renderer parity is a separate required record; absence of parity is not permission to select the favorable channel.\n",
        encoding="utf-8", newline="\n")
    return rows


def repo_json(rel: str) -> dict[str, Any]:
    p = REPO / rel
    return load_json(p) if p.is_file() else {}


def historical_metrics() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    a = repo_json("reproduction/cross_dataset/arkitscenes_splatam_m1_learned_map_qualification_v1/evaluation/heldout_evaluation.json")
    if a:
        m=a["primary_confidence_ge1"]
        result["ARKITSCENES_M1_SPLATAM"]={"coverage":m["coverage"],"absrel":m["absrel"],"delta1":m["delta1"],"ratio":m["median_pred_gt_ratio"],"nonfinite":m["nonfinite_count"],"per_frame":a.get("per_frame",[]),"alpha":0.5}
    s = repo_json("reproduction/cross_dataset/replica_splatam_protocol_conformance_pilot_v1/splatam_60_frame_geometry_evaluation.json")
    if s:
        m=s["metrics"]
        result["REPLICA_SPLATAM_60"]={"coverage":m["valid_predicted_depth_fraction"],"absrel":m["absrel"],"delta1":m["delta1"],"ratio":m["median_depth_ratio"],"nonfinite":m["nonfinite_prediction_count"],"per_frame":s.get("per_frame",[]),"alpha":0.5}
    f = repo_json("reproduction/cross_dataset/replica_splatfacto_native_baseline_qualification_v1/splatfacto_pilot_geometry_evaluation.json")
    if f:
        m=f["metrics"]
        result["REPLICA_SPLATFACTO"]={"coverage":m["valid_predicted_depth_fraction"],"absrel":m["absrel"],"delta1":m["delta1"],"ratio":m["median_depth_ratio"],"nonfinite":m.get("nonfinite_prediction_count",0),"per_frame":f.get("per_frame",[]),"alpha":0.5}
    return result


def map_inventory() -> list[dict[str, Any]]:
    maps = [
      dict(map_id="REPLICA_GT_FINE",dataset="Replica",scene="apartment_0",learned=False,frontend="GT-derived voxel Gaussian",split="reference-derived",source_commit="PR64 lineage",params_sha=None,canonical_tree_sha="3b318a98a454ec5c36410b3c41dfb3dd4a25b7b5a1899f1f2c939fbf24ad0e55",map_role="CERTIFIED_GT_GEOMETRY_DERIVED_GAUSSIAN_SAFETY_MAP",reference_geometry="official dense mesh",renderer="SAFER canonical Gaussian query",native=True,common=True,route=True,server_path="/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1",legacy="PASS frozen bounded static qualification",failed_gate=None,possibly_misclassified=False,evaluable="identity, static query, mesh/route contracts; no new controller"),
      dict(map_id="TUM_SPLATFACTO_NEGATIVE",dataset="TUM RGB-D",scene="freiburg1_room",learned=True,frontend="Splatfacto",split="historical fixed",source_commit="PR33 lineage",params_sha=None,canonical_tree_sha=None,map_role="NEGATIVE_GEOMETRY_CONTROL",reference_geometry="held-out RGB-D only",renderer="Nerfstudio/common historical",native=True,common=True,route=False,server_path="/disk1/zlab/maintenance_records/tum_splatfacto_v1r6_checkpoint_audit_v1",legacy="geometry failed; no navigation qualification",failed_gate="depth geometry and map drift",possibly_misclassified=False,evaluable="retained summaries only where artifact identity resolves"),
      dict(map_id="REPLICA_SPLATFACTO",dataset="Replica",scene="apartment_0",learned=True,frontend="Splatfacto",split="60/30 equivalent pilot",source_commit="PR57 lineage",params_sha=None,canonical_tree_sha=None,map_role="NEGATIVE_GEOMETRY_CONTROL",reference_geometry="Replica V3 held-out depth and mesh",renderer="common Gaussian evaluator",native=True,common=True,route=False,server_path="/disk1/zlab/maintenance_records/replica_splatfacto_native_baseline_qualification_v1",legacy="negative geometry baseline",failed_gate="AbsRel/delta1/ratio",possibly_misclassified=False,evaluable="single retained working point and per-frame spatial diagnostics"),
      dict(map_id="TUM_SPLATAM_FORMAL",dataset="TUM RGB-D",scene="freiburg1_room",learned=True,frontend="SplaTAM",split="formal map-only",source_commit="PR44/47 lineage",params_sha=None,canonical_tree_sha=None,map_role="AUDIT_CANDIDATE",reference_geometry="RGB-D/trajectory; route oracle incomplete",renderer="SplaTAM native plus common adapter",native=True,common=True,route=False,server_path="/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/build/runs/splatam_full240/params.npz",legacy="static-qualified map; navigation progress limitation",failed_gate="navigation protocol/progress, not solely geometry",possibly_misclassified=True,evaluable="identity, retained geometry, query compatibility; navigation N0/N1"),
      dict(map_id="TUM_GAUSSIAN_SLAM",dataset="TUM RGB-D",scene="freiburg1_room",learned=True,frontend="Gaussian-SLAM",split="historical formal",source_commit="PR40 lineage",params_sha=None,canonical_tree_sha=None,map_role="AUDIT_CANDIDATE",reference_geometry="RGB-D/trajectory; route oracle incomplete",renderer="native-concat/common canonical adapter",native=True,common=True,route=False,server_path="/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/gaussian_slam/canonical_export/export_a",legacy="adapter/query compatible; no route qualification",failed_gate="independent route/reference evidence unresolved",possibly_misclassified=True,evaluable="canonical/query evidence, no formal navigation"),
      dict(map_id="REPLICA_SPLATAM_60",dataset="Replica",scene="apartment_0",learned=True,frontend="SplaTAM",split="60 map / 30 held-out",source_commit="PR58 lineage",params_sha=None,canonical_tree_sha=None,map_role="AUDIT_CANDIDATE",reference_geometry="Replica V3 held-out depth and dense mesh",renderer="common Gaussian evaluator",native=True,common=True,route=False,server_path="/disk1/zlab/maintenance_records/replica_splatam_protocol_conformance_pilot_v1/pilot_run/run/params.npz",legacy="failed frozen delta1 0.75 by 0.00603",failed_gate="delta1 only",possibly_misclassified=True,evaluable="single retained working point and per-frame spatial diagnostics; route absent"),
      dict(map_id="ARKITSCENES_M1_SPLATAM",dataset="ARKitScenes",scene="48018874",learned=True,frontend="SplaTAM M1",split="214 train / 53 held-out spatial groups",source_commit="26695aed7dec199c40ef7977e1885fdc2d2ecca1",params_sha="86ba75c9db0fab1a5eb7d65da82454514419a30d7bea6df68b2bbc0518000193",canonical_tree_sha="e1326f0ac5519fa1c743b9bde448a5584bc3062e61e3dccedac870fadbe977c7",map_role="AUDIT_CANDIDATE",reference_geometry="held-out LiDAR depth/confidence plus official mesh",renderer="SplaTAM alpha-composited camera-z depth",native=True,common=False,route=False,server_path="/disk1/zlab/maintenance_records/arkitscenes_splatam_m1_learned_map_qualification_v1/outputs/ARKITSCENES_SPLATAM_M1_EMPTY_DEPTH_SAFE_GT_POSE_MAP_ONLY_V1/params.npz",legacy=LEGACY_STATUS,failed_gate="global coverage 0.95 only",possibly_misclassified=True,evaluable="single retained alpha=0.5 point, per-frame missingness; no legal route"),
    ]
    for scene in ("flight", "old_union2", "statues", "stonehenge"):
        maps.append(dict(map_id=f"SAFER_OFFICIAL_{scene.upper()}",dataset="SAFER official",scene=scene,learned=True,frontend="official 3DGS",split="interface reference",source_commit="official SAFER asset lineage",params_sha=None,canonical_tree_sha=None,map_role="INTERFACE_REFERENCE_ONLY",reference_geometry="no frozen independent geometry authority in this audit",renderer="official SAFER native query",native=True,common=False,route=False,server_path=f"/disk1/zlab/safer-splat/data/{scene}",legacy="native interface example",failed_gate=None,possibly_misclassified=False,evaluable="native interface semantics only; no external geometry calibration"))
    dump_json("map_inventory/historical_map_inventory.json", {"maps": maps, "map_count": len(maps), "auto_parse_note":"minimum required candidates reconciled against tracked reports and server paths"})
    return maps


def availability(maps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows=[]
    for m in maps:
        path=m["server_path"]
        p=subprocess.run(["ssh","zlab-4090",f"test -e {path!r}"],cwd=REPO).returncode
        exists=p==0
        rows.append({"map_id":m["map_id"],"server_path":path,"available":exists,
                     "status":"AVAILABLE_FOR_READ_ONLY_RETROSPECTIVE_SCOPE" if exists else "ARTIFACT_UNAVAILABLE_FOR_RETROSPECTIVE_EVALUATION",
                     "retrain_to_recover":False,"identity_expected":m.get("params_sha") or m.get("canonical_tree_sha")})
    dump_json("map_inventory/map_artifact_availability.json", {"observed_utc":utc_now(),"maps":rows})
    return rows


def reference_authority(maps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows=[]
    for m in maps:
        ref=m["reference_geometry"]
        if "dense mesh" in ref or "official mesh" in ref: level="A_INDEPENDENT_METRIC_GEOMETRY"
        elif "held-out" in ref or "RGB-D" in ref: level="B_INDEPENDENT_OBSERVABLE_RAYS"
        else: level="C_INTERFACE_OR_UNRESOLVED"
        rows.append({"map_id":m["map_id"],"reference":ref,"authority_level":level,
                     "full_space_claim_allowed":level=="A_INDEPENDENT_METRIC_GEOMETRY",
                     "navigation_claim_allowed":bool(m["route"] and level=="A_INDEPENDENT_METRIC_GEOMETRY")})
    dump_json("reference_authority/reference_authority_registry.json", {"rows":rows})
    return rows


def parity_records(maps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows=[]
    for m in maps:
        if m["native"] and m["common"]:
            status="SEMANTIC_CHANNELS_IDENTIFIED_NO_FRESH_NUMERIC_PARITY" if m["map_id"] not in {"TUM_GAUSSIAN_SLAM","TUM_SPLATAM_FORMAL"} else "HISTORICAL_PARITY_EVIDENCE_AVAILABLE"
        elif m["native"]: status="COMMON_CHANNEL_NOT_AVAILABLE"
        else: status="NATIVE_CHANNEL_NOT_AVAILABLE"
        rows.append({"map_id":m["map_id"],"native_available":m["native"],"common_available":m["common"],"status":status,
                     "favorable_channel_selected":False,"fresh_render_count":0})
    dump_json("common_evaluator/native_common_semantic_parity.json", {"rows":rows})
    return rows


def per_frame_value(row: dict[str, Any], key: str) -> float | None:
    if key in row and isinstance(row[key], (int,float)): return float(row[key])
    primary=row.get("primary")
    if isinstance(primary,dict):
        mapping={"coverage":"coverage","absrel":"absrel","delta1":"delta1","ratio":"median_pred_gt_ratio"}
        v=primary.get(mapping.get(key,key))
        if isinstance(v,(int,float)): return float(v)
    return None


def risk_coverage(metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    maps=[]
    remote_path=ROOT/"risk_coverage/arkitscenes_m1_fixed_alpha_results.json"
    remote=load_json(remote_path) if remote_path.is_file() else None
    for mid,m in sorted(metrics.items()):
        if mid=="ARKITSCENES_M1_SPLATAM" and remote and remote.get("complete_curve") and remote.get("map_unmodified"):
            maps.append({"map_id":mid,"alpha_grid":remote["points"],"complete_curve":True,"AURC":remote.get("AURC"),"AURC_definition":remote.get("AURC_definition"),"single_working_point_is_not_curve":False,"source":"fresh read-only fixed-grid rerender","params_sha256_before":remote.get("params_sha256_before"),"params_sha256_after":remote.get("params_sha256_after")})
            continue
        points=[]
        for alpha in ALPHA_GRID:
            if abs(alpha-m["alpha"])<1e-12:
                points.append({"tau_alpha":alpha,"status":"OBSERVED_RETAINED_WORKING_POINT","global_coverage":m["coverage"],"AbsRel":m["absrel"],"RMSE":None,"SqRel":None,"delta1":m["delta1"],"delta2":None,"delta3":None,"median_ratio":m["ratio"],"nonfinite":m["nonfinite"],"accepted_pixel_count":None,"rejected_unknown_pixel_count":None})
            else:
                points.append({"tau_alpha":alpha,"status":"NOT_EVALUABLE_FROM_RETAINED_SUMMARY","global_coverage":None,"AbsRel":None,"RMSE":None,"SqRel":None,"delta1":None,"delta2":None,"delta3":None,"median_ratio":None,"nonfinite":None,"accepted_pixel_count":None,"rejected_unknown_pixel_count":None})
        frames=m.get("per_frame",[])
        cov=[per_frame_value(x,"coverage") for x in frames]; cov=[x for x in cov if x is not None]
        maps.append({"map_id":mid,"alpha_grid":points,"complete_curve":False,"AURC":None,"AURC_definition":"trapezoid of conditional AbsRel risk over observed coverage range; not computed without complete fixed grid","single_working_point_is_not_curve":True,
                     "per_frame_macro_coverage_at_legacy_point":statistics.fmean(cov) if cov else None,
                     "worst_5_percent_frame_coverage_at_legacy_point":statistics.fmean(sorted(cov)[:max(1,math.ceil(.05*len(cov)))]) if cov else None,
                     "per_group_macro_coverage":"NOT_EVALUABLE_GROUP_LABELS_NOT_RETAINED_WITH_RENDER_SUMMARY"})
    result={"fixed_alpha_grid":ALPHA_GRID,"maps":maps,"complete_curve_map_count":sum(m["complete_curve"] for m in maps),"rule":"no interpolation or favorable map-specific working point"}
    dump_json("risk_coverage/risk_coverage_results.json",result)
    return result


def multi_tolerance(maps: list[dict[str, Any]]) -> dict[str, Any]:
    rows=[]
    for m in maps:
        if m["map_id"]=="REPLICA_GT_FINE":
            status="PARTIAL_EXACT_SUPPORT_CERTIFICATE_NOT_BENCHMARK_SURFACE_CURVE"
            detail="Retained certificate proves every frozen mesh primitive intersects closed voxel support; it does not retain bidirectional surface samples needed for accuracy/completeness/F-score."
        else:
            status="NOT_EVALUABLE_NO_RETAINED_BIDIRECTIONAL_DISTANCE_SAMPLES"
            detail="No retained distance arrays at all frozen reporting tolerances; no rerendered geometry or map mutation was authorized."
        rows.append({"map_id":m["map_id"],"tolerances_m":[{"t":t,"accuracy":None,"completeness":None,"F_score":None} for t in TOLERANCE_GRID_M],"status":status,"detail":detail,"reporting_points_are_not_gates":True})
    result={"fixed_tolerances_m":TOLERANCE_GRID_M,"maps":rows,"complete_map_count":0}
    dump_json("multi_tolerance/multi_tolerance_geometry_results.json",result)
    return result


def spatial_missingness(metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows=[]
    for mid,m in sorted(metrics.items()):
        frames=m.get("per_frame",[])
        cov=[per_frame_value(x,"coverage") for x in frames]; cov=[x for x in cov if x is not None]
        if cov:
            sorted_cov=sorted(cov)
            components=sum(x<0.95 for x in cov)
            rows.append({"map_id":mid,"status":"FRAME_LEVEL_OBSERVABLE_MISSINGNESS_ONLY","frame_count":len(cov),"global_missing_fraction":1-m["coverage"],"macro_frame_missing_fraction":1-statistics.fmean(cov),"worst_frame_missing_fraction":1-min(cov),"worst_5pct_frame_missing_fraction":1-statistics.fmean(sorted_cov[:max(1,math.ceil(.05*len(cov)))]),"frames_below_legacy_coverage_0_95":components,"contiguous_2d_components":"NOT_EVALUABLE_NO_RETAINED_BINARY_MASKS","3d_clusters":"NOT_EVALUABLE_NO_RETAINED_BACKPROJECTED_UNKNOWN_POINTS","border_vs_interior":"NOT_EVALUABLE","range_bins":"NOT_EVALUABLE","robot_height_band":"NOT_EVALUABLE"})
        else:
            rows.append({"map_id":mid,"status":"NOT_EVALUABLE_NO_PER_FRAME_SUPPORT_SUMMARY"})
    result={"maps":rows,"claim_boundary":"Held-out rays characterize only the observable camera domain; no full-space occupancy claim."}
    dump_json("spatial_missingness/spatial_missingness_results.json",result)
    return result


def unknown_semantics(metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows=[]
    for mid,m in sorted(metrics.items()):
        missing=1-m["coverage"]
        rows.append({"map_id":mid,"unknown_fraction_at_retained_working_point":missing,
                     "policies":{"UNKNOWN_AS_FREE":"FORBIDDEN_DANGEROUS","UNKNOWN_AS_OCCUPIED":"CONSERVATIVE_BUT_MAY_BLOCK_PROGRESS","UNKNOWN_AS_HIGH_COST":"DIAGNOSTIC_ONLY_REQUIRES_FROZEN_COST_AND_PLANNER_CONTRACT"},
                     "cluster_or_route_intersection":"NOT_EVALUABLE_NO_RETAINED_MASK_ROUTE_JOIN","selected_policy":"NONE_THIS_TASK"})
    result={"maps":rows,"rule":"UNKNOWN is never free and carries an explicit cost or exclusion semantics in future evaluation."}
    dump_json("spatial_missingness/unknown_semantics_results.json",result)
    return result


def navigation_conditioned(maps: list[dict[str, Any]], refs: list[dict[str, Any]]) -> dict[str, Any]:
    ref={x["map_id"]:x for x in refs}
    rows=[]
    for m in maps:
        required={"independent_reference":ref[m["map_id"]]["authority_level"]=="A_INDEPENDENT_METRIC_GEOMETRY","robot_contract":m["map_id"]=="REPLICA_GT_FINE","legal_route_registry":m["route"]}
        evaluable=all(required.values())
        rows.append({"map_id":m["map_id"],"requirements":required,"navigation_conditioned_evaluable":evaluable,
                     "status":"HISTORICAL_POSITIVE_CONTROL_CONTRACT_AVAILABLE_NO_NEW_ROLLOUT" if evaluable else "N0_NOT_EVALUABLE",
                     "route_tube":"existing frozen route/swept-body contract" if evaluable else "NOT_DEFINED",
                     "global_metric_used_as_navigation_gate":False,"controller_executed":False})
    result={"maps":rows,"evaluated_map_count":sum(x["navigation_conditioned_evaluable"] for x in rows),"new_navigation_conclusion_count":0}
    dump_json("navigation_conditioned/navigation_conditioned_results.json",result)
    return result


def physical_budgets(maps: list[dict[str, Any]]) -> dict[str, Any]:
    rows=[]
    eps=["epsilon_loc","epsilon_shape","epsilon_sampled","epsilon_stop","epsilon_tracking"]
    for m in maps:
        if m["map_id"]=="REPLICA_GT_FINE":
            status="HISTORICAL_CONTRACT_PRESENT_REQUIRES_RETROSPECTIVE_V2_BOUND_RECHECK"
            missing=[]
        else:
            status="PHYSICAL_ERROR_BUDGET_UNRESOLVED"
            missing=eps
        rows.append({"map_id":m["map_id"],"e_plus_formula":"max(0,d_map-d_ref)","m_ref_formula":"d_ref-r_robot","B_map_available_formula":"m_ref-epsilon_loc-epsilon_shape-epsilon_sampled-epsilon_stop-epsilon_tracking","missing_allowance_sources":missing,"status":status,"upper_bound_kind":"UNRESOLVED" if missing else "historical deterministic frozen-sample evidence; not re-certified here","empirical_p99_is_certificate":False})
    result={"maps":rows,"resolved_count":sum(not x["missing_allowance_sources"] for x in rows),"unresolved_count":sum(bool(x["missing_allowance_sources"]) for x in rows)}
    dump_json("physical_derivation/physical_map_error_budget.json",result)
    return result


def evidence_profiles(maps: list[dict[str, Any]], availability_rows: list[dict[str, Any]]) -> dict[str, Any]:
    av={x["map_id"]:x["available"] for x in availability_rows}
    profiles=[]
    fixed={
      "REPLICA_GT_FINE":("R2_GLOBAL_RECONSTRUCTION_CANDIDATE","N3_LIMITED_DOMAIN_NAVIGATION_QUALIFIED",True,"positive control; historical certification preserved, not newly granted"),
      "TUM_SPLATFACTO_NEGATIVE":("R1_DIAGNOSTIC_RECONSTRUCTION","N0_NOT_EVALUABLE",True,"negative geometry control"),
      "REPLICA_SPLATFACTO":("R1_DIAGNOSTIC_RECONSTRUCTION","N0_NOT_EVALUABLE",True,"negative geometry control"),
      "TUM_SPLATAM_FORMAL":("R1_DIAGNOSTIC_RECONSTRUCTION","N1_NAVIGATION_DIAGNOSTIC_ONLY",True,"geometry and progress limitation must remain separate"),
      "TUM_GAUSSIAN_SLAM":("R1_DIAGNOSTIC_RECONSTRUCTION","N1_NAVIGATION_DIAGNOSTIC_ONLY",True,"adapter/query evidence; physical route budget absent"),
      "REPLICA_SPLATAM_60":("R1_DIAGNOSTIC_RECONSTRUCTION","N0_NOT_EVALUABLE",True,"LEGACY_SINGLE_THRESHOLD_BORDERLINE; no route registry"),
      "ARKITSCENES_M1_SPLATAM":("R1_DIAGNOSTIC_RECONSTRUCTION","N0_NOT_EVALUABLE",False,"legacy coverage-only failure; spatial unknown and route evidence unresolved"),
    }
    for m in maps:
        r,n,q,note=fixed.get(m["map_id"],("R1_DIAGNOSTIC_RECONSTRUCTION","N0_NOT_EVALUABLE",True,"interface reference only"))
        if not av.get(m["map_id"],False): r="R1_DIAGNOSTIC_RECONSTRUCTION" if m["map_id"].startswith("SAFER") else r
        profiles.append({"map_id":m["map_id"],"reconstruction_axis":r,"navigation_axis":n,"SAFETY_QUERY_COMPATIBLE":q,"provisional_only":True,"new_pass_granted":False,"note":note})
    result={"profiles":profiles,"calibration":{"positive_controls":["REPLICA_GT_FINE"],"negative_controls":["TUM_SPLATFACTO_NEGATIVE","REPLICA_SPLATFACTO"],"audit_candidates":["TUM_SPLATAM_FORMAL","TUM_GAUSSIAN_SLAM","REPLICA_SPLATAM_60","ARKITSCENES_M1_SPLATAM"],"candidate_used_to_fit_gate":False,"leave_one_map_out":"NOT_JUSTIFIED_TOO_FEW_INDEPENDENT_CONTROLS","leave_one_dataset_out":"NOT_JUSTIFIED_TOO_FEW_INDEPENDENT_CONTROLS","global_numeric_gate_decision":GLOBAL_DECISION}}
    dump_json("calibration/provisional_evidence_profiles.json",result)
    dump_json("calibration/calibration_sensitivity.json",result["calibration"])
    return result


def write_protocols() -> None:
    (ROOT / "protocol_v2").mkdir(parents=True, exist_ok=True)
    (ROOT / "protocol_v2/GAUSSIAN_MAP_LAYERED_EVALUATION_PROTOCOL_V2.md").write_text(PROTOCOL_V2,encoding="utf-8",newline="\n")
    (ROOT / "protocol_v2/NEW_DATASET_MAP_EVALUATION_ENTRY_CHECKLIST_V2.md").write_text(CHECKLIST,encoding="utf-8",newline="\n")
    (ROOT / "protocol_v2/RETROSPECTIVE_REQUALIFICATION_HANDOFF_V2.md").write_text(HANDOFF,encoding="utf-8",newline="\n")


PROTOCOL_V2 = """# Gaussian Map Layered Evaluation Protocol V2

## 1. Scope and terminology

This protocol evaluates immutable Gaussian-map instances for three separate claims: global reconstruction evidence, limited-domain navigation evidence, and safety-query compatibility. A renderer's accepted set is `K_tau`; its complement is UNKNOWN, not FREE.

## 2. Provenance requirements

Every formula records one allowed formula-source enum. Every numerical decision point records one allowed threshold-source enum, applicability domain, first task/commit, rationale, decision role, failure implication, and non-implication. `PROJECT_HEURISTIC` and `UNDOCUMENTED_OR_UNRESOLVED` cannot be universal navigation gates.

## 3. Integrity hard gates

Identity, TRAIN/HELDOUT non-leakage, metric units/pose/intrinsics, finite required outputs, deterministic canonical export, query immutability, exact numerical engine qualification, independent-oracle identity, and absence of unauthorized post-processing are hard gates. Integrity failure yields `R0_INVALID` and stops qualification, but diagnostic evidence required for attribution may still be produced read-only.

## 4. Descriptive reconstruction evaluation

Report native and common semantics without favorable selection. At the fixed alpha grid `{0.05,0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.90,0.95}`, report global/frame/group/worst-5% coverage and accepted-support AbsRel, RMSE, SqRel, delta1/2/3, median ratio, nonfinite, accepted and rejected counts. AURC is trapezoidal conditional risk over the observed coverage interval and is descriptive only. Missing grid evidence is `NOT_EVALUABLE`, never interpolated.

Where independent metric geometry and immutable samples exist, report accuracy, completeness, F-score, boundary recall, false-positive rate, and thin-structure recall at `{0.01,0.02,0.03,0.05,0.10,0.20}` metres. These are reporting coordinates, not pass cutoffs. Aggregate globally, frame macro, group macro, worst 5%, worst spatial component, range, border, and robot-height band when supported.

## 5. Missing geometry and unknown policy

Measure connected 2D missing components, back-projected 3D clustering, persistence, range/border/robot-height distributions, and route-tube intersection only when the retained evidence supports them. Held-out rays certify only their observable domain. UNKNOWN must be excluded or assigned an explicitly frozen conservative/high-cost policy; it is never silently free.

## 6. One-sided safety risk and physical budget

Use `e_plus=max(0,d_map-d_ref)`. For a frozen robot and route, `m_ref=d_ref-r_robot` and `B_map_available=m_ref-epsilon_loc-epsilon_shape-epsilon_sampled-epsilon_stop-epsilon_tracking`. A necessary route condition is `UpperBound[e_plus | swept route tube] <= B_map_available`. Label the bound as exact, deterministic frozen-sample maximum, bootstrap UCB, conformal, or empirical percentile. A p99 is never called a certificate. Any missing allowance source yields `PHYSICAL_ERROR_BUDGET_UNRESOLVED`.

## 7. Physical navigation hard gates

UNKNOWN is not FREE; the reference swept body has no obstacle collision; the route-tube overestimation upper bound is within the physical budget; velocity/actuation/dynamics contracts hold; and an independent collision predicate passes. Global coverage, alpha, AbsRel, delta1, ratio, PSNR, SSIM, LPIPS, Gaussian count, single runtime and AURC cannot alone be universal navigation gates.

## 8. Two-axis classification

Reconstruction: `R0_INVALID`, `R1_DIAGNOSTIC_RECONSTRUCTION`, `R2_GLOBAL_RECONSTRUCTION_CANDIDATE`, `R3_GLOBAL_DENSE_RECONSTRUCTION_QUALIFIED`. R3 requires independent multi-scene or benchmark calibration.

Navigation: `N0_NOT_EVALUABLE`, `N1_NAVIGATION_DIAGNOSTIC_ONLY`, `N2_LIMITED_DOMAIN_UNKNOWN_AWARE_NAVIGATION_CANDIDATE`, `N3_LIMITED_DOMAIN_NAVIGATION_QUALIFIED`. N3 requires complete route-tube, physical-budget and independent-oracle evidence. `SAFETY_QUERY_COMPATIBLE` is recorded separately.

## 9. Reference authority and uncertainty

Authority A is independent metric geometry; B is independent observable rays; C is interface or unresolved evidence. Full-space claims require A. Formal method claims freeze seed count before training. Single seed supports only the map instance. Confidence intervals cluster by frame, group, route or map—not pixels—and report spatial autocorrelation, worst components, map variance and domain shift.

## 10. Artifact, early-stop and claims

Freeze map/checkpoint/canonical SHA, source commit, renderer, reference and route identities before evaluation and verify immutability after. Early-stop may close formal PASS but must not suppress read-only attribution diagnostics. Never repair scale, ICP/Sim3-align, filter opacity, delete frames or choose a favorable threshold/channel without a separate preregistered task. Preserve every legacy result verbatim and label V2 outputs provisional until the retrospective requalification task.

## 11. Requalification and new-dataset entry

Run controls before candidates. Candidates cannot fit their own gate. If control evidence is insufficient, record `NO_UNIVERSAL_NUMERIC_GATE_JUSTIFIED_BY_CURRENT_EVIDENCE`. Requalification produces two axes and bounded claims, not a rewritten historical PR. A new dataset must pass the separate entry checklist before formal training.
"""

CHECKLIST = """# New Dataset Map Evaluation Entry Checklist V2

Before formal training, freeze and validate:

- [ ] independent reference authority and its exact identity;
- [ ] depth, pose, intrinsics, image, frame and metric-unit semantics;
- [ ] TRAIN/HELDOUT split and spatial-leakage proof;
- [ ] native and common renderer/query semantics and parity plan;
- [ ] alpha/coverage definitions and complete fixed-grid diagnostic plan;
- [ ] UNKNOWN policy that never treats rejection as free by default;
- [ ] robot body, localization, model, sampled-data, stopping and tracking contracts;
- [ ] legal reference route and swept-tube construction, if navigation is claimed;
- [ ] formula primary sources and every threshold source/decision role;
- [ ] one-sided physical map-error budget and bound type;
- [ ] seed count and cluster-bootstrap unit frozen before training;
- [ ] diagnostic-after-failure plan;
- [ ] immutable artifact/publication policy and exact downstream claim;
- [ ] resource limits separated from scientific qualification;
- [ ] no candidate-dependent threshold selection.

An unchecked item blocks formal training for the associated claim. It does not authorize data repair, training, controller execution, or threshold relaxation.
"""

HANDOFF = """# Retrospective Requalification Handoff V2

## Only authorized next task

`RETROSPECTIVE_REQUALIFY_EXISTING_GAUSSIAN_MAPS_UNDER_LAYERED_PROTOCOL_V2`

Use the immutable inventory, source ledger, fixed alpha/tolerance grids, reference-authority registry and two-axis rules from this task. Start with Replica GT-FINE positive control and the two negative controls. Then evaluate TUM SplaTAM, TUM Gaussian-SLAM, Replica SplaTAM and ARKitScenes M1 without retraining or selecting candidate-favourable cutoffs.

For each map, freeze identities, assess native/common parity, run only evidence-supported diagnostics, preserve UNKNOWN, and derive route-conditioned budgets only when independent reference, robot contract and legal route all exist. Missing evidence becomes `NOT_EVALUABLE`. Do not rewrite PRs #68-#74. ETH3D remains paused until its entry checklist is complete.
"""


def manifest(summary: dict[str, Any], rows: list[dict[str, Any]], hist: dict[str, Any], sources: list[dict[str, Any]], maps: list[dict[str, Any]], avail: list[dict[str, Any]], risk: dict[str, Any], multi: dict[str, Any], nav: dict[str, Any], budgets: dict[str, Any]) -> dict[str, Any]:
    m={"schema":"gaussian-map-metric-provenance-audit/run-manifest/v1","generated_utc":utc_now(),"branch":summary["branch"],"head_at_start":summary["git_head"],"frozen_upstream_pr":74,"frozen_upstream_head":"26695aed7dec199c40ef7977e1885fdc2d2ecca1","legacy_status":LEGACY_STATUS,"legacy_interpretation":LEGACY_INTERPRETATION,"navigation_usability":"NOT_YET_DETERMINED_UNDER_PROTOCOL_V2","counts":{"scanned_files":summary["reproduction_file_count"],"scanned_commits":summary["commit_count"],"scanned_reports":summary["report_count"],"metric_count":len({r["metric_name"] for r in rows}),"threshold_count":len(rows),"undocumented_threshold_count":hist["undocumented_count"],"threshold_conflict_count":hist["conflict_count"],"primary_source_count":len(sources),"map_count":len(maps),"artifact_available_count":sum(x["available"] for x in avail),"risk_coverage_complete_map_count":risk["complete_curve_map_count"],"multi_tolerance_complete_map_count":multi["complete_map_count"],"navigation_conditioned_evaluable_map_count":nav["evaluated_map_count"],"physical_budget_resolved_count":budgets["resolved_count"],"physical_budget_unresolved_count":budgets["unresolved_count"],"download":0,"training":0,"map_modification":0,"controller":0,"planner":0,"ETH3D":0},"global_numeric_gate_decision":GLOBAL_DECISION,"ETH3D_paused":True,"watchdog_or_managed_ssh_modified":False,"old_pr_modified":False,"final_status":"PENDING_VALIDATION","final_decision":"PENDING_VALIDATION","only_next_task":"RETROSPECTIVE_REQUALIFY_EXISTING_GAUSSIAN_MAPS_UNDER_LAYERED_PROTOCOL_V2"}
    dump_json("run_manifest.json",m); return m


def handoff_json() -> None:
    dump_json("downstream_handoff.json",{"status":"PENDING_VALIDATION","decision":"PENDING_VALIDATION","global_numeric_gate_decision":GLOBAL_DECISION,"ETH3D":"PAUSED","only_next_task":"RETROSPECTIVE_REQUALIFY_EXISTING_GAUSSIAN_MAPS_UNDER_LAYERED_PROTOCOL_V2","training_authorized":False,"controller_authorized":False,"legacy_prs_mutated":False})


def main_phase(name: str) -> None:
    if name in {"inventory","all"}: source_inventory()
    if name in {"thresholds","all"}: build_threshold_history(scan_thresholds())
    if name in {"sources","all"}:
        s=primary_sources(); write_primary_source_docs(s); metric_semantics()
    if name in {"maps","all"}:
        maps=map_inventory(); availability(maps); reference_authority(maps); parity_records(maps)
    if name in {"diagnostics","all"}:
        metrics=historical_metrics(); maps=map_inventory(); refs=reference_authority(maps); av=availability(maps)
        risk_coverage(metrics); multi_tolerance(maps); spatial_missingness(metrics); unknown_semantics(metrics); navigation_conditioned(maps,refs); physical_budgets(maps); evidence_profiles(maps,av)
    if name in {"protocol","all"}: write_protocols(); handoff_json()


if __name__ == "__main__":
    main_phase(sys.argv[1] if len(sys.argv)>1 else "all")
