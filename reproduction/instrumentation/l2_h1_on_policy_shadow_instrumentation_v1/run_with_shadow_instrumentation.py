"""Outer wrapper for a future equivalence task; never run by this task.

The protected controller file is executed in place through `runpy`. Its imported
CBF symbol is temporarily decorated, then restored. No controller source is
copied or modified.
"""

from __future__ import annotations

import argparse
import importlib
import runpy
from pathlib import Path

from instrumented_cbf_wrapper import InstrumentedCBFFactory
from lifecycle import ShadowInstrumentationLifecycle


def execute_protected_run(
    *,
    run_path: Path,
    lifecycle: ShadowInstrumentationLifecycle,
    run_id: str,
    dt: float,
) -> tuple[dict, object]:
    cbf_module = importlib.import_module("cbf.cbf_utils")
    dynamics_module = importlib.import_module("dynamics.systems")
    original_cbf = cbf_module.CBF
    original_plant = dynamics_module.double_integrator_dynamics
    factory = InstrumentedCBFFactory(original_cbf, lifecycle=lifecycle, run_id=run_id, dt=dt)
    cbf_module.CBF = factory
    dynamics_module.double_integrator_dynamics = factory.decorate_plant(original_plant)
    try:
        globals_after_run = runpy.run_path(str(run_path), run_name="__main__")
    finally:
        cbf_module.CBF = original_cbf
        dynamics_module.double_integrator_dynamics = original_plant
        factory.flush_capture_errors()
    return globals_after_run, factory


def main() -> int:
    parser = argparse.ArgumentParser(description="Future-only protected-controller wrapper")
    parser.add_argument("--dry-run", action="store_true", help="validate invocation without executing navigation")
    args = parser.parse_args()
    if not args.dry_run:
        parser.error("real execution is intentionally unavailable in this task; use --dry-run")
    print("DRY_RUN_ONLY_NO_NAVIGATION_EXECUTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
