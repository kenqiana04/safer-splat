# FC-Aware V1 Final Positioning After Flight20 Stop

## Recommended Paper Positioning

FC-Aware V1 should be positioned as:

- a diagnostic branch revealing the limitation of selected_K-only scheduling;
- a candidate-count ablation in smoke and targeted DT-risk windows;
- a future efficiency direction;
- not the final method;
- not flight20 validated;
- not full100 validated.

## Safe Claims

The paper can safely state:

1. selected_K-only scheduling did not control the dominant forced heading candidates.
2. Forced heading candidates were identified as the candidate-count bottleneck.
3. `nearest_first cap16000` preserved active / tight / low-h recall in targeted replay.
4. Wrapper-level heading cap reduced candidate counts in smoke and targeted risk-window runs.
5. A broader flight20 candidate evaluation was stopped at trial0 because both fixed and capped recovery-disabled configurations encountered collision.
6. FC-Aware V1 was therefore not promoted to benchmark validation.

## Forbidden Claims

Do not claim:

1. FC-Aware V1 passed flight20.
2. FC-Aware V1 passed full100.
3. FC-Aware V1 improves safety.
4. FC-Aware V1 guarantees safety.
5. FC-Aware V1 is the main method.
6. FC-Aware V1 caused the collision.
7. FC-Aware V1 formally improves runtime.
8. cap16000 is universally safe.
9. heading cap can replace DT Verification, CBF-QP filtering, or recovery.

## Suggested Wording

Although FC-Aware heading capping reduced candidate counts in smoke and targeted DT-risk windows without worsening the monitored DT-verification metrics, a broader flight20 candidate evaluation was stopped at trial 0 because both the fixed and capped configurations encountered a collision under recovery-disabled execution. We therefore do not promote FC-Aware V1 to the final method, and retain it as diagnostic evidence and a future efficiency direction.
