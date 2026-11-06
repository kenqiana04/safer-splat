# FAS / safer-splat 固定交接文档

> **先读结论：** 最新授权任务已实际完成服务器CPU接入与有界准入，裁决 **COMPLETED_BOUNDED_ADMISSION_WITH_NEGATIVE_RESULT / APPLICABILITY_LIMIT_STATIC_LINE_REJECTED**。8项接口检查PASS；固定6请求中4个端点PASS、Trial17直线FAIL（FINITE_UNSAFE_WITNESS）、Trial53直线因首个非PASS停止而NOT_RUN。7次FULL、几何进程4.529989s，四臂GPU全部未启动。不是停在计划，也不是成熟A运行失败或“收益只能在Trial23”的证明。旧Trial23 D500/L417实际结果与全部失败保留；本次39件封印完成、进程退出，无自动后继。

- 正式维护位置：**https://github.com/kenqiana04/safer-splat/blob/master/HANDOFF.md**；本机文件只是工作副本，阶段更新须同步到 GitHub。
- 最后更新：**2026-11-06 19:20，Asia/Shanghai**（Git 提交记录提供精确发布时间）。
- 更新者：**Codex，本 safer-splat 会话**。
- 本次文档变更：补记新授权Trial17/53的真实CPU准入否定结果、立即停止、零原生执行及封存；仅提交本交接文档，不发布研究代码、不改变默认配置。
- 最近实测阶段：CPU准入`run_20261106T111343Z`，5/6请求实际完成、7FULL，39件封印。最近原生仍是Trial23 `run_20261106T095437Z`的917真实提交；未重跑旧12场景或旧D/L。
- 状态依据：本会话4090服务器实际记录、独立只读复算和封印核验。**今后项目实验、测试及计算默认在4090服务器执行；Windows仅作连接客户端和获授权的文档/Git维护。设备选择和实验资源仍须遵守当轮授权，不是无限GPU授权。**

### 最新实际阶段：Trial17直线准入FAIL，按合同停止四臂计划

- 用户在本轮明确授权CPU准入及全部通过后的四臂GPU，正常SSH按原`zlab-4090`配置建立；主机`zlab-Super-Server`、UID1000。既有会话正常退出不是连接拒绝；本轮没有访问拒绝、提权、换账户、安装依赖或物理设备操作。
- 新DEV：`/disk1/zlab/tmp/fas_fixed_a_dl_independent_task_replication_v1/run_20261106T111343Z/`。39成员清单SHA **`910aea7c87f4c65a77ad3dd90710505da69cf6d0193e462b13b0458418fbf0d2`**，系统sha256sum与独立逐项摘要通过；清单外`SEAL_RECEIPT.json`不自指。旧规划6、几何50、原生102成员先复验；三保护HEAD和联合97锁定来源文件前后相同且clean，旧sealed内容与所有历史失败不变。
- 固定输入17/53、最终goal和map/profile/6D字节身份未变，原半径.015q、reserve0及source geometry参数不变。新DEV复用原`GSplatLoader.query_distance`的AST与`SourceGaussianBarrierAdapter`、`ConservativeSignedDistanceIntervalBackend`；只增加输入验证、累计计数和首非PASS即停/NOT_RUN记录，diff落盘。不创建规划器、不调前视、不删Gaussian、不改认证。
- 8项接口检查 **8 PASS/0 FAIL/0 NOT_RUN**，1测试进程、含启动0.216525775s/120s、临时数据0B。覆盖源状态哈希/字节、错goal/map、q/m和半径、重复任务/错顺序、FULL/超时上限入口、CPU/OFF/停止分支静态检查、实际Reference类的D/L同task goal与过期cycle拒绝；不是GPU原生资格验证。未重跑观察器旧12项。
- 几何执行顺序为四端点，然后17完整线段，再53完整线段。四端点均PASS，每点1次FULL；17完整线段在第3次FULL返回 **CERTIFIED_UNSAFE / FINITE_UNSAFE_WITNESS**，立即停止。计划6请求、完成5：**4 PASS / 1 FAIL / 0 UNKNOWN / 1 NOT_RUN**。53直线为`STOP_AFTER_FIRST_NONPASS`，不得写成PASS、FAIL或已检查。
- 17失败见证：线段比例 **0.75**（不是时间秒）；float32点`[-0.17256511747837067,-0.2027648538351059,0.054894015192985535] q`，字节`e9b430be97a14fbe8cd8603d`；原FULL最小h **−0.0002249742392450571 q²**；checkpoint行61489只是Gaussian数组索引，不是物理障碍ID。这是有限源查询触发的否定，不是保守区间尚未收敛、超时或UNKNOWN；仍仅共享Gaussian CPU表示域，不是GPU严格误差/物理碰撞证明。
- 几何总计 **7/132 FULL**、1进程含启动/导入/加载 **4.529989288s/300s**，17线段自身0.909709094s。CPU Torch2.1.2+cu118、1线程、CUDA_VISIBLE_DEVICES空、cuda_initialized=false；编译支持CUDA不等于使用GPU。逐次START/RETURN计数7/7、全部116446 Gaussian、无缺账/重试。纯日志独立核算0.065352425s，复核输入与.5/.25/.75查询点字节、失败h和停止后无新增调用，新增几何0。
- 初始被动资源快照GPU1为既定UUID/PCI、6MiB、无compute进程；没有重复本任务worker。但CPU准入失败，故**17-D、17-L、53-L、53-D全部NOT_STARTED**；GPU会话/Factory/Token/PlantCommit/P0或PSF求解/原生几何均0。没有“GPU阶段资源不足”或“成熟A失败”；也没有可报告的H260、到达、停滞、后备或执行净空，指标为NOT_EVALUATED，不填性能0。
- 科学含义：起终点SAFE不推出直连SAFE；此固定两任务方案未满足参考适用条件，不能回答跨任务D/L增益。既有Trial23的收益保留，但不能据本次断言收益仅限Trial23、Trial17无绕行路径或FAS全方向失败。必须保留54/89/1旧直连否定，不换17、不补查53、不补跑剩余GPU授权。
- 核心工件：`FINAL_REPORT.md`、`results/ALL_SIX_REQUESTS.csv`、`GEOMETRY_QUERY_LEDGER.jsonl`、`GEOMETRY_RESULTS.jsonl`、`INDEPENDENT_ACCOUNTING.json`、`RESOURCE_SUMMARY.json`、`NATIVE_ARMS_NOT_STARTED.json`、`SOURCE_LOCK.json`、`PROTECTED_BEFORE/AFTER.json`、`inputs/GEOMETRY_DRIVER_DIFF.patch`与可复核代码。无本轮运行错误或结果导向修复/重试；所有计算子进程exit0，SSH已正常结束，无自动后继。

