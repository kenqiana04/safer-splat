"""Run the preregistered TUM direct-safe geometry gate once on the server."""

from gate_core import run_geometry_gate


if __name__ == "__main__":
    result = run_geometry_gate()
    print(result["gate"]["pair_pool_gate"])
