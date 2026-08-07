# Alternative-control eligibility

`ALT_ELIGIBLE(x_k,primary,M_k) := ADMISSIBLE(x_k,M_k) AND IMMEDIATE_SAFE(x_k,M_k) AND PRIMARY_EVALUATED(primary) AND NOT PRIMARY_CERTIFIED(primary) AND PRIMARY_FAILURE in {CANDIDATE_FUTURE_SAFETY_FAIL, BACKUP_WITNESS_FAIL} AND NOT TERMINAL_ALREADY_SAFE(x_k) AND NOT CANDIDATE_INDEPENDENTLY_PRECLUDED(x_k,M_k)`.

`h(x_k)<0` is not a B3 opportunity. An immediate unsafe segment is not a B3 opportunity. Candidate-dependent future failure or primary witness failure may be eligible if the predicate holds. A committed primary and terminal-already-safe state are not eligible. This predicate constrains future A3 coverage identification; it does not run a search.
