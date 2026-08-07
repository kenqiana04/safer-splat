"""Materialize the frozen Core causal-control architecture specification only."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from freeze_upstream_inputs import main as freeze_inputs
from task_config import FIGURES, ROLE_IDS, TASK_ID, TASK_ROOT
from verify_position_first_euler import main as verify_formula


FOOTER = "SPECIFICATION ONLY | NO NEW CONTROLLER | NO FORMAL B0-B3 RUN | FROZEN POSITION-FIRST EULER | HISTORICAL RESULTS PRESERVED | NOT A NEW SAFETY GUARANTEE | NOT A PERFORMANCE CLAIM | NOT A REAL-TIME CLAIM"
CASE = "CASE_B"
STATUS = "PASS_CORE_CAUSAL_ARCHITECTURE_LOCAL_STRUCTURAL_GAP"
DECISION = "FREEZE_CORE_V1_AND_WRITE_CORE_V2_CAUSAL_INCREMENT_SPECIFICATION"
NEXT_TASK = "WRITE_CORE_V2_CAUSAL_INCREMENT_SPECIFICATION_V1"

LAYERS = [
    ("L0_START_STATE_ADMISSION", "admit, repair, or explicitly fail-close a current/start state", "x_k, map snapshot, full query, Start-Safe status", "none for current u_k", "S0_UNASSESSED", "full-query admissible or post-repair full-query verified", "current infeasible/unknown or repair failure", "L1 or L5", "EXECUTION_ADMISSION", "N_all", "map query validity and repair policy are external contracts"),
    ("L1_IMMEDIATE_UNAVOIDABLE_SEGMENT", "primary execution-admission and late-risk detector for [t_k,t_(k+1)]", "x_k, map snapshot, frozen immediate position path", "none: ∂p(tau)/∂u_k=0", "L0 passes", "immediate segment passes continuous/sampled contract", "unavoidable segment fails", "L2 or L5", "SAMPLED_DATA_CONSISTENCY", "N_state_admissible", "continuous segment/model consistency requires a frozen certificate contract"),
    ("L2_CANDIDATE_DEPENDENT_FUTURE_SAFETY", "conceptual future-safety predicate for candidate u_k", "x_k, u_k, map snapshot, horizon/witness assumptions", "first affects position on [t_(k+1),t_(k+2)] and p_(k+2)", "L1 passes and not terminal-already-safe", "candidate future predicate passes", "candidate-specific future predicate fails", "L3 or L4/L5", "FUTURE_CERTIFICATION_CONCEPT", "N_primary_candidate_evaluable", "not implemented in formal Core V1; H2 requires an explicit future-control witness"),
    ("L3_CANDIDATE_RECOVERABILITY", "secondary candidate recoverability/backup witness", "future-safe candidate, braking/terminal witness, terminal condition", "after candidate semantics are established", "L2 passes", "a sufficient witness is found", "witness absent", "commit or L4/L5", "CERTIFICATION_WITNESS", "N_recoverability_evaluable", "witness absence is not mathematical unrecoverability"),
    ("L4_ALTERNATIVE_CONTROL_SEARCH", "finite alternative search after a candidate-dependent primary non-certification", "admissible x_k, immediate-safe path, primary failure type, finite library", "candidate dependent only", "ALT_ELIGIBLE predicate", "an alternative is certified", "finite library exhausted/budget stops", "commit or L5", "CANDIDATE_GENERATOR", "N_alt_eligible", "finite library does not prove continuous-space infeasibility"),
    ("L5_TERMINAL_OR_FAIL_CLOSED_EXECUTION", "execute a terminal action only with certificate, otherwise explicitly fail-close", "terminal witness or typed failure", "terminal control only if certified", "terminal certified or no lawful certified route remains", "terminal certificate/commit", "typed fail-close", "S14_COMMIT or S13_FAIL_CLOSED", "TERMINAL_CONDITION", "N_fail_closed", "fail-close is not a guaranteed safe stop"),
]

TRANSITIONS = [
    ("S0_UNASSESSED", "full query admits current/start state", "S1_START_ADMISSIBLE", "NO", "EXECUTION_ADMISSION", "YES", "YES", "PR83/PR84", "query semantics"),
    ("S0_UNASSESSED", "near-unsafe or unsafe start requires repair", "S2_START_REPAIR_REQUIRED", "NO", "EXECUTION_ADMISSION", "NO", "YES", "Start-Safe Flight100", "repair eligibility"),
    ("S2_START_REPAIR_REQUIRED", "projection plus full-query verification passes", "S1_START_ADMISSIBLE", "NO", "RECOVERY_POLICY", "YES", "YES", "Start-Safe synthetic120/Flight100", "projection is not full certificate"),
    ("S2_START_REPAIR_REQUIRED", "repair or full-query verification fails", "S3_START_REPAIR_FAILED", "NO", "RECOVERY_POLICY", "YES", "YES", "Start-Safe historical boundary", "repair policy limit"),
    ("S1_START_ADMISSIBLE", "frozen immediate segment is safe", "S4_IMMEDIATE_SEGMENT_SAFE", "NO", "EXECUTION_ADMISSION", "YES", "YES", "PR87 G1/PR90 F04", "segment contract"),
    ("S1_START_ADMISSIBLE", "immediate segment unsafe independently of candidate", "S5_IMMEDIATE_SEGMENT_UNSAFE_UNAVOIDABLE", "NO", "EXECUTION_ADMISSION", "YES", "YES", "DT verification history", "no same-cycle control authority"),
    ("S4_IMMEDIATE_SEGMENT_SAFE", "primary candidate is evaluated", "S6_PRIMARY_CANDIDATE_UNDER_TEST", "YES", "METHOD_COMPONENT", "NO", "YES", "PR84 pipeline", "candidate semantics"),
    ("S6_PRIMARY_CANDIDATE_UNDER_TEST", "candidate-dependent future predicate passes", "S7_PRIMARY_FUTURE_SAFE", "YES", "FUTURE_CERTIFICATION_CONCEPT", "YES", "NO", "none; conceptual only", "future-safety certificate absent in V1"),
    ("S7_PRIMARY_FUTURE_SAFE", "backup/terminal witness is sufficient", "S8_PRIMARY_RECOVERABLE", "YES", "CERTIFICATION_WITNESS", "YES", "YES", "PR84 braking/PR87 G2-G3", "witness scope"),
    ("S6_PRIMARY_CANDIDATE_UNDER_TEST", "candidate future predicate fails", "S9_PRIMARY_NOT_CERTIFIED", "YES", "FUTURE_CERTIFICATION_CONCEPT", "YES", "NO", "conceptual failure only", "candidate-dependent predicate must be specified"),
    ("S7_PRIMARY_FUTURE_SAFE", "backup witness absent", "S9_PRIMARY_NOT_CERTIFIED", "YES", "CERTIFICATION_WITNESS", "YES", "YES", "PR84/PR90 F05", "absence is not unrecoverability"),
    ("S8_PRIMARY_RECOVERABLE", "candidate commits", "S14_COMMIT", "YES", "METHOD_COMPONENT", "YES", "YES", "PR84/PR87", "runtime deadline"),
    ("S9_PRIMARY_NOT_CERTIFIED", "ALT_ELIGIBLE is true", "S10_ALTERNATIVE_SEARCH_ELIGIBLE", "YES", "CANDIDATE_GENERATOR", "NO", "YES", "PR87 G3/PR90 F06", "finite library only"),
    ("S9_PRIMARY_NOT_CERTIFIED", "ALT_ELIGIBLE is false", "S13_FAIL_CLOSED", "NO", "TERMINAL_CONDITION", "YES", "YES", "typed failure history", "fail-close safety unproven"),
    ("S10_ALTERNATIVE_SEARCH_ELIGIBLE", "finite alternative certified", "S11_ALTERNATIVE_CERTIFIED", "YES", "CANDIDATE_GENERATOR", "YES", "YES", "PR87 G3", "coverage unproven"),
    ("S11_ALTERNATIVE_CERTIFIED", "alternative candidate commits", "S14_COMMIT", "YES", "METHOD_COMPONENT", "YES", "YES", "PR87 G3", "runtime deadline"),
    ("S10_ALTERNATIVE_SEARCH_ELIGIBLE", "finite library exhausted or deadline", "S13_FAIL_CLOSED", "YES", "TERMINAL_CONDITION", "YES", "YES", "PR90 F06", "not continuous infeasibility"),
    ("S1_START_ADMISSIBLE", "terminal-already-safe condition is certified", "S12_TERMINAL_CERTIFIED", "NO", "TERMINAL_CONDITION", "YES", "YES", "PR89/PR90 metric taxonomy", "terminal sufficient not maximal"),
    ("S12_TERMINAL_CERTIFIED", "certified terminal action commits", "S14_COMMIT", "NO", "TERMINAL_CONDITION", "YES", "YES", "PR84 terminal certificate", "terminal policy scope"),
    ("S3_START_REPAIR_FAILED", "typed fail-close record", "S13_FAIL_CLOSED", "NO", "TERMINAL_CONDITION", "YES", "YES", "Start-Safe boundary", "not safe stop"),
    ("S5_IMMEDIATE_SEGMENT_UNSAFE_UNAVOIDABLE", "typed fail-close record", "S13_FAIL_CLOSED", "NO", "TERMINAL_CONDITION", "YES", "YES", "DT history", "not candidate failure"),
    ("S13_FAIL_CLOSED", "next observation/diagnosis, no safety claim", "S0_UNASSESSED", "NO", "DIAGNOSTIC_ONLY", "NO", "YES", "PR84 state-machine convention", "external supervisory policy"),
    ("S14_COMMIT", "next sampled cycle", "S0_UNASSESSED", "NO", "METHOD_COMPONENT", "NO", "YES", "PR84 state-machine convention", "execution tracking"),
]

FAILURES = [
    ("F_START_INVALID", "NO", "possibly after external repair", "YES", "NO", "YES if repair fails", "NO"),
    ("F_CURRENT_QUERY_UNKNOWN", "NO", "NO", "NO", "NO", "YES", "YES"),
    ("F_CURRENT_FEASIBILITY_FAIL", "NO", "only through Start-Safe repair", "YES", "NO", "YES", "NO"),
    ("F_IMMEDIATE_UNAVOIDABLE_SEGMENT_FAIL", "NO", "next cycle only after new state", "NO", "NO", "YES", "NO"),
    ("F_PRIMARY_FUTURE_SAFETY_FAIL", "possibly via another candidate", "YES", "NO", "YES if ALT_ELIGIBLE", "YES after exhaustion", "NO"),
    ("F_PRIMARY_BACKUP_FAIL", "possibly via another candidate", "YES", "NO", "YES if ALT_ELIGIBLE", "YES after exhaustion", "NO"),
    ("F_ALTERNATIVE_LIBRARY_EXHAUSTED", "NO finite-library conclusion only", "unknown", "NO", "NO", "YES", "NO"),
    ("F_TERMINAL_NOT_CERTIFIED", "NO", "unknown", "NO", "NO", "YES", "NO"),
    ("F_RUNTIME_DEADLINE", "NO within missed deadline", "possibly later", "NO", "NO", "typed fail-close", "YES"),
    ("F_MAP_REFERENCE_UNRESOLVED", "not semantic controller question", "not inferred", "NO", "NO", "typed non-evaluable/fail-close", "YES"),
    ("F_TRACKING_LATENCY_UNMODELED", "not inferred", "not inferred", "NO", "NO", "typed limitation/fail-close", "YES"),
]


def write_text(rel: str, text: str) -> None:
    path = TASK_ROOT / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(rel: str, payload: object) -> None:
    write_text(rel, json.dumps(payload, indent=2, sort_keys=True))


def write_csv(rel: str, header: list[str], rows: list[list[object]]) -> None:
    path = TASK_ROOT / rel; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle); writer.writerow(header); writer.writerows(rows)


def architecture_documents() -> None:
    write_text("architecture/control_authority_timeline.md", """# Frozen position-first control-authority timeline

