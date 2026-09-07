
# Alternative cycle integration V2

The frozen `SOURCE_NATIVE_EXISTING` inventory is currently empty. The
coordinator may call `AlternativeProvider` only after a Supervisor routing
decision explicitly names `ALTERNATIVE_SOURCE_QUERY`; an empty inventory
returns `ALT_EXHAUSTED/NO_ALTERNATIVE_AVAILABLE` to Supervisor. The
coordinator must not jump directly to backup.

If a future authorized native candidate exists, it reuses the single L1 result
from this cycle, creates a fresh candidate-specific binding, and repeats
C0 -> L2 -> L3. It never recomputes L1, synthesizes/perturbs a candidate, or
lets an alternative provider commit an action. Expired deadlines block a new
query; an unavailable alternative is not itself unsafe.
