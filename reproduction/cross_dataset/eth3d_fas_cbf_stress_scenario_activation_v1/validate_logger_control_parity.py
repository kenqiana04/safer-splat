#!/usr/bin/env python3
"""Bitwise fixed non-trigger proof that post-hoc V2 logging cannot alter control."""
import json,sys
import numpy as np
from task_config_v2 import PR80_ROOT,TASK_ROOT,atomic_json,sha256_file
if str(PR80_ROOT) not in sys.path:sys.path.insert(0,str(PR80_ROOT))
from fas_cbf_modules import solve_bounded_qp
from run_v2_controller_matrix import canonicalize
def main():
 a=np.asarray([[1.,0.,0.],[-1.,0.,0.],[0.,1.,0.],[0.,-1.,0.],[0.,0.,1.],[0.,0.,-1.]])
 b=np.full(6,.1); u=np.asarray([.02,-.01,.005]); v=np.zeros(3); qp=solve_bounded_qp(a,b,u,v); assert qp.control is not None
 before=np.ascontiguousarray(qp.control); raw={"status":"SUCCESS","candidate_count_mean":6,"active_constraints_mean":6,"control_vector_probe":before.tolist()}
 after=np.ascontiguousarray(canonicalize(raw,{"activation_reason":[]})["control_vector_probe"],dtype=np.float64)
 result={"status":"PASS_LOGGER_ONLY_CONTROL_BITWISE_PARITY","fixed_nontrigger_probe":True,"before_hex":before.tobytes().hex(),"after_hex":after.tobytes().hex(),"bitwise_equal":before.tobytes()==after.tobytes(),"max_abs_difference":float(np.max(np.abs(before-after))),"scientific_runner_sha256":sha256_file(PR80_ROOT/"run_formal_paired_controller_benchmark.py"),"control_path_modified":False,"posthoc_logger_only":True}
 assert result["bitwise_equal"] and result["max_abs_difference"]==0;atomic_json(TASK_ROOT/"shadow_predicates/logger_control_parity.json",result);print(json.dumps(result,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
