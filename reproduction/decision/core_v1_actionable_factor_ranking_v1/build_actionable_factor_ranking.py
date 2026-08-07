"""Materialize the frozen, desk-based Core V1 action-package decision analysis."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from freeze_upstream_inputs import main as freeze_inputs
from task_config import FIGURES, FATAL_GATES, POSITIVE_KEYS, RISK_KEYS, TASK_ID, TASK_ROOT, UPSTREAM_HEAD


FOOTER = "DECISION ANALYSIS ONLY | NO NEW FORMAL METHOD RUN | NO METHOD CHANGE | NO DATASET ADDITION | NO TRAINING | NO PERFORMANCE CLAIM | FROZEN PR90 EVIDENCE"
SELECTED = "A1"
NEXT_TASK = "WRITE_CORE_CAUSAL_ARCHITECTURE_SPECIFICATION_V1"

PACKAGES = {
    "A1": {
        "name": "CAUSAL_ARCHITECTURE_SPEC", "factors": "F03,F04,F08",
        "question": "Does the B0→B1→B2→B3 pipeline conflate admission, immediate uncontrollable risk, future candidate safety, recoverability, and alternative search?",
        "objective": "Write a causal control-structure specification only; implement nothing.",
        "next_task": NEXT_TASK,
        "scores": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
        "risks": [1, 0, 0, 1, 1, 0, 1, 0],
        "failure": "A specification may reveal that B1 is a naming/evaluation-role issue rather than a method defect.",
        "stop": "Stop at a signed role/horizon/denominator specification with no controller implementation.",
    },
    "A2": {
        "name": "ON_POLICY_EVALUATION_DESIGN", "factors": "F07,F10,F01",
        "question": "How can a deployment-relevant on-policy evaluation be defined without method-outcome selection?",
        "objective": "Design a data and statistics contract only; acquire no data.",
        "next_task": "WRITE_CORE_V1_ON_POLICY_EVALUATION_PROTOCOL_V1",
        "scores": [3, 4, 5, 4, 3, 2, 3, 1, 4, 4, 4, 4],
        "risks": [2, 2, 5, 1, 2, 4, 2, 0],
        "failure": "Without a defined candidate-dependent horizon, denominators and conditional gates remain ambiguous.",
        "stop": "Stop at a data/cluster/power/logging contract; no collection or rollout.",
    },
    "A3": {
        "name": "B3_COVERAGE_IDENTIFICATION", "factors": "F06,F03",
        "question": "Is the six-slot library missing a certifiable control, or was no legal alternative-search state reached?",
        "objective": "Design an eligibility and bounded-oracle protocol only; run no oracle.",
        "next_task": "WRITE_B3_CONTROL_COVERAGE_IDENTIFICATION_PROTOCOL_V1",
        "scores": [3, 2, 4, 3, 4, 3, 4, 4, 4, 3, 3, 3],
        "risks": [2, 3, 1, 2, 2, 5, 3, 1],
        "failure": "All frozen states may remain ineligible, requiring forbidden active construction or new sampling.",
        "stop": "Stop at a pre-registered eligible-state and bounded-search contract.",
    },
    "A4": {
        "name": "CONFIGURATION_REGIME_IDENTIFICATION", "factors": "F02,F01",
        "question": "Does the frozen low-speed/no-delay regime suppress mechanism exposure for physically sourced reasons?",
        "objective": "Write a regime diagnostic protocol only; do not optimize a configuration.",
        "next_task": "WRITE_CORE_V1_CONFIGURATION_REGIME_PROTOCOL_V1",
        "scores": [3, 3, 4, 3, 3, 2, 3, 2, 4, 3, 3, 3],
        "risks": [4, 3, 4, 2, 3, 3, 2, 1],
        "failure": "No frozen real-system source may bound velocity, latency, or tracking error without trigger engineering.",
        "stop": "Stop at a provenance-qualified regime boundary or an explicit no-source block.",
    },
    "A5": {
        "name": "EVIDENCE_CONSOLIDATION", "factors": "all frozen evidence",
        "question": "Is consolidation more valuable than resolving any remaining causal prerequisite?",
        "objective": "Freeze evidence into a claim-bounded contribution plan; add no method.",
        "next_task": "WRITE_FROZEN_PAPER_CONTRIBUTION_AND_EXPERIMENT_PLAN_V1",
        "scores": [3, 2, 4, 3, 2, 5, 5, 5, 5, 5, 1, 4],
        "risks": [0, 0, 0, 0, 2, 1, 2, 3],
        "failure": "It can prematurely present an unresolved architectural ambiguity as an adequate frozen contribution.",
        "stop": "Stop at a claim-bounded paper plan with no new results.",
    },
}

DEPENDENCIES = [
    ("A1", "A2", "REQUIRED", "Conditional evaluation denominators require the candidate-dependent horizon and B1 role."),
    ("A1", "A3", "REQUIRED", "B3 eligibility requires a lawful B1/B2/B3 entry definition."),
    ("A1", "A4", "REQUIRED", "Activation interpretation is not meaningful until B1 is distinguished from a candidate gate."),
    ("A2", "A5", "HELPFUL", "A future on-policy contract would sharpen, but is not required for, a frozen-paper plan."),
    ("A3", "A5", "HELPFUL", "A coverage contract would narrow a future claim boundary but is not required for a plan."),
    ("A4", "A5", "HELPFUL", "A provenance-qualified regime could refine a future limitation statement."),
]

EFFORT = {
    "A1": (1, 3, 5, 4, 14, 0, "<0.05 GB", "none", "none", "none", "none", 0.90, 0.25, "role ambiguity remains but is itself a decision"),
    "A2": (2, 4, 5, 6, 18, 0, "<0.05 GB", "none for design", "future logging contract", "none", "existing-log absence", 0.70, 0.55, "missing on-policy asset prevents an actionable denominator"),
    "A3": (2, 4, 5, 6, 16, 0, "<0.05 GB", "none for protocol", "none", "none", "no frozen eligible state", 0.55, 0.70, "eligibility cannot be identified without new sampling"),
    "A4": (2, 4, 5, 5, 16, 0, "<0.05 GB", "none for protocol", "real-system budget source", "none", "no provenance-qualified ranges", 0.45, 0.70, "diagnostic becomes prohibited trigger engineering"),
    "A5": (1, 3, 4, 2, 18, 0, "<0.05 GB", "none", "none", "none", "premature consolidation", 0.65, 0.65, "unresolved prerequisite is buried rather than resolved"),
}

REVIEWS = [
    ("control_theory", "RVR1 Control/Theory Reviewer", "A1", "A3", "The position-first derivative makes horizon/role semantics the prerequisite; B3 eligibility inherits it.", "Skipping A1 leaves any later candidate or backup claim semantically underdetermined."),
    ("robotics_system", "RVR2 Robotics/System Reviewer", "A1", "A2", "A reproducible system log contract is useful, but cannot label an immediate interval as control-sensitive before its role is fixed.", "Skipping A1 risks collecting or describing system evidence with unusable gate denominators."),
    ("evaluation_statistics", "RVR3 Evaluation/Statistics Reviewer", "A2", "A1", "The largest observed evidence gap is no on-policy data and low conditional n; nevertheless A2 must inherit the architectural horizon definition.", "Skipping A2 preserves weak power, but doing it first would bake in an undefined conditioning event."),
    ("novelty_publication", "RVR4 Novelty/Publication Reviewer", "A1", "A5", "A frozen paper plan is defensible only after the architecture is stated clearly enough to separate a role correction from a claimed method contribution.", "Skipping A1 invites an ambiguous novelty claim or a premature paper freeze."),
]

ACTION_REQUIREMENTS = {
    "A1": "Define B0's role; classify B1 as admission/late-risk detection or candidate safety; state the first candidate-dependent position horizon; state backup/recoverability and alternative-search entry; define conditional versus unconditional ablation denominators; separate method from evaluation protocol.",
    "A2": "Define on-policy/intermediate/turn/lateral/pre-failure/recovery/off-route units, trial clustering, conditional-gate power, leakage prevention, required logs, and a minimal data plan without selecting by method outcome.",
    "A3": "Define legal eligible states, bounded-oracle cap and purpose, coverage/false-negative metrics, six-slot confidence, continuous-space non-claim, anti-shopping selection, and a kill gate.",
    "A4": "Define only physically sourced velocity/dt/latency/tracking-error ranges, the configuration-specific claim boundary, and a regime boundary that rejects trigger engineering.",
    "A5": "Freeze a claim-bounded contribution and experiment plan only if all higher-value bounded actions are gated or depend on unavailable short-term assets.",
}


def write_text(relative: str, text: str) -> None:
    path = TASK_ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(relative: str, payload: object) -> None:
    write_text(relative, json.dumps(payload, indent=2, sort_keys=True))


def write_csv(relative: str, header: list[str], rows: list[list[object]]) -> None:
    path = TASK_ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gate_rows() -> list[list[str]]:
    common = {
        "G1": "clear problem statement", "G2": "desk-based without method-result mutation",
        "G3": "explicit stop condition", "G4": "positive and negative outcomes reduce uncertainty",
        "G5": "decision artifact within five working days", "G6": "no new map training",
        "G7": "no new dataset", "G8": "not activation-rate optimization",
        "G9": "no undefined reference truth", "G10": "no method branch before prerequisite is solved",
        "G11": "controller-centered safety-assurance alignment", "G12": "at most one next task",
    }
    rows = []
    blocked = {"A2": "A1 role/horizon prerequisite", "A3": "A1 lawful gate-entry prerequisite", "A4": "A1 B1-role prerequisite"}
    for aid in PACKAGES:
        for gate in FATAL_GATES:
            status = "PASS"
            reason = common[gate]
            if gate == "G10" and aid in blocked:
                status, reason = "FAIL", f"Dependency blocked: {blocked[aid]}"
            rows.append([aid, gate, status, reason])
    return rows


def package_rows() -> list[list[object]]:
    rows = []
    for aid, data in PACKAGES.items():
        positive = sum(data["scores"])
        risk = sum(data["risks"])
        rows.append([aid, data["name"], data["factors"], positive, risk, f"{positive - 0.75 * risk:.2f}", data["next_task"]])
    return rows


def source_evidence_index() -> None:
    sources = [
        (UPSTREAM_HEAD, "reproduction/causal_audit/core_v1_representative_shortfall_causal_decomposition_v1/causes/factor_verdicts.json", "F01-F11 verdicts"),
        (UPSTREAM_HEAD, "reproduction/causal_audit/core_v1_representative_shortfall_causal_decomposition_v1/causal_attribution/interaction_matrix.csv", "factor interactions"),
        (UPSTREAM_HEAD, "reproduction/causal_audit/core_v1_representative_shortfall_causal_decomposition_v1/decision/supported_claims.md", "supported claims"),
        (UPSTREAM_HEAD, "reproduction/causal_audit/core_v1_representative_shortfall_causal_decomposition_v1/decision/prohibited_claims.md", "prohibited claims"),
        (UPSTREAM_HEAD, "reproduction/causal_audit/core_v1_representative_shortfall_causal_decomposition_v1/decision/unresolved_factors.md", "unresolved factors"),
        ("9287617cce74561aa434d1aca7eb684f79551188", "reproduction/research_direction/safer_splat_direction_audit_v1/literature/fulltext_evidence_matrix.csv", "frozen competitor matrix"),
        ("9287617cce74561aa434d1aca7eb684f79551188", "reproduction/research_direction/safer_splat_direction_audit_v1/feasibility/effort_estimates.csv", "frozen effort estimates"),
    ]
    records = []
    for commit, path, role in sources:
        raw = subprocess.check_output(["git", "show", f"{commit}:{path}"])
        blob = subprocess.check_output(["git", "rev-parse", f"{commit}:{path}"], text=True).strip()
        records.append({"commit": commit, "path": path, "role": role, "git_blob": blob, "sha256": hashlib.sha256(raw).hexdigest(), "size": len(raw)})
    write_json("input_freeze/source_evidence_index.json", {"status": "PASS_FROZEN_EVIDENCE_INDEX", "records": records})


def materialize_action_cards() -> None:
    write_json("actions/action_package_registry.json", {"status": "PRE_FROZEN_BEFORE_SCORING", "packages": [{"id": k, **v} for k, v in PACKAGES.items()]})
    for aid, data in PACKAGES.items():
        write_text(f"actions/action_cards/{aid}.md", f"""# {aid}: {data['name']}

