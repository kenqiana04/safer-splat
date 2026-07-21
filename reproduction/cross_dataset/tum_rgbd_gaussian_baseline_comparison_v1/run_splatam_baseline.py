"""Run one bounded SplaTAM stage from a newly-created task-owned output only."""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--python", type=Path, required=True); p.add_argument("--repo", type=Path, required=True); p.add_argument("--config", type=Path, required=True); p.add_argument("--output", type=Path, required=True); p.add_argument("--log", type=Path, required=True); a = p.parse_args()
    if a.output.exists():
        raise RuntimeError(f"SPLATAM_OUTPUT_MUST_BE_NEW:{a.output}")
    a.output.parent.mkdir(parents=True, exist_ok=True); a.log.parent.mkdir(parents=True, exist_ok=True)
    # The official offline entry evaluates its own input at shutdown.  It is
    # monkey-patched to a no-op here so the held-out evaluator is the sole metric producer.
    launcher = a.output.parent / "run_official_splatam_noeval.py"
    launcher.write_text("import runpy,sys\nfrom pathlib import Path\nrepo=Path(sys.argv[1]); cfg=sys.argv[2]\nsys.path.insert(0,str(repo))\nm=runpy.run_path(str(repo/'scripts'/'gaussian_splatting.py'),run_name='splatam_official')\nf=m['offline_splatting']; f.__globals__['eval']=lambda *args,**kwargs: None\nfrom importlib.machinery import SourceFileLoader\ne=SourceFileLoader('task_config',cfg).load_module()\nm['seed_everything'](seed=e.config['seed'])\nf(e.config)\n", encoding="utf-8")
    env = os.environ.copy(); env.update({"CUDA_VISIBLE_DEVICES": "1", "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    with a.log.open("w", encoding="utf-8") as log:
        result = subprocess.run([str(a.python), str(launcher), str(a.repo), str(a.config)], cwd=a.repo, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"SPLATAM_STAGE_FAILED:{result.returncode}")
    print("SPLATAM_STAGE_PASS")


if __name__ == "__main__": main()
