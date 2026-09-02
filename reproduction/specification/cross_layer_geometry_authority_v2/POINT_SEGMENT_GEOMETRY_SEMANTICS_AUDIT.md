# Point/Segment Geometry Semantics Audit

| Question | Frozen V2 answer |
|---|---|
| Base robot radius | G0, `0.015 m` |
| Certification margin | G1, `0.01 m`, exactly once |
| Certification effective radius | `0.025 m` for every point and segment certificate |
| Segment reserve | G2, `rho_seg=0.0 m`, independent of margin |
| Point reserve | Not applicable |
| Map/query | Same immutable G3 represented-Gaussian query for all consumers |
| Sign | Unchanged controller/query sign convention |
| L1 endpoints | Closed segment includes `p_k` and `p_{k+1}` |
| L2 endpoints | Frozen H1 segment `p_{k+1}` to `p_{k+2}` |
| L3 | Every backup segment plus terminal point and zero-hold use one authority |
| L5 | Terminal point and zero-hold use one authority |

The parameterized segment backend remains reusable because it accepts `effective_radius` and `rho_seg` independently. Reuse is conditional on typed V2 injection; the backend is not an authority source. Point and zero-hold components may not independently load historical constants.

Verdict: `PASS_UNIFIED_POINT_SEGMENT_GEOMETRY_SEMANTICS_V2`.
