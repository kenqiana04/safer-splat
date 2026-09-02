# Cross-Layer Geometry Authority V2

This directory freezes one geometry-authority contract for the controller and all certification layers. It is a design and validation artifact only: no controller, map, runtime, rollout, or frozen V1 result is changed.

The controller retains its operational ball radius of `0.015 m`. Certification consumes that controller authority plus the pre-existing certification margin `0.01 m`, exactly once, yielding `0.025 m`. Segment reserve remains the separate, explicit value `rho_seg=0.0 m`. Every V2 point and segment certificate uses the same immutable represented-Gaussian-map authority.

Historical V1 constants (`0.10/0.01/0.11 m`) remain valid evidence for V1 but are quarantined from V2 authority resolution. An unresolved V2 authority produces `UNKNOWN/BLOCK`; it never falls back to a historical literal.

Scope counters: runtime implementation `0`; controller mutation `0`; certification-layer mutation `0`; map mutation `0`; rollout `0`; GPU execution `0`; V1 reinterpretation `0`.
