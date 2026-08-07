"""Create the F01-F11 diagnostic contract before any new diagnostics are read."""
from __future__ import annotations

from common import sha256_file, write_csv, write_json, write_text
from task_config import (
    DT, EFFECTIVE_RADIUS, EVIDENCE_CLASSES, FORMAL_ENVIRONMENTS, GRID7,
    H_STOP_MAX, SOBOL_SCRAMBLE, SOBOL_SEED, TASK_ROOT, TERMINAL_TOLERANCE,
    U_BOUND, UPSTREAM_ROOT, V_BOUND, VERDICTS,
)

FACTORS = {
    "F01": ("environment_exposure", "Representative states may have insufficient physical, represented-map, dynamic, or downstream-gate exposure.", "E1 reanalysis plus E5 asset audit", "No physical-danger claim for behavior-only maps."),
    "F02": ("configuration_exposure", "Frozen velocity/dt/acceleration/latency regime may suppress activation.", "E4 one-factor-at-a-time shadow regimes", "No deployment or formal-performance claim."),
    "F03": ("b0_masking", "B0 current feasibility may left-truncate downstream B1/B2/B3 evaluation.", "E1 funnel plus E2 independent-gate shadow", "No shadow control is a committed action."),
    "F04": ("b1_timing", "Immediate position-first segment may be candidate-insensitive.", "E2 S0-S3 same-dynamics shadow", "S2/S3 are not a Core V1 replacement."),
    "F05": ("b2_atomicity", "Terminal/backup/braking composition may conceal component-level causes.", "E2 atomic decomposition and L1-L5", "Leave-one-out is not a new method."),
    "F06": ("b3_coverage", "Six slots may miss controls in a finite pre-registered search set.", "E3 GRID7+SOBOL512 over C0/C1", "No continuous control-space conclusion."),
    "F07": ("representative_distribution", "Frozen registries can be leakage-free yet not deployment/on-policy representative.", "E5 asset inventory and read-only comparison", "No initial-state-to-deployment inference."),
    "F08": ("metric_sensitivity", "Final action change can miss certificate or availability gains.", "E1/E2/E3 metric taxonomy", "Certificate gain is not behavioral gain."),
    "F09": ("map_representation", "Map type and reference authority can limit learned-map conclusions.", "E5 representation/readiness audit", "Proxy clearance is not physical clearance."),
    "F10": ("statistical_power", "Zero-event cohorts may not exclude low underlying event rates, especially downstream conditional rates.", "E1 binomial/cluster/conditional analysis", "Do not pool the 360 states."),
    "F11": ("implementation_consistency", "An adapter, serialization, or classification mismatch could explain zero results.", "E0 hashes plus deterministic replays/formula checks", "Any semantic mismatch forces Case G."),
}


def main() -> None:
    registry = []
    matrix = []
    hypothesis_lines = ["# Causal hypotheses F01-F11", "", "All verdicts are pre-registered. A diagnostic result is never elevated above its evidence class.", ""]
    for factor_id, (name, hypothesis, diagnostic, prohibited) in FACTORS.items():
        item = {
            "factor_id": factor_id, "name": name, "precise_hypothesis": hypothesis,
            "competing_explanation": "Observed representative zero increments arise from another registered factor or an interaction.",
            "required_evidence": diagnostic, "allowed_diagnostic": diagnostic,
            "prohibited_inference": prohibited,
            "support_criterion": "Pre-registered diagnostic directly meets the factor-specific mechanism condition without a higher-priority inconsistency.",
            "refute_criterion": "The factor-specific diagnostic is evaluable and contradicts the hypothesis.",
            "partial_criterion": "Evidence establishes a contributing limitation but not a unique primary cause.",
            "data_blocked_criterion": "Required frozen asset, reference, or on-policy evidence is absent.",
            "downstream_implication": "Use only the final fixed Case A-G table; no method implementation follows automatically.",
            "allowed_verdicts": list(VERDICTS),
        }
        registry.append(item)
        matrix.append({"factor_id": factor_id, "required_evidence": diagnostic, "allowed_evidence_classes": "|".join(EVIDENCE_CLASSES), "prohibited_inference": prohibited})
        hypothesis_lines.extend([f"## {factor_id} {name}", "", f"Hypothesis: {hypothesis}", "", f"Allowed diagnostic: {diagnostic}", "", f"Prohibited inference: {prohibited}", ""])
    contract = {
        "status": "FROZEN_BEFORE_NEW_DIAGNOSTIC_READ", "factor_count": len(registry),
        "factors": [item["factor_id"] for item in registry], "verdict_vocabulary": list(VERDICTS),
        "evidence_classes": list(EVIDENCE_CLASSES),
        "formal_environment_order": list(FORMAL_ENVIRONMENTS),
        "model": "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1",
        "dt_s": DT, "u_bound_inf": U_BOUND, "v_bound_inf": V_BOUND,
        "effective_radius_m": EFFECTIVE_RADIUS, "terminal_tolerance": TERMINAL_TOLERANCE,
        "h_stop_max": H_STOP_MAX,
        "counterfactual_regime": {
            "one_factor_at_a_time": True, "velocity_scale_nonzero_only": [0.25, 0.5, 0.75, 1.0],
            "dt_s": [0.025, 0.05, 0.10, 0.20], "u_bound_inf": [0.05, 0.10, 0.20],
            "latency_cycles": [0, 1, 2], "tracking_error": "DATA_BLOCKED_UNLESS_FROZEN_ERROR_BUDGET_EXISTS",
        },
        "bounded_oracle": {
            "c0_max_per_environment": 16, "c0_selection": "frozen_registry_state_sha_sorted_stratified",
            "c1_max_per_environment": 16, "c1_selection": "frozen_B2_noncommit_or_B0_current_infeasible_typed_status_then_state_sha",
            "grid7_axis": list(GRID7), "grid7_candidate_count": 343,
            "sobol_candidate_count": 512, "sobol_seed": SOBOL_SEED, "sobol_scramble": SOBOL_SCRAMBLE,
            "claim_boundary": "finite searched set only; not a continuous control-space proof",
        },
        "frozen_upstream_formal_csv_sha256": sha256_file(UPSTREAM_ROOT / "benchmark/one_step_records.csv"),
        "formal_method_run_count_before_contract": 0,
    }
    write_json(TASK_ROOT / "causes/causal_factor_registry.json", {"status": "PASS_F01_F11_PREREGISTERED", "factors": registry})
    write_csv(TASK_ROOT / "causes/evidence_required_matrix.csv", matrix)
    write_json(TASK_ROOT / "causes/verdict_contract.json", contract)
    write_text(TASK_ROOT / "causes/causal_hypotheses.md", "\n".join(hypothesis_lines))
    write_json(TASK_ROOT / "phase_manifests/phase0.json", {"status": "PASS_PHASE0_FROZEN", "contract_sha256": sha256_file(TASK_ROOT / "causes/verdict_contract.json"), "factor_registry_sha256": sha256_file(TASK_ROOT / "causes/causal_factor_registry.json"), "new_diagnostic_result_read_before_freeze": False})
    print("PASS_PREREGISTERED_CAUSAL_CONTRACT", len(registry))


if __name__ == "__main__":
    main()
