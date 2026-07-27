"""The complete deterministic gate invokes this endpoint-inventory stage."""

from gate_core import run_geometry_gate


if __name__ == "__main__":
    print(run_geometry_gate()["endpoints"]["status"])
