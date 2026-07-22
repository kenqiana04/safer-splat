"""Read-only source audit; no controller, dynamics, QP, or rollout execution."""
from __future__ import annotations
import json
from pathlib import Path
def main():
 out={'query_return_fields':['h','grad_h','hess_h','info'],'runtime_gradient_source':'official GSplatLoader.query_distance analytical grad_h','autograd_to_map_parameters_required':False,'query_state_gradient_required':True,'hessian_consumed_by_cbf_qp':True,'hessian_evidence':['cbf/cbf_utils.py:45','cbf/cbf_utils.py:50-63'],'hessian_status':'HESSIAN_CONTRACT_UNQUALIFIED','static_calibrated_audit_authorized':False,'g1_authorized':False,'read_only_audit':True}
 root=Path(__file__).parent; (root/'downstream_gradient_contract.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');(root/'DOWNSTREAM_QUERY_CONTRACT_AUDIT.md').write_text('# Downstream query contract audit\n\n`CBF.get_QP_matrices` consumes `h`, `grad_h`, and `hes_h`; the Hessian enters both second-order Lie-derivative terms. The calibrated contract therefore covers only query/state gradient, not the required Hessian. No downstream execution occurred.\n');print(json.dumps(out))
if __name__=='__main__':main()
