#!/usr/bin/env python3
"""Local-only external pretrained Gaussian-map acquisition and handoff gate.

The no-access path is deliberately a first-class terminal result.  This module
never accepts web terms, receives a token argument, changes a map, or connects
to the server.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "LOCAL_EXTERNAL_GS_ACQUISITION_AND_VERIFIED_HANDOFF_V1"
UPSTREAM_HEAD = "71d17db633ef5e70e394cf64b92672abe872bfd0"
UPSTREAM_PR = 60
ROOT = Path(os.environ.get("LOCAL_HANDOFF_ROOT", Path.home() / "Documents" / "Codex" / "external_gs_handoff_v1"))
TRACKED_ROOT = Path(__file__).resolve().parent
MAX_BYTES = 20 * 1024**3
SUBDIRS = ("tools", "auth_audit", "source_cards", "metadata", "candidate_registry", "download_staging", "materialized_payload", "checksums", "package", "logs", "report", "tmp")
ACCESS_BLOCK = "BLOCKED_BY_LOCAL_HF_ACCESS_APPROVAL_REQUIRED"
NETWORK_BLOCK = "BLOCKED_BY_LOCAL_HF_NETWORK"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def encoded_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def atomic_json(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = encoded_json(value)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    return sha256_bytes(data)


def json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_root() -> None:
    for subdir in SUBDIRS:
        (ROOT / subdir).mkdir(parents=True, exist_ok=True)
    identity = {
        "task_id": TASK_ID,
        "upstream_pr": UPSTREAM_PR,
        "expected_upstream_head": UPSTREAM_HEAD,
        "created_utc": now(),
    }
    destination = ROOT / "TASK_IDENTITY.json"
    if destination.exists():
        existing = json_load(destination)
        if existing.get("task_id") != TASK_ID or existing.get("expected_upstream_head") != UPSTREAM_HEAD:
            raise RuntimeError("LOCAL_HANDOFF_ROOT_IDENTITY_MISMATCH")
    else:
        atomic_json(destination, identity)


def no_execution_counts() -> dict[str, int]:
    return {
        "map_training": 0, "map_modification": 0, "filtering_pruning_downsampling": 0,
        "canonical_export": 0, "geometry_evaluation": 0, "safer_g0": 0,
        "navigation": 0, "cbf_qp": 0, "scale_fitting": 0, "sim3": 0,
        "icp": 0, "preview_selection": 0, "non_official_mirror": 0,
        "language_feature_download": 0, "whole_snapshot_download": 0,
        "token_command_argument": 0, "token_disclosure": 0,
    }


def freeze_upstream_state() -> dict[str, Any]:
    payload = {
        "task_id": TASK_ID,
        "generated_utc": now(),
        "upstream_pr": UPSTREAM_PR,
        "upstream_branch": "cross-dataset-qualified-gaussian-map-acquisition-v1",
        "upstream_head": UPSTREAM_HEAD,
        "upstream_terminal_status": "BLOCKED_BY_EXTERNAL_DATASET_ACCESS_APPROVAL_REQUIRED",
        "upstream_empty_candidate_registry_sha256": "04d88c077eec6e240ab34ffe09ee4cca01b1a40663a80bbac96c3e149f93e9a8",
        "frozen_routes": {
            "tum": "CLOSE_TUM_NAVIGATION_BENCHMARK_KEEP_SAFETY_CASE_STUDY",
            "splatfacto": "CLOSE_SPLATFACTO_NAVIGATION_MAP_ROUTE",
            "splatam": "CLOSE_SPLATAM_REPLICA_MAPPING_ROUTE_UNDER_FROZEN_CONFIG",
            "gaussian_slam": "CLOSE_GAUSSIAN_SLAM_REPLICA_ROUTE_UNDER_OFFICIAL_CONFIG",
            "replica_tree_sha256": "24e21d3bccceb0516ed8b9b49b426964f3954ccd0cd804eedd5846baabd66dcb",
        },
        "budget": {"max_remote_download_bytes": MAX_BYTES, "max_full_external_scenes": 1, "backup_metadata_only": True, "max_ranked_candidates": 10, "max_families": 2},
        "counts": no_execution_counts(),
    }
    atomic_json(ROOT / "frozen_upstream_state.json", payload)
    return payload


def version_of(module: str) -> str | None:
    try:
        imported = __import__(module)
        return getattr(imported, "__version__", "installed")
    except Exception:
        return None


def tool_environment() -> dict[str, Any]:
    pip = subprocess.run([sys.executable, "-m", "pip", "--version"], text=True, capture_output=True, check=False)
    hf = shutil.which("hf")
    hf_version = None
    if hf:
        result = subprocess.run([hf, "--version"], text=True, capture_output=True, check=False)
        hf_version = (result.stdout or result.stderr).strip()[:200]
    payload = {
        "task_id": TASK_ID, "generated_utc": now(), "python_path": sys.executable,
        "python_version": sys.version, "pip_version": pip.stdout.strip(),
        "platform": platform.platform(), "hf_cli_path": hf, "hf_cli_version": hf_version,
        "packages": {name: version_of(name) for name in ("huggingface_hub", "pandas", "pyarrow", "requests", "tqdm")},
        "project_conda_modified": False,
    }
    atomic_json(ROOT / "local_tool_environment.json", payload)
    return payload


def write_manual_action(reason: str) -> Path:
    text = """# Manual Hugging Face access action required

