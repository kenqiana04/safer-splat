# TUM DT-Triggered V4-C Recovery V1

## Result

`PASS_DT_TRIGGERED_V4C_AVOIDS_OVERLAP_WITH_PROGRESS_LIMITATION`.

PR #47 remains the independent original SAFER baseline and PR #48 remains the
shadow-only numerical forensics.  This task is the first control intervention:
it used the recovered V4-C only after a strict float32 complete-map H3
predicted overlap, never after an ordinary margin warning.

## Frozen identities and contract

- V4-C source: restoration commit `b626b99cb1ed1437730c0e0734635fd8f0bdc517`, blob
  `5b28585b9b98d991d9f4fa9e0158812d2a3be80a`.
- H3 is three explicit-Euler steps under the current CBF-safe control.
- Margin monitor: `h3_min < 0.0005`, log-only.
- Recovery entry: `current_fullmap_h > 0 and h3_min < 0`.
- V4-C remains one-step, non-always-on: it selects and executes a bounded first
  control, then re-evaluates on the next state. Float64 was post-hoc only.

## Development 0->50

The strict trigger fired at step 770 once. The run completed 800 steps without
float32 negative h, QP failure, nonfinite values, or timeout. Progress was
`0.6445666648765063` versus frozen baseline `0.6442182910871558`; it did not
reach the goal. Independent float64 certification had minimum
`3.464632642439418e-09`, zero robust overlaps, and residual at most
`4.440892098500626e-16`.

## Held-out paired diagnostics

The pre-frozen registry pairs were 1->51, 8->58, and 9->59. Both 1->51 and
9->59 baseline arms stopped on a float32 GSplat-overlap proxy. Their strict
V4-C interventions each fired once, reached 800 steps without float32 negative
h, and their certified boundary sets had zero robust overlaps. Pair 8->58
reached no strict trigger; baseline and intervention were identical under the
frozen controller. No intervention introduced a robust overlap, QP failure,
nonfinite state, or timeout.

The intervention did not reach goals on these three held-out pairs. It is
therefore a bounded proof-of-mechanism, not a general safety, completion, or
20/100-trial claim. GSplat overlap remains a proxy rather than an official mesh
collision.

## Boundaries and next task

No Start-Safe, Risk-Aware ranking, new Top-K, always-on recovery, formal
training, V1R7, or extra trials ran. The original baseline was not overwritten.
The next unique task, if separately authorized, is a broader preregistered
held-out evaluation; it must preserve this frozen baseline and trigger contract.
