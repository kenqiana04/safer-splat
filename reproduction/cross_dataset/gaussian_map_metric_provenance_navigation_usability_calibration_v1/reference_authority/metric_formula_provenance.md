# Metric Formula Provenance

Metric definitions and decision thresholds are separate provenance objects.

| Source | Formula or semantic contribution | Universal pass gate? |
|---|---|---|
| [3D Gaussian Splatting](https://arxiv.org/abs/2308.04079) | Gaussian parameters and alpha compositing | no |
| [Gaussian-SLAM](https://arxiv.org/abs/2312.10070) | frontend and reported reconstruction metrics | no |
| [Nerfstudio Splatfacto](https://docs.nerf.studio/nerfology/methods/splat.html) | implementation semantics and defaults | no |
| [Nerfstudio depth conventions](https://docs.nerf.studio/quickstart/data_conventions.html) | depth and camera conventions | no |
| [SplaTAM official repository](https://github.com/spla-tam/SplaTAM) | native mapping and renderer semantics | no |
| [SplaTAM](https://arxiv.org/abs/2312.02126) | mapping and evaluation metrics | no |
| [TUM RGB-D evaluation tools](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/tools) | ATE and RPE trajectory metrics | no |
| [TUM RGB-D dataset](https://cvg.cit.tum.de/data/datasets/rgbd-dataset) | RGB-D units, associations, and trajectory authority | no |
| [Replica](https://arxiv.org/abs/1906.05797) | photorealistic indoor dataset and geometry | no |
| [Replica Dataset](https://github.com/facebookresearch/Replica-Dataset) | asset distribution and dense mesh authority | no |
| [ARKitScenes DATA](https://github.com/apple/ARKitScenes/blob/main/DATA.md) | depth uint16 millimetres, confidence 0..2, trajectory metres | no |
| [ARKitScenes](https://arxiv.org/abs/2111.08897) | dataset capture and benchmark scope | no |
| [ETH3D high-resolution multi-view benchmark](https://eth3d.ethz.ch/high_res_multi_view?metric=f1-score&set=test&sortby=g1&tolerance_id=2) | accuracy, completeness, F1 and tolerance reporting | no |
| [SAFER-Splat](https://arxiv.org/abs/2409.09868) | Gaussian ellipsoid safety query and control formulation | no |
| [Splat-Nav](https://arxiv.org/abs/2403.02751) | Gaussian-map navigation pipeline | no |
| [OctoMap official documentation](https://octomap.github.io/octomap/doc/index) | occupied, free, and unknown occupancy semantics | no |
| [Selective Classification for Deep Neural Networks](https://arxiv.org/abs/1705.08500) | risk-coverage analysis | no |
| [SelectiveNet](https://arxiv.org/abs/1901.09192) | coverage-risk trade-off | no |
| [Control Barrier Functions for Sampled-Data Systems](https://arxiv.org/abs/2103.03677) | sampled-data safety margins | no |
| [Sample-and-hold safety with CBFs](https://arxiv.org/abs/2304.08685) | inter-sample safety | no |

## Audit conclusion

Standard formulas do not make project-selected numeric cutoffs universal. Dataset units and confidence labels define input semantics; they do not certify navigation. The physically relevant bridge is an explicit robot/route/reference error budget, not a global image metric.
