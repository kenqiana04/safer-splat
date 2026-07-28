# Replica Render Protocol V3 Coverage Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** qualify a new, pre-render Replica apartment_0 camera protocol solely from the frozen direct asset, original navmesh, independent CPU coverage, and fresh Habitat observations.

**Architecture:** the server-only pipeline freezes identity and a JSON contract before candidate generation, then derives every candidate pose from a seeded navmesh sample and hash-derived yaw.  A float64 CPU BVH provides independent coverage before fresh-process Habitat probes; only three-yaw locations passing both can enter deterministic spatial selection, split, manifest freeze, and repeatability checks.

**Tech Stack:** Python 3.9, Habitat-Sim 0.3.3, NumPy, task-owned C++17 float64 BVH, SHA-256, CSV/JSON, Matplotlib.

---

### Task 1: Freeze upstream identity and protocol contract

**Files:**
- Create: `freeze_replica_v3_input_identity.py`
- Create: `freeze_replica_v3_protocol_contract.py`
- Create: `upstream_replica_v3_identity.json`
- Create: `REPLICA_RENDER_PROTOCOL_V3_CONTRACT.json`

- [ ] Verify PR #53 head, mesh, navmesh, V1 manifest, and V1 staging tree against their frozen SHA-256 identities.
- [ ] Write the complete V3 contract and compute its SHA-256 before any `get_random_navigable_point()` call.
- [ ] Stop with `BLOCKED_BY_REPLICA_V3_INPUT_IDENTITY_MISMATCH` if any frozen identity differs.

### Task 2: Generate deterministic navmesh candidates and poses

**Files:**
- Create: `generate_replica_v3_navmesh_candidates.py`
- Create: `build_replica_v3_candidate_poses.py`
- Create: `raw_navmesh_candidate_summary.json`
- Create: `candidate_location_summary.json`
- Create: `candidate_pose_summary.json`

- [ ] Seed the original PathFinder with `20260728` and make exactly 2,048 calls.
- [ ] Retain only finite, navigable, snap-valid, in-bounds points; hash-sort and greedily deduplicate at 0.05 m, then cap at 1,024.
- [ ] Repeat generation in a fresh process and byte-compare positions and hashes.
- [ ] Derive all base yaws from location hashes and construct three finite V1-convention c2w poses per location.

### Task 3: Independently qualify direct-mesh geometry

**Files:**
- Create: `qualify_replica_v3_independent_coverage.py`
- Create: `independent_candidate_coverage_summary.json`

- [ ] Build exactly 41 x 31 pinhole rays for every candidate view and keep rows server-only.
- [ ] Run the PR #53 float64 BVH reference and independently brute-force at least eight center key rays spanning four pass and four fail locations.
- [ ] Require all three yaw views to pass the 0.10 near/far hit threshold for a location.

### Task 4: Habitat pre-render qualification and cross-validation

**Files:**
- Create: `run_replica_v3_habitat_preprobe.py`
- Create: `cross_validate_replica_v3_coverage.py`
- Create: `habitat_preprobe_summary.json`
- Create: `coverage_cross_validation_summary.json`
- Create: `qualified_location_pool_summary.json`

- [ ] Probe hash-ordered independent passes in stages 160, 240, then 320 only as necessary.
- [ ] Use a new OS subprocess and Simulator for each location, recording only compact RGB/depth metrics.
- [ ] Require each yaw to meet RGB nonzero >= 0.05 and depth positive >= 0.10.
- [ ] Stop before manifest freeze if unexplained independent-pass/Habitat-fail views exceed 5 percent.

### Task 5: Freeze spatial selection, split, and 300-frame manifest

**Files:**
- Create: `select_replica_v3_spatial_locations.py`
- Create: `build_replica_v3_location_split.py`
- Create: `freeze_replica_v3_manifest.py`
- Create: `selected_v3_location_registry.json`
- Create: `replica_v3_location_split.json`
- Create: `formal_camera_manifest_v3.csv`
- Create: `formal_camera_manifest_v3.json`
- Create: `transforms_v3.json`
- Create: `replica_protocol_v3_identity.json`

- [ ] Apply hash-tied farthest-point selection to 100 Habitat-qualified locations with 0.10 m minimum separation.
- [ ] Select ten eval locations by independent hash-tied farthest-point selection; retain each three-yaw location intact.
- [ ] Freeze the 300 rows and all content hashes without rendering an image.

### Task 6: Repeatability, validation, figures, report, and handoff

**Files:**
- Create: `run_replica_v3_repeatability_probe.py`
- Create: `validate_replica_v3_protocol.py`
- Create: `repeatability_probe_summary.json`
- Create: `validation_result.json`
- Create: `downstream_handoff.json`
- Create: `REPORT_REPLICA_RENDER_PROTOCOL_V3_QUALIFICATION.md`
- Create: `figures/*.png`

- [ ] Select thirty frozen manifest frames by repeatability hash and run A/B fresh-process observations without changing the manifest.
- [ ] Validate every gate, artifact format, count, boundary, and no-execution condition.
- [ ] Generate compact figures and the same report under the task-owned server root.
- [ ] Commit only this directory, push once, and open one Draft PR only after the terminal result is recorded.

## Scope check and self-review

The plan covers the contract-before-results rule, deterministic candidate generation, independent and Habitat qualification, spatial selection, split, manifest freeze, repeatability, reporting, and Git delivery. It intentionally excludes formal RGB-D rendering, dataset publication, Gaussian mapping/training, SAFER/CBF, and every TUM rollout. Each terminal blocker named by the protocol is produced only at its relevant gate; no threshold, seed, yaw, scene, mesh, or split is modified after the contract is frozen.
