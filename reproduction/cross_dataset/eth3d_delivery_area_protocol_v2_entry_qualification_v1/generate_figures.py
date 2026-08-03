#!/usr/bin/env python3
"""Generate twenty source-backed, metadata-only Protocol V2 diagrams."""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


FIGURES = {
    "eth3d_benchmark_identity.png": ("Benchmark identity", "Do not conflate ETH3D benchmark families", [("MVS / 3D reconstruction", "Delivery Area training scene\nDSLR 44 + rig 4 x 237\nLaser-scan evaluation reference", "#D8EAFE"), ("Not SLAM RGB-D", "Separate ETH3D benchmark\nVI / stereo / RGB-D sequences\nDifferent dataset namespace", "#FDE4E1"), ("Frozen conclusion", "DATASET_FAMILY:\nETH3D_MULTI_VIEW_STEREO", "#DCFCE7")]),
    "delivery_area_variant_comparison.png": ("Delivery Area variants", "Pretrained-result-free modality comparison", [("Low-res rig", "948 images / 237 captures\n4 synchronized cameras\nSelected future mapping input", "#D8EAFE"), ("High-res DSLR", "44 indoor images\nDifferent camera modality\nCross-view evaluation only", "#EDE9FE"), ("Shared reference", "scan_clean / scan_eval\nocclusion / rendered depth\nNever mapping input", "#FEF3C7")]),
    "official_asset_role_matrix.png": ("Official asset roles", "One immutable access class per archive", [("TRAIN", "rig_undistorted only\nRGB + official poses\nMAPPING_INPUT_ONLY", "#DCFCE7"), ("EVAL / ORACLE", "scan_eval, scan_clean, depth,\nocclusion, DSLR cross-view", "#D8EAFE"), ("DENIED", "raw/JPG duplicates, rig original,\nscan_raw, stereo_pairs_gt", "#FDE4E1")]),
    "train_eval_oracle_isolation.png": ("Physical isolation", "Training cannot open reference assets", [("TRAIN_INPUT_ROOT", "Rig RGB\nIntrinsics + poses\nRig grouping", "#DCFCE7"), ("One-way audit gate", "Separate mount/root\nOpen-file log\nReference access = 0", "#FEF3C7"), ("EVAL_ORACLE_ROOT", "Heldout RGB\nDepth / scans\nOcclusion", "#D8EAFE")]),
    "gt_depth_leakage_boundary.png": ("GT depth leakage boundary", "Rendered depth is laser-scan-derived ground truth", [("Official pipeline", "Aligned laser scans\nOcclusion mesh + splats\nGroundTruthCreator", "#D8EAFE"), ("Rendered depth", "HELDOUT EVALUATION ONLY\nObservable-ray oracle\nNever mounted for training", "#FEF3C7"), ("SplaTAM RGB-D", "REJECTED\nNo independent sensor RGB-D\nWould leak reference geometry", "#FDE4E1")]),
    "modality_selection_flow.png": ("Modality selection", "Frozen before any training result", [("M1 rig RGB-only", "Official poses + PINHOLE\nGroup split feasible\nMetadata-level PASS", "#DCFCE7"), ("Select", "LOW_RES_MANY_VIEW\nRIG_RGB_ONLY", "#D8EAFE"), ("M2 DSLR", "Keep entirely out of TRAIN\nCross-view evaluation", "#EDE9FE")]),
    "frontend_selection_flow.png": ("Frontend selection", "No post-result fallback", [("F1 official 3DGS", "COLMAP text/binary loader\nPINHOLE supported\nSelected", "#DCFCE7"), ("F2 Splatfacto", "Historical reference only\nSeparate authorization required", "#FEF3C7"), ("F3 SplaTAM", "No legal sensor RGB-D\nInadmissible", "#FDE4E1")]),
    "rig_group_split_contract.png": ("Rig group split contract", "All four simultaneous images stay together", [("Capture t", "cam0 + cam1 + cam2 + cam3\nRIG_CAPTURE_GROUP", "#D8EAFE"), ("Deterministic spatial split", "Camera centers + neighbors\nView overlap + sensitivity\nFreeze before mapping", "#FEF3C7"), ("Prohibited", "Per-image random split\nCross-partition same pose\nResult-driven selection", "#FDE4E1")]),
    "cross_view_evaluation_design.png": ("Cross-view evaluation", "Distinct camera modality remains untouched by TRAIN", [("Rig TRAIN", "Only selected rig capture groups\nRGB + official calibration", "#DCFCE7"), ("Frozen map", "Single scene instance\nNo candidate-driven heldout", "#FEF3C7"), ("DSLR CROSS-VIEW", "All 44 RGB held out\nOwn depth/scan_eval/occlusion\nDescriptive NVS", "#EDE9FE")]),
    "reference_authority_layers.png": ("Reference authority layers", "Different questions require different official assets", [("R axis", "scan_eval + evaluator\n+ occlusion\nAccuracy/completeness/F-score", "#D8EAFE"), ("Observable rays", "Variant depth\nRisk-coverage diagnostics\nEvaluation only", "#EDE9FE"), ("Route candidate", "scan_clean + alignment\nVerified mesh/splats\nPending asset audit", "#FEF3C7")]),
    "runtime_unknown_entry_options.png": ("Runtime UNKNOWN candidates", "Reference-free deployable support only", [("U1 frustum support", "Frustum alone is not free\nMulti-view support needed", "#D8EAFE"), ("U2 free ray to surface", "Stop before first learned surface\nNever extrapolate behind", "#DCFCE7"), ("U3 visibility count", "Supports occupied evidence\nAbsence is not free", "#EDE9FE")]),
    "unknown_not_free_flow.png": ("UNKNOWN is not FREE", "Fail closed at every unsupported query", [("Mapping-time evidence", "TRAIN poses + RGB\nLearned Gaussians\nVisibility/transmittance", "#D8EAFE"), ("Knownness gate", "Distinct views + angular baseline\nConservative first surface", "#FEF3C7"), ("SAFER query", "Supported -> evaluate\nUnsupported -> UNKNOWN\nUNKNOWN -> occupied", "#FDE4E1")]),
    "robot_route_reference_separation.png": ("Robot / route separation", "Camera trajectory is not a robot route", [("Reference-only route", "Generated before mapping\nNo candidate-map access\nOpen/moderate/tight strata", "#D8EAFE"), ("Project robot", "0.10 m sphere\n6D double integrator\nOracle-state simulation", "#FEF3C7"), ("Independent oracle", "Swept-sphere collision\nCandidate cannot delete route\nNo real-robot claim", "#DCFCE7")]),
    "physical_budget_derivation_path.png": ("Physical budget path", "No arbitrary centimetre threshold", [("Reference clearance", "Verified route tube margin\nPending asset audit", "#D8EAFE"), ("Subtract uncertainty", "loc + shape + sampled\n+ stop + tracking\nloc=0 only with oracle state", "#FEF3C7"), ("Map requirement", "UpperBound[e_plus]\n<= B_map_available\nNumeric closure later", "#DCFCE7")]),
    "protocol_v2_future_evaluation.png": ("Future Protocol V2 evaluation", "Layered evidence; no universal hard gate", [("Integrity + parity", "Identity / no leakage\nNative vs common renderer\nImmutable map", "#D8EAFE"), ("Geometry + risk", "11 fixed alpha points\nOfficial multi-tolerance MVS\nDescriptive NVS", "#EDE9FE"), ("Navigation conditioned", "UNKNOWN + route tube\ne_plus + physical budget\nSwept-body oracle / G0 separate", "#DCFCE7")]),
    "stage_gate_plan.png": ("Seven-stage gate plan", "Entry cannot jump to training", [("1-2 Acquire / audit", "Bounded whitelist only\nHash, listing, pose, rig, frame\nNo environment", "#D8EAFE"), ("3-5 Freeze / qualify", "UNKNOWN + route + budget\nOfficial 3DGS environment\nNonformal smoke", "#FEF3C7"), ("6-7 Formal / evaluate", "One frozen mapping\nThen Protocol V2 qualification\nSeparate authorization", "#DCFCE7")]),
    "bounded_download_whitelist.png": ("Bounded future whitelist", "Nine archives; none downloaded now", [("Mapping: 1", "rig_undistorted\nTRAIN_INPUT_ROOT", "#DCFCE7"), ("Rig/reference: 4", "rig scan_eval / occlusion / depth\n+ scan_clean\nEVAL_ORACLE_ROOT", "#D8EAFE"), ("DSLR cross-view: 4", "undistorted / scan_eval\nocclusion / depth\nEVAL_ORACLE_ROOT", "#EDE9FE")]),
    "license_and_attribution.png": ("License and attribution", "Non-commercial academic route only", [("ETH3D data", "CC BY-NC-SA 4.0\nAttribution + share-alike\nNo commercial use", "#D8EAFE"), ("Official 3DGS", "Research/evaluation license\nNon-commercial only\nPreserve notices", "#EDE9FE"), ("Publication boundary", "No raw payload in Git\nMaps conditional on same terms\nHashes/scripts are allowed", "#FEF3C7")]),
    "final_entry_decision.png": ("Final entry decision", "All metadata-level Case A gates pass", [("Evidence gates", "Identity + assets + license\nIsolation + modality + frontend", "#D8EAFE"), ("Navigation-entry gates", "Split + reference + UNKNOWN\nRoute + physical budget + evaluator", "#EDE9FE"), ("Decision", "AUTHORIZE BOUNDED ASSET\nACQUISITION + CONTRACT AUDIT\nTraining remains unauthorized", "#DCFCE7")]),
    "claim_boundary.png": ("Claim boundary", "What this metadata-only PASS does and does not establish", [("May claim", "Possible legal GT-pose\nRGB-only map-only route\nBounded acquisition may follow", "#DCFCE7"), ("Still pending", "Asset integrity + split\nReference / UNKNOWN / route / budget\nEnvironment + smoke", "#FEF3C7"), ("Must not claim", "Qualified map or navigation\nFull SLAM / RGB-D / real robot\nAny R/N grade or training authority", "#FDE4E1")]),
}


