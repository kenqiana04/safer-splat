请完整执行以下唯一授权任务。该任务仅授权 ETH3D Delivery Area 的 Protocol V2 数据集准入审计，不授权下载任何数据集压缩包、创建训练环境、运行训练、生成地图或运行控制器。

# ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1

==================================================
0. 任务目标与科学定位
==================================================

PR #76 已按 Layered Gaussian Map Evaluation Protocol V2 完成现有地图回溯重认证，并得出：

FINAL_STATUS=
NO_EXISTING_LEARNED_GAUSSIAN_MAP_NAVIGATION_QUALIFIED_UNDER_PROTOCOL_V2

FINAL_DECISION=
PROCEED_TO_NEW_DATASET_ENTRY_QUALIFICATION

Only next task=
ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1

本任务的目标不是直接训练 ETH3D，而是回答：

1. “delivery_area”究竟属于 ETH3D 哪个benchmark、哪些数据变体；
2. 是否存在一个不使用评价真值作为mapping输入的合法 learned-Gaussian-map 路线；
3. 哪些资产可作为训练输入，哪些只能作为held-out评价或独立oracle；
4. 是否能够构造无数据泄漏的TRAIN/HELDOUT合同；
5. 是否能够形成独立reference、UNKNOWN、route、robot和physical-budget合同；
6. 应选择什么mapping frontend；
7. 是否应允许后续有限资产下载；
8. 若允许，下一任务的精确资产白名单与禁用清单是什么；
9. 若不允许，必须在下载或训练前关闭路线。

本任务必须防止此前出现的错误：

- 把论文指标公式误当成通用hard gate；
- 把GT/evaluation depth作为训练depth；
- 把MVS场景误当成ETH3D SLAM RGB-D序列；
- 训练完成后才发现没有合法route、UNKNOWN或physical budget；
- 使用候选地图生成自己的考试路线；
- 通过降低coverage、delta1或alpha门来挽救地图；
- 把GT-pose map-only写成完整SLAM；
- 先下载大量数据，再判断数据合同不成立。

本任务是：

METADATA_ONLY_PROTOCOL_V2_NEW_DATASET_ENTRY_AUDIT

不是：

DATASET_ACQUISITION
MAPPING
TRAINING
NAVIGATION_BENCHMARK

==================================================
1. Git lineage
==================================================

Repository：

kenqiana04/safer-splat

冻结上游：

PR #76

branch：

retrospective-requalify-existing-gaussian-maps-protocol-v2

预期 head：

d8fc27f7fa781ceb80e66ff12ca1a93fa0fc52de

执行前确认 PR #76：

- state=OPEN；
- draft=true；
- merged=false；
- mergeable=true；
- base=gaussian-map-metric-provenance-navigation-usability-calibration-v1；
- FINAL_STATUS=
  NO_EXISTING_LEARNED_GAUSSIAN_MAP_NAVIGATION_QUALIFIED_UNDER_PROTOCOL_V2；
- FINAL_DECISION=
  PROCEED_TO_NEW_DATASET_ENTRY_QUALIFICATION；
- Only next task=
  ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1；
- training/download/controller/planner/map modification均为0。

冻结上游身份：

Protocol V2 SHA-256：
a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e

New-dataset checklist SHA-256：
7c95f787fd7fb503e4bd2726546debac53acd41c1d5f9a8dd08c29cb27735593

PR #76 report SHA-256：
052ccdf0…153b570

必须从PR #76 machine-readable artifact读取完整report SHA，不得只使用截断值。

不得修改、amend、rebase、force-push、关闭、合并或重写 PR #68–#76。

从PR #76实际最新head创建：

branch：

eth3d-delivery-area-protocol-v2-entry-qualification-v1

新 Draft PR base：

retrospective-requalify-existing-gaussian-maps-protocol-v2

Draft PR title：

[Draft] Qualify ETH3D Delivery Area for Protocol V2 asset acquisition

建议commit：

docs(reproduction): qualify ETH3D Delivery Area protocol v2 entry

只允许一个正式branch和一个Open Draft PR。

==================================================
2. 网络、SSH和下载边界
==================================================

使用既有：

- Codex-Persistent-Reverse-Proxy-Watchdog；
- server proxy 127.0.0.1:17898；
- ~/.config/scannetpp_proxy/run_with_scannetpp_proxy.sh。

禁止：

- 修改或重启watchdog；
- 操作17897；
- 终止managed SSH；
- 重启ssh/sshd、网络或防火墙；
- kill其他SSH会话；
- 修改全局Git proxy。

允许的网络操作仅包括：

- 读取ETH3D官方网页；
- 读取官方GitHub仓库元数据和小型文本文件；
- HTTP HEAD；
- HTTP Range请求必须为0字节body或仅用于验证服务器是否正确拒绝；
- 记录Content-Length、ETag、Last-Modified、Content-Type和重定向链；
- 读取许可证、README、数据格式和evaluation文档。

