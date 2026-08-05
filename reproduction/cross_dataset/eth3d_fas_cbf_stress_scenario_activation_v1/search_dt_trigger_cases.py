#!/usr/bin/env python3
import json
from task_config_v2 import TASK_ROOT
def main():
 d=json.loads((TASK_ROOT/"candidate_pool/candidate_pool_summary.json").read_text())["qualified_pool_counts"]
 assert sum(d.get(k,0) for k in ("G3_ENDPOINT_UNSAFE","G3_ENDPOINT_ONLY","G3_MARGIN"))>=20,d
 print("PASS_DT_TRIGGER_SEARCH"); return 0
if __name__=="__main__": raise SystemExit(main())
