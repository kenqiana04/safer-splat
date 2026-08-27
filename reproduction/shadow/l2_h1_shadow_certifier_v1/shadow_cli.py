"""CLI for deterministic task-local fixtures only; never a controller entry point."""
from __future__ import annotations

import argparse

from fixtures.synthetic_fixtures import conservative_case, diagnostic_context, sphere_case
from l2_h1_shadow_certifier import l2_h1_shadow_certify
from shadow_contract import load_frozen_robot_margin_contract


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one L2/H1 shadow implementation fixture")
    parser.add_argument(
        "--fixture",
        choices=("sphere-safe", "sphere-intersection", "sphere-endpoint-trap", "conservative-safe", "conservative-intersection", "conservative-budget"),
        required=True,
    )
    parser.add_argument("--diagnostic-samples", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.fixture.startswith("sphere-"):
        fixture = sphere_case(args.fixture.removeprefix("sphere-"))
    else:
        fixture = conservative_case(args.fixture.removeprefix("conservative-"))
    state, candidate, snapshot, context = fixture
    if args.diagnostic_samples:
        if args.diagnostic_samples < 2:
            raise SystemExit("diagnostic samples must be >= 2")
        context = diagnostic_context(context, args.diagnostic_samples)
    result = l2_h1_shadow_certify(state, candidate, snapshot, context, load_frozen_robot_margin_contract())
    print(result.to_json())


if __name__ == "__main__":
    main()
