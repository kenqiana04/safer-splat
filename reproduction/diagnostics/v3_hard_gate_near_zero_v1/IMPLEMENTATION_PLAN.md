# Implementation plan

This task is a post-failure, read-only diagnostic. It preserves the frozen `FAIL_V3_HARD_SAFETY_GATE` decision and does not modify runtime, controller, dynamics, map, paired protocol, or paired analyzer code.

1. Verify the exact `50cadfe614da70ce0345c4b1789c787dc529287e` start identity, frozen top-level evidence, four raw trial locks, source hashes, protocol hash, and map hashes.
2. Freeze the diagnostic rules, query script, and CPU validator in a pre-outcome commit. The fresh external result root must not exist at this point.
3. On GPU 1, load the frozen Stonehenge map read-only. Reconstruct committed state chains exactly as the frozen analyzer does and call the frozen segment evaluator at `0.015 q` to locate exactly one violating segment per trial.
4. For only those four segments, run the fixed 1025-point dense scan, four deterministic 65-point refinement layers, 20-repeat audits, seven-point one-ULP audits, and an independent equivalent float64 audit if the math-equivalence gate passes.
5. Align the violating committed row to runtime trace evidence. Keep trial-level backup/boundary counts separate from segment-level action attribution.
6. Write only compact summaries and locks to Git; retain dense CSVs under the external result root. Revalidate byte preservation and protected-source zero diff before the evidence commit and Draft PR.

No result-dependent protocol change is permitted. A Phase B script defect ends this protocol revision rather than being silently patched.
