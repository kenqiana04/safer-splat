# Certification–Execution State Identity Repair Engineering Pilot V1

This directory freezes an engineering pilot protocol and a future execution harness. The freeze task does **not** create the pilot result root, run GPU code, launch tmux, execute a trial, or perform scientific analysis.

The sole upstream runtime is R6 commit `601204bfc14e3ad2c8e3c714b8f5045829491635`. The sole upstream smoke authority is the immutable retry5 root named in `PILOT_PROTOCOL.json`; its complete 30-file path/size/SHA256 inventory is `UPSTREAM_SMOKE_EVIDENCE_MANIFEST.json`. The harness reuses the R6 smoke runner's delegate projection, child authorization, observation tap, and executed-action-bound continuity audit without changing runtime source. Its own trial acceptance and aggregation enforce the pilot schema and non-500-specific denominator.

The frozen order is `[5,15,25,35,45,55,65,75,85,95]`, seed 0, at most 500 completed cycles per trial, serial and separate-process, no automatic retry. This is a reused, outcome-exposed engineering cohort, **not** a scientific holdout. Deadline WARNING/EXPIRED and L3 FAIL are recorded as engineering facts, not automatic pilot failures; only frozen integrity/identity/evidence gates decide pilot PASS.

When independently authorized later, a reviewer first verifies the execution lock and runs `bash launch_cert_exec_identity_repair_pilot_v1.sh --prelaunch-check-only`. This task does not invoke the launch mode. A partial or failed trial remains in place for manual audit; the batch never automatically reruns it. PASS would only authorize a new post-repair paired scientific validation **protocol freeze**, not scientific execution.

No collision/progress/noninferiority, parameter-selection, hard-real-time, or deployment claim follows from this pilot. Historical V3 remains `FAIL_V3_HARD_SAFETY_GATE`; the old result must not be rewritten.