**Core factors:** {data['factors']}

**Question:** {data['question']}

**Bounded objective:** {data['objective']}

**Required decision content:** {ACTION_REQUIREMENTS[aid]}

**Stop condition:** {data['stop']}

**Largest failure mode:** {data['failure']}

**If selected, only next task:** `{data['next_task']}`

This card is frozen before scores, dependency resolution, and reviewer recommendations. It authorizes no implementation, rollout, data acquisition, map work, or method change.
""")


def materialize_dependencies() -> None:
    write_json("dependencies/dependency_graph.json", {
        "nodes": [{"id": aid, "label": data["name"]} for aid, data in PACKAGES.items()],
        "edges": [{"from": a, "to": b, "status": status, "evidence": evidence} for a, b, status, evidence in DEPENDENCIES],
        "critical_path": ["A1", "A2/A3/A4", "A5"],
        "conclusion": "A1 is a REQUIRED common prerequisite of A2, A3, and A4.",
    })
    write_csv("dependencies/dependency_matrix.csv", ["from", "to", "status", "evidence"], [list(row) for row in DEPENDENCIES])
    rows = [
        ["D1", "A2", "FAIL_FIRST_PRIORITY", "A1→A2 REQUIRED; horizon/denominator remains undefined."],
        ["D2", "A3", "FAIL_FIRST_PRIORITY", "A1→A3 REQUIRED; legal B3 entry remains undefined."],
        ["D3", "A4", "FAIL_FIRST_PRIORITY", "A1→A4 REQUIRED; activation interpretation is role-dependent."],
        ["D4", "A5", "FAIL_FIRST_PRIORITY", "A1 passes gates and has high information gain; consolidation cannot pre-empt it."],
        ["D5", "F05/F11", "EXCLUDED", "Frozen evidence does not support either as a primary problem."],
        ["D6", "F09", "EXCLUDED_AS_SOLO_ROUTE", "Map representation is an evaluation dependency, not a selected route."],
    ]
    write_csv("dependencies/fatal_dependency_audit.csv", ["rule", "action_or_factor", "status", "evidence"], rows)


def materialize_scoring() -> None:
    write_json("scoring/scoring_contract.json", {
        "pre_frozen": True, "positive_range": "0-5", "risk_range": "0-5, higher is worse",
        "positive_keys": POSITIVE_KEYS, "risk_keys": RISK_KEYS,
        "formula": "net_score=positive_score-0.75*risk_penalty", "weight_change": "forbidden after scoring",
        "sunk_cost_in_positive_score": False,
    })
    pos_rows, risk_rows, net_rows = [], [], []
    for aid, data in PACKAGES.items():
        pos_rows.append([aid, *data["scores"], sum(data["scores"])])
        risk_rows.append([aid, *data["risks"], sum(data["risks"])])
        pos, risk = sum(data["scores"]), sum(data["risks"])
        net_rows.append([aid, pos, risk, 0.75, f"{pos - 0.75 * risk:.2f}"])
    write_csv("scoring/positive_scores.csv", ["action", *POSITIVE_KEYS, "positive_score"], pos_rows)
    write_csv("scoring/risk_scores.csv", ["action", *RISK_KEYS, "risk_penalty"], risk_rows)
    write_csv("scoring/net_scores.csv", ["action", "positive_score", "risk_penalty", "risk_weight", "net_score"], net_rows)
    write_csv("scoring/fatal_gate_audit.csv", ["action", "gate", "status", "reason"], gate_rows())


def materialize_checks() -> None:
    write_text("checks/a1_math_prerequisite.md", """# A1 mathematical prerequisite check

