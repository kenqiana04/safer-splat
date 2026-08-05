"""Freeze PR #83 identities from canonical Git blob bytes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

from task_config import TASK_ROOT,UPSTREAM_BRANCH,UPSTREAM_HEAD,UPSTREAM_PR

REPO=TASK_ROOT.parents[2]
CORE_ROOT="reproduction/cross_dataset/fas_cbf_core_v1_conceptual_closure"
ARTIFACTS={
    "report":f"{CORE_ROOT}/report/REPORT_INTEGRATE_FAS_CBF_FULL_FRAMEWORK_WITH_MODULE_SPECIFIC_CLAIMS_V1.md",
    "execution_model":f"{CORE_ROOT}/execution_model/execution_model_contract.json",
    "safety_sets":f"{CORE_ROOT}/safety_sets/safety_set_contract.json",
    "unified_certificate":f"{CORE_ROOT}/unified_certificate/unified_certificate_schema.json",
    "state_machine":f"{CORE_ROOT}/state_machine/state_machine.json",
    "component_interfaces":f"{CORE_ROOT}/implementation_contract/core_v1_interfaces.json",
    "proof_obligations":f"{CORE_ROOT}/theory_obligations/proof_obligation_registry.csv",
    "module_inventory":f"{CORE_ROOT}/source_inventory/current_code_module_inventory.json",
    "evidence_traceability":f"{CORE_ROOT}/evidence_traceability/core_v1_claim_evidence_matrix.csv",
    "protected_hash_registry":f"{CORE_ROOT}/source_inventory/protected_core_hashes.json",
}
PROTECTED=(
    "dynamics/systems.py","cbf/cbf_utils.py","splat/gsplat_utils.py","splat/distances.py","run.py",
    "work/risk_aware_cbf/scripts/run_v4b_corrective_dt_filter.py",
    "work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py",
    "work/risk_aware_cbf/scripts/v4c_hierarchical_candidate_evaluator.py",
    "work/risk_aware_cbf/scripts/gsplat_barrier_geometry_adapter.py",
)


def run(*args:str)->bytes:
    return subprocess.check_output(args,cwd=REPO)


def canonical(path:str)->dict:
    data=run("git","show",f"{UPSTREAM_HEAD}:{path}")
    blob=run("git","rev-parse",f"{UPSTREAM_HEAD}:{path}").decode().strip()
    return {"path":path,"size":len(data),"sha256":hashlib.sha256(data).hexdigest(),"git_blob":blob}


def write_json(path:Path,value:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")


def main()->None:
    pr=json.loads(run("gh","pr","view",str(UPSTREAM_PR),"--json","number,state,isDraft,mergeable,headRefName,headRefOid,baseRefName,title,url"))
    expected={"state":"OPEN","isDraft":True,"mergeable":"MERGEABLE","headRefName":UPSTREAM_BRANCH,"headRefOid":UPSTREAM_HEAD,"baseRefName":"fas-cbf-module-evidence-assembly-v1"}
    checks={key:pr.get(key)==value for key,value in expected.items()}
    if not all(checks.values()): raise SystemExit("BLOCKED_PR83_IDENTITY_MISMATCH "+json.dumps(checks,sort_keys=True))
    artifacts={name:canonical(path) for name,path in ARTIFACTS.items()}
    protected={path:canonical(path) for path in PROTECTED}
    identity={"pr":pr,"expected":expected,"checks":checks,"canonical_identity_policy":"GIT_BLOB_BYTES_SHA256_V1","preserved":True}
    write_json(TASK_ROOT/"input_freeze"/"pr83_identity.json",identity)
    write_json(TASK_ROOT/"input_freeze"/"pr83_artifact_manifest.json",{"upstream_head":UPSTREAM_HEAD,"artifact_count":len(artifacts),"artifacts":artifacts})
    write_json(TASK_ROOT/"input_freeze"/"protected_source_hashes.json",{"upstream_head":UPSTREAM_HEAD,"protected_source_count":len(protected),"files":protected})
    print("PASS_PR83_INPUT_FREEZE",len(artifacts),len(protected))


if __name__=="__main__": main()
