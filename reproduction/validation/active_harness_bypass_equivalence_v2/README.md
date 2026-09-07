# Active Harness BYPASS Equivalence V2

This task performs a bounded execution-QA comparison of the untouched Stonehenge reference controller/plant slice against `ACTIVE_HARNESS_BYPASS`. It tests behavioral transparency only. It does not enable active assurance, evaluate safety efficacy, run official100, or invoke the scientific outcome oracle.

Frozen order: sentinel trial 50, followed only after PASS by trials 10, 30, 70, and 90. Each pair runs REFERENCE then BYPASS in fresh processes. Exact float32 bit equality is normative; numeric differences are diagnostic only and never become a post-hoc tolerance.