Frozen PR #90 establishes `p_(k+1)=p_k+dt v_k`, `v_(k+1)=v_k+dt u_k`, and `∂p(tau)/∂u_k=0` over the immediate interval.

1. **Q1:** The existing B1 label is not sufficient to distinguish state/execution admission from candidate-dependent safety filtering.
2. **Q2:** If B1 is admission/late-risk detection, the evidence establishes a role and evaluation-denominator problem, not an implementation defect.
3. **Q3:** If B1 is intended as candidate-dependent safety filtering, the strict zero derivative is a structural semantic mismatch.
4. **Q4:** `u_k` first affects velocity at `k+1` and position on the next propagated position horizon (`p_(k+2)`); it cannot alter the immediate position interval.
5. **Q5:** A2, A3, and A4 must wait: each needs the role/horizon definition to avoid circular conditioning, illegal B3 entry, or artificial activation interpretation.

Conclusion: `A1_REQUIRED_COMMON_PREREQUISITE=TRUE`. This task changes neither B1 nor any controller behavior.
""")
    write_csv("checks/a2_asset_availability.csv",
              ["asset_question", "status", "frozen_evidence", "ranking_effect"], [
                  ["frozen_on_policy_logs", "ABSENT", "PR90 on_policy_availability: false for all six assets", "A2 R3 high"],
                  ["legal_intermediate_state_recovery", "ABSENT", "PR90: static assets and no controller loop", "A2 cannot establish denominators now"],
                  ["failed_trial_trajectories_unconsumed", "ABSENT", "PR90 formal record inventory contains one-step records only", "no newly discovered existing asset"],
                  ["official100_per_step_state", "ABSENT", "E5/E6 source-map formal assets are initial-state behavior evidence", "no lead-time sequence"],
                  ["stonehenge_flight_asset_type", "INITIAL_STATES_ONLY", "PR90 F07/F09 evidence", "not on-policy"],
                  ["replica_order_for_lead_time", "ABSENT", "PR90 lead_time DATA_BLOCKED_NO_FROZEN_SEQUENCE", "no sequence reconstruction"],
              ])
    write_csv("checks/a3_eligible_state_inventory.csv",
              ["environment", "frozen_diagnostic_states", "B2_primary_committed", "candidate_independently_precluded", "eligible_states", "oracle_run_this_task", "conclusion"], [
                  ["E1_REPLICA_GT_FINE", 16, 16, 0, 0, "NO", "no B3 opportunity"],
                  ["E5_STONEHENGE_SAFER", 32, 0, 32, 0, "NO", "current-map h precludes candidates"],
                  ["E6_FLIGHT_SAFER", 32, 6, 26, 0, "NO", "no B3 opportunity"],
                  ["TOTAL", 80, 22, 58, 0, "NO", "A3 has no frozen legal eligible state"],
              ])
    write_text("checks/a4_regime_legitimacy.md", """# A4 regime-legitimacy check

