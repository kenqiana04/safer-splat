# Method scope and claim boundary V2

The model-check result supports only logical closure of this finite specification under its stated assumptions. Normative scope is a static immutable represented Gaussian map, frozen cross-layer geometry and actuator authority, exact position-first Forward Euler double-integrator state alignment, no tracking error, no actuation delay, no disturbance, and represented-map-relative certification.

Method-certified actions are: certified navigation, a still-valid retained backup action, and a certified terminal action. When none exists, the result is `NO_METHOD_CERTIFIED_ACTION / ASSURANCE_BOUNDARY_NO_CERTIFIED_ACTION`; any external emergency behavior is outside the theorem.

The specification does not prove physical-world map truth, continuous-time or intersample collision avoidance, real-time schedulability, recursive feasibility outside the frozen witness contract, deployment safety, progress, goal success, or efficacy. Continuous ZOH kinematics are nonnormative. A future extension requires `INTERSAMPLE_CONTROL_AUTHORITY_AND_ROBUSTNESS_CONTRACT`.

Safety metrics and liveness metrics must remain separate. Backup use or terminal hold never automatically counts as task success.
