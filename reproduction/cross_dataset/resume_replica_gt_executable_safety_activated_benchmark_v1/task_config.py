"""Frozen identities and preregistered constants for the resumed benchmark."""
from pathlib import Path

TASK_NAME = "RESUME_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1"
TASK_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TASK_ROOT.parents[2]
BRANCH = "resume-replica-gt-executable-safety-activated-benchmark-v1"
BASE_BRANCH = "replica-gt-executable-safety-method-matrix-v1"
BASE_HEAD = "d4f20f44a810afc2d6379853a286a3e18b175221"

PR84 = 84
PR84_HEAD = "04ebca2b1b35124ad0e61ebed96e491c9edae4bb"
PR85 = 85
PR85_HEAD = "7afef38392bec36d9d9811e5a22c816da5faf1ff"
PR86 = 86
PR86_HEAD = BASE_HEAD
PR86_BASE_HEAD = PR85_HEAD

LIBRARY_ID = "REPLICA_GT_REPRESENTED_MAP_DIRECTIONAL_ALTERNATIVE_LIBRARY_V1"
LIBRARY_SHA256 = "3d491876234161d4e881ec1227c505cb07c0af00d5e881c5289fdf1f1577c6fe"
LIBRARY_SOURCE = "TASK_LOCAL_REPRESENTED_MAP_DIRECTIONAL_V1"
SLOT_IDS = (
    "ALT-01-OUTWARD",
    "ALT-02-GOAL-TANGENT",
    "ALT-03-AUX-TANGENT-POS",
    "ALT-04-AUX-TANGENT-NEG",
    "ALT-05-BRAKE-BIASED-GOAL-TANGENT",
    "ALT-06-BRAKE-BIASED-OUTWARD",
)
DEDUP_ABS_TOL = 1.0e-12
NORMAL_EPSILON = 1.0e-12
ORTHOGONALITY_TOL = 1.0e-10

MAP_SNAPSHOT_ID = "3b318a98a454ec5c36410b3c41dfb3dd4a25b7b5a1899f1f2c939fbf24ad0e55"
REFERENCE_MESH_SHA256 = "274677d9b7caa413230363b68f4aa472e5cc1afe87e422a489fa1b7d844c6182"
ROUTE_SHA256 = "ffe0dadd2dcf4de7e0011a9e3ff6bb1170a385957486ffca33832fc90cc355a6"
START_SHA256 = "e58cd9de67928ddc22f493f1eaf182044ac7e009656f092dacea42b6aaceb499"

SERVER = "zlab-4090"
SERVER_TASK_ROOT = "/disk1/zlab/maintenance_records/resume_replica_gt_executable_safety_activated_benchmark_v1"
SERVER_PYTHON = "/disk1/zlab/conda_envs/safer_splat_official/bin/python"
MAP_ROOT = "/disk1/zlab/cross_dataset_assets/qualified_replica_gaussian_safety_maps_v1/bounded_direct_goal_v1"
ROUTE_REGISTRY = "/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1/route_registry/replica_bounded_direct_goal_route_registry.json"
START_REGISTRY = "/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1/start_state_registry/replica_start_safe_diagnostic_registry.json"
REFERENCE_MESH = "/disk1/zlab/cross_dataset_assets/raw/replica/replica_v1/apartment_0/mesh.ply"
MESH_ORACLE = "/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1/tmp/replica_mesh_oracle_backend"
MESH_ORACLE_VALIDATION = "/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1/mesh_oracle/replica_mesh_collision_oracle_validation.json"

MAP_FILES = {
    "means_world_m.npy": "e2ca0533767590c0b5ca657ec7f73fd4626a5fbaf07beb2ce76c2c67d1dc4152",
    "scales_linear_m.npy": "d81393a0ede4126a18b49fc9e12cca7476ca665c55fce05242b02766589c59e3",
    "quaternions_wxyz.npy": "a646a65b6665b4f09e7b295172045236eb40934202d5ef19481e963d591d56e1",
    "opacities_probability.npy": "953ed306a6860660568a0e649d1db0dc53fcf33ddbd2d003876682566572f492",
    "colors_rgb.npy": "1e8c6d97d066a269261d620c87841dabe42f2301ed5626449e0c24a237b9554e",
    "voxel_indices_int64.npy": "8e452be734959793f15b2dc9da796ff2f6d702cb03a88d76eb97566ca9b077f0",
}

NORMATIVE_MODEL = "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1"
DT = 0.05
U_BOUND = 0.1
V_BOUND = 0.1
ROBOT_RADIUS = 0.1
MARGIN = 0.01
EFFECTIVE_RADIUS = ROBOT_RADIUS + MARGIN
TERMINAL_TOLERANCE = 1.0e-12
H_STOP_MAX = 20
CERTIFIER_TIME_BUDGET_S = 30.0
DEADLINE_S = DT

SEED = 20260806
CANDIDATE_SEARCH_SMOKE_LIMIT = 5000
CANDIDATE_SEARCH_LIMIT = 300000
VELOCITY_MAGNITUDES = (0.0, 0.025, 0.05, 0.075, 0.1)
ROUTE_FRACTIONS = (0.0, 0.25, 0.5, 0.75)
# Frozen before search. Values probe the represented-sphere surface neighborhood
# without consulting any method or reference outcome.
SURFACE_CLEARANCE_OFFSETS_M = (-0.00002, 0.0, 0.00002, 0.0001, 0.0005, 0.001, 0.0025, 0.005, 0.01, 0.02, 0.05)
SURFACE_TANGENT_OFFSETS_M = (-0.0025, 0.0, 0.0025)
PHYSICAL_MIN_CLEARANCE_M = ROBOT_RADIUS

GROUP_TARGETS = {"G0": 20, "G1": 20, "G2": 20, "G3": 20, "G4": 10, "G5": 10}
GROUP_MINIMUMS = {"G0": 12, "G1": 12, "G2": 8, "G3": 12, "G4": 5, "G5": 5}
GROUP_PRIORITY = ("G5", "G4", "G1", "G3", "G2", "G0")
ACTIVATED_TARGET = 100
REPRESENTATIVE_TARGET = 160
REPRESENTATIVE_ROLLOUT_SUBSET = 80
ACTIVATED_ROLLOUT_MAX_STEPS = 10
REPRESENTATIVE_ROLLOUT_MAX_STEPS = 5
GOAL_POSITION_TOLERANCE_M = 0.03
GOAL_VELOCITY_TOLERANCE_MPS = 0.03

METHODS = (
    "B0_CURRENT_CBF_ONLY",
    "B1_PLUS_SWEPT_SEGMENT",
    "B2_PLUS_TERMINAL_BACKUP",
    "B3_FULL_UNIFIED_WITH_DIRECTIONAL_ALTERNATIVES",
)

PASS_VALIDATOR = "PASS_RESUMED_REPLICA_GT_EXECUTABLE_SAFETY_BENCHMARK_VALIDATION"
