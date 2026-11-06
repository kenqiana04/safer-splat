# FAS / safer-splat 固定交接文档

> **先读结论：** 用户已明确授权中断GPU1的PID3142527。2026-11-06 07:11 UTC核实root/run_mapping3d.py、functional3dgs、容器、GPU和start_ticks一致后，SSH账户zlab发送SIGINT遭`Operation not permitted`拒绝，成功发送信号0。07:12:59 UTC复查目标仍占4372 MiB。**当前阻断是操作系统信号权限，不是缺用户授权；D/L未启动，所有新实验计数0。** 未用sudo/docker/SIGKILL绕过，需负责人在有权限的作业会话中结束进程；无自动等待/续跑。旧CPU结论不变。

- 正式维护位置：**https://github.com/kenqiana04/safer-splat/blob/master/HANDOFF.md**；本机文件只是工作副本，阶段更新须同步到 GitHub。
- 最后更新：**2026-11-06，Asia/Shanghai**（Git 提交记录提供精确发布时间）。
- 更新者：**Codex，本 safer-splat 会话**。
- 本次文档变更：记录固定成熟A两参考任务的资源阻断与零执行消耗；仅改本交接文档，不发布研究代码、不改变默认配置。
- 最近实测阶段：`FAS_TRIAL23_SAME_SOURCE_QP_REFERENCE_CPU_DIAGNOSIS_V1`，`run_20261106T043951Z`。
- 状态依据：最近阶段封存文件及本会话只读核查；不是对整台服务器当前所有进程的监控。

### 最新PID3142527中断授权：系统权限拒绝

- `BLOCKED_PROCESS_SIGNAL_PERMISSION`。UID0、run_mapping3d.py、functional3dgs、原Docker cgroup和GPU1均匹配；启动时间北京时间14:31:36，start_ticks=118439017，发信号前再核对未变。
- Python pidfd接口不可用的首检查未发信号；随后普通SIGINT一次发送调用被系统拒绝：`PermissionError [Errno 1] Operation not permitted`。没有提权/绕过或再次终止。07:12:59 UTC目标仍在。
- 本地包：`C:\Users\zlab\Documents\Codex\research-output\FAS_TRIAL23_FIXED_MATURE_A_REFERENCE_NATIVE_PAIR_V1\run_20261106T071123Z`；3件工件；清单SHA `d93d045b1a17fbfe0f3e311c692ccddf128eb7c54d146463aaacd256567f64cf`。
- GPU/Factory/Token/PlantCommit/求解/几何/CPU测试全0；源码、地图、默认开关不动，旧失败保留。同步SSH退出，无本任务后台/租约/自动后继。需要负责人使用有权限的原作业会话结束目标，不重复索取同一用户许可。
- 文档检查点`codex/checkpoint-before-trial23-signal-denied-20261106T071123Z`，基于`b87fb110f4a416da90c8043eb1d2fffb10d35f44`。

### 前次明确PID中断授权：原目标已退出，新占用者阻断

- 现场时间：2026-11-06 06:42:11 UTC。授权目标PID2990859的ps无记录，/proc条目不存在；未发送信号。
- GPU1 UUID仍为`GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d`，新compute PID3142527、functional3dgs环境占4372 MiB。相同环境不证明同一作业，不扩展终止授权。裁决`BLOCKED_NEW_UNAUTHORIZED_GPU1_OCCUPANT`。
- GPU0快照8 MiB、无compute行，但本轮未自动切换。源码/地图/依赖完整准入、DEV接线、CPU测试与D/L运行均未开始；新实验计数、信号计数均0。
- 本地包：`C:\Users\zlab\Documents\Codex\research-output\FAS_TRIAL23_FIXED_MATURE_A_REFERENCE_NATIVE_PAIR_V1\run_20261106T064211Z`；4件工件复验；清单SHA `0cfa6ac21b9d2640b64946b8e3379ce32aa0faf55a8776b752dc1a4604f8f4a6`。
- 文档检查点：`codex/checkpoint-before-trial23-pid-change-20261106T064211Z`，基于`0888b5ec9a42cb2e4f07336eef6f1013bfb7f879`。同步SSH已退出，没有本任务实验进程/租约/自动后继，旧阻断包未改。

### 前次GPU0改设备授权：资源阻断，已结束