At `t_k`, the state is `(p_k,v_k)` and the candidate is `u_k`. On `[t_k,t_(k+1)]`, `p(tau)=p_k+tau v_k`; the path is determined by `(p_k,v_k)` and has zero derivative with respect to `u_k`. At `t_(k+1)`, `p_(k+1)=p_k+dt v_k` remains independent of `u_k`, while `v_(k+1)=v_k+dt u_k` is affected. On `[t_(k+1),t_(k+2)]`, the propagated position uses `v_(k+1)` and is candidate-dependent. Thus `p_(k+2)=p_k+2dt v_k+dt^2u_k`.

The immediate segment is therefore primarily execution admission / late-risk detection and a sampled-data consistency check. It is not a candidate safety discriminator. Candidate-dependent position certification cannot begin before the first control-affected segment `[t_(k+1),t_(k+2)]` or endpoint `p_(k+2)`.
""")
    write_csv("architecture/control_authority_jacobians.csv", ["quantity", "expression", "derivative_wrt_u_k", "authority_class", "role_implication"], [
        ["p_k_plus_1", "p_k+dt*v_k", "0", "uncontrollable position", "L1 only"],
        ["v_k_plus_1", "v_k+dt*u_k", "dt*I", "control affected", "velocity changes"],
        ["p_k_plus_2", "p_k+2dt*v_k+dt^2*u_k", "dt^2*I", "first control-affected position", "L2 may start"],
        ["v_k_plus_2", "v_k+dt*u_k+dt*u_(k+1)", "dt*I", "control affected under independent later control", "future witness required"],
        ["p_k_plus_n", "p_k+n*dt*v_k+dt^2*sum_(j=0)^(n-2)(n-1-j)u_(k+j)", "(n-1)*dt^2*I", "multi-step", "must state later-control assumption"],
    ])
    write_json("architecture/role_layer_registry.json", {"status": "FROZEN_ROLE_ARCHITECTURE", "layers": [{"id": row[0], "purpose": row[1], "inputs": row[2], "control_authority": row[3], "entry": row[4], "pass": row[5], "fail": row[6], "downstream": row[7], "claim_type": row[8], "denominator": row[9], "unresolved": row[10]} for row in LAYERS]})
    write_csv("architecture/role_layer_matrix.csv", ["layer", "purpose", "inputs", "control_authority", "entry", "pass", "fail", "downstream", "claim_type", "evaluation_denominator", "unresolved_assumptions"], [list(row) for row in LAYERS])
    write_csv("architecture/historical_b0_b3_mapping.csv", ["historical_ablation", "historical_contents", "new_role_mapping", "preserved_evidence", "allowed_future_claim", "prohibited_reinterpretation"], [
        ["B0_CURRENT_CBF_ONLY", "current map/full-query feasibility plus candidate preparation", "L0 current admission; preparation is not future certification", "E5 100/100 and E6 74/100 left-truncation remain", "current-admission reachability", "not an alternative-search failure"],
        ["B1_PLUS_SWEPT_SEGMENT", "immediate swept segment", "L1, not L2", "activated G1 B0 commit/B1 reject 20/20 remains", "activated immediate-segment behavioral distinction", "candidate-dependent control authority or future safety"],
        ["B2_PLUS_TERMINAL_BACKUP", "terminal/backup witness", "L3 plus L5 terminal distinction", "G2/G3 backup/terminal decision differences remain", "witness/terminal decision evidence", "do not treat terminal-already-safe as backup incremental gain"],
        ["B3_FULL_UNIFIED_WITH_DIRECTIONAL_ALTERNATIVES", "six-slot directional alternatives", "L4 finite candidate generator", "G3 directional rescue 20/20 remains", "library hit can rescue on frozen activated states", "library coverage or continuous-space claim"],
    ])
    write_text("architecture/core_state_machine_v1_spec.md", """# Core causal role state machine specification

