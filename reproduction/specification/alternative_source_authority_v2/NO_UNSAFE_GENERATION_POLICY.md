# No Unsafe Generation Policy

The V2 default alternative set is observational: a candidate must already exist natively before the Supervisor requests alternative evaluation. The safety layers do not create controls.

Random perturbation, noise injection, interpolation, heuristic steering, outcome-conditioned generation, and collision-driven candidate creation are forbidden. `L2_FAIL`, `L3_FAIL`, collision risk, and margin values may route an already authorized candidate evaluation but may not synthesize, mutate, rank into existence, or extend the source set.

`SOURCE_PREDEFINED_LIBRARY` and `SOURCE_POLICY_OUTPUT` are taxonomy entries only. They require a separate future frozen authorization before use. `SOURCE_SYNTHETIC` is forbidden by this contract. Missing or unrecognized provenance produces a typed non-success result, never implicit native status.
