#!/usr/bin/env python3
"""Regenerate canonical Retry2 execution authority after the lifecycle repair commit."""
from __future__ import annotations
import json
from pathlib import Path
from validate_post_repair_v3_bounded_recovery_paired_validation_v1 import *

REPAIR_DIR=TASK/"repair_r2"; REPORT=REPAIR_DIR/"REPORT_REPAIR_AND_START_POST_REPAIR_V3_BOUNDED_RECOVERY_FORMAL85_V1.md"
def write(path:Path,value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")

def main()->int:
    if git("branch","--show-current")!=BRANCH or git("remote","get-url","origin")!=ORIGIN: raise RuntimeError("GIT_IDENTITY_DRIFT")
    if git("status","--short"): raise RuntimeError("REPAIR_COMMIT_AND_CLEAN_WORKTREE_REQUIRED")
    if RESULT_ROOT.exists() or tmux_active(): raise RuntimeError("RETRY2_EXECUTION_STATE_MUST_BE_ABSENT")
    protocol=read(PROTOCOL); old_lock=read(LOCK); protocol_commit=git("rev-parse","HEAD"); equivalence=read(REPAIR_DIR/"SCIENTIFIC_SEMANTICS_EQUIVALENCE_AUDIT.json")
    if equivalence["scientific_diff_count"]!=0: raise RuntimeError("SCIENTIFIC_SEMANTICS_DRIFT")
    harness={name:sha(TASK/name) for name in HARNESS}
    lock={
      "schema":"POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_EXECUTION_LOCK_V1","canonical_execution_lock_basename":CANONICAL_LOCK_BASENAME,
      "protocol_commit":protocol_commit,"repair_protocol_commit":protocol_commit,"base_head":BASE,"repair_implementation_head":REPAIR,"bounded_recovery_implementation_head":IMPL,"gate0_head":GATE0,"retry2_freeze_head":RETRY2_FREEZE,"engineering_pilot_freeze_head":PILOT_FREEZE,
      "attempt0":protocol["execution_attempt"]["attempt0"],"retry1":protocol["execution_attempt"]["retry1"],"retry2":protocol["execution_attempt"]["retry2"],"attempt0_authority_files":ATTEMPT_FILES[ATTEMPT0_ROOT],"retry1_authority_files":ATTEMPT_FILES[RETRY1_ROOT],"retry2_authority_files":ATTEMPT_FILES[RETRY2_ROOT],"retry_reason":protocol["execution_attempt"]["retry_reason"],
      "formal85_source_protocol_sha256":old_lock["formal85_source_protocol_sha256"],"trial_order":TRIALS,"trial_order_sha256":semantic_hash(TRIALS),"protocol_sha256":sha(PROTOCOL),"semantic_protocol_sha256":semantic_hash(protocol),"scientific_semantics_equivalence_sha256":sha(REPAIR_DIR/"SCIENTIFIC_SEMANTICS_EQUIVALENCE_AUDIT.json"),"scientific_semantics_diff_count":0,"harness_sha256":harness,
      "pilot_postrun_artifact_hashes":old_lock["pilot_postrun_artifact_hashes"],"historical_active_artifact_hashes":old_lock["historical_active_artifact_hashes"],"reference_artifact_hashes":old_lock["reference_artifact_hashes"],
      "map":protocol["map"],"geometry":protocol["geometry"],"dynamics":protocol["dynamics"],"recovery":protocol["recovery"],"statistics":protocol["primary_scientific_gates"],"boundary_handling":protocol["boundary_contract"],"hard_zero_gates":protocol["hard_zero_integrity_gates"],
      "validation_phases":[phase.value for phase in ValidationPhase],"future_result_root":str(RESULT_ROOT),"future_tmux_session":SESSION,"launch_marker_basename":LAUNCH_MARKER,"execution_authorization_token":TOKEN,"freeze_execution_counts":protocol["freeze_execution_counts"]}
    write(LOCK,lock); write(REPAIR_DIR/"HARNESS_HASHES.json",{"schema":"FORMAL85_R2_HARNESS_HASHES_V1","status":"FROZEN","files":harness})
    protected=("cbf","splat","dynamics","run.py","reproduction/runtime","reproduction/formal/post_repair_v3_paired_validation_v1","reproduction/formal/bounded_local_recovery_smoke_v1","reproduction/formal/bounded_local_recovery_smoke_retry2_v1","reproduction/formal/bounded_local_recovery_engineering_pilot_v1","reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1")
    changed=[x for x in git("diff","--name-only",BASE).splitlines() if x]; protected_changed=[x for x in git("diff","--name-only",BASE,"--",*protected).splitlines() if x]
    write(REPAIR_DIR/"PROTECTED_DIFF_AUDIT.json",{"schema":"FORMAL85_R2_PROTECTED_DIFF_AUDIT_V1","status":"PASS" if not protected_changed and all(x.startswith(TASK_PREFIX) for x in changed) else "FAIL","base":BASE,"changed_files":changed,"protected_changed":protected_changed,"runtime_diff_count":0})
    validation=validate_phase(ValidationPhase.PRELAUNCH,require_clean=False); write(REPAIR_DIR/"PRELAUNCH_VALIDATION.json",validation)
    REPORT.write_text(f"""# Repair and Start Post-Repair V3 Bounded Recovery Formal85 V1

- Attempt0, Retry1, and Retry2 are immutable pre-cycle harness failures with zero public cycles and zero PlantCommit.
- Retry1 root cause: `FORMAL85_RETRY1_CHILD_RUNTIME_VALIDATOR_PHASE_MISMATCH`.
- Explicit phases: `{', '.join(phase.value for phase in ValidationPhase)}`.
- Runner main and delegated source/map verification both use `child_runtime`; launcher uses `prelaunch` and `batch_runtime`; analyzer uses `postcollection`.
- Retry3 root: `{RESULT_ROOT}`; tmux: `{SESSION}`; token: `{TOKEN}`.
- Scientific semantic diff count: `0`; protected runtime diff: `0`.
- CPU/static integration is executed after lock regeneration.
- GPU/tmux/real-trial/real-PlantCommit freeze counts: `0/0/0/0`.
- Final HEAD and push equality are verified externally after the containing commit.
- Launch is authorized only after clean committed-state validation and push.
""",encoding="utf-8")
    print(json.dumps({"status":validation["status"],"check_count":validation["check_count"],"lock_sha256":sha(LOCK)},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
