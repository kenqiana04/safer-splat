#!/usr/bin/env python3
import json
from task_config_v2 import TASK_ROOT
def main():
 d=json.loads((TASK_ROOT/"candidate_pool/candidate_pool_summary.json").read_text())["qualified_pool_counts"]
 assert d.get("G2",0)>=20,d; print("PASS_FEASIBILITY_DOMINANCE_SEARCH"); return 0
if __name__=="__main__": raise SystemExit(main())
