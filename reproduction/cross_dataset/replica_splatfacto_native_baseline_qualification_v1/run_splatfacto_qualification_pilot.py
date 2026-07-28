#!/usr/bin/env python3
"""Run exactly one full-budget 60-frame scientific qualification pilot."""
from __future__ import annotations

from run_splatfacto_smoke import _run


if __name__ == "__main__":
    raise SystemExit(_run("qualification_pilot", "SPLATFACTO_PILOT_COMPLETE", "SPLATFACTO_PILOT"))