### 上轮规划阶段（历史保留）：两任务四臂设计锁定

以下“尚未授权/待准入”是上轮时点；本轮授权后已执行上述CPU准入并因FAIL关闭该计划，不能把旧预算描述当作继续运行许可。

- 服务器包：`/disk1/zlab/tmp/fas_fixed_a_dl_independent_task_replication_plan_v1/run_20261106T105714Z/`。6件文档/JSON清单SHA `87e061cc9a67c2f39aa8a6990f4566907f0302c7b28baaf24f438c25f5709618`；系统sha256sum与独立逐项摘要通过，清单外`SEAL_RECEIPT.json`不自指。这是方案封存，不是新增实验PASS。
- 实际只读核查：最新原生包102成员、地图准入包50成员完整复验；历史Full85的2831成员仅核验直接消费子集，未全量审计。34个消费来源、三保护HEAD/38文件及3地图资产前后相同，工作树clean。源码/身份计算全部在`zlab-Super-Server`完成，未导入运行时，未运行任何测试、CUDA、GPU/Factory/Token/PlantCommit、求解或FULL。没有探测当前GPU资源，不假定未来空闲。
- 选样来源：历史`fas_vnext_corrected_full85_v1/run_20261011T153359Z/EXECUTION_LOCK.json`，SHA `a9f3e02a6ee27749447525b070a29fdd95fbf2d1a9cdd98d02bafb3819460de4`。85个ID排除既有COHORT列出的12个DEV来源及23/54/89/1共16个，剩69；按固定salt `FAS_FIXED_A_DL_INDEPENDENT_TASK_REPLICATION_V1` + `:` + 十进制ID的SHA排序取前二，得到 **17、53**。完整排名/排除理由/6D字节锁保存在`SELECTION_AND_ORDER_LOCK.json`。
- 两任务的初始零速度、原goal/map/dt、canonical state identity与历史首trace一致；未复用旧控制器成绩作为成熟A基线。选择先于读取个体历史结果；之后读到旧终点/首角色，未改变选样。它们是新增参考比较任务，**不是全项目未见过的holdout或独立环境样本**；来自同地图环形任务族，53与54相邻，相关性保留。不得根据后续结果换样本。
- 旧直连：Trial23共享CPU条件PASS（39 FULL）；54/89/1为`FINITE_UNSAFE_WITNESS`（4/7/7）。均属既有结果，且全部`route_qualified=false`、全局地图支持域UNRESOLVED。新17/53直线及端点为NOT_CHECKED；旧500步轨迹不证明直线安全，静态PASS也不等于动力学可跟踪或真实物理无碰撞。
- **唯一建议的下一步，尚未授权/启动**：固定17/53各起点、终点、完整直线，共6个顶层CPU请求、最多132次实际FULL（4点+两线各64）、计算墙钟≤300s、1进程、无重试/替换；单点≤15s、单线≤90s，计数无法可靠约束则不启动。任一FAIL/UNKNOWN/超限/身份问题停止该复验计划，不搜索绕行、不调参数。另最多8项新输入/顺序/计数接口检查，≤120s、2进程、16MiB；复用观察器12项旧证据，不重跑套件。
- **仅在两任务准入通过后可另行批准的原生预算建议**：T17-D→T17-L→T53-L→T53-D；GPU1单会话、4独立Factory、每臂≤500周期/600s，总尝试/提交各≤2000、求解≤4000、几何调用≤100000；会话≤2700s（45min），2400s后不入新周期。初始化、失败、后验和全部持久化开销计账；联合上限可能导致删失，不能承诺满额。此预算不是旧两臂授权自动翻倍。
- 固定同一原生GPU数值栈与成熟A、原TieredPSFWitness、optional guard=false、冻结.02q直线前视和实际PD算术/dtype、最终task goal、半径/Terminal/Deadline/身份链。四臂状态/后备/Token/缓存独立，同seed0；只读磁盘缓存同SHA，记录冷热与顺序影响。旧CPU53次量化残差与CPU/GPU非逐位等价继续分域，不计算跨域FAS单因素收益。
- 主要指标：每任务有实际共同H260时的Progress差L−D；提前停止不补终态、不伪造H260，另列实际共同长度、软件到达、末60步/near-stall、角色与拒绝、Oracle、完整wall/关键区间时效。只有2任务，不做周期独立样本推断或显著性；方向一致与工程幅度分开，数值持平容差1e−6不等于有用增益，.01 Progress仅为事前建议的实用幅度标记。若一正一负则STATE_DEPENDENT；路线准入失败则APPLICABILITY_LIMIT，不将它误当控制性能失败。
- 未来最小接线缺口：旧`prepare.py:57`硬编码23/89/54/1，旧session仍为2Factory/1000/2000/50000，必须在另行授权的新DEV中显式接入17/53身份与4臂预算；本轮未实施。不得改成熟A/安全门或静默沿用旧PARITY里的A/G描述。关键证据：最新`instrumentation.py:7–24`、`native_worker.py:127–154`；Candidate smoke`:438–445`与runtime_types`:162–183,260–263`。
- 文件：`FINAL_REPORT.md`、`SOURCE_LOCK.json`、`SELECTION_AND_ORDER_LOCK.json`、`PROPOSED_BUDGET.json`、`READONLY_CROSSCHECK.json`、`REPRODUCE_READONLY.md`。SSH正常结束，没有测试/实验子进程或后继。首个非TTY交互stdin关闭发生于项目命令前；随后同一账号配置TTY成功，无访问拒绝/提权。所有旧失败原件保持不变。

