# Legacy Runner Reuse and Quarantine V2

Reusable, read-only primitives are: frozen trial start/goal generation, PD desired-command formula, successful Clarabel CBF-QP proposal primitive, position-first double-integrator dynamics, and Stonehenge map loading/query primitives. They are imported or reproduced by exact-source adapters, not given V2 authority by historical use.

Quarantined semantics are: post-step endpoint-only `safety`; using the same represented-map query as an independent outcome oracle; declaring timeout plus motion a success; treating solver failure/break as physical safe stop; and letting `solve_QP`'s failure-returned `u_des` become executable. Trial execution and post-hoc evaluation are separate packages and processes. `run.py` remains the untouched `REFERENCE_BASELINE` and is never relabeled as the V2 active runner.
