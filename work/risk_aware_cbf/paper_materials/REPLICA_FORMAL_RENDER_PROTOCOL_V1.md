# Replica Formal Render Protocol V1

## Scope and Freeze Point

This G0.5E-v1 protocol is frozen before formal camera-manifest generation and
before any formal RGB-D output. It inherits `apartment_0`, the official
textured `mesh.ply`, and `habitat/mesh_semantic.navmesh` from G0.5D-v2.

## Fixed Randomness and Spatial Sampling

- Python, NumPy, and Habitat Pathfinder seed: `20260715`.
- First seeded navigable point is the start anchor.
- Accept later seeded candidate anchors only when their Euclidean distance from
  the preceding accepted anchor is at least `1.0` scene unit and their
  Pathfinder shortest path is finite.
- Examine at most `500` candidates. Connect accepted anchors in acceptance
  order, then uniformly resample the combined shortest-path polyline to
  exactly `100` spatial locations separated by at least `0.10` path unit.
- Failure to produce those locations is
  `blocked_by_insufficient_preregistered_navmesh_coverage`.

## Camera and Sensor Contract

- Camera base: navigable source point; camera position: base plus
  `[0, 1.50, 0]` in Habitat world coordinates.
- World up axis: `+Y`; camera height remains `1.50` even if implementation
  details require an explicit axis conversion.
- RGB and depth: pinhole, width `640`, height `480`, HFOV `90` degrees,
  near `0.05`, far `20.0` scene units.
- RGB: uint8 RGB PNG. Depth: uint16 PNG in millimetres with fixed scale
  factor `0.001` metres per stored unit; source is Habitat metric float depth.

## Orientation, Frame Order, and Split

- Base forward is the local resampled-path tangent. A degenerate tangent uses
  the nearest non-degenerate tangent; no usable tangent stops the protocol.
- Pitch and roll are zero. Yaw offsets are right-handed rotations around `+Y`
  in the fixed order `0`, `-60`, `+60` degrees.
- `frame_id = position_index * 3 + yaw_slot`, producing `frame_0000` through
  `frame_0299` only.
- `frame_id % 10 == 0` is eval (30 frames); all other frames are train (270).

## Pose and Rendering Contract

Habitat camera local basis and Nerfstudio/OpenGL camera local basis are audited
before manifest generation. The frozen conversion is identity only if the
sensor-state basis, center depth ray, rotation checks, and inverse checks pass.
The renderer consumes only the immutable manifest, renders serially in frame
order, never samples new poses, and stops on the first failed frame. It neither
replaces frames nor generates more than 300 candidates.

## Stop Rules and Boundaries

Any frozen-input hash mismatch, pose-convention failure, static protocol
failure, manifest failure, render failure, metric-contract failure, or TUM
mutation stops this version. No scene, seed, sensor, height, yaw, frame count,
split, mesh, navmesh, or tolerance is changed after formal output begins.
No COLMAP, pose auto-scale, translation normalization, Gaussian training, or
SAFER execution is in scope.
