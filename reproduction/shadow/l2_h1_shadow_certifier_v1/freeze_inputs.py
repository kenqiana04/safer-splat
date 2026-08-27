"""Freeze and verify the authoritative PR #93 and PR #84 identities."""
from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

from shadow_contract import (
    CONSERVATIVE_ELLIPSOID_IDENTITY,
    DENSE_DIAGNOSTIC_IDENTITY,
    EXACT_SPHERE_IDENTITY,
    FROZEN_BACKEND_BLOBS,
    FROZEN_BACKEND_ROOT,
    PR84_HEAD,
    PR93_BASE,
    PR93_BRANCH,
    PR93_HEAD,
    REPO_ROOT,
    SPEC_ROOT,
    TASK_ROOT,
    load_frozen_robot_margin_contract,
)

AUDIT_ROOT = TASK_ROOT / "audit"
EXPECTED_PRS = {
    83: "17805e67b75412dc21b1a5fff4143ea3bc985f7f",
    84: PR84_HEAD,
    86: "d4f20f44a810afc2d6379853a286a3e18b175221",
    87: "fbe67f0c607add7f8049d4ce75e8f9e1ae8498d9",
    89: "047513b5e612f91e63ab1e7054815615cb455fd7",
    90: "48db34d4e61f019fcd2b578c04cc87eefb00747a",
    91: "e8ec67d5585f9634ae6a5d4991eac5f9e4abfbae",
    92: "dfd9bce2633e542fdb72a1805f79cc4feeeebc3a",
    93: PR93_HEAD,
}


def run(*args: str, text: bool = True) -> str | bytes:
    completed = subprocess.run(args, cwd=REPO_ROOT, check=True, capture_output=True, text=text, timeout=30)
    return completed.stdout if not text else completed.stdout.strip()


def query_pr(number: int) -> dict[str, Any]:
    command = (
        "gh", "pr", "view", str(number), "--repo", "kenqiana04/safer-splat",
        "--json", "number,state,isDraft,baseRefName,headRefName,headRefOid,url",
    )
    last_error: Exception | None = None
    for attempt in range(1, 9):
        try:
            return json.loads(str(run(*command)))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < 8:
                time.sleep(2)
    raise RuntimeError(f"GITHUB_PR_QUERY_FAILED:{number}:{type(last_error).__name__}")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_record(commit: str, path: str) -> dict[str, Any]:
    line = str(run("git", "ls-tree", commit, "--", path))
    if not line:
        raise RuntimeError(f"MISSING_GIT_PATH:{commit}:{path}")
    metadata, actual_path = line.split("\t", 1)
    mode, object_type, blob = metadata.split()
    if object_type != "blob" or actual_path != path:
        raise RuntimeError(f"NON_BLOB_GIT_PATH:{commit}:{path}")
    data = run("git", "cat-file", "blob", blob, text=False)
    assert isinstance(data, bytes)
    return {"commit": commit, "path": path, "mode": mode, "git_blob": blob, "size": len(data), "sha256": sha256(data)}


def freeze_upstream() -> dict[str, Any]:
    records = []
    for number, expected in EXPECTED_PRS.items():
        record = query_pr(number)
        if record["headRefOid"] != expected or record["state"] != "OPEN" or record["isDraft"] is not True:
            raise RuntimeError(f"UPSTREAM_PR_IDENTITY_DRIFT:{number}")
        if number == 93 and (record["baseRefName"] != PR93_BASE or record["headRefName"] != PR93_BRANCH):
            raise RuntimeError("PR93_BASE_OR_BRANCH_DRIFT")
        record["expected_head"] = expected
        record["verification"] = "PASS_EXACT_OPEN_DRAFT_IDENTITY"
        records.append(record)
    if str(run("git", "rev-parse", PR93_BRANCH)) != PR93_HEAD:
        raise RuntimeError("LOCAL_PR93_IDENTITY_DRIFT")
    return {"status": "PASS_L2_H1_SHADOW_UPSTREAM_IDENTITY", "upstream_pr_count": len(records), "records": records}


