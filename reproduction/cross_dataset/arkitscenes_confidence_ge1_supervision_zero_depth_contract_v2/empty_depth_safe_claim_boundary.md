# Empty-Depth-Safe Claim Boundary

The task-owned compatibility layer is qualified only for the frozen M1 supervision contract and the bounded synthetic/forward-only tests in this task. It does not make official SplaTAM natively empty-depth safe, and a future mapper using it must be named a SplaTAM-derived GT-pose map-only compatibility variant rather than an official unmodified baseline.

PR #72's formal failure remains valid. No mapper loop, optimizer, real backward, parameter update, smoke, training, checkpoint, learned map, NVS, clearance, G0, SAFER, FAS-CBF, or controller benchmark was executed. Frames 76 and 79 remain in canonical order and cannot be deleted or replaced. M0/M2 cannot be substituted for M1.