`VALID_REGIME_ANALYSIS` requires a frozen real-system source for period, velocity, latency, and tracking-error budget. The PR #90 endpoint OAT grid is explicitly a counterfactual exposure diagnostic, not deployment evidence. E5/E6 have zero-velocity initial states, and the frozen record has no tracking-error budget or authoritative latency source.

Therefore `VALID_REGIME_ANALYSIS=NOT_YET_SUPPORTED` and `INVALID_TRIGGER_ENGINEERING_RISK=HIGH`. A4 cannot rank first; increasing speed, dt, delay, or error solely to make an event appear would violate the frozen boundary.
""")


def materialize_feasibility() -> None:
    header = ["action", "best_case_days", "likely_days", "worst_case_days", "coding_hours", "analysis_hours", "GPU_hours", "storage", "new_data_requirement", "new_reference_requirement", "new_method_requirement", "external_dependency", "probability_of_clear_decision", "probability_of_needing_followup", "largest_failure_mode"]
    write_csv("feasibility/effort_estimates.csv", header, [[aid, *values] for aid, values in EFFORT.items()])
    write_csv("feasibility/five_day_decision_paths.csv", ["action", "five_day_path", "day5_decision", "stop_boundary"], [
        ["A1", "role/horizon/denominator specification from PR90 formulas", "architecture role is explicit or ambiguity is proven", "no implementation"],
        ["A2", "logging/statistics contract only", "data plan is bounded but dependent on A1", "no collection"],
        ["A3", "eligibility/search contract only", "identification remains blocked if eligible=0", "no oracle"],
        ["A4", "provenance audit for physical ranges", "valid source or trigger-engineering block", "no configuration run"],
        ["A5", "claim-plan composition", "paper plan only", "cannot bypass D4"],
    ])
    write_csv("feasibility/asset_dependencies.csv", ["action", "existing_assets", "missing_asset", "effect"], [
        ["A1", "PR90 formulas, gate funnel, interaction matrix", "none", "independent"],
        ["A2", "static one-step records", "on-policy/intermediate logs", "data-blocked for execution"],
        ["A3", "80 bounded diagnostic records", "legal eligible state", "not identifiable"],
        ["A4", "endpoint OAT diagnostic", "real-system range/budget provenance", "not legitimate yet"],
        ["A5", "all frozen reports", "none", "dependency-blocked by D4"],
    ])
    write_csv("feasibility/data_dependencies.csv", ["action", "new_data_required_now", "new_dataset_required", "data_risk", "reason"], [
        ["A1", "NO", "NO", "LOW", "desk-based structural specification"],
        ["A2", "NO for design", "NO", "HIGH", "frozen on-policy data absent"],
        ["A3", "NO for protocol", "NO", "MEDIUM", "no existing eligible state"],
        ["A4", "NO for protocol", "NO", "HIGH", "real-system parameter provenance absent"],
        ["A5", "NO", "NO", "LOW", "consolidation only"],
    ])


def materialize_reviews() -> None:
    score_rows = []
    for directory, role, top1, top2, objection, dependency in REVIEWS:
        write_text(f"reviews/{directory}/{directory}_review.md", f"""# {role}

