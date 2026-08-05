#!/usr/bin/env python3
"""Validate the activation artifact emitted by the canonical V1 audit."""
import json
from task_config_v2 import TASK_ROOT

def main() -> int:
    p=TASK_ROOT/"v1_semantic_audit/v1_activation_semantics.json"; d=json.loads(p.read_text())
    assert d["v1_reported"]=={"H1_START_SAFE":14,"H2_FEASIBILITY_AWARE":0,"H3_DISCRETE_TIME":0,"H4_PREDICTIVE_RECOVERY":0}
    assert d["defect"]["code"]=="V1_BENCHMARK_SEMANTIC_DEFECT"
    print("PASS_V1_ACTIVATION_AUDIT")
    return 0
if __name__=="__main__": raise SystemExit(main())
