"""Materialize independent S0/S1/S2/S3 source trees from the raw tuned snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


VARIANTS = {"S0_TUNED_BASELINE": (False, False), "S1_SURFACE_ORIENTED_PRIOR": (True, False), "S2_POINT_TO_PLANE_LOSS": (False, True), "S3_SURFACE_PRIOR_PLUS_POINT_TO_PLANE": (True, True)}

PRIOR_FIELDS = """    surface_prior_path: Path | None = None\n"""
LOSS_FIELDS = """    surface_target_root: Path | None = None\n    surface_loss_lambda: float = 0.10\n    surface_loss_beta_m: float = 0.02\n"""
PRIOR_METHOD = """    def populate_modules(self):\n        super().populate_modules()\n        if self.config.surface_prior_path is None:\n            return\n        prior = np.load(self.config.surface_prior_path, allow_pickle=False)\n        quats = torch.from_numpy(prior[\"quats_wxyz\"]).to(device=self.quats.device, dtype=self.quats.dtype)\n        log_scales = torch.from_numpy(prior[\"log_scales\"]).to(device=self.scales.device, dtype=self.scales.dtype)\n        if quats.shape != self.quats.shape or log_scales.shape != self.scales.shape:\n            raise RuntimeError(f\"SURFACE_PRIOR_SHAPE_MISMATCH:{quats.shape}:{self.quats.shape}:{log_scales.shape}:{self.scales.shape}\")\n        with torch.no_grad():\n            self.quats.data.copy_(quats)\n            self.scales.data.copy_(log_scales)\n\n"""
LOSS_HELPER = """    def _surface_target(self, image_index: int, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:\n        if self.config.surface_target_root is None:\n            raise RuntimeError(\"SURFACE_TARGET_ROOT_REQUIRED\")\n        path = Path(self.config.surface_target_root) / f\"{image_index:06d}.npz\"\n        with np.load(path, allow_pickle=False) as target:\n            factor = torch.from_numpy(target[\"plane_factor\"].astype(\"float32\", copy=False)).to(device=device)\n            valid = torch.from_numpy(target[\"surface_valid\"].astype(\"bool\", copy=False)).to(device=device)\n        return factor, valid\n\n"""
LOSS_INSERT = """        if self.config.surface_target_root is not None:\n            factor, surface_valid = self._surface_target(index, prediction.device)\n            target_surface = target\n            if target_surface.shape != prediction.shape:\n                target_surface = F.interpolate(target_surface[None, None], size=prediction.shape[-2:], mode=\"nearest\")[0, 0]\n            if factor.shape != prediction.shape:\n                factor = F.interpolate(factor[None, None], size=prediction.shape[-2:], mode=\"nearest\")[0, 0]\n                surface_valid = F.interpolate(surface_valid.float()[None, None], size=prediction.shape[-2:], mode=\"nearest\")[0, 0].bool()\n            if accumulation.shape != prediction.shape:\n                accumulation_surface = F.interpolate(accumulation[None, None], size=prediction.shape[-2:], mode=\"nearest\")[0, 0]\n            else:\n                accumulation_surface = accumulation\n            surface_mask = (torch.isfinite(target_surface) & torch.isfinite(prediction) & (target_surface > 0) & (prediction > 0) & torch.isfinite(factor) & surface_valid & (accumulation_surface > self.config.depth_accumulation_threshold))\n            if bool(surface_mask.any()):\n                residual = (prediction[surface_mask] - target_surface[surface_mask]) * factor[surface_mask]\n                surface_loss = F.smooth_l1_loss(residual, torch.zeros_like(residual), beta=self.config.surface_loss_beta_m)\n            else:\n                surface_loss = prediction.sum() * 0.0\n            loss_dict[\"loss_surface_point_to_plane\"] = self.config.surface_loss_lambda * surface_loss\n            if metrics_dict is not None:\n                metrics_dict[\"loss_surface_point_to_plane\"] = surface_loss.detach()\n"""


def sha256_tree(root: Path) -> str:
    digest=hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode()+b"\0"+path.read_bytes())
    return digest.hexdigest()


def alter_model(path: Path, prior: bool, loss: bool) -> None:
    text=path.read_text(encoding="utf-8")
    if "import numpy as np" not in text: text=text.replace("import imageio.v3 as iio\n", "import imageio.v3 as iio\nimport numpy as np\n")
    marker="    refinement_lock_step: int | None = 3000\n"
    fields = PRIOR_FIELDS if prior else ""
    fields += LOSS_FIELDS if loss else ""
    text=text.replace(marker, marker+fields, 1)
    insert=""
    if prior: insert += PRIOR_METHOD
    if loss: insert += LOSS_HELPER
    text=text.replace("    def _depth_target", insert+"    def _depth_target", 1)
    if loss:
        needle="        if metrics_dict is not None:\n            metrics_dict[\"loss_depth_metric\"] = depth_loss.detach()\n            metrics_dict[\"valid_depth_ratio\"] = valid_ratio.detach()\n        return loss_dict\n"
        text=text.replace(needle, LOSS_INSERT+needle, 1)
    path.write_text(text,encoding="utf-8",newline="\n")


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--source",type=Path,required=True); parser.add_argument("--out",type=Path,required=True); parser.add_argument("--manifest",type=Path,required=True); args=parser.parse_args()
    baseline=sha256_tree(args.source); result={"baseline_source_sha256":baseline,"variants":{}}
    for name,(prior,loss) in VARIANTS.items():
        destination=args.out/name
        if destination.exists(): shutil.rmtree(destination)
        shutil.copytree(args.source,destination)
        if prior or loss: alter_model(destination/"tum_metric_depth_splatfacto.py",prior,loss)
        result["variants"][name]={"source_sha256":sha256_tree(destination),"surface_prior":prior,"point_to_plane_loss":loss,"s0_byte_identical": name=="S0_TUNED_BASELINE" and sha256_tree(destination)==baseline}
    args.manifest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))


if __name__ == "__main__": main()
