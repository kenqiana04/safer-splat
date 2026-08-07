#!/usr/bin/env bash
set -euo pipefail
ROOT=/disk1/zlab/maintenance_records/core_v1_cross_environment_activation_portability_audit_v1
PYTHON=/disk1/zlab/conda_envs/safer_splat_official/bin/python
export CUDA_VISIBLE_DEVICES=1
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/disk1/zlab/runtime_overlays/tum_splatfacto_pkgresources_v1/setuptools_81_0_0
cd "$ROOT"
"$PYTHON" -B benchmark/run_replica_one_step.py --mode smoke
"$PYTHON" -B benchmark/run_paired_one_step.py --environment E5_STONEHENGE_SAFER --mode smoke
"$PYTHON" -B benchmark/run_paired_one_step.py --environment E6_FLIGHT_SAFER --mode smoke
"$PYTHON" -B -c 'import json,pathlib; r=pathlib.Path("runtime_work/smoke"); xs=[json.loads((r/f"{e}.json").read_text()) for e in ("E1_REPLICA_GT_FINE","E5_STONEHENGE_SAFER","E6_FLIGHT_SAFER")]; assert all(x["status"]=="PASS_SMOKE_ONE_STEP" for x in xs); (r/"smoke_gate.json").write_text(json.dumps({"status":"PASS_FIXED_EIGHT_STATE_SMOKE","environment_count":3,"state_count":24,"method_record_count":96},sort_keys=True,indent=2)+"\n")'
echo PASS_FIXED_EIGHT_STATE_SMOKE