def freeze_protected() -> dict[str, Any]:
    source = json.loads((SPEC_ROOT / "PROTECTED_SOURCE_AUDIT.json").read_text(encoding="utf-8"))
    expected_count = int(source["protected_blob_count"])
    records = []
    paths = []
    for frozen in source["protected_records"]:
        actual = git_blob_record(frozen["commit"], frozen["path"])
        for key in ("git_blob", "size", "sha256"):
            if actual[key] != frozen[key]:
                raise RuntimeError(f"PROTECTED_{key.upper()}_DRIFT:{frozen['path']}")
        actual["role"] = frozen["role"]
        actual["verification"] = "PASS_RAW_GIT_OBJECT_SIZE_MODE_IDENTITY"
        records.append(actual)
        paths.append(frozen["path"])
    if len(records) != expected_count:
        raise RuntimeError("PROTECTED_MANIFEST_COUNT_DRIFT")
    changed = str(run("git", "diff", "--name-only", PR93_HEAD, "--", *paths)).splitlines()
    changed = [item for item in changed if item]
    if changed:
        raise RuntimeError("PROTECTED_PATH_MUTATION:" + ",".join(changed))
    return {
        "status": "PASS_L2_H1_SHADOW_PROTECTED_SOURCE_AUDIT",
        "manifest_authority": (SPEC_ROOT / "PROTECTED_SOURCE_AUDIT.json").relative_to(REPO_ROOT).as_posix(),
        "protected_blob_count": len(records),
        "protected_path_diff_count": 0,
        "records": records,
    }


def freeze_specification() -> dict[str, Any]:
    names = [
        "CORE_V2_L2_H1_CAUSAL_INCREMENT_SPECIFICATION_V1.md",
        "H1_SEGMENT_CONTRACT.md",
        "L2_PREDICATE_CONTRACT.md",
        "control_authority_h1_derivation.json",
        "continuous_segment_semantics_audit.json",
        "map_safety_semantics_audit.json",
        "SUPPORTED_AND_PROHIBITED_CLAIMS.md",
        "FINAL_CASE_DECISION.json",
    ]
    records = []
    for name in names:
        path = (SPEC_ROOT / name).relative_to(REPO_ROOT).as_posix()
        record = git_blob_record(PR93_HEAD, path)
        worktree = (REPO_ROOT / path).read_bytes()
        diff = str(run("git", "diff", "--name-only", PR93_HEAD, "--", path))
        if diff:
            raise RuntimeError(f"SPECIFICATION_GIT_CONTENT_DRIFT:{path}")
        record["worktree_sha256"] = sha256(worktree)
        record["worktree_size"] = len(worktree)
        record["checkout_transform_detected"] = (
            record["sha256"] != record["worktree_sha256"] or record["size"] != record["worktree_size"]
        )
        record["identity_authority"] = "RAW_GIT_BLOB"
        record["verification"] = "PASS_PR93_RAW_GIT_IDENTITY"
        records.append(record)
    derivation = json.loads((SPEC_ROOT / "control_authority_h1_derivation.json").read_text(encoding="utf-8"))
    if derivation["normative_model"] != "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1":
        raise RuntimeError("NORMATIVE_MODEL_DRIFT")
    return {
        "status": "PASS_FROZEN_PR93_SPECIFICATION_IDENTITY",
        "pr": 93,
        "head": PR93_HEAD,
        "normative_model": derivation["normative_model"],
        "symbolic_equations": derivation["symbolic_equations"],
        "candidate_dependence_verdict": derivation["candidate_dependence_verdict"],
        "records": records,
    }