严禁：

- 下载任何ETH3D .7z/.zip/.ply/.png/.jpg/.raw/.depth数据体；
- git clone官方大型仓库；
- 下载预训练模型；
- 下载第三方镜像；
- 创建数据集目录并放入payload；
- 安装环境或编译代码。

固定计数：

dataset_archive_download_count=0
dataset_payload_bytes=0
image_download_count=0
depth_download_count=0
scan_download_count=0
occlusion_download_count=0
model_download_count=0
git_clone_count=0
environment_create_count=0
environment_modify_count=0
training_count=0
map_count=0
controller_count=0
planner_count=0

官方HTML、GitHub API JSON和小型文本源码属于metadata fetch，必须单独计数，不得混入dataset download。

==================================================
3. 路径
==================================================

tracked root：

reproduction/cross_dataset/
eth3d_delivery_area_protocol_v2_entry_qualification_v1/

TASK_ROOT：

/disk1/zlab/maintenance_records/
eth3d_delivery_area_protocol_v2_entry_qualification_v1

创建：

$TASK_ROOT/input_freeze
$TASK_ROOT/official_authority
$TASK_ROOT/dataset_identity
$TASK_ROOT/asset_manifest
$TASK_ROOT/license
$TASK_ROOT/input_reference_partition
$TASK_ROOT/modality_audit
$TASK_ROOT/frontend_audit
$TASK_ROOT/split_contract
$TASK_ROOT/reference_contract
$TASK_ROOT/unknown_contract
$TASK_ROOT/route_robot_contract
$TASK_ROOT/physical_budget
$TASK_ROOT/evaluator_contract
$TASK_ROOT/acquisition_plan
$TASK_ROOT/decision
$TASK_ROOT/figures
$TASK_ROOT/report
$TASK_ROOT/logs
$TASK_ROOT/tmp

新增磁盘上限：

1 GiB

该上限只用于metadata、HTML快照、小型GitHub源码、报告和图，不允许数据集payload。

==================================================
4. 官方一级来源
==================================================

只允许以下一级来源作为authority：

1. ETH3D官网首页、datasets、documentation；
2. ETH3D官方SLAM overview/datasets/documentation，仅用于排除名称和benchmark混淆；
3. ETH3D官方论文：
   A Multi-View Stereo Benchmark with High-Resolution Images and Multi-Camera Videos；
4. ETH3D/dataset-pipeline官方仓库；
5. ETH3D官方multi-view evaluation源码，必须从官网官方链接解析；
6. graphdeco-inria/gaussian-splatting官方仓库及其license；
7. Protocol V2和项目冻结历史。

禁止使用：

- 博客；
- 论坛；
- 第三方下载站；
- 非官方镜像；
- 教程作为authority；
- 搜索摘要替代官方页面正文。

必须冻结：

- 每个官方页面最终URL；
- retrieval UTC；
- HTTP status；
- content SHA-256；
- 页面标题；
- 引用字段；
- 官方GitHub repo；
- 默认branch；
- HEAD commit；
- license SHA；
- 必要submodule SHAs；
- 网页与repo之间的官方链接关系。

生成：

primary_authority_registry.json
official_web_snapshot_identity.json
official_repo_identity.json

==================================================
5. 必须首先纠正的数据集身份
==================================================

必须验证并明确：

“delivery_area”是ETH3D Multi-View Stereo benchmark的training scene，不是ETH3D SLAM benchmark中的RGB-D sequence。

至少验证两个官方变体：

A. High-resolution multi-view DSLR

- scene name：delivery_area；
- indoor；
- 44 images；
- official undistorted DSLR archive；
- official COLMAP-format calibration/poses；
- official raw/clean/eval laser-scan assets；
- official occlusion assets；
- official rendered depth assets。

B. Low-resolution many-view camera rig

- scene name：delivery_area；
- indoor；
- 4 × 237 images；
- official undistorted rig archive；
- official rig/COLMAP calibration and poses；
- official raw/clean/eval laser-scan assets；
- official occlusion assets；
- official rendered depth assets；
- four simultaneous rig-camera images must be treated as one capture group for splitting。

必须生成：

eth3d_delivery_area_benchmark_identity.json

必须包含：

DATASET_FAMILY=
ETH3D_MULTI_VIEW_STEREO

NOT_DATASET_FAMILY=
ETH3D_SLAM_RGBD

如果官方metadata无法确认：

FINAL_STATUS=
BLOCKED_BY_ETH3D_DELIVERY_AREA_BENCHMARK_IDENTITY_AMBIGUITY

停止。

==================================================
6. 官方资产清单
==================================================

从ETH3D官方datasets页面解析完整、精确文件名和官方声明大小。

至少登记：

High-res DSLR：

- delivery_area_dslr_undistorted.7z
- delivery_area_dslr_jpg.7z
- delivery_area_dslr_raw.7z
- delivery_area_scan_raw.7z
- delivery_area_scan_clean.7z
- delivery_area_dslr_scan_eval.7z
- delivery_area_dslr_occlusion.7z
- delivery_area_dslr_depth.7z

