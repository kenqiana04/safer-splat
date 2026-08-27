# L2/H1 shadow certifier V1

This directory contains a task-local, removable implementation of the PR #93 L2/H1 specification. It observes one state/candidate/map-snapshot tuple, propagates the first control-affected position segment, calls the frozen PR #84 segment backend, and emits a typed `PASS`, `FAIL`, or `UNKNOWN` log record.

It is not a controller component. It has no controller, execution, candidate-selection, alternative-search, backup, terminal, or fail-close authority. It does not implement L3, L4, L5, H2, a new geometry primitive, or a production hook.

## Frozen propagation

Under `POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1`:

```text
p_k1 = p_k + dt*v_k
v_k1 = v_k + dt*u_k
p_k2 = p_k + 2*dt*v_k + dt^2*u_k
S_H1 = Segment(p_k1, p_k2)
```

## Local validation

```powershell
python -B freeze_inputs.py
python -B -m unittest discover -s tests -v
python -B build_evidence.py
python -B validate_l2_h1_shadow_certifier_v1.py
```

`shadow_cli.py` accepts only named synthetic implementation fixtures. It does not read navigation states or issue actions.

Maximum supported claim: “Specification-faithful shadow implementation of the local candidate-dependent H1 map-relative certifier.”
