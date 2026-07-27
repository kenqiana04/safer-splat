# TUM Navigation-Protocol Gap and CBF-Stall Geometry Audit V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Determine offline whether the saved TUM CBF stalls come from missing navigation semantics, invalid direct camera-center tasks, or local CBF deadlock geometry.

**Architecture:** Task-owned scripts read frozen PR47–PR50 evidence, full-map static geometry, and saved states only. They generate compact artifacts beneath the PR50 audit root; detailed samples stay on the server.

**Tech Stack:** Python, PyTorch CUDA static queries, NumPy, Matplotlib, Git, JSON.

---

### Task 1: Freeze identities and recover protocol evidence

**Files:**
- Create: `navigation_audit_core.py`
- Create: `recover_original_safer_navigation_stack.py`
- Create: `recover_tum_navigation_task_protocol.py`
- Create: `compare_navigation_protocols.py`

- [ ] **Step 1: Verify immutable inputs before map access**

```python
assert sha256(manifest_path) == "380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6"
assert state_counts == {"NOT_STARTED": 38, "TERMINAL_SCIENTIFIC_RESULT": 2}
assert frozen == {"radius": 0.015, "alpha": 5.0, "beta": 1.0, "dt": 0.05,
                  "max_steps": 800, "goal_tolerance": 0.001}
```

- [ ] **Step 2: Extract original stack facts only from source and history**

```python
original = {"start_goal_generator": "run.py circular antipodal configurations",
            "desired_controller": "clamped final-goal PD controller",
            "planner": False, "waypoint": False, "reference_trajectory": False,
            "classification": "DIRECT_GOAL_ONLY"}
```

- [ ] **Step 3: Recover TUM pair construction from frozen transforms**

```python
pairs = [(0, 50), (1, 51), (8, 58), (9, 59), (111, 287)]
for start_frame, goal_frame in pairs:
    start, goal = camera_center(transforms[start_frame]), camera_center(transforms[goal_frame])
```

- [ ] **Step 4: Run protocol recovery**

Run: `python -B recover_original_safer_navigation_stack.py && python -B recover_tum_navigation_task_protocol.py && python -B compare_navigation_protocols.py`

Expected: input identity, original stack, TUM task protocol, and field-by-field difference JSON files are written.

### Task 2: Audit static direct and camera-path geometry

**Files:**
- Create: `audit_direct_path_geometry.py`
- Create: `audit_camera_path_feasibility.py`
- Create: `direct_path_geometry_summary.json`
- Create: `camera_path_navigation_feasibility.json`

- [ ] **Step 1: Implement static full-map query with no solver or dynamics call**

```python
def static_query(point):
    h, grad, hess, info = gsplat.query_distance(torch.as_tensor(point, device=device),
        radius=0.015, distance_type="ball-to-ellipsoid")
    active = int(torch.argmin(h).item())
    return {"h": float(h[active]), "gradient": grad[active].cpu().tolist(),
            "active_gaussian": active, "closest_point": info["y"][active].cpu().tolist()}
```

- [ ] **Step 2: Sample direct lines at exactly 257 endpoint-inclusive values**

```python
for t in np.linspace(0.0, 1.0, 257):
    samples.append({"t": float(t), **static_query((1.0 - t) * start + t * goal)})
```

- [ ] **Step 3: Check every camera center and each adjacent segment endpoint/midpoint**

Run: `python -B audit_direct_path_geometry.py && python -B audit_camera_path_feasibility.py`

Expected: one direct-path and one camera-path classification for all five pairs without a new state update.

### Task 3: Analyze saved stall geometry and offline waypoint feasibility

**Files:**
- Create: `analyze_stall_geometry.py`
- Create: `analyze_local_cbf_feasible_directions.py`
- Create: `build_offline_waypoint_feasibility_graph.py`
- Create: `stall_geometry_attribution.json`
- Create: `local_cbf_feasible_direction_summary.json`
- Create: `waypoint_chain_feasibility.json`

- [ ] **Step 1: Select only fixed saved representative steps**

```python
requested = [stall_onset, stall_onset + 25, stall_onset + 100, minimum_distance_step, terminal_step]
representative_steps = [step for step in requested if step < saved_step_count]
```

- [ ] **Step 2: Compute goal/barrier alignment and static halfspace facts**

```python
goal_direction = normalize(goal - position)
barrier_outward = normalize(gradient)
alignment = float(np.dot(goal_direction, barrier_outward))
```

- [ ] **Step 3: Build camera-only forward waypoint graph**

```python
nodes = sorted(set([start_frame, goal_frame] + list(range(start_frame, goal_frame + 1, 5))))
edges = [(a, b) for a in nodes for b in nodes if a < b <= a + 25]
edge_safe = all(static_query((1.0 - t) * a + t * b)["h"] > 0.0 for t in np.linspace(0.0, 1.0, 33))
```

- [ ] **Step 4: Run static geometry analysis**

Run: `python -B analyze_stall_geometry.py && python -B analyze_local_cbf_feasible_directions.py && python -B build_offline_waypoint_feasibility_graph.py`

Expected: alignment, feasible-direction, and offline-chain artifacts; no call to `solve_QP`, Clarabel, dynamics propagation, or V4-C.

### Task 4: Classify, validate, report, and publish to PR #50

**Files:**
- Create: `classify_navigation_protocol_gap.py`
- Create: `render_navigation_protocol_figures.py`
- Create: `validate_and_report.py`
- Create: `navigation_protocol_classification.json`
- Create: `next_step_decision.json`
- Create: `validation_result.json`
- Create: `downstream_handoff.json`
- Create: `REPORT_TUM_NAVIGATION_PROTOCOL_GAP_AUDIT_V1.md`

- [ ] **Step 1: Emit exactly one CASE A–F primary classification and one non-executing decision**

```python
assert primary in {"TUM_NAVIGATION_PROTOCOL_GAP_MISSING_REFERENCE_LAYER",
                   "TUM_TASK_CONSTRUCTION_GAP_MISSING_PATH_FEASIBILITY",
                   "TUM_CAMERA_PAIR_NOT_VALID_DIRECT_NAVIGATION_TASK",
                   "TUM_LOCAL_CBF_DEADLOCK_UNDER_VALID_NAVIGATION_PROTOCOL",
                   "TUM_DIRECT_GOAL_STALL_WITH_OFFLINE_WAYPOINT_FEASIBILITY",
                   "BLOCKED_BY_TUM_NAVIGATION_PROTOCOL_UNRESOLVED"}
```

- [ ] **Step 2: Render raw labelled figures and validate no-execution invariants**

Run: `python -B render_navigation_protocol_figures.py && python -B validate_and_report.py`

Expected: `PASS_TUM_NAVIGATION_PROTOCOL_GAP_OFFLINE_AUDIT_WITH_<PRIMARY>` with zero rollout/QP/V4-C online counts.

- [ ] **Step 3: Publish only task-owned files**

```bash
git add reproduction/cross_dataset/tum_splatam_global_progress_limitation_audit_v1/navigation_protocol_gap_audit_v1
git commit -m "test(reproduction): audit TUM navigation protocol and CBF stall geometry"
git push origin tum-splatam-global-progress-limitation-audit-v1
```

## Self-review

- [ ] All direct samples use fixed 257-point grids; waypoint edges use fixed 33-point grids.
- [ ] No source PR47/48/49 or paused paired20 artifact is written, deleted, replaced, or resumed.
- [ ] Figures clearly label direct geometry, recorded camera motion, offline waypoint feasibility, and saved executed trajectories as distinct evidence classes.
