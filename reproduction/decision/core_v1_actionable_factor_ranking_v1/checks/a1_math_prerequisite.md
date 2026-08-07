# A1 mathematical prerequisite check

Frozen PR #90 establishes `p_(k+1)=p_k+dt v_k`, `v_(k+1)=v_k+dt u_k`, and `∂p(tau)/∂u_k=0` over the immediate interval.

1. **Q1:** The existing B1 label is not sufficient to distinguish state/execution admission from candidate-dependent safety filtering.
2. **Q2:** If B1 is admission/late-risk detection, the evidence establishes a role and evaluation-denominator problem, not an implementation defect.
3. **Q3:** If B1 is intended as candidate-dependent safety filtering, the strict zero derivative is a structural semantic mismatch.
4. **Q4:** `u_k` first affects velocity at `k+1` and position on the next propagated position horizon (`p_(k+2)`); it cannot alter the immediate position interval.
5. **Q5:** A2, A3, and A4 must wait: each needs the role/horizon definition to avoid circular conditioning, illegal B3 entry, or artificial activation interpretation.

Conclusion: `A1_REQUIRED_COMMON_PREREQUISITE=TRUE`. This task changes neither B1 nor any controller behavior.
