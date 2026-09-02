# Selected Control Actuator Authority V2

This directory freezes a design-only control-authority chain on exact PR #108. It does not implement a supervisor, change the controller, alter dynamics, run a simulator, or claim physical actuator readiness.

The frozen source has two distinct facts:

1. Current Stonehenge simulation: a successful CBF-QP output is assigned to `u` and passed unchanged to `double_integrator_dynamics`; there is no post-QP clip, saturation, delay, or rate transform. Thus the observed simulated chain is `CERTIFIED_EXECUTION_MATCH`.
2. Physical execution: no hardware actuator authority is exposed. The frozen componentwise `[-0.1,0.1]^3` contract is a normative benchmark admissibility authority, not a deployment guarantee. Rate, slew, jerk, delay, and quantization remain explicit outside-method/unknown fields.

V2 therefore requires actuator admission before selection and identity equality between selected and committed control. Any transformation creates a new candidate identity and requires re-certification. Unknown or hidden actuator semantics block; they never silently pass.

Scope counters: runtime implementation `0`; supervisor implementation `0`; controller mutation `0`; dynamics mutation `0`; actuator simulation `0`; rollout `0`; GPU execution `0`; formal cohort `0`; performance evaluation `0`.
