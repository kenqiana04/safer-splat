# Equivalence protocol

## Frozen authority

- Repository: `kenqiana04/safer-splat`
- Upstream PR: `#97`, Open Draft
- Head: `7d48bf6c3b8932aa65d851c3cd70404404453cb3`
- Protected runtime: immutable `run.py`, controller, dynamics, map, candidate selection, certifier, and PR #97 instrumentation.

## Trial selection

Stable-sort the 100 rows by integer `trial`, then select zero-based positions

`floor(j * (N - 1) / (K - 1))` for `j=0..K-1`, `N=100`, `K=5`.

This yields trials `0, 24, 49, 74, 99`. Trial `0` is the self-consistency anchor. No selected trial may be replaced.

## Run order and stop rules

1. A1, A2; compare immediately.
2. B1, B2; compare immediately.
3. C1, C2; validate full activation and compare immediately.
4. For each frozen QA trial in ascending order, run A, B, C and compare A/B, B/C, A/C.

Every run uses a fresh process and physical GPU 1. Normal maximum is 21 real QA navigation runs. Native self-inconsistency, an activation-invalid C run after its single allowed same-trial retry, a pairing mismatch, or a legitimate first semantic divergence triggers the protocol-defined early stop.

## Runtime selection without controller mutation

`run.py` has no single-trial argument. The task-local runner temporarily intercepts only the `zip(x0, xf)` call made from the exact `run.py` trial-loop line and returns the already-computed preregistered array row. Every other `zip` call delegates unchanged. The protected file is read from the exact checkout and is neither copied nor rewritten. Its control cycle, CBF call, success guard, plant call, and termination logic execute unchanged.

## Trace capture

A read-only Python line tracer, identical in all arms and scoped only to the exact `run.py` frame, snapshots actual `x_k`, `u_des`, selected `u_k`, solver status, plant input/output, branch, and termination facts. It does not return data to the controller or alter any local variable.

## Equality and tolerance

The primary contract is exact canonical semantic equality. Floats are represented by IEEE-754-preserving `float.hex()` strings before hashing/comparison. There is no numeric tolerance. A native A/A mismatch blocks attribution; tolerance cannot be introduced after results are observed.

## Evidence boundary

Collision/progress/termination may appear only as trajectory-identity QA. Wall-clock, GPU, queue, and worker facts are diagnostic only. No performance, overhead, real-time, safety-efficacy, logging-pilot, or formal-cohort claim is authorized.
