"""Resolved at task execution time from the frozen official parent config."""

# This file is a declarative template.  build_runtime.py writes exact smoke and
# formal configs after checking the parent identity and allowed diff whitelist.
TASK = "ARKITSCENES_SPLATAM_M1_EMPTY_DEPTH_SAFE_GT_POSE_MAP_ONLY_V1"
SCENE = "48018874"
SEED = 20260730
TRAIN_ROWS = 214
SMOKE_A = (0, 12)
SMOKE_B = (70, 83)
MASK_CONTRACT = "DEPTH_GT_ZERO_AND_CONFIDENCE_GE1"

