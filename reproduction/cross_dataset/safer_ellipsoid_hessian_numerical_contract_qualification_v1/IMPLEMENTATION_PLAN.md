# SAFER Ellipsoid Hessian Numerical Contract Qualification V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute this plan inline in the isolated task worktree; no subagents or core-source changes are permitted.

**Goal:** Independently qualify the frozen ball-to-ellipsoid signed-squared-distance Hessian, or identify the precise runtime correction needed.

**Architecture:** Freeze PR #42 identities, evaluate independent float64 implicit-KKT and finite-difference world-frame references, compare the frozen runtime Hessian and two task-owned candidates under shared gates, then conditionally inspect real maps/static audit only if the official runtime passes.

**Tech Stack:** Python, NumPy float64, PyTorch CUDA float32, Git object export, read-only source and map inspection.

---

### Task 1: Freeze evidence and source semantics

- [ ] Export raw frozen source blobs and prior contract artifacts; verify PR #42 identity.
- [ ] Record the local/world-frame data flow and CBF 3x3-to-6x6 Hessian use without execution.

### Task 2: Independent synthetic references

- [ ] Build the fixed rotation-aware registry from the PR #42 4,096-case seed and separate edge registry.
- [ ] Implement float64 implicit-KKT and five-point envelope-gradient Hessian references, including HVP checks.

### Task 3: Runtime-candidate qualification

- [ ] Compare returned local-frame Hessian, task-owned rotated local candidate, and stable implicit 25-step candidate using the common preregistered gates.
- [ ] Diagnose frame and y/x stability before selecting one of CASE H-A through H-E.

### Task 4: Conditional follow-through and publication

- [ ] Run real-map/static work only if CASE H-A permits it; otherwise record the protocol stop.
- [ ] Produce compact evidence/report, copy only the report to Desktop, validate scope, commit, push, and open a Draft PR.
