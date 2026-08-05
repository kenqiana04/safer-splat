# FAS-CBF Core V1 versus SAFER

FAS-CBF Core V1 does not replace the Gaussian-map CBF filter. It adds an executable-safety layer requiring actuator admissibility, sampled-interval certification, and a terminal-backup condition before action commitment.

- represented Gaussian obstacle field: current filter -> retained and augmented (IMPLEMENTED_CURRENTLY)
- current-state CBF filtering: current QP -> U_cbf component (IMPLEMENTED_CURRENTLY)
- actuator bounded feasibility: not unified -> U component (DESIGN_CONTRACT)
- sampled execution: historical Euler -> normative model required (DESIGN_CONTRACT)
- swept segment: one/H-step proxies -> required prior to commit (DESIGN_CONTRACT)
- terminal backup: recovery search -> certificate contract (DESIGN_CONTRACT)
- unrecoverable semantics: mixed fallback labels -> explicit fail closed (DESIGN_CONTRACT)
- initial admission: Start-Safe -> projection contract (EMPIRICALLY_SUPPORTED)
- map uncertainty: fixed/proxy boundary -> no deployment claim (UNPROVED)
- online reference: offline only -> forbidden online (DESIGN_CONTRACT)
- proof status: empirical observations -> P1-P6 unproved (UNPROVED)