- 现场：`GPU-a351decc-171b-8ec4-bbfa-e25bdc1459bc`，PCI `00000000:02:00.0`，RTX4090，驱动525.147.05；设备占4380 MiB，compute PID2972493占4372 MiB。资源门仅针对新授权GPU0；全设备清单包含GPU1不表示重试。
- 裁决：`BLOCKED_GPU0_RESOURCE_CONFLICT`；没有CUDA初始化，逻辑设备映射/完整兼容性未验证。静态发现冻结worker第7/29行写死`CUDA_VISIBLE_DEVICES='1'`，adapter导入会清空变量，`cuda:0`是逻辑设备；以后不能仅修改shell或日志冒充GPU0切换。本轮未改任何绑定或源代码。
- 来源/依赖现场全量核对、driver、CPU测试、两臂运行均未开始。同步查询已退出，没有本任务后台进程、租约或自动后继。
- 新本地包：`C:\Users\zlab\Documents\Codex\research-output\FAS_TRIAL23_FIXED_MATURE_A_REFERENCE_NATIVE_PAIR_V1\run_20261106T052722Z`；4件工件；清单SHA `bee6320466e9408d15bf09eed8ad555d1df1a9ab53b37103b23c07a7857afd3f`。
- 文档修改前检查点：`codex/checkpoint-before-trial23-gpu0-stop-20261106T052722Z`，基于`fa401d1e015b2317b1e44eb01870c3c8d93c6255`。只维护HANDOFF，旧包和dirty不动。

### 上一次GPU1授权尝试：资源阻断，原记录保留

- 任务：`FAS_TRIAL23_FIXED_MATURE_A_REFERENCE_NATIVE_PAIR_V1`。目标仅Trial23，固定H260 A臂，D/L各一臂；不扩为四组。
- 现场GPU1：`GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d`，总占用4380 MiB；已有compute PID `2990859`，`/root/miniconda3/envs/functional3dgs/bin/python`，4372 MiB。只查一次，没有等待或终止他人进程。
- 科学状态：`NOT_EVALUATED`；工程状态：`BLOCKED_GPU1_RESOURCE_CONFLICT`。不是A层恢复/权限失败，不改变既有CPU结果。
- 新增GPU会话/Factory/Supervisor/Token/PlantCommit/solver/geometry/CPU实验测试均0；未创建服务器任务目录、未接线driver。同步SSH已退出，无本任务后台或自动后继。
- 只核验两份本机上游清单自身SHA；本次服务器保护HEAD、源码依赖和地图完整复核未开展，不宣称来源准入已通过。
- 本地封存：`C:\Users\zlab\Documents\Codex\research-output\FAS_TRIAL23_FIXED_MATURE_A_REFERENCE_NATIVE_PAIR_V1\run_20261106T052241Z`；6件工件复验；清单SHA `9030dbfdb33a9d0ed8ad824952d0d97fb89e254940c0dc7f8dad60c69ecedd03`。
- 修改前命名检查点：`codex/checkpoint-before-trial23-resource-stop-20261106T052241Z`，指向`7a898e06ff15000c0c81c577c3aea8f3533af3ec`。
- 后续重试必须新授权、新目录、新资源门，不在本阻断包重启。本交接不保留自动执行资格。

## 1. 当前目标、结论与下一步

### 当前目标

区分 FAS 导航低进展来自：缺少合适任务参考、路径/轨迹跟踪、CBF-QP 的局部过滤，还是恢复与执行资格/时效。坚持以下边界：

1. 纯固定点 PD + CBF-QP 是原 FAS 安全研究主线；不能因为 Goal Success 未建立，自动把 Planner 变成默认模块。
2. 规划/航点只能作为待验证的外部名义输入或诊断变量，接入成熟算法本身不是原创贡献。
3. 保留 C0/L0–L3、后备、终端、Supervisor 与执行身份链，不通过放宽安全条件换取进展。

### 最新明确裁决

`PASS_SAME_SOURCE_CPU_QP_REFERENCE_DIAGNOSIS_WITH_LIMITS`

`REFERENCE_TRACKING_GAIN_SURVIVES_SOURCE_QP_IN_THIS_CPU_CASE`；仅Trial23已知开发任务、固定参数。16项准入检查、两组916个接受模型步、15600项独立复算与968文件封印。新CPU QP920次（含准入4次），FULL1835次（含准入3次）；另1次注入求解失败测试不计真实求解。PSF/Factory/Supervisor/Token/PlantCommit/GPU/A*均0。最终task goal始终不变。

### 推荐下一步——尚未执行

**固定成熟A层的参考身份接线与有限同参考对照**已获本次有界授权，但在资源门终止；如需重试必须重新授权，而不是先做A*或扩搜局部动作：

- 两组同源QP的CPU比较已完成；继续保持相同目标/CBF行/六盒行/求解器/PD，不可把旧无盒B拿来与有盒A混称单因素。
- task goal继续在snapshot内；tracking target在旁路记录并关联state/candidate/action身份，不擅改Token格式或沿用旧Token。本轮CPU日志没有任何native资格。
- 本轮.10q诊断域仅是范围限制，不是已观测自由空间或认证安全管；其余地图未知域仍未解决。
- 若继续CPU成熟A对照，必须先固定其真实资格与时效语义；若需要GPU/Factory/Token/PlantCommit，必须另获明确授权。不能把CPU前两组与GPU后两组拼成严格公平四组。
- 成熟A若仍阻断可跟踪参考，定位后备/拒绝/时效的首次分歧；不放宽安全条件。停止逐点LP/PSF筛选，不自动接Planner或改研究主版本。

