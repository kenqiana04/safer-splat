# Unified executable-safety certificate

A committed control must belong to U_exec, the intersection of actuator, current
CBF, swept-segment, and backup certificates. The backup witness has certified
intermediate segments and reaches X_T. If U_exec is empty, a certified terminal
action may be committed; otherwise Core V1 returns FAIL_CLOSED_UNRECOVERABLE and
does not silently execute nominal control.
