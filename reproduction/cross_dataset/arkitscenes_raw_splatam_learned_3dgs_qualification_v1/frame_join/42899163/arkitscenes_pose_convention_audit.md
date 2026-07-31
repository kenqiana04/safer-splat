# ARKitScenes pose and join convention audit

The frozen Apple DATA.md specifies axis-angle radians and translation in metres. The frozen Apple `TrajStringToMatrix` constructs world-to-pose then returns its inverse, therefore the joined manifest stores camera-to-world matrices. Matching uses the official loader's depth-led exact RGB/depth/confidence timestamps, intrinsic +/-1 ms fallback, and trajectory 1 ms indexing with a strict <5 ms pose tolerance; no interpolation or extrapolation.
