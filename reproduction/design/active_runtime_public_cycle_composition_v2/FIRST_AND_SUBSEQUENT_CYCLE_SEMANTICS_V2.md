
# First and subsequent cycle semantics V2

After I0a admission passes, cycle 0 retains no backup token unless one was
already authorized. Primary proposal still follows L1 -> P0 -> C0 -> L2 ->
L3; absence of backup never skips L3. A navigation commit creates the k+1
retained token atomically. If no navigation and no retained backup exist, only
a Supervisor-admitted terminal or assurance boundary can resolve the cycle.

For k>0, validate the retained token against the exact snapshot, registry,
actuator, and temporal identity before arbitration. Failed navigation preserves
the old token. A valid backup can be routed by Supervisor; a stale/invalid or
exhausted token is a typed event. New navigation uses the same atomic handoff.
