# Proposition R1: Tail-Witness Recoverability

**Status:** `PROVED_UNDER_EXPLICIT_ASSUMPTIONS`; implementation correspondence
is `TESTED_IMPLEMENTATION_CONSISTENCY`.

After a certified first control is executed exactly, the successor equals the
first predicted witness state. Removing the executed prefix leaves the same
certified segment/control suffix and terminal certificate. Therefore the suffix
is a valid finite backup witness if the snapshot and model remain unchanged and
there is no delay, disturbance, tracking error, or state-estimation mismatch.

This is finite-horizon witness-specific recoverability, not global recursive
feasibility.
