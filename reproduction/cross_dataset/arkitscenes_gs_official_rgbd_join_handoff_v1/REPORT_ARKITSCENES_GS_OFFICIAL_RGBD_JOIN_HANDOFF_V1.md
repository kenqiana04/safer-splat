# ARKitScenes GS Official RGB-D Join Handoff V1

## Result

`NO_ARKITSCENES_GS_TO_OFFICIAL_RGBD_FRAME_JOIN`

`CLOSE_PUBLIC_PRETRAINED_EXTERNAL_MAP_SEARCH`

The prior Hypersim direct-component route was closed because it could not provide frozen held-out RGB and GT-geometry payload identities. ARKitScenes was the bounded final public route. The component-specific access gate subsequently passed, but the immutable training-frame join gate did not.

## PR #61 corrected lineage

- PR #61 remains Open Draft, mergeable CLEAN, at `fefaf472831026ebc228c2745f61d2eb4ebfad52`.
- Its body records the verified Hypersim no-candidate result; historical evidence was not rewritten.

## Authorities and access

- SceneSplat metadata: `GaussianWorld/scene_splat_7k` at `685f9e9053b8dcc2a23100eb52f64ee4711b0875`.
- The frozen `ARKitScenesGS` link resolves uniquely to `SceneSplatPro/arkitscenes_mcmc_3dgs_new` at `39d3078f6bcebfc01a983422d6da3eaa3034aa23`.
- The same authenticated account can now read the component's gated `.gitattributes`; no legacy `GaussianWorld` repository was substituted.
- Apple authority was frozen at `7283761bf26c27570ec59a5dc0f8686fbff07726`. Its DATA.md documents single-video raw downloads, millimetre uint16 depth PNG, metre trajectory translations, intrinsics, and mesh assets. The official download script was inspected but never executed.

## Exact candidate and frame gates

- The frozen ARKitScenes statistics contain 1,627 rows; the resource-range ranking produced ten candidates.
- All ten scene IDs map exactly once to Apple raw split video IDs and all ten component prechecks found the expected PLY, transforms, and stats metadata.
- Every one of those ten `transforms_train.json` files has exactly one training frame. The protocol minimum is 20 exact training correspondences and a join ratio of 0.80.
- Therefore no Apple frame was guessed or matched from a preview, no fixed SE(3) was estimated, and no scale/Sim(3)/ICP operation occurred.

## Preserved boundaries

No Gaussian PLY, Apple video, RGB, depth, pose, mesh, or archive payload was downloaded. Primary and backup remain null; held-out selection, download planning, materialization, package validation, and server transfer are not authorized. Map training/modification, canonical export, geometry evaluation, SAFER, navigation, CBF-QP, and TUM operations are all zero.

## Sole continuation

`REDEFINE_CROSS_DATASET_VALIDATION_PROTOCOL_V1`. This route is closed; it must not be bypassed by using one transform frame, a guessed frame timestamp, a preview, ICP, Sim(3), or an alternative public dataset.
