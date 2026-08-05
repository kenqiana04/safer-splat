# Integrator consistency audit

dynamics/systems.py provides the continuous double-integrator derivative. run.py
and the V4 scripts advance x plus Delta t times that derivative. Therefore past
position updates use pre-control velocity. Missing delay and tracking bounds are
UNKNOWN_NOT_RECOVERED rather than zero.