这一下一步是建议，**不是排队任务、自动续跑或已获原生授权**。

## 2. 使用版本、分支与工作区状态

### 本机仓库（本次现场读取）

- 根目录：`C:\Users\zlab\Documents\Codex\github-clean-work\safer-splat`
- 当前分支：`tum-splatfacto-v1r5-command-preregistration-v1`
- 当前 HEAD：`d0b4f2278763fedeb4fd9bc26ff7f55a7c5c2b23`
- **这不是服务器 Candidate/Frozen/Perf 的同一版本，不能用本机 HEAD 冒充原生实验方法身份。**
- 已有 dirty 状态必须保留：已跟踪修改为 `reproduction/cross_dataset/tum_splatfacto_v1r5_command_preregistration_v1/v1r5_exact_training_command.sh`，另有 `.codex*`、`.tmp*`、`docs/` 及 reproduction 下未跟踪文件/目录。不要执行 reset、clean、stash 或批量 add。
- 本次只提交、推送 `HANDOFF.md`；使用基于远端 `master` 的隔离工作树，不修改上述已有文件或切换本机工作分支。文档发布不表示实验源码/数据被上传或方法版本改变。
- GitHub发布基点：`master@f0d3ba6530fe0a1befd988df2363b688d0d910ea`；隔离分支 `codex/handoff-github-20261106`。修改前命名检查点分支：`codex/checkpoint-before-trial23-qp-20261106T0455`。发布提交号以 GitHub 文件历史为准。
- 修改前命名检查点：`C:\Users\zlab\Documents\Codex\research-output\checkpoints\FAS_HANDOFF_BEFORE_20261106T035713Z\CHECKPOINT.json`。包含 HEAD、分支、完整 porcelain 状态和已有 tracked diff；这是文件检查点，不是 Git commit，也不是所有未跟踪数据的备份。

### 服务器保护工作树（最近 CPU 阶段前后均匹配、clean）

共同父目录：`/disk1/zlab/v3_repair_worktrees/`

|身份|目录名|冻结 HEAD|
|---|---|---|
|Candidate|`safer-splat-fas-vnext-tail-cardinality-targeted-repair-v1`|`33e34a3ac8d710452775ffe688af77393f734fa9`|
|Frozen|`safer-splat-fas-vnext-l2-deadline-routing-correctness-v1`|`481c3e5e24648d0219e1969f1145648ac99f6943`|
|Perf|`safer-splat-fas-vnext-map-epoch-cache-perf-v1`|`b0a6bbb96512cef5085feada98a900bf9d8ff15f`|

最近阶段对 47 个保护文件做前后 SHA 一致性核对。这里记录的是该阶段快照，下一次需要用到时重新核对，不宣称永久 clean。

现有 SSH 别名为 `zlab-4090`，本会话曾成功使用已有连接。Python 路径为 `/disk1/zlab/conda_envs/safer_splat_official/bin/python`。不在文档保存密码/私钥；连接和执行范围以每轮用户授权为准。

## 3. 运行中、等待中与历史待办

|任务|状态|注意事项|
|---|---|---|
|Trial23阶段0/A无QP两组CPU跟踪|已结束并封印|保留旧43工件，不重跑|
|本轮同源QP两参考CPU对照|已结束并封印|两个子进程正常退出，无后台后继任务|
|完整四组参考×FAS对照|NOT_READY|前两组CPU已实跑，成熟A两组及原生等价尚未验证|
|成熟A相同参考对照|PID3142527已获用户中断授权且身份匹配，但zlab发送SIGINT被系统权限拒绝；D/L未启动|需有权限的负责人结束作业；旧包保留，无自动等待/续跑|
|A/G H260 的 `R03_G`、`R04_G`、`R04_A`|历史待办，不在运行或排队|旧续跑曾资源阻断，不自动恢复；先确认用户是否仍要继续此支线|
|服务器其他用户/项目作业|07:12:59 UTC：GPU1仍有PID3142527，4372 MiB|只是一次复查，不持续监控，不声称此后资源状态|

H260 正式包里八个臂目录并不表示八臂完成：最近只读核查发现后三个待办结果目录为空，最终记录仍是 5 个初始化臂、1300 提交、2 对完整配对。