Low-res rig：

- delivery_area_rig_undistorted.7z
- delivery_area_rig.7z
- delivery_area_scan_raw.7z
- delivery_area_scan_clean.7z
- delivery_area_rig_scan_eval.7z
- delivery_area_rig_occlusion.7z
- delivery_area_rig_depth.7z
- delivery_area_rig_stereo_pairs_gt.7z

对每个资产记录：

- official filename；
- dataset variant；
- role；
- official size；
- final official download URL；
- redirect chain；
- Content-Length；
- ETag/Last-Modified；
- MIME；
- archive format；
- expected internal semantics；
- proposed project role；
- allowed phase；
- prohibited phase；
- future SHA verification method；
- whether required/optional/rejected。

禁止发起GET body下载。

生成：

official_asset_manifest.json
official_asset_manifest.csv
http_head_validation.json
asset_role_matrix.json

==================================================
7. 许可证与使用边界
==================================================

验证：

ETH3D data license：
CC BY-NC-SA 4.0

official 3DGS code license：
research/non-commercial license

必须判断：

- 是否允许当前非商业学术研究；
- 是否允许本地处理；
- 是否允许衍生小型统计与图；
- 是否禁止把原始dataset payload提交到Git；
- 是否要求署名；
- 是否要求share-alike；
- 是否限制commercial use；
- 是否允许发布trained map，需要什么license/attribution；
- 是否允许只发布SHA与脚本；
- 论文引用要求。

若license不兼容当前学术研究：

FINAL_STATUS=
BLOCKED_BY_ETH3D_OR_3DGS_LICENSE_INCOMPATIBILITY

不得下载。

生成：

license_compatibility_audit.json
LICENSE_AND_ATTRIBUTION_PLAN.md

==================================================
8. 输入、评价和oracle必须物理隔离
==================================================

建立唯一资产角色枚举：

MAPPING_INPUT_ONLY
HELDOUT_EVALUATION_ONLY
REFERENCE_ORACLE_ONLY
CROSS_VIEW_EVALUATION_ONLY
OPTIONAL_DIAGNOSTIC_ONLY
PROHIBITED_AS_MAPPING_INPUT
NOT_REQUIRED

必须遵守：

### 8.1 允许作为mapping input的内容

只允许：

- undistorted RGB images；
- official camera intrinsics；
- official camera extrinsics/poses；
- official image masks，前提是其语义不包含laser-scan geometry评价信息且官方定义允许；
- camera/rig grouping metadata。

### 8.2 禁止作为mapping input的内容

全部禁止：

- delivery_area_*_depth.7z；
- delivery_area_scan_raw.7z；
- delivery_area_scan_clean.7z；
- delivery_area_*_scan_eval.7z；
- delivery_area_*_occlusion.7z；
- laser scan；
- scan-derived depth；
- scan-derived normal；
- scan-derived mesh/splats；
- stereo_pairs_gt；
- evaluation result；
- held-out RGB；
- candidate-specific route；
- reference-based pruning；
- reference-based scale correction。

原因：

官方depth、scan_eval和occlusion/reference geometry均由激光扫描或官方ground-truth pipeline产生。将其用于mapping会把reference geometry泄漏到地图，不再属于纯RGB learned-map qualification。

必须生成：

eth3d_asset_access_control_contract.json

未来训练必须采用两个物理根目录：

TRAIN_INPUT_ROOT
EVAL_ORACLE_ROOT

训练进程必须：

- 无法读取EVAL_ORACLE_ROOT；
- 记录open-file审计；
- HELDOUT和reference access count=0。

==================================================
9. Mapping claim必须冻结
==================================================

候选地图的唯一允许claim：

ETH3D_DELIVERY_AREA_GT_POSE_RGB_ONLY_MAP_ONLY_LEARNED_GAUSSIAN_MAP

明确：

- GT/official scan-aligned camera poses；
- RGB-only mapping；
- map-only；
- 无tracking；
- 无pose estimation；
- 无sensor RGB-D；
- 无laser depth supervision；
- 无full SLAM；
- 单场景冻结实例；
- 不支持algorithm stability claim。

禁止claim：

- RGB-D SplaTAM map；
- online SLAM；
- tracking-and-mapping generalization；
- learned from raw sensor depth；
- independent pose estimation；
- real-robot safety；
- full-space reconstruction；
- arbitrary unknown-safe navigation。

生成：

eth3d_mapping_claim_contract.json
allowed_forbidden_claims.md

==================================================
10. Modality候选审计
==================================================

固定审计三个route。

### Route M1：Low-res rig RGB-only

输入：

delivery_area_rig_undistorted.7z中的RGB与official calibration/poses。

必须审计：

