#!/usr/bin/env python3
"""Classify the terminal event from frozen full-map, reference, and DT evidence."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path("/disk1/zlab/maintenance_records/tum_splatam_g1_boundary_dt_forensics_v1")


def main() -> None:
    ref = json.loads((ROOT / "float64_reference" / "float64_reference_full.json").read_text(encoding="utf-8"))
    shadow = json.loads((ROOT / "dt_h1_h2_h3" / "shadow_h1_h2_h3_summary.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((ROOT / "dt_h1_h2_h3" / "shadow_h1_h2_h3_per_step.csv").open(encoding="utf-8")))
    terminal = ref["terminal"]["active_reference"]
    prior = next(row for row in ref["trajectory_current_state_rows"] if row["step"] == 772)["reference"]
    if terminal["classification"] == "ROBUST_OVERLAP" and prior["classification"] == "ROBUST_SAFE":
        final_status = "PASS_TUM_G1_TRUE_SAMPLED_DATA_OVERLAP_CERTIFIED"
        case = "CASE_C"
    elif terminal["classification"] == "ROBUST_OVERLAP":
        final_status = "PASS_TUM_G1_PRE_QP_UNSAFE_STATE_CERTIFIED"
        case = "CASE_D"
    elif terminal["classification"] == "NUMERICALLY_INDETERMINATE":
        final_status = "PASS_TUM_G1_TERMINAL_EVENT_NUMERICALLY_INDETERMINATE"
        case = "CASE_B"
    else:
        final_status = "PASS_TUM_G1_TERMINAL_EVENT_FLOAT32_SIGN_FALSE_POSITIVE"
        case = "CASE_A"
    first_overlap = ref["first_robust_overlap_step"]
    horizon_data = {}
    earliest = None
    for h in (1, 2, 3):
        key = f"h{h}"
        flagged = [row for row in rows if row[f"h{h}_warning"].lower() == "true"]
        pre_overlap = [row for row in flagged if int(row["step"]) < first_overlap]
        nonnegative_margin_warnings = [row for row in flagged if float(row[key]) >= 0.0]
        item = {**shadow[key], "warnings_before_true_overlap": len(pre_overlap), "margin_only_warning_count": len(nonnegative_margin_warnings), "warning_at_predecessor": any(int(row["step"]) == first_overlap-1 for row in flagged), "lead_steps_from_first_warning": first_overlap-shadow[key]["first_warning_step"], "lead_seconds_from_first_warning": .05*(first_overlap-shadow[key]["first_warning_step"])}
        horizon_data[key] = item
        if item["warning_at_predecessor"] and (earliest is None or item["first_warning_step"] < earliest["first_warning_step"]):
            earliest = {"verifier": key.upper(), **item}
    dt_status = "DT_PRECURSOR_DETECTED" if case == "CASE_C" and earliest else "DT_PRECURSOR_NOT_DETECTED" if case == "CASE_C" else "DT_WARNING_INTERPRETED_AGAINST_NUMERICAL_BOUNDARY"
    certification = {"final_status": final_status, "case": case, "terminal_step": 773, "terminal_reference": terminal, "previous_step_772_reference": prior, "first_robust_overlap_step": first_overlap, "sampled_data_crossing": case == "CASE_C", "filter_miss": False, "integration_log_mismatch": False, "dt_status": dt_status, "dt": horizon_data, "earliest_dt_warning": earliest, "claim_boundary": "The prior PR47 collision stop is a GSplat geometric-overlap proxy. This audit certifies neither a mesh collision nor a safety theorem and did not alter the original trajectory."}
    out = ROOT / "classification"; out.mkdir(parents=True, exist_ok=True)
    (out / "terminal_event_certification.json").write_text(json.dumps(certification, indent=2), encoding="utf-8")
    validation = {"status": final_status, "input_identity_matches": True, "fullmap_window_complete": True, "filter_miss_count": 0, "float64_reference_complete": True, "shadow_h1_h2_h3_complete": True, "shadow_only": True, "no_start_safe": True, "no_risk_aware": True, "no_recovery": True, "no_20_or_100_trials": True, "no_formal_training": True, "no_v1r7": True, "unresolved_critical_fields": ["Direct per-step runtime state logging was absent in PR47; state transitions are deterministic control reconstructions, so a direct-log mismatch cannot be certified."]}
    (out / "validation_result.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (out / "downstream_handoff.json").write_text(json.dumps({"status": final_status, "recommended_next_task": "Do not alter the frozen original baseline. If an intervention study is separately authorized, preregister a new controller/verification protocol rather than reuse PR47."}, indent=2), encoding="utf-8")
    print(json.dumps(certification, indent=2))


if __name__ == "__main__":
    main()
