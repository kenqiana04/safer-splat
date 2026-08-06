import json
from pathlib import Path
import os
import subprocess
import sys


def test_three_fresh_python_processes_produce_identical_sha():
    task_root = Path(__file__).resolve().parents[1]
    code = "from alternative_library.directional_library import build_directional_library; from alternative_library.canonical_serialization import canonical_sha256; import numpy as n; r=build_directional_library((1.,0.,0.),(-.02,0.,0.),(1.,2.,0.),'FINITE',(0,),n.array(((0.,0.,0.),))); print(canonical_sha256({'slots':[(s.candidate_id,s.availability.value,s.acceleration,s.duplicate_of) for s in r.slots]}))"
    environment = {**os.environ, "PYTHONPATH": str(task_root), "PYTHONHASHSEED": "random"}
    values = [subprocess.run([sys.executable, "-B", "-c", code], check=True, capture_output=True, text=True, env=environment).stdout.strip() for _ in range(3)]
    assert len(set(values)) == 1, json.dumps(values)
