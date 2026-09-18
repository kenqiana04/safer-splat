# F1 generator

The six ordered controls are constructed directly from componentwise actuator endpoints: `(high_x,0,0)`, `(low_x,0,0)`, `(0,high_y,0)`, `(0,low_y,0)`, `(0,0,high_z)`, `(0,0,low_z)`. Unsupported dimensions, nonfinite bounds or intervals that do not straddle zero fail closed. No clipping, normalization, epsilon dedup, map query, randomization, goal steering or outcome dependence exists.

Canonical equivalence uses normalized-zero IEEE-754 binary32 bits plus actuator and transition identity. It removes a primary-equivalent vector and any duplicate while preserving earliest generator rank. The actual endpoint remains the exact inclusive authority value; the bit representation is for transition-equivalence identity, consistent with the frozen primary boundary canonicalization and C0 bound check.
