# Claims and Limitations: Adaptive V1 Update

## 1. Claims Allowed

- Adaptive V1 was evaluated as a risk-response budgeting support module.
- Adaptive V1 reacted to DT-risk states by increasing `selected_K`.
- In closed-loop pilots, `selected_K` was applied to the V1 candidate wrapper.
- Tested safety metrics did not degrade in the reported pilots.
- The experiments revealed a forced-candidate dominance bottleneck.

## 2. Claims Forbidden

- No candidate-count reduction claim.
- No runtime improvement claim.
- No standalone safety guarantee.
- No new CBF theorem.
- No full100 claim.
- No replacement for Discrete-Time Verification.
- No replacement for optional Predictive Recovery.
- No statement that `selected_K_applied` implies final candidate-count reduction.

## 3. Reviewer Risk

Likely reviewer questions:

- If `selected_K` does not reduce final candidates, why include Adaptive V1?
- Does this weaken the efficiency contribution?
- Does forced-candidate dominance mean V1 is irrelevant?
- Is candidate budgeting safe if candidates are pruned?

## 4. Response Strategy

Recommended response:

- Report Adaptive V1 as an ablation and diagnostic support module, not as the main method.
- Keep the main paper contributions on Start-Safe CBF and Discrete-Time Verification.
- Present forced-candidate dominance as a useful negative systems insight.
- State that candidate pruning is not used as a safety guarantee.
- Maintain that full-query fallback and DT Verification are required for any future pruning-based method.