历史三臂续跑曾因 `GPU1_RESOURCE_CONFLICT` 阻断，资源占用是旧事实，不是当前 GPU 状态。不要删除永久阻断标志、不在旧目录重启、不轮询等待资源、不杀他人进程。若确需继续，必须新授权、新目录和新资源核查。

## 4. 冻结配置与方法身份

### 共用模型与证据边界

- 状态 `[p,v]`；position-first forward Euler：`p1=p+dt*v`，`v1=v+dt*u`。
- `dt=.05`，canonical CPU 用原 binary32 运算图；`u0` 不影响 `p1`，但影响 `v1` 与 `p2`。
- 球半径 `.015q`，reserve `0`；q 是地图坐标单位，不是已标定的米。
- 原动作/速度边界、严格 terminal 速度容差 `1e-12`、zero-hold 与权限条件不改。
- 模型步长不是实际 20Hz；共享 CPU/GPU 表示地图 Oracle 不是独立严格浮点或物理安全真值。

### PD 与源 QP

成熟原生 worker 实际运算：

```text
desired_velocity = clip(5*(goal-pos), -.1, .1) - v
desired = clip(desired_velocity-v, -.1, .1)
```

不要为了简写改变浮点运算顺序。源 QP `P=I, q=-u_des`，等价最小化对名义首动作的平方偏差，不是最大化 Progress。成熟 A 的 P0 追加六条动作盒行；原无盒 QP、F0/Q0、成熟 A 不能混为同一基线。

- 历史 B：修复 V3 参考。
- 历史 V / 当前 A：`FAS_MATURE_NATIVE_PSF_RECOVERY_DEV_V1` 整合参考，有盒约束、独立 producer 身份、PSF 尾见证等；DEV/OFF。
- G：A 加冻结可选 guard；不是原始 SAFER-Splat 基线。
- 历史 B/V 是多因素整合对比，不支持 PSF 单因素因果。
- 旧 V3 Full85 证据仅归其原冻结版本，不继承给 A/G 或任何后续适配器。

### goal / reference / token 关键绑定

Candidate 下 `reproduction/runtime/active_runtime_assurance_v2/runtime_types.py:260–263` 将 `goal` 纳入状态身份；候选绑定状态/map/producer。`certification_execution_state_identity_repair_v1/repaired_components.py:228–241,295–324` 的 L3/Backup 后继身份也沿用 task goal。

因此不能把航点写入 `snapshot.goal`。可使用独立 `desired_reference` 接缝生成名义动作，但必须另记 tracking target、path hash、frame、map/Profile、有效期和来源；路径通过不授予 Token。

## 5. 最新实测结果与负结果

### Trial23同源QP两参考CPU诊断（最新）

直接导入源CBF/DoubleIntegrator和成熟A原六盒行函数；alpha5/beta1、minimal=True、Clarabel defaults不变。失败PD fallback被拒绝，不当作成功动作。与阶段A相同初态/goal/地图/PD/前视.02q/binary32/H500/到达阈值，固定D→L各一次，仍不加FAS恢复/权限层。

|指标|D：直接目标＋同源QP|L：直线参考＋同源QP|
|---|---:|---:|
|接受CPU模型步|500|416|
|软件阈值到达|否|是，连续10步|
|H260 Progress|0.096666339872|0.690361613797|
|共同H416 Progress|0.096668047097|0.997165659331|
|终点目标距离 q|0.708397248474|0.002222703542|
|终点速度 q/模型秒|2.01357e-7|0.001474799272|
|near-stall窗口/分母|258/441|0/357|
|首次near-stall|c183–242|无|
|末60步DeltaProgress|0|0.046527192076|
|末60名义目标投影中位数|0.100128101352|0.010397692532|
|末60QP目标投影中位数|5.26443e-11|0.010397687025|
|完整段源SAFE/UNSAFE/UNKNOWN|500/0/0|416/0/0|
|真实CPU QP调用/Solved|500/500|416/416|
|FULL调用|1000|832|
|臂墙钟秒，含初始化|389.491100|307.089383|
|逐周期p50/p95秒|0.764301 / 0.834089|0.725974 / 0.780772|

源矩阵说明：D末60步名义动作违反行数中位82、最大违反量中位约.10222676；L末60对应0行、最大残差约−.07020412。是本轮CPU现场矩阵证据，不是历史GPU活动Gaussian记录。原QP解KKT stationarity最大范数约8.68e−9/8.02e−9；不支持“求解器失败返回PD”的解释，但不是严格最优性证明。

数值负结果必须保留：D39次、L14次issued32对QP半空间有微小正残差，最大5.72e−10/2.19e−10；源容差/量化未改变，没有内缩或clip修补，不能称严格实数CBF可行证书。D197步速度非零但位置binary32字节不变，不能当物理停车。L仍有累计反向目标距离约.01014669q，非严格单调。

