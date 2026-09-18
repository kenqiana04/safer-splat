# Recovery source

`SOURCE_BOUNDED_LOCAL_RECOVERY_V1` and `AXIS_EXTREMA_F32_V1` are explicit and distinct from `SOURCE_NATIVE_EXISTING`. The provider accepts only a deterministic `RecoverySourceGrant` issued by `Supervisor.authorize_recovery_source` after exact trigger, terminal prefetch, deadline and authority checks. Candidate provenance records the grant identity, frozen rank, state and map. C0 rejects the same candidate without that exact grant or if any existing admissibility condition fails. The provider cannot select or commit an action.