### 最新原生诊断：修复观察器后D/L均完成

- 目录：`/disk1/zlab/tmp/fas_trial23_fixed_mature_a_observer_repaired_native_pair_v1/run_20261106T095437Z/`。102成员清单SHA：`7c073167c4ca89ca28bddcc8761e3a641450ddd2a01554d8bd44e9135febfd35`。系统sha256sum及独立逐项摘要均通过；清单外`SEAL_RECEIPT.json`明确排除自身、清单、缓存/tmp。缓存身份单独锁定。
- 固定H260来源成熟A `FAS_MATURE_NATIVE_PSF_RECOVERY_DEV_V1`，`experiment_arm=A`、optional guard=false、原TieredPSFWitness、原deadline及失败语义。D→L，每臂上限500；最终goal相同，L仅使用冻结.02q直线前视nominal输入，不增加Planner。原保护源码和默认开关不变；独立DEV worker只解除本次授权入口阻断，observer核心与CPU封存同SHA。

|指标|D直接目标|L直线前视|
|---|---:|---:|
|实际尝试/提交|500/500|417/417|
|停止原因|500上限，未到达|软件到达，非严格Terminal|
|共同H260 Progress|0.0966663398720|0.6880003190347|
|实际终点Progress|0.0966680470970|0.9971743411106|
|终点距离q / 速度q每模型秒|0.708397248474 / 2.01357e-7|0.002215895249 / 0.001517444928|
|Primary / retained Backup|500 / 0|416 / 1|
|PSF尝试 / 支撑Primary提交|59 / 59|3 / 3|
|Oracle SAFE/UNSAFE/UNKNOWN|500/0/0|417/0/0|
|字节静止周期 / 最长连续|198 / 194|1 / 1|
|末60步ΔProgress|0|0.0462238963621|
|near-stall窗口 / 所有60步窗口|258/441|0/358|
|entry→PlantReturn p50/p95/p99/max ms|340.089/445.113/509.426/835.851|434.301/499.142/690.536/1728.087|
|guard→transition p50/p95/max ms|0.900/1.041/1.446|1.009/1.152/1.542|
|最小共享Oracle clearance q|1.97581749e-7|0.00994886074485|

- 软件到达：距离≤.01q且速度≤.005q/模型秒连续10步；L在第417次提交满足，不能写成1e-12严格Terminal。D首次near-stall窗c183–242；该新运行不改写旧V轨迹的c186–245。
- 首次nominal和QP字节分歧均c0，后续状态自然分叉。L c56：Primary C0/L2/L3 PASS，最终guard620.615302ms=WARNING，原路由`CERTIFIED_NAVIGATION_NOT_TIMELY_USE_VALID_RETAINED_BACKUP`，retained Backup于transition621.359376ms执行，仍在800ms后备时限内。这不是非法提交。其余916次最终OPEN；实际transition超过各角色门限0次，Boundary0、未决提交0。
- D59次、L3次原制动均在同一Terminal速度证书失败家族触发PSF，全部见证PASS并支撑同一候选Primary首控；不是62种失效，也非执行62条预测整尾。L事件为c380/c382/c408。C0/L1/L2/L3最后结果917/917 PASS，事务COMPLETE/Token APPLIED/trace RECORDED逐条核对。
- 新D c87：guard227.258861ms、transition228.088336ms；旧c87同步日志干扰未复现，但没有无观察器随机对照，不能把新旧差当严格观察器因果效应。持久化成本未消失：L c12 entry→PlantReturn1728.086734ms，其中entry→epoch1336.045640ms、intent→ack1335.665022ms；原epoch后transition391.564022ms。区间仍含调度，不归因单一fsync，不事后扣时或声称硬实时。
- 预算：GPU1会话1、Factory2、尝试/提交917、solve979（D559/L420）、geometry API调用11075（D4761/L6314）；会话702.492992s，D348.960899s/L352.703659s，均未触上限。Factory init4.252002s/4.361256s。GPU1 UUID/PCI核对，logical0映射物理GPU1；采样显存最大1764MiB，非严格峰值。两臂torch peak allocated129047552B/reserved148897792B。没有GPU0实验或终止其他进程。
- 观察器917 intent/outcome闭合，真实收据与state/candidate/action/goal/参考摘要、Token后继、单次Plant、binary32 Euler核对；两个trace FINALIZED。保护3HEAD/38文件及原运行37文件/地图/Profile前后一致、clean，运行code lock未变。新增CPU测试0；事后纯数据复算不调用GPU/solver/geometry。
- 事后补充解析初版错误：将参考内部ID误比为整个参考记录SHA、将plant_calls列表误当数字；依worker136–139/151/154行修正纯解析，V1失败文件与V2通过输出均封存。另有创建补充脚本的绝对patch路径拒绝，改为任务目录相对路径；无修改raw或重跑原生。不得删除失败记录。
- 当前原生issued32正半空间残差D38/500、L11/417，最大5.111410184e-10 / 4.03149513772e-10；旧CPU53次另列，未clip或放宽阈值。CPU/GPU非逐位等价，不能拼成严格四组FAS单因素增益。
- 结论仅是：本已知Trial23中，参考收益能通过固定成熟A完整原生软件资格链；D仍可合法微动趋停。原系统不用Planner仍可作为安全过滤研究；本次直线参考不是新路径规划算法。三任务进程3342040/3342192/3347611已退出，无自动后继。会话刚结束时compute表空；稍后正式封存快照显示GPU0有其他作业PID3360988占1620MiB、GPU1无compute进程；未干预该作业，不能声称整台服务器持续空闲。
- 核心文件：`FINAL_REPORT.md`、`results/SCORECARD.json`、`results/PAIRED.json`、`results/TRANSACTION_TIMING_AUDIT_V2.json`、`results/PER_CYCLE_TIMING_V2.csv`、`results/RESOURCE_SUMMARY.json`、`SOURCE_LOCK.json`、`SEAL_RECEIPT.json`。

