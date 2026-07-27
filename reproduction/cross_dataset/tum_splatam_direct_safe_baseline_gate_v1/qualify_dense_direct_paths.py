"""The complete deterministic gate invokes dense qualification after coarse screening."""

from gate_core import run_geometry_gate


if __name__ == "__main__":
    print(run_geometry_gate()["dense"]["dense_sample_clear_candidate_count"])