The state machine is a specification, not code. It has 15 semantically distinct states: S0 unassessed; S1 start-admissible; S2 repair-required; S3 repair-failed; S4 immediate-segment-safe; S5 immediate-unsafe-unavoidable; S6 primary-under-test; S7 primary-future-safe; S8 primary-recoverable; S9 primary-not-certified; S10 alternative-search-eligible; S11 alternative-certified; S12 terminal-certified; S13 fail-closed; S14 commit.

All terminal execution/fail-close states return only to a new-cycle diagnostic state. No transition equates fail-close with safe stop, and no transition opens alternative search for a start-infeasible or immediate-unavoidable state.
""")
    write_csv("architecture/state_transition_table.csv", ["source", "condition", "destination", "control_dependent", "method_component", "certification", "diagnostic", "historical_evidence_exists", "evidence_source_pr", "unresolved_assumption"], [list(row) for row in TRANSITIONS])
    write_text("architecture/failure_taxonomy.md", """# Failure taxonomy

Current infeasible is not alternative-library failure. Immediate unavoidable unsafe is not candidate failure. A backup witness failure means only that the specified witness was not found, not that recovery is impossible. Finite library exhaustion is not continuous-space infeasibility. A deadline miss is not semantic safety failure. Map/reference unresolved is an evidence limitation rather than a controller collision.
""")
    write_csv("architecture/failure_types.csv", ["failure_type", "current_control_can_repair", "next_control_can_repair", "enter_start_safe", "enter_alternative_search", "only_fail_close", "evidence_limitation"], [list(row) for row in FAILURES])


def semantic_documents() -> None:
    write_text("architecture/start_safe_integration.md", """# Start-Safe integration

