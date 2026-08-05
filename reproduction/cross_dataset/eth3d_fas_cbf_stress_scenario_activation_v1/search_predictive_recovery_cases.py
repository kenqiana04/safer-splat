#!/usr/bin/env python3
import json
from task_config_v2 import TASK_ROOT
def main():
 d=json.loads((TASK_ROOT/"candidate_pool/candidate_pool_summary.json").read_text())["qualified_pool_counts"]
 assert d.get("G4_RECOVERABLE",0)>=14 and d.get("G4_UNRECOVERABLE",0)>=6,d
 print("PASS_PREDICTIVE_RECOVERY_SEARCH"); return 0
if __name__=="__main__": raise SystemExit(main())
