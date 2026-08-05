#!/usr/bin/env python3
import json
from task_config_v2 import TASK_ROOT
def main():
 d=json.loads((TASK_ROOT/"paired_analysis/terminal_transition_matrices.json").read_text()); assert len(d)==5; print("PASS_V2_TERMINAL_TRANSITIONS"); return 0
if __name__=="__main__": raise SystemExit(main())
