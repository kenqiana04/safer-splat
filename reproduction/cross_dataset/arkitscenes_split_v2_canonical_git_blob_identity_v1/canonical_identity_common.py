"""Shared byte and semantic identity helpers for the ARKitScenes V2 correction."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path
from typing import Any


PR68 = "9f068e1708e7422e3e53c01c96fa29242be35f0a"
PR69 = "dabaa0bbf44cd81783c3c00d0744f44affaffcb2"
V2_ROOT = Path("reproduction/cross_dataset/arkitscenes_spatial_group_split_contract_v2")
CORRECTION_ROOT = Path("reproduction/cross_dataset/arkitscenes_split_v2_canonical_git_blob_identity_v1")
TRAIN_RELATIVE = V2_ROOT / "v2_split/arkitscenes_train_manifest_v2.csv"
HELDOUT_RELATIVE = V2_ROOT / "v2_split/arkitscenes_heldout_manifest_v2.csv"
CONTRACT_RELATIVE = V2_ROOT / "v2_split/arkitscenes_spatial_group_split_contract_v2.json"
SELECTED_RELATIVE = V2_ROOT / "v2_split/selected_arkitscenes_mapping_scene_v2.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes())


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=False) + "\n").encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args], input=input_bytes)


def git_blob(repo: Path, commit: str, relative: Path) -> tuple[str, bytes]:
    target = f"{commit}:{relative.as_posix()}"
    oid = git(repo, "rev-parse", target).decode("ascii").strip()
    return oid, git(repo, "cat-file", "blob", oid)


def git_file(repo: Path, commit: str, relative: Path) -> bytes:
    return git(repo, "show", f"{commit}:{relative.as_posix()}")


def decode_utf8_no_bom(data: bytes) -> str:
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is forbidden")
    return data.decode("utf-8")


def eol_profile(data: bytes) -> dict[str, Any]:
    decode_utf8_no_bom(data)
    crlf = data.count(b"\r\n")
    bare_cr = data.count(b"\r") - crlf
    lf = data.count(b"\n")
    return {
        "utf8_decode": "PASS",
        "bom": False,
        "lf_count": lf,
        "crlf_count": crlf,
        "bare_cr_count": bare_cr,
        "lf_only": crlf == 0 and bare_cr == 0,
        "final_lf": data.endswith(b"\n"),
    }


def semantic_csv_identity(data: bytes) -> dict[str, Any]:
    text = decode_utf8_no_bom(data)
    reader = csv.reader(io.StringIO(text, newline=""))
    rows = list(reader)
    if not rows:
        raise ValueError("CSV is empty")
    fieldnames = rows[0]
    ordered_rows = rows[1:]
    if any(len(row) != len(fieldnames) for row in ordered_rows):
        raise ValueError("CSV row field count differs from frozen header")
    if any(not row for row in ordered_rows):
        raise ValueError("CSV contains a blank row")
    payload = {"fieldnames": fieldnames, "ordered_rows": ordered_rows}
    return {
        "semantic_csv_sha256": sha256(canonical_json_bytes(payload)),
        "fieldnames": fieldnames,
        "row_count": len(ordered_rows),
        "payload": payload,
    }


def lf_to_crlf(data: bytes) -> bytes:
    profile = eol_profile(data)
    if not profile["lf_only"]:
        raise ValueError("input must be LF-only before deterministic LF-to-CRLF conversion")
    return data.replace(b"\n", b"\r\n")


def file_tree_sha256(files: list[Path], root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        name = path.relative_to(root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(name).to_bytes(8, "big")); digest.update(name)
        digest.update(len(payload).to_bytes(8, "big")); digest.update(payload)
    return digest.hexdigest()


def exact_csv_record(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    semantic = semantic_csv_identity(data)
    return {
        "path": path.as_posix(),
        "sha256": sha256(data),
        "encoding": "UTF-8",
        "eol": eol_profile(data),
        "semantic_csv_sha256": semantic["semantic_csv_sha256"],
        "row_count": semantic["row_count"],
        "fieldnames": semantic["fieldnames"],
    }