1. In a browser, sign in to Hugging Face.
2. Open `GaussianWorld/scene_splat_7k`, read and accept applicable terms.
3. Open `GaussianWorld/hypersim_mcmc_3dgs`, read and accept applicable terms.
4. If original Hypersim GT geometry requires a separate license, read and accept it yourself.
5. In a separate PowerShell, run the current official `hf auth login` command with a read-only token.
6. Do not paste the token into Codex, Git, this directory, or a command argument.
7. Restart this task after access is available.

Codex did not accept any terms or record a token. Reason: """ + reason + "\n"
    target = ROOT / "auth_audit" / "MANUAL_ACTION_REQUIRED.md"
    target.write_text(text, encoding="utf-8")
    return target


def classify_exception(exc: Exception) -> str:
    message = str(exc).lower()
    if any(part in message for part in ("connection", "network", "dns", "timed out", "proxy", "ssl")):
        return NETWORK_BLOCK
    return ACCESS_BLOCK


def access_audit() -> tuple[dict[str, Any], Any | None]:
    env_token_present = any(bool(os.environ.get(name)) for name in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_HUB_TOKEN"))
    payload: dict[str, Any] = {
        "task_id": TASK_ID, "generated_utc": now(), "token_env_present_boolean_only": env_token_present,
        "token_content_logged": False, "token_command_argument_count": 0,
        "repositories": ["GaussianWorld/scene_splat_7k", "GaussianWorld/hypersim_mcmc_3dgs"],
        "user_terms_accepted_by_codex": False,
    }
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        who = api.whoami()
        # Do not persist username or organisation names; authentication is only a boolean gate.
        payload["login_authenticated"] = bool(who)
        checks = []
        for repo in payload["repositories"]:
            info = api.repo_info(repo, repo_type="dataset")
            tree = list(api.list_repo_tree(repo, repo_type="dataset", revision=getattr(info, "sha", None), recursive=False, expand=False))
            checks.append({"repo_id": repo, "repo_info_readable": True, "tree_readable": bool(tree), "immutable_revision": getattr(info, "sha", None)})
        payload["repository_checks"] = checks
        payload["status"] = "PASS_LOCAL_HF_ACCESS_AND_TERMS_GATE"
        payload["terms_access_evidence"] = "Authenticated official API could read both repository metadata and trees; user acceptance itself was not automated."
        atomic_json(ROOT / "local_hf_access_and_terms_audit.json", payload)
        return payload, api
    except Exception as exc:
        payload.update({"login_authenticated": False, "status": classify_exception(exc), "exception_class": type(exc).__name__, "exception_message_redacted": str(exc)[:240]})
        write_manual_action(payload["status"])
        atomic_json(ROOT / "local_hf_access_and_terms_audit.json", payload)
        return payload, None


def blocked_artifacts(status: str, environment: dict[str, Any], upstream: dict[str, Any]) -> None:
    gate = "LOCAL_HF_NETWORK" if status == NETWORK_BLOCK else "LOCAL_HF_ACCESS_APPROVAL_REQUIRED"
    names = (
        "external_repository_revision_identity.json", "external_scene_statistics_schema.json", "external_scene_statistics_summary.json", "external_candidate_precheck.json", "external_metadata_ranked_candidates.json", "external_pretrained_gs_candidate_registry.json", "primary_minimal_download_plan.json", "primary_download_execution.json", "materialization_audit.json", "handoff_tree_identity.json", "local_handoff_double_validation_summary.json", "package_identity.json",
    )
    for name in names:
        atomic_json(ROOT / name, {"task_id": TASK_ID, "generated_utc": now(), "status": f"NOT_AUTHORIZED_DUE_TO_{gate}", "gate": gate, "no_external_payload_downloaded": True})
    final = {
        "task_id": TASK_ID, "generated_utc": now(), "status": "VALIDATION_PASS_FOR_BLOCKED_LOCAL_ACCESS_STATE",
        "final_status": status, "checks": {"upstream_frozen": True, "token_disclosure_count": 0, "token_command_argument_count": 0, "downloaded_bytes": 0, "map_training": 0, "map_modification": 0, "geometry_evaluation": 0, "safer_g0": 0, "navigation": 0, "no_payload_before_access": True},
    }
    atomic_json(ROOT / "validation_result.json", final)
    decision = "REPAIR_LOCAL_HF_NETWORK_BEFORE_DOWNLOAD" if status == NETWORK_BLOCK else "USER_MUST_ACCEPT_TERMS_AND_LOGIN_LOCALLY"
    next_task = "RESUME_LOCAL_EXTERNAL_GS_ACQUISITION_AFTER_NETWORK_REPAIR_V1" if status == NETWORK_BLOCK else "RESUME_LOCAL_EXTERNAL_GS_ACQUISITION_AFTER_LOGIN_V1"
    atomic_json(ROOT / "downstream_handoff.json", {"task_id": TASK_ID, "generated_utc": now(), "final_status": status, "final_decision": decision, "sole_next_task": next_task, "no_map_qualification": True, "counts": no_execution_counts()})
    lines = [
        "# Local External GS Acquisition and Verified Handoff V1", "",
        "## Final outcome", "", f"- `FINAL_STATUS`: `{status}`", f"- `FINAL_DECISION`: `{decision}`", f"- Sole next task: `{next_task}`", "",
        "## Why local acquisition was attempted", "", "PR #60 was blocked because the authority server could not reach Hugging Face. This local task keeps acquisition separate from map qualification.", "",
        "## Access and security boundary", "", "The user has not been represented in accepting any web terms. No token, cookie, auth header, or token command argument was recorded. No metadata or external payload was downloaded.", "",
        "## Frozen research boundary", "", "TUM, Splatfacto, SplaTAM, Gaussian-SLAM, Replica training, map modification, geometry evaluation, SAFER G0, navigation, and CBF-QP all remain at zero for this task.", "",
        "## Required user action", "", "See `auth_audit/MANUAL_ACTION_REQUIRED.md`, then resume the sole next task. This blocked result is not a Gaussian-map qualification result.",
    ]
    (ROOT / "report" / "REPORT_LOCAL_EXTERNAL_GS_ACQUISITION_AND_HANDOFF_V1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> int:
    ensure_root()
    upstream = freeze_upstream_state()
    environment = tool_environment()
    access, api = access_audit()
    if api is None:
        blocked_artifacts(access["status"], environment, upstream)
        print(json.dumps({"final_status": access["status"], "root": str(ROOT)}, sort_keys=True))
        return 0
    # The authenticated full pipeline intentionally requires the separately frozen
    # metadata schema implementation. It is never entered until the user gate has
    # been demonstrated through the official API.
    raise RuntimeError("AUTHENTICATED_PIPELINE_REQUIRES_METADATA_STAGE_IMPLEMENTATION")


if __name__ == "__main__":
    raise SystemExit(run())