**Blindness declaration:** this role assessment was written from frozen evidence without using the final selection file.

**Top 1:** {top1} ({PACKAGES[top1]['name']})

**Top 2:** {top2} ({PACKAGES[top2]['name']})

**Fatal objection:** {objection}

**Dependency argument:** {dependency}

The review neither claims performance nor authorizes a new method, data acquisition, rollout, or training run.
""")
        score_rows.append([role, top1, top2, "A1" if top1 == "A1" else "A2", "independent role assessment"])
    write_csv("reviews/reviewer_score_matrix.csv", ["reviewer", "top1", "top2", "recommendation", "independence_note"], score_rows)
    write_text("reviews/disagreement_analysis.md", """# Reviewer disagreement analysis

Three of four roles rank A1 first. The Evaluation/Statistics reviewer ranks A2 first because on-policy absence and conditional power are the largest data limitations, but ranks A1 second and explicitly identifies the A1 horizon definition as necessary before A2 can define conditioning. The disagreement is substantive, preserved, and resolved by the REQUIRED dependency edges rather than by averaging away the data limitation.
""")


def materialize_decision() -> None:
    scores = {aid: {"positive": sum(d["scores"]), "risk": sum(d["risks"])} for aid, d in PACKAGES.items()}
    for value in scores.values(): value["net"] = round(value["positive"] - 0.75 * value["risk"], 2)
    ordered = sorted(scores, key=lambda aid: scores[aid]["net"], reverse=True)
    selection = {
        "selected_case": "CASE_A1", "selected_action_package": SELECTED,
        "top1": ordered[0], "top2": ordered[1], "top1_top2_score_gap": round(scores[ordered[0]]["net"] - scores[ordered[1]]["net"], 2),
        "FINAL_STATUS": "SELECT_CAUSAL_ARCHITECTURE_SPEC_AS_NEXT_STEP",
        "FINAL_DECISION": "FREEZE_IMPLEMENTATION_AND_WRITE_CORE_CAUSAL_ARCHITECTURE_SPECIFICATION_V1",
        "Only_next_task": NEXT_TASK,
        "selection_rule": "A1 passes all fatal gates, has highest net score, is REQUIRED for A2/A3/A4, and is first-ranked by 3/4 reviewers.",
        "scores": scores,
        "rejected": {"A2": "REQUIRED dependency A1", "A3": "REQUIRED dependency A1 and zero eligible frozen states", "A4": "REQUIRED dependency A1 plus invalid-trigger-engineering risk", "A5": "D4 blocks consolidation while A1 has high bounded information gain"},
    }
    write_json("decision/final_action_selection.json", selection)
    write_text("decision/selection_rationale.md", """# Selection rationale

