# Segment Reserve Authority Trace

Authority `G2 = SEGMENT_RESERVE_AUTHORITY` is the explicit segment-only reserve `rho_seg=0.0 m`. The legacy `SweptSegmentCertifier` constructor (`segment_certificate.py:11-18`) and frozen backend adapter (`frozen_backend_adapter.py:39-40,123-124`) expose `effective_radius` and `rho_seg` as separate inputs. Historical shadow contract code also fixes `rho_seg=0.0` (`shadow_contract.py:52-58`).

V2 preserves this separation. `rho_seg` is not the certification margin and is never silently set to `0.01`. Point queries mark it `NOT_APPLICABLE`; segment queries use exactly `0.0 m`.
