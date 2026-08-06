# Library independence

The six slots depend only on current state, local goal, frozen actuator/dt constants, current represented-map full-query status and active primitive, and frozen map identity. They do not accept a reference mesh, oracle output, future trajectory, group label, registry, runtime, or outcome input.
