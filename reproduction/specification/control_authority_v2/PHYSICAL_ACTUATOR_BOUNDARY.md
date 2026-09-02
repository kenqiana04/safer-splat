# Physical Actuator Boundary

The V2 authority freezes a normative benchmark admissibility box, not a physical robot actuator model.

Established for the benchmark model:

- acceleration bounds: componentwise inclusive `[-0.1,0.1]^3`
- velocity bounds: componentwise `[-0.1,0.1]^3`
- control period: `0.05 s`
- post-certification saturation: forbidden
- transformed alternatives: new identity and re-certification required

Not established:

- hardware torque/thrust/acceleration realization
- slew, jerk, or delta-control limits
- actuation delay
- quantization
- tracking error and disturbances
- device-specific saturation or low-level controller behavior

These unknowns are `OUTSIDE_METHOD_BOUNDARY_UNKNOWN`. They block physical-executability and deployment claims but do not prevent freezing the normative simulation authority chain. No infinite-control assumption is made.
