# Proposition F1: Fail-Closed Soundness

**Status:** `PROVED_UNDER_EXPLICIT_ASSUMPTIONS`; implementation correspondence
is `TESTED_IMPLEMENTATION_CONSISTENCY`.

The only code path assigning `committed_control_or_none` requires a candidate
whose actuator, current-feasibility, segment, and backup checks all pass. Every
exhausted, unknown, nonfinite, unsafe, timeout, and infrastructure path assigns
no unverified nominal control. Thus absence of a certificate cannot silently
execute an uncertified candidate.

This does not prove that no control exists outside the frozen finite library.
