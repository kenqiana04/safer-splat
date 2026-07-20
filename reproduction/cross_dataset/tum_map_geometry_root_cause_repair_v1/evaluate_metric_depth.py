"""Evaluate all fixed eval frames in raw meters with no scale alignment."""
METRICS = ("valid_overlap", "AbsRel", "SqRel", "RMSE", "RMSE_log", "delta1", "delta2", "delta3", "median_predicted_over_gt_ratio")
NO_ALIGNMENT = "no Sim(3), global scale, per-frame scale, or outcome-based frame filtering"