### 服务器观察器 CPU 阶段：12/12通过；后续收尾已完成（旧故障保留）

- **后续补齐记录**：在同一服务器包完成3个保护HEAD/工作树及38文件后置核对，全部与前置一致；原31件工件未改，新增测试0。40件清单经系统sha256sum及独立摘要复验。清单SHA `6fe629588f4d1754643e1bf27abfc370a81ff1b3f5485118ea9913e52c077349`，清单外`SEAL_RECEIPT.json` SHA `b3d7808b6f4b28aa71356e48a57f7d5a386ff9d62524c6758e0196509d9b9cac`。
- 补齐时finalizer在哈希全部通过后，因中文“成功”不匹配英文`OK`断言退出1；未修改清单或重跑测试，独立逐文件哈希复核后完成清单外回执，保留该故障。收尾至封存225.550199s，非原测试成本。服务器GitHub fetch曾发生GnuTLS -110，未换路重试，待发布补充保存在`/disk1/zlab/tmp/fas_handoff_cpu_closeout_publish_v1/run_20261106T093743Z/`。本次后续任务统一补记GitHub；不是把当时发布失败改为成功。
- 以下段落保留**最初测试结束时的状态**；其中“未封印/后置待核验”已由上述补齐记录解决。CPU证据仍不赋予GPU准入，也不证明掉电/跨重启exactly-once或真实GPU时效。

- 目录：`/disk1/zlab/tmp/fas_dev_observer_server_cpu_validation_v1/run_20261106T091159Z/`。实际主机 `zlab-Super-Server`，用户 `zlab` / UID1000，解释器 `/usr/bin/python3`；使用正常 `zlab-4090` 通道，无提权、无访问拒绝。今后项目实验和测试仅在服务器运行；Windows仅用于获授权的文档/Git维护，不继续本机测试。
- **CPU结果12 PASS / 0 FAIL / 0 NOT_RUN，进程exit=0**。仅1个测试进程；套件内部墙钟1.2304334838408977s，含进程启动1.2803700200747699s；临时测试数据20,719字节。预算120s / 最多2进程 / 16MiB；内部100s监护、外部115s超时。没有自动使用剩余额度。
- Linux `monotonic` 与 `perf_counter` 均报告 `clock_gettime(CLOCK_MONOTONIC)`、不可调整、分辨率1e-9s；这是时钟元数据，不是准确度或WCET保证。慢写测试仍用20/20/40ms阈值，未放宽：周期前持久化52.195191ms、协调返回后持久化53.480603ms、总区间105.727554ms；两个25ms注入实际25.138740/25.139309ms。不把Windows的16ms现象直接归因于Linux时钟，不扣除日志耗时。
- 12项依次为：①正常及intent ack先于模拟epoch；②重复/身份错配；③关键区间零同步文件I/O；④慢持久化完整计时；⑤部分写；⑥write/fsync失败；⑦提交前模拟中断及未决不重放；⑧提交后模拟异常及被事务吞掉异常的停止锁；⑨outcome确认丢失；⑩容量耗尽/超大结果；⑪汇总滞后保留真实模拟收据；⑫精确DEV wrapper接线。全部PASS，但故障使用模拟回调/同进程SystemExit，不是真实崩溃或掉电测试。
- 精确wrapper函数由AST抽取后配模拟依赖执行，**没有导入完整原生模块或执行成熟A**。Token/trace仅模拟标记。`native_worker.py`仍无条件阻断`--dev-native`，默认OFF；GPU/CUDA初始化、真实Factory/Token/PlantCommit、求解器和硬件操作均0。
- 设计：进入原`run_cycle`前确认唯一持久化审计意图（不是Token/动作授权）；Plant关键区间仅有界内存观察；原协调调用、Token/事务/trace完成后持久化outcome，确认后才可进入下一周期。未决意图禁止自动重放。原epoch、成熟A、goal/参考、deadline及安全门不变；原恢复枚举内部I/O未被本观察器修复删除。
- **收尾失败**：测试完成后发送中文后置核验/报告/封印脚本，服务器读取stdin时出现 `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xd5 in position 856: invalid continuation byte`（`/usr/lib/python3.8/codecs.py:322`），脚本尚未执行，SSH随后exit=1。不是权限拒绝、不是测试失败，也不能据此说服务器断开。没有重连重试。
- 因此 `PROTECTED_AFTER`、前后比较、`FINAL_REPORT.md`、`ARTIFACT_SHA256.txt` **未完成/未生成**，最终清单SHA为 **NOT_AVAILABLE**。不得推定保护前后相等；只确认运行前38个源哈希和3个HEAD匹配、clean。地图/Profile本阶段未加载、未重算。代码只写新DEV目录不等于后置哈希验证已经完成。
- 已落盘：`SOURCE_LOCK.json`、`SERVER_CONTEXT.json`、`checkpoints/PROTECTED_BEFORE.json`、`results/CPU_RESULTS.json`、`results/S04_COMPONENTS.json`、`results/LAUNCH_RECEIPT.json`、`logs/CPU_STDOUT.log`、`logs/CPU_STDERR.log`、`tests_data/*.jsonl`、`PLAN.md`及`code/`和原版本`inputs/`。这些是未封印证据，不伪造最终清单。
- 当前DEV代码SHA：`cycle_audit.py`=`535f7a18446634d191103fc6ba5cc9e35ebf82ba0c0b38eda43511214ccb9141`；`native_worker.py`=`3ad63eda587c1cce83a12f522c28c91eb8679b2d9f8fffcf8f956df8497849ac`；`test_cpu.py`=`1fbfb911acadd1ff50df07c0dce7eeaad598abe3a68b9f6c12660a77938c0696`。单文件哈希不是完整包封印。
- 保护HEAD（仅本阶段前置已核验）：Candidate `33e34a3ac8d710452775ffe688af77393f734fa9`；Frozen `481c3e5e24648d0219e1969f1145648ac99f6943`；Perf `b0a6bbb96512cef5085feada98a900bf9d8ff15f`。后置状态待核验。
- 测试子进程已同步等待退出，随后SSH也退出；没有本任务遗留测试或自动后继。没有核查服务器所有其它作业。CPU通过不证明真实GPU时效、磁盘与Plant/Token原子提交、跨重启exactly-once或掉电恢复；D/L新原生运行仍需独立准入和授权。

