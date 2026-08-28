# Approved Instrumentation Delta

## Protected/forbidden gate result

`run.py` is present in the Core V2 authority manifest's supplemental protected evidence set. The accompanying policy says the baseline, map, controller, and historical evidence are read-only. Therefore direct Option A source modification is forbidden in this task.

## Approved production delta

`NONE_REQUIRED`

No production/controller file is modified. The approved implementation is the PR #96 fallback wrapper/decorator under this task-local directory. It temporarily decorates the already-imported `cbf.cbf_utils.CBF` factory when a future, separately authorized equivalence runner invokes it.

The single task-local observation hook has two decorator seams but one logical capture: the CBF wrapper delegates the frozen `solve_QP`, records only same-decision object identity integers plus an immutable `u_des` tuple, and returns the exact original output. The protected caller then executes its original `solver_success` guard. Entry to the temporarily decorated frozen plant function proves that guard passed; immediately before delegating the unchanged plant function, the hook creates the immutable state/selected-control snapshot and performs `put_nowait`. It does not copy the main loop, recompute the control, modify the success flag, alter the plant result, or add a controller gate.

Approved instrumentation hook count: 1.
