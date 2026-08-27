"""Independent calculation and claim-support QA for the replay artifacts."""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
import json
from pathlib import Path

from replay_common import TASK_ROOT, read_json, write_json


def read_jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (TASK_ROOT / name).read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    manifest = read_jsonl("frozen_replay_manifest.jsonl")
    results = read_jsonl("replay_results.jsonl")
    denominator = read_json(TASK_ROOT / "denominator_audit.json")
    increment = read_json(TASK_ROOT / "l2_information_increment_summary.json")
    multi = read_json(TASK_ROOT / "multi_candidate_summary.json")
    checks = {}
    manifest_ids = [row["row_id"] for row in manifest]
    result_ids = [row["row_id"] for row in results]
    eligible = {
        row["row_id"] for row in manifest
        if row["replayability_class"] == "FORMAL_REPLAYABLE" and row["l2_reached"] is True and row["primary_analysis_eligible"] is True
    }
    replayability = Counter(row["replayability_class"] for row in manifest)
    statuses = Counter(row["status"] for row in results)
    checks["manifest_row_ids_unique"] = len(manifest_ids) == len(set(manifest_ids))
    checks["result_row_ids_unique"] = len(result_ids) == len(set(result_ids))
    checks["result_set_equals_predefined_primary_set"] = set(result_ids) == eligible
    checks["replayability_partition"] = sum(replayability.values()) == len(manifest)
    checks["N_all_recomputed"] = denominator["N_all"] == len(manifest) == 6853
    checks["N_formal_recomputed"] = denominator["N_formal_replayable"] == replayability["FORMAL_REPLAYABLE"] == 2594
    checks["N_not_replayable_recomputed"] = denominator["N_not_replayable"] == replayability["NOT_REPLAYABLE"] == 4259
    checks["evaluated_recomputed"] = denominator["N_L2_candidate_evaluated"] == len(results) == 788
    checks["status_partition_recomputed"] = (statuses["PASS"], statuses["FAIL"], statuses["UNKNOWN"]) == (770, 18, 0)
    checks["all_results_architecture_reached"] = all(row["l2_reached"] is True and row["primary_analysis_eligible"] is True for row in results)
    checks["not_replayable_never_called"] = not (set(result_ids) & {row["row_id"] for row in manifest if row["replayability_class"] == "NOT_REPLAYABLE"})
    checks["stored_l1_increment_recomputed"] = sum(row["stored_l1_status"] == "PASS" and row["status"] == "FAIL" for row in results) == increment["N_L1_PASS_L2_FAIL"] == 18
    checks["unknown_rate_denominator_recomputed"] = increment["N_L1_PASS_L2_UNKNOWN"] == 0
    checks["controller_authority_zero"] = all(row["controller_authority"] is False and row["controller_intervention"] is False for row in results)
    checks["endpoint_fallback_zero"] = all(row["endpoint_fallback_enabled"] is False for row in results)
    checks["candidate_inputs_preserved"] = all(len(row["u_k"]) == 3 and len(row["p_k1"]) == 3 and len(row["p_k2"]) == 3 for row in results)
    checks["determinism_pass"] = read_json(TASK_ROOT / "replay_determinism_audit.json")["status"] == "PASS_REPLAY_DETERMINISM"
    checks["differential_pass"] = read_json(TASK_ROOT / "replay_differential_integrity_audit.json")["status"] == "PASS_REPLAY_DIFFERENTIAL_INTEGRITY"
    with (TASK_ROOT / "multi_candidate_group_analysis.csv").open(encoding="utf-8", newline="") as handle:
        multi_rows = list(csv.DictReader(handle))
    checks["multi_candidate_group_count_recomputed"] = len(multi_rows) == multi["N_multi_candidate_state_groups"] == 20
    checks["multi_candidate_disagreement_recomputed"] = sum(row["has_L2_status_disagreement"].lower() == "true" for row in multi_rows) == multi["N_groups_with_L2_status_disagreement"] == 0
    checks["case_A_supported_by_increment"] = read_json(TASK_ROOT / "FINAL_CASE_DECISION.json")["selected_case"] == "CASE_A" and increment["N_L1_PASS_L2_FAIL"] > 0
    report_text = (TASK_ROOT / "report/REPORT_VALIDATE_L2_H1_SHADOW_CERTIFIER_ON_FROZEN_REPLAY_V1.md").read_text(encoding="utf-8")
    checks["report_has_required_negative_claims"] = all(token in report_text for token in ("Collision prevented?** **NO", "Any new candidate?** **NO", "On-policy/navigation experiment run?** **NO"))
    checks["selection_bias_prominent"] = "PASS_WITH_EXPLICIT_SOURCE_AND_MISSINGNESS_BIAS" in (TASK_ROOT / "selection_bias_audit.md").read_text(encoding="utf-8")
    failed = sorted(key for key, value in checks.items() if not value)
    write_json(TASK_ROOT / "audit/analysis_validation_report.json", {
        "skill_workflow": "data-analytics:validate-data",
        "overall_assessment": "READY_TO_SHARE_WITH_EXPLICIT_CAVEATS" if not failed else "NEEDS_REVISION",
        "question_validated": "Whether frozen historical evidence supports a replayable, deterministic, candidate-dependent L2/H1 information increment without control-performance claims",
        "calculation_spot_checks": checks,
        "failed_checks": failed,
        "required_caveats": [
            "The replayable and architecture-reached subsets are source- and missingness-selected.",
            "The 18 L1 PASS/L2 FAIL rows are offline certificate signals, not prevented collisions or improved closed-loop performance.",
            "No on-policy observation or controller authority occurred.",
        ],
        "blockers": [],
    })
    if failed:
        raise RuntimeError("ANALYSIS_QA_FAILED:" + ",".join(failed))
    print("PASS_INDEPENDENT_ANALYSIS_QA", len(checks))


if __name__ == "__main__":
    main()