### 保留的观察器 Windows 阶段（不与服务器证据合并）

- V1：`C:\Users\zlab\Documents\Codex\research-output\FAS_DEV_OBSERVER_INTENT_OUTCOME_CPU_V1\run_20261106T082207Z`，3 PASS / 1 FAIL / 8 NOT_RUN；第4项慢写计时断言失败。1测试进程、约0.156s、9182字节；35件封印，SHA `9e984f0472810c38d9e4d17e7836e2347794d52ebe8783fe519b7f23c9c58d43`。原裁决保持PARTIAL，不追溯改判。
- V2：`C:\Users\zlab\Documents\Codex\research-output\FAS_DEV_OBSERVER_CPU_FAILURE_RESOLUTION_V2\run_20261106T085252Z`，4次固定计时探测后12场景通过，总2测试进程、约0.4431371s、27399字节；用户要求改为仅服务器后未封印。Windows `GetTickCount64`报告15.625ms分辨率，25ms注入曾读出16ms，而同区间`QueryPerformanceCounter`为25.1874/25.253ms；旧断言在4探测中2次为假。修正测试测量而非放宽20/40ms阈值；该Windows解释不自动覆盖Linux。
- V1/V2与服务器新预算分别记账，旧失败和未封印状态保留；不得将Windows测试写成服务器原生集成验证。

### 上一次原预算运行（历史保留）：D 88步，观察器时效干扰导致停止

- 服务器包：`/disk1/zlab/tmp/fas_trial23_fixed_mature_a_reference_native_pair_v1/run_20261106T073852Z/`；本机research-output同名目录下`SEALED_RESULT/`完整副本。76件封印SHA：`d91e07014697826d9907a9b22326e2a4287da38a6a23ffa4a94d3fce2f6e4988`。
- 现场GPU1空闲、物理UUID/PCI映射通过，已修复代码及同SHA离线缓存复用；12项CPU检查通过。固定A、optional guard false、原TieredPSFWitness运行身份已落盘。三HEAD/37保护文件前后clean且哈希一致。
- GPU会话1、Factory1、尝试/提交88、求解92（88P0+4PSF）、几何API调用1022。会话140.217s，D139.830s，初始化59.453s；未超过任何预算。GPU1采样最大1764MiB，不是严格峰值。
- D全部Primary，C0/L2/L3 PASS各88，最终guard OPEN88；4次PSF见证支撑4次Primary首控提交。Oracle SAFE/UNSAFE/UNKNOWN=88/0/0。实际终点Progress=.0870109418862、距离=.715970396681q、末速度=.00758140283623q/模型秒；H260未覆盖。L NOT_STARTED，不能完成配对结论。
- 首次阻断c87：guard236.460774ms；observer写日志前236.995104ms；原Plant入口695.532655ms；transition入口696.802104ms；返回697.844807ms。原OPEN阈值600ms；异常不是EXPIRED（800ms）。实际已提交后任务监测停止，不能写成预先拦截。
- `native_worker.py:110–115`提交前同步append/flush/fsync及调度区间458.537551ms，占guard→transition460.341330ms的99.608%。这不是孤立fsync测量、也没有无观察器对照，但强烈限制时效归因；本次不能估计无仪器化A性能。下一步只建议DEV观察器非干扰修复，不修改Deadline/安全门，不事后扣时。
- 独立收据复算及Token后继身份核对通过，Trace FINALIZED88不等于合法时效PASS。原NATIVE_RESULT.final_state因停止前未更新仍为cycle87，实际最后receipt为cycle88，端点以receipt为准；原timely_new_method_navigation88只是guard采样口径，实际transition OPEN87/88。
- 本轮issued32正半空间残差29/88，最大5.111410184e-10；与旧CPU53次分开。最小共享Oracle clearance约.007172765861q；不证明物理安全、严格GPU误差或20Hz。
- 父子进程退出、GPU资源释放、无自动后继。日志问题定位不授权再跑D或启动L，未进行结果导向重试。文档检查点`codex/checkpoint-before-trial23-native-stop-20261106T073852Z`，基于`ebc5b5aa0037731223585dfca20ad37d2f976fe4`。

### 前次获授权修复重试：设备门通过，Factory缓存失败

