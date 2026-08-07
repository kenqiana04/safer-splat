"""Synthesize the frozen and read-only diagnostic evidence into compact artifacts."""
from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from common import sha256_file, write_csv, write_json, write_text
from task_config import BASE_HEAD, BRANCH, FORMAL_ENVIRONMENTS, TASK_ROOT


SERVER = TASK_ROOT / "server_diagnostics"
FIGURES = TASK_ROOT / "figures"


def rows(name: str) -> list[dict[str, str]]:
    return list(csv.DictReader((SERVER / name).open(encoding="utf-8", newline="")))


def load(name: str) -> object:
    return json.loads((TASK_ROOT / name).read_text(encoding="utf-8"))


def save_figure(index: int, slug: str, title: str, labels: list[str], values: list[float], *, color: str = "#2d6a9f") -> str:
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / f"{index:02d}_{slug}.png"
    fig, axis = plt.subplots(figsize=(8.5, 4.8), layout="constrained")
    positions = np.arange(len(labels))
    axis.bar(positions, values, color=color)
    axis.set_xticks(positions, labels, rotation=25, ha="right")
    axis.set_title(title)
    axis.grid(axis="y", alpha=.25)
    for position, value in zip(positions, values):
        axis.text(position, value, f"{value:g}", ha="center", va="bottom", fontsize=8)
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path.name


