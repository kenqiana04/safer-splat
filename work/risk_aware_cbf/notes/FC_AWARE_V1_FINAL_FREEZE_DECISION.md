# FC-Aware V1 Final Freeze Decision

## Decision

The current FC-Aware V1 branch is frozen after the partial flight20 stop.

| question | answer |
| --- | --- |
| Continue current FC-Aware V1 | no |
| Continue flight20 | no |
| Run full100 | no |
| Use as paper main method | no |
| Use as paper ablation | yes, only as diagnostic / targeted ablation evidence |
| Claim candidate-count reduction | only in smoke and targeted risk-window scopes, plus partial trial0 candidate reduction with failure clearly stated |
| Claim flight20 success | no |
| Claim FC-Aware caused collision | no, fixed also collided |
| Claim safety stable in full20 | no |
| Claim runtime improvement | no |
| Need future redesign | yes, if this branch is revisited |

## Rationale

The broader flight20 candidate evaluation requested trials 0-19 but completed only trial0. Both fixed and `fc_aware_nearest_cap16000` stopped at trial0 step359 with collision / negative h. The capped profile reduced candidate counts and did not increase H-step, DT-warning, or low-margin counts relative to fixed, but collision in the broader evaluation blocks expansion.

## Mainline Return

No more FC-Aware V1 branch expansion should run before paper drafting. The method narrative should return to:

- Start-Safe CBF;
- Discrete-Time Verification;
- optional triggered V4-C recovery.

FC-Aware V1 remains diagnostic evidence that forced heading candidates can dominate candidate-count behavior and that wrapper-level capping can reduce candidate counts in selected narrower scopes.
