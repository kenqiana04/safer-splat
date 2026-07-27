"""The complete deterministic gate freezes the registry only after certification."""

from gate_core import run_geometry_gate


if __name__ == "__main__":
    print(run_geometry_gate()["registry"]["status"])
