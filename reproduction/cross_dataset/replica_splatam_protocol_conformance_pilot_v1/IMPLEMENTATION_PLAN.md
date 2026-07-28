# Replica SplaTAM Protocol-Conformance Pilot V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Audit the frozen PR #56 SplaTAM evidence and, only after all identity and operational gates pass, execute one immutable 60/30 Replica GT-pose map-only pilot and static SAFER G0 qualification.

**Architecture:** Task-owned wrappers consume the existing PR #56 registry, launcher, exporter, evaluator, and G0 adapter without changing baseline code. Raw outputs stay only under the 4090 maintenance root; compact JSON, figures, and report evidence are tracked here. Every gate emits a terminal status so a non-authorized pilot cannot start.

**Tech Stack:** Python 3, Bash, SSH to zlab-4090, SplaTAM official archive, PyTorch/CUDA GPU 1, NumPy/Matplotlib, Git/GitHub CLI.

---

## File structure

- `REPLICA_SPLATAM_PROTOCOL_CONFORMANCE_PILOT_V1.md`: frozen scope, inputs, gates, and prohibitions.
- `freeze_*`, `audit_*`, `bind_*`: identity, historical evidence, environment, and evaluator gates.
- `run_splatam_60_frame_pilot.py`: guarded one-science-run wrapper delegating to PR #56's frozen runner.
- `export_*`, `evaluate_*`, `qualify_*`, `classify_*`: post-run evidence stages.
- `*.json`, `figures/*.png`, `REPORT_*.md`: compact tracked evidence; checkpoints, render arrays, CUDA cache, and complete logs remain on server.

### Task 1: Establish immutable Git and protocol identity

**Files:**
- Create: `reproduction/cross_dataset/replica_splatam_protocol_conformance_pilot_v1/REPLICA_SPLATAM_PROTOCOL_CONFORMANCE_PILOT_V1.md`
- Create: `reproduction/cross_dataset/replica_splatam_protocol_conformance_pilot_v1/SPLATFACTO_ROUTE_CLOSURE_DECISION.json`

- [ ] **Step 1: Verify the upstream Draft PR head.**

Run:
```bash
gh pr view 57 --repo kenqiana04/safer-splat --json headRefOid,headRefName,state,isDraft
```
Expected: open Draft branch `replica-splatfacto-native-baseline-qualification-v1` at recorded head `9501da9c4956c4be48ae474d01cf4d6038304e6b`.

- [ ] **Step 2: Freeze the Splatfacto route closure with zero execution counts.**

The JSON must set `decision=CLOSE_SPLATFACTO_NAVIGATION_MAP_ROUTE`, `retained_role=SAFER_NATIVE_COMPATIBILITY_AND_NEGATIVE_GEOMETRY_BASELINE`, and training/render/G0 counts to zero.

- [ ] **Step 3: Compile tracked scripts after Tasks 2–7.**

Run:
```bash
python -B -m py_compile reproduction/cross_dataset/replica_splatam_protocol_conformance_pilot_v1/*.py
```
Expected: exit code 0.

### Task 2: Bind the input, PR #56, and environment evidence

**Files:**
- Create: `freeze_replica_splatam_input_identity.py`
- Create: `audit_pr56_splatam_protocol_conformance.py`
- Create: `audit_existing_splatam_smoke_operational_evidence.py`
- Create: `audit_splatam_environment.py`
- Create: `input_identity_summary.json`
- Create: `PR56_SPLATAM_PROTOCOL_CONFORMANCE_AUDIT.json`
- Create: `splatam_existing_smoke_operational_audit.json`
- Create: `splatam_environment_audit.json`

- [ ] **Step 1: Hash Replica V3 tree, manifests, pose array, RGB/depth pairing, and split.**

Run on zlab-4090:
```bash
python -B freeze_replica_splatam_input_identity.py --root /disk1/zlab/maintenance_records/replica_splatam_protocol_conformance_pilot_v1
```
Expected: prescribed six SHA-256 values and 300/270/30 contract; otherwise `BLOCKED_BY_SPLATAM_REPLICA_INPUT_IDENTITY_MISMATCH` with no runner invocation.

- [ ] **Step 2: Audit PR #56 without retraining the smoke.**

