# Retrospective Requalification Under Layered Protocol V2 Implementation Plan

> **For agentic workers:** Execute this plan inline in the current task. Do not delegate, retrain, tune, run a controller, or change frozen inputs.

**Goal:** Reclassify every existing Gaussian map under the immutable Layered Protocol V2 using control-first, read-only evidence and publish one auditable Draft PR.

**Architecture:** A tracked Python evidence pipeline freezes upstream identities, mirrors only compact server evidence, validates controls before candidates, and writes one normalized per-map evidence card. Independent scripts expose each required audit surface while a final classifier enforces the frozen R/N/query rules and decision tree. All large maps stay in authoritative server storage and are hashed before and after read-only evaluation.

**Tech Stack:** Python 3 standard library, NumPy/PyTorch where already installed on zlab-4090, Matplotlib, Git/GitHub CLI, SSH/SCP.

---

### Task 1: Freeze lineage and inputs

**Files:**
- Create: `freeze_protocol_v2_and_inputs.py`
- Create: `input_freeze/protocol_v2_input_freeze.json`
- Create: `map_inventory/requalification_map_inventory.json`

- [x] Verify PR #75 is Open Draft, unmerged, mergeable, and at `d1d3301076bec33868c52ff49e81857379038de1`.
- [x] Byte-verify Protocol V2, checklist, and PR #75 report SHA-256 values.
- [x] Reconcile the fixed eleven-map inventory with current server existence and artifact identity.
- [x] Record all unavailable artifacts without downloading or retraining.

Run:
```powershell
python -B freeze_protocol_v2_and_inputs.py --server zlab-4090
```

Expected: `PASS_PROTOCOL_V2_AND_INPUT_FREEZE` and eleven ordered map entries.

### Task 2: Validate positive and negative controls

**Files:**
- Create: `validate_control_maps.py`
- Create: `validate_map_integrity.py`
- Create: `control_validation/protocol_v2_control_discrimination.json`
- Create: `control_validation/positive_control_result.json`
- Create: `control_validation/negative_control_result.json`
- Create: `control_validation/control_failure_analysis.md`

- [x] Validate REPLICA_GT_FINE identity, deterministic construction certificate, R3/N3 route/oracle contract, explicit non-free unknown policy, and query compatibility.
- [x] Validate REPLICA_SPLATFACTO as an executable negative control and prevent a finite G0 result from raising its N axis.
- [x] Preserve TUM_SPLATFACTO_NEGATIVE as historical evidence when its artifact remains unavailable.
- [x] Stop candidate classification on either frozen control failure state.

Run:
```powershell
python -B validate_control_maps.py --input input_freeze/protocol_v2_input_freeze.json
```

Expected: `PASS_PROTOCOL_V2_CONTROL_DISCRIMINATION`.

### Task 3: Collect immutable per-map evidence

**Files:**
- Create: `evaluate_native_common_parity.py`
- Create: `evaluate_fixed_alpha_risk_coverage.py`
- Create: `evaluate_multi_tolerance_geometry.py`
- Create: `evaluate_unknown_missingness.py`
- Create: `evaluate_replica_route_tube.py`
- Create: `derive_route_physical_budget.py`
- Create: `validate_one_sided_distance_engine.py`
- Create: `evaluate_one_sided_route_risk.py`

- [x] Use the fixed candidate order REPLICA_SPLATAM_60, ARKITSCENES_M1_SPLATAM, TUM_SPLATAM_FORMAL, TUM_GAUSSIAN_SLAM.
- [x] Reuse frozen risk-coverage samples and only rerender when a required mask is absent and the map SHA remains unchanged.
- [x] Use fixed alpha `{0.05,0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.90,0.95}` and reporting tolerances `{0.01,0.02,0.03,0.05,0.10,0.20}`.
- [x] Record missing bidirectional samples, route contracts, references, unknown mechanisms, or physical allowances as unresolved rather than fabricating values.
- [x] Verify the exact anisotropic ellipsoid distance engine against at least 256 frozen samples whenever route distance evaluation is legal.

Run:
```powershell
python -B run_requalification.py --phase evidence
```

Expected: compact source-backed JSON/CSV records for every evaluable channel and explicit `NOT_EVALUABLE` records elsewhere.

### Task 4: Run read-only G0 and classify axes

**Files:**
- Create: `run_readonly_safer_g0.py`
- Create: `classify_protocol_v2_axes.py`
- Create: `select_requalification_decision.py`
- Create: `classification/classification_matrix.json`
- Create: `classification/allowed_forbidden_claims.json`

- [x] Run three fresh-process, 256-state G0 probes only for accessible maps with legal adapters, at most one GPU process at a time.
- [x] Validate finite h/gradient/Hessian, Hessian symmetry, active-index determinism, resource use, and map SHA immutability.
- [x] Assign only the frozen R0-R3, N0-N3, query, reference, unknown, and physical-budget enums.
- [x] Apply the frozen A/B/C/D decision tree without candidate-dependent thresholds.

Run:
```powershell
python -B run_requalification.py --phase classify
```

Expected: one classification card per map and exactly one final decision.

### Task 5: Build and validate the technical report

**Files:**
- Create: `generate_figures.py`
- Create: `build_report.py`
- Create: `validate_requalification.py`
- Create: `REPORT_RETROSPECTIVE_REQUALIFY_EXISTING_GAUSSIAN_MAPS_UNDER_LAYERED_PROTOCOL_V2.md`
- Create: `run_manifest.json`
- Create: `validation_result.json`
- Create: `downstream_handoff.json`

- [x] Generate the twenty preregistered PNG figures from compact evidence using measured/derived/empirical/unresolved/not-evaluable visual distinctions.
- [x] Write an answer-first technical report covering all 29 required questions, with limitations adjacent to claims.
- [x] Validate required files, enums, control discrimination, map identities, immutability, zero prohibited execution counts, figure readability, and decision-tree consistency.
- [x] Copy only the final `REPORT*.md` file to `C:\Users\zlab\Desktop\REPORT`.

Run:
```powershell
python -B run_requalification.py --phase finalize
python -B validate_requalification.py
```

Expected: final PASS/NO-QUALIFIED/BLOCKED status dictated only by the frozen tree and no unresolved critical validator fields.

### Task 6: Publish one bounded Draft PR

**Files:**
- Stage only: `reproduction/cross_dataset/retrospective_requalify_existing_gaussian_maps_protocol_v2/`

- [ ] Print and review the exact staged file list.
- [ ] Commit `test(reproduction): requalify existing maps under protocol v2` without amend.
- [ ] Push `retrospective-requalify-existing-gaussian-maps-protocol-v2` without force.
- [ ] Create exactly one Open Draft PR against `gaussian-map-metric-provenance-navigation-usability-calibration-v1`.

Run:
```powershell
git add reproduction/cross_dataset/retrospective_requalify_existing_gaussian_maps_protocol_v2
git diff --cached --name-only
git commit -m "test(reproduction): requalify existing maps under protocol v2"
git push -u origin retrospective-requalify-existing-gaussian-maps-protocol-v2
```

Expected: clean worktree, remote head equal to local commit, and one Draft PR.
