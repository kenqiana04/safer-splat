# Formal TUM Splatfacto Training Execution V1R6 Implementation Plan

> **For agentic workers:** Execute this plan in order. Do not retry after a real `ns-train` attempt exits.

**Goal:** Launch one V1R6 formal TUM FR1 Room Splatfacto attempt using the qualified precompiled gsplat overlay.

**Architecture:** Freeze V1R6 identity and command bytes in this directory, verify the inherited protocol and runtime on the authoritative server, then create one task-owned execution record and launch once. Evidence is written under the V1R6 execution-record root, never into the frozen V1R5 or V1R4 records.

**Tech Stack:** Bash, Python 3.10, Nerfstudio 1.1.5, PyTorch 2.1.2+cu118, gsplat 1.4.0+pt21cu118.

---

### Task 1: Freeze identity and launcher

**Files:**
- Create: `V1R6_RUN_IDENTITY.json`
- Create: `v1r6_exact_training_command.sh`

- [x] Set the new V1R6 timestamp, output identity, and task-owned record root.
- [x] Keep all 71 `ns-train` tokens except V1R6 experiment name and timestamp.
- [x] Place the qualified precompiled gsplat overlay before the existing setuptools overlay.

### Task 2: Preflight and one launch

**Files:**
- Create: `V1R6_EXECUTION_AUTHORIZATION.md`
- Create: `validate_v1r6_static.py`

- [x] Verify command bytes, identity JSON, overlay provenance, GPU 1 idle state, frozen config, data split, and absent V1R6 output.
- [x] Create a Draft PR before server checkout and launch.
- [x] Launch exactly once after all preflight checks pass; do not resume or retry after a real attempt failure.
