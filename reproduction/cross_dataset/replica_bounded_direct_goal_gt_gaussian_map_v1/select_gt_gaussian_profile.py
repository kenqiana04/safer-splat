#!/usr/bin/env python3
"""Select exactly one qualifying profile using only frozen static gate evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def passed(path: Path) -> bool:
    return json.loads(path.read_text(encoding="utf-8")).get("status") == "PASS"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--profile-dir", type=Path, required=True)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--determinism", type=Path, required=True)
    parser.add_argument("--resource", type=Path, required=True)
    parser.add_argument("--free-space", type=Path, required=True)
    parser.add_argument("--g0", type=Path, required=True)
    parser.add_argument("--robot-contract", type=Path, required=True)
    parser.add_argument("--bounded-qp", type=Path, required=True)
    parser.add_argument("--routes", type=Path, required=True)
    parser.add_argument("--start-states", type=Path, required=True)
    parser.add_argument("--mesh-oracle", type=Path, required=True)
    parser.add_argument("--integration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    summary = json.loads((args.profile_dir / "profile_build_summary.json").read_text(encoding="utf-8"))
    evidence = {
        "voxelization_resource": args.resource,
        "mesh_coverage": args.coverage,
        "determinism": args.determinism,
        "free_space": args.free_space,
        "safer_g0": args.g0,
        "static_integration": args.integration,
    }
    checks = {name: passed(path) for name, path in evidence.items()}
    checks["profile_summary"] = summary.get("status") == "PASS"
    checks["profile_matches_requested"] = summary.get("profile") == args.profile
    allowed = all(checks.values())
    arrays = {
        name: {"sha256": sha256(args.profile_dir / name), "bytes": (args.profile_dir / name).stat().st_size}
        for name in (
            "means_world_m.npy", "scales_linear_m.npy", "quaternions_wxyz.npy",
            "opacities_probability.npy", "colors_rgb.npy", "voxel_indices_int64.npy",
        )
    }
    result = {
        "status": "PASS" if allowed else "FAIL",
        "dataset": "Replica",
        "scene": "apartment_0",
        "selected_profile": args.profile,
        "selection_rule": "coarsest profile passing voxelization, coverage, determinism, resource, free-space, static G0, and static integration gates",
        "profile_order": ["COARSE", "MEDIUM", "FINE"],
        "voxel_size_m": summary["voxel_size_m"],
        "gaussian_count": summary["resource"]["gaussian_count"],
        "canonical_tree_sha256": summary["canonical_tree_sha256"],
        "canonical_arrays": arrays,
        "evidence": {name: {"path": str(path), "sha256": sha256(path)} for name, path in evidence.items()},
        "robot_contract_sha256": sha256(args.robot_contract),
        "bounded_qp_adapter_contract_sha256": sha256(args.bounded_qp),
        "route_registry_sha256": sha256(args.routes),
        "start_safe_registry_sha256": sha256(args.start_states),
        "mesh_oracle_validation_sha256": sha256(args.mesh_oracle),
        "map_role": "CERTIFIED_GT_GEOMETRY_DERIVED_GAUSSIAN_SAFETY_MAP",
        "claims": {
            "learned_3dgs": False,
            "reconstructed_3dgs": False,
            "mapping_frontend_generalization_evidence": False,
            "gaussian_primitives_are": "deterministic conservative safety geometry",
            "formal_multistep_navigation_executed": False,
        },
        "gate_checks": checks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"GT_GAUSSIAN_PROFILE_SELECTION_{result['status']} profile={args.profile}")
    return 0 if allowed else 3


if __name__ == "__main__":
    raise SystemExit(main())
