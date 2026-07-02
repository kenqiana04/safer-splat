# Synthetic Initial-Unsafe Stress Test Design

This document defines a future stress test. It is not executed in V4-A.

## Purpose

The current `flight100` benchmark contains only a small number of initial near-unsafe or unsafe starts. A controlled stress test can evaluate whether safe-start projection remains reliable when initial states are deliberately perturbed toward risky GSplat geometry.

## Candidate Construction

1. Select several `initial_safe` trials from the existing flight audit.
2. For each selected start, query the nearest or most risky Gaussian using the official GSplat safety query.
3. Perturb the start toward that Gaussian along controlled offsets:
   - `0.005`
   - `0.010`
   - `0.020`
   - `0.050`
4. Keep the original goal unchanged.
5. Label the perturbed starts as controlled near-unsafe or unsafe starts using full GSplat query verification.

## Methods To Compare

- no repair;
- heuristic StartGuard repulsion;
- `verified_projection`;
- `active_set_verified_projection`.

## Metrics

- repair success rate;
- repair distance;
- repair steps or projection iterations;
- full-query verification pass rate;
- post-repair collision count;
- post-repair `min_safety_h` statistics;
- runtime overhead.

## Execution Boundary

This stress test should only be run after V4-A projection and DT audit are reviewed. It should be reported as a synthetic stress test, not as an official benchmark result.
