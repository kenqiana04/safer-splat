"""Frozen identities and non-tunable task constants."""
from pathlib import Path

TASK_NAME = "BUILD_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1"
TASK_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TASK_ROOT.parents[2]
BRANCH = "replica-gt-executable-safety-activated-benchmark-v1"
BASE_BRANCH = "fas-cbf-unified-executable-safety-certifier-v1"
PR84 = 84
PR84_HEAD = "04ebca2b1b35124ad0e61ebed96e491c9edae4bb"
PR84_BASE = "17805e67b75412dc21b1a5fff4143ea3bc985f7f"
PR84_REPORT_SHA256 = "d22943d8302d344b1c588ac0fb07f5b1aa5a29caa55c08af9eca6a29ce6b1cd3"

SERVER = "zlab-4090"
SERVER_TASK_ROOT = "/disk1/zlab/maintenance_records/replica_gt_executable_safety_activated_benchmark_v1"
MAP_ROOT = "/disk1/zlab/cross_dataset_assets/qualified_replica_gaussian_safety_maps_v1/bounded_direct_goal_v1"
ROUTE_REGISTRY = "/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1/route_registry/replica_bounded_direct_goal_route_registry.json"
START_REGISTRY = "/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1/start_state_registry/replica_start_safe_diagnostic_registry.json"
REFERENCE_MESH = "/disk1/zlab/cross_dataset_assets/raw/replica/replica_v1/apartment_0/mesh.ply"
MESH_ORACLE = "/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1/tmp/replica_mesh_oracle_backend"
MESH_ORACLE_VALIDATION = "/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1/mesh_oracle/replica_mesh_collision_oracle_validation.json"

EXPECTED_MAP = {
    "means_world_m.npy": "e2ca0533767590c0b5ca657ec7f73fd4626a5fbaf07beb2ce76c2c67d1dc4152",
    "scales_linear_m.npy": "d81393a0ede4126a18b49fc9e12cca7476ca665c55fce05242b02766589c59e3",
    "quaternions_wxyz.npy": "a646a65b6665b4f09e7b295172045236eb40934202d5ef19481e963d591d56e1",
    "opacities_probability.npy": "953ed306a6860660568a0e649d1db0dc53fcf33ddbd2d003876682566572f492",
    "colors_rgb.npy": "1e8c6d97d066a269261d620c87841dabe42f2301ed5626449e0c24a237b9554e",
    "voxel_indices_int64.npy": "8e452be734959793f15b2dc9da796ff2f6d702cb03a88d76eb97566ca9b077f0",
}
MAP_SNAPSHOT_ID = "3b318a98a454ec5c36410b3c41dfb3dd4a25b7b5a1899f1f2c939fbf24ad0e55"
ROUTE_SHA256 = "ffe0dadd2dcf4de7e0011a9e3ff6bb1170a385957486ffca33832fc90cc355a6"
START_SHA256 = "e58cd9de67928ddc22f493f1eaf182044ac7e009656f092dacea42b6aaceb499"
REFERENCE_MESH_SHA256 = "274677d9b7caa413230363b68f4aa472e5cc1afe87e422a489fa1b7d844c6182"

NORMATIVE_MODEL = "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1"
DT = 0.05
U_BOUND = 0.1
V_BOUND = 0.1
ROBOT_RADIUS = 0.1
MARGIN = 0.01
TERMINAL_TOLERANCE = 1.0e-12
H_STOP_MAX = 20
SEED = 20260806
CANDIDATE_SEARCH_LIMIT = 300000

BLOCK_STATUS = "BLOCKED_BY_METHOD_FAIRNESS_CONTRACT_MISMATCH"
BLOCK_DECISION = "RECONCILE_REPLICA_GT_ACTIVATED_BENCHMARK_METHOD_CONTRACT"
BLOCK_NEXT = "FREEZE_REPLICA_GT_EXECUTABLE_SAFETY_METHOD_MATRIX_V1"