- 服务器包：`/disk1/zlab/tmp/fas_trial23_fixed_mature_a_reference_native_pair_v1/run_20261106T073111Z/`；同名本地research-output下`SEALED_RESULT/`。61件封印SHA `c8ce7117b2886ebd474af877ea5f053cff1d26e634a7196a19aed0438de11a6b`。
- 修复仅DEV设备绑定：使用物理GPU1 UUID设置可见设备，调用已有libcudart获取逻辑0 PCI，再与nvidia-smi UUID/PCI交叉核对。保存`DEVICE_MAPPING_RAW.json`实测PASS；PID表空不再单独判错设备。12项CPU检查（原10+PCI正负2）通过。
- 源228/968项及3HEAD/37文件匹配；保护前后相同、clean。D PID3207028进入Factory初始化，nerfstudio的LPIPS构造因隔离TORCH_HOME漏复制旧缓存而请求AlexNet下载，offline_gate拒绝。没有放网、安装、替换组件或改变安全语义。
- GPU会话1，Factory尝试1/完成0，控制周期0、PlantCommit0、solver0、geometry0；L NOT_STARTED。墙钟20.144743秒。没有D/L Progress或A层恢复/权限结论。
- 失败后只做CPU文件操作：原H260与/home/zlab缓存同名244408911字节文件的完整SHA一致，复制到新任务独立缓存并复核；见`results/OFFLINE_CACHE_REPAIR.json`。这是当轮接线修复，不是缺依赖安装；补齐后未再次启动CUDA/Factory。
- 一次重试已消费，父子进程退出，资源释放，无自动续跑。旧49件失败包不改。若后续继续，须新授权、新目录、新资源门，复用两项DEV修复，不扩大试验。文档检查点`codex/checkpoint-before-trial23-cache-stop-20261106T073111Z`，基于`f4cdcb58a9cff99d47fb26fb360960ca9dce4a60`。

### 前次GPU1释放后尝试：设备身份门失败，已结束

- 包：`/disk1/zlab/tmp/fas_trial23_fixed_mature_a_reference_native_pair_v1/run_20261106T071541Z/`；本地同名研究输出根下`SEALED_RESULT/`为完整下载副本。
- 来源：H260的228项、上轮CPU参考的968项封印全量通过；三保护HEAD和37个源/地图/Profile文件匹配且前后clean。10项CPU接口/算术/静态检查通过，不是原生权限PASS。
- GPU1物理UUID `GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d`、PCI `00000000:82:00.0`、4090；启动前6MiB、无compute进程。本轮未发送进程终止信号。D→L事前锁定，A核心身份及默认OFF不改。
- D PID3189781，`code/native_worker.py:51`失败。查询设备属性后要求本PID出现在计算进程表的新增断言未通过，16次父进程采样compute表为空；显存采样最大8MiB，不是负载峰值。worker即时device_rows/逻辑设备UUID未落盘，不能确诊错GPU。延迟上下文或监控可见性是假设，不是已证实根因。
- GPU会话1/Factory0/周期0/提交0/求解0/几何0；D无轨迹，L NOT_STARTED。不存在可报告的Progress/两臂首次认证分歧。79.524438秒，无结果导向重试；父子进程已退出、GPU计算进程表为空，无后继。
- 独立核算仅验证零执行、代码锁、保护快照及计数，不虚称完整轨迹审计。49件封印复验，清单SHA `7f52db8c6a0c27fb7907ad1034d92e4a6062258bcba32c8de3215c075e97d5cf`。主文件`FINAL_REPORT.md`、`results/INDEPENDENT_CROSSCHECK.json`、`GPU_SESSION_RESULT.json`。
- 下一步仅建议修复DEV逻辑UUID/PCI证据采集；不删除安全检查，不重构A，不延长时限。新的CUDA验证或D/L执行需另行明确授权，不在本包重启。文档检查点`codex/checkpoint-before-trial23-device-gate-20261106T0730`，基于`f303b4b4a10fe422a4236fb3f004adaf4e321674`。

### 历史PID3142527中断授权：系统权限拒绝（随后负责人释放）

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

最新状态：**COMPLETED_BOUNDED_ADMISSION_WITH_NEGATIVE_RESULT / APPLICABILITY_LIMIT_STATIC_LINE_REJECTED**。17/53已实际做CPU准入，17直线FAIL使53直线与全部GPU臂停止，见文首。最新实际原生状态仍是**COMPLETED_BOUNDED_PAIR_WITH_LIMITS**，Trial23 D500/L417，不是本轮新增提交。CPU观察器收尾已补齐，但其证据不等于原生权限；原生资格来自此前新授权与实际链路。以下为保留的较早CPU参考结论，不与新GPU数据混成四组：

`PASS_SAME_SOURCE_CPU_QP_REFERENCE_DIAGNOSIS_WITH_LIMITS`

`REFERENCE_TRACKING_GAIN_SURVIVES_SOURCE_QP_IN_THIS_CPU_CASE`；仅Trial23已知开发任务、固定参数。16项准入检查、两组916个接受模型步、15600项独立复算与968文件封印。新CPU QP920次（含准入4次），FULL1835次（含准入3次）；另1次注入求解失败测试不计真实求解。PSF/Factory/Supervisor/Token/PlantCommit/GPU/A*均0。最终task goal始终不变。

### 推荐下一步——尚未执行

**本次授权任务已依科学停止门结束，不续跑剩余查询或GPU。唯一下一步建议：先明确研究目标是“合格直连任务的跟踪”还是“包含绕障的成熟参考比较”，据此另行批准新的适用域/路线方案，NOT_STARTED。** 不换17、不补查53、不重复Trial23求好结果，不重跑旧CPU两组，不自动接A*或继续局部LP/PSF筛选。现有证据不足以把直线追踪当作一般导航参考，任何问题定义变化都不能冒称本轮既定复验。

