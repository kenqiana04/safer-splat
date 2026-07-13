# Cross-Dataset Scene Adapter Contract

An adapter is declarative scene metadata, not a controller extension. It may provide the asset path, coordinate transform, scale transform, scene bounds, start/goal regions, and an optional independent geometry checker.

It must not modify or wrap the CBF equations, nominal controller, dynamics, QP solver, Gaussian safety query, stopping criteria, or any baseline parameter. It must not select a transform, region, or radius after inspecting navigation results, and it must not invoke a planner.

Each adapter exports `SCENE_ADAPTER`, a dictionary with these required keys:

```python
SCENE_ADAPTER = {
    "candidate_id": "verified_candidate_id",
    "checkpoint_path": "/absolute/or/repo-relative/path",
    "coordinate_transform": {"matrix_4x4": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], "source": "metadata reference"},
    "scale_transform": {"scene_units_per_meter": 1.0, "status": "metric", "source": "dataset reference"},
    "bounds": {"min_xyz": [-1, -1, -1], "max_xyz": [1, 1, 1]},
    "start_region": {"min_xyz": [-0.8, -0.8, -0.8], "max_xyz": [-0.2, -0.2, -0.2]},
    "goal_region": {"min_xyz": [0.2, 0.2, 0.2], "max_xyz": [0.8, 0.8, 0.8]},
    "minimum_start_goal_separation": 0.5,
    "geometry_checker": None,
}
```

The source fields must identify provenance evidence, not merely a directory name.
