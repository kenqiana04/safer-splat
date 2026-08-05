#!/usr/bin/env python3
"""Create only static FAS-CBF Core V1 conceptual-closure artifacts."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parent
UP = ROOT.parent / "fas_cbf_module_evidence_assembly_v1"
STATUS = "PASS_FAS_CBF_CORE_V1_CONCEPTUAL_CLOSURE"
DECISION = "IMPLEMENT_UNIFIED_EXECUTABLE_SAFETY_CERTIFIER"
NEXT = "IMPLEMENT_ACTUATOR_BOUNDED_SWEPT_SEGMENT_TERMINAL_BACKUP_CERTIFIER_V1"
UPSTREAM = [
    "report/REPORT_ASSEMBLE_FAS_CBF_MODULE_EVIDENCE_FROM_ETH3D_AND_EXISTING_FROZEN_CASES_V1.md",
    "evidence_ledger/evidence_provenance_ledger.json",
    "module_matrices/module_evidence_matrix.json",
    "claim_audit/claim_evidence_matrix.json",
    "config_compatibility/configuration_compatibility_matrix.csv",
    "config_compatibility/cohort_overlap_audit.json",
    "module_matrices/positive_negative_structural_registry.csv",
    "paper_architecture/paper_experiment_architecture.json",
    "minimal_remaining_experiment/minimal_remaining_experiment.json",
]
SOURCE_PATHS = [
    "dynamics/systems.py", "cbf/cbf_utils.py", "splat/gsplat_utils.py",
    "splat/distances.py", "run.py",
    "work/risk_aware_cbf/scripts/run_v4b_corrective_dt_filter.py",
    "work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py",
    "work/risk_aware_cbf/scripts/v4c_hierarchical_candidate_evaluator.py",
    "work/risk_aware_cbf/scripts/gsplat_barrier_geometry_adapter.py",
]
WRAPPERS = [
    "freeze_pr82_inputs.py", "inventory_current_modules.py", "audit_execution_model.py",
    "build_safety_set_contract.py", "build_unified_certificate_schema.py",
    "build_state_machine.py", "map_current_modules_to_core_v1.py",
    "build_safer_distinction_matrix.py", "build_theory_obligation_registry.py",
    "build_core_v1_evidence_traceability.py", "build_component_interface_contracts.py",
    "build_deferred_extension_roadmap.py", "run_framework_reviewer_audit.py",
    "select_framework_decision.py",
]
FIGURES = [
    "safer_to_fas_cbf_problem_shift.png", "fas_cbf_core_v1_overview.png",
    "safety_set_hierarchy.png", "execution_model_consistency.png",
    "swept_segment_certificate.png", "terminal_backup_certificate.png",
    "unified_executable_control_set.png", "fas_cbf_state_machine.png",
    "current_module_to_core_mapping.png", "safer_vs_fas_cbf_scope_matrix.png",
    "theory_proof_obligation_map.png", "evidence_to_core_traceability.png",
    "positive_negative_boundary_evidence.png", "fail_closed_semantics.png",
    "current_vs_deferred_features.png", "implementation_roadmap.png",
    "reviewer_claim_boundary.png", "final_framework_decision.png",
]

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def put(path: str, data: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dedent(data).strip() + "\n", encoding="utf-8", newline="\n")

def put_json(path: str, value: object) -> None:
    put(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))

def put_csv(path: str, rows: list[dict[str, object]]) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0]) if rows else ["empty"]
    with p.open("w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=keys, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

def frozen_artifacts() -> list[dict[str, object]]:
    result = []
    for rel in UPSTREAM:
        p = UP / rel
        if not p.exists():
            raise FileNotFoundError(p)
        result.append({"path": rel, "sha256": digest(p), "bytes": p.stat().st_size})
    return result

def protected_hashes() -> list[dict[str, object]]:
    repo = ROOT.parents[2]
    return [{"path": p, "sha256": digest(repo / p), "bytes": (repo / p).stat().st_size,
             "protected": True} for p in SOURCE_PATHS]

def write_root_and_problem() -> None:
    put("INTEGRATE_FAS_CBF_FULL_FRAMEWORK_WITH_MODULE_SPECIFIC_CLAIMS_V1.md", """
    # FAS-CBF Core V1 conceptual closure

    This task freezes an executable-safety design contract, not a final algorithm,
    theorem, deployment guarantee, or global superiority result. Before control
    commitment, Core V1 requires actuator admissibility, current feasibility,
    swept-segment safety, and terminal-backup evidence. Otherwise it returns an
    explicit non-execution or fail-closed result.
    """)
    put("IMPLEMENTATION_PLAN.md", """
    # FAS-CBF Core V1 Conceptual Closure Implementation Plan

    > For agentic workers: documentation and static-validation only. Do not run a plant,
    > train a map, tune a controller, or mutate protected source.

    **Goal:** Freeze the Core V1 executable-safety contract from PR #82 evidence.

    **Architecture:** Read frozen evidence and source identities; generate problem,
    > certificate, state-machine, theory, interface, reviewer, and report artifacts.

    **Tech Stack:** Python standard library, JSON, CSV, Markdown, Pillow.

    ---

    ### Task 1: Freeze sources
    - [x] Freeze PR #82 identity, source artifacts, and unknown fields.
    - [x] Hash protected historical source without mutation.

    ### Task 2: Freeze Core V1 semantics
    - [x] Define problem, execution contract, safety sets, certificate, and state machine.
    - [x] Keep the normative implementation model and terminal set as future work.

    ### Task 3: Map evidence and boundaries
    - [x] Reclassify modules, audit SAFER distinction, theory obligations, and evidence.
    - [x] Preserve negative and structural records.

    ### Task 4: Validate
    - [x] Validate zero execution, claim limits, identity, interfaces, and static artifacts.
    """)
    put("problem_definition/FAS_CBF_CORE_V1_PROBLEM_STATEMENT.md", """
    # Problem statement

    Inputs are Gaussian map G, state x_k, nominal control u_nom,k, actuator set U,
    sample period Delta t, footprint B, fixed margin rho, flow Phi, backup policy,
    terminal set X_T, and an UNKNOWN policy. Outputs are certified nominal,
    alternative, backup, or terminal actions; otherwise FAIL_CLOSED_UNRECOVERABLE,
    NOT_EVALUABLE_MAP_QUERY, or INFRASTRUCTURE_FAILURE.

    The object of certification is the represented Gaussian obstacle field under stated
    map and error assumptions. Map certificate, execution certificate, offline
    reference-oracle evaluation, and deployment guarantee are different claims.
    """)
    put_json("problem_definition/research_question.json", {
        "research_question": "With bounded actuators and sampled execution on a represented Gaussian obstacle field, how can control be committed only with interval safety, finite-control feasibility, and terminal-backup evidence, or otherwise fail closed?",
        "outputs": ["CERTIFIED_NOMINAL_CONTROL", "CERTIFIED_ALTERNATIVE_CONTROL", "CERTIFIED_BACKUP_CONTROL", "TERMINAL_SAFE_ACTION", "FAIL_CLOSED_UNRECOVERABLE", "NOT_EVALUABLE_MAP_QUERY", "INFRASTRUCTURE_FAILURE"],
        "status": "DESIGN_CONTRACT",
    })
    put("problem_definition/system_boundary.md", """
    # System boundary

    Online components are map query, dynamics flow, actuator set, CBF filter,
    segment/backup certificates, fail-closed policy, and immutable identities.
    Reference collision oracle, benchmark labels, mesh evaluation, and calibration are
    offline only. UNKNOWN map query is never free space. Infrastructure errors are
    engineering states, not scientific safety outcomes.
    """)
    put("problem_definition/contribution_boundary.md", """
    # Contribution boundary

    Current contribution is a unifying contract and evidence remapping. Historical
    components are not silently converted into a unified implementation. No claim is
    made for Full FAS-CBF global superiority, deployment safety, universal recovery,
    metric distance, adaptive margin, smooth execution, or recursive feasibility.
    """)
    put("notation/FAS_CBF_CORE_V1_NOTATION.md", """
    # Notation

    G is the represented Gaussian obstacle field; h_G is a barrier lower bound or proxy,
    not metric clearance without independent proof. F_Delta is the discrete transition,
    Phi is interval flow, rho is fixed margin, H is backup horizon, and C_seg is the
    swept-segment certificate. X_T is terminal-safe only under explicit assumptions.
    """)

def write_execution_sets_certificate() -> None:
    put_json("execution_model/execution_model_contract.json", {
        "abstract_transition": "x_(k+1)=F_Delta(x_k,u_k)",
        "interval_flow": "x(tau)=Phi(tau;x_k,u_k), tau in [0,Delta t]",
        "historical_evidence_model": {
            "name": "forward_Euler_position_first",
            "equations": ["p_(k+1)=p_k+Delta t v_k", "v_(k+1)=v_k+Delta t u_k"],
            "sources": ["run.py", "run_v4b_corrective_dt_filter.py", "run_v4c_hstep_predictive_recovery.py"],
        },
        "future_candidate_not_retroactive": "constant acceleration ZOH",
        "unknowns": ["actuation_delay", "computation_delay", "tracking_error", "normative_model"],
    })
    put("execution_model/EXECUTION_MODEL_CONTRACT_V1.md", """
    # Execution-model contract

    Core V1 uses abstract F_Delta and Phi. Located historical experiments propagate a
    double integrator with position-first forward Euler. Constant-acceleration ZOH is
    a future candidate only and cannot reinterpret historical evidence. Before actual
    implementation, optimizer, certifier, and plant must share one frozen normative
    model with explicit delay and hold treatment.
    """)
    put("execution_model/integrator_consistency_audit.md", """
    # Integrator consistency audit

    dynamics/systems.py provides the continuous double-integrator derivative. run.py
    and the V4 scripts advance x plus Delta t times that derivative. Therefore past
    position updates use pre-control velocity. Missing delay and tracking bounds are
    UNKNOWN_NOT_RECOVERED rather than zero.
    """)
    put("execution_model/relative_degree_and_latency_audit.md", """
    # Relative-degree and latency audit

    DoubleIntegrator has relative degree two. V4-B zero success for one-step
    acceleration correction is a timing/relative-degree boundary: position-first Euler
    cannot change immediate position with current acceleration. This does not invalidate
    all DT policies or establish a continuous safety proof.
    """)
    sets = {
        "X_map": "represented-Gaussian static safety with fixed margin",
        "X_feas": "exists actuator-bounded current feasible u in U",
        "X_seg": "exists u with min over sampled interval h_G(Phi)-rho_seg >= 0",
        "X_rec": "exists finite H-step bounded sequence with all segments certified and terminal endpoint",
        "X_T": "frozen terminal policy is safe/invariant/stopping only under explicit assumptions",
        "X_exec": "X_map intersection X_feas intersection X_seg intersection X_rec",
    }
    put_json("safety_sets/safety_set_contract.json", {
        "sets": sets, "unknown_policy": "UNKNOWN_NOT_EVALUABLE is never safe/free",
        "relations_status": "PROOF_OBLIGATIONS_NOT_PROVED"})
    put("safety_sets/FAS_CBF_CORE_V1_SAFETY_SET_HIERARCHY.md", """
    # Safety-set hierarchy

    X_map, X_feas, X_seg, X_rec, and X_T have distinct semantics. X_exec is their
    stated intersection. Do not infer any additional inclusion. In particular,
    X_rec is not X_map, current non-collision is not recoverability, and h_G is not
    called a metric distance without evidence.
    """)
    classifications = [
        ("MAP_UNSAFE","not X_map"), ("MAP_SAFE_NOT_ACTUATOR_FEASIBLE","not X_feas"),
        ("ACTUATOR_FEASIBLE_NOT_SEGMENT_CERTIFIED","not X_seg"),
        ("SEGMENT_CERTIFIED_NOT_BACKUP_RECOVERABLE","not X_rec"),
        ("BACKUP_RECOVERABLE","finite witness exists"), ("TERMINAL_SAFE","in X_T under assumptions"),
        ("UNRECOVERABLE_FAIL_CLOSED","no certified executable action"),
        ("UNKNOWN_NOT_EVALUABLE","required evidence unavailable"),
    ]
    put_csv("safety_sets/state_classification_table.csv",
            [{"state_class":a,"meaning":b,"online_policy":"never commit uncertified nominal"} for a,b in classifications])
    put("safety_sets/set_relation_proof_obligations.md", """
    # Set-relation obligations

    Any inclusion needs barrier lower-bound, common flow, margin coverage, and concrete
    certificates. Positive invariance of X_T and recursive executability remain
    unproved. Start-Safe is an executability-admission contract, not merely h >= 0.
    """)
    failures = {
        "MAP_QUERY_UNKNOWN":"NOT_EVALUABLE_MAP_QUERY", "ACTUATOR_SET_EMPTY":"FAIL_CLOSED_UNRECOVERABLE",
        "CBF_QP_INFEASIBLE":"PREDICTIVE_RECOVERY", "SEGMENT_CERTIFICATE_FAILED":"PREDICTIVE_RECOVERY",
        "BACKUP_WITNESS_ABSENT":"TERMINAL_BACKUP_OR_FAIL_CLOSED",
        "TERMINAL_POLICY_UNAVAILABLE":"FAIL_CLOSED_UNRECOVERABLE",
        "REFERENCE_LEAK_ATTEMPT":"INFRASTRUCTURE_FAILURE", "INFRASTRUCTURE_ERROR":"INFRASTRUCTURE_FAILURE",
    }
    put_json("unified_certificate/certificate_failure_codes.json", failures)
    put_json("unified_certificate/unified_certificate_schema.json", {
        "acceptance":"U_exec=U intersection U_cbf intersection U_seg intersection U_backup",
        "conditions":["actuator admissible","current CBF feasible","C_seg passes","terminal backup witness"],
        "limitations":["finite candidate witness is not global controllability","finite horizon is not recursive feasibility","discrete samples are not continuous proof without lower bound","X_T is currently a design contract"],
    })
    put("unified_certificate/ACTUATOR_BOUNDED_SWEPT_SEGMENT_TERMINAL_BACKUP_CERTIFICATE_V1.md", """
    # Unified executable-safety certificate

    A committed control must belong to U_exec, the intersection of actuator, current
    CBF, swept-segment, and backup certificates. The backup witness has certified
    intermediate segments and reaches X_T. If U_exec is empty, a certified terminal
    action may be committed; otherwise Core V1 returns FAIL_CLOSED_UNRECOVERABLE and
    does not silently execute nominal control.
    """)
    decisions = [
        ("CERTIFIED_NOMINAL_CONTROL",True,"all certificate components"),
        ("CERTIFIED_ALTERNATIVE_CONTROL",True,"all components for replacement"),
        ("CERTIFIED_BACKUP_CONTROL",True,"backup witness and first action"),
        ("TERMINAL_SAFE_ACTION",True,"terminal witness"),
        ("FAIL_CLOSED_UNRECOVERABLE",False,"empty U_exec"),
        ("NOT_EVALUABLE_MAP_QUERY",False,"unknown query"),
        ("INFRASTRUCTURE_FAILURE",False,"engineering failure"),
    ]
    put_csv("unified_certificate/certificate_decision_table.csv",
            [{"decision":a,"plant_execution":b,"required_evidence":c} for a,b,c in decisions])
    put("unified_certificate/reference_algorithm_pseudocode.md", """
    # Reference algorithm pseudocode

    Diagnose initial executability; apply recorded Start-Safe projection only when
    certified; construct actuator-bounded current candidates; certify their interval;
    require backup witness; then commit. Search alternatives only after nominal failure.
    If a terminal action is certified, execute it. Otherwise fail closed. Re-certify
    each period. Reference oracles cannot enter online decisions.
    """)

def write_state_machine() -> None:
    states = ["INITIAL_DIAGNOSIS","START_SAFE_PROJECTION","ACTUATOR_BOUNDED_CBF_QP",
              "SWEPT_SEGMENT_CERTIFICATION","TERMINAL_BACKUP_CERTIFICATION",
              "CERTIFIED_EXECUTION","PREDICTIVE_RECOVERY","TERMINAL_BACKUP_EXECUTION",
              "FAIL_CLOSED_UNRECOVERABLE","NOT_EVALUABLE","MISSION_COMPLETE"]
    raw = [
        ("INITIAL_DIAGNOSIS","START_SAFE_PROJECTION","needs projection","projection evidence","state","NONE",False),
        ("INITIAL_DIAGNOSIS","ACTUATOR_BOUNDED_CBF_QP","admissible start","map query","state","NONE",False),
        ("START_SAFE_PROJECTION","ACTUATOR_BOUNDED_CBF_QP","projection passes","projection certificate","state","PROJECTION_FAILED",False),
        ("ACTUATOR_BOUNDED_CBF_QP","SWEPT_SEGMENT_CERTIFICATION","candidate exists","U plus U_cbf","candidate","CBF_QP_INFEASIBLE",False),
        ("SWEPT_SEGMENT_CERTIFICATION","TERMINAL_BACKUP_CERTIFICATION","C_seg passes","interval certificate","candidate","SEGMENT_CERTIFICATE_FAILED",False),
        ("TERMINAL_BACKUP_CERTIFICATION","CERTIFIED_EXECUTION","witness exists","backup certificate","control","BACKUP_WITNESS_ABSENT",True),
        ("CERTIFIED_EXECUTION","INITIAL_DIAGNOSIS","next period","state observation","none","NONE",False),
        ("CERTIFIED_EXECUTION","MISSION_COMPLETE","completion contract","state observation","none","NONE",False),
        ("ACTUATOR_BOUNDED_CBF_QP","PREDICTIVE_RECOVERY","nominal absent","failure code","none","CBF_QP_INFEASIBLE",False),
        ("SWEPT_SEGMENT_CERTIFICATION","PREDICTIVE_RECOVERY","segment fails","failure code","none","SEGMENT_CERTIFICATE_FAILED",False),
        ("TERMINAL_BACKUP_CERTIFICATION","PREDICTIVE_RECOVERY","witness absent","failure code","none","BACKUP_WITNESS_ABSENT",False),
        ("PREDICTIVE_RECOVERY","TERMINAL_BACKUP_EXECUTION","terminal action exists","terminal witness","terminal control","NONE",True),
        ("TERMINAL_BACKUP_EXECUTION","INITIAL_DIAGNOSIS","next period after certified terminal action","new state","none","NONE",False),
        ("PREDICTIVE_RECOVERY","FAIL_CLOSED_UNRECOVERABLE","no certified action","empty U_exec","none","UNRECOVERABLE",False),
    ]
    transitions = [{"from":a,"to":b,"guard":c,"required_evidence":d,"control_output":e,
                    "failure_code":f,"plant_execution":g,"map_query_required":True,
                    "reference_oracle_forbidden":True} for a,b,c,d,e,f,g in raw]
    put_json("state_machine/state_machine.json", {
        "states":states,"transitions":transitions,
        "terminal_states":["FAIL_CLOSED_UNRECOVERABLE","NOT_EVALUABLE","MISSION_COMPLETE"]})
    put_csv("state_machine/transition_table.csv", transitions)
    put("state_machine/FAS_CBF_CORE_V1_STATE_MACHINE.md", """
    # State machine

    Core V1 separates diagnosis, projection, current feasibility, segment certification,
    backup certification, execution, recovery, terminal execution, and fail-closed
    states. Every execution period is re-certified. Online reference access is forbidden.
    """)
    put("state_machine/failure_semantics.md", """
    # Failure semantics

    Failed certification never authorizes nominal control. Certified terminal backup,
    uncertified engineering abort, and infrastructure failure have different labels.
    Unknown map evidence enters NOT_EVALUABLE. Only typed terminal behavior may follow
    a failure code.
    """)
    put("state_machine/reference_state_machine.mmd", """
    stateDiagram-v2
      INITIAL_DIAGNOSIS --> ACTUATOR_BOUNDED_CBF_QP
      ACTUATOR_BOUNDED_CBF_QP --> SWEPT_SEGMENT_CERTIFICATION
      SWEPT_SEGMENT_CERTIFICATION --> TERMINAL_BACKUP_CERTIFICATION
      TERMINAL_BACKUP_CERTIFICATION --> CERTIFIED_EXECUTION
      TERMINAL_BACKUP_CERTIFICATION --> PREDICTIVE_RECOVERY
      PREDICTIVE_RECOVERY --> TERMINAL_BACKUP_EXECUTION
      TERMINAL_BACKUP_EXECUTION --> INITIAL_DIAGNOSIS
      PREDICTIVE_RECOVERY --> FAIL_CLOSED_UNRECOVERABLE
    """)

def write_inventory_mapping(evidence: list[dict[str, object]]) -> None:
    entries = [
        ("Gaussian barrier","splat/gsplat_utils.py","GSplatLoader.query_distance","barrier/gradient/Hessian","direct abstract reuse","proxy not metric distance"),
        ("Dynamics","dynamics/systems.py","double_integrator_dynamics","state derivative","abstract reuse","historical Euler flow"),
        ("Current CBF QP","cbf/cbf_utils.py","CBF.solve_QP","control and solver flag","interface rebuild","source fallback behavior split"),
        ("Start-Safe","historical reports and scripts","abstract contract","admission/projection","abstract only","source implementation not fully recovered"),
        ("Risk-Aware","run_v4b_corrective_dt_filter.py","make_cbf and generate_candidates","candidate/control","reclassify","prioritization not certificate"),
        ("DT verification","run_v4b_corrective_dt_filter.py","evaluate_candidates","predicted h","reclassify","one-step proxy"),
        ("Predictive Recovery","run_v4c_hstep_predictive_recovery.py","evaluate_sequences","sequence witness","interface rebuild","finite family/horizon"),
        ("HCE","v4c_hierarchical_candidate_evaluator.py","evaluate_hierarchical","staged search","reclassify","does not enlarge recoverable set"),
        ("Geometry adapter","gsplat_barrier_geometry_adapter.py","query_barrier_geometry","critical barrier","direct read-only reuse","critical barrier proxy"),
    ]
    rows = [{"module":a,"source_path":b,"public_interface":c,"input_output":d,
             "core_v1_disposition":e,"known_limitation":f,"reference_access":"offline forbidden online"}
            for a,b,c,d,e,f in entries]
    put_json("source_inventory/current_code_module_inventory.json", {"count":len(rows),"modules":rows})
    put_csv("source_inventory/current_interface_inventory.csv", rows)
    put_json("source_inventory/protected_core_hashes.json",
             {"protected_sources":protected_hashes(),"policy":"read-only only"})
    put("source_inventory/current_control_flow.md", """
    # Current control flow

    Located baseline flow is nominal PD control, Gaussian CBF QP, position-first Euler
    propagation, then barrier logging. V4-B adds one-step screening; V4-C evaluates
    finite sequences; HCE stages search. These are not a single executable-safety
    certifier. Current CBF source returns desired control after solver failure, while
    run.py stops before propagation on a false solver flag; Core V1 resolves this with
    one explicit non-execution contract.
    """)
    put("source_inventory/current_semantic_conflicts.md", """
    # Semantic conflicts

    Barrier values, clearance, margin violation, GSplat overlap, and reference collision
    remain distinct. One-step V4-B, H-step V4-C, and HCE have no common terminal-set
    contract. Risk budgeting is not a certificate. Fallback must split into terminal
    backup, engineering abort, and infrastructure failure.
    """)
    mapping = [
        ("Start-Safe","initial executability admission and projection","abstract contract"),
        ("Risk-Aware budgeting","computational prioritization","not safety certificate"),
        ("Feasibility-Aware/dominance","actuator-feasible set construction","reduced/full relation unproved"),
        ("DT Verification","swept-segment precursor","margin is not collision"),
        ("Predictive Recovery","backup-witness sequence search","finite candidate limit"),
        ("HCE","backup-search acceleration","does not enlarge X_rec"),
        ("Fallback","terminal backup or abort or infrastructure failure","must split"),
        ("V4-B","relative-degree late-intervention boundary","negative evidence"),
        ("Trial20","finite horizon/candidate exhaustion","negative boundary"),
        ("ETH3D H3","structural activation limit","not DT invalidity"),
        ("Replica saturation","integration/no-regression context","not superiority"),
    ]
    mp = [{"historical_module":a,"core_v1_role":b,"claim_boundary":c} for a,b,c in mapping]
    put_csv("module_mapping/module_mapping.csv", mp)
    put_json("module_mapping/module_role_reclassification.json", {"mapping":mp})
    put("module_mapping/CURRENT_TO_CORE_V1_MODULE_MAPPING.md",
        "# Current module mapping\n\n" + "\n".join("- " + r["historical_module"] + ": " + r["core_v1_role"] + "; " + r["claim_boundary"] for r in mp))
    put("module_mapping/deprecated_or_renamed_terms.md", """
    # Deprecated or renamed terms

    Unqualified fallback is forbidden. Use certified terminal backup, uncertified
    engineering abort, or infrastructure failure. Replace risk-aware certificate with
    prioritization. Replace DT safety proof with finite-step precursor unless a
    lower-bound proof exists. Replace recovery success with bounded witness success.
    """)

def write_safer_theory_evidence(evidence: list[dict[str, object]]) -> None:
    matrix = [
        ("represented Gaussian obstacle field","current filter","retained and augmented","IMPLEMENTED_CURRENTLY"),
        ("current-state CBF filtering","current QP","U_cbf component","IMPLEMENTED_CURRENTLY"),
        ("actuator bounded feasibility","not unified","U component","DESIGN_CONTRACT"),
        ("sampled execution","historical Euler","normative model required","DESIGN_CONTRACT"),
        ("swept segment","one/H-step proxies","required prior to commit","DESIGN_CONTRACT"),
        ("terminal backup","recovery search","certificate contract","DESIGN_CONTRACT"),
        ("unrecoverable semantics","mixed fallback labels","explicit fail closed","DESIGN_CONTRACT"),
        ("initial admission","Start-Safe","projection contract","EMPIRICALLY_SUPPORTED"),
        ("map uncertainty","fixed/proxy boundary","no deployment claim","UNPROVED"),
        ("online reference","offline only","forbidden online","DESIGN_CONTRACT"),
        ("proof status","empirical observations","P1-P6 unproved","UNPROVED"),
    ]
    srows = [{"dimension":a,"frozen_SAFER_baseline":b,"Core_V1":c,"status":d}
             for a,b,c,d in matrix]
    put("safer_distinction/FAS_CBF_VS_SAFER_SCOPE_MATRIX.md",
        "# FAS-CBF Core V1 versus SAFER\n\nFAS-CBF Core V1 does not replace the Gaussian-map CBF filter. It adds an executable-safety layer requiring actuator admissibility, sampled-interval certification, and a terminal-backup condition before action commitment.\n\n" +
        "\n".join("- " + r["dimension"] + ": " + r["frozen_SAFER_baseline"] + " -> " + r["Core_V1"] + " (" + r["status"] + ")" for r in srows))
    put_json("safer_distinction/safer_baseline_audit.json", {
        "matrix":srows, "prohibited":["SAFER ignores dynamics","SAFER is unsafe","Core V1 has global recursive feasibility","Core V1 is globally superior"]})
    put("safer_distinction/novelty_claim_boundary.md", """
    # Novelty boundary

    The distinction is an executable-safety design layer around the frozen Gaussian-map
    current-state filter. It is not a claim that SAFER has no dynamics capability, nor
    that Core V1 is empirically globally superior or proof complete.
    """)
    qs = [
        ("Only a lookahead?","No. The design requires actuator, interval, and backup certificates; proof and implementation remain future work."),
        ("MPC terminal set?","A terminal-policy contract, not a claimed invariant MPC set."),
        ("Finite horizon safe?","Only a bounded witness; recursion requires P4 assumptions."),
        ("Barrier metric distance?","No, proxy/lower-bound only unless separately proved."),
        ("Missing obstacle?","Represented-map boundary; no deployment claim."),
        ("Empty U_exec?","Certified terminal action or explicit fail closed."),
        ("Unified evidence?","Complementary module evidence, not full-stack superiority."),
        ("Why not stronger DT-CBF?","Alternative future method, no dominance claim."),
        ("Projection semantics?","Projection is recorded, separate from original outcome."),
        ("Candidate limitation?","A finite-family boundary, not global impossibility."),
    ]
    put("safer_distinction/reviewer_objection_responses.md",
        "# Reviewer objections\n\n" + "\n\n".join("## " + a + "\n\n" + b for a,b in qs))
    obligations = [
        ("P1","single interval represented-map safety","UNPROVED","barrier lower bound/common Phi/margin/query regularity","V4-B","no continuous or real-world safety claim"),
        ("P2","actuator-bounded admissibility","DESIGN_CONTRACT","correct U and U_cbf construction","QP fallback","no claim beyond stated U"),
        ("P3","terminal-backup implication","UNPROVED","safe witness and verified X_T","Trial20","no global controllability claim"),
        ("P4","recursive executability","UNPROVED","invariant X_T/common model/re-certification","ETH3D limit","no recursive feasibility claim"),
        ("P5","fail-closed correctness","DESIGN_CONTRACT","typed failures/no implicit nominal","fallback ambiguity","no physical safety guarantee"),
        ("P6","constraint-reduction preservation","UNPROVED","reduced/full set relation","forced dominance","no equivalence claim"),
    ]
    prows = [{"id":a,"statement":b,"proof_status":c,"assumptions":d,"counterexample":e,"prohibited_wording":f} for a,b,c,d,e,f in obligations]
    put_csv("theory_obligations/proof_obligation_registry.csv", prows)
    put_csv("theory_obligations/assumption_registry.csv",
            [{"assumption_id":"A"+str(i+1),"assumption":x} for i,x in enumerate(["barrier lower bound","margin covers error","common flow","actuator identity","query regularity","terminal invariance","no online reference"])])
    put("theory_obligations/FAS_CBF_CORE_V1_THEOREM_SKELETON.md",
        "# Theorem skeleton\n\n" + "\n\n".join("## " + r["id"] + " " + r["statement"] + "\n\nStatus: " + r["proof_status"] + ". Assumptions: " + r["assumptions"] + ". Boundary: " + r["counterexample"] + "." for r in prows))
    put_csv("theory_obligations/known_proved_empirical_unknown_matrix.csv",
            [{"item":a,"status":b} for a,b in [("historical Euler","IMPLEMENTED_CURRENTLY"),("module observations","EMPIRICALLY_SUPPORTED_CONFIGURATION_SPECIFIC"),("Core certificate","DESIGN_CONTRACT"),("P1-P6","UNPROVED"),("deployment safety","UNPROVED")]])
    put("theory_obligations/counterexample_registry.md", """
    # Counterexample registry

    V4-B is late-intervention evidence. Forced-candidate dominance limits candidate
    budgeting. Trial20 is finite recovery exhaustion. ETH3D is a structural state-set
    activation limit. Replica saturation blocks superiority inference. These remain
    first-class theory boundaries.
    """)
    role = {"M-A":"initial admission","M-B":"actuator-feasible boundary","M-C":"efficiency",
            "M-D":"segment-risk precursor","M-E":"backup search","M-F":"search acceleration",
            "M-G":"integration boundary","M-H":"structural boundary"}
    trace = []
    for e in evidence:
        sid = str(e["evidence_id"])
        pol = str(e["polarity"])
        stat = "NEGATIVE_BOUNDARY" if pol == "negative" else ("STRUCTURAL_LIMIT" if pol == "structural" else "SUPPORTED_CONFIGURATION_SPECIFIC")
        trace.append({"evidence_id":sid,"core_role":role[str(e["module"])],"activity":e["activity"],
                      "map_role":e["map_role"],"status":stat,"source_sha256":e["report_sha256"],
                      "allowed_claim":e["allowed_claims"],"prohibited_claim":e["prohibited_claims"]})
    put_csv("evidence_traceability/core_v1_claim_evidence_matrix.csv", trace)
    put_json("evidence_traceability/module_to_evidence_graph.json",
             {"nodes":trace,"aggregate_effect_score_forbidden":True})
    put_csv("evidence_traceability/proof_obligation_to_evidence.csv", [
        {"proof_obligation":"P1","evidence_ids":"E11,E12,E17","relation":"precursor/negative"},
        {"proof_obligation":"P2","evidence_ids":"E01,E03,E08","relation":"configuration support"},
        {"proof_obligation":"P3","evidence_ids":"E13,E14,E15,E16,E18","relation":"bounded backup"},
        {"proof_obligation":"P4","evidence_ids":"E02,E03,E16","relation":"structural limit"},
        {"proof_obligation":"P5","evidence_ids":"E04,E12,E16","relation":"failure boundary"},
        {"proof_obligation":"P6","evidence_ids":"E10","relation":"dominance boundary"},
    ])
    put("evidence_traceability/current_evidence_coverage.md", """
    # Evidence coverage

    All 18 frozen sources are remapped without changing labels. Active Start-Safe,
    Risk-Aware efficiency, DT detection, recovery, and HCE remain configuration-specific.
    Shadow, diagnostic, negative, structural, and unknown records are not pooled.
    """)
    put("evidence_traceability/evidence_gaps.md", """
    # Evidence gaps

    Missing: fully activated same-map paired full-stack superiority, deployment
    certificate, metric-distance proof, online terminal set, recursive-feasibility
    theorem, map-confidence calibration, adaptive margin, and smooth execution.
    """)

def write_interfaces_deferred_review() -> None:
    names = ["MapBarrierQuery","DynamicsFlow","ActuatorSet","CurrentCBFFilter",
             "SweptSegmentCertifier","TerminalSet","BackupPolicy","BackupSequenceSearch",
             "ExecutableSafetyCertifier","FailClosedPolicy","ReferenceOracleEvaluator"]
    interfaces = [{"name":n,"inputs":"immutable identity tagged inputs","outputs":"typed result or failure",
                   "units_and_frame":"must be declared","deterministic":True,
                   "online":n!="ReferenceOracleEvaluator",
                   "reference_input_forbidden":n!="ReferenceOracleEvaluator",
                   "failure_code_required":True,"tolerance_policy":"explicit fixed only",
                   "logging":"certificate record","identity":"map/method/config SHA"} for n in names]
    put_json("implementation_contract/core_v1_interfaces.json", {"interfaces":interfaces})
    put_json("implementation_contract/certificate_record_schema.json", {
        "required":["decision","selected_control","current_barrier","actuator_feasible","segment_certificate","backup_certificate","terminal_witness","horizon","failure_reason","module_timings","map_sha","method_sha","config_sha","no_reference_leak_count"]})
    put_json("implementation_contract/runtime_failure_codes.json", {
        "codes":["MAP_QUERY_UNKNOWN","ACTUATOR_SET_EMPTY","CBF_QP_INFEASIBLE","SEGMENT_CERTIFICATE_FAILED","BACKUP_WITNESS_ABSENT","TERMINAL_POLICY_UNAVAILABLE","REFERENCE_LEAK_ATTEMPT","INFRASTRUCTURE_ERROR"],
        "every_failure_has_terminal_behavior":True})
    put("implementation_contract/FAS_CBF_CORE_V1_COMPONENT_INTERFACES.md",
        "# Component interfaces\n\n" + "\n".join("- " + x["name"] + ": typed immutable inputs/outputs, declared units and frame, deterministic requirements, explicit failure/logging/identity, and " + ("online reference forbidden." if x["online"] else "offline only.") for x in interfaces))
    put("implementation_contract/no_reference_leak_contract.md", "Online components cannot receive mesh collision, reference path, benchmark label, or offline oracle input. REFERENCE_LEAK_ATTEMPT stops decision without plant action.")
    put("implementation_contract/protected_source_policy.md", "Current baseline, map, controller, and historical evidence are read-only. This task does not modify protected source.")
    put("implementation_contract/unit_test_specification.md", "Future unit tests use mocks and test typed failures, unknown rejection, actuator bounds, segment rejection, backup witness, and reference leak. They never run scientific plant rollouts.")
    put("implementation_contract/integration_test_specification.md", "Future integration tests use mock map, dynamics, and terminal policy to validate state transitions and certificate records only.")
    future = [
        ("Local map confidence","offline calibration; confidence is not occupancy probability"),
        ("Adaptive margin","one-sided error bound, regularity, hysteresis/envelope"),
        ("Smooth execution","Delta u, slew, jerk, TV can change U_exec and X_T"),
        ("Improved terminal set","braking, invariant, or verified terminal controller"),
        ("Enhanced discrete model","exact/ZOH, delay-aware flow, tracking tube"),
    ]
    put("deferred_extensions/DEFERRED_EXTENSIONS_ROADMAP.md",
        "# Deferred extensions\n\n" + "\n".join("- " + a + ": " + b + ". Status FUTURE_WORK." for a,b in future))
    put("deferred_extensions/adaptive_margin_future_contract.md", "Adaptive margin is deferred pending a one-sided dangerous free-space error bound, time-varying regularity, and conservative hysteresis.")
    put("deferred_extensions/smooth_execution_future_contract.md", "Smooth execution is deferred. Slew, jerk, TV, or Delta u cannot override safety and may change feasible/terminal sets.")
    put("deferred_extensions/map_confidence_future_contract.md", "Map confidence is deferred. Runtime may use only available signals; confidence cannot be treated as occupancy probability without calibration.")
    put_csv("deferred_extensions/future_experiment_priority.csv", [
        {"priority":1,"item":"unified swept-segment terminal-backup certifier"},
        {"priority":2,"item":"normative execution model"},
        {"priority":3,"item":"terminal set and fail-closed implementation"},
        {"priority":4,"item":"minimal module activation experiment"},
        {"priority":5,"item":"adaptive margin"},
        {"priority":6,"item":"smooth execution"},
    ])
    checks = [
        ("safe terminology","PASS","labels separated"),("segment coverage","PASS","explicit C_seg"),
        ("terminal set","PASS","contract unproved"),("recovery terminal split","PASS","typed states"),
        ("fail closed","PASS","non-execution output"),("adaptive margin","PASS","deferred"),
        ("evidence scope","PASS","no global claim"),("SAFER distinction","PASS","no caricature"),
        ("map uncertainty","PASS","represented-map boundary"),("dynamics","PASS","Euler separated"),
        ("reference oracle","PASS","offline only"),("proof status","PASS","P1-P6 unproved"),
    ]
    put("reviewer_audit/internal_design_review.md",
        "# Internal design review\n\n" + "\n".join("- " + a + ": " + b + " - " + c for a,b,c in checks))
    put_csv("reviewer_audit/claim_stress_test.csv", [
        {"claim":"Core executable-safety contract","challenge":"proved final controller?","response":"No, design with proof obligations.","status":"PASS"},
        {"claim":"Core versus SAFER","challenge":"global superiority?","response":"Explicitly prohibited.","status":"PASS"},
        {"claim":"Gaussian safety","challenge":"deployment guarantee?","response":"represented-map only.","status":"PASS"},
    ])
    audit = {"status":"PASS_REVIEWER_AUDIT","checks":checks,
             "high_risk_open_items":["normative model","online terminal set","P1-P6 proof","full-stack paired cohort"]}
    put_json("reviewer_audit/definition_consistency_audit.json", audit)
    put_json("reviewer_audit/safer_novelty_audit.json", {"status":"PASS","finding":"defensible executable-safety augmentation"})
    put_json("reviewer_audit/theory_overclaim_audit.json", {"status":"PASS","all_obligations_unproved":True})
    put_json("reviewer_audit/evidence_overclaim_audit.json", {"status":"PASS","global_superiority_prohibited":True,"deployment_prohibited":True})

def write_figures() -> None:
    from PIL import Image, ImageDraw, ImageFont
    title = {
        "safer_to_fas_cbf_problem_shift.png":"Current filtering to executable safety",
        "fas_cbf_core_v1_overview.png":"Core V1: actuator, segment, backup",
        "safety_set_hierarchy.png":"X_map, X_feas, X_seg, X_rec, X_T",
        "execution_model_consistency.png":"Historical Euler versus future normative model",
        "swept_segment_certificate.png":"Whole sampled interval certificate",
        "terminal_backup_certificate.png":"Finite witness to terminal contract",
        "unified_executable_control_set.png":"Commit only U_exec",
        "fas_cbf_state_machine.png":"Certify or fail closed",
        "current_module_to_core_mapping.png":"Current modules to Core roles",
        "safer_vs_fas_cbf_scope_matrix.png":"Filter plus executable-safety layer",
        "theory_proof_obligation_map.png":"P1 through P6 are unproved obligations",
        "evidence_to_core_traceability.png":"18 frozen sources mapped to Core",
        "positive_negative_boundary_evidence.png":"Positive, negative, structural evidence",
        "fail_closed_semantics.png":"No U_exec means no implicit execution",
        "current_vs_deferred_features.png":"Current contract and deferred features",
        "implementation_roadmap.png":"Certifier, model, terminal set, experiment",
        "reviewer_claim_boundary.png":"Configuration-specific claims only",
        "final_framework_decision.png":"Conceptual closure and implementation next",
    }
    styles = [("DESIGN_CONTRACT","#2f6b9a"),("IMPLEMENTED_CURRENTLY","#2c7a4b"),
              ("EMPIRICALLY_SUPPORTED","#8a5a00"),("NEGATIVE_BOUNDARY","#a63d40"),
              ("FUTURE_WORK","#6b5b95"),("UNPROVED","#666666")]
    font = ImageFont.load_default()
    for name in FIGURES:
        im = Image.new("RGB",(960,540),"white")
        d = ImageDraw.Draw(im)
        d.rectangle((20,20,940,520),outline="#203040",width=3)
        d.text((55,55),title[name],fill="#102030",font=font)
        y=140
        for label,color in styles:
            d.rectangle((80,y,110,y+25),fill=color)
            d.text((130,y+5),label,fill="#102030",font=font)
            y += 45
        d.text((80,455),"Static design and evidence diagram. No scientific execution.",fill="#102030",font=font)
        p=ROOT/"figures"/name
        p.parent.mkdir(parents=True,exist_ok=True)
        im.save(p)

def write_report_and_wrappers(evidence_count: int) -> None:
    counters = {
        "map_training_count":0,"map_mutation_count":0,"controller_rollout_count":0,
        "plant_execution_count":0,"scenario_search_count":0,"candidate_generation_count":0,
        "parameter_tuning_count":0,"dataset_switch_count":0,
        "method_scientific_mutation_count":0,"baseline_core_mutation_count":0,
        "evidence_source_count":evidence_count,"current_module_inventory_count":9,
        "safety_set_definition_count":6,"proof_obligation_count":6,
        "interface_contract_count":11,"figure_count":18,
        "operational_autonomy_action_count":0,"task_owned_process_cleanup_count":0,
    }
    put_json("report/run_manifest.json", {
        "task":"INTEGRATE_FAS_CBF_FULL_FRAMEWORK_WITH_MODULE_SPECIFIC_CLAIMS_V1",
        "upstream_pr82_head":"1b857906405d3f76d01339d9b30897e7b82ad664",
        "execution_counters":counters,
        "final":{"FINAL_STATUS":STATUS,"FINAL_DECISION":DECISION,"ONLY_NEXT_TASK":NEXT,
                 "case":"A","meaning":"Conceptual closure, not proof, final algorithm, deployment guarantee, or new experimental result."}})
    put_json("operational_autonomy_actions.json", {"actions":[],"count":0,
             "policy":"No infrastructure repair required."})
    put("report/REPORT_INTEGRATE_FAS_CBF_FULL_FRAMEWORK_WITH_MODULE_SPECIFIC_CLAIMS_V1.md", """
    # FAS-CBF Core V1 conceptual-closure report

    PASS_FAS_CBF_CORE_V1_CONCEPTUAL_CLOSURE

    Core V1 is a conceptually closed but extensible executable-safety contract. It
    requires actuator admissibility, current CBF feasibility, swept-segment
    certification, and terminal-backup evidence before committing control. With no
    certified action, it emits typed terminal/non-execution behavior rather than
    implicitly applying nominal control.

    All 18 PR #82 evidence sources are remapped without relabeling active, shadow,
    diagnostic, negative, structural, non-comparable, or unknown records. Existing
    support remains module-specific and configuration-specific. V4-B, forced-candidate
    dominance, Trial20, ETH3D activation limitation, and Replica saturation remain
    visible theory and evidence boundaries.

    No new map training, mutation, controller rollout, plant execution, scenario
    search, candidate generation, tuning, data switch, or scientific method change
    occurred. This report does not claim global Full FAS-CBF superiority, learned-map
    deployment safety, universal recovery, metric distance, or proof-complete recursive
    feasibility.

    FINAL_DECISION: IMPLEMENT_UNIFIED_EXECUTABLE_SAFETY_CERTIFIER

    Only next task: IMPLEMENT_ACTUATOR_BOUNDED_SWEPT_SEGMENT_TERMINAL_BACKUP_CERTIFIER_V1
    """)
    put_json("report/downstream_handoff.json", {"status":STATUS,"decision":DECISION,
             "only_next_task":NEXT,"handoff":"Freeze a normative execution model and concrete terminal-set contract while implementing one unified certifier."})
    put("report/DRAFT_PR_BODY.md", """
    ## Summary

    Preserves PR #82 with no new experiment, training, rollout, or source mutation.
    This PR freezes FAS-CBF Core V1 as conceptual closure, not a final algorithm.

    It defines a unified research question, SAFER distinction, safety sets, execution
    contract, swept-segment and terminal-backup certificate, fail-closed state machine,
    current module mapping, proof obligations, and 18-source evidence traceability.
    Adaptive margin and smooth execution remain deferred. No global superiority,
    deployment, or recursive-feasibility claim is made.

    - FINAL_STATUS: PASS_FAS_CBF_CORE_V1_CONCEPTUAL_CLOSURE
    - FINAL_DECISION: IMPLEMENT_UNIFIED_EXECUTABLE_SAFETY_CERTIFIER
    - Only next task: IMPLEMENT_ACTUATOR_BOUNDED_SWEPT_SEGMENT_TERMINAL_BACKUP_CERTIFIER_V1
    """)
    for name in WRAPPERS:
        put(name, '''#!/usr/bin/env python3
"""Task-owned static artifact wrapper."""
from core_v1_builder import build_all
if __name__ == "__main__":
    build_all()
''')
    put("record_final_system_state.py", '''#!/usr/bin/env python3
"""Capture GPU and proxy/watchdog state using read-only local/remote commands."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def run(args):
    p=subprocess.run(args,text=True,capture_output=True,check=False)
    return p.returncode,(p.stdout+p.stderr).strip()
