# Gaussian-SLAM Resolution Adaptation Contract Audit V1 Implementation Plan

> **For agentic workers:** Execute this plan in the isolated audit worktree only. Every stage writes compact, atomic evidence and does not invoke Gaussian-SLAM mapping.

**Goal:** Recover the PR #56 Gaussian-SLAM failure semantics and determine whether a uniquely justified, non-core resolution adaptation rule exists for Replica V3.

**Architecture:** A task-owned driver performs ordered identity, archive/config, static-source, candidate-population, legality, and final-classification stages against the frozen server inputs. Thin named entry points expose each stage; all tracked results are compact copies of the authoritative server evidence.

**Tech Stack:** Python 3, NumPy, OpenCV, Matplotlib, JSON, CSV, SHA-256, read-only SSH access to the frozen Gaussian-SLAM archive and Replica V3 data.

---

### Task 1: Freeze inputs and prior-route decisions

**Files:**
- Create: `freeze_gaussian_slam_audit_input_identity.py`
- Create: `freeze_frontend_route_decisions.py`
- Test: `input_identity_summary.json`

- [ ] Recompute the published Replica V3 metadata and tree identities, inspect the frozen selection/order identity fields, and atomically record the pass/fail gate.
- [ ] Record the already-final Splatfacto and SplaTAM route decisions without changing their conclusions or execution counts.

### Task 2: Recover the frozen Gaussian-SLAM failure

**Files:**
- Create: `audit_gaussian_slam_frozen_assets.py`
- Create: `recover_pr56_gaussian_slam_failure.py`
- Create: `trace_gaussian_slam_resolution_call_graph.py`
- Test: `pr56_gaussian_slam_failure_evidence.json`

- [ ] Audit the archived source, environment, official config, task-generated config, and immutable PR #56 log.
- [ ] Extract the complete traceback and the exact no-replacement sampling call, then record short source-evidence hashes rather than copying source trees.

### Task 3: Audit resolution semantics without mapping

**Files:**
- Create: `audit_gaussian_slam_config_provenance.py`
- Create: `count_gaussian_slam_candidate_population.py`
- Create: `classify_gaussian_slam_failure_hypotheses.py`
- Test: `gaussian_slam_candidate_population_summary.json`

- [ ] Apply the frozen Replica loader/preprocessing contract to the 16 smoke and 60 pilot frame lists only.
- [ ] Construct the same per-image candidate representation, count population/masks, and never call a mapper, optimizer, renderer, or checkpoint writer.
- [ ] Compare the task resolution with the official Replica config and classify competing explanations before assessing any rule.

### Task 4: Gate adaptations and publish the audit result

**Files:**
- Create: `build_gaussian_slam_adaptation_legality_contract.py`
- Create: `validate_gaussian_slam_adaptation_without_training.py`
- Create: `freeze_gaussian_slam_resolution_adaptation.py`
- Create: `classify_gaussian_slam_resolution_audit.py`
- Test: `validation_result.json`

- [ ] Apply all fourteen legality conditions; if no unique legal rule exists, create explicit NOT_CREATED placeholders instead of an invented config.
- [ ] Generate validation, handoff, report, figures, and the stage manifest; compile all task Python files and parse every compact JSON.
- [ ] Stage only this task directory, commit once, push once, and create one Draft PR after all input gates pass.
