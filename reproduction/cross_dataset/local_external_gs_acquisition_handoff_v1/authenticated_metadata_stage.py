#!/usr/bin/env python3
"""Official, fixed-revision metadata acquisition for the local handoff task.

Only dataset cards, attributes, statistics, and manifest metadata are allowed.
No Gaussian payload, render, RGB, depth, mesh, or full snapshot is requested.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from huggingface_hub import HfApi, hf_hub_download


TASK_ID = "LOCAL_EXTERNAL_GS_ACQUISITION_AND_VERIFIED_HANDOFF_V1"
ROOT = Path(os.environ.get("LOCAL_HANDOFF_ROOT", Path.home() / "Documents" / "Codex" / "external_gs_handoff_v1"))
REPOS = {
    "metadata": "GaussianWorld/scene_splat_7k",
    "component": "GaussianWorld/hypersim_mcmc_3dgs",
}
ALLOWED = {
    "metadata": ("README.md", ".gitattributes", "statistics/hypersim_mcmc_3dgs_runs.csv"),
    "component": ("README.md", ".gitattributes", "hypersim_mcmc_3dgs_runs.csv", "manifest/manifest.parquet"),
}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def tree_row(item: Any) -> dict[str, Any]:
    return {
        "path": item.path,
        "size": getattr(item, "size", None),
        "blob_id": getattr(item, "blob_id", None),
        "lfs_oid": getattr(getattr(item, "lfs", None), "oid", None),
        "xet_hash": getattr(item, "xet_hash", None),
    }


def main() -> int:
    api = HfApi()
    # Access has already been user-approved; this recheck only emits booleans.
    assert bool(api.whoami()), "LOCAL_HF_LOGIN_REQUIRED"
    revisions: dict[str, Any] = {"task_id": TASK_ID, "generated_utc": now(), "repositories": []}
    trees: dict[str, Any] = {"task_id": TASK_ID, "generated_utc": now(), "repositories": []}
    records: list[dict[str, Any]] = []
    raw = ROOT / "metadata" / "raw"
    cache = ROOT / "tmp" / "hf_cache"
    for role, repo in REPOS.items():
        info = api.repo_info(repo, repo_type="dataset")
        revision = info.sha
        all_items = list(api.list_repo_tree(repo, repo_type="dataset", revision=revision, recursive=True, expand=False))
        files = [item for item in all_items if hasattr(item, "blob_id")]
        selected_info = api.get_paths_info(repo, list(ALLOWED[role]), repo_type="dataset", revision=revision)
        revisions["repositories"].append({"role": role, "repo_id": repo, "revision": revision, "selected_file_count": len(selected_info)})
        trees["repositories"].append({"role": role, "repo_id": repo, "revision": revision, "file_count": len(files), "bytes": sum((getattr(item, "size", 0) or 0) for item in files), "selected_files": [tree_row(item) for item in selected_info]})
        for item in selected_info:
            cached = Path(hf_hub_download(repo_id=repo, repo_type="dataset", filename=item.path, revision=revision, cache_dir=str(cache)))
            destination = raw / role / item.path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(cached, destination)
            records.append({"role": role, "repo_id": repo, "revision": revision, "remote_path": item.path, "local_relative_path": str(destination.relative_to(ROOT)).replace("\\", "/"), "bytes": destination.stat().st_size, "remote_blob_id": item.blob_id, "remote_lfs_oid": getattr(getattr(item, "lfs", None), "oid", None), "remote_xet_hash": getattr(item, "xet_hash", None), "local_sha256": digest(destination)})
    stats = pd.read_csv(raw / "metadata" / "statistics" / "hypersim_mcmc_3dgs_runs.csv")
    manifest = pd.read_parquet(raw / "component" / "manifest" / "manifest.parquet")
    schema = {
        "task_id": TASK_ID, "generated_utc": now(), "status": "EXTERNAL_METADATA_SCHEMA_DISCOVERED",
        "statistics": {"rows": int(len(stats)), "columns": list(stats.columns), "dtypes": {key: str(value) for key, value in stats.dtypes.items()}, "source_sha256": digest(raw / "metadata" / "statistics" / "hypersim_mcmc_3dgs_runs.csv")},
        "component_manifest": {"rows": int(len(manifest)), "columns": list(manifest.columns), "dtypes": {key: str(value) for key, value in manifest.dtypes.items()}, "source_sha256": digest(raw / "component" / "manifest" / "manifest.parquet")},
    }
    write_json(ROOT / "external_repository_revision_identity.json", revisions)
    write_json(ROOT / "external_repository_tree_compact.json", trees)
    write_json(ROOT / "metadata_download_manifest.json", {"task_id": TASK_ID, "generated_utc": now(), "status": "METADATA_DOWNLOAD_PASS", "files": records, "total_bytes": sum(row["bytes"] for row in records), "no_map_payload_downloaded": True})
    write_json(ROOT / "external_scene_statistics_schema.json", schema)
    write_json(ROOT / "external_scene_statistics_summary.json", {"task_id": TASK_ID, "generated_utc": now(), "status": "EXTERNAL_STATISTICS_READY_FOR_PRECHECK", "statistics_rows": int(len(stats)), "component_manifest_rows": int(len(manifest)), "source_revisions": {entry["role"]: entry["revision"] for entry in revisions["repositories"]}})
    write_json(ROOT / "local_hf_access_and_terms_audit.json", {"task_id": TASK_ID, "generated_utc": now(), "status": "PASS_LOCAL_HF_ACCESS_AND_TERMS_GATE", "login_authenticated": True, "repository_readable": True, "user_terms_accepted_by_codex": False, "user_terms_acceptance_asserted_by_user": True, "token_content_logged": False, "token_command_argument_count": 0})
    print(json.dumps({"status": "METADATA_DOWNLOAD_PASS", "statistics_rows": int(len(stats)), "manifest_rows": int(len(manifest)), "metadata_bytes": sum(row["bytes"] for row in records)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
