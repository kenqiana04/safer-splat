# Proposition S1: One-Sample Represented-Map Safety

**Status:** `PROVED_UNDER_EXPLICIT_ASSUMPTIONS`; implementation correspondence
is `TESTED_IMPLEMENTATION_CONSISTENCY`.

Assume exact normative flow, a static snapshot, a valid exact or conservative
Gaussian segment lower bound, the frozen footprint/margin, and no delay,
disturbance, or tracking error. If `SegmentCertificate.certified=true`, its
lower bound is nonnegative on the entire interval, so the represented Gaussian
barrier does not fall below the frozen threshold during that sample.

This is not a reference-mesh or real-world collision guarantee.
