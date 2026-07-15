# REPORT: Replica Frozen Formal Metric Preprocessing V1

## 1. Purpose
Freeze and execute a formal Replica RGB-D protocol without training or SAFER.

## 2. Prior Renderer Closure
G0.5D-v2 passed the isolated Python 3.9 Habitat-Sim renderer, scene load,
navmesh, and EGL smoke.

## 3. Missing-Protocol Root Cause
The inherited task lacked a camera trajectory, seed, pose convention, frame
order, and split. G0.5E-v1 supplied them before manifest generation.

## 4. Failure-Level Classification
The prior missing artifact was Level B. This execution freezes at the recorded
RGB-integrity gate, not a renderer-environment or Replica-asset failure.

## 5. Frozen Scene and Input Assets
The selected scene remains `apartment_0`; official textured mesh and navmesh
hashes match the prior closure.

## 6. Preregistered Camera Protocol
Seed 20260715, 100 spatial locations, yaw order 0/-60/+60, 640x480 pinhole
sensors, HFOV 90, near/far 0.05/20, height 1.50, and the 270/30 split were
written to Git before formal output.

## 7. Pose-Convention Audit
The Habitat center depth ray, sensor basis, determinant, orthogonality, and
inverse checks passed. Habitat camera to Nerfstudio/OpenGL camera conversion is
the frozen identity matrix.

## 8. Frozen Camera Manifest
The external manifest has 300 ordered rows and SHA-256
`1056121e4470124e180a3367172440f540f0acdc5adab665c3187ac8ab87be25`.

## 9. Manifest Geometry and Metric Checks
All manifest rows, rotations, quaternions, source navmesh points, height
offsets, and path arclength spacing passed before rendering.

## 10. Formal RGB-D Rendering
The manifest-only serial renderer recorded 300 successful status rows and did
not resample or replace any frame.

## 11. RGB and Depth Integrity
Integrity failed: 33 RGB frames are black or near-black and 32 depth frames are
all zero under the fixed check. They remain in external staging unchanged.

## 12. Nerfstudio Transform Contract
Staging `transforms.json` has 300 valid finite camera-to-world transforms equal
to the immutable manifest.

## 13. Metric-Preservation Validation
Translation scale ratio is 1; no auto-scale, normalization, COLMAP, or pose
estimation was used.

## 14. Train/Eval Split
The staging split is 270 train and 30 eval frames, disjoint and complete.

## 15. Geometry and Navigation-Volume Readiness
Mesh, navmesh, source points, and bounds passed. This does not override failed
image/depth integrity.

## 16. TUM Immutability
TUM `transforms.json` remained SHA-256
`b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`.

## 17. Negative and Neutral Evidence
No frame was removed, replaced, or rerendered. The optional semantic descriptor
warning is retained as neutral context; it was not used to alter the protocol.

## 18. Decision
`blocked_by_rgb_integrity`. The staging directory was not atomically published.

## 19. Fixed Splatfacto Training Entry Conditions
Not met. A new protocol version must diagnose the stored black/zero frames
before any training task can be considered.

## 20. Claim Boundaries
No Gaussian reconstruction, Splatfacto training, SAFER loader evaluation, or
SAFER baseline execution occurred. Renderer output is not generalization.
