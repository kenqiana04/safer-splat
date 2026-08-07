# Minimal state-machine delta V1

Preserve the PR #92 ordering: L0 current admission/repair → L1 immediate uncontrollable segment → frozen candidate preparation → S6 primary candidate under test. Define only the formerly conceptual S6 L2 transition:

- `L2_PASS`: S6 → S7 primary future-safe → L3 witness.
- `L2_FAIL`: S6 → S9 primary not certified → test frozen `ALT_ELIGIBLE` before L4.
- `L2_UNKNOWN`: S6 → typed L5 fail-close/non-evaluable path; it is not candidate unsafe and is not L4 eligible.

All L0/L1/L3/L4/L5 behavior remains frozen. This is a specification delta, not an implemented state machine.
