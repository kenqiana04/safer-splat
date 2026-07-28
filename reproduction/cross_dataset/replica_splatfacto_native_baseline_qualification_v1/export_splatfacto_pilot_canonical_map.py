#!/usr/bin/env python3
"""Entrypoint for the one permitted qualification-pilot canonical export."""
from export_splatfacto_smoke_canonical_map import _export


if __name__ == "__main__":
    raise SystemExit(_export("qualification_pilot"))
