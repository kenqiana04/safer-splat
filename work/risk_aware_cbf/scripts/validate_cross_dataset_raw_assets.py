#!/usr/bin/env python3
"""Validate external TUM and Replica raw assets without preprocessing or training."""

from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import tarfile
from pathlib import Path, PurePosixPath


ASSET_ROOT = Path("/disk1/zlab/cross_dataset_assets")
RESULT_DIR = Path("work/risk_aware_cbf/results/cross_dataset_raw_acquisition")
TUM_URL = "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_room.tgz"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list[list[float]]:
    rows: list[list[float]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        try:
            rows.append([float(value) for value in fields])
        except ValueError:
            continue
    return rows


def nearest_rate(source: list[float], target: list[float], threshold: float) -> float | None:
    if not source or not target:
        return None
    target = sorted(target)
    matched = 0
    for value in source:
        index = bisect.bisect_left(target, value)
        candidates = target[max(0, index - 1):min(len(target), index + 1)]
        matched += int(bool(candidates) and min(abs(value - candidate) for candidate in candidates) <= threshold)
    return matched / len(source)


def archive_safe(archive: Path) -> tuple[bool, str, list[tarfile.TarInfo]]:
    try:
        with tarfile.open(archive, "r:gz") as handle:
            members = handle.getmembers()
            for member in members:
                pure = PurePosixPath(member.name)
                if pure.is_absolute() or ".." in pure.parts or member.issym() or member.islnk():
                    return False, f"unsafe archive member: {member.name}", members
            return True, "", members
    except (tarfile.TarError, OSError) as exc:
        return False, f"{type(exc).__name__}: {exc}", []


def extract_safe(archive: Path, target: Path, members: list[tarfile.TarInfo]) -> None:
    target.mkdir(parents=True, exist_ok=True)
    root = target.resolve()
    with tarfile.open(archive, "r:gz") as handle:
        for member in members:
            candidate = (target / member.name).resolve()
            if root != candidate and root not in candidate.parents:
                raise RuntimeError(f"Path traversal rejected: {member.name}")
            handle.extract(member, path=target)


def png_readable(path: Path) -> bool:
    try:
        return path.stat().st_size > 0 and path.open("rb").read(8) == b"\x89PNG\r\n\x1a\n"
    except OSError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", type=Path, default=ASSET_ROOT)
    parser.add_argument("--result-dir", type=Path, default=RESULT_DIR)
    parser.add_argument("--extract-tum", action="store_true")
    args = parser.parse_args()
    root, results = args.asset_root.resolve(), args.result_dir
    results.mkdir(parents=True, exist_ok=True)
    state_path = root / "manifests/raw_acquisition_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"tum": {}, "replica": {}}
    archive = root / "downloads/rgbd_dataset_freiburg1_room.tgz"
    tum_raw = root / "raw/tum_rgbd/rgbd_dataset_freiburg1_room"
    archive_valid = False
    archive_note, members = "archive_missing", []
    if archive.exists():
        archive_valid, archive_note, members = archive_safe(archive)
        if archive_valid and args.extract_tum and not tum_raw.exists():
            extract_safe(archive, root / "raw/tum_rgbd", members)
    expected = {"rgb": tum_raw / "rgb", "depth": tum_raw / "depth", "rgb_txt": tum_raw / "rgb.txt", "depth_txt": tum_raw / "depth.txt", "groundtruth_txt": tum_raw / "groundtruth.txt", "accelerometer_txt": tum_raw / "accelerometer.txt"}
    rgb_files = sorted(expected["rgb"].glob("*.png")) if expected["rgb"].is_dir() else []
    depth_files = sorted(expected["depth"].glob("*.png")) if expected["depth"].is_dir() else []
    rgb_rows, depth_rows, gt_rows, accel_rows = (read_rows(expected[key]) for key in ("rgb_txt", "depth_txt", "groundtruth_txt", "accelerometer_txt"))
    rgb_times, depth_times, gt_times = ([row[0] for row in rows if rows] for rows in (rgb_rows, depth_rows, gt_rows))
    rgb_depth_rate = nearest_rate(rgb_times, depth_times, 0.02)
    rgb_pose_rate = nearest_rate(rgb_times, gt_times, 0.02)
    triple_rate = None if rgb_depth_rate is None or rgb_pose_rate is None else min(rgb_depth_rate, rgb_pose_rate)
    core_present = all(expected[key].is_file() and expected[key].stat().st_size > 0 for key in ("rgb_txt", "depth_txt", "groundtruth_txt"))
    images_ok = bool(rgb_files and depth_files) and all(png_readable(path) for path in rgb_files + depth_files)
    tum_integrity = bool(archive_valid and core_present and images_ok and rgb_times and depth_times and gt_times)
    tum_archive_row = {"dataset_id": "TUM_FR1_ROOM", "archive_path": str(archive), "archive_exists": archive.exists(), "archive_size_bytes": archive.stat().st_size if archive.exists() else None, "archive_sha256": sha256(archive) if archive.exists() else None, "gzip_tar_valid": archive_valid, "path_traversal_safe": archive_valid, "member_count": len(members), "notes": archive_note}
    tum_file_row = {"dataset_id": "TUM_FR1_ROOM", "extracted_path": str(tum_raw), "rgb_count": len(rgb_files), "depth_count": len(depth_files), "rgb_txt_exists": expected["rgb_txt"].is_file(), "depth_txt_exists": expected["depth_txt"].is_file(), "groundtruth_exists": expected["groundtruth_txt"].is_file(), "accelerometer_status": "present" if expected["accelerometer_txt"].is_file() else "absent_not_fatal", "images_readable": images_ok, "core_files_nonempty": core_present, "integrity_passed": tum_integrity}
    tum_time_row = {"dataset_id": "TUM_FR1_ROOM", "rgb_index_row_count": len(rgb_rows), "depth_index_row_count": len(depth_rows), "groundtruth_row_count": len(gt_rows), "accelerometer_row_count": len(accel_rows), "rgb_timestamp_min": min(rgb_times) if rgb_times else None, "rgb_timestamp_max": max(rgb_times) if rgb_times else None, "depth_timestamp_min": min(depth_times) if depth_times else None, "depth_timestamp_max": max(depth_times) if depth_times else None, "groundtruth_timestamp_min": min(gt_times) if gt_times else None, "groundtruth_timestamp_max": max(gt_times) if gt_times else None, "metric_scale_status": "source_documented" if gt_times else "not_available"}
    association_row = {"dataset_id": "TUM_FR1_ROOM", "rgb_depth_threshold_s": 0.02, "rgb_pose_threshold_s": 0.02, "rgb_depth_match_rate": rgb_depth_rate, "rgb_pose_match_rate": rgb_pose_rate, "triple_match_rate": triple_rate, "notes": "Diagnostic only; no association file was written."}
    replica = state.get("replica", {})
    marker = root / "approvals/replica_research_terms_accepted.txt"
    marker_present = marker.is_file() and marker.stat().st_size > 0
    expected_parts = replica.get("expected_parts", [f"replica_v1_0.tar.gz.parta{chr(code)}" for code in range(ord("a"), ord("q") + 1)])
    replica_rows = [{"part_id": part, "source_url": "", "resolved_url": "", "content_length": None, "head_status": "not_downloaded", "downloaded": False, "local_path": str(root / "downloads" / part), "local_size": None, "sha256": None, "verification_status": "waiting_for_manual_license_confirmation" if not marker_present else "not_downloaded", "notes": ""} for part in expected_parts]
    replica_scene_rows: list[dict[str, object]] = []
    replica_integrity = False
    if not marker_present:
        replica_status = "waiting_for_manual_license_confirmation"
    else:
        replica_status = "not_downloaded"
    if tum_integrity and not marker_present:
        decision = "tum_ready_replica_waiting_manual_license_confirmation"
    elif tum_integrity:
        decision = "inconclusive_due_to_environment"
    elif archive.exists():
        decision = "blocked_by_data_integrity"
    else:
        decision = "blocked_by_official_source_access"
    write_csv(results / "archive_integrity_summary.csv", list(tum_archive_row), [tum_archive_row])
    write_csv(results / "tum_file_integrity_summary.csv", list(tum_file_row), [tum_file_row])
    write_csv(results / "tum_timestamp_summary.csv", list(tum_time_row), [tum_time_row])
    write_csv(results / "tum_association_feasibility_summary.csv", list(association_row), [association_row])
    write_csv(results / "replica_download_part_inventory.csv", list(replica_rows[0]), replica_rows)
    write_csv(results / "replica_scene_integrity_summary.csv", ["scene_name", "mesh_exists", "mesh_size", "mesh_sha256", "navmesh_exists", "navmesh_size", "navmesh_sha256", "textures_exists", "stage_config_exists", "scene_complete", "missing_fields"], replica_scene_rows)
    write_csv(results / "citation_summary.csv", ["dataset_id", "citation", "official_reference"], [{"dataset_id": "TUM_FR1_ROOM", "citation": "Sturm et al., A Benchmark for the Evaluation of RGB-D SLAM Systems, IROS 2012", "official_reference": "https://cvg.cit.tum.de/data/datasets/rgbd-dataset"}, {"dataset_id": "REPLICA_V1", "citation": replica.get("citation", "Straub et al., The Replica Dataset, arXiv:1906.05797"), "official_reference": "https://github.com/facebookresearch/Replica-Dataset/releases/tag/v1.0"}])
    write_csv(results / "external_asset_paths.csv", ["dataset_id", "external_path", "git_tracked", "notes"], [{"dataset_id": "TUM_FR1_ROOM", "external_path": str(tum_raw), "git_tracked": False, "notes": "Archive retained outside Git."}, {"dataset_id": "REPLICA_V1", "external_path": str(root / "raw/replica"), "git_tracked": False, "notes": "Download remains gated by manual acceptance marker."}])
    metrics = {"task": "Cross-Dataset Raw Asset Acquisition and Integrity Audit", "new_scientific_experiment_run": False, "baseline_navigation_run": False, "gsplat_training_run": False, "dataset_processing_run": False, "tum_dataset": "rgbd_dataset_freiburg1_room", "tum_official_source_verified": bool(state.get("tum", {}).get("official_source_verified")), "tum_license_recorded": bool(state.get("tum", {}).get("license_recorded")), "tum_download_attempted": bool(state.get("tum", {}).get("download_attempted")), "tum_download_completed": archive.exists(), "tum_archive_valid": archive_valid, "tum_archive_sha256": tum_archive_row["archive_sha256"], "tum_archive_size_bytes": tum_archive_row["archive_size_bytes"], "tum_extracted": tum_raw.is_dir(), "tum_rgb_count": len(rgb_files) if tum_raw.exists() else None, "tum_depth_count": len(depth_files) if tum_raw.exists() else None, "tum_groundtruth_row_count": len(gt_rows) if tum_raw.exists() else None, "tum_triple_match_rate_diagnostic": triple_rate, "tum_integrity_passed": tum_integrity, "replica_version": "v1", "replica_official_source_verified": bool(replica.get("commit")), "replica_license_recorded": bool(replica.get("license_sha256")), "replica_manual_acceptance_marker_present": marker_present, "replica_storage_gate_passed": bool(replica.get("storage_gate", {}).get("storage_gate_passed")), "replica_download_attempted": False, "replica_download_completed": False, "replica_split_part_count_expected": 17, "replica_split_part_count_downloaded": 0, "replica_scene_count": None, "replica_complete_scene_count": None, "replica_integrity_passed": replica_integrity, "third_party_data_committed": False, "third_party_license_text_committed": False, "raw_trace_committed": False, "official_core_source_modified": False, "forbidden_paths_modified": False, "acquisition_decision": decision, "limitations": ["raw asset acquisition and integrity only", "no data preprocessing", "no Gaussian reconstruction", "no SAFER baseline execution", "no method-improvement module evaluation", "Replica download requires manual user acceptance of its research terms"]}
    (results / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (results / "README.md").write_text("# Cross-Dataset Raw Acquisition\n\nCompact summaries only. All third-party data, page snapshots, licenses, archives, and approval markers remain under the external asset root.\n", encoding="utf-8")
    (results / "analysis_notes.md").write_text(f"# Analysis Notes\n\nTUM integrity: `{tum_integrity}`. Replica status: `{replica_status}`.\n", encoding="utf-8")
    report = f"""# REPORT: Cross-Dataset Raw Asset Acquisition and Integrity Audit

## 1. Purpose
获取并验证原始跨数据集资产；不进行预处理、训练或 SAFER 执行。

## 2. Relationship to Baseline Cross-Dataset G0-G1
本任务只解除原始资产可用性阻断，不构成 GSplat 兼容性或 baseline 泛化证据。

## 3. Fixed Dataset Preregistration
TUM RGB-D `rgbd_dataset_freiburg1_room` 与 Replica Dataset v1 已在下载前固定。

## 4. Official Sources
TUM: `{TUM_URL}`。Replica 元数据来自官方 repository，commit `{replica.get('commit')}`。

## 5. License and Manual-Approval Boundaries
TUM 许可证已记录为 CC BY 4.0。Replica marker present: `{marker_present}`；未由本任务创建或伪造。

## 6. Storage and Network Gates
所有原始资产仅位于 `{root}`；下载仅允许官方 host，完成后保留至少 50 GiB。

## 7. TUM RGB-D Download
archive exists: `{archive.exists()}`，size: `{tum_archive_row['archive_size_bytes']}`，SHA256: `{tum_archive_row['archive_sha256']}`。

## 8. TUM Archive and File Integrity
gzip/tar and path-traversal gate: `{archive_valid}`；TUM integrity: `{tum_integrity}`。

## 9. TUM Timestamp and Association Feasibility
RGB-depth rate: `{rgb_depth_rate}`；RGB-pose rate: `{rgb_pose_rate}`；triple rate: `{triple_rate}`。这些仅为诊断，不生成 association 文件。

## 10. Replica Official Download Contract
记录官方 metadata、LICENSE 和 `download.sh` hashes；完整 Replica v1 仍只能按官方脚本获取。

## 11. Replica Manual License Gate
Replica status: `{replica_status}`。用户人工条款确认是正式下载的前置条件。

## 12. Replica Download and Scene Integrity
未执行 Replica 下载、解压或场景处理。

## 13. External Asset Locations
第三方数据位于 `{root}`，未进入 Git。

## 14. Negative and Neutral Evidence
Replica 等待许可不是数据完整性或 SAFER 方法失败。下载成功也不表示 baseline 能泛化。

## 15. Acquisition Decision
`{decision}`

## 16. Next Processing Entry Conditions
TUM 只有在 `tum_integrity_passed=true` 时可进入单独的预处理任务。Replica 还需用户创建且非空的 acceptance marker。

## 17. Claim Boundaries
This task acquires and verifies raw cross-dataset assets only. It does not preprocess the datasets, train Gaussian maps, or evaluate SAFER baseline generalization.
"""
    (results.parent.parent / "REPORT_CROSS_DATASET_RAW_ACQUISITION.md").write_text(report, encoding="utf-8")
    print(f"acquisition_decision={decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
