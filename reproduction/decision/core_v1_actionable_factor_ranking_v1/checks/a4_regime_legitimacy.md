# A4 regime-legitimacy check

`VALID_REGIME_ANALYSIS` requires a frozen real-system source for period, velocity, latency, and tracking-error budget. The PR #90 endpoint OAT grid is explicitly a counterfactual exposure diagnostic, not deployment evidence. E5/E6 have zero-velocity initial states, and the frozen record has no tracking-error budget or authoritative latency source.

Therefore `VALID_REGIME_ANALYSIS=NOT_YET_SUPPORTED` and `INVALID_TRIGGER_ENGINEERING_RISK=HIGH`. A4 cannot rank first; increasing speed, dt, delay, or error solely to make an event appear would violate the frozen boundary.
