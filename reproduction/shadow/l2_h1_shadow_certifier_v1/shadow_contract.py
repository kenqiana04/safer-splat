"""Frozen PR #93 identities and non-tunable shadow contract loader."""
from __future__ import annotations

import json
import math
from pathlib import Path

from shadow_types import RobotMarginContract

CONTRACT_VERSION = "L2_H1_SHADOW_CERTIFIER_V1"
LOG_SCHEMA_VERSION = "L2_H1_SHADOW_LOG_SCHEMA_V1"
NORMATIVE_MODEL = "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1"
PR93_HEAD = "1df09c56eedb53d46f9347695026086319738a89"
PR93_BRANCH = "core-v2-causal-increment-specification-v1"
PR93_BASE = "core-causal-architecture-specification-v1"
PR84_HEAD = "04ebca2b1b35124ad0e61ebed96e491c9edae4bb"

TASK_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TASK_ROOT.parents[2]
SPEC_ROOT = REPO_ROOT / "reproduction/specification/core_v2_causal_increment_specification_v1"
FROZEN_BACKEND_ROOT = REPO_ROOT / "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1"
MAP_CONTRACT_PATH = SPEC_ROOT / "map_safety_semantics_audit.json"
MAP_CONTRACT_RAW_GIT_BLOB = "df275faa516979d3ed86dcfbd99cf69198425b1d"
MAP_CONTRACT_RAW_SHA256 = "5fad9c0773673ead60cd3f5229525d01a8fdf563de070f06dceecff190b8b223"

EXACT_SPHERE_IDENTITY = "EXACT_ANALYTIC_SPHERE_SEGMENT_MINIMUM"
CONSERVATIVE_ELLIPSOID_IDENTITY = "CONSERVATIVE_SIGNED_DISTANCE_LIPSCHITZ_INTERVAL"
DENSE_DIAGNOSTIC_IDENTITY = "DENSE_SAMPLED_DIAGNOSTIC_ONLY"
FORMAL_BACKEND_CLASSES = {
    EXACT_SPHERE_IDENTITY: "EXACT_ANALYTIC",
    CONSERVATIVE_ELLIPSOID_IDENTITY: "CONSERVATIVE_LOWER_BOUND",
}
DIAGNOSTIC_BACKENDS = {DENSE_DIAGNOSTIC_IDENTITY: "DIAGNOSTIC_ONLY"}
ENDPOINT_FALLBACK_ENABLED = False
FORMAL_THRESHOLD = 0.0

FROZEN_BACKEND_BLOBS = {
    "certifier.segment_backends.analytic_primitive.ExactSphereSegmentBackend.certify": "68d9c94cedf444379c262c550dd80e9c289ea843",
    "certifier.segment_backends.conservative_interval.ConservativeSignedDistanceIntervalBackend.certify": "cd011939dc9cc00e1997dc855c4212810c3be9f1",
    "certifier.segment_backends.sampled_diagnostic.SampledDiagnosticBackend.diagnose": "2421d73e0667e5a396450056fbfb93403cebc055",
}


def load_frozen_robot_margin_contract() -> RobotMarginContract:
    data = json.loads(MAP_CONTRACT_PATH.read_text(encoding="utf-8"))
    if data.get("robot_footprint") != "ball radius 0.10 m":
        raise RuntimeError("ROBOT_RADIUS_CONTRACT_DRIFT")
    if data.get("fixed_safety_margin") != "0.01 m":
        raise RuntimeError("SAFETY_MARGIN_CONTRACT_DRIFT")
    if data.get("effective_radius") != "0.11 m":
        raise RuntimeError("EFFECTIVE_RADIUS_CONTRACT_DRIFT")
    if not math.isclose(float(data.get("segment_margin_rho_seg")), 0.0, rel_tol=0.0, abs_tol=0.0):
        raise RuntimeError("RHO_SEG_CONTRACT_DRIFT")
    return RobotMarginContract(
        robot_radius_m=0.10,
        margin_m=0.01,
        effective_radius_m=0.11,
        rho_seg=0.0,
        contract_sha256=MAP_CONTRACT_RAW_SHA256,
        source_path=MAP_CONTRACT_PATH.relative_to(REPO_ROOT).as_posix(),
    )


def robot_margin_contract_matches(contract: RobotMarginContract) -> bool:
    try:
        frozen = load_frozen_robot_margin_contract()
    except Exception:
        return False
    return contract == frozen
