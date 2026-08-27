"""Freeze historical candidate-state-map rows before any L2 result exists."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

from replay_common import (
    DT, MAPS, PR87_ROOT, PR89_ROOT, PR90_ROOT, PR94_HEAD, PR94_ROOT, ROBOT_CONTRACT_SHA256,
    TASK_ROOT, candidate_numeric_hash, canonical_bytes, parse_bool, parse_float,
    parse_json_field, read_csv, read_json, relative, sha256_bytes, sha256_file,
    stable_row_id, vector_or_none, write_csv, write_json, write_jsonl,
)


def stored_l1(row: dict[str, str], candidate_id: str, selected: bool, rejected: dict[str, dict[str, Any]] | None = None) -> tuple[str, str]:
    if candidate_id != "PRIMARY-CBF-FILTERED":
        rejected = rejected or {}
        item = rejected.get(candidate_id)
        if selected:
            return "PASS", "STORED_HISTORICAL_SELECTED_AFTER_SEGMENT_GATE"
        if item is None:
            return "NOT_AVAILABLE", "CANDIDATE_LOGGED_NOT_EVALUATED"
        stage = str(item.get("stage", ""))
        reason = str(item.get("reason_code", ""))
        if stage == "SWEPT_SEGMENT_CERTIFICATION":
            return ("FAIL", "STORED_HISTORICAL_SEGMENT_REJECTION") if "UNSAFE" in reason else ("UNKNOWN", "STORED_HISTORICAL_SEGMENT_INCONCLUSIVE")
        if stage in {"BACKUP_CERTIFICATION", "TERMINAL_CERTIFICATION"}:
            return "PASS", "STORED_HISTORICAL_PASSED_SEGMENT_BEFORE_LATER_REJECTION"
        if stage == "CURRENT_FEASIBILITY_CHECK":
            return "NOT_REACHED", "STORED_HISTORICAL_CURRENT_GATE_REJECTION"
        return "NOT_AVAILABLE", "STORED_HISTORICAL_STAGE_UNRESOLVED"
    gate = str(row.get("segment_gate", "")).strip()
    if gate in {"PASS", "FAIL", "UNKNOWN"}:
        return gate, "STORED_HISTORICAL_NORMALIZED_SEGMENT_GATE"
    lower = parse_float(row.get("segment_lower_bound"))
    if lower is not None:
        return ("PASS", "STORED_HISTORICAL_SEGMENT_LOWER_BOUND") if lower >= 0.0 else ("FAIL", "STORED_HISTORICAL_SEGMENT_LOWER_BOUND")
    return "NOT_AVAILABLE", "STORED_HISTORICAL_SEGMENT_NOT_EVALUATED"


def replayability(row: dict[str, Any]) -> tuple[str, list[str]]:
    reasons = []
    for field in ("p_k", "v_k", "u_k"):
        value = row.get(field)
        if not isinstance(value, list) or len(value) != 3:
            reasons.append("MISSING_" + field.upper())
    if not row.get("candidate_id"):
        reasons.append("MISSING_CANDIDATE_IDENTITY")
    if not row.get("map_snapshot_id") or not row.get("map_content_sha256"):
        reasons.append("MISSING_MAP_AUTHORITY")
    if row.get("dt") != DT:
        reasons.append("INVALID_DT_IDENTITY")
    if row.get("backend_identity") is None:
        reasons.append("MISSING_BACKEND_CONTEXT")
    if reasons:
        if row.get("diagnostic_reconstructable"):
            return "DIAGNOSTIC_RECONSTRUCTABLE", reasons
        return "NOT_REPLAYABLE", reasons
    return "FORMAL_REPLAYABLE", []


def base_candidate(source: str, source_sha: str, environment: str, row: dict[str, str], registry: dict[str, Any] | None, ordinal: int) -> dict[str, Any]:
    if source == "PR87_ACTIVATED_ONE_STEP":
        p_k = vector_or_none(row.get("position_m")); v_k = vector_or_none(row.get("velocity_m_per_s"))
        cohort = row.get("cohort") or "ACTIVATED"
    else:
        state = None if registry is None else registry.get(row["state_id"])
        p_k = None if state is None else [float(v) for v in state["position_m"]]
        v_k = None if state is None else [float(v) for v in state["velocity_m_per_s"]]
        cohort = "REPRESENTATIVE_HOLDOUT"
    map_contract = MAPS.get(environment, {})
    candidate = vector_or_none(row.get("u_filtered"))
    selected_id = row.get("selected_candidate") or None
    selected = parse_bool(row.get("committed")) and selected_id == "PRIMARY-CBF-FILTERED"
    l1, l1_origin = stored_l1(row, "PRIMARY-CBF-FILTERED", selected)
    reached = True if l1 == "PASS" else False if l1 in {"FAIL", "NOT_REACHED"} else None
    result = {
        "source_kind": source,
        "source_file_sha256": source_sha,
        "source_row_ordinal": ordinal,
        "source_run_id": source,
        "trial_id": f"{environment}:{row.get('method')}:{row.get('state_id')}",
        "step_id": "ONE_STEP:0",
        "environment": environment,
        "cohort": cohort,
        "method": row.get("method"),
        "state_id": row.get("state_id"),
        "p_k": p_k,
        "v_k": v_k,
        "u_k": candidate,
        "dt": DT,
        "candidate_id": "PRIMARY-CBF-FILTERED" if candidate is not None else None,
        "candidate_id_origin": "STORED_HISTORICAL",
        "candidate_origin": "EXISTING_CBF_FILTERED",
        "candidate_role": "EXECUTED_OR_SELECTED_HISTORICAL_CANDIDATE" if selected else "LOGGED_NONEXECUTED_HISTORICAL_CANDIDATE",
        "candidate_numeric_hash": candidate_numeric_hash(candidate),
        "historically_committed": parse_bool(row.get("committed")),
        "historically_selected_candidate": selected_id,
        "map_snapshot_id": map_contract.get("snapshot_id"),
        "map_content_sha256": map_contract.get("content_sha256"),
        "map_authority_origin": map_contract.get("authority_origin"),
        "robot_margin_contract_sha256": ROBOT_CONTRACT_SHA256,
        "backend_identity": map_contract.get("backend_identity"),
        "backend_class": map_contract.get("backend_class"),
        "primitive_family": map_contract.get("primitive_family"),
        "query_context_identity": f"PR84:{map_contract.get('backend_identity')}",
        "stored_l1_status": l1,
        "stored_l1_origin": l1_origin,
        "l2_reached": reached,
        "l2_reachability_evidence": l1_origin,
        "diagnostic_reconstructable": False,
        "historical_semantic_status": row.get("semantic_status"),
        "historical_typed_reason": row.get("typed_reason"),
        "historical_segment_lower_bound": parse_float(row.get("segment_lower_bound")),
        "formal_attempt": parse_bool(row.get("formal_attempt")),
    }
    result["row_id"] = stable_row_id({key: result[key] for key in ("source_kind", "source_row_ordinal", "trial_id", "step_id", "candidate_id", "candidate_numeric_hash")})
    result["replayability_class"], result["replayability_reasons"] = replayability(result)
    result["primary_analysis_eligible"] = result["replayability_class"] == "FORMAL_REPLAYABLE" and reached is True
    return result


def alternatives(base: dict[str, Any], raw: dict[str, str]) -> list[dict[str, Any]]:
    slots = parse_json_field(raw.get("directional_slot_states")) or []
    rejected_rows = parse_json_field(raw.get("rejected_candidate_table")) or []
    rejected = {str(item.get("candidate_id")): item for item in rejected_rows}
    result = []
    for slot in slots:
        if slot.get("availability") != "AVAILABLE" or not slot.get("candidate_id"):
            continue
        candidate_id = str(slot["candidate_id"])
        candidate = vector_or_none(slot.get("acceleration"))
        selected = parse_bool(raw.get("committed")) and raw.get("selected_candidate") == candidate_id
        l1, l1_origin = stored_l1(raw, candidate_id, selected, rejected)
        reached = True if l1 == "PASS" else False if l1 in {"FAIL", "NOT_REACHED"} else None
        item = dict(base)
        item.update({
            "candidate_id": candidate_id,
            "candidate_id_origin": "STORED_HISTORICAL",
            "candidate_origin": slot.get("source"),
            "candidate_role": "EXECUTED_OR_SELECTED_HISTORICAL_CANDIDATE" if selected else "LOGGED_NONEXECUTED_HISTORICAL_CANDIDATE",
            "candidate_numeric_hash": candidate_numeric_hash(candidate),
            "u_k": candidate,
            "historically_committed": selected,
            "stored_l1_status": l1,
            "stored_l1_origin": l1_origin,
            "l2_reached": reached,
            "l2_reachability_evidence": l1_origin,
            "historical_rejection_stage": None if candidate_id not in rejected else rejected[candidate_id].get("stage"),
            "historical_rejection_reason": None if candidate_id not in rejected else rejected[candidate_id].get("reason_code"),
        })
        item["row_id"] = stable_row_id({"base": base["row_id"], "candidate_id": candidate_id, "candidate_numeric_hash": item["candidate_numeric_hash"]})
        item["replayability_class"], item["replayability_reasons"] = replayability(item)
        item["primary_analysis_eligible"] = item["replayability_class"] == "FORMAL_REPLAYABLE" and reached is True
        result.append(item)
    return result


def rollout_rows(source_sha: str) -> list[dict[str, Any]]:
    output = []
    path = PR87_ROOT / "benchmark/rollout_records.csv"
    for ordinal, raw in enumerate(read_csv(path), start=1):
        map_contract = MAPS["E1_REPLICA_GT_FINE"]
        item = {
            "source_kind": "PR87_REPLICA_ROLLOUT_STEP",
            "source_file_sha256": source_sha,
            "source_row_ordinal": ordinal,
            "source_run_id": "PR87_REPLICA_FORMAL_ROLLOUT",
            "trial_id": raw.get("episode_id"),
            "step_id": raw.get("step_index"),
            "environment": "E1_REPLICA_GT_FINE",
            "cohort": raw.get("cohort"),
            "method": raw.get("method"),
            "state_id": raw.get("state_id"),
            "p_k": vector_or_none(raw.get("position_before_m")),
            "v_k": vector_or_none(raw.get("velocity_before_m_per_s")),
            "u_k": None,
            "dt": DT,
            "candidate_id": raw.get("selected_candidate") or None,
            "candidate_id_origin": "STORED_ID_WITHOUT_NUMERIC_CANDIDATE",
            "candidate_origin": "ROLLOUT_EXECUTION_LOG",
            "candidate_role": "EXECUTED_OR_SELECTED_HISTORICAL_CANDIDATE",
            "candidate_numeric_hash": None,
            "historically_committed": parse_bool(raw.get("committed")),
            "historically_selected_candidate": raw.get("selected_candidate") or None,
            "map_snapshot_id": map_contract["snapshot_id"],
            "map_content_sha256": map_contract["content_sha256"],
            "map_authority_origin": "STATIC_TRIAL_MAP_CONTRACT",
            "robot_margin_contract_sha256": ROBOT_CONTRACT_SHA256,
            "backend_identity": map_contract["backend_identity"],
            "backend_class": map_contract["backend_class"],
            "primitive_family": map_contract["primitive_family"],
            "query_context_identity": "PR84:EXACT_ANALYTIC_SPHERE_SEGMENT_MINIMUM",
            "stored_l1_status": "NOT_AVAILABLE",
            "stored_l1_origin": "ROLLOUT_LOG_DID_NOT_STORE_CANDIDATE_VECTOR_OR_SEGMENT_CERTIFICATE",
            "l2_reached": None,
            "l2_reachability_evidence": "L2_REACHABILITY_UNKNOWN",
            "diagnostic_reconstructable": False,
            "historical_semantic_status": raw.get("semantic_status"),
            "historical_typed_reason": raw.get("step_terminal_reason"),
            "historical_segment_lower_bound": None,
            "formal_attempt": True,
        }
        item["row_id"] = stable_row_id({key: item[key] for key in ("source_kind", "source_row_ordinal", "trial_id", "step_id", "candidate_id")})
        item["replayability_class"], item["replayability_reasons"] = replayability(item)
        item["primary_analysis_eligible"] = False
        output.append(item)
    return output


def inventory_record(path: Path, role: str, disposition: str, contributes: bool) -> dict[str, Any]:
    rows = max(0, len(path.read_text(encoding="utf-8").splitlines()) - 1) if path.suffix == ".csv" else None
    return {
        "path": relative(path), "role": role, "sha256": sha256_file(path),
        "size": path.stat().st_size, "row_count": rows,
        "source_universe_disposition": disposition,
        "contributes_candidate_rows_to_N_all": contributes,
    }


def main() -> None:
    pr87_one = PR87_ROOT / "benchmark/one_step_records.csv"
    pr87_rollout = PR87_ROOT / "benchmark/rollout_records.csv"
    pr89_one = PR89_ROOT / "benchmark/one_step_records.csv"
    registry_paths = {environment: PR89_ROOT / "registry" / environment / "representative_registry.json" for environment in MAPS}
    registries = {environment: {item["state_id"]: item for item in read_json(path)["states"]} for environment, path in registry_paths.items()}
    rows: list[dict[str, Any]] = []
    sha87 = sha256_file(pr87_one); sha89 = sha256_file(pr89_one)
    for ordinal, raw in enumerate(read_csv(pr87_one), start=1):
        if raw.get("cohort") != "ACTIVATED":
            continue
        base = base_candidate("PR87_ACTIVATED_ONE_STEP", sha87, "E1_REPLICA_GT_FINE", raw, None, ordinal)
        rows.append(base)
        if raw.get("method") == "B3_FULL_UNIFIED_WITH_DIRECTIONAL_ALTERNATIVES":
            rows.extend(alternatives(base, raw))
    for ordinal, raw in enumerate(read_csv(pr89_one), start=1):
        environment = raw["environment"]
        if environment not in MAPS:
            continue
        base = base_candidate("PR89_NORMALIZED_ONE_STEP", sha89, environment, raw, registries[environment], ordinal)
        rows.append(base)
        if raw.get("method") == "B3_FULL_UNIFIED_WITH_DIRECTIONAL_ALTERNATIVES":
            rows.extend(alternatives(base, raw))
    rows.extend(rollout_rows(sha256_file(pr87_rollout)))
    rows.sort(key=lambda item: (item["source_kind"], int(item["source_row_ordinal"]), str(item["candidate_id"]), item["row_id"]))
    if len({row["row_id"] for row in rows}) != len(rows):
        raise RuntimeError("SOURCE_ROW_ID_COLLISION")

    inventory = [
        inventory_record(pr87_one, "PR87 activated and representative formal one-step records", "ACTIVATED_ROWS_INCLUDED; REPRESENTATIVE_ROWS_SUPERSEDED_BY_PR89", True),
        inventory_record(pr87_rollout, "PR87 frozen rollout steps", "INCLUDED_AS_REAL_HISTORICAL_ROWS_WITH_MISSING_NUMERIC_CANDIDATE", True),
        inventory_record(pr89_one, "PR89 normalized formal one-step records", "ALL_ROWS_INCLUDED", True),
        inventory_record(PR89_ROOT / "benchmark/natural_event_rollout_records.csv", "PR89 natural-event output", "EMPTY_SOURCE", False),
        inventory_record(PR90_ROOT / "diagnostic_design/bounded_state_selection.csv", "PR90 derived bounded diagnostic selection", "DERIVED_DUPLICATE_NO_NEW_TUPLE", False),
        inventory_record(PR90_ROOT / "factor_f04_b1_timing/shadow_segment_records.csv", "PR90 derived H1 formula endpoints", "DIAGNOSTIC_DERIVED_DUPLICATE_NO_CANDIDATE_VECTOR", False),
        inventory_record(PR90_ROOT / "factor_f06_b3_coverage/control_search_records.csv", "PR90 bounded candidate-search aggregate", "AGGREGATE_ONLY_NO_CANDIDATE_VECTORS", False),
        inventory_record(PR94_ROOT / "l2_h1_shadow_certifier.py", "Frozen PR94 shadow implementation", "IMPLEMENTATION_AUTHORITY_NOT_SOURCE_ROW", False),
    ]
    for environment, path in registry_paths.items():
        inventory.append(inventory_record(path, f"{environment} frozen state registry", "JOIN_AUTHORITY_NOT_ADDITIONAL_ROWS", False))

    class_counts = Counter(row["replayability_class"] for row in rows)
    reason_counts = Counter(reason for row in rows for reason in row["replayability_reasons"])
    inventory_json = {"status": "PASS_SOURCE_INVENTORY", "artifact_count": len(inventory), "artifacts": inventory}
    write_json(TASK_ROOT / "source_inventory.json", inventory_json)
    write_csv(TASK_ROOT / "source_inventory.csv", inventory)
    write_jsonl(TASK_ROOT / "frozen_replay_manifest.jsonl", rows)
    manifest_sha = sha256_file(TASK_ROOT / "frozen_replay_manifest.jsonl")
    universe_semantics = {
        "definition": "PR89 all normalized one-step candidate rows plus PR87 activated one-step rows not represented in PR89, expanded only with logged available B3 directional candidates, plus PR87 frozen rollout-step rows retained as genuine historical rows even when the numeric candidate is absent",
        "deduplication": "PR87 representative one-step rows are superseded by byte-identified PR89 normalized records; PR90 derived diagnostics add no rows",
        "N_all": len(rows),
        "class_counts_before_replay": dict(sorted(class_counts.items())),
        "precall_missingness_reason_counts": dict(sorted(reason_counts.items())),
        "manifest_sha256": manifest_sha,
        "source_inventory_sha256": sha256_file(TASK_ROOT / "source_inventory.json"),
        "pr94_head": PR94_HEAD,
        "differential_sample_selection_rule": "first 8 primary-analysis-eligible rows per backend identity after stable sort by row_id",
        "determinism_repetition_contract": "two complete passes over every primary-analysis-eligible manifest row",
        "replay_execution_started": False,
        "l2_result_field_count": 0,
        "historical_replay_manifest_count": 1,
        "replay_cohort_definition_count": 1,
        "new_data_collection_count": 0,
        "synthetic_state_generation_count": 0,
        "synthetic_candidate_generation_count": 0,
        "map_generation_count": 0,
    }
    write_json(TASK_ROOT / "source_universe_freeze.json", {
        **universe_semantics,
        "source_universe_semantic_sha256": sha256_bytes(canonical_bytes(universe_semantics)),
        "status": "PASS_SOURCE_UNIVERSE_FROZEN_BEFORE_REPLAY",
    })
    audit_rows = []
    for row in rows:
        audit_rows.append({
            "row_id": row["row_id"], "source_kind": row["source_kind"],
            "environment": row["environment"], "trial_id": row["trial_id"],
            "candidate_id": row["candidate_id"], "candidate_role": row["candidate_role"],
            "replayability_class": row["replayability_class"],
            "replayability_reasons": "|".join(row["replayability_reasons"]),
            "l2_reached": row["l2_reached"],
            "l2_reachability_evidence": row["l2_reachability_evidence"],
            "primary_analysis_eligible": row["primary_analysis_eligible"],
        })
    write_csv(TASK_ROOT / "replayability_audit.csv", audit_rows)
    write_csv(TASK_ROOT / "architecture_reachability_audit.csv", audit_rows)
    write_csv(TASK_ROOT / "replayability_reason_breakdown.csv", [
        {"replayability_class": key, "reason": reason, "count": count}
        for (key, reason), count in sorted(Counter((row["replayability_class"], reason or "NONE") for row in rows for reason in (row["replayability_reasons"] or [None])).items())
    ])
    print("PASS_SOURCE_UNIVERSE_FROZEN_BEFORE_REPLAY", len(rows), manifest_sha)


if __name__ == "__main__":
    main()
