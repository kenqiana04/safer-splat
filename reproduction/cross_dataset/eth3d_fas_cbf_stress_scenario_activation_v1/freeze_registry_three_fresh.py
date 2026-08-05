#!/usr/bin/env python3
"""Build V2 registry in three fresh processes and freeze byte-identical output."""
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from task_config_v2 import (  # noqa: F401
    MAP_PLY,
    TASK_ROOT,
    V1_REGISTRY,
    atomic_json,
    sha256_file,
)


def build_selected_stage_table(registry: dict, output: Path) -> None:
    fields = (
        "scenario_id",
        "group",
        "candidate_id",
        "generation_source",
        "reason_codes",
        "reference_valid",
        "reference_clearance_lower_bound_m",
        "s1_classification",
        "s1_projection_attempted",
        "s1_projection_success",
        "s2_m1_qp_feasible",
        "s2_m2_qp_feasible",
        "s2_h2_dominance_active",
        "s2_original_constraint_population",
        "s2_reduced_constraint_population",
        "s3_trigger_type",
        "s3_verifier_trigger",
        "s3_endpoint_only_miss",
        "s3_unavoidable_immediate_segment",
        "s4_recovery_trigger",
        "s4_recovery_recoverable",
    )
    temporary = output.with_suffix(output.suffix + ".tmp")
    output.parent.mkdir(parents=True, exist_ok=True)
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for scenario in registry["scenarios"]:
            shadow = scenario["shadow_stage_reachability"]
            s1 = shadow.get("S1", {})
            s2 = shadow.get("S2", {})
            s3 = shadow.get("S3", {})
            s4 = shadow.get("S4", {})
            writer.writerow(
                {
                    "scenario_id": scenario["scenario_id"],
                    "group": scenario["group"],
                    "candidate_id": scenario["candidate_id"],
                    "generation_source": shadow.get("generation_source"),
                    "reason_codes": "|".join(shadow.get("reason_codes", [])),
                    "reference_valid": shadow.get("reference_valid"),
                    "reference_clearance_lower_bound_m": shadow.get(
                        "reference_clearance_lower_bound_m"
                    ),
                    "s1_classification": s1.get("classification"),
                    "s1_projection_attempted": s1.get("projection_attempted"),
                    "s1_projection_success": s1.get("projection_success"),
                    "s2_m1_qp_feasible": s2.get("m1_qp_feasible"),
                    "s2_m2_qp_feasible": s2.get("m2_qp_feasible"),
                    "s2_h2_dominance_active": s2.get("H2_DOMINANCE_ACTIVE"),
                    "s2_original_constraint_population": s2.get(
                        "original_constraint_population"
                    ),
                    "s2_reduced_constraint_population": s2.get(
                        "reduced_constraint_population"
                    ),
                    "s3_trigger_type": s3.get("trigger_type"),
                    "s3_verifier_trigger": s3.get("verifier_trigger"),
                    "s3_endpoint_only_miss": s3.get("endpoint_only_miss"),
                    "s3_unavoidable_immediate_segment": s3.get(
                        "unavoidable_immediate_segment"
                    ),
                    "s4_recovery_trigger": s4.get("recovery_trigger"),
                    "s4_recovery_recoverable": s4.get("recovery_recoverable"),
                }
            )
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, output)


def main() -> int:
    root = TASK_ROOT / "scenario_registry_v2"
    builder = Path(__file__).with_name("build_scenario_registry_v2.py")
    map_sha_before = sha256_file(MAP_PLY)
    v1_sha_before = sha256_file(V1_REGISTRY)
    fresh_paths: list[Path] = []
    process_records: list[dict] = []
    for ordinal in range(1, 4):
        output = root / f"fresh_{ordinal}" / "scenario_registry.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            [sys.executable, "-B", str(builder), "--output", str(output)],
            cwd=Path(__file__).parent,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            text=True,
            capture_output=True,
            check=False,
        )
        process_records.append(
            {
                "fresh_process": ordinal,
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        )
        if completed.returncode != 0:
            raise RuntimeError(process_records[-1])
        fresh_paths.append(output)
    raw_hashes = [sha256_file(path) for path in fresh_paths]
    raw_bytes = [path.read_bytes() for path in fresh_paths]
    if len(set(raw_hashes)) != 1 or not all(value == raw_bytes[0] for value in raw_bytes):
        raise RuntimeError(f"fresh registry mismatch: {raw_hashes}")
    if sha256_file(MAP_PLY) != map_sha_before or sha256_file(V1_REGISTRY) != v1_sha_before:
        raise RuntimeError("frozen map or V1 registry identity changed")

    locked = root / "scenario_registry.json"
    shutil.copyfile(fresh_paths[0], locked)
    registry = json.loads(locked.read_text(encoding="utf-8"))
    build_selected_stage_table(
        registry, TASK_ROOT / "stage_reachability" / "stage_reachability_table.csv"
    )
    result = {
        "status": "PASS_THREE_FRESH_PROCESS_REGISTRY_FREEZE",
        "fresh_process_count": 3,
        "all_raw_bytes_identical": True,
        "fresh_raw_sha256": raw_hashes,
        "locked_raw_sha256": sha256_file(locked),
        "locked_logical_sha256": registry["registry_sha256"],
        "scenario_count": len(registry["scenarios"]),
        "map_sha256_before_after": [map_sha_before, sha256_file(MAP_PLY)],
        "v1_registry_raw_sha256_before_after": [
            v1_sha_before,
            sha256_file(V1_REGISTRY),
        ],
        "process_records": process_records,
    }
    atomic_json(root / "registry_fresh_process_determinism.json", result)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
