# REPORT: Replica Habitat-Sim Python 3.9 Official Binary Closure

## 1. Purpose
Close the official isolated Python 3.9 renderer gate and audit the frozen
Replica scene without training or SAFER execution.

## 2. G0.5D-v1 Failure
G0.5D-v1 required Python 3.12 with Habitat-Sim 0.3.3. The official stable
binary matrix did not provide that ABI combination.

## 3. Failure-Level Classification
The v1 result remains frozen as Level B, environment configuration
overconstraint.

## 4. Pre-Execution Protocol Amendment
G0.5D-v2 changes only Python 3.12 to Python 3.9 before any formal Replica
rendering. It is not performance-driven tuning.

## 5. Official Python 3.9 Package Availability
The exact official Linux build is Habitat-Sim 0.3.3
`py3.9_headless_bullet_linux_acbe6f4922e68145e401e55c30f9dfea460a3f24`
from `aihabitat`.

## 6. Environment Creation
`replica_habitat_renderer_py39` was created at
`/disk1/zlab/conda_envs/replica_habitat_renderer_py39` from
`conda-forge;aihabitat`. Python is 3.9.23 and Habitat-Sim is 0.3.3.

## 7. Isolation from SAFER Environments
The `safer_splat_official` explicit manifests before and after have identical
SHA-256 `0907db99ad80717d5032758b694731c7bb9289941bbe3879b548cb4b6bc7222a`;
their diff is empty and `habitat_sim` remains unavailable there.

## 8. Import and EGL Smoke
Habitat-Sim imports from the new environment. With `CUDA_VISIBLE_DEVICES=1`
and in-process GPU id 0, headless EGL used an NVIDIA RTX 4090 successfully.

## 9. Frozen Replica Scene
`apartment_0` is frozen by the complete-eligible-scenes, alphabetical-first
rule. It was not changed after smoke.

## 10. Scene and Texture Contract
No downloaded official stage or dataset JSON exists. The allowed priority-3
official textured `mesh.ply` path and its 32 texture files passed the contract;
no manual scene configuration was generated.

## 11. Navmesh and Pathfinder Contract
The official `habitat/mesh_semantic.navmesh` loaded with the selected scene and
returned a finite navigable point. The semantic mesh was not used as the
textured render scene.

## 12. Formal Rendering Protocol
No inherited frozen Replica trajectory, seed, selection manifest, pose
convention, or train/eval split exists in the baseline. This task does not
invent one.

## 13. Formal RGB-D Output
No formal RGB-D frames were generated; the renderer smoke was one validation
frame only and no image assets are committed.

## 14. Metric Transform Validation
Not executable because formal poses and `transforms.json` were not authorized.

## 15. Train/Eval Readiness
Not ready. The missing frozen render protocol blocks the 300-frame dataset and
therefore any fixed Splatfacto training task.

## 16. TUM Immutability
The external TUM `transforms.json` SHA-256 stayed
`b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a`.

## 17. Negative and Neutral Evidence
The v1 Python 3.12 failure remains valid. The optional semantic descriptor
warning did not prevent the RGB/depth smoke; it is not evidence of
preprocessing or generalization.

## 18. Decision
`blocked_by_missing_frozen_replica_render_protocol`. The Python 3.9 renderer
closure passed, but formal Replica metric preprocessing has not been run.

## 19. Fixed Splatfacto Training Entry Conditions
First freeze and review the missing trajectory, seed, frame-selection,
coordinate, and split contract. Then render exactly 300 RGB-D frames and
validate the resulting metric transforms in a separate task.

## 20. Claim Boundaries
No GSplat or Splatfacto training, no Gaussian reconstruction, no SAFER loader
evaluation, and no SAFER baseline execution occurred. Renderer success is not
cross-dataset generalization.
