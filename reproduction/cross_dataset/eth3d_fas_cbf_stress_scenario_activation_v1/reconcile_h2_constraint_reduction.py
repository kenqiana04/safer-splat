#!/usr/bin/env python3
"""Fail closed unless the V1 H2 reconciliation is complete and exact."""
import json
from task_config_v2 import METHODS,TASK_ROOT

def main() -> int:
    d=json.loads((TASK_ROOT/"v1_semantic_audit/v1_metric_aggregation_audit.json").read_text())
    m1=d["method_summary"][METHODS[1]]["active_constraints_mean_all_100_terminal_records"]
    m2=d["method_summary"][METHODS[2]]["active_constraints_mean_all_100_terminal_records"]
    assert abs(m1-1600.0)<1e-12 and abs(m2-160.0405329011306)<1e-6,(m1,m2)
    print(json.dumps({"status":"PASS_V1_H2_RECONCILIATION","M1":m1,"M2":m2},sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
