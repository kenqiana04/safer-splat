#!/usr/bin/env python3
"""Shared immutable source definitions and deterministic writers for evidence assembly."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
BASE_HEAD = "e9bf932143542232400b451e3fa6caa888ae3a85"
PR80_HEAD = "a05f8e1eca4c400a86583eb97fcce5be32062a0d"
PR79_HEAD = "4694a7cbfa062a53ac270c1c1c5654a2d1b5f166"
REPLICA_HEAD = "fcb9b54541e331d5981ba9dfc8132313fb5cd429"
RISK_REPORT_HEAD = "d77a0633d0c46c8be8ae1abf0e91c756271334a2"
TUM_FORENSICS_HEAD = "3d66958914c662ed635f3b0d401371e6cd5673c2"
TUM_V4C_HEAD = "519478a541ab114e7877b365b93e54a0b049e119"

ETH3D_MAP_SHA = "927734a2339a3f2710640065b0893eaae162cc0144ac67e2f377bcff2e71ae34"
ETH3D_TREE_SHA = "06c1ff17d2ed5eb184b6a9699a3a32da431a1460840431a3effe76d5f03b9ee3"
ETH3D_MESH_SHA = "82a9b20c9f3c7dc933f86c45e0855adf649fcf08b7549baba760cf385d489370"
ETH3D_METHOD_SHA = "41fc7363fecbf2e65cc1e25233d5ea9f5fa6581fe3b1eb6a81505806d0376193"
ETH3D_BASELINE_SHA = "9df7fa1945631cdb0b65b70568661c7eaaa75ff847bfe6f951241e56205d0bb2"

SOURCE_SPECS: list[dict[str, Any]] = [
    {"evidence_id": "E01_ETH3D_PR80", "module": "M-G", "dataset": "ETH3D", "scene": "Delivery Area", "map_role": "LEARNED_3DGS", "source_pr": "PR #80", "branch": "eth3d-single-map-fas-cbf-module-stress-benchmark-v1", "commit": PR80_HEAD, "report_path": "reproduction/cross_dataset/eth3d_single_map_fas_cbf_module_stress_benchmark_v1/report/REPORT_TRAIN_ONE_ETH3D_3DGS_MAP_AND_RUN_FAS_CBF_MODULE_STRESS_BENCHMARK_V1.md", "sample_unit": "scenario-method terminal record", "sample_count": 500, "comparator": "M0–M4 shared 100-scenario registry", "result_type": "formal", "polarity": "structural", "activity": "formal", "domain": "external", "allowed_claims": "One learned 3DGS map passed minimum controller viability; its PR80 stress registry did not activate all modules.", "prohibited_claims": "Learned-map deployment safety or Full FAS-CBF superiority.", "unresolved_fields": "No sufficiently activated paired full-stack cohort."},
    {"evidence_id": "E02_ETH3D_PR81", "module": "M-H", "dataset": "ETH3D", "scene": "Delivery Area", "map_role": "LEARNED_3DGS", "source_pr": "PR #81", "branch": "eth3d-fas-cbf-stress-scenario-activation-v1", "commit": BASE_HEAD, "report_path": "reproduction/cross_dataset/eth3d_fas_cbf_stress_scenario_activation_v1/report/REPORT_REFINE_FAS_CBF_STRESS_SCENARIO_ACTIVATION_ON_FROZEN_ETH3D_MAP_V1.md", "sample_unit": "plant-free candidate state tuple", "sample_count": 200000, "comparator": "frozen stage-reachability contract", "result_type": "structural", "polarity": "structural", "activity": "shadow", "domain": "external", "allowed_claims": "The preregistered strict endpoint-unsafe/QP-feasible H3 stratum was unavailable under this frozen ETH3D contract.", "prohibited_claims": "DT verification does not exist or is ineffective.", "unresolved_fields": "No V2 registry, smoke, or formal paired outcome."},
    {"evidence_id": "E03_REPLICA_PR65", "module": "M-G", "dataset": "Replica", "scene": "bounded direct-goal scene", "map_role": "GT_DERIVED_GAUSSIAN", "source_pr": "PR #65", "branch": "replica-bounded-direct-goal-safer-fas-cbf-benchmark-v1", "commit": REPLICA_HEAD, "report_path": "reproduction/cross_dataset/replica_bounded_direct_goal_safer_fas_cbf_benchmark_v1/report/REPORT_REPLICA_BOUNDED_DIRECT_GOAL_SAFER_FAS_CBF_BENCHMARK_V1.md", "sample_unit": "route-method terminal record", "sample_count": 500, "comparator": "M0–M4 shared 100-route registry", "result_type": "formal", "polarity": "structural", "activity": "formal", "domain": "in-domain", "allowed_claims": "All methods completed all 99 map-admissible routes with zero official-mesh collisions; module activations are observable on a clean GT-derived Gaussian map.", "prohibited_claims": "Statistical safety superiority or learned-map evidence.", "unresolved_fields": "Outcome saturation prevents superiority inference."},
    {"evidence_id": "E04_STARTGUARD_TRIAL57", "module": "M-A", "dataset": "dense-flight", "scene": "trial 57", "map_role": "OFFICIAL_SAFER_MAP", "source_pr": "historical frozen report", "branch": "historical work/risk_aware_cbf", "commit": RISK_REPORT_HEAD, "report_path": "work/risk_aware_cbf/REPORT_STARTGUARD_TRIAL57.md", "sample_unit": "trial", "sample_count": 1, "comparator": "original start versus separately reported repaired start", "result_type": "case study", "polarity": "negative", "activity": "active", "domain": "in-domain", "allowed_claims": "The original unsafe start and its negative h remain preserved.", "prohibited_claims": "Post-repair navigation is original benchmark superiority.", "unresolved_fields": "Single-trial original failure."},
    {"evidence_id": "E05_STARTGUARD_FLIGHT100", "module": "M-A", "dataset": "dense-flight", "scene": "flight100", "map_role": "OFFICIAL_SAFER_MAP", "source_pr": "historical frozen report", "branch": "historical work/risk_aware_cbf", "commit": RISK_REPORT_HEAD, "report_path": "work/risk_aware_cbf/REPORT_STARTGUARD_FLIGHT100.md", "sample_unit": "trial", "sample_count": 100, "comparator": "original flight versus post-repair flight", "result_type": "active validation", "polarity": "positive", "activity": "active", "domain": "in-domain", "allowed_claims": "In this frozen flight100 setting, StartGuard identified 8 repair-needed starts and repaired all 8; post-repair navigation is reported separately.", "prohibited_claims": "Original benchmark safety improvement or universal start repair.", "unresolved_fields": "Original trial57 collision remains."},
    {"evidence_id": "E06_ACTIVE_PROJECTION", "module": "M-A", "dataset": "dense-flight", "scene": "flight100", "map_role": "OFFICIAL_SAFER_MAP", "source_pr": "historical frozen report", "branch": "historical work/risk_aware_cbf", "commit": RISK_REPORT_HEAD, "report_path": "work/risk_aware_cbf/REPORT_V4A_ACTIVE_PROJECTION_DT_AUDIT.md", "sample_unit": "repair-needed state / navigation trial", "sample_count": 8, "comparator": "active-set verified projection versus verified projection", "result_type": "active validation", "polarity": "positive", "activity": "active", "domain": "in-domain", "allowed_claims": "All 8 active-set repairs were full-query verified; the post-repair 100-trial navigation had zero collisions and no QP infeasibility.", "prohibited_claims": "A general CBF theorem or original-flight superiority.", "unresolved_fields": "Only eight natural repair-needed states."},
    {"evidence_id": "E07_SYNTHETIC_START_STRESS", "module": "M-A", "dataset": "synthetic perturbation", "scene": "initial-unsafe stress", "map_role": "OFFICIAL_SAFER_MAP", "source_pr": "historical frozen report", "branch": "historical work/risk_aware_cbf", "commit": RISK_REPORT_HEAD, "report_path": "work/risk_aware_cbf/REPORT_SYNTHETIC_INITIAL_UNSAFE_STRESS_TEST.md", "sample_unit": "synthetic state", "sample_count": 120, "comparator": "no repair / heuristic / verified projection", "result_type": "synthetic stress", "polarity": "positive", "activity": "static", "domain": "in-domain", "allowed_claims": "Verified projection repaired and full-query verified all 120 constructed states under this synthetic protocol.", "prohibited_claims": "Official benchmark-start performance.", "unresolved_fields": "Synthetic construction is not a natural held-out cohort."},
    {"evidence_id": "E08_RISK_AWARE_STONEHENGE", "module": "M-C", "dataset": "Stonehenge", "scene": "formal100", "map_role": "OFFICIAL_SAFER_MAP", "source_pr": "historical frozen report", "branch": "historical work/risk_aware_cbf", "commit": RISK_REPORT_HEAD, "report_path": "work/risk_aware_cbf/REPORT_RISK_AWARE_V1_BEST_CONFIG_100_TRIAL.md", "sample_unit": "trial", "sample_count": 100, "comparator": "SAFER baseline versus Risk-Aware V1 bestD", "result_type": "formal efficiency", "polarity": "positive", "activity": "formal", "domain": "in-domain", "allowed_claims": "Risk-Aware V1 bestD reduced active constraints and mean runtime while preserving collision and progress in Stonehenge formal100.", "prohibited_claims": "A universal safety or progress improvement.", "unresolved_fields": "Configuration-specific candidate budgeting."},
    {"evidence_id": "E09_RISK_AWARE_FLIGHT", "module": "M-C", "dataset": "dense-flight", "scene": "flight100", "map_role": "OFFICIAL_SAFER_MAP", "source_pr": "historical frozen report", "branch": "historical work/risk_aware_cbf", "commit": RISK_REPORT_HEAD, "report_path": "work/risk_aware_cbf/REPORT_RISK_AWARE_V1_FLIGHT_100_TRIAL.md", "sample_unit": "trial", "sample_count": 100, "comparator": "SAFER baseline versus Risk-Aware V1 bestD", "result_type": "formal efficiency", "polarity": "positive", "activity": "formal", "domain": "in-domain", "allowed_claims": "The report supports efficiency improvement on flight while preserving progress within its stated rule.", "prohibited_claims": "Cross-scene robustness or safety improvement; both variants retain trial57 collision.", "unresolved_fields": "Shared original collision."},
    {"evidence_id": "E10_FORCED_DOMINANCE", "module": "M-B", "dataset": "dense-flight", "scene": "adaptive diagnostic", "map_role": "OFFICIAL_SAFER_MAP", "source_pr": "historical frozen report", "branch": "historical work/risk_aware_cbf", "commit": RISK_REPORT_HEAD, "report_path": "work/risk_aware_cbf/REPORT_FORCED_CANDIDATE_DOMINANCE.md", "sample_unit": "controller step", "sample_count": 199, "comparator": "adaptive budget versus forced candidate union", "result_type": "diagnostic", "polarity": "negative", "activity": "diagnostic", "domain": "in-domain", "allowed_claims": "Forced candidates dominated the final union, limiting observed candidate-count benefit in this implementation.", "prohibited_claims": "Adaptive V1 efficiency benefit or a safety conclusion.", "unresolved_fields": "No forced-candidate-aware active redesign evaluated."},
    {"evidence_id": "E11_DT_DETECTION", "module": "M-D", "dataset": "dense-flight", "scene": "flight100", "map_role": "OFFICIAL_SAFER_MAP", "source_pr": "historical frozen report", "branch": "historical work/risk_aware_cbf", "commit": RISK_REPORT_HEAD, "report_path": "work/risk_aware_cbf/REPORT_DISCRETE_TIME_VERIFICATION_CONSOLIDATION.md", "sample_unit": "controller step", "sample_count": 14422, "comparator": "H1/H2/H3 audit horizons on same-model rollout", "result_type": "detection audit", "polarity": "positive", "activity": "active", "domain": "in-domain", "allowed_claims": "DT verification detected 463/488/519 H1/H2/H3 sampled-data margin risks while collision count remained zero.", "prohibited_claims": "Margin risk is collision or DT universally prevents collision.", "unresolved_fields": "Detection is not a paired avoidance result."},
    {"evidence_id": "E12_V4B_NEGATIVE", "module": "M-D", "dataset": "dense-flight", "scene": "one-step correction", "map_role": "OFFICIAL_SAFER_MAP", "source_pr": "historical frozen report", "branch": "historical work/risk_aware_cbf", "commit": RISK_REPORT_HEAD, "report_path": "work/risk_aware_cbf/REPORT_V4B_CORRECTIVE_DT_FILTER.md", "sample_unit": "margin-violating controller step", "sample_count": 15, "comparator": "base one-step risk versus corrected one-step risk", "result_type": "negative ablation", "polarity": "negative", "activity": "active", "domain": "in-domain", "allowed_claims": "Under the frozen Euler double-integrator, acceleration-only one-step correction did not change immediate position-margin violations.", "prohibited_claims": "All corrective DT control is impossible.", "unresolved_fields": "Only one-step acceleration wrapper tested."},
    {"evidence_id": "E13_V4C_H3", "module": "M-E", "dataset": "dense-flight", "scene": "flight100", "map_role": "OFFICIAL_SAFER_MAP", "source_pr": "historical frozen report", "branch": "historical work/risk_aware_cbf", "commit": RISK_REPORT_HEAD, "report_path": "work/risk_aware_cbf/REPORT_V4C_FLIGHT100_VALIDATION.md", "sample_unit": "trial / recovery activation", "sample_count": 100, "comparator": "base H3 risk versus executed H3 risk", "result_type": "active validation", "polarity": "positive", "activity": "active", "domain": "in-domain", "allowed_claims": "H3_N128 eliminated the 236 observed H-step margin violations in this dense-flight full100 configuration, with zero recovery failures.", "prohibited_claims": "Collision superiority or a low-overhead default controller.", "unresolved_fields": "High activated runtime overhead."},
    {"evidence_id": "E14_V4C_TUNED_H2", "module": "M-E", "dataset": "dense-flight", "scene": "flight100", "map_role": "OFFICIAL_SAFER_MAP", "source_pr": "historical frozen report", "branch": "historical work/risk_aware_cbf", "commit": RISK_REPORT_HEAD, "report_path": "work/risk_aware_cbf/REPORT_V4C_TUNED_FULL100_VALIDATION.md", "sample_unit": "trial / recovery activation", "sample_count": 100, "comparator": "H3_N128 reference versus R4_H2_N64 tuned configuration", "result_type": "configuration-specific validation", "polarity": "positive", "activity": "active", "domain": "in-domain", "allowed_claims": "The tuned H2_N64 configuration eliminated its 193 observed H-step violations with lower runtime than H3_N128 in dense flight.", "prohibited_claims": "Untuned or universal recovery superiority.", "unresolved_fields": "Configuration was tuned on a hotspot pilot."},
    {"evidence_id": "E15_HCE_HELDOUT", "module": "M-F", "dataset": "dense-flight", "scene": "R-V4C-1 held-out activated cohort", "map_role": "OFFICIAL_SAFER_MAP", "source_pr": "historical frozen report", "branch": "historical work/risk_aware_cbf", "commit": "a83259798e0e4b1a2c7fcdce2617ebd8783ebcc3", "report_path": "work/risk_aware_cbf/REPORT_V4C_HIERARCHICAL_HELDOUT_ACTIVATED_COHORT.md", "sample_unit": "held-out activated trial", "sample_count": 16, "comparator": "original V4-C versus hierarchical evaluator", "result_type": "held-out efficiency", "polarity": "positive", "activity": "active", "domain": "in-domain", "allowed_claims": "HCE reduced activated median runtime on its held-out activated cohort without progress, safety, or feasibility regression; it preserved Stage-B failures.", "prohibited_claims": "New recovery capability or universal runtime gain.", "unresolved_fields": "Only activated cohort; Stage-B failed 34 contexts."},
    {"evidence_id": "E16_TRIAL20_BOUNDARY", "module": "M-H", "dataset": "dense-flight", "scene": "trial20", "map_role": "OFFICIAL_SAFER_MAP", "source_pr": "historical frozen report", "branch": "historical work/risk_aware_cbf", "commit": "4f8e00fcc10cbeb98b933d3507eb009659e1341f", "report_path": "work/risk_aware_cbf/REPORT_V4C_TRIAL20_RECOVERY_FAILURE_DIAGNOSIS.md", "sample_unit": "recovery activation", "sample_count": 34, "comparator": "original V4-C and exact Stage-B fallback", "result_type": "structural boundary", "polarity": "negative", "activity": "shadow", "domain": "in-domain", "allowed_claims": "The current local recovery contract was exhausted for the 34 trial20 activations.", "prohibited_claims": "Universal uncontrollability.", "unresolved_fields": "A new primitive would require a new safety contract."},
    {"evidence_id": "E17_TUM_DT_FORENSICS", "module": "M-D", "dataset": "TUM", "scene": "G1 boundary event", "map_role": "LEARNED_SLAM_MAP", "source_pr": "TUM forensic report", "branch": "tum-splatam-g1-boundary-dt-forensics-v1", "commit": TUM_FORENSICS_HEAD, "report_path": "reproduction/cross_dataset/tum_splatam_g1_boundary_dt_forensics_v1/REPORT_TUM_SPLATAM_G1_BOUNDARY_DT_FORENSICS_V1.md", "sample_unit": "time step", "sample_count": 800, "comparator": "shadow H1/H2/H3 prediction versus terminal GSplat overlap proxy", "result_type": "event precursor", "polarity": "positive", "activity": "shadow", "domain": "external", "allowed_claims": "At step 772 the shadow H1/H2/H3 checks predicted the later GSplat overlap proxy event.", "prohibited_claims": "Shadow audit avoided the event or proves mesh-collision safety.", "unresolved_fields": "GSplat proxy, no closed-loop intervention in this source."},
    {"evidence_id": "E18_TUM_V4C_INTERVENTION", "module": "M-E", "dataset": "TUM", "scene": "DT-triggered V4-C cases", "map_role": "LEARNED_SLAM_MAP", "source_pr": "TUM intervention report", "branch": "tum-splatam-dt-triggered-v4c-recovery-v1", "commit": TUM_V4C_HEAD, "report_path": "reproduction/cross_dataset/tum_splatam_dt_triggered_v4c_recovery_v1/REPORT_TUM_SPLATAM_DT_TRIGGERED_V4C_RECOVERY_V1.md", "sample_unit": "development or held-out paired case", "sample_count": 3, "comparator": "frozen baseline versus strict-trigger V4-C intervention", "result_type": "bounded proof-of-mechanism", "polarity": "positive", "activity": "active", "domain": "external", "allowed_claims": "A strict H3-triggered V4-C intervention avoided float32 GSplat overlap in the bounded development and held-out cases described by the report.", "prohibited_claims": "Goal-completion superiority, general safety, or official-mesh collision avoidance.", "unresolved_fields": "Small case-study cohort and overlap proxy."},
]


def ensure_dirs() -> None:
    for name in ("input_freeze", "source_inventory", "evidence_ledger", "semantic_alignment", "config_compatibility", "module_matrices", "claim_audit", "paper_architecture", "minimal_remaining_experiment", "figures", "report", "logs", "tmp"):
        (TASK / name).mkdir(parents=True, exist_ok=True)


def git_text(args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=REPO, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return completed.stdout.decode("utf-8").strip()


def git_bytes(ref: str, path: str) -> bytes:
    completed = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=REPO, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return completed.stdout


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def inventory_sources() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in SOURCE_SPECS:
        raw = git_bytes(spec["commit"], spec["report_path"])
        blob = git_text(["rev-parse", f"{spec['commit']}:{spec['report_path']}"])
        row = dict(spec)
        row.update({"report_sha256": sha256_bytes(raw), "git_blob_sha": blob, "report_bytes": len(raw), "config_sha": "UNKNOWN_NOT_RECOVERED", "method_source_sha": "UNKNOWN_NOT_RECOVERED", "cohort_registry_sha": "UNKNOWN_NOT_RECOVERED"})
        rows.append(row)
    return rows


def require_phrase(evidence_id: str, phrase: str) -> bool:
    item = next(item for item in SOURCE_SPECS if item["evidence_id"] == evidence_id)
    return phrase in git_bytes(item["commit"], item["report_path"]).decode("utf-8", errors="replace")


def load_json(relative: str) -> Any:
    return json.loads((TASK / relative).read_text(encoding="utf-8"))


def source_map() -> dict[str, dict[str, Any]]:
    return {row["evidence_id"]: row for row in load_json("evidence_ledger/evidence_provenance_ledger.json")}
