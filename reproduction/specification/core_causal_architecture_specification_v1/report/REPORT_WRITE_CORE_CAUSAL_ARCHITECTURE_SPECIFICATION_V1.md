# REPORT: Write Core causal architecture specification V1

## Result

`PASS_CORE_CAUSAL_ARCHITECTURE_LOCAL_STRUCTURAL_GAP`

**Decision:** `FREEZE_CORE_V1_AND_WRITE_CORE_V2_CAUSAL_INCREMENT_SPECIFICATION`

**Only next task:** `WRITE_CORE_V2_CAUSAL_INCREMENT_SPECIFICATION_V1`

## Frozen mathematical result

The normative model remains `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`: `p_(k+1)=p_k+dt v_k`, `v_(k+1)=v_k+dt u_k`, `∂p_(k+1)/∂u_k=0`, and `∂p_(k+2)/∂u_k=dt²I`. B1 is consequently reclassified as L1 immediate execution admission/late-risk detection, not a candidate safety discriminator.

## Architecture decision

L0 handles Start-Safe/current admission and repair. L1 handles the immediate uncontrollable segment. L2 is the missing candidate-dependent future-safety role; H1 `[t_(k+1),t_(k+2)]` is the preferred future specification target. L3 is a secondary sufficient backup witness, L4 is a finite alternative search under `ALT_ELIGIBLE`, and L5 separates certified terminal action from explicit fail-close.

This is CASE_B: the role decomposition does not establish a full pipeline failure, but any future-control safety method claim requires a new L2 specification outside formal Core V1. Historical B0-B3, Start-Safe, PR87, PR89, and PR90 values remain preserved and unrecomputed.

## Boundaries

No controller, map, data, candidate library, dynamics, B0-B3 gate, rollout, formal navigation, B3 oracle, configuration sweep, or Core V2 implementation was performed. This specification is not a safety guarantee, performance claim, real-time claim, recursive-feasibility proof, global controllability proof, or deployment claim.
