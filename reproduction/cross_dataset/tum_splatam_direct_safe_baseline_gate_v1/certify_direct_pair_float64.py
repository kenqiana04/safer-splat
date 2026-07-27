"""The complete deterministic gate invokes float64 pair certification."""

from gate_core import run_geometry_gate


if __name__ == "__main__":
    print(run_geometry_gate()["certification"]["direct_safe_pair_qualified_count"])