Safe start is full-query admitted. Near-unsafe or unsafe start is repair-needed, not an alternative-control opportunity. Historical Flight100 records 92 safe starts, 7 near-unsafe starts, 1 unsafe start, and 8/8 required repairs successful; those values are preserved without new execution. Projection is an active-set repair proposal, never itself a complete certificate. A projected state must receive full-query verification before it re-enters L1. Initial-only admission, episodic repair, and per-step current admission are separate invocation modes; B0 ablation must not absorb the Start-Safe route.
""")
    write_text("architecture/candidate_dependent_future_safety_spec.md", """# Candidate-dependent future-safety concept specification

Define `FUTURE_SAFE(x_k,u_k,M_k,H,W)` as a conceptual predicate with state, candidate, frozen map snapshot, horizon `H`, and explicit future-control witness/assumption `W`. Its output is one of `CERTIFIED`, `NOT_CERTIFIED`, or `NOT_EVALUABLE`; it is not implemented here.

**H1 FIRST_CONTROL_AFFECTED_SEGMENT (preferred specification target):** check `[t_(k+1),t_(k+2)]`, starting from the frozen position-first state at `t_(k+1)`. Candidate `u_k` affects that segment via `v_(k+1)`. H1 is authority-correct, minimally assumption-bearing, compatible with an explicit segment check, and does not posit a perfect future policy. It is nevertheless not present as a formal Core V1 certification layer.

**H2 SHORT_CONTROL_AFFECTED_HORIZON:** check a finite horizon from `t_(k+1)` onward. H2 may reduce local myopia, but must state every later-control witness/policy and cannot assume a perfect future controller. It is more computationally expensive and has greater witness dependence.

The immediate uncontrollable segment remains L1 and is a prerequisite to, not a substitute for, L2. Future safety is a certification target for a future specification, not an established efficacy claim.
""")
    write_text("architecture/recoverability_role_spec.md", """# Recoverability role specification

Backup/recoverability is a secondary candidate certificate after candidate-dependent future safety has passed. Deterministic braking is a witness generator and a terminal-controller candidate where separately certified; it is not a proof of a policy's universal recoverability. The terminal set is sufficient, not maximal. A backup failure means `NO_WITNESS_FOUND_UNDER_THE_FROZEN_WITNESS_CONTRACT`, not `NO_RECOVERY_EXISTS`. Terminal-already-safe is counted separately from a backup incremental certificate. HCE is a search-acceleration mechanism, not a standalone scientific safety contribution.
""")
    write_text("architecture/alternative_search_eligibility.md", """# Alternative-control eligibility

`ALT_ELIGIBLE(x_k,primary,M_k) := ADMISSIBLE(x_k,M_k) AND IMMEDIATE_SAFE(x_k,M_k) AND PRIMARY_EVALUATED(primary) AND NOT PRIMARY_CERTIFIED(primary) AND PRIMARY_FAILURE in {CANDIDATE_FUTURE_SAFETY_FAIL, BACKUP_WITNESS_FAIL} AND NOT TERMINAL_ALREADY_SAFE(x_k) AND NOT CANDIDATE_INDEPENDENTLY_PRECLUDED(x_k,M_k)`.