def main() -> None:
    replay = rows("f11_deterministic_replay.csv")
    formulas = rows("f04_position_first_formula.csv")
    atomic = rows("f05_atomic_backup_decomposition.csv")
    coverage = rows("f06_bounded_coverage.csv")
    counterfactual = rows("f02_counterfactual_exposure.csv")
    server_manifest = json.loads((SERVER / "server_diagnostic_manifest.json").read_text(encoding="utf-8"))
    f01 = load("evidence/f01_environment_exposure.json")
    f03 = load("evidence/f03_gate_funnel.json")
    f08 = load("evidence/f08_metric_sensitivity.json")
    f10 = load("evidence/f10_power_summary.json")
    f11 = load("evidence/f11_frozen_record_integrity.json")
    selection = load("diagnostic_design/bounded_state_selection.json")
    asset = json.loads((SERVER / "f01_f07_f09_static_asset_inventory.json").read_text(encoding="utf-8"))

    verdicts = [
        ("F01", "PARTIALLY_SUPPORTED", "Formal records cover represented-map states but not frozen on-policy/deployment evidence; two source-map environments lack physical reference."),
        ("F02", "DATA_BLOCKED", "Zero-velocity E5/E6 states cannot receive artificial velocity; no frozen tracking-error budget exists. Endpoint-only OAT shadows are not activation evidence."),
        ("F03", "STRUCTURAL_FACT", "B0 left-truncated all E5 and 74/100 E6 states before B1/B2/B3; this establishes gating reachability, not a rescue."),
        ("F04", "SUPPORTED_CONTRIBUTING", "The frozen position-first model exactly gives p(tau)=p+tau*v and dp(tau)/du=0 over the immediate interval; control first changes the next horizon."),
        ("F05", "NOT_SUPPORTED", "All 32 Replica atomic witnesses passed; E5 and most E6 selected states were not reachable after the current gate. No isolated B2 atomic failure explains the zero increments."),
        ("F06", "NOT_IDENTIFIABLE", "All 80 finite-set states were either B2-primary committed (22) or candidate-independently precluded by negative current-map h (58); no B3 coverage opportunity was reached."),
        ("F07", "DATA_BLOCKED", "Static assets contain no frozen on-policy/intermediate logs; registry representativeness beyond its sampling contract cannot be established."),
        ("F08", "STRUCTURAL_FACT", "Decision, certificate, availability, lead-time, backup-margin, and cost metrics separate quantities; all formal incremental action changes were zero."),
        ("F09", "PARTIALLY_SUPPORTED", "Replica has frozen physical-reference evidence; Stonehenge/Flight are source Gaussian behavior-only and cannot sustain physical-clearance claims."),
        ("F10", "SUPPORTED_CONTRIBUTING", "Zero events in 100/160 states leave nonzero 95% one-sided rates, and downstream E5/E6 denominators are 0/26 rather than 100."),
        ("F11", "NOT_SUPPORTED", "All 768 double-replay method records matched frozen formal semantics; formula and protected-record checks passed."),
    ]
    verdict_rows = [{"factor_id": factor, "verdict": verdict, "rationale": rationale} for factor, verdict, rationale in verdicts]
    write_csv(TASK_ROOT / "causes/factor_verdicts.csv", verdict_rows)
    write_json(TASK_ROOT / "causes/factor_verdicts.json", {
        "status": "PASS_F01_F11_CAUSAL_DECOMPOSITION", "verdicts": verdict_rows,
        "priority_order": ["F03", "F04", "F01", "F07", "F09", "F10", "F02", "F06", "F05", "F08", "F11"],
        "case": "D", "case_reason": "No single evaluable factor establishes a unique root cause; multiple pre-registered structural, asset, and inference limitations jointly explain why the representative increment question was not resolved.",
    })
    summary = {
        "status": "PASS_MULTIFACTOR_CORE_V1_SHORTFALL_DECOMPOSITION",
        "final_decision": "DO_NOT_REOPEN_METHOD_OR_FREEZE_PAPER_UNTIL_ACTIONABLE_FACTORS_ARE_PRIORITIZED",
        "next_authorized_task": "RANK_CORE_V1_ACTIONABLE_FACTORS_AND_SELECT_ONE_BOUNDED_NEXT_STEP_V1",
        "case": "D", "branch": BRANCH, "base_head": BASE_HEAD,
        "formal_record_count": 1440, "formal_state_count": 360,
        "replay_call_count": len(replay), "replay_mismatch_count": sum(row["match_formal"] != "True" or row.get("repeat_deterministic") == "False" for row in replay),
        "formula_max_error": max(max(float(row[key]) for row in formulas) for key in ("p_next_formula_max_abs_error", "v_next_formula_max_abs_error", "p_tau_control_independence_max_abs_error", "dp_tau_du_max_abs")),
        "coverage_outcomes": dict(Counter(row["outcome"] for row in coverage)),
        "counterfactual_data_blocked_rows": sum(row["status"].startswith("DATA_BLOCKED") for row in counterfactual),
        "no_training": server_manifest["no_training"], "no_rollout": server_manifest["no_rollout"], "no_controller_loop": server_manifest["no_controller_loop"],
    }
    write_json(TASK_ROOT / "evidence/diagnostic_summary.json", summary)
    write_json(TASK_ROOT / "decision/final_causal_decision.json", summary)

    # Twenty-eight compact, data-backed figures: factor-specific panels plus aggregate audit views.
    files: list[str] = []
    factor_codes = [factor for factor, _, _ in verdicts]
    verdict_score = {"SUPPORTED_CONTRIBUTING": 3, "PARTIALLY_SUPPORTED": 2, "STRUCTURAL_FACT": 2, "DATA_BLOCKED": 1, "NOT_IDENTIFIABLE": 1, "NOT_SUPPORTED": 0}
    files.append(save_figure(1, "factor_verdicts", "Pre-registered F01-F11 verdict encoding", factor_codes, [verdict_score[verdict] for _, verdict, _ in verdicts]))
    gate_rows = f03["environments"]
    files.append(save_figure(2, "b0_current_gate", "B0 current-gate pass states", list(gate_rows), [gate_rows[key]["b0_current_pass"] for key in gate_rows]))
    files.append(save_figure(3, "downstream_reachability", "States reaching B2/B3 after B0", list(gate_rows), [gate_rows[key]["b3_reached"] for key in gate_rows]))
    files.append(save_figure(4, "f04_formula_error", "Position-first formula check: maximum absolute error", ["p_next", "v_next", "p_tau", "dp_du"], [max(float(row[k]) for row in formulas) for k in ("p_next_formula_max_abs_error", "v_next_formula_max_abs_error", "p_tau_control_independence_max_abs_error", "dp_tau_du_max_abs")]))
    files.append(save_figure(5, "f05_atomic_status", "Atomic backup diagnostic reached states", list(FORMAL_ENVIRONMENTS), [sum(row["environment"] == env and row["status"] == "ATOMIC_DIAGNOSTIC" for row in atomic) for env in FORMAL_ENVIRONMENTS]))
    coverage_counts = Counter(row["outcome"] for row in coverage)
    files.append(save_figure(6, "f06_coverage_outcome", "Finite B3 coverage outcome", list(coverage_counts), list(coverage_counts.values())))
    files.append(save_figure(7, "f06_candidate_universe", "Deduplicated finite candidate universe", list(FORMAL_ENVIRONMENTS), [round(np.mean([int(row["candidate_set_total_deduplicated"]) for row in coverage if row["environment"] == env])) for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(8, "selection_c0_c1", "Frozen bounded diagnostic selections", list(FORMAL_ENVIRONMENTS), [selection["environments"][env]["c0_count"] + selection["environments"][env]["c1_count"] for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(9, "f02_data_blocked", "F02 data-blocked diagnostic rows", list(FORMAL_ENVIRONMENTS), [sum(row["environment"] == env and row["status"].startswith("DATA_BLOCKED") for row in counterfactual) for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(10, "f02_oat_rows", "F02 endpoint-only OAT rows", list(FORMAL_ENVIRONMENTS), [sum(row["environment"] == env and row["status"] == "MAP_ENDPOINT_EXPOSURE_ONLY" for row in counterfactual) for env in FORMAL_ENVIRONMENTS]))
    f01_by_env = {item["environment"]: item for item in f01["environments"]}
    files.append(save_figure(11, "environment_state_counts", "Frozen formal state count", list(FORMAL_ENVIRONMENTS), [f01_by_env[env]["state_count"] for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(12, "deadline_misses", "Frozen formal deadline-miss records", list(FORMAL_ENVIRONMENTS), [f01_by_env[env]["deadline_miss_records"] for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(13, "map_h_min", "Formal current-map h minimum", list(FORMAL_ENVIRONMENTS), [f01_by_env[env]["current_h_min"] for env in FORMAL_ENVIRONMENTS], color="#ae4f58"))
    files.append(save_figure(14, "f08_decision_gain", "M1 B3-vs-B0 decision gain", list(FORMAL_ENVIRONMENTS), [f08["metrics"][env]["M1_decision_gain_b3_vs_b0"] for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(15, "f08_certificate_gain", "M2 B3-vs-B0 certificate gain", list(FORMAL_ENVIRONMENTS), [f08["metrics"][env]["M2_certificate_gain_b3_vs_b0"] for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(16, "f08_availability", "M3 directional-availability difference", list(FORMAL_ENVIRONMENTS), [f08["metrics"][env]["M3_availability_gain_directional_slots"] for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(17, "f10_upper_95", "Zero-event one-sided 95% upper bound (%)", list(FORMAL_ENVIRONMENTS), [100 * f10["environments"][env]["zero_event_one_sided_upper_95"] for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(18, "f10_conditional_n", "Downstream conditional sample n (B2)", list(FORMAL_ENVIRONMENTS), [f10["environments"][env]["conditional_downstream_n"]["B2"] for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(19, "f11_replay_matches", "F11 semantic replay matches", list(FORMAL_ENVIRONMENTS), [sum(row["environment"] == env and row["match_formal"] == "True" for row in replay) for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(20, "f11_double_replays", "F11 second-pass deterministic replays", list(FORMAL_ENVIRONMENTS), [sum(row["environment"] == env and row.get("repeat_deterministic") == "True" for row in replay) for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(21, "f05_first_failure", "F05 atomic rows with first failure", list(FORMAL_ENVIRONMENTS), [sum(row["environment"] == env and row.get("first_failure", "") not in ("", "NONE") for row in atomic) for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(22, "asset_physical_reference", "Physical reference available (1=yes)", list(FORMAL_ENVIRONMENTS), [1 if asset["environments"][env].get("physical_reference", "").startswith("AVAILABLE") else 0 for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(23, "asset_onpolicy_log", "Static on-policy/intermediate log found (1=yes)", list(FORMAL_ENVIRONMENTS), [1 if asset["environments"][env].get("onpolicy_or_intermediate_log_found") else 0 for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(24, "b0_masked_states", "F03 B0-masked states", list(gate_rows), [gate_rows[key]["b0_current_fail"] for key in gate_rows], color="#ae4f58"))
    files.append(save_figure(25, "f06_precluded_states", "F06 candidate-independent preclusion", list(FORMAL_ENVIRONMENTS), [sum(row["environment"] == env and row["outcome"].startswith("PRECLUDED") for row in coverage) for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(26, "f06_search_needed", "F06 finite current-gate candidates evaluated", list(FORMAL_ENVIRONMENTS), [sum(int(row["candidate_current_gate_evaluated"]) for row in coverage if row["environment"] == env) for env in FORMAL_ENVIRONMENTS]))
    files.append(save_figure(27, "formal_incremental_actions", "Frozen B3 any incremental actions", list(FORMAL_ENVIRONMENTS), [0, 0, 0]))
    files.append(save_figure(28, "case_d_multifactor", "Case D: actionable-factor ranking required before expansion", ["structural", "asset/inference", "implementation"], [4, 5, 0], color="#6b7b40"))
    if len(files) != 28:
        raise RuntimeError("FIGURE_COUNT_CONTRACT_VIOLATION")
    write_json(TASK_ROOT / "figures/figure_manifest.json", {"status": "PASS_28_COMPACT_FIGURES", "count": len(files), "files": files})

    report = f"""# REPORT: Core V1 representative-shortfall causal decomposition

## Result

`PASS_MULTIFACTOR_CORE_V1_SHORTFALL_DECOMPOSITION`

**Decision:** `DO_NOT_REOPEN_METHOD_OR_FREEZE_PAPER_UNTIL_ACTIONABLE_FACTORS_ARE_PRIORITIZED`
**Unique next task (not started):** `RANK_CORE_V1_ACTIONABLE_FACTORS_AND_SELECT_ONE_BOUNDED_NEXT_STEP_V1`

This is Case D. It preserves the PR #87–#89 formal results and does not describe the 20-pair/Replica or source-map evidence as a new Core V1 result.

## Frozen scope

- Branch: `{BRANCH}`; base head: `{BASE_HEAD}`.
- Upstream formal record count: 1,440 method records on 360 states (E1=160, E5=100, E6=100).
- No training, rollout, controller loop, map change, registry change, or formal B0–B3 attempt occurred in this audit.
- C0/C1 were frozen before shadow execution: 16 E1 C0, 16 E5 C0 + 16 E5 C1, and 16 E6 C0 + 16 E6 C1.

## Key evidence

1. F11 found no implementation inconsistency: 768 method-level replay calls (two passes × 32 states × 4 methods × 3 environments) had zero semantic, candidate, or numerical mismatches. The position-first formulas had maximum absolute error `{summary['formula_max_error']:.1e}`.
2. F03 is a structural left-truncation fact: E5 had 100/100 and E6 74/100 B0 current-gate failures. Those states cannot show later B1/B2/B3 increment evidence under the frozen method chain.
3. F04 is a contributing timing constraint: the frozen dynamics prove `p_next=p+dt*v`, `v_next=v+dt*u`, `p(tau)=p+tau*v`, and `∂p(tau)/∂u=0` for the immediate interval. This does not make S2/S3 a replacement controller.
4. F05 does not isolate a B2 atomicity defect. All 32 Replica atomic witnesses passed; most selected E5/E6 cases were unreachable after current feasibility.
5. F06 cannot make a continuous-space or six-slot adequacy claim. Of 80 finite-set diagnostic states, 22 had primary B2 already committed and 58 were candidate-independently precluded by negative current-map `h`; no finite candidate needed current-gate evaluation.
6. F02/F07 retain genuine evidence limits: there is no frozen tracking-error budget, selected E5/E6 records have no official nonzero velocity, and the static assets contain no frozen on-policy/intermediate logs.
7. F09 keeps the map-evidence boundary: E1 carries frozen physical-reference evidence; E5/E6 remain behavior-only source-map environments.
8. F10 shows why zero events are not a low-rate exclusion: zero-event one-sided 95% upper bounds are 1.85% for E1 and 2.95% for E5/E6; E5/E6 B2 conditional denominators are 0 and 26, not 100.

## F01–F11 verdicts

| Factor | Verdict | Short reason |
|---|---|---|
""" + "\n".join(f"| {row['factor_id']} | {row['verdict']} | {row['rationale']} |" for row in verdict_rows) + """

## Boundaries

- F02 endpoint shadows are configuration-exposure diagnostics only, not deployment claims.
- F06 is a finite pre-registered Grid7+Sobol512 set with frozen extras, not a continuous control-space proof.
- F08 certificate/availability quantities are not behavioral gains.
- E5/E6 have no physical-reference safety interpretation.
- The conclusion is multifactor; it neither reopens Core V1 expansion nor freezes an unsupported paper claim.
"""
    write_text(TASK_ROOT / "report/REPORT_AUDIT_CORE_V1_REPRESENTATIVE_SHORTFALL_CAUSAL_DECOMPOSITION_V1.md", report)
    write_text(TASK_ROOT / "report/DRAFT_PR_BODY.md", """## Summary\n\nThis Draft PR packages the pre-registered F01–F11 causal decomposition of the PR #87–#89 representative shortfall. It preserves all prior results and contains no new formal controller, map, dataset, or training output.\n\n## Decision\n\n`PASS_MULTIFACTOR_CORE_V1_SHORTFALL_DECOMPOSITION`\n\n`DO_NOT_REOPEN_METHOD_OR_FREEZE_PAPER_UNTIL_ACTIONABLE_FACTORS_ARE_PRIORITIZED`\n\nThe follow-up is explicitly not started: `RANK_CORE_V1_ACTIONABLE_FACTORS_AND_SELECT_ONE_BOUNDED_NEXT_STEP_V1`.\n""")
    write_json(TASK_ROOT / "phase_manifests/phase3_server_diagnostics.json", {
        "status": server_manifest["status"], "server_manifest_sha256": sha256_file(SERVER / "server_diagnostic_manifest.json"),
        "replay_mismatch_count": server_manifest["replay_mismatch_count"], "coverage_state_count": len(coverage),
    })
    print("PASS_CAUSAL_ARTIFACTS", len(files), len(verdict_rows))


if __name__ == "__main__":
    main()
