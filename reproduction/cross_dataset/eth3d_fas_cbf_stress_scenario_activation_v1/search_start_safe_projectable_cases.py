#!/usr/bin/env python3
import json
from task_config_v2 import TASK_ROOT
def main():
 d=json.loads((TASK_ROOT/"candidate_pool/candidate_pool_summary.json").read_text())["qualified_pool_counts"]
 assert d.get("G1_PROJECTABLE",0)>=12 and d.get("G1_NEAR",0)>=4 and d.get("G1_UNPROJECTABLE",0)>=4,d
 print("PASS_START_SAFE_SEARCH"); return 0
if __name__=="__main__": raise SystemExit(main())
