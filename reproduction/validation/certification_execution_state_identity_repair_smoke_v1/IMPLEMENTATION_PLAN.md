# Certification-execution identity repair smoke protocol freeze plan

This task freezes an engineering smoke protocol only. It does not execute a GPU preflight, controller/QP cycle, PlantCommit, trial, analyzer, Reference arm, Official100, or Formal arm.

1. Lock the exact implementation authority `546598a70e12fa99f9153f1927d0542ca27862b4`, repair specification, evidence locks, repaired runtime tree, canonical transition, stack factory, and Stonehenge map artifacts.
2. Freeze the development-exposed cohort `[15, 45, 75]`, fixed order, 500-cycle cap, serial isolated processes, seed 0, GPU1, and a fresh result root.
3. Implement a task-local future runner that delegates runtime work to the existing Active Runtime smoke harness while replacing only stack construction with `build_repaired_v3_stack`. Retain a parent-owned result root, identity-bound child authorization, no retry, and immutable early-failure evidence.
4. Add a CPU-only protocol validator and preflight covering the typed mismatch guard, child authorization, first-launch ordering, early-child failure persistence, trace-cardinality semantics, and summary continuity schema.
5. Run `py_compile`, `bash -n`, CPU preflight, validator, and `git diff --check`; verify result-root absence and zero protected diff.
6. Commit the protocol first, then add the execution lock in a second non-amended commit so the protocol-before-outcome identity remains auditable.