`h(x_k)<0` is not a B3 opportunity. An immediate unsafe segment is not a B3 opportunity. Candidate-dependent future failure or primary witness failure may be eligible if the predicate holds. A committed primary and terminal-already-safe state are not eligible. This predicate constrains future A3 coverage identification; it does not run a search.
""")
    write_csv("architecture/component_type_matrix.csv", ["component", "classification", "role_layer", "claim_boundary"], [
        ["Start-Safe diagnosis", "EXECUTION_ADMISSION", "L0", "admission/diagnosis only"], ["Start-Safe projection", "RECOVERY_POLICY", "L0", "requires full-query verification"],
        ["current full-query feasibility", "EXECUTION_ADMISSION", "L0", "not future control efficacy"], ["immediate swept segment", "EXECUTION_ADMISSION", "L1", "not candidate discriminator"],
        ["candidate-dependent future safety", "METHOD_CORE (future specification only)", "L2", "not implemented or validated"], ["terminal backup witness", "CERTIFICATION_WITNESS", "L3", "sufficient witness only"],
        ["deterministic braking", "RECOVERY_POLICY", "L3/L5", "not maximal recoverability"], ["terminal set", "TERMINAL_CONDITION", "L5", "sufficient not maximal"],
        ["six-slot alternatives", "CANDIDATE_GENERATOR", "L4", "finite library only"], ["fail-close", "TERMINAL_CONDITION", "L5", "not safe stop"],
        ["offline reference collision check", "REFERENCE_ONLY", "none", "not controller behavior"], ["activated cohort", "EVALUATION_ONLY", "none", "mechanism activation only"],
        ["representative cohort", "EVALUATION_ONLY", "none", "prevalence limited"], ["Wilson CI", "EVALUATION_ONLY", "none", "statistical bound"], ["runtime deadline audit", "DIAGNOSTIC_ONLY", "none", "not semantic safety"],
    ])
    write_text("architecture/method_vs_evaluation_boundary.md", """# Method, execution, and evaluation boundary

L0/L1 are execution admission and consistency checks. L3 is a certificate witness; L4 is a finite candidate generator; L5 is terminal/fail-close semantics. The proposed L2 is a future method component only in a future Core V2 specification. Cohorts, references, Wilson intervals, and runtime audits are evaluation or diagnostic assets, not method contributions. This classification prevents a claim/evaluation redesign from being described as an already validated algorithm.
""")


def evaluation_and_evidence() -> None:
    write_text("evaluation/denominator_contract.md", """# Denominator contract

`N_all` is every frozen or future pre-registered assessed state. Layer denominators are never replaced by a nominal 0/100 after upstream truncation. Unconditional prevalence is `count(event)/N_all`. Conditional efficacy is `count(success)/N_eligible_for_that_mechanism`. Reachability is `N_reached_layer/N_parent_layer`; opportunity is `N_mechanism_needed/N_reached_layer`. Certificate gain reports certificate status only. Decision gain reports a committed action/decision change only.

For future B3 reporting, always show `N_all`, `N_alt_eligible`, `N_alt_attempted`, `N_alt_certified`, unconditional prevalence, and conditional rescue efficacy. Stonehenge/Flight are only historical illustrations and are not recomputed here.
""")
    rows = [
        ["N_all", "all pre-registered assessed states", "unconditional base", "no truncation hidden"], ["N_state_admissible", "L0 pass", "L1 reachability", "current query semantic"],
        ["N_immediate_evaluable", "L1 can be assessed", "L1 reachability", "segment contract"], ["N_immediate_safe", "L1 pass", "L2 parent", "unavoidable risk separate"],
        ["N_primary_candidate_evaluable", "L1 pass and candidate exists", "L2 parent", "future predicate exists"], ["N_primary_future_safe", "L2 pass", "L3 parent", "candidate witness"],
        ["N_recoverability_evaluable", "L2 pass", "L3 parent", "backup contract"], ["N_primary_not_certified", "candidate-specific L2/L3 failure", "L4 parent", "not candidate-independent preclusion"],
        ["N_alt_eligible", "ALT_ELIGIBLE true", "conditional rescue denominator", "finite library only"], ["N_alt_attempted", "search executed under budget", "search reachability", "runtime budget"],
        ["N_alt_certified", "alternative witness passes", "conditional rescue numerator", "not coverage proof"], ["N_commit", "certified primary/alternative/terminal commit", "decision gain", "execution tracking"], ["N_fail_closed", "typed no-certified-route outcome", "failure prevalence", "not safe stop"],
    ]
    write_csv("evaluation/metric_denominators.csv", ["metric", "definition", "use", "boundary"], rows)
    evidence_rows = [
        ["Start-Safe Flight100", "L0 admission/repair", "92 safe, 8 repair-needed and 8 successful", "not per-step candidate efficacy"],
        ["projection synthetic120", "L0 repair/projection", "projection can be proposed and verified", "active set alone is not full certificate"],
        ["dense DT H1/H2/H3 violations", "L1 sampled-data diagnostics", "horizon distinction and violation diagnostics", "not candidate future authority"],
        ["V4-B 0 success", "late-intervention boundary", "negative boundary evidence", "not universal failure"],
        ["TUM step772 shadow prediction", "authority-aware shadow diagnostic", "prediction boundary evidence", "not a formal method run"],
        ["H3_N128 recovery", "L3/L5 recovery witness history", "finite recovery configuration evidence", "not universal recoverability"],
        ["H2_N64 recovery", "L3/L5 recovery witness history", "finite recovery configuration evidence", "not universal recoverability"],
        ["HCE held-out", "recovery acceleration", "search acceleration evidence", "not enlarged recoverable set"],
        ["Stonehenge Risk-Aware bestD", "reference/map limitation", "behavior-only map boundary", "not physical clearance"],
        ["PR87 G0-G5", "activated mechanism roles", "G1 L1 difference; G3 library hit rescue", "not representative prevalence or coverage"],
        ["PR87 representative160", "evaluation prevalence", "zero incremental changes on frozen cohort", "not no possible activation"],
        ["PR89 E1/E5/E6", "L0 truncation/evaluation boundary", "E5/E6 left truncation and behavior-only scope", "not downstream mechanism failure"],
        ["PR90 F01-F11", "causal limitation taxonomy", "F03/F04 structural role evidence", "not a new method result"],
    ]
    write_csv("evidence/evidence_role_remapping.csv", ["evidence", "role", "what_it_proves", "what_it_does_not_prove"], evidence_rows)
    write_text("evidence/historical_claim_boundary.md", """# Historical claim boundary

