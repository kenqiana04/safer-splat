#!/usr/bin/env bash
set -euo pipefail
ROOT=/disk1/zlab/maintenance_records/core_v1_cross_environment_activation_portability_audit_v1
PYTHON=/disk1/zlab/conda_envs/safer_splat_official/bin/python
export CUDA_VISIBLE_DEVICES=1
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/disk1/zlab/runtime_overlays/tum_splatfacto_pkgresources_v1/setuptools_81_0_0
cd "$ROOT"
if test -e benchmark/formal_attempt.json; then
  echo FORMAL_ATTEMPT_ALREADY_EXISTS_NO_RETRY
  exit 40
fi
"$PYTHON" -B -c 'import json,pathlib,os; p=pathlib.Path("benchmark/formal_attempt.json"); v={"status":"FORMAL_ATTEMPT_STARTED","formal_attempt_count":1,"infrastructure_failure_count":0,"same_manifest_resume_count":0,"method_order":["B0_CURRENT_CBF_ONLY","B1_PLUS_SWEPT_SEGMENT","B2_PLUS_TERMINAL_BACKUP","B3_FULL_UNIFIED_WITH_DIRECTIONAL_ALTERNATIVES"],"environment_order":["E1_REPLICA_GT_FINE","E5_STONEHENGE_SAFER","E6_FLIGHT_SAFER"]}; t=p.with_suffix(".tmp"); t.write_text(json.dumps(v,sort_keys=True,indent=2)+"\n"); os.replace(t,p)'
"$PYTHON" -B benchmark/run_replica_one_step.py --mode formal
"$PYTHON" -B benchmark/run_paired_one_step.py --environment E5_STONEHENGE_SAFER --mode formal
"$PYTHON" -B benchmark/run_paired_one_step.py --environment E6_FLIGHT_SAFER --mode formal
"$PYTHON" -B -c 'import csv,json,pathlib,os,hashlib; root=pathlib.Path("."); inputs=[root/"runtime_work/formal"/f"{e}.csv" for e in ("E1_REPLICA_GT_FINE","E5_STONEHENGE_SAFER","E6_FLIGHT_SAFER")]; rows=[]; fields=[]; [(rows.extend(list(csv.DictReader(p.open(encoding="utf-8"))))) for p in inputs]; [(fields.extend(k for k in r if k not in fields)) for r in rows]; out=root/"benchmark/one_step_records.csv"; h=out.open("w",encoding="utf-8",newline=""); w=csv.DictWriter(h,fields,lineterminator="\n"); w.writeheader(); w.writerows(rows); h.close(); marker=json.loads((root/"benchmark/formal_attempt.json").read_text()); marker.update({"status":"FORMAL_ONE_STEP_COMPLETED","one_step_state_count":360,"one_step_method_record_count":len(rows),"output_sha256":hashlib.sha256(out.read_bytes()).hexdigest()}); tmp=root/"benchmark/formal_attempt.tmp"; tmp.write_text(json.dumps(marker,sort_keys=True,indent=2)+"\n"); os.replace(tmp,root/"benchmark/formal_attempt.json")'
echo PASS_SINGLE_FORMAL_ONE_STEP_ATTEMPT
