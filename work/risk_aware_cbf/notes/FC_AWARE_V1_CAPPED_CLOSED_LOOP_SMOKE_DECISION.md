# FC-Aware V1 Capped Closed-Loop Smoke Decision

- Smoke completed scopes: trial12_step20, trial12_step80, trial13_step20.
- Overall action: `RECOMMEND_TARGETED_EXTENSION_ONLY`.
- Cap integrated in all completed scopes: True.
- Candidate count reduced in all completed scopes: True.
- Any unsafe_to_expand: False.
- Recommend continue FC-Aware V1: yes if action is targeted extension; otherwise hold.
- Recommend targeted extension: yes only when action is RECOMMEND_TARGETED_EXTENSION_ONLY.
- Recommend flight20: no.
- Recommend full100 now: no.
- Paper positioning: capped smoke can be reported as a small wrapper-level ablation if safety remains unchanged; it is not a safety proof.