- 每个image是否有official pose；
- four-camera rig grouping是否可由官方metadata确定；
- intrinsics/extrinsics格式；
- pose坐标是否与scan/reference同一metric frame；
- 同时camera images是否共享rig pose；
- 是否能按capture group split；
- 是否可转为official 3DGS COLMAP input而不重新跑SfM；
- 是否需要对图像做未授权crop/undistortion；
- official rig pipeline已知的鲁棒性限制；
- 是否存在足够独立held-out/cross-view评价通道。

### Route M2：High-res DSLR RGB-only

输入：

delivery_area_dslr_undistorted.7z中的RGB与official calibration/poses。

必须审计：

- 44 images；
- official poses/intrinsics；
- metric scan alignment；
- 是否可以形成TRAIN和HELDOUT；
- 是否只能作为cross-view held-out；
- sparse-view风险；
- 是否能作为Route M1的独立DSLR cross-view评价；
- 是否可转为official 3DGS COLMAP input。

### Route M3：SplaTAM RGB-D

必须判断：

- Delivery Area MVS是否提供真实同步sensor RGB-D input；
- official rendered depth是否来自laser scan/reference pipeline；
- 使用该depth训练是否导致GT leakage。

除非一级来源证明存在独立真实sensor RGB-D数据且不是评价GT，否则固定：

ROUTE_M3_STATUS=
NOT_ADMISSIBLE_WITHOUT_REFERENCE_GEOMETRY_LEAKAGE

不得使用official rendered depth驱动SplaTAM训练。

生成：

modality_candidate_audit.json
splatam_admissibility_audit.json

==================================================
11. Mapping frontend审计
==================================================

固定候选：

F1. official graphdeco-inria gaussian-splatting
F2. project historical Splatfacto
F3. SplaTAM

### F1 official 3DGS

必须审计：

- official repo和commit；
- submodule identities；
- license；
- COLMAP input contract；
- ability to consume official posed RGB；
- whether it reruns COLMAP or can bypass conversion；
- camera model support；
- Gaussian parameter semantics；
- export semantics；
- resolution/VRAM implications；
- deterministic seed support；
- official default iterations；
- no depth requirement；
- no scan/reference input；
- future canonical adapter feasibility；
- SAFER ellipsoid semantics compatibility。

### F2 Splatfacto

只作为历史compatibility reference。

必须记录：

- 历史TUM/Replica几何失败；
- 不得因更易export而优先；
- 不得在同一正式task中与F1并行跑后择优；
- 若未来选择F2必须单独协议授权。

### F3 SplaTAM

因没有合法sensor RGB-D时，不可选择。

### 前端选择规则

只有一个frontend可进入未来formal route。

优先选择：

OFFICIAL_3DGS_COLMAP_RGB_ONLY

前提：

- official posed-RGB input compatible；
- no GT depth；
- canonical Gaussian export可证明；
- server environment在后续单独task可构建；
- license compatible。

若F1不满足：

不得自动回退Splatfacto或SplaTAM。

FINAL_STATUS=
NO_ETH3D_DELIVERY_AREA_FRONTEND_ENTRY_CONTRACT

Only next task=
REVIEW_PROTOCOL_V2_REAL_WORLD_DATASET_OR_FRONTEND_ALTERNATIVES_V1

生成：

frontend_authority_audit.json
selected_frontend_contract.json

==================================================
12. Primary modality与cross-view评价选择规则
==================================================

预注册选择规则：

1. 若Low-res rig满足official pose、rig-group、metric-frame和COLMAP compatibility：
   SELECTED_MAPPING_INPUT=
   LOW_RES_MANY_VIEW_RIG_RGB_ONLY

2. 在1成立时，High-res DSLR默认：
   CROSS_VIEW_EVALUATION_ONLY

3. 若Low-res rig不满足，但High-res DSLR独立满足posed-RGB和合法split：
   SELECTED_MAPPING_INPUT=
   HIGH_RES_DSLR_RGB_ONLY

4. 若两者均不满足：
   NO_ETH3D_DELIVERY_AREA_INPUT_MODALITY_QUALIFIED

5. 不得因为某variant预计更容易得到好结果而改变选择。

6. 若两者都满足，Low-res rig优先的理由必须只基于：
   - 更多official views；
   - capture grouping；
   - 能保留完全不同camera modality的DSLR作为cross-view评价；
   不得基于任何地图训练结果。

生成：

selected_input_modality_contract.json

==================================================
13. TRAIN/HELDOUT split entry合同
==================================================

本任务不得生成最终split，因为dataset payload未下载。

但必须冻结后续split生成规则和不可违反的条件。

### Low-res rig规则

split unit必须是：

RIG_CAPTURE_GROUP

同一rig capture/time的四个camera images必须全部属于同一partition。

禁止：

- 逐image随机split；
- 同一rig pose跨TRAIN/HELDOUT；
- 使用candidate map结果决定split；
- 使用render quality选择heldout；
- 删除困难capture；
- 将DSLR images放入TRAIN后再称其cross-view heldout。

