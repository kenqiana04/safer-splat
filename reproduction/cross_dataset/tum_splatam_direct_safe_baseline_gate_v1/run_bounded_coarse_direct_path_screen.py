"""The complete deterministic gate invokes the bounded coarse screen."""

from gate_core import run_geometry_gate


if __name__ == "__main__":
    print(run_geometry_gate()["coarse"]["coarse_clear_count"])
