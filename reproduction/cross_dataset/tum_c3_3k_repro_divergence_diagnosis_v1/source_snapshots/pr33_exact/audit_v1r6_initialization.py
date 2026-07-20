"""Read-only source/config audit for the frozen V1R6 initialization path."""
from pathlib import Path

V1R6_CONFIG = Path("/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1r6/splatfacto/20260717_070309/config.yml")

# Evidence recorded in initialization_audit_summary.json: metadata lacks
# points3D_xyz/RGB, so SplatfactoModel.populate_modules takes its random branch.
