#!/usr/bin/env python3
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
(ROOT/"report/validation_result.json").write_text(json.dumps({"status":status,"errors":errors,"checks":{"evidence_sources":len(ledger),"python_compile":True,"figure_count":18,"online_reference_forbidden":"reference_leak" not in errors,"system":system.get("status")}},indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
print(status)
raise SystemExit(0 if not errors else 1)