必须在后续asset audit中：

- 解析全部unique rig captures；
- 验证每capture camera数量；
- 计算camera-center分布；
- 计算pose-neighbor和view-overlap分布；
- 生成至少一个deterministic spatially separated heldout候选；
- 报告split敏感性；
- 冻结唯一split前不得训练。

### High-res DSLR规则

若作为mapping input：

- image/pose为不可分单位；
- deterministic spatial split；
- 禁止random image leakage；
- 禁止使用GT depth或scan选择“容易”的heldout；
- 至少保留独立heldout和reference observable-ray评价。

### Cross-view

若rig为TRAIN：

- 全部DSLR RGB不得进入TRAIN；
- DSLR depth/scan_eval只用于cross-view evaluation；
- cross-view结果单独报告，不替代rig heldout。

不得在本任务中拍脑袋固定通用80/20为科学门。
后续任务必须把split比例标记为PROJECT_DESIGN并报告敏感性。

生成：

future_split_generation_contract.json
split_leakage_prohibition.json

==================================================
14. Reference authority合同
==================================================

冻结reference用途。

### R轴重建reference

Primary：

official variant-specific scan_eval
+
official ETH3D multi-view evaluator
+
official occlusion data

用于：

- accuracy；
- completeness；
- F-score；
- official visibility/occlusion support；
- multi-tolerance reporting。

### Observable-ray reference

official variant-specific depth maps，只用于：

- held-out depth；
- risk–coverage；
- accepted/rejected；
- ray-local false-free；
- per-frame诊断。

不得训练。

### Route/collision reference候选

official scan_clean
+
official scan alignment
+
official occlusion mesh/splats（若archive包含且语义可验证）

必须在后续asset audit中证明：

- metric frame；
- completeness；
- floor/obstacle可解释性；
- mesh/point-cloud queryability；
- routeable connected region；
- thin objects；
- occlusion/support限制。

scan_eval不能自动宣称full-space route oracle，因为其定义会移除只被至多一个image观测的点。

REFERENCE_AUTHORITY拟定：

A_DENSE_INDEPENDENT_GEOMETRY

但只有route/collision reference完整性在后续下载审计通过后才能正式授予。

生成：

eth3d_reference_authority_contract.json
reference_role_boundary.md

==================================================
15. UNKNOWN合同准入
==================================================

Protocol V2固定：

UNKNOWN != FREE

Entry qualification必须判断是否存在不依赖GT/reference的deployable runtime unknown机制。

不得：

- 使用scan/reference在runtime标known/free；
- 把low alpha直接视为free；
- 把距离最近Gaussian很远视为known free；
- 在看到地图后为它定制unknown区域。

未来candidate unknown机制只能使用mapping-time可用信息：

- training camera poses；
- RGB images；
- learned Gaussians；
- deterministic render visibility/transmittance；
- pre-frozen spatial support algorithm。

本任务必须审计三种候选机制，但不得实现或选择candidate-specific参数：

U1. training-frustum support only
U2. multi-view observed free-ray support to learned first surface
U3. Gaussian visibility/support count

对每个回答：

- 能标known occupied吗；
- 能标known free吗；
- 是否会把occluded space误标free；
- 是否依赖learned map；
- 是否可在训练前冻结算法；
- 是否需要minimum distinct views；
- 是否需要angular baseline；
- 是否可在SAFER query中返回UNKNOWN；
- 是否允许unknown-as-occupied；
- 是否可生成route knownness。

Entry通过至少要求：

UNKNOWN_CONTRACT_FEASIBLE_FOR_FUTURE_ASSET_VALIDATION

不要求本任务已实现。

若无法提出不使用GT且可部署的unknown合同：

FINAL_STATUS=
NO_ETH3D_DELIVERY_AREA_RUNTIME_UNKNOWN_ENTRY_CONTRACT

不得下载或训练。

未来unknown实现必须是单独task-owned adapter，不修改SAFER核心。

生成：

runtime_unknown_entry_audit.json
future_unknown_contract_specification.md

==================================================
16. Robot、route与目标claim
==================================================

本项目下一阶段只允许：

REAL_WORLD_SCENE_MAP_WITH_ORACLE_STATE_SIMULATED_NAVIGATION

不允许：

REAL_ROBOT_DEPLOYMENT_SAFETY

为了跨数据集可比，拟复用PR #64 benchmark robot/dynamics作为项目benchmark选择：

- 6D free-3D double integrator；
- forward Euler；
- dt=0.05 s；
- sphere robot；
- r_robot=0.10 m；
- epsilon_base=0.01 m；
- componentwise |v_i|<=0.10 m/s；
- componentwise |u_i|<=0.10 m/s²；
- bounded QP；
- independent swept-sphere collision oracle。

必须明确这些是：

PROJECT_BENCHMARK_DESIGN_CHOICE

不是ETH3D官方机器人，也不是通用物理标准。

Entry audit必须判断：

