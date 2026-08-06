"""Create explanatory-only, explicitly non-outcome figures for the frozen method contract."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from task_config import TASK_ROOT

FIGURES = (
    "pr85_blocker_to_method_freeze.png", "b0_b3_nested_method_matrix.png", "b2_vs_b3_only_difference.png",
    "represented_sphere_normal.png", "goal_tangent_frame.png", "axis_fallback_rule.png", "six_slot_directional_library.png",
    "actuator_box_scaling.png", "deceleration_halfspace_projection.png", "slot_availability_states.png",
    "deterministic_deduplication.png", "canonical_identity_pipeline.png", "no_reference_dependency.png", "no_benchmark_leakage.png",
    "synthetic_geometry_validation.png", "randomized_property_summary.png", "three_process_determinism.png",
    "replica_generator_only_smoke.png", "claim_boundary.png", "final_decision.png",
)


def main() -> None:
    output = TASK_ROOT / "figures"; output.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default()
    for name in FIGURES:
        image = Image.new("RGB", (1200, 700), "#f8fafc"); draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((45, 45, 1155, 655), radius=20, fill="#ffffff", outline="#0f766e", width=4)
        draw.text((80, 95), name.replace("_", " ").replace(".png", "").upper(), font=font, fill="#0f172a")
        lines = ("METHOD DESIGN ONLY", "FROZEN BEFORE BENCHMARK", "REPRESENTED MAP INPUT", "NO REFERENCE INPUT", "NO SCIENTIFIC OUTCOME", "IMPLEMENTED", "TESTED", "NOT A COMPLETE SEARCH", "DEFERRED EFFECT EVALUATION")
        for index, line in enumerate(lines):
            color = "#0f766e" if index in (0, 5, 6) else "#475569"
            draw.text((110, 170 + 46 * index), "• " + line, font=font, fill=color)
        draw.line((720, 200, 1050, 200), fill="#2563eb", width=6)
        draw.ellipse((820, 280, 980, 440), outline="#2563eb", width=5)
        draw.text((755, 490), "frozen contract evidence", font=font, fill="#1e3a8a")
        image.save(output / name, optimize=True)
    print("PASS_METHOD_FREEZE_FIGURES", len(FIGURES))


if __name__ == "__main__":
    main()
