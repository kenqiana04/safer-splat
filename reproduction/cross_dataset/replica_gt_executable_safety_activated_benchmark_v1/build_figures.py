"""Generate explicit presearch-blocker figures without fabricating benchmark data."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from task_config import BLOCK_STATUS, TASK_ROOT

FIGURES = {
    "benchmark_scope_and_claim_boundary.png": ("Scope and claim boundary", ["Candidate-level paired benchmark", "Blocked before candidate generation", "No performance or safety comparison"]),
    "nested_method_matrix.png": ("Nested B0-B3 method matrix", ["B0-B2 inputs are definable", "B3 requires concrete frozen alternatives", "PR84 freezes order only"]),
    "scenario_generation_pipeline.png": ("Scenario pipeline", ["Identity freeze: PASS", "Method fairness: BLOCKED", "Candidate generation: NOT STARTED"]),
    "stage_predicate_funnel.png": ("Stage-predicate funnel", ["Candidate tuples: 0", "Stage predicates: 0", "Registry states: 0"]),
    "group_activation_counts.png": ("G0-G5 activation counts", ["G0=G1=G2=G3=G4=G5=0", "Counts are not scientific outcomes", "Fairness gate preceded search"]),
    "registry_composition.png": ("Registry composition", ["Registry not created", "No state selected or replaced", "No future reference read"]),
    "endpoint_vs_swept_segment_examples.png": ("Endpoint vs swept segment", ["No examples evaluated", "Gate evidence unavailable", "No implied H1 result"]),
    "primary_backup_fail_examples.png": ("Primary backup failures", ["No examples evaluated", "Gate evidence unavailable", "No implied H2 result"]),
    "alternative_rescue_examples.png": ("Alternative rescue", ["B3 library content undefined", "No rescue trial executed", "No implied H3 result"]),
    "terminal_state_examples.png": ("Terminal semantics", ["No terminal state evaluated", "NO_CERTIFIED_ACTION is not SAFE_STOP", "Upstream contract preserved"]),
    "one_step_status_matrix.png": ("One-step status matrix", ["Method runs: 0", "No status frequencies", "Formal attempt: 0"]),
    "commit_rate_by_group.png": ("Commit rate by group", ["Not estimable", "No registry denominator", "Do not interpret as zero rate"]),
    "fail_closed_reason_by_group.png": ("Fail-closed reasons", ["Scientific fail-closed count: 0", "Task blocked by method contract", "Not a robot safe-stop result"]),
    "alternative_selection_by_group.png": ("Alternative selection", ["Not estimable", "Alternative library identity missing", "No candidate was run"]),
    "represented_segment_bounds.png": ("Represented-map segment bounds", ["No benchmark query", "PR84 backend identity frozen", "No represented false-safe trial"]),
    "reference_swept_collision_by_method.png": ("Offline reference collision", ["Reference queries: 0", "Registry never locked", "No collision comparison"]),
    "map_reference_disagreement.png": ("Map-reference disagreement", ["Not evaluated", "No disagreement count from trials", "Representation and reference remain distinct"]),
    "progress_by_method_group.png": ("Logical-time progress", ["Episodes: 0", "Control steps: 0", "No progress comparison"]),
    "logical_rollout_terminal_reasons.png": ("Logical rollout terminal reasons", ["No rollout executed", "No terminal reasons", "Not a real-time experiment"]),
    "runtime_component_breakdown.png": ("Runtime components", ["No decision timed", "No runtime estimate", "PR84 p95 is upstream evidence only"]),
    "deadline_miss_rate.png": ("50 ms deadline audit", ["Decision count: 0", "Miss rate not estimable", "No real-time claim"]),
    "paired_effect_sizes.png": ("Paired effect sizes", ["H1-H5 not tested", "No state-level pairs", "No p-values or confidence intervals"]),
    "false_safe_and_false_reject_summary.png": ("Certificate consistency", ["Benchmark trials: 0", "No false-safe observation", "Do not infer a zero risk rate"]),
    "gate_causal_attribution.png": ("Gate causal attribution", ["B1/B2 definitions available", "B3 comparison undefined", "Causal benchmark not executed"]),
    "final_decision.png": ("Final decision", [BLOCK_STATUS, "Reconcile and freeze B3 inputs", "Then rebuild the method matrix"]),
}


def font(size: int):
    candidates = [Path("C:/Windows/Fonts/segoeui.ttf"), Path("C:/Windows/Fonts/arial.ttf")]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def main() -> None:
    output = TASK_ROOT / "figures"
    output.mkdir(parents=True, exist_ok=True)
    title_font, body_font, small_font = font(34), font(24), font(18)
    for name, (title, lines) in FIGURES.items():
        image = Image.new("RGB", (1200, 700), "#f8fafc")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 1200, 88), fill="#7f1d1d")
        draw.text((42, 24), "BLOCKED PRESEARCH — NO SCIENTIFIC RESULT", font=title_font, fill="white")
        draw.text((55, 140), title, font=title_font, fill="#0f172a")
        y = 230
        for line in lines:
            draw.rounded_rectangle((70, y, 1130, y + 82), radius=14, fill="#fee2e2", outline="#ef4444", width=2)
            draw.text((98, y + 24), line, font=body_font, fill="#450a0a")
            y += 108
        draw.text((55, 650), "Layer: STRUCTURAL LIMIT / METHOD FAIRNESS AUDIT", font=small_font, fill="#475569")
        image.save(output / name, optimize=True)
    print("PASS_BLOCKER_FIGURE_BUILD", len(FIGURES))


if __name__ == "__main__":
    main()
