# Geometry Contract V2 Decision

## Why `0.10` is no longer a legal base radius authority

PR #105 established that `0.10` was an independently frozen shadow value, while the controller operating on the same state and Gaussian clearance field used `0.015`. The `0.10` value was internally well-formed but was not derived from the controller's operational footprint. Retaining it would preserve the exact dual-authority defect classified as SS-F5.

## Why controller radius is the base footprint authority

The controller's `radius` is the value actually passed into `CBF` and then into the same `GSplatLoader.query_distance` function. It therefore defines the operational footprint against which the controller computes its barrier. V2 makes L0 consume that authority read-only so the two layers cannot silently diverge again.

## Why the `0.01` margin is preserved

The value was named `FIXED_SAFETY_MARGIN_M` and composed separately from `ROBOT_RADIUS_M` in commit `04ebca2b1b35124ad0e61ebed96e491c9edae4bb`, before PR #105 and before this V2 decision. This supports an independent certification-buffer interpretation. V2 preserves that policy while changing only the base authority. The sentinel values were not consulted to choose or validate `0.01`.

## Why radius cannot be chosen to make L0 PASS

Choosing a radius from observed PASS/FAIL, L1/L2 reachability, or the 15 sentinel values would make the admission contract outcome-dependent. It would invalidate prospective endpoint support and make the contract impossible to distinguish from tuning. V2 therefore freezes authority and margin from pre-existing semantics only.

## Why Gaussian filtering is not changed

PR #105 found that L0 and controller already share the FULL Gaussian set and filtering behavior. Changing floor/background/opacity handling would introduce a second causal variable and would not isolate SS-F5. Those semantics remain unchanged and unresolved semantic labels are not guessed.

## Why the controller is not changed to `0.11`

This task has no controller mutation authority. More importantly, the design objective is authority alignment for shadow certification, not retrospective controller redesign. Enlarging the controller footprint would alter actions, trajectories, and scientific conditions and would require an independent controller protocol.

## Why V1 remains historically valid

V1 correctly executed its frozen `0.11` contract: `N_primary=0`, `L0 FAIL=14122`, and Case C remain immutable. V2 is a new contract motivated by the diagnosed authority mismatch. It is not a correction of stored V1 outcomes and does not imply that V1 rows “should have passed.”

## Why a support-only pilot precedes any formal cohort

Changing the geometry contract may alter only shadow reachability, but endpoint support is not assumed. After static, sentinel-conformance, and noninterference gates, a bounded pilot may expose only L0 PASS/non-PASS and L1/L2 reached counts. L2 PASS/FAIL/UNKNOWN distribution remains hidden so no scientific endpoint can influence contract selection. A new formal cohort protocol is eligible only after support is established without drift.