准入：历史GPU捕获矩阵在同CPU源Clarabel重放raw64/issued32逐字节一致；但c240从CPU重新计算几何的A/b与GPU捕获不逐位相同，动作最大差3.04468e−11。**仅同源CPU域内公平，不是GPU原生等价。** 16项准入和15600项独立复算通过。保护3HEAD/47文件及附加源不变。至封印1222.04秒；两臂均在600秒内，0超时。

解释：该参考收益确实能穿过同源QP；本案例不需要先假定缺少绕障路线。但有QP直线组比无QP的368步多48步，且墙钟更高，不宣称无代价。尚未检验成熟A的后备、1e−12终端、Supervisor/Token和真实时效。1个开发任务不能证明跨场景导航或新方法优势。

### Trial23直线参考CPU诊断（上一阶段0/A）

固定同初态、goal、地图、原PD两级clip及源binary32 Euler。D直接目标，L当前位置在线投影到p0→goal线段后前视`.02q`，不引入速度前馈；task goal未被航点替换。H500、每臂600秒/1000 FULL、每段32 FULL、固定D→L各一次。`.10q`范围不是安全走廊。原终端1e-12/hold及FAS权限不修改，本阶段不调用它们。

|指标|D：直接目标PD|L：直线参考＋同PD|
|---|---:|---:|
|接受CPU模型步|38|368|
|待检查段数|39|368|
|闭段源状态|38 SAFE、1 UNSAFE|368 SAFE|
|终止|c38待推进段UNSAFE，未接受|软件到达阈值连续10步|
|共同H38 Progress|0.096012407697|0.089844146220|
|H260 Progress|NA（未覆盖）|0.796985728614|
|各自终点Progress，非同H比较|0.096012407697|0.997131337912|
|终点距离 q|0.708911404035|0.002249618563|
|终点速度 q/模型秒|0.069473405707|0.001552176059|
|最大偏离直线 q|0.065168096892|0.009191732950|
|FULL调用|45|368|
|臂墙钟秒，含初始化|17.171535|122.567561|
|逐步p50/p95秒|0.328338 / 0.397715|0.328283 / 0.341115|

到达阈值只用于本轮软件诊断：距goal≤`.01q`且速度≤`.005q/模型秒`连续10个接受状态，不追溯历史Goal、不替代严格FAS终端资格。没有新原生导航或PlantCommit。

必须保留负结果：共同H38时L进展更低；L有累计负向目标距离变化约`.01050572q`，不是严格单调趋近。D不足60步，不能用0个near-stall命中声称无停滞；L309个滚动窗口0命中。L到达支持CPU代理模型内可跟踪，不证明参考能通过QP/FAS、不是整个旧停滞的唯一因果解释。

总新FULL413；原始407个待检查段，406个接受模型步；UNSAFE段不纳入接受轨迹。17合同测试、4099独立复算通过，Progress最大差约1.46e−16。源前后3HEAD/47文件及附加源不变，父50工件复验通过。至封印702.73秒，30分钟预算内；D/L固定顺序，时延不作严格算法加速比。源几何是共享CPU Gaussian代理、q非米、无独立GPU舍入包络或物理真值。

### 地图、路径、跟踪准入 CPU 阶段

配置：四个固定初态 Trial23/54/89/1；8个端点；每任务一条直连；最多264次底层 FULL，每段最多64次、90秒。源段 backend 保持4096节点与1e-10参数容差，不修改安全语义。

|任务|端点|直连段源判定|FULL 次数|墙钟秒|
|---|---|---|---:|---:|
|23|起终点均PASS|`CERTIFIED_SAFE`|39|13.393|
|54|起终点均PASS|`FINITE_UNSAFE_WITNESS`|4|1.384|
|89|起终点均PASS|`FINITE_UNSAFE_WITNESS`|7|2.409|
|1|起终点均PASS|`FINITE_UNSAFE_WITNESS`|7|2.380|

总计65次FULL（含8端点），没有预算UNKNOWN、几何重试或新增路径搜索。57/57合同/算术测试、91/91独立记录/算术核验通过。独立核验没有独立几何真值；query点float64到float32最大坐标差约`1.30385e-8q`，尚无外向舍入误差包络。

Trial23 通过是**原共享CPU函数的条件结果**。另外三条直连 FAIL 不表示无绕行路线；八端点安全不表示连线安全。

同四条既有 V 轨迹各260行的只读统计（总1040历史提交，0新提交）：

|Trial|初始PD对目标方向夹角°|最大偏离起终点直线 q|历史H260 Progress|
|---|---:|---:|---:|
|23|47.786314|0.076517147|0.096665994|
|54|30.441527|0.068683764|0.102931440|
|89|8.981160|0.041464946|0.662249198|
|1|45.738882|0.047200470|0.376518298|

