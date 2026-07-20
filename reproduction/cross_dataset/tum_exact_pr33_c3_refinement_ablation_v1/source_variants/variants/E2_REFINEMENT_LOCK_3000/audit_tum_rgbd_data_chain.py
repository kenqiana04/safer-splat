"""Read-only TUM RGB-D association, encoding, intrinsics, and pose audit.

The executed server copy writes only task-owned JSON/CSV artifacts and checks
all 300 frame records, uint16 depth encoding, camera poses, and fixed adjacent
reprojections.  It never edits DATA_ROOT or transforms.json.
"""
from pathlib import Path

DATA_ROOT = Path("/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room")
DEPTH_UNIT_SCALE = 0.0002
FIXED_PAIRS = ((0, 1), (12, 13), (24, 25), (48, 49), (100, 101), (150, 151), (200, 201), (250, 251), (298, 299))
