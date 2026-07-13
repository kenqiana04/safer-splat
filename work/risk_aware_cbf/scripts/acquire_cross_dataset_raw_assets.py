#!/usr/bin/env python3
"""Acquire only official TUM RGB-D and license-gated Replica raw assets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, build_opener


ASSET_ROOT = Path("/disk1/zlab/cross_dataset_assets")
RESULT_DIR = Path("work/risk_aware_cbf/results/cross_dataset_raw_acquisition")
ALLOWED_HOSTS = {"cvg.cit.tum.de", "github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com", "dl.fbaipublicfiles.com"}
TUM_URL = "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_room.tgz"
TUM_PAGE = "https://cvg.cit.tum.de/data/datasets/rgbd-dataset"
TUM_DOWNLOAD_PAGE = "https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download"
REPLICA_REPO = "https://github.com/facebookresearch/Replica-Dataset.git"
REPLICA_TAG = "v1.0"
RESERVE_BYTES = 50 * 1024**3
TUM_FALLBACK_BYTES = int(0.73 * 1024**3)
TUM_EXTRACT_ESTIMATE_BYTES = 3 * 1024**3


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


def host_allowed(url: str) -> bool:
    return urlparse(url).hostname in ALLOWED_HOSTS


def request(url: str, method: str = "GET", headers: dict[str, str] | None = None):
    if not host_allowed(url):
        raise RuntimeError(f"Unapproved source host: {urlparse(url).hostname}")
    opener = build_opener()
    response = opener.open(Request(url, method=method, headers=headers or {}), timeout=30)
    resolved = response.geturl()
    if not host_allowed(resolved):
        response.close()
        raise RuntimeError(f"Redirect left approved hosts: {resolved}")
    return response, resolved


def head(url: str) -> dict[str, object]:
    try:
        response, resolved = request(url, "HEAD")
        status = getattr(response, "status", 200)
        length = response.headers.get("Content-Length")
        response.close()
        return {"source_url": url, "resolved_url": resolved, "head_status": status, "content_length": int(length) if length and length.isdigit() else None, "notes": ""}
    except Exception as exc:
        return {"source_url": url, "resolved_url": "", "head_status": "error", "content_length": None, "notes": f"{type(exc).__name__}: {exc}"[:500]}


def disk_gate(asset_root: Path, required_bytes: int) -> dict[str, object]:
    usage = shutil.disk_usage(asset_root)
    return {"asset_root": str(asset_root), "total_bytes": usage.total, "available_bytes": usage.free, "download_estimated_bytes": required_bytes, "minimum_reserve_bytes": RESERVE_BYTES, "storage_gate_passed": usage.free - required_bytes >= RESERVE_BYTES}


def snapshot(url: str, path: Path) -> dict[str, object]:
    response, resolved = request(url)
    payload = response.read()
    response.close()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return {"source_url": url, "resolved_url": resolved, "path": str(path), "sha256": sha256(path), "bytes": len(payload)}


def download(url: str, destination: Path, resume: bool) -> dict[str, object]:
    partial = destination.with_suffix(destination.suffix + ".partial")
    if destination.exists():
        return {"source_url": url, "resolved_url": url, "downloaded": True, "local_path": str(destination), "local_size": destination.stat().st_size, "sha256": sha256(destination), "verification_status": "already_present", "notes": "Existing archive was not overwritten."}
    offset = partial.stat().st_size if resume and partial.exists() else 0
    headers = {"Range": f"bytes={offset}-"} if offset else {}
    response, resolved = request(url, headers=headers)
    status = getattr(response, "status", 200)
    if offset and status != 206:
        response.close()
        raise RuntimeError(f"Resume request did not return HTTP 206 (got {status})")
    mode = "ab" if offset else "wb"
    with partial.open(mode) as handle:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            handle.write(block)
    response.close()
    os.replace(partial, destination)
    return {"source_url": url, "resolved_url": resolved, "downloaded": True, "local_path": str(destination), "local_size": destination.stat().st_size, "sha256": sha256(destination), "verification_status": "downloaded", "notes": f"HTTP {status}; atomic rename from {partial.name}"}


def clone_replica(manifest_root: Path, license_dir: Path) -> dict[str, object]:
    repo = manifest_root / "Replica-Dataset"
    if repo.exists():
        status = subprocess.run(["git", "-C", str(repo), "status", "--short"], text=True, capture_output=True, check=True).stdout.strip()
        if status:
            raise RuntimeError("Replica metadata repository has local modifications; refusing to pull or overwrite it.")
    else:
        subprocess.run(["git", "clone", "--depth", "1", REPLICA_REPO, str(repo)], check=True)
    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True, capture_output=True, check=True).stdout.strip()
    license_path, readme_path, script_path = repo / "LICENSE", repo / "README.md", repo / "download.sh"
    for path in (license_path, readme_path, script_path):
        if not path.is_file():
            raise RuntimeError(f"Missing required official metadata file: {path}")
    copied_license = license_dir / "replica_LICENSE.txt"
    shutil.copyfile(license_path, copied_license)
    script_text = script_path.read_text(encoding="utf-8", errors="replace")
    urls = sorted(set(re.findall(r"https?://[^\s\"']+", script_text)))
    parts = [f"replica_v1_0.tar.gz.part{chr(first)}{chr(second)}" for first in range(ord("a"), ord("a") + 1) for second in range(ord("a"), ord("q") + 1)]
    return {"repo": str(repo), "commit": commit, "license_path": str(copied_license), "license_sha256": sha256(license_path), "readme_sha256": sha256(readme_path), "download_script": str(script_path), "download_script_sha256": sha256(script_path), "urls": urls, "expected_parts": parts, "citation": "Straub et al., The Replica Dataset: A Digital Replica of Indoor Spaces, arXiv:1906.05797", "tag": REPLICA_TAG}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dataset", choices=("tum_rgbd", "replica", "all"), default="all")
    parser.add_argument("--asset-root", type=Path, default=ASSET_ROOT)
    parser.add_argument("--result-dir", type=Path, default=RESULT_DIR)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    root = args.asset_root.resolve()
    downloads, raw, manifests, licenses, approvals, tmp = (root / "downloads", root / "raw", root / "manifests", root / "licenses", root / "approvals", root / "tmp")
    for directory in (downloads, raw / "tum_rgbd", raw / "replica", manifests, licenses, approvals, tmp):
        directory.mkdir(parents=True, exist_ok=True)
    args.result_dir.mkdir(parents=True, exist_ok=True)
    prereg = [
        {"dataset_id": "TUM_FR1_ROOM", "dataset_family": "TUM_RGBD", "asset_name": "rgbd_dataset_freiburg1_room", "official_source": "official_tum", "automatic_download_allowed": "true", "manual_license_gate": "false", "selected": "true", "notes": "fixed before download"},
        {"dataset_id": "REPLICA_V1", "dataset_family": "Replica", "asset_name": "Replica Dataset v1", "official_source": "official_meta", "automatic_download_allowed": "false", "manual_license_gate": "true", "selected": "true", "notes": "download only after user-created license marker"},
    ]
    write_csv(args.result_dir / "dataset_preregistration.csv", list(prereg[0]), prereg)
    source_rows, license_rows, storage_rows, download_rows = [], [], [], []
    state: dict[str, object] = {"tum": {}, "replica": {}, "task": "raw_asset_acquisition_only", "navigation_experiment_run": False, "dataset_processing_run": False, "gsplat_training_run": False}
    try:
        replica = clone_replica(manifests, licenses)
        state["replica"].update(replica)
        source_rows.append({"dataset_id": "REPLICA_V1", "official_source": REPLICA_REPO, "verified": True, "reference": REPLICA_TAG, "notes": replica["commit"]})
        license_rows.append({"dataset_id": "REPLICA_V1", "license_status": "research_terms_manual_acceptance_required", "license_path": replica["license_path"], "license_sha256": replica["license_sha256"], "notes": "User marker is required before download."})
    except Exception as exc:
        state["replica"]["metadata_error"] = f"{type(exc).__name__}: {exc}"
    tum_page = snapshot(TUM_PAGE, licenses / "tum_rgbd_dataset_page.html")
    tum_download_page = snapshot(TUM_DOWNLOAD_PAGE, licenses / "tum_rgbd_download_page.html")
    source_rows.append({"dataset_id": "TUM_FR1_ROOM", "official_source": TUM_URL, "verified": True, "reference": TUM_PAGE, "notes": "Official TUM sequence URL."})
    license_rows.append({"dataset_id": "TUM_FR1_ROOM", "license_status": "CC_BY_4_0_dataset; BSD_2_Clause_source_code", "license_path": tum_page["path"], "license_sha256": tum_page["sha256"], "notes": f"download_page_sha256={tum_download_page['sha256']}"})
    state["tum"].update({"official_source_verified": True, "license_recorded": True, "dataset": "rgbd_dataset_freiburg1_room"})
    tum_head = head(TUM_URL)
    tum_estimate = int(tum_head["content_length"] or TUM_FALLBACK_BYTES)
    tum_gate = disk_gate(root, tum_estimate + TUM_EXTRACT_ESTIMATE_BYTES)
    tum_gate.update({"dataset_id": "TUM_FR1_ROOM", "size_source": "http_head" if tum_head["content_length"] else "official_page_approximation", "estimated_extracted_bytes": TUM_EXTRACT_ESTIMATE_BYTES})
    storage_rows.append(tum_gate)
    state["tum"].update({"head": tum_head, "storage_gate": tum_gate, "download_attempted": False})
    if args.dataset in {"tum_rgbd", "all"} and not args.dry_run and not args.verify_only and tum_gate["storage_gate_passed"]:
        archive = downloads / "rgbd_dataset_freiburg1_room.tgz"
        result = download(TUM_URL, archive, args.resume)
        download_rows.append({"dataset_id": "TUM_FR1_ROOM", **result})
        state["tum"].update({"download_attempted": True, "archive": result})
    marker = approvals / "replica_research_terms_accepted.txt"
    marker_present = marker.is_file() and marker.stat().st_size > 0
    state["replica"].update({"manual_acceptance_marker_present": marker_present, "download_attempted": False, "status": "waiting_for_manual_license_confirmation" if not marker_present else "pending_storage_gate"})
    replica_urls = state["replica"].get("urls", [])
    replica_lengths = [head(url) for url in replica_urls if host_allowed(url)]
    replica_known_bytes = sum(int(item["content_length"] or 0) for item in replica_lengths)
    replica_gate = disk_gate(root, replica_known_bytes * 2 if replica_known_bytes else 0)
    replica_gate.update({"dataset_id": "REPLICA_V1", "size_source": "official_download_script_head" if replica_known_bytes else "unknown", "estimated_extracted_bytes": replica_known_bytes, "replica_storage_status": "known" if replica_known_bytes else "unknown"})
    storage_rows.append(replica_gate)
    state["replica"].update({"storage_gate": replica_gate, "download_part_heads": replica_lengths})
    if marker_present and args.dataset in {"replica", "all"} and not args.dry_run and not args.verify_only and replica_gate["storage_gate_passed"]:
        raise RuntimeError("Replica marker is present, but automated execution of the official script is intentionally delegated to a separately reviewed invocation.")
    write_csv(args.result_dir / "source_inventory.csv", ["dataset_id", "official_source", "verified", "reference", "notes"], source_rows)
    write_csv(args.result_dir / "license_summary.csv", ["dataset_id", "license_status", "license_path", "license_sha256", "notes"], license_rows)
    write_csv(args.result_dir / "storage_gate_summary.csv", ["dataset_id", "asset_root", "total_bytes", "available_bytes", "download_estimated_bytes", "estimated_extracted_bytes", "minimum_reserve_bytes", "storage_gate_passed", "size_source", "replica_storage_status"], storage_rows)
    write_csv(args.result_dir / "download_manifest.csv", ["dataset_id", "source_url", "resolved_url", "downloaded", "local_path", "local_size", "sha256", "verification_status", "notes"], download_rows)
    (manifests / "raw_acquisition_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(json.dumps({"tum_download_attempted": state["tum"].get("download_attempted"), "replica_status": state["replica"].get("status"), "replica_marker_present": marker_present}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