事实：分量裁剪PD不是直线跟踪。推测：参考/跟踪不适配可能参与Trial23停滞。未证明：这就是唯一原因，或航点一定改善。Trial1仍能推进，应保留这个反方案例。

### 尚未完成的资格

- 未定义并验证有限导航有效域/观测支持与 UNKNOWN 策略；不发明 bbox 自由空间。
- Trial23阶段A已有隔离CPU跟踪；未建立同QP/FAS跟踪、原生参考时效及授权绑定，不能泛化为真实机器人路线跟踪。
- 两参考同源CPU QP/失败语义准入已通过；没有CPU→GPU严格数值等价，也没有成熟A层的同参考全链对照；其原生权限不可由CPU算术继承。
- 本轮Trial23阶段A已冻结软件Goal阈值并评分，但旧实验没有该统一Goal评分；软件到达不等于FAS严格Terminal、native授权或物理成功。

### 上一准入阶段接线失败与修复（保留历史）

首轮导入 canonical_transition 的父包会连带导入 `stack_factory`；本任务import防线在其模块执行前拦截。改为按原文件绝对路径加载纯canonical模块后，通过相同测试。未修改源码、未实例化Factory、未放宽权限。保留 `logs/validate_attempt1.log`、第二次成功日志和 `WIRING_REPAIR_LOG.md`。

## 6. 证据位置、封印与复核入口

### 最新权威包