- Delivery Area室内scene在原则上是否能支持0.10m sphere；
- reference asset是否足以生成独立route；
- route可以完全由reference生成，不读取candidate map；
- route生成应在map training前冻结；
- candidate map不得删除route；
- route应覆盖open、moderate、tight等reference clearance分层；
- 是否有明确floor/gravity/upright frame；
- camera rig trajectory不能自动当作robot route；
- 如果缺少floor/upright metadata，后续asset audit如何解析；
- route必须在known/reference支持域内。

本任务不生成route。

生成：

eth3d_robot_benchmark_entry_contract.json
future_reference_route_contract.json

==================================================
17. Physical error budget准入
==================================================

Entry阶段不得填任意cm门。

未来route-tube必须满足：

UpperBound[e_plus | route tube]
<=
B_map_available

其中：

B_map_available =
reference clearance margin
- epsilon_loc
- epsilon_shape
- epsilon_sampled
- epsilon_stop
- epsilon_tracking

本benchmark拟采用oracle state，因此：

epsilon_loc=0

但必须明确：

- 仅适用于oracle-state simulation；
- 不支持real-world localization safety claim。

其余项必须在后续route/robot task中从：

- sphere model；
- forward Euler；
- dt；
- vmax；
- umax；
- bounded QP；
- waypoint tracking contract；

推导。

Entry通过要求：

PHYSICAL_BUDGET_DERIVATION_PATH_FEASIBLE

不是要求数值已闭合。

若未来asset/route无法提供reference clearance margin，则不得训练。

生成：

physical_budget_entry_contract.json

==================================================
18. Evaluation Protocol V2准入
==================================================

未来map qualification必须预先冻结以下评价。

### 18.1 Integrity

- identity；
- no leakage；
- pose/intrinsics；
- finite；
- deterministic export；
- map immutability；
- no reference access during training。

### 18.2 Native/common parity

- official 3DGS native renderer；
- project common renderer；
- same camera/mask；
- no favorable channel selection。

### 18.3 Risk–coverage

固定Protocol V2 alpha网格：

{0.05,0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.90,0.95}

不产生通用hard gate。

### 18.4 ETH3D official geometry

固定official evaluator和reporting tolerances。
必须同时报告：

- accuracy；
- completeness；
- F-score；
- official visibility support；
- no universal numeric gate。

### 18.5 Navigation-conditioned

- deployable UNKNOWN；
- route tube；
- one-sided e_plus；
- physical budget；
- independent swept-body oracle；
- G0 separate。

### 18.6 NVS

- rig heldout；
- DSLR cross-view（若rig training）；
- 仅描述，不作为navigation hard gate。

生成：

eth3d_protocol_v2_future_evaluator_contract.json

==================================================
19. Frontend与资产未来执行顺序
==================================================

若Entry通过，后续必须严格分阶段。

Phase 1：
bounded asset acquisition

Phase 2：
archive hash、内部file listing、license、calibration、pose、rig grouping、reference frame和split审计

Phase 3：
unknown、route和physical-budget合同冻结

Phase 4：
official 3DGS source/environment qualification

Phase 5：
smoke

Phase 6：
single frozen formal mapping

Phase 7：
Protocol V2 qualification

禁止直接从Entry跳到训练。

必须生成：

eth3d_delivery_area_stage_gate_plan.json

==================================================
20. 最小未来资产白名单
==================================================

本任务必须基于最终selected modality生成未来下载白名单，但不得下载。

若选择Low-res rig，拟定最小白名单：

Required mapping input：

- delivery_area_rig_undistorted.7z

Required evaluation/reference：

- delivery_area_rig_scan_eval.7z
- delivery_area_rig_occlusion.7z
- delivery_area_rig_depth.7z
- delivery_area_scan_clean.7z

Cross-view evaluation：

- delivery_area_dslr_undistorted.7z
- delivery_area_dslr_scan_eval.7z
- delivery_area_dslr_occlusion.7z
- delivery_area_dslr_depth.7z

Not initially required：

- delivery_area_scan_raw.7z
- delivery_area_dslr_raw.7z
- delivery_area_dslr_jpg.7z
- delivery_area_rig.7z
- delivery_area_rig_stereo_pairs_gt.7z

若选择High-res DSLR，重新生成最小白名单，但仍禁止GT depth作为TRAIN。

每个资产必须给出：

- exact role；
- reason；
- official size；
- expected disk expanded size；
- next-task download authorization；
- TRAIN/EVAL root；
- license attribution；
- checksum procedure。

生成：

future_bounded_download_whitelist.json
future_download_denylist.json
future_disk_budget.json

==================================================
21. 数据下载后的必检项
==================================================

Entry通过后的下一任务必须在下载后、训练前验证：

