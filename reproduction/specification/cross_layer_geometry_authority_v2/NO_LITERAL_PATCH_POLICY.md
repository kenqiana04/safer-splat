# No-Literal-Patch Policy

Future implementation must resolve G0–G3 through one typed authority object. It may not repair consumers by scattering `0.015`, `0.01`, `0.025`, `0.0`, `0.10`, or `0.11` literals across L0–L5.

Allowed literals exist only in a single versioned authority construction boundary backed by frozen provenance. All consumers receive the authority or a derived point/segment view. Any missing field, unknown map snapshot, or provenance mismatch is `UNKNOWN/BLOCK`.

The policy forbids controller mutation, double margin addition, silent `rho_seg` substitution, V1 fallback, layer-local overrides, and historical-loader imports in the V2 runtime graph.