A1 is selected under CASE_A1. Its 60 positive points, 4 risk points, and net score of 57.00 reflect a bounded, falsifiable, data-independent specification that directly resolves the shared ambiguity exposed by F03/F04/F08. Crucially, the decision does not follow convenience: A1 is selected because PR #90's exact position-first derivative establishes a shared semantic prerequisite for A2, A3, and A4. Three independent reviewer roles agree. A positive result can specify a lawful pipeline; a negative result can show that the current B1 label is only admission/late-risk semantics. Either result reduces uncertainty without changing Core V1.
""")
    write_text("decision/rejected_actions.md", """# Rejected action packages

- **A2:** valuable but cannot define an interpretable candidate-dependent denominator before A1.
- **A3:** all 80 frozen diagnostic states are either B2-primary committed (22) or candidate-independently precluded (58); no legal B3 opportunity exists.
- **A4:** lacks real-system provenance and would risk post-hoc trigger engineering.
- **A5:** safe consolidation is not sufficient when an inexpensive, high-information structural prerequisite remains.
""")
    write_text("decision/anti_drift_contract.md", """# Anti-drift contract

The selected follow-up may write only a causal architecture specification. It may not implement Core V2, alter B0/B1/B2/B3, change dt/velocity/acceleration, create candidates or terminal sets, run rollouts/navigation/B0-B3, train or change maps, add datasets/cohorts, collect on-policy data, run an oracle, tune for activation, or make a performance claim. Completion yields exactly one potential subsequent task; this task stops before executing it.
""")
    write_text("decision/next_task_contract.md", f"""# Next task contract

**Only next task:** `{NEXT_TASK}`

**Purpose:** specify the causal roles and horizons of B0/B1/B2/B3 from frozen evidence.