def freeze_backend_symbols() -> dict[str, Any]:
    if str(FROZEN_BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(FROZEN_BACKEND_ROOT))
    from certifier.result_types import SegmentCertificate, SegmentStatus
    from certifier.segment_backends.analytic_primitive import ExactSphereSegmentBackend
    from certifier.segment_backends.conservative_interval import ConservativeSignedDistanceIntervalBackend
    from certifier.segment_backends.sampled_diagnostic import SampledDiagnosticBackend

    symbols = [
        (
            "certifier.segment_backends.analytic_primitive.ExactSphereSegmentBackend.certify",
            ExactSphereSegmentBackend,
            "certify",
            EXACT_SPHERE_IDENTITY,
            "EXACT_ANALYTIC",
            "FORMAL",
            "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/segment_backends/analytic_primitive.py",
        ),
        (
            "certifier.segment_backends.conservative_interval.ConservativeSignedDistanceIntervalBackend.certify",
            ConservativeSignedDistanceIntervalBackend,
            "certify",
            CONSERVATIVE_ELLIPSOID_IDENTITY,
            "CONSERVATIVE_LOWER_BOUND",
            "FORMAL",
            "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/segment_backends/conservative_interval.py",
        ),
        (
            "certifier.segment_backends.sampled_diagnostic.SampledDiagnosticBackend.diagnose",
            SampledDiagnosticBackend,
            "diagnose",
            DENSE_DIAGNOSTIC_IDENTITY,
            "DIAGNOSTIC_ONLY",
            "DIAGNOSTIC_ONLY",
            "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/segment_backends/sampled_diagnostic.py",
        ),
    ]
    records = []
    for qualified, cls, callable_name, identity, classification, authority, path in symbols:
        record = git_blob_record(PR84_HEAD, path)
        if record["git_blob"] != FROZEN_BACKEND_BLOBS[qualified]:
            raise RuntimeError(f"FROZEN_BACKEND_BLOB_DRIFT:{qualified}")
        if getattr(cls, "method") != identity:
            raise RuntimeError(f"FROZEN_BACKEND_SEMANTIC_IDENTITY_DRIFT:{qualified}")
        records.append({
            **record,
            "module": cls.__module__,
            "class": cls.__name__,
            "callable": callable_name,
            "qualified_symbol": qualified,
            "signature": str(inspect.signature(getattr(cls, callable_name))),
            "semantic_identity": identity,
            "classification": classification,
            "authority": authority,
            "return_type": SegmentCertificate.__name__,
            "status_type": SegmentStatus.__name__,
            "verification": "PASS_FROZEN_CALLABLE_AND_RAW_GIT_IDENTITY",
        })
    return {"status": "PASS_FROZEN_BACKEND_SYMBOL_MAP", "adapter_only": True, "new_geometry_primitive_count": 0, "records": records}


def main() -> None:
    AUDIT_ROOT.mkdir(parents=True, exist_ok=True)
    upstream = freeze_upstream()
    protected = freeze_protected()
    specification = freeze_specification()
    symbols = freeze_backend_symbols()
    robot = load_frozen_robot_margin_contract()
    map_contract_record = next(
        record for record in specification["records"]
        if record["path"].endswith("/map_safety_semantics_audit.json")
    )
    if robot.contract_sha256 != map_contract_record["sha256"]:
        raise RuntimeError("ROBOT_MARGIN_RAW_CONTRACT_IDENTITY_DRIFT")
    map_audit = json.loads((SPEC_ROOT / "map_safety_semantics_audit.json").read_text(encoding="utf-8"))
    write_json(AUDIT_ROOT / "frozen_upstream_identity.json", upstream)
    write_json(AUDIT_ROOT / "protected_source_audit.json", protected)
    write_json(AUDIT_ROOT / "frozen_specification_identity.json", specification)
    write_json(AUDIT_ROOT / "frozen_backend_symbol_map.json", symbols)
    write_json(AUDIT_ROOT / "robot_margin_contract.json", {"status": "PASS_FROZEN_ROBOT_MARGIN_CONTRACT", **robot.to_dict()})
    write_json(AUDIT_ROOT / "map_snapshot_contract.json", {
        "status": "PASS_MAP_SNAPSHOT_CONTRACT",
        "authority": map_audit["authority"],
        "expected_actual_identity_required": True,
        "snapshot_mismatch_mapping": "L2_UNKNOWN",
        "map_hash_mismatch_mapping": "L2_UNKNOWN",
        "map_unavailable_mapping": "L2_UNKNOWN",
        "stale_snapshot_mapping": "L2_UNKNOWN",
        "query_context_unresolved_mapping": "L2_UNKNOWN",
        "physical_world_truth_claim": False,
    })
    print("PASS_L2_H1_SHADOW_INPUT_FREEZE")


if __name__ == "__main__":
    main()