- task goal继续在snapshot；tracking target旁路绑定state/candidate/action，不能擅改Token、半径、Deadline或安全门。
- 参考收益已穿过成熟A，但仅单个已知开发Trial23，D→L固定顺序；无跨地图泛化、无严格实时或物理安全证据。
- 原CPU与新GPU数值域不同，不能直接计算FAS单因素增益；.10q诊断域也不是自由空间/安全管证明。
- 新GPU、Factory或导航任务均须另行授权和现场资源门；默认4090服务器执行不等于持续占用或无限授权。

## 2. 使用版本、分支与工作区状态

### 本机仓库（本次现场读取）

- 根目录：`C:\Users\zlab\Documents\Codex\github-clean-work\safer-splat`
- 当前分支：`tum-splatfacto-v1r5-command-preregistration-v1`
- 当前 HEAD：`d0b4f2278763fedeb4fd9bc26ff7f55a7c5c2b23`
- **这不是服务器 Candidate/Frozen/Perf 的同一版本，不能用本机 HEAD 冒充原生实验方法身份。**
- 已有 dirty 状态必须保留：已跟踪修改为 `reproduction/cross_dataset/tum_splatfacto_v1r5_command_preregistration_v1/v1r5_exact_training_command.sh`，另有 `.codex*`、`.tmp*`、`docs/` 及 reproduction 下未跟踪文件/目录。不要执行 reset、clean、stash 或批量 add。
- 本次只提交、推送 `HANDOFF.md`；使用基于远端 `master` 的隔离工作树，不修改上述已有文件或切换本机工作分支。文档发布不表示实验源码/数据被上传或方法版本改变。
- 本次GitHub发布基点：`master@08cbc152a05ccffd632c82f125654a6f33acf50a`；隔离分支 `codex/handoff-replication-admission-20261106`，隔离工作树 `C:\Users\zlab\Documents\Codex\github-publish-work\safer-splat-handoff-replication-admission-20261106`。修改前命名检查点分支 `codex/checkpoint-before-replication-admission-20261106`；不包含用户未提交文件备份，不恢复/reset用户工作树。发布提交号以GitHub文件历史为准。
- 修改前命名检查点：`C:\Users\zlab\Documents\Codex\research-output\checkpoints\FAS_HANDOFF_BEFORE_20261106T035713Z\CHECKPOINT.json`。包含 HEAD、分支、完整 porcelain 状态和已有 tracked diff；这是文件检查点，不是 Git commit，也不是所有未跟踪数据的备份。

### 服务器保护工作树（最近原生D/L阶段前后均匹配、clean）

共同父目录：`/disk1/zlab/v3_repair_worktrees/`

|身份|目录名|冻结 HEAD|
|---|---|---|
|Candidate|`safer-splat-fas-vnext-tail-cardinality-targeted-repair-v1`|`33e34a3ac8d710452775ffe688af77393f734fa9`|
|Frozen|`safer-splat-fas-vnext-l2-deadline-routing-correctness-v1`|`481c3e5e24648d0219e1969f1145648ac99f6943`|
|Perf|`safer-splat-fas-vnext-map-epoch-cache-perf-v1`|`b0a6bbb96512cef5085feada98a900bf9d8ff15f`|

本次对CPU锁定38个文件及原运行37文件/地图/Profile快照做前后核对，两组有重叠，不相加为75个不同文件。三HEAD/dirty一致。较早47文件口径不与本轮混同；下一次使用时重新核对，不宣称永久clean。

现有 SSH 别名为 `zlab-4090`，本会话曾成功使用已有连接。Python 路径为 `/disk1/zlab/conda_envs/safer_splat_official/bin/python`。不在文档保存密码/私钥；连接和执行范围以每轮用户授权为准。

## 3. 运行中、等待中与历史待办

|任务|状态|注意事项|
|---|---|---|
|Trial23阶段0/A无QP两组CPU跟踪|已结束并封印|保留旧43工件，不重跑|
|本轮同源QP两参考CPU对照|已结束并封印|两个子进程正常退出，无后台后继任务|
|完整四组参考×FAS对照|跨数值域，不能作严格四组因果比较|前两组CPU已实跑，固定成熟A的D/L已在GPU软件仿真完成；CPU/GPU非逐位等价|
|成熟A相同参考对照|本次D500/L417完成并封印，旧D88失败独立保留|102件；无运行中任务、无自动后继|
|A/G H260 的 `R03_G`、`R04_G`、`R04_A`|历史待办，不在运行或排队|旧续跑曾资源阻断，不自动恢复；先确认用户是否仍要继续此支线|
|服务器其他用户/项目作业|会话结束时compute表空；稍后封存时GPU0其他作业PID3360988占1620MiB，GPU1无compute进程|两个不同时间的被动快照；未干预、不持续监控、不保证未来空闲|

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

### Trial23同源QP两参考CPU诊断（历史；最新原生结果见文首）

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

### 观察器 CPU 原始证据（已补齐封印，原收尾失败保留）

- 服务器：`/disk1/zlab/tmp/fas_dev_observer_server_cpu_validation_v1/run_20261106T091159Z/`；以`results/CPU_RESULTS.json`、`results/S04_COMPONENTS.json`、`results/LAUNCH_RECEIPT.json`及日志为入口。12/12 CPU通过；后置保护、FINAL_REPORT与40件清单已补齐，manifest SHA `6fe629588f4d1754643e1bf27abfc370a81ff1b3f5485118ea9913e52c077349`。未声称完整下载到本机，复验不重跑测试。
- 最近原生封印是文首`run_20261106T095437Z`的102件D/L结果，清单SHA `7c073167c4ca89ca28bddcc8761e3a641450ddd2a01554d8bd44e9135febfd35`；完整服务器根目录及核心文件见文首。旧`run_20261106T073852Z`76件部分D失败结果保留。下面的968件包是完整同源CPU QP参考比较，证据域不同，不合并。

