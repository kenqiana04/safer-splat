#!/usr/bin/env python3
"""Shared deterministic primitives for the formal collection harness."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterator

DATA_ROLE = "FORMAL_PROSPECTIVE_SHADOW_COHORT_V1"
PROTOCOL_SHA256 = "e8ea8f3fda15ab81664829ea6f71fcb37f772ad613c13f61007856c16117791a"
MAP_AUTHORITY_ID = "65c2e4a5ccfd71a0fa8d633c207397215dd8206d5f8fb77a731c05bcb0109af3"
EXPECTED_UPSTREAM_HEAD = "84cf0734bafd52ddc7b100686fb0d1f509f1e356"
OFFICIAL100_SHA256 = "1b236bba8173c8a37fb7752fd2e2f09fc569191d6820089759b4be547bd6c344"

CAPTURE_SEMANTIC_KEYS = (
    "schema_version", "run_id", "trial_id", "step_id", "state_sequence_id",
    "decision_commit_id", "x_k", "p_k", "v_k", "dt", "selected_candidate",
    "native_sibling_candidates", "candidate_group_id", "native_candidate_group_size",
    "reachability", "map_authority_id", "controller_authority", "execution_authority",
    "candidate_selection_authority", "intervention", "shadow_only",
)
RESULT_SEMANTIC_KEYS = (
    "l0_status", "l0_reason", "l0_observation_source", "l1_status", "l1_reason",
    "l1_observation_source", "l2_reached", "l2_reachability_reason", "l2_status",
    "l2_reason", "backend_identity",
)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def semantic_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: JSONL row is not an object")
            yield value


def formal_run_id(trial_id: int, attempt_id: int) -> str:
    if trial_id not in range(100) or attempt_id not in (0, 1):
        raise ValueError("formal trial/attempt outside preregistered range")
    return f"formal-v1-trial-{trial_id:03d}-attempt-{attempt_id}"


def verify_execution_lock(lock_path: Path, script_dir: Path) -> dict[str, Any]:
    lock = load_json(lock_path)
    if lock.get("schema_version") != "L2_H1_COLLECTION_EXECUTION_LOCK_V1":
        raise RuntimeError("execution lock schema mismatch")
    if lock.get("protocol_sha256") != PROTOCOL_SHA256 or lock.get("upstream_head") != EXPECTED_UPSTREAM_HEAD:
        raise RuntimeError("execution lock upstream/protocol mismatch")
    expected_combined = lock.get("collection_execution_lock_sha256")
    unhashed = dict(lock)
    unhashed.pop("collection_execution_lock_sha256", None)
    unhashed.pop("combined_collection_execution_sha256", None)
    if expected_combined != semantic_sha256(unhashed) or lock.get("combined_collection_execution_sha256") != expected_combined:
        raise RuntimeError("execution lock deterministic combined hash mismatch")
    for name, expected in lock.get("task_script_sha256", {}).items():
        actual = file_sha256(script_dir / name)
        if actual != expected:
            raise RuntimeError(f"execution-locked script drift: {name}")
    return lock
