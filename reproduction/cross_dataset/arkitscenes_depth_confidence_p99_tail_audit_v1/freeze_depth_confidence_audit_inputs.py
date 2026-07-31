#!/usr/bin/env python3
"""Fail-closed raw-byte and authority freezer for the ARKitScenes p99 audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path


BASE_HEAD = "1c55f67e7b93b098c672eb09ff483fd8d037fde9"
PR70_HEAD = "ff58dbbd4d7da143e5d457a2765b8760bdcc4959"
TRAIN_PATH = "reproduction/cross_dataset/arkitscenes_spatial_group_split_contract_v2/v2_split/arkitscenes_train_manifest_v2.csv"
HELDOUT_PATH = "reproduction/cross_dataset/arkitscenes_spatial_group_split_contract_v2/v2_split/arkitscenes_heldout_manifest_v2.csv"
EXPECTED = {
    "train": {
        "sha256": "167066916ce1a3281ac754dfdeec37ada9f5b0e31227c731c94cebb698a2a6e3",
        "oid": "a2ddc70775e6d0f9c25f77ef5f869556d83b292c",
        "rows": 214,
        "split": "TRAIN",
        "path": TRAIN_PATH,
    },
    "heldout": {
        "sha256": "7b65f741e901690f2a723579d75200eebe7b9e77b0cd57c030d4a14d0474c0c7",
        "oid": "cf28dd385711a31733360e5fc21dce229ce605bc",
        "rows": 53,
        "split": "HELDOUT",
        "path": HELDOUT_PATH,
    },
}
AUTHORITIES = {
    "arkitscenes": "7283761bf26c27570ec59a5dc0f8686fbff07726",
    "splatam": "da6bbcd24c248dc884ac7f49d62e91b841b26ccc",
    "rasterizer": "cb65e4b86bc3bd8ed42174b72a62e8d3a3a71110",
}


def run(*args: str, cwd: Path | None = None) -> bytes:
    return subprocess.check_output(args, cwd=cwd)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_oid(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def parse_rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(data.decode("utf-8").splitlines()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--heldout", type=Path, required=True)
    parser.add_argument("--arkitscenes-source", type=Path, required=True)
    parser.add_argument("--splatam-source", type=Path, required=True)
    parser.add_argument("--environment-lock", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repo = args.repo.resolve()
    repo_head = run("git", "rev-parse", "HEAD", cwd=repo).decode().strip()
    checks: dict[str, bool] = {"repo_head_pr70": repo_head == PR70_HEAD}
    records: dict[str, object] = {}
    for label, supplied in (("train", args.train), ("heldout", args.heldout)):
        spec = EXPECTED[label]
        disk = supplied.resolve().read_bytes()
        blob = run("git", "cat-file", "blob", f"HEAD:{spec['path']}", cwd=repo)
        rows = parse_rows(blob)
        entry = {
            "path": spec["path"],
            "disk_sha256": sha256(disk),
            "git_blob_sha256": sha256(blob),
            "git_blob_oid": git_blob_oid(blob),
            "row_count": len(rows),
            "working_tree_equals_blob": disk == blob,
            "scene_values": sorted({row["video_id"] for row in rows}),
            "split_values": sorted({row["split"] for row in rows}),
            "utf8_no_bom": not blob.startswith(b"\xef\xbb\xbf"),
            "lf_only": b"\r" not in blob,
            "final_lf": blob.endswith(b"\n"),
        }
        entry_checks = {
            "sha256": entry["git_blob_sha256"] == spec["sha256"],
            "oid": entry["git_blob_oid"] == spec["oid"],
            "rows": entry["row_count"] == spec["rows"],
            "disk_equals_blob": entry["working_tree_equals_blob"],
            "scene": entry["scene_values"] == ["48018874"],
            "split": entry["split_values"] == [spec["split"]],
            "encoding": entry["utf8_no_bom"] and entry["lf_only"] and entry["final_lf"],
        }
        entry["checks"] = entry_checks
        checks[f"{label}_all"] = all(entry_checks.values())
        records[label] = entry

    arkit_head = run("git", "rev-parse", "HEAD", cwd=args.arkitscenes_source.resolve()).decode().strip()
    splatam_head = run("git", "rev-parse", "HEAD", cwd=args.splatam_source.resolve()).decode().strip()
    lock = json.loads(args.environment_lock.read_text(encoding="utf-8"))
    authority = {
        "arkitscenes": arkit_head,
        "splatam": splatam_head,
        "rasterizer": lock.get("official_rasterizer_submodule_head"),
    }
    checks["authorities"] = authority == AUTHORITIES
    mesh = args.asset_root.resolve() / "48018874_3dod_mesh.ply"
    checks["asset_root"] = args.asset_root.resolve().is_dir()
    checks["mesh"] = mesh.is_file() and mesh.stat().st_size > 0
    status = "PASS_DEPTH_CONFIDENCE_AUDIT_INPUT_IDENTITY" if all(checks.values()) else "BLOCKED_BY_DEPTH_CONFIDENCE_AUDIT_INPUT_IDENTITY"
    payload = {
        "status": status,
        "audit_base_head": BASE_HEAD,
        "server_canonical_repo_head": repo_head,
        "checks": checks,
        "manifest_records": records,
        "authority": authority,
        "asset_root": str(args.asset_root.resolve()),
        "mesh": {"path": str(mesh), "size": mesh.stat().st_size if mesh.is_file() else 0, "sha256": hashlib.sha256(mesh.read_bytes()).hexdigest() if mesh.is_file() else None},
        "frozen_contract": {
            "scene": "48018874",
            "visit": "483945",
            "train": 214,
            "heldout": 53,
            "split_identity": "97a707510227271d12859ee78defc0d6170cc24cb67e423568cd1a72e3345dee",
            "selected_group_tuple": "8ad320980bb36edb2accb38629ec3046095c9ef7735fbb748f4e112ee75bd388",
            "pr71_loader_audit_sha": "adb90f8ee4fd5638662ae2174e7fd75bd31413639038c987ad33508280fc33b7",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(status)
    return 0 if status.startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
