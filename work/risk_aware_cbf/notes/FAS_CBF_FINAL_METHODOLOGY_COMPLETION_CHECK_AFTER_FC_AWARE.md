# FAS-CBF Final Methodology Completion Check After FC-Aware

## Main Method Status

| component | status | role |
| --- | --- | --- |
| Start-Safe CBF | ready | main method |
| Discrete-Time Verification | ready | main method |
| optional V4-C Recovery | ready | optional triggered module |
| Adaptive V1 selected_K-only | frozen | support / diagnostic |
| MPC-style Recovery | frozen | future work / negative diagnostic |
| FC-Aware V1 | frozen | diagnostic / targeted ablation only |

## FC-Aware Final Status

FC-Aware V1 is frozen after the partial flight20 stop. It has useful diagnostic evidence and targeted candidate-count ablation evidence, but it is not promoted to the final method.

Key reason:

- broader flight20 candidate evaluation requested 20 trials but stopped after trial0;
- fixed and capped both encountered collision;
- no complete flight20 evidence exists;
- no full100 evidence exists.

## Paper-Writing Implication

No more method branches should be added before paper drafting. The next step is Method + Experiments writing around the main line:

- Certified Feasibility-Aware Start-Safe CBF;
- Discrete-Time Verification;
- optional triggered V4-C recovery.

FC-Aware V1 can appear only as diagnostic / targeted ablation material, with all scope limits stated explicitly.
