#!/usr/bin/env python3
"""Non-scientific V1.1 packaging correction before the first rollout.

The completed geometry outputs are preserved on the server.  This script only
removes accidentally embedded raw sample arrays from compact summaries and
adds the already-frozen transform positions required by the registry contract.
It neither queries the map nor changes selected pair IDs/order.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path("/disk1/zlab/maintenance_records/tum_splatam_direct_safe_baseline_gate_v1_1")
TRANSFORMS = Path("/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room/transforms.json")


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def compact(value: object) -> object:
    if isinstance(value, dict):
        return {key: compact(item) for key, item in value.items() if key != "samples"}
    if isinstance(value, list):
        return [compact(item) for item in value]
    return value


def main() -> None:
    positions = [[frame["transform_matrix"][0][3], frame["transform_matrix"][1][3], frame["transform_matrix"][2][3]] for frame in json.loads(TRANSFORMS.read_text(encoding="utf-8"))["frames"]]
    for relative in ("dense_qualification/dense_direct_path_qualification_summary_v1_1.json", "float64_certification/float64_direct_pair_certification_summary_v1_1.json"):
        path = ROOT / relative
        write_json(path, compact(json.loads(path.read_text(encoding="utf-8"))))
    path = ROOT / "frozen_rollout_registry/frozen_direct_safe_rollout_registry_v1_1.json"
    registry = compact(json.loads(path.read_text(encoding="utf-8")))
    frozen_pairs_before = [(row["label"], row["start_frame"], row["goal_frame"], row["hash_order"]) for row in registry["registry"]]
    if registry.get("registry_packaging_correction") is None:
        for row in registry["registry"]:
            row["start_position"] = positions[row["start_frame"]]
            row["goal_position"] = positions[row["goal_frame"]]
        registry["registry_pre_enrichment_sha256"] = registry.get("registry_sha256")
        registry["registry_packaging_correction"] = "positions_added_and_raw_samples_removed_before_first_rollout; pair_ids_and_order_unchanged"
        registry["registry_sha256"] = None
        registry["registry_sha256"] = hashlib.sha256(json.dumps(registry, indent=2, sort_keys=True).encode("utf-8")).hexdigest()
    elif any("start_position" not in row or "goal_position" not in row for row in registry["registry"]):
        raise RuntimeError("INCOMPLETE_PREVIOUS_REGISTRY_PACKAGING_CORRECTION")
    frozen_pairs_after = [(row["label"], row["start_frame"], row["goal_frame"], row["hash_order"]) for row in registry["registry"]]
    if frozen_pairs_before != frozen_pairs_after:
        raise RuntimeError("FROZEN_PAIR_MUTATION_FORBIDDEN")
    write_json(path, registry)
    manifest_path = ROOT / "manifests/run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if any(entry["state"] != "NOT_STARTED" for entry in manifest["states"].values()):
        raise RuntimeError("MANIFEST_ALREADY_STARTED_CANNOT_BE_PACKAGING_CORRECTED")
    for row in registry["registry"]:
        manifest["states"][row["label"]]["pair"] = row
    write_json(manifest_path, manifest)
    print(registry["registry_sha256"])


if __name__ == "__main__":
    main()