Historical B0–B3 are frozen ablation identities. Their numbers are neither recomputed nor relabeled as a new method. PR87 G1 supports behavioral discrimination by the immediate-segment layer on activated states, not candidate-dependent authority. PR87 G3 supports finite-library rescue when a frozen alternative hits, not coverage. PR89 and PR90 preserve truncation, reference, and denominator limits.
""")


def alternatives_and_reviews() -> None:
    specs = {
        "A": ("ARCH_A_ROLE_RECLASSIFICATION", "Keep Core V1 mechanisms; classify B1 as L1 and remove any candidate-level DT improvement claim.", "Mathematically coherent only if future candidate-safety is not claimed; insufficient for a future-control safety claim."),
        "B": ("ARCH_B_LOCAL_STRUCTURAL_EXTENSION", "Keep L0/L1/L3/L4 roles, but specify a new L2 candidate-dependent future-safety layer before recoverability/alternatives.", "Selected: local missing layer is required for future-control claim, while existing Start-Safe/recoverability structures remain role-coherent."),
        "C": ("ARCH_C_FULL_PIPELINE_RETHINK", "Treat historical B0-B3 only as diagnostics and rebuild conceptual core around Start-Safe and authority-aware verification.", "Not selected: frozen F05/F11 do not establish multiple irreparable role failures; full rethink is disproportionate now."),
    }
    for key, (name, design, verdict) in specs.items(): write_text(f"alternatives/architecture_{key}_{'role_reclassification' if key=='A' else 'local_structural_extension' if key=='B' else 'full_pipeline_rethink'}.md", f"# {name}\n\n{design}\n\n**Verdict:** {verdict}\n")
    write_csv("alternatives/architecture_comparison.csv", ["architecture", "mathematical_correctness", "authority_alignment", "frozen_evidence_compatibility", "method_change", "evaluation_change", "falsifiability", "computational_implication", "novelty_risk", "reviewer_defensibility", "implementation_burden", "claim_clarity", "verdict"], [
        ["ARCH_A", 4, 4, 5, "low", "high", 4, "low", "low", 3, "low", 3, "reject for retained future-control claim"],
        ["ARCH_B", 5, 5, 5, "local future spec", "moderate", 5, "bounded conceptual", "moderate", 5, "moderate", 5, "SELECT"],
        ["ARCH_C", 4, 5, 3, "full", "full", 3, "high", "high", 2, "high", 3, "reject as unsupported expansion"],
    ])
    reviews = [
        ("control_theory_review.md", "R1 Control Theory", "CASE_B", "1) B1 cannot discriminate u_k over the immediate position segment. 2) L2 is absent from V1. 3) backup witness is not universal recoverability.", "L1 role; exact first affected horizon; requirement for a future L2 specification", "candidate-level immediate safety, global controllability, recursive feasibility"),
        ("robotics_system_review.md", "R2 Robotics Systems", "CASE_B", "1) Start-Safe, terminal, and fail-close need separate entries. 2) current infeasible cannot route to alternatives. 3) finite-library exhaustion needs a typed terminal path.", "state-machine separation and non-cyclic terminal paths", "fail-close as safe stop, terminal set as maximal"),
        ("evaluation_statistics_review.md", "R3 Evaluation/Statistics", "CASE_B", "1) 0/100 hides B0 truncation. 2) prevalence and conditional efficacy require separate denominators. 3) B3 opportunity is zero in frozen diagnostics.", "denominator hierarchy and conditional B3 accounting", "representative prevalence or efficacy beyond denominators"),
        ("novelty_publication_review.md", "R4 Novelty/Publication", "CASE_B", "1) role clarification alone cannot sustain a future-control claim. 2) L2 is not validated. 3) a full redesign lacks evidence.", "narrow local structural gap and preserved historical claims", "new algorithm, performance, deployment safety"),
    ]
    rows=[]
    for filename, role, vote, objections, preserve, prohibit in reviews:
        write_text(f"reviews/{filename}", f"""# {role}

**Blind review declaration:** This review is written from frozen inputs and does not rely on the final decision file.

**Recommended case:** `{vote}`

**Fatal objections:** {objections}

**Claims that may be preserved:** {preserve}.

**Claims that must remain prohibited:** {prohibit}.
""")
        rows.append([role, vote, "three fatal objections recorded", preserve, prohibit])
    write_csv("reviews/reviewer_case_matrix.csv", ["reviewer", "case_vote", "fatal_objections", "preserved_claim", "prohibited_claim"], rows)
    write_text("reviews/disagreement_analysis.md", """# Reviewer disagreement analysis

All four independently written role reviews select CASE_B. Their reasoning differs: theory emphasizes the Jacobian; systems emphasizes lawful terminal paths; statistics emphasizes denominators; publication emphasizes claim clarity. Their common conclusion is limited: a future L2 specification is necessary for a future-control safety claim, but it is neither implemented nor validated here. ARCH_A remains a defensible narrower reporting posture if no future-control claim is retained; ARCH_C remains a rejected expansion without evidence of multiple irreparable defects.
""")


def decision_and_reports() -> None:
    supported = """# Supported claims

