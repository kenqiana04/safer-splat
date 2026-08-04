#!/usr/bin/env bash
set -euo pipefail

TASK_ROOT=/disk1/zlab/maintenance_records/eth3d_delivery_area_provision_7zz_resume_assets_v1
AUDIT_PY=/disk1/zlab/conda_envs/safer_splat_official/bin/python
export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
cd "$TASK_ROOT"

phase() {
  local name=$1
  shift
  printf 'PHASE_START %s %s\n' "$name" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  "$@" >"logs/${name}.log" 2>&1
  printf 'PHASE_PASS %s %s\n' "$name" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}

phase license_boundary python3 install_license_boundary.py
phase nondata_contracts python3 freeze_nondata_contracts.py
phase split_three_fresh python3 verify_split_reproducibility.py
phase train_only_three_fresh python3 build_and_isolate_inputs.py
phase metric_reference "$AUDIT_PY" audit_reference_geometry.py
phase reference_prm "$AUDIT_PY" build_reference_prm.py
phase route_candidates "$AUDIT_PY" enumerate_reference_route_candidates.py
phase routes_three_fresh "$AUDIT_PY" verify_route_reproducibility.py

printf 'POST_EXTRACT_PIPELINE_PASS %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
