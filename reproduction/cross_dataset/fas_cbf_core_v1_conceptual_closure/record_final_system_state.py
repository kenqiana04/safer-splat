#!/usr/bin/env python3
"""Capture GPU and proxy/watchdog state using read-only local/remote commands."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def run(args):
    p=subprocess.run(args,text=True,capture_output=True,check=False)
    return p.returncode,(p.stdout+p.stderr).strip()
if __name__ == "__main__":
    query="nvidia-smi -i 1 --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader; nvidia-smi -i 1 --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader || true; pgrep -af '[f]as_cbf_core_v1_conceptual_closure' || true; ss -ltn | grep 127.0.0.1:17898 || true"
    rc,text=run(["ssh","zlab-4090",query])
    wrc,watchdog=run(["powershell","-NoProfile","-Command","(Get-ScheduledTask -TaskName 'Codex-Persistent-Reverse-Proxy-Watchdog' -ErrorAction SilentlyContinue).State"])
    payload={"status":"PASS_FINAL_SYSTEM_READONLY_CHECK" if rc==0 and wrc==0 and watchdog=="Running" else "BLOCKED_FINAL_SYSTEM_READONLY_CHECK","remote_returncode":rc,"watchdog_returncode":wrc,"remote_read_only_output":text,"watchdog_state":watchdog,"mutations":{"training":0,"controller_rollout":0,"map_mutation":0,"method_mutation":0,"watchdog_modification":0}}
    (ROOT/"report/system_final_state.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    print(payload["status"])
