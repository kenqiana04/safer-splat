# L2/H1 Shadow Instrumentation Implementation Contract V1

This package implements instrumentation only. It is not authorized to execute real navigation, an OFF-vs-ON equivalence smoke, a logging pilot, or a prospective cohort.

The controller-side contract is:

1. call the exact frozen `solve_QP` once;
2. retain only object identity integers plus an immutable `u_des` tuple until the protected caller reaches its plant call; no live tensor/array/list is retained for async handoff;
3. at entry to the frozen plant function, after the caller's success guard and before plant evaluation, deep-copy `x_k`, `u_des`, selected `u_k`, identity, reachability facts, and map authority reference;
4. call bounded `try_capture` using `put_nowait` semantics;
5. return the exact frozen selected output irrespective of observer health.

`u_des` is a `NOMINAL_REFERENCE`, never a native alternative. The native candidate group contains the selected control plus only sibling candidates that a frozen mechanism created before observation. With no such siblings its size is one.

The worker has no result-return channel. It receives immutable payloads, runs injected frozen read-only certifiers on worker-owned values, and appends evidence. L0/L1 values produced there are labeled `SHADOW_RECOMPUTED_FROZEN_CERTIFIER`. Instrumentation health never becomes L2 UNKNOWN.

Map authority is frozen once per run. Step payloads carry only `map_authority_id`. Queue full, worker absence/crash, serializer failure, map-authority failure, certifier exception, and shutdown timeout cannot change controller output or cause fail-close.

No H2 or L3/L4/L5 implementation exists in this package.
