# Collision versus Certification-Margin Oracle V2

Two outcomes are frozen and never merged:

1. `REPRESENTED_MAP_COLLISION_PROXY`: evaluate each closed, actually executed position segment against the frozen represented Gaussian obstacle reference using operational footprint radius **0.015 m** and no certification margin. Report per-segment minimum clearance, trial minimum clearance, penetration indicator, first violating cycle, and violating-segment count.
2. `CERTIFICATION_MARGIN_VIOLATION`: use effective certification radius **0.025 m = 0.015 m + 0.010 m**. This measures loss of reserved certification margin and must not be named physical collision.

The final collision proxy is swept-segment, posthoc, represented-map-relative, identical across compared variants, and independent of internal certificate PASS/FAIL. Endpoints alone are insufficient. Safety and task progress remain separate; no composite score is defined.