1. archive SHA；
2. internal file listing；
3. image count；
4. unique capture count；
5. camera count；
6. image dimensions；
7. cameras.txt；
8. images.txt；
9. points3D.txt是否存在以及是否作为input；
10. pose convention；
11. intrinsics；
12. rig grouping；
13. scan alignment；
14. coordinate units；
15. scan_eval/clean差异；
16. depth format和单位；
17. occlusion asset；
18. image masks；
19. split候选；
20. cross-view alignment；
21. reference coverage；
22. floor/upright；
23. routeability；
24. unknown-contract feasibility；
25. disk/GPU estimate；
26. official 3DGS converter dry-run；
27. no TRAIN access toreference。

未全部通过不得训练。

==================================================
22. Entry决策树
==================================================

### Case A：完整准入通过

必须同时满足：

- benchmark identity明确；
- official asset manifest完整；
- license compatible；
- input/reference可物理隔离；
- 至少一个RGB-only modality可用；
- selected frontend为official 3DGS；
- SplaTAM GT-depth leakage route已拒绝；
- future split合同可行；
- reference authority路径可行；
- deployable unknown合同路径可行；
- independent route路径可行；
- physical budget推导路径可行；
- Protocol V2 evaluator路径可行；
- future bounded whitelist明确；
- no dataset payload downloaded。

FINAL_STATUS=
PASS_ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION

FINAL_DECISION=
AUTHORIZE_BOUNDED_ETH3D_DELIVERY_AREA_ASSET_ACQUISITION_AND_CONTRACT_AUDIT

Only next task=

ACQUIRE_ETH3D_DELIVERY_AREA_FROZEN_ASSETS_AND_VALIDATE_SPLIT_REFERENCE_UNKNOWN_ROUTE_CONTRACT_V1

注意：

training_authorized=false

### Case B：无合法RGB-only mapping route

例如：

- official poses不能与RGB配套；
- 只能靠GT depth支持mapper；
- official 3DGS不能合法消费；
- input/reference无法隔离。

FINAL_STATUS=
NO_ETH3D_DELIVERY_AREA_LEARNED_MAP_ENTRY_CONTRACT

FINAL_DECISION=
CLOSE_ETH3D_DELIVERY_AREA_BEFORE_DOWNLOAD

Only next task=

REVIEW_PROTOCOL_V2_REAL_WORLD_DATASET_OR_FRONTEND_ALTERNATIVES_V1

### Case C：unknown/route/physical路径不成立

FINAL_STATUS=
NO_ETH3D_DELIVERY_AREA_NAVIGATION_ENTRY_CONTRACT

FINAL_DECISION=
CLOSE_ETH3D_DELIVERY_AREA_BEFORE_DOWNLOAD

Only next task=

REVIEW_PROTOCOL_V2_REAL_WORLD_DATASET_ALTERNATIVES_V1

### Case D：官方metadata不足

FINAL_STATUS=
BLOCKED_BY_ETH3D_DELIVERY_AREA_OFFICIAL_METADATA_AMBIGUITY

FINAL_DECISION=
STOP_BEFORE_DATASET_DOWNLOAD

Only next task=

RESOLVE_ETH3D_DELIVERY_AREA_OFFICIAL_ASSET_METADATA_V1

不得以猜测继续。

==================================================
23. 状态与claim边界
==================================================

Entry PASS只允许声称：

- ETH3D Delivery Area在metadata和协议层面具备一个可能合法的RGB-only GT-pose learned-map路线；
- 允许下一步下载白名单资产并验证；
- reference、unknown、route和physical budget仍需资产级闭合；
- 未训练、未生成地图、未获得R/N等级。

禁止声称：

- ETH3D map qualified；
- official 3DGS会成功；
- Delivery Area可导航；
- unknown已经解决；
- route已经存在；
- physical budget已经通过；
- SplaTAM可用；
- GT depth可用于训练；
- ETH3D正式训练已获授权。

==================================================
24. Tracked产物
==================================================

至少包含：

1. ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1.md
2. freeze_protocol_v2_entry_inputs.py
3. audit_eth3d_official_authority.py
4. parse_eth3d_delivery_area_assets.py
5. validate_eth3d_http_metadata.py
6. audit_eth3d_license.py
7. audit_dataset_benchmark_identity.py
8. classify_asset_roles.py
9. audit_input_reference_isolation.py
10. audit_delivery_area_modalities.py
11. audit_mapping_frontends.py
12. audit_splatam_gt_depth_leakage.py
13. build_future_split_contract.py
14. build_reference_authority_contract.py
15. audit_runtime_unknown_entry.py
16. build_robot_route_entry_contract.py
17. build_physical_budget_entry_contract.py
18. build_future_evaluator_contract.py
19. select_entry_decision.py
20. primary authority registry
21. official page/repo identities
22. official asset manifest
23. license audit
24. modality audit
25. frontend audit
26. input/reference partition
27. split contract
28. reference contract
29. unknown contract
30. robot/route contract
31. physical budget entry
32. evaluator contract
33. stage-gate plan
34. future download whitelist/denylist
35. future disk budget
36. run_manifest.json
37. validation_result.json
38. downstream_handoff.json
39. REPORT_ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1.md

