"""The complete deterministic gate invokes candidate construction after inventory."""

from gate_core import run_geometry_gate


if __name__ == "__main__":
    print(run_geometry_gate()["candidates"]["total_candidate_count"])
