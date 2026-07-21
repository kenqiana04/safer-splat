"""Validate the frozen factor-effect interpretation generated from 6K evidence."""
from __future__ import annotations
import json
from pathlib import Path

root = Path(__file__).parent
data = json.loads((root / "tuned_surface_factor_analysis.json").read_text(encoding="utf-8"))
assert data["surface_loss_effect"] == "BENEFICIAL_AND_SELECTED_BY_FROZEN_B_SCREEN"
print("FACTOR_EFFECT_ANALYSIS_PASS")
