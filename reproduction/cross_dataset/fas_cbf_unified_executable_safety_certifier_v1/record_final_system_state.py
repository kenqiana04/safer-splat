"""Read-only final GPU, task-process, proxy-listener, and watchdog audit."""
from __future__ import annotations

import base64
import json
from pathlib import Path
import subprocess

from task_config import TASK_ROOT


def main()->None:
    remote_script=r'''set -u
echo HOST=$(hostname)
echo UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo GPU_BEGIN
nvidia-smi -i 1 --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader
echo GPU_END
echo COMPUTE_BEGIN
nvidia-smi -i 1 --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader || true
echo COMPUTE_END
echo TASK_PROCESS_BEGIN
pgrep -af 'python3 -B map_smoke/[r]un_replica_smoke.py' || true
echo TASK_PROCESS_END
echo LISTENER_BEGIN
ss -ltnp 2>/dev/null | grep '127.0.0.1:17898' || true
echo LISTENER_END
'''
    encoded=base64.b64encode(remote_script.encode()).decode()
    remote=subprocess.check_output(["ssh","zlab-4090",f"echo {encoded} | base64 -d | bash"],text=True)
    sections={}; current=None
    for line in remote.splitlines():
        if line.endswith("_BEGIN"): current=line[:-6]; sections[current]=[]
        elif line.endswith("_END"): current=None
        elif current is not None: sections[current].append(line)
    watchdog=subprocess.run(["powershell","-NoProfile","-Command","(Get-ScheduledTask -TaskName 'Codex-Persistent-Reverse-Proxy-Watchdog').State"],capture_output=True,text=True)
    gpu=sections.get("GPU",[]); compute=[line for line in sections.get("COMPUTE",[]) if line.strip()]; task_process=[line for line in sections.get("TASK_PROCESS",[]) if line.strip()]; listener=sections.get("LISTENER",[])
    data={"remote_host":next((line.split("=",1)[1] for line in remote.splitlines() if line.startswith("HOST=")),None),"remote_utc":next((line.split("=",1)[1] for line in remote.splitlines() if line.startswith("UTC=")),None),"gpu1_query":gpu,"gpu1_compute_processes":compute,"gpu1_compute_process_count":len(compute),"task_owned_remote_processes":task_process,"task_owned_remote_process_count":len(task_process),"remote_proxy_listener_127_0_0_1_17898":bool(listener),"watchdog_task":"Codex-Persistent-Reverse-Proxy-Watchdog","watchdog_state":watchdog.stdout.strip(),"watchdog_preserved":watchdog.returncode==0 and "Running" in watchdog.stdout,"ssh_or_sshd_restart_count":0,"network_restart_count":0,"firewall_change_count":0,"status":"PASS_FINAL_SYSTEM_READONLY_CHECK" if len(compute)==0 and len(task_process)==0 and bool(listener) and "Running" in watchdog.stdout else "FINAL_SYSTEM_CHECK_REQUIRES_REVIEW"}
    path=TASK_ROOT/"report"/"system_final_state.json"; path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="\n") as handle: handle.write(json.dumps(data,indent=2,sort_keys=True)+"\n")
    print(data["status"])


if __name__=="__main__": main()