### 最近完整CPU参考比较权威包

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

拟议四组为直接目标/航点参考 × 无FAS/固定成熟A，四组都使用同一QP。前两个参考＋QP臂在隔离CPU域完成；固定成熟A的新D500/L417在GPU原生软件域完成。旧D88/L未启动仅属历史失败包。仍不能把两种数值域拼成严格四组因果试验，不能直接计算FAS单因素增益。

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

- **2026-11-06 19:20 / Codex / Trial17/53有界准入否定结果**：用户批准准入及通过后的四臂，本轮实际8接口PASS；四端点PASS后17直线FINITE_UNSAFE_WITNESS（比例.75、h=−2.24974239245e−4q²），立即停止，53直线NOT_RUN，四GPU臂未启动。7FULL/4.529989s、0GPU/Factory/提交/求解；账本与字节独立复核、3HEAD/97来源不变、39件封印910aea7c…；旧失败保留，任务进程退出，GitHub仅更新HANDOFF。不能据此宣称跨任务性能或成熟A失败。
- **2026-11-06 19:03 / Codex / 服务器只读跨任务复验设计**：复验102+50成员、34消费来源、三HEAD/38文件/3地图资产；从冻结85输入排除16已知任务，固定哈希选17/53，6D字节与历史state identity一致。保存2任务4臂AB/BA条件方案；两直线未查，先建议≤132FULL CPU准入，原生45min/4Factory等预算尚需另行授权。0测试/新求解/FULL/GPU/Factory/提交，6件方案封印87e061cc…；仅GitHub HANDOFF发布，旧失败不变，无自动后继。
- **2026-11-06 18:18 / Codex / 服务器观察器收尾与新授权固定A原生D/L**：先复验CPU40件、原生父包76件及保护身份，未重跑12场景；新独立DEV保持CPU观察器核心，复用设备绑定/离线缓存，D→L实际完成500/417提交。917/917执行段Oracle SAFE；共同H260 Progress 0.09666634/0.68800032；L软件到达，c56 WARNING合法后备1次，无超角色transition。会话702.493s、solve979、geometry11075，所有预算内；保护前后一致、102件封印7c073167…、任务进程退出。事后解析路径/schema错误修复与原失败均留存，不重跑实验。GitHub仅发布HANDOFF，旧CPU编码/中文OK断言/Git fetch失败均补记而非回改裁决。后续只建议审阅证据再决定是否授权独立复验，不自动扩样。
- **2026-11-06 17:19 / Codex / 服务器观察器CPU验证与未完成收尾**：新授权预算内1进程完成12/12场景，含启动1.280370s、20,719字节，Linux真实单调钟及20/40ms阈值不变。随后中文stdin编码失败发生于后置脚本执行前，SSH退出1；后置保护/报告/清单未完成，整体PARTIAL，不宣称GPU准入。保留Windows V1失败、V2未封印以及原生c87已提交后停止。此次仅GitHub HANDOFF更新，没有重连、测试或新实验。
- **2026-11-06 / Codex / PID3142527明确授权与信号拒绝**：完整核对目标身份和start_ticks后尝试一次SIGINT，系统返回EPERM，信号未发出；失败后复查目标仍在。未通过sudo/docker/SIGKILL绕过。3件工件封印，清单d93d045b…；实验未启动，权限与资源问题未解决。
- **2026-11-06 / Codex / 明确PID中断授权核查**：授权目标2990859已退出，GPU1新PID3142527占4372 MiB，依用户“其他占用即停”条件终止准入。未发信号、未自动转GPU0、未启动实验。4件阻断工件封印，清单0cfa6ac2…；源和旧包未改，无后继。
- **2026-11-06 / Codex / Trial23 GPU0改设备准入**：用户仅把设备改为GPU0，其余预算不变。05:27:22 UTC物理GPU0已有PID2972493占4372 MiB，停止不排队。额外只读定位了worker两处写死GPU1与逻辑cuda:0，未改代码/初始化CUDA。4件阻断工件复验，实验计数全0；旧GPU1包清单SHA不变，无自动后继。
- **2026-11-06 / Codex / Trial23固定成熟A两参考原生准入**：用户明确批准1次GPU1会话、2 Factory、≤1000提交、≤2000求解/50000几何调用；首次资源门发现GPU1 PID2990859占4372 MiB，按合同停止。新实验计数全0，来源完整复核/接线/CPU测试/D/L运行均未开始。6件阻断工件封印，不排队、不自动恢复；旧CPU结果及53次量化正残差边界不变。
- **2026-11-06 / Codex / Trial23同源QP阶段B**：完成源求解器/六盒行准入、D/L各一次有界CPU运行、矩阵/KKT只读诊断、15600项复核及968工件封印。D500步未到达；L416步软件到达；916/916运动段源SAFE。明确53次微小量化半空间正残差、CPU/GPU非逐位等价、D量化停滞及L超调。新QP920/FULL1835，GPU/Factory/Token/PlantCommit均0。下一步成熟A同参考对照仅建议，NOT_STARTED。
- **2026-11-06 / Codex / Trial23阶段0/A**：用户授权后完成无QP/FAS的D/L隔离CPU诊断。D38个接受步后c38待推进段UNSAFE；L368个接受步及软件阈值到达。总413FULL、17合同测试、4099独立复算、43文件封印；3保护HEAD/47文件不变；全部原生权限0。四组仍未就绪；下一步只建议同源QP准入及两参考对照，NOT_STARTED。
- **2026-11-06 / Codex**：首次建立固定交接与AGENTS维护规则。登记最新地图/路径/跟踪CPU准入包：Trial23直连条件通过、其余三直连有不安全见证；57合同测试、91复核、65FULL；四组未准入；无新原生执行。按用户澄清改为GitHub正式维护，仅文档提交推送；既有本机dirty完整保留。
