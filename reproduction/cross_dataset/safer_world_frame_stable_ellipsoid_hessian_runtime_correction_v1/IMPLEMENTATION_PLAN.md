# SAFER World-Frame Stable Ellipsoid Hessian Runtime Correction V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute inline in this isolated worktree. Only `splat/distances.py`, `splat/gsplat_utils.py`, and this task root may change.

**Goal:** Apply the independently qualified stable, signed-local, world-frame Hessian correction while preserving every frozen h/gradient/projection behavior.

**Architecture:** Freeze pre-patch bytes, prove the required first-octant sign reflection against high-precision references, apply the two minimal core changes, then run staged synthetic, real-map, and 908-point static gates before classifying G0.

**Tech Stack:** PyTorch CUDA float32 runtime, NumPy float64 references, Git identity/diff gates, frozen canonical maps.

---

### Task 1: Freeze and prove sign reflection

- [ ] Record source blobs/ASTs and run RF0 versus RFR on fixed mixed-sign rotations.
- [ ] Stop if RFR does not meet the shared reference and HVP gates.

### Task 2: Apply minimal core patch

- [ ] Replace only the Hessian diagonal in `splat/distances.py` with `lam/(lam+s**2)`.
- [ ] Restore signed local coordinates and rotate Hessian to world in `splat/gsplat_utils.py`, preserving h, grad, y, phi, sorting, and root solve.

### Task 3: Staged regression

- [ ] Validate minimal source diff, exact forward regressions, sign-reflection, zero components, synthetic Hessian/HVP, and CBF algebra without executing CBF or dynamics.
- [ ] Only after those pass, run frozen real-map cases and full static 908 audits.

### Task 4: Contract and publication

- [ ] Freeze V2 only after both maps pass; classify G0; write compact evidence/report and copy only report to Desktop.
- [ ] Stage explicit allowed paths, commit, push, and open a Draft PR.
