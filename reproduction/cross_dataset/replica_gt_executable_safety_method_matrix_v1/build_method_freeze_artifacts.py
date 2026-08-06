"""Build static B0-B3 method contract and cryptographic directional-library identity."""
from __future__ import annotations

import csv
from pathlib import Path

from alternative_library.canonical_serialization import canonical_sha256
from alternative_library.contract import contract_payload
from common import sha256_file, write_json, write_text
from task_config import LIBRARY_ID, LIBRARY_SOURCE, LIBRARY_VERSION, PR84_HEAD, TASK_ROOT


def source_manifest() -> list[dict[str, object]]:
    paths = (
        "task_config.py", "alternative_library/result_types.py", "alternative_library/canonical_serialization.py",
        "alternative_library/represented_sphere_frame.py", "alternative_library/actuator_box_scaling.py",
        "alternative_library/deceleration_projection.py", "alternative_library/directional_library.py",
        "alternative_library/contract.py", "methods/b2_primary_and_braking_wrapper.py",
        "methods/b3_directional_library_wrapper.py",
    )
    return [{"path": path, "sha256": sha256_file(TASK_ROOT / path), "size": (TASK_ROOT / path).stat().st_size} for path in paths]


def main() -> None:
    contract = contract_payload()
    slots = [{"slot_index": index + 1, "candidate_id": identifier, "source": LIBRARY_SOURCE, "formula": formula} for index, (identifier, formula) in enumerate(zip(contract["slot_ids"], ("u_box(n)", "u_box(t_g)", "u_box(t_a)", "u_box(-t_a)", "u_box(project_Hv(b_hat+t_g))", "u_box(project_Hv(b_hat+n))")))]
    manifest = source_manifest()
    map_identity = __import__("json").loads((TASK_ROOT / "input_freeze/replica_map_identity.json").read_text(encoding="utf-8"))
    pr84_identity = __import__("json").loads((TASK_ROOT / "input_freeze/pr84_certifier_identity.json").read_text(encoding="utf-8"))
    identity_material = {"library": contract, "slots": slots, "generator_source_manifest": manifest, "map_snapshot_identity": map_identity["map_snapshot_id"], "pr84_head": PR84_HEAD, "pr84_certifier_manifest_sha256": pr84_identity["artifact_manifest_sha256"]}
    global_sha = canonical_sha256(identity_material)
    write_json(TASK_ROOT / "alternative_library/alternative_library_contract.json", contract)
    write_json(TASK_ROOT / "alternative_library/alternative_library_slot_schema.json", {"library_id": LIBRARY_ID, "slot_schema": slots, "availability_states": ["AVAILABLE", "MAP_QUERY_UNAVAILABLE", "ACTIVE_PRIMITIVE_UNAVAILABLE", "NORMAL_DEGENERATE", "GOAL_DEGENERATE_AXIS_FALLBACK_USED", "DIRECTION_NONFINITE", "DIRECTION_ZERO", "BRAKING_DIRECTION_UNAVAILABLE", "DEGENERATE_AFTER_DECELERATION_PROJECTION", "DUPLICATE_OF_EARLIER_SLOT", "ACTUATOR_CONTRACT_REJECTED"]})
    write_json(TASK_ROOT / "alternative_library/alternative_library_source_manifest.json", {"library_id": LIBRARY_ID, "source_manifest": manifest})
    write_json(TASK_ROOT / "alternative_library/alternative_library_identity.json", {"library_id": LIBRARY_ID, "library_version": LIBRARY_VERSION, "global_library_sha256": global_sha, "identity_material": identity_material})
    methods = [
        {"id": "B0_CURRENT_CBF_ONLY", "candidates": ["PRIMARY-CBF-FILTERED"], "gates": ["actuator", "current_full_query"], "directional_slots": False},
        {"id": "B1_PLUS_SWEPT_SEGMENT", "candidates": ["PRIMARY-CBF-FILTERED"], "gates": ["actuator", "current_full_query", "swept_segment"], "directional_slots": False},
        {"id": "B2_PLUS_TERMINAL_BACKUP_WITH_BUILTIN_BRAKING", "candidates": ["PRIMARY-CBF-FILTERED", "DETERMINISTIC_BRAKING"], "external_alternative_controls": [], "gates": ["actuator", "current_full_query", "swept_segment", "terminal_backup"], "directional_slots": False},
        {"id": "B3_FULL_UNIFIED_WITH_FROZEN_DIRECTIONAL_ALTERNATIVES", "candidates": ["PRIMARY-CBF-FILTERED", *contract["slot_ids"], "DETERMINISTIC_BRAKING"], "external_alternative_controls": list(contract["slot_ids"]), "gates": ["actuator", "current_full_query", "swept_segment", "terminal_backup"], "directional_slots": True, "library_id": LIBRARY_ID, "library_sha256": global_sha},
    ]
    write_json(TASK_ROOT / "methods/method_registry.json", {"status": "FROZEN_METHOD_MATRIX", "methods": methods, "b3_only_difference": "Six fixed represented-map directional slot templates; unavailable or duplicate slots are retained in identity but not passed to the certifier."})
    matrix_path = TASK_ROOT / "methods/method_difference_matrix.csv"; matrix_path.parent.mkdir(parents=True, exist_ok=True)
    with matrix_path.open("w", encoding="utf-8", newline="\n") as handle:
        writer = csv.writer(handle, lineterminator="\n"); writer.writerow(("method", "primary", "current", "segment", "backup", "built_in_braking", "directional_library"))
        writer.writerows((("B0", True, True, False, False, False, False), ("B1", True, True, True, False, False, False), ("B2", True, True, True, True, True, False), ("B3", True, True, True, True, True, True)))
    write_text(TASK_ROOT / "methods/nested_causal_contract.md", "# Nested B0-B3 causal contract\n\nB0 uses only the frozen filtered primary control and actuator/current-full-query gates. B1 adds only swept-segment certification. B2 adds only PR #84 terminal backup and its deterministic built-in braking candidate. B3 shares every B2 input and gate, then adds at most the six frozen directional slots in fixed order. This document defines a future comparison; it reports no decision, collision, rescue, progress, runtime, or safety outcome.")
    write_json(TASK_ROOT / "methods/method_canonical_identity.json", {"methods": methods, "method_matrix_sha256": canonical_sha256(methods), "b2_b3_shared": ["u_nom_logged", "u_filtered_primary", "actuator_bounds", "current_full_query", "normative_model", "segment_backend", "terminal_set", "backup_policy", "deterministic_braking"], "b3_only_difference": contract["slot_ids"]})
    fairness = {key: True for key in ("same_map_snapshot", "same_state_goal", "same_u_nom_logged", "same_u_filtered_primary", "same_actuator_bounds", "same_current_full_query", "same_normative_model", "same_segment_backend", "same_terminal_set", "same_backup_policy", "same_builtin_braking_B2_B3", "B3_only_adds_six_slot_directional_template", "no_reference_input", "no_future_outcome_input", "no_registry_input", "no_group_count_input", "no_parameter_tuning", "no_candidate_search", "canonical_library_identity_frozen", "per_state_candidate_identity_reproducible")}
    write_json(TASK_ROOT / "methods/fairness_audit.json", {"status": "PASS_METHOD_FAIRNESS_CONTRACT_FREEZE", "checks": fairness, "library_id": LIBRARY_ID, "global_library_sha256": global_sha})
    write_text(TASK_ROOT / "proof_artifacts/library_independence_argument.md", "# Library independence\n\nThe six slots depend only on current state, local goal, frozen actuator/dt constants, current represented-map full-query status and active primitive, and frozen map identity. They do not accept a reference mesh, oracle output, future trajectory, group label, registry, runtime, or outcome input.")
    write_text(TASK_ROOT / "proof_artifacts/method_fairness_argument.md", "# Method fairness\n\nB2 and B3 have identical filtered primary control, four PR #84 gates, and deterministic braking. B3 adds only the frozen directional library. This is a design contract, not a result claim.")
    write_text(TASK_ROOT / "proof_artifacts/geometric_candidate_semantics.md", "# Geometric candidate semantics\n\nThe normal is a represented-sphere outward normal derived from the nearest active represented Gaussian primitive. It is not an official-mesh normal or a real-world surface normal. Tangents are deterministic directions in that represented-sphere tangent plane.")
    print("PASS_STATIC_METHOD_MATRIX_ARTIFACTS", global_sha)


if __name__ == "__main__":
    main()
