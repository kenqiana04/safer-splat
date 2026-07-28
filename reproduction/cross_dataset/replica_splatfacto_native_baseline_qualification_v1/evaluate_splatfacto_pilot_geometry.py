#!/usr/bin/env python3
"""Run the frozen common evaluator on the completed pilot; no early-stop logic."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from _common import PYTHON, ROOT, SPLATNAV_REPO, atomic_json, load_json, task_env, update_stage


def main():
    summary = load_json(ROOT / "qualification_pilot" / "splatfacto_pilot_summary.json")
    export = load_json(ROOT / "canonical_export" / "splatfacto_pilot_canonical_export_summary.json")
    path = ROOT / "common_evaluation" / "splatfacto_pilot_geometry_evaluation.json"
    if summary.get("status") != "SPLATFACTO_PILOT_COMPLETE" or not export.get("status", "").endswith("PASS"):
        atomic_json(path, {"status": "NOT_AUTHORIZED_DUE_TO_PILOT_OR_EXPORT"}); return
    process = subprocess.run([str(PYTHON), "-B", str(Path(__file__).resolve().with_name("evaluate_splatfacto_common_geometry.py")), "--stage", "qualification_pilot"], cwd=str(SPLATNAV_REPO), env=task_env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=1800)
    if process.returncode != 0:
        atomic_json(path, {"status": "SPLATFACTO_PILOT_RENDER_EXECUTION_FAILURE", "error": process.stdout[-8000:]})
        update_stage("PILOT_GEOMETRY", "FAILED_INFRASTRUCTURE", result_status="SPLATFACTO_PILOT_RENDER_EXECUTION_FAILURE")
        raise SystemExit(1)
    result = load_json(path)
    result["status"] = "SPLATFACTO_PILOT_GEOMETRY_EVALUATED"
    result["geometry_pass"] = bool(result["geometry_gate"]["pass"])
    result["common_evaluator_is_pr56_frozen_contract"] = True
    atomic_json(path, result)
    update_stage("PILOT_GEOMETRY", "TERMINAL_SCIENTIFIC_RESULT", result_status=result["status"], geometry_pass=result["geometry_pass"])
    print(result["status"])


if __name__ == "__main__": main()
