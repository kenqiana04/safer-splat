# Future Trial Manifest Policy

The first prospective environment is Stonehenge because the frozen baseline already defines its map/config, deterministic 100-trial circle, controller, `dt`, and step cap. Replica/TUM/cross-dataset expansion is a separate authorization. No environment may be added to increase the L2 FAIL rate.

Before Phase 1, freeze controller commit, source blobs, environment, map manifest, exact starts/goals, trial IDs/order, deterministic seed policy, `dt`, termination rules, robot/margin/rho contract, queue configuration, schema versions, and equivalence tolerances. Phase 3 receives a distinct signed/hashed manifest before any formal shadow result.

Every intended step is retained irrespective of L1 margin, L2 status, collision, progress, risk, multi-candidate presence, or observer health. Minimal drop records preserve the intended denominator. Pilot data are excluded from the formal cohort by default. Completed trials are never silently rerun; infrastructure recovery appends provenance and resumes only under a pre-frozen policy.

Seed policy for the current `run.py` design is `NO_RANDOM_SAMPLING_FROZEN_INDEXED_TRIALS`; if future wrappers introduce randomness, explicit seeds and RNG-library identities become mandatory before Phase 1.

**Scope:** DESIGN ONLY | NO ON-POLICY COLLECTION | NO CONTROLLER AUTHORITY | NO DECISION FEEDBACK | NO PERFORMANCE CLAIM.