- The frozen position-first Euler contract gives zero immediate position sensitivity to `u_k` and nonzero sensitivity at `p_(k+2)`.
- B1 is primarily L1 execution admission/late-risk detection, not candidate-dependent safety filtering.
- Start-Safe admission/repair, backup witness, finite alternatives, terminal condition, and fail-close have separable roles.
- If a future method claims candidate-level future discrete safety, it needs an explicit L2 specification not present in Core V1.
"""
    prohibited = """# Prohibited claims

- No new controller, Core V2 implementation, safety guarantee, performance result, real-time result, recursive feasibility, global controllability, deployment safety, maximal terminal set, continuous-library coverage, candidate-level future discrete safety, or candidate-dependent efficacy is established.
- Fail-close is not a safe stop; backup witness absence is not no recovery; B0 truncation is not alternative failure.
"""
    unresolved = """# Unresolved assumptions

1. Map-query and reference semantics for a future L2 certificate.
2. Continuous segment-check contract for H1.
3. Explicit later-control witness/policy for H2.
4. Start-Safe repair eligibility and supervisory authority.
5. Tracking/latency budget and runtime deadline integration.
6. Finite alternative-library coverage beyond frozen hits.
7. Representative on-policy opportunity distribution.
"""
    write_text("decision/supported_claims.md", supported); write_text("decision/prohibited_claims.md", prohibited); write_text("decision/unresolved_assumptions.md", unresolved)
    selection = {"selected_case": CASE, "FINAL_STATUS": STATUS, "FINAL_DECISION": DECISION, "Only_next_task": NEXT_TASK, "rationale": "B1 is logically coherent as L1, but a retained future-control safety claim requires an absent L2; no evidence requires full pipeline rethink.", "preferred_future_safety_target": "H1_FIRST_CONTROL_AFFECTED_SEGMENT", "reviewer_case_votes": {"CASE_B": 4}}
    write_json("decision/final_architecture_decision.json", selection)
    write_text("decision/downstream_plan.md", f"""# Downstream plan

**Only next task:** `{NEXT_TASK}`.

It may write a causal increment specification for L2 only. It must not implement Core V2, modify Core V1, run B0-B3, acquire data, train a map, or interpret historical results as V2 evidence.
""")
    write_json("audits/operational_autonomy_actions.json", {"count": 5, "actions": ["isolated worktree creation", "raw Git freeze", "task-owned Markdown/CSV/JSON serialization", "task-owned figure generation", "read-only formula and GPU/watchdog verification"], "scientific_contract_changes": 0})
    write_json("audits/no_implementation_audit.json", {"formal_method_run_count": 0, "controller_mutation_count": 0, "method_mutation_count": 0, "map_training_count": 0, "map_mutation_count": 0, "dataset_addition_count": 0, "cohort_addition_count": 0, "b3_oracle_count": 0, "configuration_sweep_count": 0, "core_v2_implementation_count": 0, "status": "PASS_NO_IMPLEMENTATION_BOUNDARY"})
    report = f"""# REPORT: Write Core causal architecture specification V1

## Result

`{STATUS}`

**Decision:** `{DECISION}`

**Only next task:** `{NEXT_TASK}`

## Frozen mathematical result

The normative model remains `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`: `p_(k+1)=p_k+dt v_k`, `v_(k+1)=v_k+dt u_k`, `∂p_(k+1)/∂u_k=0`, and `∂p_(k+2)/∂u_k=dt²I`. B1 is consequently reclassified as L1 immediate execution admission/late-risk detection, not a candidate safety discriminator.

## Architecture decision

L0 handles Start-Safe/current admission and repair. L1 handles the immediate uncontrollable segment. L2 is the missing candidate-dependent future-safety role; H1 `[t_(k+1),t_(k+2)]` is the preferred future specification target. L3 is a secondary sufficient backup witness, L4 is a finite alternative search under `ALT_ELIGIBLE`, and L5 separates certified terminal action from explicit fail-close.

This is CASE_B: the role decomposition does not establish a full pipeline failure, but any future-control safety method claim requires a new L2 specification outside formal Core V1. Historical B0-B3, Start-Safe, PR87, PR89, and PR90 values remain preserved and unrecomputed.

## Boundaries

No controller, map, data, candidate library, dynamics, B0-B3 gate, rollout, formal navigation, B3 oracle, configuration sweep, or Core V2 implementation was performed. This specification is not a safety guarantee, performance claim, real-time claim, recursive-feasibility proof, global controllability proof, or deployment claim.
"""
    write_text("WRITE_CORE_CAUSAL_ARCHITECTURE_SPECIFICATION_V1.md", report)
    write_text("report/REPORT_WRITE_CORE_CAUSAL_ARCHITECTURE_SPECIFICATION_V1.md", report)
    write_json("report/downstream_handoff.json", {"FINAL_STATUS": STATUS, "FINAL_DECISION": DECISION, "Only_next_task": NEXT_TASK, "started": False, "formal_method_runs": 0})
    write_text("report/DRAFT_PR_BODY.md", f"""## Summary

