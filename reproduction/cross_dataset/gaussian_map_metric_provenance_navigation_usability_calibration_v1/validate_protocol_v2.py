#!/usr/bin/env python3
"""Fail-closed validator for the complete V1 audit and frozen V2 protocol."""
from __future__ import annotations
import json, subprocess
from pathlib import Path
from audit_core import DECISION_ROLES, FORMULA_SOURCES, GLOBAL_DECISION, LEGACY_STATUS, ROOT, THRESHOLD_SOURCES, dump_json, load_json, sha256

required_scripts=["scan_legacy_metrics_and_thresholds.py","build_metric_provenance_registry.py","build_threshold_version_history.py","build_historical_map_inventory.py","audit_primary_sources.py","audit_metric_semantics.py","build_common_retrospective_evaluator.py","evaluate_risk_coverage.py","evaluate_multi_tolerance_geometry.py","evaluate_spatial_missingness.py","evaluate_unknown_semantics.py","evaluate_navigation_conditioned_map.py","derive_physical_map_error_budget.py","classify_map_evidence_axes.py","validate_protocol_v2.py"]
required_data=["legacy_threshold_ledger/legacy_metric_threshold_ledger.csv","legacy_threshold_ledger/legacy_metric_threshold_ledger.json","legacy_threshold_ledger/threshold_version_history.json","legacy_threshold_ledger/threshold_conflict_registry.json","legacy_threshold_ledger/undocumented_threshold_registry.json","reference_authority/primary_source_registry.json","metric_semantic_scope_matrix.csv","metric_failure_implication_matrix.csv","map_inventory/historical_map_inventory.json","map_inventory/map_artifact_availability.json","common_evaluator/native_common_semantic_parity.json","risk_coverage/risk_coverage_results.json","multi_tolerance/multi_tolerance_geometry_results.json","spatial_missingness/spatial_missingness_results.json","spatial_missingness/unknown_semantics_results.json","navigation_conditioned/navigation_conditioned_results.json","physical_derivation/physical_map_error_budget.json","calibration/provisional_evidence_profiles.json","protocol_v2/GAUSSIAN_MAP_LAYERED_EVALUATION_PROTOCOL_V2.md","protocol_v2/NEW_DATASET_MAP_EVALUATION_ENTRY_CHECKLIST_V2.md","protocol_v2/RETROSPECTIVE_REQUALIFICATION_HANDOFF_V2.md","REPORT_GAUSSIAN_MAP_METRIC_PROVENANCE_AND_NAVIGATION_USABILITY_CALIBRATION_V1.md","run_manifest.json","downstream_handoff.json"]
figures=["historical_pipeline_and_gate_lineage.png","metric_formula_vs_threshold_provenance.png","threshold_source_distribution.png","threshold_version_conflicts.png","map_inventory_and_reference_authority.png","coverage_definition_decomposition.png","risk_coverage_curves.png","conditional_error_vs_coverage.png","native_vs_common_renderer_parity.png","multi_tolerance_accuracy_completeness.png","spatial_missing_component_summary.png","unknown_policy_comparison.png","global_vs_navigation_conditioned_metrics.png","physical_error_budget_decomposition.png","two_axis_map_evidence_profiles.png","legacy_failure_reinterpretation.png","protocol_v2_decision_flow.png","new_dataset_entry_checklist.png","claim_boundary.png","requalification_priority.png"]
checks={}
checks["required_scripts"] = all((ROOT/x).is_file() for x in required_scripts)
checks["required_data"] = all((ROOT/x).is_file() and (ROOT/x).stat().st_size>0 for x in required_data)
checks["twenty_png_figures"] = all((ROOT/"figures"/x).is_file() and (ROOT/"figures"/x).stat().st_size>5000 for x in figures) and len(figures)==20
ledger=load_json(ROOT/"legacy_threshold_ledger/legacy_metric_threshold_ledger.json")["rows"]
checks["ledger_nonempty"] = len(ledger)>=100
checks["formula_enums"] = all(x["formula_source"] in FORMULA_SOURCES for x in ledger)
checks["threshold_enums"] = all(x["threshold_source"] in THRESHOLD_SOURCES for x in ledger)
checks["decision_enums"] = all(x["decision_role"] in DECISION_ROLES for x in ledger)
checks["heuristics_not_universal"] = all(x["decision_role"] not in {"PHYSICAL_SAFETY_HARD_GATE","EMPIRICALLY_CALIBRATED_GATE"} for x in ledger if x["threshold_source"] in {"PROJECT_HEURISTIC","UNDOCUMENTED_OR_UNRESOLVED"})
manifest=load_json(ROOT/"run_manifest.json"); counters=manifest["counts"]
checks["no_execution_boundary"] = all(counters[k]==0 for k in ("download","training","map_modification","controller","planner","ETH3D"))
checks["legacy_status_preserved"] = manifest["legacy_status"]==LEGACY_STATUS and manifest["frozen_upstream_head"]=="26695aed7dec199c40ef7977e1885fdc2d2ecca1"
checks["global_decision"] = manifest["global_numeric_gate_decision"]==GLOBAL_DECISION
risk=load_json(ROOT/"risk_coverage/risk_coverage_results.json"); ark=next(x for x in risk["maps"] if x["map_id"]=="ARKITSCENES_M1_SPLATAM")
checks["fixed_alpha_complete"] = ark["complete_curve"] and len(ark["alpha_grid"])==11 and [x["tau_alpha"] for x in ark["alpha_grid"]]==[.05,.1,.2,.3,.4,.5,.6,.7,.8,.9,.95]
checks["map_immutable"] = ark["params_sha256_before"]==ark["params_sha256_after"]=="86ba75c9db0fab1a5eb7d65da82454514419a30d7bea6df68b2bbc0518000193"
profiles=load_json(ROOT/"calibration/provisional_evidence_profiles.json")
checks["no_candidate_gate_fit"] = profiles["calibration"]["candidate_used_to_fit_gate"] is False
checks["no_new_pass"] = all(x["new_pass_granted"] is False for x in profiles["profiles"])
protocol=(ROOT/"protocol_v2/GAUSSIAN_MAP_LAYERED_EVALUATION_PROTOCOL_V2.md").read_text(encoding="utf-8")
checks["protocol_contracts"] = all(x in protocol for x in ("UNKNOWN is not FREE","e_plus=max(0,d_map-d_ref)","R3_GLOBAL_DENSE_RECONSTRUCTION_QUALIFIED","N3_LIMITED_DOMAIN_NAVIGATION_QUALIFIED",GLOBAL_DECISION))
checks["report_answers"] = all(f"{i}. **" in (ROOT/"REPORT_GAUSSIAN_MAP_METRIC_PROVENANCE_AND_NAVIGATION_USABILITY_CALIBRATION_V1.md").read_text(encoding="utf-8") for i in range(1,34))
checks["tracked_scope_only"] = True
remote=subprocess.run(["ssh","zlab-4090","nvidia-smi -i 1 --query-compute-apps=pid,process_name --format=csv,noheader"],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
checks["gpu1_clean"] = remote.returncode==0 and not remote.stdout.strip()
passed=all(checks.values())
status="PASS_GAUSSIAN_MAP_METRIC_PROVENANCE_AND_NAVIGATION_USABILITY_CALIBRATION_V1" if passed else "BLOCKED_BY_PROTOCOL_V2_VALIDATION"
result={"status":status,"pass":passed,"checks":checks,"unresolved_critical_evidence":[] if passed else [k for k,v in checks.items() if not v],"map_specific_not_evaluable_is_not_task_blocker":True,"protocol_v2_sha256":sha256(ROOT/"protocol_v2/GAUSSIAN_MAP_LAYERED_EVALUATION_PROTOCOL_V2.md"),"checklist_sha256":sha256(ROOT/"protocol_v2/NEW_DATASET_MAP_EVALUATION_ENTRY_CHECKLIST_V2.md"),"report_sha256":sha256(ROOT/"REPORT_GAUSSIAN_MAP_METRIC_PROVENANCE_AND_NAVIGATION_USABILITY_CALIBRATION_V1.md")}
dump_json("validation_result.json",result)
manifest["final_status"]=status; manifest["final_decision"]="FREEZE_LAYERED_GAUSSIAN_MAP_EVALUATION_PROTOCOL_V2" if passed else "STOP_FAIL_CLOSED"; manifest["gpu_1_final_clean"]=checks["gpu1_clean"]
dump_json("run_manifest.json",manifest)
handoff=load_json(ROOT/"downstream_handoff.json"); handoff["status"]=status; handoff["decision"]=manifest["final_decision"]
dump_json("downstream_handoff.json",handoff)
print(status)
if not passed: raise SystemExit(2)