def font(size: int, bold: bool = False):
    candidates = [
        Path("C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def multiline(draw, xy, text, fnt, fill, width, spacing=12):
    wrapped = []
    for line in text.splitlines():
        wrapped.extend(textwrap.wrap(line, width=width) or [""])
    draw.multiline_text(xy, "\n".join(wrapped), font=fnt, fill=fill, spacing=spacing)


def render(path: Path, title: str, subtitle: str, cards):
    image = Image.new("RGB", (1600, 900), "#F8FAFC")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1600, 150), fill="#102A43")
    draw.text((80, 36), title, font=font(44, True), fill="white")
    draw.text((82, 98), subtitle, font=font(24), fill="#CFE8FF")
    x_positions = [75, 570, 1065]
    for index, ((heading, body, color), x) in enumerate(zip(cards, x_positions)):
        draw.rounded_rectangle((x, 210, x + 455, 650), radius=26, fill=color, outline="#486581", width=3)
        draw.ellipse((x + 28, 238, x + 82, 292), fill="#102A43")
        draw.text((x + 47, 248), str(index + 1), font=font(24, True), fill="white", anchor="mm")
        multiline(draw, (x + 34, 320), heading, font(30, True), "#102A43", 23, 8)
        multiline(draw, (x + 34, 400), body, font(24), "#243B53", 29, 13)
        if index < 2:
            draw.line((x + 460, 430, x + 485, 430), fill="#486581", width=6)
            draw.polygon([(x + 485, 418), (x + 505, 430), (x + 485, 442)], fill="#486581")
    badges = ["METADATA ONLY", "NO DATASET PAYLOAD", "NO TRAINING", "GT DEPTH PROHIBITED AS MAPPING INPUT", "GT-POSE RGB-ONLY MAP-ONLY", "TRAINING UNAUTHORIZED"]
    y = 705
    x = 78
    for idx, badge in enumerate(badges):
        if idx == 3:
            y = 770
            x = 78
        w = draw.textbbox((0, 0), badge, font=font(20, True))[2] + 40
        draw.rounded_rectangle((x, y, x + w, y + 46), radius=20, fill="#FFFFFF", outline="#B91C1C" if "PROHIBITED" in badge or "UNAUTHORIZED" in badge else "#486581", width=2)
        draw.text((x + 20, y + 11), badge, font=font(20, True), fill="#B91C1C" if "PROHIBITED" in badge or "UNAUTHORIZED" in badge else "#102A43")
        x += w + 16
    draw.text((80, 850), "Authority: official ETH3D pages/repos + frozen Protocol V2 | Entry audit V1", font=font(18), fill="#627D98")
    image.save(path, format="PNG", optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    args = parser.parse_args()
    out = args.task_root.resolve() / "figures"
    out.mkdir(parents=True, exist_ok=True)
    chart_map = []
    for name, spec in FIGURES.items():
        render(out / name, *spec)
        chart_map.append({"filename": name, "title": spec[0], "source": "official frozen metadata and Protocol V2 contracts", "metadata_only": True})
    (out / "chart_map.json").write_text(json.dumps(chart_map, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "figure_count": len(FIGURES)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
