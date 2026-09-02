# Map Geometry Authority Trace

Authority `G3 = STATIC_IMMUTABLE_REPRESENTED_GAUSSIAN_MAP_AUTHORITY` freezes the same map snapshot and mathematical query contract used by the current controller: FULL represented-Gaussian set, Gaussian centers, scales/covariances/rotations as loaded, a single log-scale exponentiation where applicable, frozen opacity/filter behavior, metric world/map frame, axis convention, and point-to-ellipsoid sign convention.

V2 does not remove floor/background Gaussians, change opacity filtering, rescale the map, add transforms, or select a different snapshot. Every certification consumer records the immutable map identity and the same query-context identity. A missing or conflicting map identity yields `UNKNOWN/BLOCK`.

The authority is static for the frozen benchmark. If a later benchmark uses mutable maps, it requires a separately frozen per-step snapshot authority; this contract does not silently generalize.