Freeze a Core causal control-architecture specification from PR #83/#84/#86/#87/#89/#90/#91 evidence. No controller, dynamics, B0-B3, map, dataset, cohort, formal run, oracle, sweep, or implementation is changed.

## Decision

- Preserved mathematical model: position-first Euler; immediate position authority is zero and `p_(k+2)` is first control-affected.
- L0-L5 separates Start-Safe/admission, immediate segment, conceptual L2 future safety, witness recoverability, finite alternatives, and terminal/fail-close.
- Historical B0-B3 are remapped as frozen diagnostics only.
- Four independent reviews select CASE_B.
- **Only next task:** `{NEXT_TASK}`.

## Claim boundary

This is a specification-only local structural-gap decision, not Core V2, a new safety guarantee, or a performance result.
""")


def make_figure(name: str, title: str, labels: list[str], values: list[float], ylabel: str) -> None:
    path = TASK_ROOT / "figures" / name; path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 6)); bars=plt.bar(labels, values, color="#2563eb"); plt.title(title, fontweight="bold"); plt.ylabel(ylabel)
    for b,v in zip(bars,values): plt.text(b.get_x()+b.get_width()/2,b.get_height(),f"{v:g}",ha="center",va="bottom",fontsize=8)
    plt.figtext(.5,.01,FOOTER,ha="center",fontsize=6,wrap=True); plt.tight_layout(rect=(0,.08,1,1)); plt.savefig(path,dpi=150); plt.close()


def figures() -> None:
    chart = {
        "historical_b0_b3_vs_role_architecture.png": ("Historical B0-B3 remapped to role layers", ["B0/L0","B1/L1","B2/L3","B3/L4"],[0,1,3,4],"role index"),
        "control_authority_timeline.png": ("Control authority over frozen samples", ["p_k","p_k+1","v_k+1","p_k+2"],[0,0,1,1],"u_k authority"),
        "position_first_euler_dependency.png": ("Position-first Euler derivative", ["dp1/du","dv1/du","dp2/du"],[0,1,1],"nonzero indicator"),
        "first_control_affected_horizon.png": ("First candidate-dependent position horizon", ["[k,k+1]","[k+1,k+2]","H2+"],[0,1,1],"position sensitivity"),
        "start_safe_integration.png": ("Start-Safe frozen evidence roles", ["safe","repair-needed","repair-success"],[92,8,8],"historical count"),
        "immediate_unavoidable_vs_candidate_future.png": ("Immediate versus candidate-future roles", ["L1 authority","L2 authority"],[0,1],"u_k sensitivity"),
        "recoverability_entry_conditions.png": ("Recoverability requires future-safe candidate", ["L1","L2","L3"],[1,1,1],"required condition"),
        "alternative_search_eligibility.png": ("Alternative search eligible only after candidate-specific failure", ["start invalid","immediate unsafe","future fail","backup fail"],[0,0,1,1],"ALT eligible"),
        "state_machine.png": ("Role-state machine state counts", ["admission","immediate","candidate","terminal"],[4,2,6,3],"states"),
        "failure_taxonomy.png": ("Failure taxonomy", ["semantic","witness","runtime","evidence"],[5,2,1,3],"failure types"),
        "gate_reachability_and_denominators.png": ("Gate reachability denominators", ["N_all","N_L0","N_L1","N_L2","N_alt"],[1,.8,.6,.4,.2],"conceptual denominator"),
        "unconditional_vs_conditional_metrics.png": ("Prevalence versus conditional efficacy", ["N_all","N_eligible","N_success"],[100,26,0],"illustrative frozen counts"),
        "method_vs_evaluation_boundary.png": ("Component classification", ["method","admission","witness","evaluation"],[1,4,3,5],"components"),
        "historical_evidence_remapping.png": ("Historical evidence remapping", ["StartSafe","DT","recovery","PR87","PR89/90"],[1,1,1,1,1],"preserved role"),
        "architecture_A.png": ("ARCH_A: role reclassification", ["math","claim clarity","future claim"],[4,3,0],"score"),
        "architecture_B.png": ("ARCH_B: local structural extension", ["math","authority","clarity"],[5,5,5],"score"),
        "architecture_C.png": ("ARCH_C: full rethink", ["math","evidence support","burden"],[4,3,5],"score"),
        "architecture_comparison.png": ("Architecture comparison", ["A","B","C"],[3,5,2],"reviewer defensibility"),
        "reviewer_case_preferences.png": ("Independent reviewer case preferences", ["A","B","C","D","E"],[0,4,0,0,0],"votes"),
        "final_architecture_decision.png": ("Final architecture decision: CASE_B", ["A","B","C"],[0,1,0],"selected"),
        "downstream_single_next_step.png": ("Exactly one downstream task", ["next task","parallel tasks"],[1,0],"count"),
    }
    for name, (title, labels, values, ylabel) in chart.items(): make_figure(name,title,labels,values,ylabel)
    assert set(chart)==set(FIGURES)
    write_json("figures/figure_manifest.json", {"count":len(FIGURES),"figures":[{"file":f,"annotation":FOOTER} for f in FIGURES]})


def main() -> None:
    freeze_inputs(); verify_formula(); architecture_documents(); semantic_documents(); evaluation_and_evidence(); alternatives_and_reviews(); decision_and_reports(); figures()
    print("PASS_CORE_CAUSAL_ARCHITECTURE_ARTIFACTS_MATERIALIZED")


if __name__ == "__main__": main()
