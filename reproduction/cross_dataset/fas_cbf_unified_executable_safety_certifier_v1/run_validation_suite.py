"""Compile every Python source and run the full pytest suite."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import py_compile

from task_config import TASK_ROOT


def main()->None:
    env=dict(os.environ); env["PYTHONDONTWRITEBYTECODE"]="1"
    test_cmd=[sys.executable,"-B","-m","pytest","-q",str(TASK_ROOT/"tests"),"--disable-warnings"]
    compile_root=Path(tempfile.mkdtemp(prefix="fcbf_compile_"))
    compile_errors=[]
    source_files=sorted(TASK_ROOT.rglob("*.py"))
    try:
        for index, source in enumerate(source_files):
            try:
                py_compile.compile(
                    str(source),
                    cfile=str(compile_root/f"{index:04d}.pyc"),
                    doraise=True,
                )
            except py_compile.PyCompileError as exc:
                compile_errors.append(f"{source.relative_to(TASK_ROOT)}: {exc.msg}")
    finally:
        shutil.rmtree(compile_root,ignore_errors=True)
    tested=subprocess.run(test_cmd,capture_output=True,text=True,env=env)
    match=re.search(r"(\d+) passed",tested.stdout)
    evidence={"python":sys.version.split()[0],"syntax_compile":{"exit_code":1 if compile_errors else 0,"source_count":len(source_files),"errors":compile_errors,"temporary_outputs_removed":not compile_root.exists()},"pytest":{"exit_code":tested.returncode,"stdout":tested.stdout.strip(),"stderr":tested.stderr.strip(),"passed_count":int(match.group(1)) if match else None},"pycache_redirected_outside_repository":True}
    path=TASK_ROOT/"report"/"test_execution.json"; path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="\n") as handle: handle.write(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    if compile_errors or tested.returncode: raise SystemExit("VALIDATION_SUITE_FAILED")
    print("PASS_SYNTAX_COMPILE_AND_PYTEST",len(source_files),evidence["pytest"]["passed_count"])


if __name__=="__main__": main()