Run:
```bash
python -B audit_pr56_splatam_protocol_conformance.py --pr56-root /disk1/zlab/maintenance_records/replica_rgbd_gaussian_mapping_frontend_qualification_v1
```
Expected: classify real renderer exception versus geometry-gate misclassification while leaving historical artifacts unchanged.

- [ ] **Step 3: Reload/export/render only existing smoke evidence.**

Run:
```bash
python -B audit_existing_splatam_smoke_operational_evidence.py --mode reload-render-only
```
Expected: checkpoint checksum, finite canonical arrays, positive scales, 8/8 holdouts, zero tracking/pose updates, zero nonfinite predictions; otherwise `SPLATAM_EXISTING_SMOKE_EVIDENCE_NOT_RECOVERABLE`.

- [ ] **Step 4: Audit exact archive and environment without mutations.**

Run:
```bash
python -B audit_splatam_environment.py --no-package-mutation
```
Expected: Python, PyTorch, CUDA, extension, loader/exporter/renderer evidence and archive commit `da6bbcd24c248dc884ac7f49d62e91b841b26ccc`.

### Task 3: Freeze and regress the executable pilot contract

**Files:**
- Create: `freeze_splatam_60_frame_pilot_contract.py`
- Create: `bind_splatam_common_evaluator.py`
- Create: `splatam_60_frame_pilot_contract.json`
- Create: `splatam_common_evaluator_binding.json`

- [ ] **Step 1: Recover the PR #56 frozen configuration; never hand-assemble it.**

Run:
```bash
python -B freeze_splatam_60_frame_pilot_contract.py --pr56-root /disk1/zlab/maintenance_records/replica_rgbd_gaussian_mapping_frontend_qualification_v1
```
Expected: selection SHA `1beaacaeb8a4126ff4410aae0b296702a7b84dfaee402e15d90d4f5d70741d19`, ingestion SHA `d3dc24d673c97700dc340785425abf8482827c0c81b72a6b33e6972b361c2fb1`, 60 map/30 holdout, GT-pose map-only, tracking/pose optimization off, official eval 0. Ambiguity blocks execution.

- [ ] **Step 2: Bind and regress the common evaluator.**

Run:
```bash
python -B bind_splatam_common_evaluator.py --regression-tolerance 1e-9
```
Expected: PR #56 smoke coverage, AbsRel, delta1, and median ratio reproduce within `1e-9`; otherwise `BLOCKED_BY_SPLATAM_COMMON_EVALUATOR_IDENTITY_MISMATCH`.

### Task 4: Execute one guarded 60/30 map-only pilot

**Files:**
- Create: `run_splatam_60_frame_pilot.py`
- Create: `run_manifest.json`
- Create: `splatam_60_frame_pilot_summary.json`

- [ ] **Step 1: Enforce all authorization predicates before GPU use.**

Run:
```bash
CUDA_VISIBLE_DEVICES=1 python -B run_splatam_60_frame_pilot.py --preflight-only
```
Expected: no scientific run before all prior gates pass.

- [ ] **Step 2: Start exactly one science run.**

Run:
```bash
CUDA_VISIBLE_DEVICES=1 timeout 7200s python -B run_splatam_60_frame_pilot.py --execute-once
```
Expected: one 60-frame GT-pose map-only, 30-holdout run. A single fresh-output retry is allowed only for path/permission/environment/cache infrastructure failure, never for geometry/loss/map quality.

- [ ] **Step 3: Record a prescribed terminal status.**

Expected: one `SPLATAM_60_FRAME_PILOT_*` status with runtime, GPU peak, ingestion order, losses, Gaussian count, and zero-count prohibited mechanisms.

### Task 5: Export and evaluate without altering the map

**Files:**
- Create: `export_splatam_60_frame_canonical_map.py`
- Create: `evaluate_splatam_60_frame_geometry.py`
- Create: `audit_splatam_60_frame_map_structure.py`
- Create: `splatam_60_frame_canonical_export_summary.json`
- Create: `splatam_60_frame_geometry_evaluation.json`
- Create: `splatam_60_frame_map_structure_audit.json`

- [ ] **Step 1: Export unfiltered canonical arrays after a complete pilot.**