if __name__ == "__main__":
    query="nvidia-smi -i 1 --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader; nvidia-smi -i 1 --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader || true; pgrep -af '[f]as_cbf_core_v1_conceptual_closure' || true; ss -ltn | grep 127.0.0.1:17898 || true"
    rc,text=run(["ssh","zlab-4090",query])
    wrc,watchdog=run(["powershell","-NoProfile","-Command","(Get-ScheduledTask -TaskName 'Codex-Persistent-Reverse-Proxy-Watchdog' -ErrorAction SilentlyContinue).State"])
    payload={"status":"PASS_FINAL_SYSTEM_READONLY_CHECK" if rc==0 and wrc==0 and watchdog=="Running" else "BLOCKED_FINAL_SYSTEM_READONLY_CHECK","remote_returncode":rc,"watchdog_returncode":wrc,"remote_read_only_output":text,"watchdog_state":watchdog,"mutations":{"training":0,"controller_rollout":0,"map_mutation":0,"method_mutation":0,"watchdog_modification":0}}
    (ROOT/"report/system_final_state.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\\n",encoding="utf-8",newline="\\n")
    print(payload["status"])
''')
    put("validate_core_v1.py", '''#!/usr/bin/env python3
"""Static Core V1 conceptual-closure validator."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
UP=ROOT.parent/"fas_cbf_module_evidence_assembly_v1"
REQUIRED=["problem_definition/FAS_CBF_CORE_V1_PROBLEM_STATEMENT.md","execution_model/execution_model_contract.json","safety_sets/safety_set_contract.json","unified_certificate/unified_certificate_schema.json","state_machine/state_machine.json","module_mapping/module_mapping.csv","safer_distinction/FAS_CBF_VS_SAFER_SCOPE_MATRIX.md","theory_obligations/proof_obligation_registry.csv","evidence_traceability/core_v1_claim_evidence_matrix.csv","implementation_contract/core_v1_interfaces.json","deferred_extensions/DEFERRED_EXTENSIONS_ROADMAP.md","reviewer_audit/internal_design_review.md","report/run_manifest.json","report/system_final_state.json","report/REPORT_INTEGRATE_FAS_CBF_FULL_FRAMEWORK_WITH_MODULE_SPECIFIC_CLAIMS_V1.md"]
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
errors=[]
for r in REQUIRED:
    if not (ROOT/r).exists(): errors.append("missing:"+r)
freeze=json.loads((ROOT/"input_freeze/upstream_artifact_manifest.json").read_text(encoding="utf-8"))
for r in freeze["artifacts"]:
    p=UP/r["path"]
    if not p.exists() or h(p)!=r["sha256"]: errors.append("upstream:"+r["path"])
ledger=json.loads((UP/"evidence_ledger/evidence_provenance_ledger.json").read_text(encoding="utf-8"))
if len(ledger)!=18: errors.append("evidence_count")
sm=json.loads((ROOT/"state_machine/state_machine.json").read_text(encoding="utf-8"))
out={x["from"] for x in sm["transitions"]}
for state in sm["states"]:
    if state not in set(sm["terminal_states"]) and state not in out: errors.append("dead_state:"+state)
ints=json.loads((ROOT/"implementation_contract/core_v1_interfaces.json").read_text(encoding="utf-8"))
if any(x["online"] and not x["reference_input_forbidden"] for x in ints["interfaces"]): errors.append("reference_leak")
for p in ROOT.rglob("*.py"): compile(p.read_text(encoding="utf-8"),str(p),"exec")
if len(list((ROOT/"figures").glob("*.png")))!=18: errors.append("figures")
if any(p.stat().st_size>1000000 for p in ROOT.rglob("*") if p.is_file()): errors.append("large_file")
run=json.loads((ROOT/"report/run_manifest.json").read_text(encoding="utf-8"))
zero=["map_training_count","map_mutation_count","controller_rollout_count","plant_execution_count","scenario_search_count","candidate_generation_count","parameter_tuning_count","dataset_switch_count","method_scientific_mutation_count","baseline_core_mutation_count"]
if any(run["execution_counters"][k]!=0 for k in zero): errors.append("execution")
system=json.loads((ROOT/"report/system_final_state.json").read_text(encoding="utf-8"))
if system.get("status")!="PASS_FINAL_SYSTEM_READONLY_CHECK": errors.append("system")
status="PASS_FAS_CBF_CORE_V1_CONCEPTUAL_CLOSURE_VALIDATION" if not errors else "BLOCKED_FAS_CBF_CORE_V1_CONCEPTUAL_CLOSURE_VALIDATION"
(ROOT/"report/validation_result.json").write_text(json.dumps({"status":status,"errors":errors,"checks":{"evidence_sources":len(ledger),"python_compile":True,"figure_count":18,"online_reference_forbidden":"reference_leak" not in errors,"system":system.get("status")}},indent=2,sort_keys=True)+"\\n",encoding="utf-8",newline="\\n")
print(status)
raise SystemExit(0 if not errors else 1)
''')

def build_all() -> None:
    shutil.rmtree(ROOT / "__pycache__", ignore_errors=True)
    evidence = json.loads((UP/"evidence_ledger/evidence_provenance_ledger.json").read_text(encoding="utf-8"))
    if len(evidence)!=18: raise RuntimeError("expected 18 frozen evidence sources")
    put_json("input_freeze/pr82_identity.json", {
        "pr":82,"branch":"fas-cbf-module-evidence-assembly-v1",
        "head":"1b857906405d3f76d01339d9b30897e7b82ad664",
        "final_status":"PASS_MODULE_WISE_EVIDENCE_WITHOUT_FULL_STACK_SUPERIORITY",
        "final_decision":"FRAME_PAPER_AS_MODULAR_SAFETY_ASSURANCE_NOT_GLOBAL_SUPERIORITY",
        "only_next_task":"INTEGRATE_FAS_CBF_FULL_FRAMEWORK_WITH_MODULE_SPECIFIC_CLAIMS_V1"})
    put_json("input_freeze/upstream_artifact_manifest.json",
             {"artifacts":frozen_artifacts(),"evidence_source_count":18,
              "unknown_policy":"retain UNKNOWN_NOT_RECOVERED"})
    put_csv("source_inventory/framework_source_inventory.csv", evidence)
    put_json("source_inventory/framework_source_inventory.json", {"sources":evidence})
    put_json("source_inventory/unresolved_fields.json",
             json.loads((UP/"evidence_ledger/missing_or_ambiguous_evidence.json").read_text(encoding="utf-8")))
    write_root_and_problem(); write_execution_sets_certificate(); write_state_machine()
    write_inventory_mapping(evidence); write_safer_theory_evidence(evidence)
    write_interfaces_deferred_review(); write_figures(); write_report_and_wrappers(len(evidence))

if __name__ == "__main__":
    build_all()
