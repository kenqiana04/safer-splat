# TUM SplaTAM Direct-Safe Baseline Gate V1.1 Implementation Plan

**Goal:** Correct the camera universe and complete the bounded, original-SAFER-only gate without reusing pre-correction results.

**Architecture:** The task-owned core first freezes identities and writes all large raw records only to a new server root.  Compact V1.1 summaries are copied into this tracked directory; baseline children can run only from the pre-frozen compact registry.

**Tech stack:** Python 3, NumPy, PyTorch/CUDA, existing SAFER SplatAM map query and CBF modules, JSON, Git.

---

### Task 1: Freeze the corrected protocol

- [x] Preserve the V1 cardinality blocker and write the V1.1 correction record.
- [ ] Verify the 300 original-order transform positions and all frozen runtime identities in the new server root.
- [ ] Stop with `BLOCKED_BY_CORRECTED_CAMERA_UNIVERSE_IDENTITY_MISMATCH` if an identity differs.

### Task 2: Qualify geometry without reusing V1 results

- [ ] Re-query all 300 centers at radius 0.015 and retain complete rows only on the server.
- [ ] Build hash-ordered, correctly binned unordered pairs; execute only the bounded three-stage coarse screen.
- [ ] Densely screen at most 32 pairs, perform two independent float64 references, and freeze a four-pair registry only if the pair-pool gate passes.

### Task 3: Run and certify original baselines only when authorized by the gate

- [ ] Spawn at most four serial child processes from the frozen registry using the original CBF and frozen parameters.
- [ ] Float64-certify boundary-relevant states, determine the pre-registered viability decision, and verify no prohibited execution occurred.
- [ ] Write compact summaries, report, validation result, then make the single authorized commit, push, and Draft PR.
