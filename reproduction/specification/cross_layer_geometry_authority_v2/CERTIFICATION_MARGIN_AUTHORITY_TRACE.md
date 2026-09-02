# Certification Margin Authority Trace

Authority `G1 = CERTIFICATION_MARGIN_AUTHORITY` is the pre-existing fixed safety margin `0.01 m` frozen by PR #106. It is not a second robot radius and is not controller authority.

For every V2 certification point or segment:

`r_cert_effective = r_controller + m_cert = 0.015 m + 0.01 m = 0.025 m`.

The addition occurs exactly once at authority composition time. Downstream adapters receive the composed `0.025 m`; they must not add `0.01 m` again. A layer-local margin literal, missing provenance, or double addition is a validation failure.
