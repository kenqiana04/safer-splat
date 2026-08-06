"""Immutable configuration for the method-design-only freeze."""
from pathlib import Path

TASK_NAME = "FREEZE_REPLICA_GT_EXECUTABLE_SAFETY_METHOD_MATRIX_V1"
TASK_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TASK_ROOT.parents[2]
BRANCH = "replica-gt-executable-safety-method-matrix-v1"
BASE_BRANCH = "replica-gt-executable-safety-activated-benchmark-v1"
PR85 = 85
PR85_HEAD = "7afef38392bec36d9d9811e5a22c816da5faf1ff"
PR85_BASE = "04ebca2b1b35124ad0e61ebed96e491c9edae4bb"
PR85_REPORT_SHA256 = "823bd790c125f0db8c4dfd5dd2491e387727769e3f14542bf5c5d6378e066fd4"
PR84 = 84
PR84_HEAD = "04ebca2b1b35124ad0e61ebed96e491c9edae4bb"

SERVER = "zlab-4090"
SERVER_TASK_ROOT = "/disk1/zlab/maintenance_records/replica_gt_executable_safety_method_matrix_v1"
MAP_ROOT = "/disk1/zlab/cross_dataset_assets/qualified_replica_gaussian_safety_maps_v1/bounded_direct_goal_v1"
ROUTE_REGISTRY = "/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1/route_registry/replica_bounded_direct_goal_route_registry.json"
START_REGISTRY = "/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1/start_state_registry/replica_start_safe_diagnostic_registry.json"
REFERENCE_MESH = "/disk1/zlab/cross_dataset_assets/raw/replica/replica_v1/apartment_0/mesh.ply"

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

LIBRARY_ID = "REPLICA_GT_REPRESENTED_MAP_DIRECTIONAL_ALTERNATIVE_LIBRARY_V1"
LIBRARY_VERSION = 1
LIBRARY_SOURCE = "TASK_LOCAL_REPRESENTED_MAP_DIRECTIONAL_V1"
SLOT_IDS = (
    "ALT-01-OUTWARD", "ALT-02-GOAL-TANGENT", "ALT-03-AUX-TANGENT-POS",
    "ALT-04-AUX-TANGENT-NEG", "ALT-05-BRAKE-BIASED-GOAL-TANGENT",
    "ALT-06-BRAKE-BIASED-OUTWARD",
)
NORMAL_EPSILON = 1.0e-12
DEDUP_ABS_TOL = 1.0e-12
ORTHOGONALITY_TOL = 1.0e-10
DT = 0.05
U_BOUND = 0.1
V_BOUND = 0.1
ROBOT_RADIUS = 0.1
MARGIN = 0.01
TERMINAL_TOLERANCE = 1.0e-12
H_STOP_MAX = 20
PROPERTY_SEED = 20260806
SYNTHETIC_GEOMETRY_CASES = 20_000
AXIS_DEGENERATE_CASES = 5_000
PROJECTION_CASES = 5_000
SERIALIZATION_CASES = 5_000
SMOKE_STATE_COUNT = 25

PASS_STATUS = "PASS_REPLICA_GT_EXECUTABLE_SAFETY_METHOD_MATRIX_FREEZE_V1"
PASS_VALIDATION = "PASS_REPLICA_GT_EXECUTABLE_SAFETY_METHOD_MATRIX_FREEZE_VALIDATION"
PASS_DECISION = "RESUME_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK"
PASS_NEXT = "RESUME_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1"