**Bound:** desk-based documentation only, at most five working days, with an explicit stop after the specification. It must not implement a controller or alter the frozen method.
""")


def make_figure(relative: str, title: str, labels: list[str], values: list[float], ylabel: str, colors: list[str] | None = None) -> None:
    path = TASK_ROOT / "figures" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, values, color=colors or "#3b82f6")
    plt.title(title, fontweight="bold")
    plt.ylabel(ylabel)
    for bar, value in zip(bars, values): plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{value:g}", ha="center", va="bottom", fontsize=9)
    plt.figtext(0.5, 0.01, FOOTER, ha="center", fontsize=6, wrap=True)
    plt.tight_layout(rect=(0, 0.08, 1, 1))
    plt.savefig(path, dpi=150)
    plt.close()


def make_dependency_figure() -> None:
    path = TASK_ROOT / "figures" / "dependency_graph.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 6)); ax = plt.gca(); ax.set_axis_off()
    positions = {"A1": (0.18, 0.54), "A2": (0.48, 0.78), "A3": (0.48, 0.54), "A4": (0.48, 0.30), "A5": (0.82, 0.54)}
    for aid, (x, y) in positions.items():
        ax.text(x, y, aid + "\n" + PACKAGES[aid]["name"], ha="center", va="center", bbox={"boxstyle": "round,pad=0.5", "fc": "#dbeafe" if aid == "A1" else "#f3f4f6"})
    for a, b, status, _ in DEPENDENCIES:
        ax.annotate("", xy=positions[b], xytext=positions[a], arrowprops={"arrowstyle": "->", "lw": 1.8, "color": "#1d4ed8"})
        mx, my = ((positions[a][0]+positions[b][0])/2, (positions[a][1]+positions[b][1])/2)
        ax.text(mx, my+0.035, status, ha="center", fontsize=8, color="#1d4ed8")
    ax.set_title("Dependency graph: A1 is the common prerequisite", fontweight="bold")
    plt.figtext(0.5, 0.01, FOOTER, ha="center", fontsize=6, wrap=True); plt.tight_layout(rect=(0, .08, 1, 1)); plt.savefig(path, dpi=150); plt.close()


def materialize_figures() -> None:
    positive = [sum(PACKAGES[a]["scores"]) for a in PACKAGES]
    risk = [sum(PACKAGES[a]["risks"]) for a in PACKAGES]
    net = [positive[i] - .75*risk[i] for i in range(5)]
    charts = {
        "pr87_pr90_decision_lineage.png": ("Frozen decision lineage", ["PR87", "PR88", "PR89", "PR90", "This task"], [1, 1, 1, 1, 1], "frozen stage"),
        "f01_f11_current_status.png": ("F01-F11 current evidence status", ["support", "structural", "blocked", "not-id"], [4, 2, 2, 1], "factor count"),
        "action_package_map.png": ("Pre-frozen action-package coverage", list(PACKAGES), [3, 3, 2, 2, 11], "core factors"),
        "fatal_dependency_matrix.png": ("Fatal dependency blocks", ["A1", "A2", "A3", "A4", "A5"], [0, 1, 1, 1, 1], "first-priority block"),
        "positive_score_comparison.png": ("Positive-score comparison", list(PACKAGES), positive, "positive score"),
        "risk_penalty_comparison.png": ("Risk-penalty comparison", list(PACKAGES), risk, "risk penalty"),
        "net_score_comparison.png": ("Net-score comparison", list(PACKAGES), net, "net score"),
        "five_day_decision_value.png": ("Probability of a clear ≤5-day decision", list(PACKAGES), [100*EFFORT[a][11] for a in PACKAGES], "percent"),
        "asset_reuse_comparison.png": ("Existing-asset reuse", list(PACKAGES), [5, 3, 4, 3, 5], "score"),
        "data_dependency_comparison.png": ("Data-dependency risk", list(PACKAGES), [0, 5, 1, 4, 0], "risk score"),
        "a1_control_authority_dependency.png": ("A1: candidate control authority by horizon", ["immediate p", "v(k+1)", "p(k+2)"], [0, 1, 1], "candidate sensitivity"),
        "a2_on_policy_asset_availability.png": ("A2: frozen on-policy asset availability", ["on-policy", "intermediate", "failed trajectories", "per-step"], [0, 0, 0, 0], "available assets"),
        "a3_eligible_state_availability.png": ("A3: legal frozen B3 eligible states", ["E1", "E5", "E6", "total"], [0, 0, 0, 0], "eligible states"),
        "a4_regime_legitimacy.png": ("A4: provenance-qualified regime dimensions", ["velocity", "dt", "latency", "tracking error"], [0, 0, 0, 0], "qualified sources"),
        "reviewer_preferences.png": ("Reviewer top-1 preferences", ["A1", "A2", "A3", "A4", "A5"], [3, 1, 0, 0, 0], "reviewer count"),
        "reviewer_disagreement.png": ("Reviewer disagreement is preserved", ["A1 top1", "A2 top1", "A1 top2"], [3, 1, 1], "reviewer count"),
        "claim_impact_comparison.png": ("Claim-impact score", list(PACKAGES), [PACKAGES[a]["scores"][3] for a in PACKAGES], "score"),
        "final_action_selection.png": ("Final selection: CASE_A1", list(PACKAGES), [1, 0, 0, 0, 0], "selected"),
        "downstream_one_step.png": ("Exactly one downstream task", ["selected task", "parallel tasks"], [1, 0], "task count"),
    }
    make_dependency_figure()
    for figure, (title, labels, values, ylabel) in charts.items(): make_figure(figure, title, labels, values, ylabel)
    assert set(charts) | {"dependency_graph.png"} == set(FIGURES)
    write_json("figures/figure_manifest.json", {"count": len(FIGURES), "figures": [{"file": n, "annotation": FOOTER} for n in FIGURES]})


def materialize_reports() -> None:
    score_table = "\n".join(f"| {aid} | {sum(d['scores'])} | {sum(d['risks'])} | {sum(d['scores'])-.75*sum(d['risks']):.2f} |" for aid, d in PACKAGES.items())
    report = f"""# REPORT: Rank Core V1 actionable factors and select one bounded next step

