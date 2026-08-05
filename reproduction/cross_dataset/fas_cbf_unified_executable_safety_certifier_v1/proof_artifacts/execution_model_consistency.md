# Execution Model Consistency

All audited formal plant, candidate-verifier, and predictive-backup paths use `x_next = x + dt * [v,u]`. Therefore position is updated from pre-control velocity and current acceleration cannot change the immediate swept-position segment. Constant-acceleration ZOH remains diagnostic and is not used to reinterpret historical evidence.

This is a frozen-model relative-degree/timing boundary, not a universal physical impossibility claim. Delay, disturbance, and tracking-error bounds remain unproved.