- 服务器：`/disk1/zlab/tmp/fas_trial23_same_source_qp_reference_cpu_diagnosis_v1/run_20261106T043951Z/`
- 本机副本：`C:\Users\zlab\Documents\Codex\research-output\FAS_TRIAL23_SAME_SOURCE_QP_REFERENCE_CPU_DIAGNOSIS_V1\run_20261106T043951Z\SEALED_RESULT\`
- 968工件清单自身SHA256：`aa14e341ec044142e021255a675155488e3022e63ee1372391c7621df755eb55`。
- 核心：`FINAL_SCIENTIFIC_ENGINEERING_VERDICT.md`、`SOURCE_QP_PARITY_AND_LIMITS.md`、`results/SCORECARD.csv`、`results/PAIRED.json`、`results/STAGE_A_VS_B.json`、`results/INDEPENDENT_CROSSCHECK.json`。
- 逐周期源矩阵/dual/raw64/issued32在`results/D|L/matrices/`，状态、reference、query及矩阵hash在各臂JSONL。新矩阵不能填入旧历史记录。
- `code/common.py`和纯算术/几何适配器只读复用上一封存包，外部依赖不可删除；参见`REPRODUCE.md`。`SEAL_RECEIPT.json`清单外回执。

### 上一阶段0/A包

- 服务器：`/disk1/zlab/tmp/fas_trial23_straight_reference_cpu_diagnosis_v1/run_20261106T041825Z/`
- 本机副本：`C:\Users\zlab\Documents\Codex\research-output\FAS_TRIAL23_STRAIGHT_REFERENCE_CPU_DIAGNOSIS_V1\run_20261106T041825Z\SEALED_RESULT\`
- 43工件清单自身SHA256：`543e247e50ae93df26cbc1f796dcb98ccf6fb57d9ba3aa373766affdf78dc7c5`。
- 核心：`FINAL_SCIENTIFIC_ENGINEERING_VERDICT.md`、`results/SCORECARD.csv`、`results/PAIRED.json`、`results/INDEPENDENT_CROSSCHECK.json`、`inputs/PREREGISTRATION.json`、`results/D/`与`results/L/`完整原始周期/查询日志。
- `REPRODUCE.md`给出只读复验；`SEAL_RECEIPT.json`清单外，避免自指。禁止在已封印包中重跑写出脚本。

### 上一准入权威包

- 服务器：`/disk1/zlab/tmp/fas_map_path_tracking_admission_v1/run_20261106T034059Z/`
- 本机封存副本：`C:\Users\zlab\Documents\Codex\research-output\FAS_MAP_PATH_TRACKING_ADMISSION_V1\run_20261106T034059Z\SEALED_RESULT\`
- 清单：`ARTIFACT_SHA256.txt`，50个文件；服务器和本机均已复验。
- 清单自身 SHA256：`ffa12c04c7c2a3669dbf1480591b76696ecdb21097906754b3b84fb37f962c03`
- 核心文件：`FINAL_SCIENTIFIC_ENGINEERING_VERDICT.md`、`MAP_PATH_TRACKING_CONTRACT.md`、`FOUR_ARM_COMPARISON_ADMISSION.md`、`FOUR_ARM_ADMISSION_DECISION.json`。
- 原始/表格：`results/GEOMETRY_QUERY_LEDGER.jsonl`、`GEOMETRY_RESULTS.jsonl`、`STATIC_GEOMETRY_RESULTS.csv`、`HISTORICAL_TRACKING_GEOMETRY.csv`、`INDEPENDENT_CROSSCHECK.json`。
- 运行入口与复核：`code/`、`REPRODUCE.md`。不要在已封印目录重跑写出脚本。`SEAL_RECEIPT.json`是清单外回执，避免自指；`tmp/`不在科学清单内。

### 关键上游（不同证据域，不合并分母）

|包|服务器目录|用途 / 状态|
|---|---|---|
|旧四对B/V回归|`/disk1/zlab/tmp/fas_system_frozen_independent_abba_native_regression_v1/run_20261023T024748Z/`|4对2080历史提交；当前已知开发任务，不称新holdout|
|Trial23整轨诊断|`/disk1/zlab/tmp/fas_system_trial23_full_trajectory_nominal_qp_liveness_diagnosis_v1/run_20261023T142306Z/`|近停滞c186–245、末60 Primary/OPEN与PD-QP冲突|
|旧路线预诊断|`/disk1/zlab/tmp/fas_system_mature_nominal_reference_route_feasibility_preflight_v1/run_20261023T152536Z/`|此前首条段因16次FULL上限UNKNOWN；旧结论不重写，新包另有39次通过证据|
|A/G H260|`/disk1/zlab/tmp/fas_pd_only_frozen_ag_h260_matched_system_regression_v1/run_20261103T023103Z/`|5臂1300提交、2完整配对；不能写8臂完成|
|旧三臂续跑阻断|`/disk1/zlab/tmp/fas_pd_only_ag_h260_remaining_three_native_continuation_v1/run_20261103T070720Z/`|历史资源阻断；不恢复旧目录|

上游清单自身SHA：

- B/V：`baf34cb21e5226af1854aa27daf51e4cbac8643936adce812673895fbe2a79fd`
- 旧路线：`c8d3c6939117d45d698779e4110b5d8993899083f871e2f59aaf73c0c8fcd7d7`
- A/G：`9e4cdf42775a3d1092f6dfa8ed81a0a6315ebd82e14cc438d9e0a9a91af24db2`
- 旧三臂资源阻断：`29e0c06d12242de2bd9bb92b8f58c08a77053567e690ca94dbeaed92eb47fb09`（历史记录，不据此推断当前资源）

上一准入阶段全量复验旧路线59成员和A/G 228成员；旧B/V只校验清单自身及直接消费的4个raw成员。最新跟踪阶段复验直接父包50成员与实际消费源，不宣称重新全量重算这些旧闭环。

### 地图资产

- 根：`/disk1/zlab/datasets/safer_splat_gdrive/outputs/stonehenge/splatfacto/2024-09-11_100724/`
- checkpoint：`nerfstudio_models/step-000029999.ckpt`，SHA `ac14f5ced354c93f26cf92404540712eff65bd02554d9e9ed0332508e290382d`
- 配置：`config.yml`；变换：`dataparser_transforms.json`。变换scale `.3333` 不等于已经标定米制尺度。
- CPU消费的有效参数：`/disk1/zlab/tmp/fas_system_native_qp_gpu_first_locked_11_pairs_v5/run_20261023T082659Z/results/GPU_EFFECTIVE_MAP_PARAMETERS.npz`
- NPZ SHA：`4c3b18e009f3bb85241a6dec7de67b4aff0b85f58b87b094e3616bcd8e4c43e0`；116446个Gaussian，数组与dtype/hash见最新`inputs/PREREGISTRATION.json`及上一准入包`inputs/API_QUALIFICATION.json`。

## 7. 四组对照的进入条件

拟议四组为直接目标/航点参考 × 无FAS/固定成熟A，四组都使用同一QP。前两个参考＋QP臂已在本轮隔离CPU域完成；后两个成熟A臂未执行，不能称完整四组完成。

1. 同一源QP、盒约束、量化、求解失败规则；不能用原无盒与有盒混称同QP。
2. 同地图、初态、最终goal、动力学与单位；两个航点组共享路径与跟踪规则。
3. 完整路径边检查、UNKNOWN传播、路径hash与参考有效期；实际动态跟踪资格。
4. 无FAS组只用独立软件模拟器，不借受保护PlantCommit绕过资格。
5. A层CPU诊断与原生权限/墙钟时效分开；如需原生验证，另取授权。
6. 同一组内比较参考影响；跨FAS层比较整层系统作用，不能单因归PSF。
7. 固定任务和预算；保留全部失败、右删失及未知。四Trial为开发任务，不把周期当独立样本。

## 8. 禁止覆盖、禁止运行与不能声称的内容

- 不覆盖任何历史sealed目录、manifest、raw receipt/trace或失败标志；新工作新目录。
- 不修改保护源码、地图、Profile、安全半径/CBF系数/Deadline/终端容差或默认OFF开关。
- 不自动运行GPU、Factory、Supervisor、Token、PlantCommit、训练、导航、A*、QP/PSF/FULL扩搜；有界CPU授权不等于原生/硬件授权。
- 不自动续跑旧H260待办，不对占用GPU排队、轮询、抢占或kill。
- 不把260提交当Goal Success；不把共享Oracle SAFE当物理无碰撞；不把dt=.05当实际20Hz。
- 不把静态路径条件通过当动态/递归可行；不把直连FAIL当无路；不把UNKNOWN当SAFE或碰撞。
- 不把同轨c220/c240/c259当独立试验，不将微小P2反事实收益累加为真实导航收益。
- 不把新GPU QP重放dual当旧现场记录，不把历史Full85继承给新方法。
- 不自动复制桌面。当前交接与结果在仓库/研究输出目录；另有明确复制请求时再执行。

## 9. 阶段结束维护流程

1. 先读本文件，按当前任务范围核对源，不把交接当原始事实替代品。
2. 更新当前目标、状态、版本、实际结果/分母、数据路径/清单SHA、失败与阻断。
3. 明确本会话任务已结束还是仍在运行；没有检查服务器全局进程就写未检查。
4. 下一步写 `NOT_STARTED`、授权边界与进入门，不写后台自动承诺。
5. 保留旧失败，必要时追加“新证据改变哪条判断”，不要回改旧封印包。
6. 刷新时间与更新者，检查Git diff只涉及本轮文档；仅stage交接相关文件，提交并以非强推方式同步GitHub默认分支，核对远端SHA与文件。分支保护不允许直推则提交PR并说明尚未合入。若本轮明确只读，遵守只读并在回复注明未更新。

### 阶段更新记录

- **2026-11-06 / Codex / PID3142527明确授权与信号拒绝**：完整核对目标身份和start_ticks后尝试一次SIGINT，系统返回EPERM，信号未发出；失败后复查目标仍在。未通过sudo/docker/SIGKILL绕过。3件工件封印，清单d93d045b…；实验未启动，权限与资源问题未解决。
- **2026-11-06 / Codex / 明确PID中断授权核查**：授权目标2990859已退出，GPU1新PID3142527占4372 MiB，依用户“其他占用即停”条件终止准入。未发信号、未自动转GPU0、未启动实验。4件阻断工件封印，清单0cfa6ac2…；源和旧包未改，无后继。
- **2026-11-06 / Codex / Trial23 GPU0改设备准入**：用户仅把设备改为GPU0，其余预算不变。05:27:22 UTC物理GPU0已有PID2972493占4372 MiB，停止不排队。额外只读定位了worker两处写死GPU1与逻辑cuda:0，未改代码/初始化CUDA。4件阻断工件复验，实验计数全0；旧GPU1包清单SHA不变，无自动后继。
- **2026-11-06 / Codex / Trial23固定成熟A两参考原生准入**：用户明确批准1次GPU1会话、2 Factory、≤1000提交、≤2000求解/50000几何调用；首次资源门发现GPU1 PID2990859占4372 MiB，按合同停止。新实验计数全0，来源完整复核/接线/CPU测试/D/L运行均未开始。6件阻断工件封印，不排队、不自动恢复；旧CPU结果及53次量化正残差边界不变。
- **2026-11-06 / Codex / Trial23同源QP阶段B**：完成源求解器/六盒行准入、D/L各一次有界CPU运行、矩阵/KKT只读诊断、15600项复核及968工件封印。D500步未到达；L416步软件到达；916/916运动段源SAFE。明确53次微小量化半空间正残差、CPU/GPU非逐位等价、D量化停滞及L超调。新QP920/FULL1835，GPU/Factory/Token/PlantCommit均0。下一步成熟A同参考对照仅建议，NOT_STARTED。
- **2026-11-06 / Codex / Trial23阶段0/A**：用户授权后完成无QP/FAS的D/L隔离CPU诊断。D38个接受步后c38待推进段UNSAFE；L368个接受步及软件阈值到达。总413FULL、17合同测试、4099独立复算、43文件封印；3保护HEAD/47文件不变；全部原生权限0。四组仍未就绪；下一步只建议同源QP准入及两参考对照，NOT_STARTED。
- **2026-11-06 / Codex**：首次建立固定交接与AGENTS维护规则。登记最新地图/路径/跟踪CPU准入包：Trial23直连条件通过、其余三直连有不安全见证；57合同测试、91复核、65FULL；四组未准入；无新原生执行。按用户澄清改为GitHub正式维护，仅文档提交推送；既有本机dirty完整保留。
