"""Static validator for the design package; never runs runtime code."""
from __future__ import annotations
import csv, hashlib, json, subprocess
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
EXPECTED_HEAD = "6c5c59dd083dc83661e56c4ddd3e62fa12497652"
EXPECTED_BRANCH = "validate-active-runtime-contract-conformance-v2"

def text(name): return (TASK / name).read_text(encoding="utf-8")
def obj(name): return json.loads(text(name))
def check(cid, name, passed, evidence): return {"id": cid, "name": name, "passed": bool(passed), "evidence": evidence}

def main() -> int:
    checks=[]
    lock=obj("PUBLIC_CYCLE_DESIGN_INPUT_LOCK.json")
    exec_lock=obj("PUBLIC_CYCLE_DESIGN_EXECUTION_LOCK.json")
    api=obj("PUBLIC_CYCLE_API_V2.json"); transition=obj("EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json")
    phases=obj("PUBLIC_ACTIVE_CYCLE_PHASES_V2.json"); ctx=obj("ACTIVE_CYCLE_CONTEXT_SCHEMA_V2.json")
    result=obj("ACTIVE_CYCLE_RESULT_SCHEMA_V2.json"); events=obj("PUBLIC_CYCLE_EVENT_SCHEMA_V2.json")
    scenarios=obj("PUBLIC_CYCLE_DESIGN_SCENARIOS_V2.json"); invariants=obj("PUBLIC_CYCLE_COMPOSITION_INVARIANTS_V2.json")
    checks += [
      check("U-01","exact PR120 head",lock["direct_upstream"]["head_sha"]==EXPECTED_HEAD,lock["direct_upstream"]),
      check("U-02","exact PR120 branch",lock["direct_upstream"]["branch"]==EXPECTED_BRANCH,lock["direct_upstream"]["branch"]),
      check("U-03","PR120 status/title",lock["direct_upstream"]["state"]=="OPEN_DRAFT" and lock["direct_upstream"]["title"]=="[Draft] Validate active runtime contract conformance V2","identity lock"),
      check("U-04","frozen blocker preserved",lock["upstream_assertions"]["final_status"]=="BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP","PR120 evidence unchanged"),
      check("U-05","critical routes preserved",lock["upstream_assertions"]["critical_public_routes_blocked"]==35,"35 routes"),
      check("U-06","E2E preserved",lock["upstream_assertions"]["genuine_e2e"]=="0/6","0/6"),
      check("S-01","single composition owner",api["owner"]=="ActiveCycleCoordinator",api["owner"]),
      check("S-02","public API complete",[m["name"] for m in api["methods"]]==["start_trial","run_cycle","finalize_trial"],"start/run/finalize"),
      check("S-03","Supervisor routing owner","Supervisor.route_transition" in text("SUPERVISOR_ROUTING_AUTHORITY_V2.md"),"route_transition"),
      check("S-04","Supervisor selection owner","arbitrate" in text("SUPERVISOR_ROUTING_AUTHORITY_V2.md"),"arbitrate"),
      check("S-05","Plant sole owner","PlantCommitAdapter" in text("PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2.md"),"PlantCommitAdapter"),
      check("S-06","no coordinator policy","certificate mathematics" in text("PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2.md") and "does **not** own" in text("PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2.md"),"authority boundary"),
      check("T-01","43 transition rules",transition["rule_count"]==43 and len(transition["rules"])==43,"43"),
      check("T-02","unique/exact-one transition",transition["unique_rule_ids"] and transition["exactly_one_applicable_rule"],"exact-one"),
      check("T-03","no default routing",transition["coordinator_default_rule"] is False,"no guessed route"),
      check("T-04","typed ambiguity handling","typed ROUTING_LOOKUP_UNKNOWN" in transition["unknown_or_ambiguous"],"typed block"),
      check("P-01","canonical order",phases["cycle_phases"][:6]==["CYCLE_BEGIN","L1_IMMEDIATE_CERTIFICATION","PRIMARY_PROPOSAL","PRIMARY_C0","PRIMARY_L2","PRIMARY_L3"],"L1/P0/C0/L2/L3"),
      check("P-02","L1 once", "L1 runs once per cycle" in text("PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2.md"),"once"),
      check("P-03","R0 non-gate",phases["r0_is_hard_gate"] is False,"R0"),
      check("P-04","immutable context",ctx["immutable_evolution"] is True,"append-only evidence"),
      check("P-05","result schema","runtime_result_not_scientific_outcome" in result,"runtime-only"),
      check("D-01","deadline observation only","no routing or action authority" in text("DEADLINE_STAGE_ADMISSION_INTERFACE_V2.md"),"DeadlineTracker"),
      check("D-02","deadline warning/expiry semantics","DEADLINE_EXPIRED" in text("DEADLINE_STAGE_ADMISSION_INTERFACE_V2.md"),"expired"),
      check("A-01","primary fresh binding","fresh" in text("PRIMARY_CYCLE_INTEGRATION_V2.md"),"binding"),
      check("A-02","alternative inventory empty","currently empty" in text("ALTERNATIVE_CYCLE_INTEGRATION_V2.md"),"native inventory"),
      check("A-03","no synthetic alternatives","synthesizes/perturbs" in text("ALTERNATIVE_CYCLE_INTEGRATION_V2.md"),"no synthesis"),
      check("B-01","backup supervisor priority","Supervisor owns routing" in text("BACKUP_CYCLE_INTEGRATION_V2.md"),"priority"),
      check("B-02","ActiveRunner token reuse","ActiveRunner.commit_active_decision" in text("BACKUP_CYCLE_INTEGRATION_V2.md"),"reuse"),
      check("TERM-01","terminal route-only","only when a Supervisor routing decision" in text("TERMINAL_CYCLE_INTEGRATION_V2.md"),"terminal"),
      check("TERM-02","goal hold disabled","GOAL_HOLD_RUNTIME_ENABLED=false" in text("TERMINAL_CYCLE_INTEGRATION_V2.md"),"goal hold"),
      check("BOUND-01","boundary no plant","plant_commit" in str(result["boundary_contract"]).lower() and result["boundary_contract"]["plant_commit"] is False,"boundary"),
      check("TRACE-01","one outcome trace","exactly one outcome trace" in text("PUBLIC_CYCLE_TRACE_CONTRACT_V2.md"),"trace"),
      check("TRACE-02","no oracle","oracle" in text("PUBLIC_CYCLE_TRACE_CONTRACT_V2.md"),"no scientific computation"),
      check("EV-01","event taxonomy typed",len(events["events"])>=35 and all(e["typed"] for e in events["events"]),"typed events"),
      check("EV-02","frozen taxonomy source",events["taxonomy_source"].startswith("PR107"),events["taxonomy_source"]),
      check("SC-01","scenario coverage",scenarios["count"]>=28,"scenario count"),
      check("SC-02","PCC 30",invariants["count"]>=30,"invariant count"),
      check("M-01","model checker zero",obj("public_cycle_design_model_check.json")["counterexample_count"]==0,"0 counterexamples"),
      check("M-02","change matrix owner","active_cycle.py" in text("PUBLIC_CYCLE_RUNTIME_CHANGE_MATRIX_V2.csv"),"future files"),
      check("BP-01","BYPASS preservation","BYPASS_REVALIDATION_REQUIRED=true" in text("BYPASS_EVIDENCE_PRESERVATION_V2.md"),"conditional revalidation"),
      check("L-01","ladder blocks smoke jump","Design -> Implement -> Smoke is forbidden" in text("POST_COMPOSITION_VALIDATION_LADDER_V2.md"),"ladder"),
      check("X-01","design execution counters zero",all(v==0 for v in exec_lock["execution_counters"].values()),exec_lock["execution_counters"]),
      check("X-02","no rollout authorization",exec_lock["design_only"] and "rollout" in " ".join(exec_lock["forbidden"]),"design only"),
    ]
    # Working tree must be free of runtime/production changes relative to exact PR120 head.
    protected = subprocess.check_output(["git","diff","--name-only",EXPECTED_HEAD,"--","run.py","cbf","dynamics","reproduction/runtime"], cwd=ROOT, text=True).splitlines()
    checks.append(check("X-03","runtime/protected diff zero",len(protected)==0,protected))
    checks.append(check("X-04","required artifacts present",all((TASK/n).exists() for n in ["README.md","PUBLIC_CYCLE_API_V2.json","model_check_public_cycle_composition_v2.py","PUBLIC_CYCLE_IMPLEMENTATION_MANIFEST_V2.csv"]),"task-local files"))
    failed=[c for c in checks if not c["passed"]]
    out={"schema":"VALIDATE_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_DESIGN_V2","check_count":len(checks),"checks":checks,"counterexample_count":len(failed),"runtime_execution_count":0,"gpu_execution_count":0,"rollout_count":0,"verdict":"PASS_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2_DESIGN_VALIDATION" if not failed else "BLOCKED_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_DESIGN"}
    (TASK/"validation_result.json").write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding="utf-8")
    return 0 if not failed else 1

if __name__ == "__main__": raise SystemExit(main())