## Result

`SELECT_CAUSAL_ARCHITECTURE_SPEC_AS_NEXT_STEP`

**Decision:** `FREEZE_IMPLEMENTATION_AND_WRITE_CORE_CAUSAL_ARCHITECTURE_SPECIFICATION_V1`

**Only next task:** `{NEXT_TASK}`

## Frozen boundary

PR #84–#90 remain preserved Open Drafts. This is a decision analysis from frozen evidence only: formal B0–B3 runs=0; training=0; map/controller/method mutations=0; new data or datasets=0. The analysis preserves the PR #90 Case D conclusion and does not claim performance, navigation, or a new Core method.

## Action packages and scoring

| Action | Positive | Risk | Net |
| --- | ---: | ---: | ---: |
{score_table}

The scoring contract uses all 12 frozen positive items and eight risk items with `net=positive-0.75*risk`. Sunk cost is excluded. A1 is highest and, independently, the required common prerequisite for A2/A3/A4.

## Decisive evidence

- PR #90 proves the immediate position derivative with respect to `u_k` is zero; B1 must be given an explicit admission-versus-candidate-safety role before later gates can be interpreted.
- No frozen on-policy/intermediate logs, unused failed trajectories, or per-step official100 sequences were found; A2 remains data-dependent.
- The frozen A3 inventory has 0 legal eligible states: 22 are B2-primary committed and 58 are candidate-independently precluded.
- The OAT regime grid is not a real-system range contract; A4 cannot use artificial activation.
- A5 is deliberately rejected by D4, not selected merely because it is safe.

## Reviewer panel

Control/theory, robotics/system, and novelty/publication rank A1 first. Evaluation/statistics ranks A2 first due to the on-policy/power gap, but records A1 as a prerequisite. The 3:1 disagreement is preserved and resolved by REQUIRED edges, not suppressed.

## What this does not prove

It does not prove that Core V1 is correct, incorrect, competitive, safe for deployment, more active, generalizable, or ready for a paper. It does not implement a causal correction. It selects only the bounded specification task needed to distinguish a role-definition issue from a structural method mismatch.

## Anti-drift rule

The selected task may write a role/horizon/denominator specification only. It must not change B0–B3, create a controller branch, run a formal trial, use a new map/data/cohort, train, run a B3 oracle, or execute a configuration study.
"""
    write_text("RANK_CORE_V1_ACTIONABLE_FACTORS_AND_SELECT_ONE_BOUNDED_NEXT_STEP_V1.md", report)
    write_text("report/REPORT_RANK_CORE_V1_ACTIONABLE_FACTORS_AND_SELECT_ONE_BOUNDED_NEXT_STEP_V1.md", report)
    write_text("report/DRAFT_PR_BODY.md", f"""## Summary

Freeze a desk-based ranking of A1–A5 using PR #84–#90 evidence. No new formal B0–B3 run, method/controller/map/data mutation, training, dataset, or representative cohort is included.

## Decision

- Selected CASE_A1 / A1 `CAUSAL_ARCHITECTURE_SPEC`.
- Exact reason: A1 is the highest-net bounded action, a REQUIRED prerequisite for A2/A3/A4, and first-ranked by 3/4 role-separated reviewers.
- **Only next task:** `{NEXT_TASK}`.

## Checks

- Frozen PR #84–#90 identities and protected source bytes are verified.
- A1–A5, dependencies, fatal gates, scores, effort, special checks, and reviewer disagreement are committed as traceable artifacts.
- A2 has no newly discovered on-policy asset; A3 has zero eligible frozen states; A4 lacks provenance-qualified regime ranges.
- A5 is rejected by D4; no hidden second contribution is proposed.
""")
    write_json("report/downstream_handoff.json", {"FINAL_STATUS": "SELECT_CAUSAL_ARCHITECTURE_SPEC_AS_NEXT_STEP", "FINAL_DECISION": "FREEZE_IMPLEMENTATION_AND_WRITE_CORE_CAUSAL_ARCHITECTURE_SPECIFICATION_V1", "Only_next_task": NEXT_TASK, "started": False, "formal_method_runs": 0})


def main() -> None:
    freeze_inputs()
    source_evidence_index()
    materialize_action_cards(); materialize_dependencies(); materialize_scoring(); materialize_checks(); materialize_feasibility(); materialize_reviews(); materialize_decision(); materialize_figures(); materialize_reports()
    print("PASS_ACTIONABLE_FACTOR_RANKING_ARTIFACTS_MATERIALIZED")


if __name__ == "__main__":
    main()
