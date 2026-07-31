#!/usr/bin/env python3
"""Freeze the canonical PR #70 mapping inputs using exact Git blob bytes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path
from typing import Any


PR68 = "9f068e1708e7422e3e53c01c96fa29242be35f0a"
PR69 = "dabaa0bbf44cd81783c3c00d0744f44affaffcb2"
PR70 = "ff58dbbd4d7da143e5d457a2765b8760bdcc4959"
V2 = Path("reproduction/cross_dataset/arkitscenes_spatial_group_split_contract_v2")
RAW_V1 = Path("reproduction/cross_dataset/arkitscenes_raw_splatam_learned_3dgs_qualification_v1")
EXPECTED = {
    "train": {
        "path": V2 / "v2_split/arkitscenes_train_manifest_v2.csv",
        "oid": "a2ddc70775e6d0f9c25f77ef5f869556d83b292c",
        "sha256": "167066916ce1a3281ac754dfdeec37ada9f5b0e31227c731c94cebb698a2a6e3",
        "semantic_sha256": "32adca1e09694dce9ff5bebc895109f32f866e1c8ecc845e3927a07f60129d12",
        "rows": 214,
    },
    "heldout": {
        "path": V2 / "v2_split/arkitscenes_heldout_manifest_v2.csv",
        "oid": "cf28dd385711a31733360e5fc21dce229ce605bc",
        "sha256": "7b65f741e901690f2a723579d75200eebe7b9e77b0cd57c030d4a14d0474c0c7",
        "semantic_sha256": "69c8328511cd8405b17b2fc17da9f557ed69ac75b3cfc442f380d586ecab7117",
        "rows": 53,
    },
}
EXPECTED_SPLIT_ID = "97a707510227271d12859ee78defc0d6170cc24cb67e423568cd1a72e3345dee"
EXPECTED_TUPLE = "8ad320980bb36edb2accb38629ec3046095c9ef7735fbb748f4e112ee75bd388"
AUTHORITIES = {
    "arkitscenes": "7283761bf26c27570ec59a5dc0f8686fbff07726",
    "splatam": "da6bbcd24c248dc884ac7f49d62e91b841b26ccc",
    "rasterizer": "cb65e4b86bc3bd8ed42174b72a62e8d3a3a71110",
}
LEGACY = {
    "b2d66720fbb0bc7acc998a81e073a9e4774ece7e3ce2900651ff28bf921c2404",
    "670255f2e00f04a0e462e1a83cd4c4d0344e92906604aba9312aa7baabb3b78e",
}


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args])


def blob(repo: Path, commit: str, path: Path) -> tuple[str, bytes]:
    oid = git(repo, "rev-parse", f"{commit}:{path.as_posix()}").decode("ascii").strip()
    return oid, git(repo, "cat-file", "blob", oid)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def csv_identity(data: bytes) -> dict[str, Any]:
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is forbidden")
    text = data.decode("utf-8")
    crlf = data.count(b"\r\n")
    bare_cr = data.count(b"\r") - crlf
    rows = list(csv.reader(io.StringIO(text, newline="")))
    if not rows or any(len(row) != len(rows[0]) for row in rows[1:]) or any(not row for row in rows[1:]):
        raise ValueError("invalid canonical CSV structure")
    payload = {"fieldnames": rows[0], "ordered_rows": rows[1:]}
    semantic = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=False).encode("utf-8") + b"\n"
    return {
        "sha256": sha256(data), "semantic_sha256": sha256(semantic), "row_count": len(rows) - 1,
        "fieldnames": rows[0], "lf_count": data.count(b"\n"), "crlf_count": crlf,
        "bare_cr_count": bare_cr, "lf_only": crlf == 0 and bare_cr == 0,
        "no_bom": not data.startswith(b"\xef\xbb\xbf"), "final_lf": data.endswith(b"\n"),
        "rows": rows[1:],
    }


def compact_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--commit", default=PR70)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--platform", required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    out = args.output_root.resolve()
    failures: list[str] = []
    records: dict[str, Any] = {}
    parsed: dict[str, dict[str, Any]] = {}
    for name, expected in EXPECTED.items():
        oid, data = blob(repo, args.commit, expected["path"])
        identity = csv_identity(data)
        working = (repo / expected["path"]).read_bytes()
        checks = {
            "expected_oid": oid == expected["oid"], "expected_git_blob_sha256": identity["sha256"] == expected["sha256"],
            "expected_semantic_sha256": identity["semantic_sha256"] == expected["semantic_sha256"],
            "expected_row_count": identity["row_count"] == expected["rows"], "utf8_no_bom": identity["no_bom"],
            "lf_only": identity["lf_only"], "final_lf": identity["final_lf"], "working_tree_equals_blob": working == data,
        }
        for check, passed in checks.items():
            if not passed:
                failures.append(f"{name}:{check}")
        records[name] = {"path": expected["path"].as_posix(), "git_blob_oid": oid, **{key: identity[key] for key in ("sha256", "semantic_sha256", "row_count", "fieldnames", "lf_count", "crlf_count", "bare_cr_count", "lf_only", "no_bom", "final_lf")}, "working_tree_equals_blob": working == data, "checks": checks}
        parsed[name] = identity
    contract_path = V2 / "v2_split/arkitscenes_spatial_group_split_contract_v2.json"
    contract = json.loads(blob(repo, args.commit, contract_path)[1].decode("utf-8"))
    train_groups = {row[-2] for row in parsed["train"]["rows"]}
    heldout_groups = {row[-2] for row in parsed["heldout"]["rows"]}
    train_keys = {row[-4] for row in parsed["train"]["rows"]}
    heldout_keys = {row[-4] for row in parsed["heldout"]["rows"]}
    invariants = {
        "train_heldout_counts": (len(parsed["train"]["rows"]), len(parsed["heldout"]["rows"])) == (214, 53),
        "group_counts": (len(train_groups), len(heldout_groups)) == (8, 5), "overlap_zero": not (train_keys & heldout_keys),
        "cross_edge_zero": not (train_groups & heldout_groups), "discard_zero": len(train_keys | heldout_keys) == 267,
        "duplicate_zero": len(train_keys) == 214 and len(heldout_keys) == 53,
        "split_identity": contract.get("split_identity_sha256") == EXPECTED_SPLIT_ID,
        "selected_group_tuple": contract.get("selected_group_hash_tuple_sha256") == EXPECTED_TUPLE,
    }
    for check, passed in invariants.items():
        if not passed:
            failures.append(f"invariant:{check}")
    warnings: list[dict[str, str]] = []
    for path in repo.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        hashes = sorted(token for token in LEGACY if token in text)
        if hashes:
            warnings.append({"path": path.relative_to(repo).as_posix(), "legacy_hashes": ",".join(hashes), "classification": "NONCRITICAL_DERIVED_METADATA_WARNING"})
    status = "PASS_CANONICAL_MAPPING_INPUT_ROOT_IDENTITY" if not failures else "BLOCKED_BY_CANONICAL_MAPPING_INPUT_ROOT_IDENTITY"
    freeze = {"task": "RESTART_ARKITSCENES_SPLATAM_LEARNED_MAP_QUALIFICATION_FROM_CANONICAL_INPUT_FREEZE_V1", "platform": args.platform, "source_commit": args.commit, "frozen_pr68": PR68, "frozen_pr69": PR69, "frozen_pr70": PR70, "authority": AUTHORITIES, "manifest_records": records, "contract": {"split_identity_sha256": contract.get("split_identity_sha256"), "selected_group_hash_tuple_sha256": contract.get("selected_group_hash_tuple_sha256")}, "invariants": invariants, "status": status}
    validation = {"status": status, "hard_failures": failures, "git_blob_is_raw_authority": True, "working_tree_is_consistency_check_only": True, "linux_server_validation_required": args.platform != "linux_server", "invariants": invariants}
    compact_json(out / "canonical_mapping_input_freeze.json", freeze)
    compact_json(out / "canonical_mapping_input_validation.json", validation)
    compact_json(out / "noncritical_derived_metadata_warnings.json", {"status": "NONCRITICAL_DERIVED_METADATA_WARNING" if warnings else "NO_NONCRITICAL_DERIVED_METADATA_WARNING", "warnings": warnings})
    print(status)
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