Run:
```bash
python -B export_splatam_60_frame_canonical_map.py --unfiltered
```
Expected: finite arrays, positive scales, positive-definite covariance, meter-frame metadata, and no filtering, pruning, downsampling, or reoptimization.

- [ ] **Step 2: Evaluate only 30 frozen holdouts with official eval count zero.**

Run:
```bash
python -B evaluate_splatam_60_frame_geometry.py --holdouts 30 --official-eval 0
```
Expected: per-frame and aggregate depth/RGB metrics, worst five frames, frozen thresholds, and no changed gates.

- [ ] **Step 3: Audit structural and scale evidence.**

Run:
```bash
python -B audit_splatam_60_frame_map_structure.py --no-scale-fit --no-sim3 --no-icp
```
Expected: finite distribution, bounds, covariance evidence and zero scale fitting, Sim3, ICP, tracking, pose optimization.

### Task 6: Run static G0 only when map export is qualified

**Files:**
- Create: `qualify_splatam_60_frame_safer_g0.py`
- Create: `splatam_60_frame_safer_g0_summary.json`

- [ ] **Step 1: Pin SAFER and run three identical static queries.**

Run:
```bash
python -B qualify_splatam_60_frame_safer_g0.py --query-id REPLICA_FRONTEND_SAFER_G0_V1 --radius-m 0.015 --repetitions 3
```
Expected: prescribed head/blobs, finite h/gradient/Hessian, relative Hessian symmetry at most `1e-5`, repeatable active Gaussian, no map mutation, no OOM.

- [ ] **Step 2: Prove no controller or navigation ran.**

Expected: summary has zero navigation, CBF-QP, Start-Safe, Risk-Aware, Recovery/V4-C, TUM, and Gaussian-SLAM counts.

### Task 7: Classify, validate, package, and publish exactly one Draft PR

**Files:**
- Create: `classify_splatam_replica_pilot.py`
- Create: `splatam_replica_pilot_result.json`
- Create: `validation_result.json`
- Create: `downstream_handoff.json`
- Create: `REPORT_REPLICA_SPLATAM_PROTOCOL_CONFORMANCE_PILOT_V1.md`
- Create: 14 required `figures/*.png` named in the frozen protocol.

- [ ] **Step 1: Compute exactly one final status and one next task.**

Run:
```bash
python -B classify_splatam_replica_pilot.py --validate-all
```
Expected: one prescribed result branch; never a claim that full mapping or navigation occurred.

- [ ] **Step 2: Validate every compact artifact.**

Run:
```bash
python -B -m py_compile reproduction/cross_dataset/replica_splatam_protocol_conformance_pilot_v1/*.py
python -B -c "import json,pathlib; [json.loads(p.read_text(encoding='utf-8')) for p in pathlib.Path('reproduction/cross_dataset/replica_splatam_protocol_conformance_pilot_v1').glob('*.json')]; print('JSON_PASS')"
```
Expected: exit 0 and `JSON_PASS`.

- [ ] **Step 3: Commit only the task directory and publish one Draft PR.**

Run:
```bash
git add reproduction/cross_dataset/replica_splatam_protocol_conformance_pilot_v1
git commit -m "test(reproduction): qualify Replica SplaTAM 60-frame pilot"
git push origin replica-splatam-protocol-conformance-pilot-v1
gh pr create --draft --base replica-splatfacto-native-baseline-qualification-v1 --head replica-splatam-protocol-conformance-pilot-v1 --title "[Draft] Audit and qualify Replica SplaTAM 60-frame pilot"
```
Expected: one non-amended commit, ordinary push, and one open Draft PR.

## Self-review

- All fixed hashes, Splatfacto closure, server-only raw artifacts, and TUM boundary are represented.
- A missing smoke checkpoint, identity conflict, or evaluator mismatch is terminal and cannot be bypassed by retraining.
- The only scientific execution is one serial 60/30 GPU-1 pilot capped at 120 minutes; no scientific retry is possible.
- No task runs 270-frame mapping, official evaluation, Gaussian-SLAM, navigation, CBF-QP, TUM, scale fitting, Sim3, ICP, tracking, or pose optimization.