不得提交：

- dataset payload；
- downloaded archives；
- images；
- scans；
- depth maps；
- environments；
- models；
- credentials；
- proxy配置。

==================================================
25. 图表
==================================================

至少生成：

1. eth3d_benchmark_identity.png
2. delivery_area_variant_comparison.png
3. official_asset_role_matrix.png
4. train_eval_oracle_isolation.png
5. gt_depth_leakage_boundary.png
6. modality_selection_flow.png
7. frontend_selection_flow.png
8. rig_group_split_contract.png
9. cross_view_evaluation_design.png
10. reference_authority_layers.png
11. runtime_unknown_entry_options.png
12. unknown_not_free_flow.png
13. robot_route_reference_separation.png
14. physical_budget_derivation_path.png
15. protocol_v2_future_evaluation.png
16. stage_gate_plan.png
17. bounded_download_whitelist.png
18. license_and_attribution.png
19. final_entry_decision.png
20. claim_boundary.png

图中必须注明：

- metadata only；
- no dataset payload；
- no training；
- GT depth prohibited as mapping input；
- GT-pose RGB-only map-only；
- training unauthorized。

==================================================
26. 报告
==================================================

生成：

REPORT_ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1.md

必须回答：

1. PR #76和Protocol V2身份；
2. ETH3D官方authority；
3. Delivery Area属于哪个benchmark；
4. high-res与low-res资产；
5. 为什么不是ETH3D SLAM RGB-D；
6. license；
7. input/reference/oracle隔离；
8. rendered depth是否是GT；
9. SplaTAM route是否允许；
10. official 3DGS compatibility；
11. Splatfacto历史边界；
12. selected frontend；
13. selected modality；
14. DSLR cross-view角色；
15. split生成规则；
16. reference authority；
17. scan_eval与scan_clean差异；
18. UNKNOWN合同；
19. route合同；
20. robot contract；
21. physical budget；
22. future evaluator；
23. minimal download whitelist；
24. denylist；
25. 未来磁盘预算；
26. training authorization；
27. allowed/forbidden claims；
28. execution counts；
29. FINAL_STATUS；
30. FINAL_DECISION；
31. Only next task。

==================================================
27. Git与Draft PR
==================================================

只stage：

reproduction/cross_dataset/
eth3d_delivery_area_protocol_v2_entry_qualification_v1/

禁止：

git add -A

提交前输出精确staged file list。

commit：

docs(reproduction): qualify ETH3D Delivery Area protocol v2 entry

push使用现有wrapper。

创建一个Open Draft PR。

Base：

retrospective-requalify-existing-gaussian-maps-protocol-v2

PR正文必须包含：

- PR #76 lineage；
- Protocol V2 SHA；
- metadata-only；
- benchmark identity；
- official assets；
- no payload download；
- license；
- GT depth leakage rejection；
- selected modality；
- selected frontend；
- split/reference/unknown/route/budget entry；
- whitelist/denylist；
- training_authorized=false；
- FINAL_STATUS；
- FINAL_DECISION；
- Only next task。

==================================================
28. 执行计数
==================================================

必须记录：

- official HTML fetches；
- GitHub API metadata fetches；
- HTTP HEAD count；
- dataset archive download count；
- dataset payload bytes；
- images/depth/scans/occlusion downloads；
- git clone；
- environment create/modify；
- training；
- optimizer；
- model/map；
- controller；
- planner；
- route generation；
- data split generation；
- asset whitelist count；
- asset denylist count。

以下必须为0：

dataset archive download
dataset payload bytes
image download
depth download
scan download
occlusion download
git clone
environment create
environment modify
training
optimizer
model/map
controller
planner
route generation
final data split generation

==================================================
29. 最终汇报
==================================================

完成后只汇报一次：

1. branch；
2. Draft PR；
3. commit；
4. base/head；
5. PR #76 status preserved；
6. Protocol V2 SHA；
7. checklist SHA；
8. report SHA；
9. official authority count；
10. ETH3D dataset family；
11. Delivery Area variants；
12. official asset count；
13. HTTP metadata status；
14. license result；
15. high-res image count；
16. low-res rig image/capture count；
17. selected mapping modality；
18. cross-view modality；
19. selected frontend；
20. SplaTAM admissibility；
21. GT depth training policy；
22. mapping claim；
23. input/reference partition；
24. split contract status；
25. reference authority entry status；
26. runtime unknown entry status；
27. robot/route entry status；
28. physical budget derivation status；
29. future evaluator status；
30. whitelist assets；
31. denylist assets；
32. future disk budget；
33. dataset archive/payload/download counts；
34. training/environment/map/controller/planner counts；
35. GPU final；
36. watchdog/SSH preservation；
37. training_authorized；
38. FINAL_STATUS；
39. FINAL_DECISION；
40. unresolved critical evidence；
41. server report；
42. downstream handoff；
43. Only next task。

完成后停止。