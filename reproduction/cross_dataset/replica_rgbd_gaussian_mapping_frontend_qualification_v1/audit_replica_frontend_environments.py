#!/usr/bin/env python3
"""Import-only/CUDA-extension audit using pre-existing frontend environments."""
from __future__ import annotations

import json
from pathlib import Path

from _common import FRONTENDS, ROOT, atomic_json, ensure_dirs, run_capture, update_stage


def probe(name: str) -> dict:
    item = FRONTENDS[name]
    modules = ["torch", "cv2", "open3d", "wandb"]
    if name == "splatam":
        modules += ["natsort", "diff_gaussian_rasterization", "datasets.gradslam_datasets.replica", "scripts.gaussian_splatting"]
    else:
        modules += ["simple_knn", "src.entities.datasets", "src.entities.tracker", "src.entities.gaussian_slam", "src.utils.io_utils"]
    code = "import importlib,json,sys,traceback; sys.path.insert(0," + repr(str(item["repo"])) + "); out={'modules':{}}\n" + "\nfor n in " + repr(modules) + ":\n try:\n  m=importlib.import_module(n);out['modules'][n]={'ok':True,'file':getattr(m,'__file__',None)}\n except Exception as e: out['modules'][n]={'ok':False,'error':type(e).__name__+':'+str(e)}\n" + "\nimport torch; out['runtime']={'python':sys.version.split()[0],'torch':torch.__version__,'cuda':torch.version.cuda,'cuda_available':torch.cuda.is_available(),'device_count':torch.cuda.device_count()};print(json.dumps(out,sort_keys=True))"
    result = run_capture([str(item["python"]), "-c", code], cwd=item["repo"], timeout=180)
    payload = json.loads(result["stdout"].splitlines()[-1]) if result["returncode"] == 0 and result["stdout"].splitlines() else {"modules": {}, "parse_error": result}
    ready = bool(payload.get("runtime", {}).get("cuda_available")) and all(value.get("ok") for value in payload.get("modules", {}).values())
    return {"frontend": item["display"], "environment": str(item["python"].parent.parent), "environment_python": str(item["python"]), "status": "FRONTEND_ENVIRONMENT_READY" if ready else "FRONTEND_ENVIRONMENT_UNAVAILABLE", "import_smoke": payload, "command": result, "repair_count": 0, "expected_gpu_index": 0, "physical_gpu": 1}


def main() -> None:
    ensure_dirs(); values = {name: probe(name) for name in FRONTENDS}
    output = {"frontends": values, "status": "PASS" if all(value["status"] == "FRONTEND_ENVIRONMENT_READY" for value in values.values()) else "PARTIAL_ENVIRONMENT_UNAVAILABLE"}
    atomic_json(ROOT / "environment_audit" / "frontend_environment_audit.json", output)
    for name, value in values.items():
        state = "TERMINAL_SCIENTIFIC_RESULT" if value["status"] == "FRONTEND_ENVIRONMENT_READY" else "FAILED_INFRASTRUCTURE"
        update_stage(name, "ENVIRONMENT_AUDIT", state, environment_status=value["status"])
    print(output["status"])


if __name__ == "__main__":
    main()
