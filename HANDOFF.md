# FAS / safer-splat 固定交接文档

> **当前结论（2026-11-13）：实际 Stonehenge 地图任务级规划适配与小验证完成。** 成熟 Splat-Plan 走廊/样条＋共同双积分器时间安排已实际运行；10条CPU模型轨迹均软件到达且1943段代理几何覆盖。本次曲率加速度分量反馈在三个任务的主要时间指标上均更慢，停止该具体加权构造；保留成熟几何/shortcut两种基线，不事后逐例择优冒充统一策略。全部结果仅限共享Gaussian代理模型，不是生产FAS闭环或物理安全。

## 当前阶段：实际项目地图的成熟规划与几何反馈小验证（2026-11-13）

- **裁决：ADOPT_ADAPTED_MATURE_PLANNING_BASELINES / STOP_THIS_CURVATURE_WEIGHT_INCREMENT。** 已完成定向原文/源码核查、三次新有限LazyPRM种子、作者走廊/六阶Bézier适配、公式级reachability时间安排、同模型执行、完整段检查、消融、冻结Trial53检验、独立复核与封存。不是只交方案；不是官方整篇Splat-Plan或官方toppra复现，不称新算法成立。
- 任务：Trial61/17为开发，Trial53为**已见复用检验**；全部固定原初态/goal。地图为116446有效Gaussians，NPZ SHA `4c3b18e009f3bb85241a6dec7de67b4aff0b85f58b87b094e3616bcd8e4c43e0`；半径.015q，position-first binary32双积分器dt.05，逐轴速度/加速度≤.1。软件到达距离≤.01q、速度模≤.005、连续10后状态；不是原严格Terminal1e-12或20Hz。观测支持域UNKNOWN，搜索盒不是已知自由空间。
- 来源：服务器safer-splat HEAD `ab643b8b75d2867cccde54bc7283d9868d48cdc2`；作者splatnav HEAD `e996e229daca4e25703a13243541371290a6f7f8`。作者完整入口有CUDA同步/voxel终点投影，故保留精确任务终点、以已有LazyPRM替代种子；直接复用作者碰撞集合、支持半空间、Bezier矩阵/目标。所有方法共同增加端点静止与逐轴动态时间安排，最终CPU模型回放。未运行生产Factory/Token/PlantCommit/PSF或原生六臂。
- 比较：成熟几何基线G、合法shortcut S、一次曲率分量反馈F。F用首次时间安排的`q''(s)*sdot²`片峰值加权二阶控制点差分，系数1、一次QP更新；只是分量，不含`q'*sddot`及抵消，不是时间梯度。第二张方向扩展路网方案卡未实现、非自动后继。没有按开发负结果调参，dev/test代码哈希相同。
- **模型到达T / 控制努力E**：61 G **8.85/.04861224**，S **8.85/.04671613**，F **9.65/.05495712**；17 G **9.30/.04303518**，S **8.85/.03824522**，F **10.50/.05298267**；53 G **9.60/.03703110**，S **10.00/.03871255**，F **9.85/.03602986**。到达前E与完整E分列CSV（上述舍入一致）。F主要T全更慢；53仍保留T+2.60%/E−2.70%取舍，不改主要目标宣称胜出。S也并非总更好。61付费零权重消融与G的曲线/状态/动作/参数化数组全部字节一致。
- 分母：**10/10软件到达，1943/1943实际CPU模型段完整覆盖；0最终几何UNKNOWN/UNSAFE**。种子请求120SAFE/16UNSAFE，shortcut6SAFE/49UNSAFE；这些是规划边拒绝，不是执行碰撞。所有实际执行仅为独立模型算术，没有真实接受/Token。不能与旧R557次原生提交直接排序。
- 几何：作者走廊判定与共同原CPU共享FULL/保守区间分层；用包含整块实际运动段的距离Lipschitz球，必要时分裂到原单段检查。离轨球中心查询净空不是轨迹最小净空；没有独立物理真值或外向舍入全链包络。独立复核10条初态/转移bytes、动作/速度、到达、努力、控制点包含、段覆盖PASS；仅证明这些数值检查，不继承全局连续最优/原生资格。
- 实际成本：**13/150完整种子/样条规划调用、14QP+7260LP、1499FULL、10/60完整模型执行**；最终账本CPU **641.620142s/1800s**、活动墙钟 **676.214579s/3600s**，另封印CPU.191773s/墙钟.332348s。GPU0。种子174.79s、shortcut174.45s、样条/时间安排/回放108.93s、几何审核202.28s；主要开销在搜索/验证。计费表每方法都收种子成本，实际共享只算一次；一档配置、顺序/缓存不同，不称同墙钟消耗下的质量曲线、WCET或算法净加速。首次base约30.815s位于未细分启动/导入/退出区间，不单因归某库。
- 保留失败/修复：根分区满导致/tmp传输失败，改用授权/disk1，不清理他人文件；初P1计数/退出/尺度报告修补，原首条结果和初版代码保留；只读引号/错文件名失败、绘图标签修复、报告自观察排除误报均留痕，未重跑轨迹。无研究性调参修订。P2 PASS_WITH_LIMITS；复跑入口静态复核，未为验证入口再次运行全批。START账本在Popen后，不宣称启动原子性或掉电保证。
- 服务器包：`/disk1/zlab/tmp/fas_task_level_planning_v1/run_20261113T111100Z/`；**259文件清单逐项PASS**，manifest SHA **`f12883539c8d17991df14f66824e3f23dfba8a6706bad3bbecb591bcd164f249`**；主报告SHA **`d0f9b96d77b060e5f6559955d174ab3aec9cd8cb04a34e3982aad0cfbeedf83e`**。包外`run_20261113T111100Z_SEAL_RECEIPT.json`另记封印，不自指。核心报告、code/reproduce.py、PROTOCOL、RESULTS.csv、FINAL_STATE、两张图及操作记录在包内。本机只交付 `C:\Users\zlab\Desktop\REPORT\REPORT_TASK_LEVEL_PLANNING_CN_20261113.md`，传输SHA一致。
- 保护与退出：来源哈希和5工作树HEAD/status前后未变（含作者既有dirty）；Windows未跑数值；无新安装/GPU/生产提交。10条模型任务及batch已退出，无排队/自动后继。账户余额UNKNOWN；未用旧GPU快照作资源许可。
- **下一步：采用成熟几何规划及shortcut作为两个可复用基线，结束当前加权构造。** Gaussian是表示/验证平台、FAS是资产来源，不是本轮贡献必要结构。不重开切换/Newton/拒绝证书/误差包络；联合空间—时间强方法、扰动跟踪、第二卡均NOT_RUN，需另行具体授权，不能把“还有变量”当自动后继。
- 发布基点`39370030e66898b3bb449d2b85c9f50dfb3d26b3`；命名检查点`codex/checkpoint-task-planning-20261113`，文档分支`codex/task-planning-20261113`。仅提交HANDOFF摘要，不公开原型代码/数据，原主工作树dirty保留。最后更新：**2026-11-13 19:40 Asia/Shanghai，Codex / 本Safer-Splat-1会话**。

## 历史阶段：时间—努力结构分解、同预算强基线及结案（2026-11-13）

- **裁决 A / ADOPT_MATURE_SPEED_ALLOCATION_CLOSE_LOCAL_INCREMENT；NO_NEW_ALGORITHM。** 已完成数学分解、区间/KKT实现、两开发＋四已见复用检验、共同预算修正、预定细化、独立算术核验、少量图表与封存。没有第四模型、没有新调度估计器；旧Newton、拒绝证书、Gaussian误差包络等不重开。不是否定一般规划—控制协同。
- 来源锁：上游`fas_mature_control_efficiency_v1/run_20261113T091600Z`及清单`794a8ef1…`，12个实际消费文件按旧清单前后核对。单积分器速度输入、圆障碍、gamma1/alpha5、真实欧氏U12、共同阶段域不变；原目标距离.03连续.20模型时间，努力E为速度平方积分，不是电池能量。
- 层级：A固定反馈；B固定CLF/CBF/输入/域/阶段，允许名义控制/调速；C仅碰撞/输入解析下界。原反馈dt.05点上CLF/CBF＋段几何，调速采用更强全cell连续不等式与事件对齐ZOH，是轨迹级保守子集，不是固定周期逐位等价或扰动反馈认证。确认后缀不缩时、不漏努力；主T为公共终态完成时刻，首次命中/最早确认另存。
- 结构：圆开发早→晚交接运动L **1.793529→1.936395**、T **9.55→12.95**、E **.548305→.513080**、eta **.614315→.564330**。晚切换省努力不是路径短；`ΔlogE=.153286−.304555+.084869=−.066400`。全局缩放运动TE不变但确认使全任务TE不恒定。旧24有限候选原集合均非支配，加入本轮稀疏预算成熟记录后6点被支配；其余18点不等于全局Pareto最优。
- 冻结预算 **.539/.77/1.54**，两开发选择后固定部署策略 **late/gain0/gain1**；原四设置仅复用检验、不称未见。预定三路径gain0/late/gain4，两种调速均使用相同完整路径库。圆开发同预算T：反馈 **13.15/9.75/4.95**；global **12.528161/7.121580/3.657606**；成熟allocation **8.838534/4.706169/2.392817**。后两项是含构建成本的事后参照；不能当无未来信息在线增益。
- 干净同路径例：circle late、B.539，原13.15→global12.528161→allocation8.838534；后两者E≈.538999999846。KKT `v=clip(c,l,u)`是成熟凸分配，不叫TOPP-RA。紧预算同路径C层解析下界7.157149与B层8.838534的差距来自合同/离散充分条件，不是物理限制。不同预算选路变化由现成有限库等效覆盖，无独立新增机制证据。
- 分母：累计 **201尝试/149实际完整轨迹/27419段**；146ARRIVED、3旧正超额、30准入拒绝、22路径预算不可行。最新版本165记录（含9细化）：125ARRIVED/24准入拒绝/16预算不可行；主156记录为116ARRIVED。反馈ARRIVED不代表它在每个B内可选，选择仍严格E<=B。不是201独立任务。
- 19唯一路径表示中15准入（25日志条目含6复用，已去重）；4个障碍设置的gain0有空连续速度区间。circle cell69下界.329029>上界.310940，只否定本cell恒速充分实现，不判原采样轨迹不安全或B全域无解。
- 保留失败/修复：初P1发现确认上界符号、CBF零系数极限、原容差及确认/预算问题，修后22项PASS。初3调速E正超额1.11e-16/6.66e-16/8.88e-16先排除，再共同内侧预算余量1e-10(1+B)，配对重做36条，E<=B不放宽。P2修准备耗时重复计数；图检查目录WARN与一次汇总引号SyntaxError保留，不增加科学运行。
- 细化radius-high：k12粗T/E **.65/17.207214**→细 **.60/14.714284**，高增益敏感不可忽略；late路径cell二分紧预算allocation **8.838534→8.713580**，三预算分类及同路径global比较稳定；未证明全部路径排序网格收敛。
- 独立复核PASS_WITH_LIMITS：动力学最大差1.11e-16，T/E积分差7.11e-14/7.11e-15；最低圆障碍净空.000106767797。无外向舍入，非严格物理安全。verify的10个负控标签多为数据sanity断言，**不是故障注入**；未独立重推全部区间/逐cell源绑定。完整段约束复算与静态解析审查范围分开。
- 预算：**201/240尝试、5434/50000原型求解、745071/300万更新**；已记账CPU **16.363138s**、活动墙钟 **28.987652s**，另封印CPU.086016s/墙钟.225599s；不把阅读写作/SSH跨度叫数值计算墙钟。核心feedback/retime计时边界不同，故不宣称跨方法实测净加速；完整批次含日志和修复。账户余额UNKNOWN，无GPU资源声明。
- 服务器包：`/disk1/zlab/tmp/fas_time_effort_structure_v1/run_20261113T100633Z/`；**67文件逐项核验通过**，清单SHA **`9ee919147a392b5357a43acc66137d6ad36ad9de9951f551c44d88343052bb06`**。包外`run_20261113T100633Z_SEAL_RECEIPT.json`不自指。主报告`REPORT_TIME_EFFORT_STRUCTURE_CN.md` SHA **`bd6231ca4650a5d64e55d52c1013b084b4319c27d5f3f37eac6d8eaf5a6232ed`**；协议、experiment.py、RESULTS.csv、PAIRED_BUDGET.csv、REFINEMENT.csv及figures在包内。本机仅交付`C:\Users\zlab\Desktop\REPORT\REPORT_TIME_EFFORT_STRUCTURE_CN_20261113.md`。
- 保护与状态：zlab-Super-Server/zlab，服务器项目HEAD前后`ab643b8b75d2867cccde54bc7283d9868d48cdc2`、工作树clean，12消费源哈希未变；未重审全部保护树。GPU/CUDA/生产QP/Factory/Token/PSF/FULL/Plant/训练0；Windows未跑数值。任务计算已退出，无排队/自动后继，不扫描或干扰其他作业。
- **下一步：本支线结束。** 如未来有明确部署需求，可另行定义“未知未来路径＋固定更新时钟＋扰动”的在线速度安排问题，但本轮未启动，不以尚存稀疏Pareto点为由继续调参。现成熟基线保留复用。
- 发布基点`3568e38558f143d9964cabf655cdc85d551c3344`；修改前命名检查点`codex/checkpoint-time-effort-20261113`，文档分支`codex/time-effort-structure-20261113`。仅提交HANDOFF，原型代码/数据不公开；原主工作树dirty保留。最后更新：**2026-11-13，Asia/Shanghai，Codex / 本Safer-Splat-1会话**。

## 历史阶段：成熟控制结构、敏感性与强基线完成（2026-11-13）

- **裁决：ADOPT_MATURE_BASELINES_STOP_SWITCH_ONLY_INCREMENT_FOR_THIS_FAMILY。** 已实际完成公式级硬CLF–CBF最小实现、一次共同兼容域准备修订、开发调参、四设置冻结检验、步长细化、成本拆分和独立审查；不是只交计划。没有新的增量控制器，不维护旧Newton估计器。研究剩余关系是给定努力预算的交接/名义控制取舍，尚无低成本新机制证据，不自动继续。
- 继承原文`arxiv:2410.08364v2`单积分器/圆障碍/平方距离CLF、硬约束反馈、兼容子水平集与Remark VII.1名义目标。无明确可运行作者实现，称**公式级适配**，不称官方整篇复现。共同`||u||2<=12`真圆界、alpha5/gamma1、dt.05、目标距离.03连续.20模型时间；输入是速度，无独立速度/姿态状态，不是FAS二阶binary32。每段完整圆障碍/域/CLF/输入检查；无外向舍入或物理误差保证。
- 旧结构结案：C-dev交接前y/vy恒零并非重置，后段`e_y=-.6(1+s)e^-s`，26合法候选内`T=tau+4.95`；上下速度和直行例不适用该固定尾公式。只排除旧分离族中的额外余时估计器需要，不排除一般二阶问题。
- v1域过保守导致仅一个候选、最小范数CBF未活动；保留28条旧开发结果。唯一共同修订以径向/切向可行场加强有界输入域证明，所有方法同用，未改场景/安全阈值，不宣称创新。v2圆开发tau=2.40/3.20/4.20/5.95，J_next=7.35/7.30/7.25/7.20，T=9.75/10.50/11.45/13.15，E=.548347/.534197/.523055/.513120；四点均非支配。最早CBF活动16步，最低净空.000359018。
- 冻结阈值从.2/.35/.5选**.35**；四冻结设置radius-low/high、start-low/high，固定paper-like/earliest/tuned/reference共同T分别**9.75/9.75/9.75/9.80**。两goal变化在冻结前因累计160计数和回归预留被标NOT_RUN，不按结果换样。每例后验包络另列，非实际部署策略。
- 成熟任务基线k=1/4/12：圆开发T/E为**4.95/1.108039、1.35/4.627345、.65/17.181822**，更快伴随更高输入努力，不叫电池能量。无障碍合法简化k4从1.35降到1.10；圆障碍自身充分域未证则保留原路径，不称无路径。TOPP-RA未集成、NOT_RUN，不冒称已击败它。四冻结k4均T1.35，但不据此称跨场景泛化。
- 分母：**91完整执行记录全部ARRIVED**＝28v1开发＋28v2开发＋32冻结＋3细化；不是91独立任务。预算**144轨迹/尝试**还包括38预测尾、11前缀、4模拟故障尝试。v1两预测尾/两前缀缺完整链，明确保留缺口。18,195次独立原型凸优化；没有生产QP调用。最小几何裕量约.000106768模型单位，不能忽略模型误差。
- 细化radius-high（按最小净空预定规则）dt.025：paper/earliest仍相同T9.825/E.545935；k12 T.60/E14.714284，粗步长为.65/17.207214，高增益结果对采样敏感。并非连续极限或真实实时收益。
- 成本：共同准备约.268–.269ms，最早规则约.110ms；充分预测351–419ms/701求解，包含已测日志278–343ms，非日志区间73–76ms。1热身＋2实测重复，少于原计划重复以保留总预算。计算期间plant冻结，不能称WCET/20Hz或事后从端到端扣日志。时间—努力Pareto未被一个简单参数全面覆盖。
- 质量：P1修正重复key、故障部分轨迹、等待边界及简化自身域，保留旧代码/故障。P2初次FAIL发现独立域/身份绑定遗漏及Pareto措辞过宽，补纯算术核对、不新增轨迹；初次失败不能抹掉。原审计16454执行/预测段＋1070前缀段，KKT最大站立残差6.66e-16、正原始残差5.33e-15；详细追加复核及最终P2见包内文件。
- 服务器包：`/disk1/zlab/tmp/fas_mature_control_efficiency_v1/run_20261113T091600Z/`。**70文件逐项校验通过，清单SHA `794a8ef1dc76c4629d24a29f17e19d49a12e7131b2cde1d399b8fb618c0cab3d`**；包外`run_20261113T091600Z_SEAL_RECEIPT.json`不自指。主报告`REPORT_EXECUTION_EFFICIENCY_CN.md`、结构协议`BASELINE_AND_STRUCTURE_CN.md`、`prototype.py/config.json`、配对/敏感性/任务CSV、4逻辑图及原始记录。主报告本机`C:\Users\zlab\Desktop\REPORT\REPORT_EXECUTION_EFFICIENCY_CN_20261113.md`，SHA `241718f4cbae512ee2c6aabe84645648b32ee8c4d3e66f8f2ebf00a28e19892a`；原型代码/数据不提交GitHub。
- 最终P2 **PASS_WITH_LIMITS**：追加654131项算术检查，91执行/36绑定预测尾/16454段＋1070前缀，0新求解/轨迹；旧v1缺链不补造。预算账本CPU **19.648629s**、累计活动墙钟 **30.628480s**、144/160轨迹或尝试、18195/100000求解、76657/3000000等价更新；SHA尾部开销另记包外收据，启动/SSH不当模型性能。16个登记任务进程经只读ps均已退出，无active标记/自动后继。91记录共13饱和步，不据此冒称二阶曲率/加速耦合验证。
- 保护：服务器zlab-Super-Server/zlab，项目分支`audit-v3-validation-cohort-source-feasibility-v1`，HEAD `ab643b8b75d2867cccde54bc7283d9868d48cdc2`；前后仅核对直接消费5个旧文件与项目状态，不声称全历史重审。GPU/CUDA/生产FAS/Factory/Token/PSF/FULL/Plant/训练0，Windows未跑数值；不干扰其他任务。完成后无排队/自动后继。
- 发布基点`8cd13f62a6642ae9012d93686d0abb17eb3007c6`；修改前命名检查点`codex/checkpoint-mature-control-efficiency-20261113`；文档分支`codex/mature-control-efficiency-20261113`；原主工作树dirty保留，只提交HANDOFF。最后更新：**2026-11-13，Asia/Shanghai，Codex / 本Safer-Splat-1会话**。

## 历史阶段：二阶兼容交接机制验证与成熟基线完成（2026-11-13）

- **裁决B：SIMPLE_EVENT_ROOT_BASELINE_SUFFICIENT_FOR_THIS_MODEL。** 已实际完成独立二维双积分器、连续临界阻尼反馈、全状态合法域、6种固定反馈规则、3档任务反馈、开发调参、冻结检验、步长细化、独立复核和封印；不是仅设计。没有新增估计器，因成熟规则已覆盖本轮有限候选参考；不据此宣称一般二阶问题已解决。
- 模型：连续理想反馈精确流，速度不重置，不是FAS Euler/binary32或数字ZOH。Ki用全部未来轨迹的位置/速度/输入极值定义，guard=K1∩K2；实数模型有尾流不变性依据，float64核验没有外向舍入误差证书。机器人半径.05、合成已知走廊；输入/速度欧氏界采用共同轴向充分条件。不把未知区当自由空间、不强制任务基线过尖角停止。
- 主评价预冻结为**时间—加速度努力Pareto**；到达每轴位置/速度误差均≤.03，dt=.05连续5点确认，最长24模型时间；首次进入/确认分别记录。开发距离阈值从.04/.08/.16选.16，短预测从.2/.5/1.0选.5；任务反馈档固定.8/1.1/1.4。固定反馈只是隔离调度的方法学条件，没有编造现实不可替换限制。
- 分母：26开发轨迹＋71冻结轨迹＋6细化＝**103实际轨迹/15304转移**；另1条C-a15/task1.4未准入，零执行。8冻结设置每种主表方法均到达，最早/短预测/事件根/充分预测/位置评分消融结果相同；事件法相对冻结距离7快1平，不代表相对强简单方法有收益。10设置265个候选事件根与充分预测的采样到达分数一致；候选参考不是任务全局最优。
- 冻结确认时间（最早/距离/短视/事件/充分预测）：C-v0 **7.25/7.60/7.25/7.25/7.25**；C-v35 **6.60/6.90/6.60/6.60/6.60**；C-up **7.00/7.30/7.00/7.00/7.00**；C-down **7.05/7.30/7.05/7.05/7.05**；C-narrow全部**7.30**；C-wide **6.65/7.30/6.65/6.65/6.65**；C-a15与C-a25均 **7.00/7.30/7.00/7.00/7.00**。这些是模型时间、参数检验，不是物理时间或独立实景导航样本。
- 机制边界：同p=(-.12,0)，v=(0,0)和(.5,0)均在K1，但K2未来位置余量分别+.08和−.1230316852，速度必须进入guard。多数vy=0拐角后续纵向尾为e_y=−.6(1+s)e^-s，与交接时刻无关；C-dev各候选确认尾固定4.95，因此最早τ2.05→T7.00，距离τ2.35→T7.30。**资格差异真实，新增性能信息未激活**，不能把二阶性本身称创新。
- 任务层取舍：C-dev固定策略T/E=**7.00/.117682**；标准反馈档.8为**8.60/.056961**，1.1为**6.45/.161392**，1.4为**5.30/.356579**。更快但最高档努力约3.03倍。C-a15/task1.4下一段初始y加速度1.176>共同轴界1.06066017，任何等待都无合法交接，记录NOT_ADMISSIBLE_NO_FINITE_BASELINE；不调参或改界。没有虚称TOPP-RA实现。
- 成本：共同候选/guard/决策计费、单线程、1热身＋5重复；C-dev p50最早**3.370ms**、短视**3.316ms**、事件根**14.456ms**、充分预测**13.229ms**。事件根并非普遍更快，共用prepare也让简单规则承担可进一步简化的成本。非WCET/20Hz，模型plant在计算时冻结。旧一阶强控制的时间收益与2.155–5.293倍努力另表；不事后改旧时间目标，不混合两种努力单位。
- 工程/质量：P1作者和独立各16项通过；修正未准入负行记录与轨迹计数、(q1,0)有效域前提、误要求未使用pandas/scipy的依赖检查和104尝试误标trajectory字段。保留prototype_pre_P1.py、FAILURES和修复记录，冻结数值代码/配置未改。独立矩阵流/连续极值/Simpson复核103轨迹，最大状态误差2.22e-16、单步努力差1.1376e-10、最小约束余量.000615012；P2 PASS_WITH_LIMITS。C-wide按最小几何余量选择dt=.025细化、确认跨度仍.20，结论不变。回退仅helper检查，不声称任意崩溃/时限故障证明。
- **实际资源：CPU14.889399s、活动计算墙钟20.852567s（含封印），1879729/3000000等价更新，103/240实际轨迹**；CPU上限1200s、单批墙钟1800s，初始预留≥20%修复额度。预测、调参、根、连续检查、审计和计时均计入，未重置。全部同步任务已退出，无active标记、排队或自动后继；未扫描/干扰其他GPU任务。
- 服务器包：`/disk1/zlab/tmp/fas_second_order_handover_v1/run_20261113T083434Z/`；**54文件封印逐项通过，清单SHA `78af45bdd955f0625cb417977601b1da7c95cc5d6e1ad575f1b86f0b9604e133`**。父目录`run_20261113T083434Z_SEAL_RECEIPT.json`独立记录最终成本/校验，不自指。核心为REPORT_SECOND_ORDER_HANDOVER_CN.md、MODEL_AND_GUARDS.md、prototype.py/reproduce.py、两张方法表、合并RESULTS/DECISIONS/TRAJECTORIES、旧表补充及4逻辑图。本机报告：`C:\Users\zlab\Desktop\REPORT\REPORT_SECOND_ORDER_HANDOVER_CN_20261113.md`，文件SHA `cbf8c9da74cc714c9eda179494980223236bba83c04b7a6e93efe71df4a60d41`。
- 版本/保护：服务器zlab-Super-Server/zlab，项目分支audit-v3-validation-cohort-source-feasibility-v1，HEAD前后`ab643b8b75d2867cccde54bc7283d9868d48cdc2`、工作树clean；直接消费7个旧文件前后SHA不变。没有重新全历史/全保护树哈希审计。GPU/CUDA/生产QP/PSF/FULL/Factory/Token/Plant/训练0，Windows未跑数值。仅独立CPU原型目录写入。
- **单一下一步 / NOT_STARTED**：本族保留最早合法/短预测，不开发新估计器或加样找赢家。若重新立项，先提出有实际控制依据、不能被固定纵向尾还原的速度—净空耦合机制和一对解析反例，再讨论新实验；不为造收益堆模块。本轮完成即停止，不自动开启FAS接入、Gaussian误差包络、旧A工程备选或其他方向。
- 发布基点`32f0886e…`；修改前检查点`codex/checkpoint-second-order-handover-20261113`；文档分支`codex/second-order-handover-20261113`；仅提交推送HANDOFF，原型代码/原始数据不公开，原主工作树dirty保持。最后更新：**2026-11-13，Asia/Shanghai，Codex / 本Safer-Splat-1会话**。发布commit以远端历史为准。

## 历史阶段：第一阶兼容域内阶段交接原型完成（2026-11-13）

- **裁决：PROTOTYPE_COMPLETE / NARROW_FIXED_POLICY_VALUE / NO_GENERAL_ADVANTAGE_ESTABLISHED。** 用户授权的实现、最小测试、开发对照、一次机制修订、冻结检验、独立核对、报告及封存已完成，不是仅完成框架。只研究固定阶段反馈内的一次合法交接；第一阶解析模型，非FAS binary32/双积分器，不继承完整RRT完备性或物理安全。
- 分母：14条开发v1＋6条fixed/reference/cheap配对v2＋42条冻结（6设置×7方法）＝**62条模型轨迹全部到达**；这不是62个独立任务，也不是新原生导航。统一dt=.01，10个连续目标区域采样点，最长模型时域20；连续首次命中/采样首次进入/确认分别报告。所有原始版本、失败预测及修订理由保留。
- 主表：固定距离、最早合法、开发调参阈值、共同目标距离下降率、有限候选高精度参考、低成本余时。阈值仅开发选择`.05`后冻结。任务层另给同安全/输入要求下积极控制＋合法路线；不是TOPP-RA/PBF官方实现，不将改变控制组织混成调度单因素。
- 开发失败与修订：C-dev v1用最慢速率统一估计，完成7.58，排序逆序2072/2080；参考3.39。一次预注册修订为分量下界＋单次Newton，完成3.49、逆序101/2080；固定`.05`也3.39。P1在任何开发输出前已发现固定阈值近最优，准入门槛仅衡量最早/局部的调度空间，不是优越门槛；未换场景/控制器/安全阈值。
- 冻结完成时间（fixed/local/reference/cheap/strong）：S1 **12.16/11.38/11.38/11.38/1.57**；S2 **10.02/6.90/6.90/6.90/1.57**；S3 **10.93/5.76/5.76/5.76/1.57**；C1 **3.39/4.60/3.39/3.51/1.15**；C2 **4.08/6.03/3.95/3.99/1.07**；C3 **8.19/5.67/5.67/5.67/1.10**，均为模型确认时间。cheap相对固定5胜1负，相对各例最佳简单规则**1胜1负4平**；不以更多更新数作独立样本。
- 成本/取舍：cheap调度p50/p95 **2.297/3.041ms**，遍历参考 **19.047/20.005ms**，固定 **.070/.095ms**、局部 **.501/1.166ms**；每设置一次，非WCET/稳定速度比。strong全部完成更快但努力更高，如C2 cheap `.295864` 对strong `.953494`，不是Pareto全面支配；积分控制努力不是电池能耗。计算期间plant冻结，未建立真实实时净收益。
- 解析负证据：标量内点就是两速度相等，局部规则已覆盖；原连续0.677359强反例复算，统一采样到达确认为.77。二维当前特例可由闭式驻点＋两侧候选匹配遍历参考；4例后验算术核对一致，**不是已运行的冻结在线基线，不补造计时**。v2是实数模型下的乐观下界而非排名保证；最大余时误差约.2483，足以吞掉.09–.13的收益；未做外向舍入，不能写严格数值界。
- 工程/质量：开发前修复实际预测异常回退、异常轨迹前缀保存、简单规则多余网格开销及连续/采样字段说明；13项smoke＋2项故障路径检查。独立复核33308行，34种轨迹16670行不同公式＋相同字节/模型复用覆盖全部62条；最大转移误差2.22e-16、努力2.93e-15。阶段单调、连续域和强控制努力已核对；第一阶额外速度拒绝测试不冒充双积分器验证，日志前缀测试不证明掉电持久性。
- **预算实际：66/68短运行入口、119408/136000等价状态/控制更新；含预测、参考二分、开发阈值查询、修订配对、独立审核和后验算术。** 最终计账CPU **6.602381s**、活动计算墙钟 **24.883555s**，各上限1200s；不将阅读/写作跨度叫计算墙钟。没有预算重置或超限，没有结果导向补样；本任务计算进程已退出，无排队/自动后继，服务器其他作业未扫描。
- 归档：`/disk1/zlab/tmp/fas_compatible_handover_prototype_v1/run_20261113T073440Z/`。287文件清单逐项校验通过，SHA **ac3305a8c77c0884384e472b1ad61da16e37c541d126d65943bd3a962a36e5c2**；回执为同父目录`run_20261113T073440Z_SEAL_RECEIPT.json`，不自指。核心：`REPORT_PROTOTYPE_CN.md`、`prototype.py`、`reproduce.py`、`config.json`、两张方法表、`COMPARISON.csv`、`ESTIMATOR_ERRORS.csv`、`runs/*`、独立核对及图。本机仅交付报告：`C:\Users\zlab\Desktop\REPORT\REPORT_HANDOVER_PROTOTYPE_CN_20261113.md`。
- 版本/保护：服务器`zlab-Super-Server / zlab`，项目HEAD前后 `ab643b8b75d2867cccde54bc7283d9868d48cdc2`、tracked状态前后clean。冻结代码SHA `9c5652bee6eb6230294fc5128d611f9335cbdec6d9b472a0356314d401349a28`，配置SHA `6f96229eaa424d9b2ea6d5cc4cc7de3ad62d63085995608514ab24a36f562a33`。仅新独立目录写入；不声称本轮重新逐字节核查全部保护树。GPU/CUDA/生产QP/PSF/FULL/Factory/Token/Plant/训练均0，Windows未跑原型数值。
- **唯一下一步建议 / NOT_STARTED**：若继续，仅先设计速度连续、加速度受限且固定已认证反馈确有不可替换理由的双积分器拐角模型，检验局部/闭式规则是否仍能等效覆盖；若没有这样的限制，采用成熟积极控制/合理时间安排，不扩大当前估计器主张。没有自动开始新模型、FAS接入、Gaussian误差包络或旧A工程备选。
- 发布基点`b0e95ff…`；修改前检查点`codex/checkpoint-handover-prototype-20261113`；文档分支`codex/handover-prototype-20261113`；仅提交推送HANDOFF，原型代码/实验数据不公开。原主工作树dirty保持原样。最后更新：**2026-11-13，Asia/Shanghai，Codex / 本Safer-Splat-1会话**。提交版本以远端文件历史为准。

## 历史阶段：增量方法设计完成，原型建议已由本轮执行（2026-11-13）

- **裁决：DESIGN_COMPLETE / RECOMMEND_SINGLE_BOUNDED_PROTOTYPE_NOT_STARTED。** 按用户新优先级从兼容路径执行效率开始，而非沿用上一审查的H3取证建议自动执行。主目标选模型内完成时间；控制能量与规划/调度墙钟单列。阶段参考非任务必经点，最终goal和安全标准不变。
- 三张完整卡：①兼容guard内按剩余时间交接（推荐）；②入口集合/速度标签上的执行时间区间选路（保留）；③允许执行偏差/后备模式下的信息收益下界（远期备选）。不并行搭建三模块，不将FAS/Gaussian预设为必要贡献。
- 原文核查：C-CLF-CBF-RRT arXiv v2 2025-03-12，Definition V.1、Eq24、Remark VI.8/VII.1已涉及区域兼容、名义目标、有限时间CLF及收敛率；2026 Conflict-Aware Switching已有按冲突切换；TOPP-RA、PBF governor和成熟mode scheduling是强起点/对照。Safe Dual Gatekeeper核至2026-05-24 v2，另查2026-04-16 Dual-gatekeeper扩展，后者已有闭环采样信息预测。报告有公式/段落定位，未将摘要当等效证明。
- **已完成手工例子，非数值实验**：共同标量模型/输入/安全标准，固定邻域交接T=3.100308、最早合法T=2.995732、余时最优内点s=2/3时T=2.864920；相对固定邻域约快7.59%，控制能量却约增4.74%。普通shortcut＋积极名义控制在同安全/输入条件下T约0.677359，明确胜过该例的新交接；因此只证明固定策略间有可优化变量，不能证明优于成熟强方法。
- 理论边界：导数1＋grad(J)·f_i在J满足后续时间方程时就是标准切换灵敏度grad(J)·(f_i−f_next)，不是新公式。组合安全、有限候选2ε界为成熟工具应用；新增价值待检验于兼容guard＋低维余时近似的质量—计算权衡。移动参考额外导数、双积分器速度域、离散采样安全及整个RRT完备性不能直接继承。
- **下一步仅建议 / NOT_STARTED**：独立CPU原型，先两个解析开发设置的简单方法淘汰检查，若仍有空间再6个冻结检验设置；同路径/同控制器主表与改变控制器的强任务层压力检查分开。协议建议最多20分钟CPU、68短运行、136000控制更新，均需下一轮启动授权；本轮未使用该预算。若简单方法足够，关闭此具体增量，不追加更难样本找赢家。
- 服务器归档：`/disk1/zlab/tmp/fas_incremental_method_design_v1/run_20261113T051155Z/`。仅三份主文档＋清单，服务器sha256sum逐项通过，传输前后SHA一致。清单SHA **159120794cc658526b1fc4a3e5b0dd116a529b3e0a1c20c07e09b2dc8ceb3c77**。文件：`REPORT_INCREMENTAL_DESIGN_CN.md`、`METHOD_SKETCH.md`、`MINIMAL_EVALUATION_PLAN.md`。本机文档副本：`C:\Users\zlab\Documents\Codex\research-output\FAS_INCREMENTAL_DESIGN_20261113\`；报告不公开提交仓库。
- 来源基点：正式交接`1208b5352e7c1bb2bf543298e9716ed084a5f57f`；服务器`zlab-Super-Server / zlab`，项目`/disk1/zlab/projects/safer-splat`，HEAD `ab643b8b75d2867cccde54bc7283d9868d48cdc2`、分支`audit-v3-validation-cohort-source-feasibility-v1`。直接读取上一审查归档相关结论，不重做全历史哈希审计。
- 权限/状态：新GPU/CUDA/Factory/Token/PlantCommit/QP/PSF/FULL/导航/训练/性能测试/扫描均0；没有原型代码或本轮后台任务、排队、自动后继；未扫描服务器其他作业，其他任务状态UNKNOWN，未宣称GPU空闲。Windows只处理文献、文档和Git交接；服务器新增独立报告目录。未写算法、地图、默认开关或历史结果，主工作树dirty保持原样。
- 文献限制：旧鲁棒OED PDF一次打开失败；改用实际读到的ECC2013原文核对相应机制；CatalyzeX详情403未重试，独立公开arXiv原文可读。主论文官方代码可运行性未核验；期刊元数据已确认，但本轮公式依据用户指定arXiv v2。封印只证明文档完整性。
- 发布基点`1208b535…`；修改前检查点`codex/checkpoint-incremental-design-20261113`；文档分支`codex/incremental-design-20261113`；仅stage/push HANDOFF，提交见GitHub历史。最后更新：**2026-11-13，Asia/Shanghai，Codex / 本Safer-Splat-1会话**。本阶段结束，不自动开始原型。

## 历史阶段：论文共有假设独立审查完成（2026-11-13）

- **裁决：REVIEW_COMPLETE_WITH_SOURCE_LIMITS / NO_NEW_ALGORITHM_APPROVED。** 初稿大多数判断审慎；修正“纳入/外置/限定”混合维度、P04兼容域及P06配套控制器责任、版本与补充证据边界。保留原五表，新增六表、120条多维覆盖、20项确认/修正、4项候选裁决；21篇文献与24条来源记录，不把阅读当作实验复现。
- 直接先例：PSF已有状态/输入置信集合，PFaSTrack已有参数化界，2026-05-24 safe-dual gatekeeper v2已有主动辨识、安全与预算；ASAP-MPC/旧提交机制处理计算期间跟踪和未来接续；Eclares与Persistification已有能源返航/增广状态不变性。不能由旧版future work推当前空白，不能要求图搜索独自完成感知和控制。
- SUPER已补读官方主文相关方法与第16页公式；补充Theorem 1访问403、正式勘误`10.1126/scirobotics.adx3476`正文未取得，影响UNKNOWN。未将未知算成论文遗漏，也未声称仓库PDF已包含更正。P19以v2为准，不能搬用v1假设编号。
- 本轮手工推导：一维延迟加速＋制动安全距离；带有界地图纠错的充分停止条件；计划辨识激励被安全过滤消除的反例及条件性奇异值扰动界。均为条件性分析/已有工具，不是FAS新算法或数值实验。强基线全部成功时仍可比代价，但同信息标准治理得到同一包络则没有独立增量。
- **唯一下一步建议 / NOT_STARTED**：如另行批准，只核查已存正常/异常接受记录是否具备同钟观测→接受年龄、计算期间plant实际演化/控制、后备剩余有效期与可信界。区分软件接线问题与真实延迟—恢复需求；若状态冻结或成熟同信息方案直接覆盖，停止该科研构造。H1非并行主线；不新建能源/辨识模块。
- 来源：输入`C:\Users\zlab\Downloads\planning_safety_assumptions_matrix.xlsx`，SHA `b312b61c1743671f4a374bb41c52cab2490747ab63b6b631e9aa0b99f8daecd8`；原2200单元格比较0差异，修订版11表、120个P/V键完整、0错误单元格。这是**文档完整性复核**，不是CPU科学验证。
- 服务器归档：`/disk1/zlab/tmp/fas_planning_safety_assumptions_review_v1/run_20261113T043023Z/`。27成员清单SHA **045e7abe8acebaec5ff7a9bfd58fdfd90ab890167f4539dc38c43705ce985b57**，传输ZIP前后SHA一致，服务器逐项验证及`sha256sum -c`全部通过。主文件`REPORT_ASSUMPTION_REVIEW_CN.md`、`planning_safety_assumptions_matrix_reviewed.xlsx`、`SOURCE_EVIDENCE.csv`。本机副本`C:\Users\zlab\Documents\Codex\research-output\FAS_ASSUMPTION_REVIEW_20261113\`；文献和工件不提交GitHub。
- 本轮正常SSH确认`zlab-Super-Server / zlab`，项目`/disk1/zlab/projects/safer-splat`，HEAD `ab643b8b75d2867cccde54bc7283d9868d48cdc2`、分支`audit-v3-validation-cohort-source-feasibility-v1`。只读项目结案/版本材料；不重跑六臂、不复核全历史运行、不宣称GPU当前空闲。原98次PSF恢复、243/196/47拆分与包络非实测加速的边界保留。
- 新导航/GPU/Factory/Token/PlantCommit/QP/PSF/FULL/训练/性能实验均**0**；没有后台任务、排队或自动后继。Windows只读取用户Excel、处理文献与生成交付物；服务器保存独立副本。未修改算法、历史数据、默认开关或安全合同。保留SUPER访问失败及文档工具问题记录。
- 发布：基点`9d99e979cede4f8b7ea5e51c890b610a454f1bdb`；文档分支`codex/assumptions-review-20261113`；修改前检查点`codex/checkpoint-assumptions-review-20261113`。原主工作树dirty不清理，仅stage/push HANDOFF；提交版本以GitHub文件历史为准。
- 最后更新：**2026-11-13，Asia/Shanghai**；更新者：**Codex，本Safer-Splat-1会话**。本轮交付后停止，未将取证建议写成已执行。

## 历史已结案：候选 A 结构差异与成本审查

> **当前结论（2026-11-13）：本轮“拒绝证书＋逆像”构造已结案，关闭独立创新主张。** 等信息、等数值要求下，现有构造可由碰撞 Safety Certificates＋相同转移预计算＋历史违规约束优先检查等效表达。终端早检查与相同运动段复用仅登记为 **NOT_STARTED 工程备选**，不是后继任务。不开发 Gaussian 全链误差包络，不启动证明、修复或实验，不自动扩展 B；本支线结束。

## 已结案阶段：候选 A 结构差异与可节约成本审查（2026-11-13）

- **结案裁决：CLOSED_INDEPENDENT_NOVELTY_CLAIM_ENGINEERING_OPTIONS_NOT_STARTED。** 只关闭当前“拒绝证书＋逆像”具体构造，不宣称整个拒绝证书研究方向无解。用户已明确要求结束支线；上一阶段关于补误差包络及本轮审查中提出的最小终端等价性证明建议，均不再作为待执行计划。
- 优化对象固定为**原生确定性制动尾分支验证**。规划阶段几何请求单列，不能借其失败频率论证原生尾段命中率或加速。
- 结构还原：固定模式下 `a^T(M ξ+d)>b-rho+epsilon` 与预计算 `w=a^T M, eta=b-rho-a^T d` 后的 `w^T ξ>eta+epsilon` 是相同判断；失败球的入口逆像与在同一预计算位置上检查碰撞证书是同一覆盖条件。模式/地图/数值误差与失效管理两方均需承担。跨不同查询优于完全相同查询缓存，并不证明优于该组合强基线；没有新增结构或实测总成本优势证据。
- 真实顺序：首控界→首段几何→canonical后继与h_stop→逐尾动作界/几何/转移→终端速度1e-12→终端位置→zero-hold。确定性尾的终端必要条件可以作为工程上的前置检查候选，但必须保留真实binary32图、饱和/ceil模式、有限性与动作约束。通过早检查不能省略后续安全检查；失败只否定指定制动尾，不否定同首控PSF。
- 三值/时效边界：提前获知终端失败不自动保留原先首先遇到的几何UNKNOWN、异常reason及恢复路由；不能将UNKNOWN悄悄改为FAIL。缓存几何不复用旧OPEN/Token，加速也可能改变原时效仲裁与轨迹。本次未实施或证明这种重排与绑定。

### 保留的历史分母与调用拆分（只读日志复算，不是新实验）

|原生臂|原制动终端速度失败后PSF PASS|失败分支几何调用|其中两段共享前缀|其余分支独有调用|
|---|---:|---:|---:|---:|
|61-PRM|19|46|38|8|
|61-RRT|29|78|58|20|
|17-PRM|6|14|12|2|
|17-RRT|16|38|32|6|
|53-PRM|17|42|34|8|
|53-RRT|11|25|22|3|
|合计|**98**|**243**|**196**|**47**|

- **98/98** 原分支reason为 `TERMINAL_CERTIFICATE_FAILED:TERMINAL_VELOCITY_NOT_ZERO_WITHIN_TOLERANCE`，随后同首控PSF均PASS；不是98个独立任务，不能将原尾失败扩大成首控不可恢复。这些是六臂/三任务中的相关事件，历史真实结果不改。
- 51次h_stop=1、47次h_stop=2；243=98个首段＋145个制动尾段。对98条记录，首段与L1、第一制动段与L2的端点binary32字节全部一致；position-first使第二位置不依赖尾首动作。196次属于普通相同运动段复用的潜在覆盖范围，不是拒绝证书独占能力。仍需地图/半径/后端/候选证据合法绑定，**未实现缓存、未发新资格**。
- 相对相同段复用，终端早检查剩余可避免的分支独有几何调用为47次。98条在速度判据失败后，终端位置与hold原本没有执行，不计入可节约工作。通过分支的完整验证及同首控PSF保留。
- 原生分支外包计时：从原epoch＋`L3_DISCOVERY_ADMISSION.elapsed` 到原制动返回后创建的PSF `entry_ns`，98次合计 **5.148574580秒**；47个最后独有调用从geometry ENTER到上述PSF entry的包络合计 **0.944806380秒**。后者中位数19.756553ms、最大24.310398ms。
- **包络不是独占几何耗时，也不是实测加速。** CALL_BUDGET只有ENTER、没有逐调用EXIT；区间含收尾/记账/调度。在冻结历史成本核算中仅是对应可删工作的理想外包上界；扣除预检查、复用/绑定、成功分支及失效管理开销后的净收益UNKNOWN。不得事后从历史时延扣时、据此改判OPEN或承诺新闭环加速。
- 98次PSF自身entry→return合计 **20.541659762秒**，必须保留，不属于可删成本。六臂原会话3317.445856秒仅作尺度参照，不将不同阶段、不同数值域或修改后轨迹混算加速比。
- 规划数据另列：父包1235条RETURN=861 SAFE＋374 UNSAFE＋0 UNKNOWN；374分为69状态/305运动请求。没有据此估计原生尾段证书收益，也未开展规划拒绝域新验证。

### 可复核来源、版本与本轮维护边界

- 原生包 R：`/disk1/zlab/tmp/fas_mature_reference_frozen_six_arm_native_v1/run_20261111T101823Z/`；清单SHA `4036f8d97603d54a4804e350da5d69f9898e5a3678eb1cb3eb9c6c00db3cd1cf`。计数/包络来自 `native_pair/raw/<arm>/results/{PSF_EVENTS,RAW_CYCLES,CALL_BUDGET}.jsonl`，按cycle/state/candidate关联；并核对PSF保存的states与原L1/L2端点字节。例61-PRM c521：3次原分支几何、h_stop=2、原分支包络63.827361ms、随后PSF PASS；不是新运行。
- 既有机制审查包：`/disk1/zlab/tmp/fas_candidate_a_rejection_certificate_review_v1/run_20261112T043342Z/`，21工件清单SHA `91a74686bb030244896ff7218abbb23f124e292d9d4c974409c01d9dfc7f0a93`。其中 `REPORT_CANDIDATE_A_CN.md` 第129–174行记录强机制还原与历史NARROW；原包不改写。父规划包见下方历史索引。
- 源C：`/disk1/zlab/v3_repair_worktrees/safer-splat-fas-vnext-tail-cardinality-targeted-repair-v1`，HEAD `33e34a3ac8d710452775ffe688af77393f734fa9`。Q=C＋`/reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1`；核查 `Q/certifier/backup_certifier.py:19–52`、`terminal_certificate.py:27–39`、`terminal_set.py:13–14`、`braking_backup_policy.py:20–45`。运行时 `C/reproduction/runtime/certification_execution_state_identity_repair_v1/repaired_components.py:49–69,97–113,162–178` 与 `stack_factory.py:112–163` 给出共享段与canonical绑定。`R/native_pair/code/psf_recovery.py:74–89,113–133` 保留原制动失败后的同首控PSF；`instrumentation.py:35–38,54–57` 确认几何仅记录ENTER。
- 本轮审查正常只读连接已确认zlab-Super-Server/zlab、项目 `/disk1/zlab/projects/safer-splat`，HEAD `ab643b8b75d2867cccde54bc7283d9868d48cdc2`。本结案发布只维护文档，不重新检查GPU/整机任务，不宣称服务器当前空闲；没有本支线运行、排队或自动后继任务。
- 发布基点：GitHub master `6f0b36387d36a27a297c952b1b66dc325c8326f3`；隔离文档分支 `codex/candidate-a-closeout-20261113`；修改前命名检查点分支 `codex/checkpoint-a-closeout-20261113` 指向该基点，保留旧HANDOFF。它不是对用户全部dirty/未跟踪数据的备份；原本机工作树、历史失败、服务器封印、算法源码及默认开关均不修改。本结案记录即本节，发布版本以GitHub文件历史为准，不另造实验封印。
- 最后更新：**2026-11-13，Asia/Shanghai**；更新者：**Codex，本Safer-Splat-1会话**。本次只提交/推送HANDOFF；新证明/修复/测试/导航/QP/PSF/FULL/GPU/Factory/Token/PlantCommit均0。封存成功不等于新增科学验证。

### 结案后的任务状态与重启门槛

|事项|状态|约束|
|---|---|---|
|当前拒绝证书＋逆像的独立创新主张|CLOSED|不作为新算法贡献，不自动继续研发|
|终端必要条件早检查|ENGINEERING_OPTION / NOT_STARTED|仅登记；证明、修复、测试及实验均未启动、未排队|
|相同运动段复用|ENGINEERING_OPTION / NOT_STARTED|仅登记；必须另行核对绑定与UNKNOWN/时效语义|
|Gaussian全链误差包络|NOT_STARTED / NOT_PLANNED_IN_THIS_BRANCH|本支线不继续开发|
|B方向|NOT_STARTED|不自动扩展或转移任务|

**结束条件已满足：完成结案交接后停止。** 只有出现新的、相对上述强机制不能等效复制的机制证据，或明确部署需求，才重新讨论是否开启；仍须另行明确授权，旧建议和本HANDOFF不构成实验权限。没有新证据/需求时，不以补模块、补误差包络或优化名义为由恢复该支线。

## 历史阶段：候选 A 拒绝证书机制可行性审查 V1（2026-11-12；后续建议已由上述结案取代）

- 当前目标：从明确失败见证建立有有效域的跨候选拒绝；只研究 A，不扩展 B，不预设 FAS/Gaussian 构成贡献。
- 裁决 **NARROW**：限定固定后备模式、单个必检几何条件及外向误差包络。已给解析证明、两个无相同失败状态前缀的不同查询正例、跨模式误删反例。不能由指定尾失败推出同首控全部后备失败。
- 关键新复核：六臂98条PSF事件的原制动失败全部为终端速度未达容差，随后98/98 PSF PASS。错误地把原制动FAIL变成整个首控拒绝会删除这些已接受结果。六规划账1235 RETURN中374 UNSAFE（69状态/305运动）；它们不是原生后备失败样本，不能混算命中率。
- 实际源链：canonical binary32转移、饱和/ceil可变制动、共享FULL闭段、terminal/hold、TieredPSFWitness及实际接受时限。源25次距离二分与1e-8扰动不构成可复用误差上界；原FAIL包装也不等于数学不可行。
- 已深入核对指定五篇的算法/公式/定理。Safety Certificates作者全文Alg1明确包含碰撞区域拒绝；仿射逆像、转移预计算、Lipschitz失败球本身不主张原创。Gatekeeper接受安全定理不等于拒绝可跨候选推广。
- 服务器 zlab-Super-Server / zlab；项目HEAD `ab643b8b75d2867cccde54bc7283d9868d48cdc2`、分支 `audit-v3-validation-cohort-source-feasibility-v1`；三保护HEAD及70保护文件前后不变。正式交接仍GitHub master；本机旧HANDOFF与dirty保留。
- 新包：`/disk1/zlab/tmp/fas_candidate_a_rejection_certificate_review_v1/run_20261112T043342Z/`
- 主报告 `REPORT_CANDIDATE_A_CN.md`，另有源码逐行快照/哈希、历史reason/见证字段复核、4例算术结果、操作与复核说明。21工件清单SHA **91a74686bb030244896ff7218abbb23f124e292d9d4c974409c01d9dfc7f0a93**；封存UTC 2026-11-12T04:42:48.769056Z，回执清单外。
- 上游224+166+8=398成员全量只读哈希复验。1个服务器标准库微计算进程、4个固定案例，600s CPU硬上限下算术体墙钟0.000106494s；process_time差低于计量粒度，**不是零开销或加速benchmark**。无torch/原canonical导入，不称GPU复现。新GPU/Factory/Token/PlantCommit/QP/PSF/FULL均0。
- 只读定位时的旧本地交接、缺文件路径、reason及witness字段名问题均在报告说明；没有重跑旧实验、改判历史结果或修改安全阈值。命名检查点 `candidate-a-mechanism-review-before-artifact-write`，原交接blob `9409cf5b1ba4b0745320e5c0ca26ff2d39bb88fe`及完整原文保留在新包。
- 下一步 **NOT_STARTED**：只考虑对一个保存的有限不安全见证/固定模式补足数值误差包络，并与“碰撞Safety Certificate+相同转移预计算”作等信息还原攻击。误差证明不成立则停在数学模型；机制等效则关闭本构造创新主张。未批准/启动正式评估器、GPU或下一批导航。
- 更新者：Codex，本Safer-Splat-1会话。相关任务进程检查未发现native_worker/session_new，当前审查脚本已退出；未建立后台任务或自动后继。本次仅发布HANDOFF，不提交算法/数据。

## 历史已封存阶段（保留，不作为新运行授权）

> **当前结论（2026-11-11）：三任务×两种冻结规划参考的原生六臂全部完成，6/6满足原软件到达条件。** 3405次实际提交、3405共享Gaussian执行段SAFE，0执行段UNSAFE/UNKNOWN、0近停滞窗口；不是严格Terminal、物理安全、普适导航或FAS创新证明。规划优劣随任务变化。全部进程退出，无自动后继。正QP残差和6次WARNING后备仍完整保留。

## 已完成阶段：冻结六路线原生闭环对照完成 V1（2026-11-11）

- **裁决：COMPLETED_SIX_ARM_FROZEN_REFERENCE_COMPARISON_WITH_LIMITS。** 本次用户明确批准在GPU1空闲时复用六条冻结路线/参数完成原预算，不重搜、不调参、不干扰其他作业。启动前实际GPU1空闲，通过单会话锁和每臂资源门；未使用GPU0、未终止/共用其他作业。
- 更新者Codex，本Safer-Splat-1会话；主包封存UTC **2026-11-11T11:14:17.046299Z**，勘误封存约11:16:56Z。正式交接仅GitHub master HANDOFF；命名检查点 `FROZEN_SIX_ARM_NATIVE_BEFORE_V1`，修改前blob `93a527f85cf89a8fa81c447d5591b77814304713` 完整保存在新包inputs/HANDOFF_BEFORE.md。服务器分析/实验，不在Windows运行测试；本地仅辅助代码传输暂存和交接，不动本地工作树。
- 主包：
  `/disk1/zlab/tmp/fas_mature_reference_frozen_six_arm_native_v1/run_20261111T101823Z/`
- 收尾勘误包：
  `/disk1/zlab/tmp/fas_mature_reference_frozen_six_arm_native_v1/closeout_correction_20261111T111651Z/`
- 服务器zlab-Super-Server/zlab；物理GPU1 `GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d`→逻辑cuda:0。结束及后置只读核查GPU1回到6MiB、无计算进程；本任务全部退出，无排队、重试或自动后继。
- 父CPU规划包166工件、清单 `97774c6a52f925b37198575047163be0a952d93858a2a8a2e7cb8e617a472ede` 前后复验，旧GPU资源阻断记录未改。本次新目录执行，不在已封印父包重启。六条路径、输入和原生Python代码逐文件哈希与父包相同；仅本任务目录授权及只读分析新增。

### 冻结范围、方法与真实六臂结果

- 固定顺序 **61-PRM→61-RRT→17-RRT→17-PRM→53-PRM→53-RRT**。项目有限Lazy PRM是成熟算法的项目实现，不伪称官方库；RRT为官方OMPL2.0.1 RRTConnect首解、seed61、range=.02、无平滑。既有路线不重搜，规划/CPU几何/CPU回归本轮新增均0。
- 同一 `ACCEPTED_MOTION_LOCAL_ARC_V1` 跟踪器、.02q前视、成熟A、TieredPSFWitness、CBF-QP、PD算术、map/初态/最终goal、dt=.05、半径.015q、动作/速度约束、1e-12终端/hold及 `FAS_SOFTWARE_ACCEPTANCE_DEADLINE_DEV_V1` 不变。原.8s guard/.2s reserve和实际接受边界未放宽。
- 每臂最多700周期/900秒；单GPU会话5500秒、最多6Factory/4200尝试或提交/8400求解/120000几何。此次所有实际用量在限内；不是沿用更早500步的结果或扩预算重试。
- 到达仍为实际post-state距task goal<=.01q且速度范数<=.005q/模型秒，连续10次实际提交；**不是1e-12严格Terminal**。六臂最后10次独立复算通过。滚动60步ΔProgress<=1e-4且末速<=1e-5为near-stall，六臂均0窗口命中。
- Trial61=开发；17=已知受阻挑战；53=事前固定补充评估，均非整个项目从未见过的holdout。比较单位3任务对，不是3405个独立样本。每路线仅一次/同种子，不作显著性结论。

|臂|到达提交数|共同H260 Progress|最终Progress|原生臂墙钟秒|PSF支撑提交|RetainedBackup提交|
|---|---:|---:|---:|---:|---:|---:|
|61-PRM|559|53.7202%|99.7232%|542.763|19|1|
|61-RRT|649|28.8734%|99.7218%|673.361|29|0|
|17-RRT|504|52.4253%|99.7173%|488.850|16|1|
|17-PRM|597|30.0720%|99.7149%|547.578|6|1|
|53-PRM|453|57.5386%|99.7274%|427.628|17|1|
|53-RRT|643|15.9252%|99.7181%|633.976|11|2|

- 六臂全部软件到达，不存在未启动、删失或隐藏失败臂。最后距离约.00214–.00224q、末速约.00140–.00166q/模型秒，完整值在CASE_RESULTS；没有把预测尾段当实际执行。
- 共同H260 **RRT−PRM**：Trial61 **−24.846793个百分点**、Trial17 **+22.353232个百分点**、Trial53 **−41.613325个百分点**。到达步数也呈PRM在61/53较少、RRT在17较少；不存在三任务一致赢家。
- H260目标距离缩减不是沿路弧长或累计位移。53-RRT H260实际走.429191q、沿参考弧长.438801q，但目标Progress仅.159252；不能据此说不运动或CBF堵死。表另存实际轨迹长度/沿路进度，路径形状、长度、拐角、速度/饱和和状态历史共同影响比较。
- 本轮只比较两种规划参考加同一安全层，**未重跑D直接目标，也未运行无FAS对照**。不把旧D/新R当同期单因素，不宣称FAS独有改进。SplatPlan、优化型RRT*、MPPI、同目标MPC本轮均NOT_RUN，不宣称战胜所有成熟方法。

### 接受时效、恢复与保留的分歧

- 3405实际提交：**3399 Primary、6 RetainedBackup；3399 OPEN、6 WARNING**。PSF尝试98次、支撑Primary提交98次；全部3405原Primary最终L3 PASS，原制动尾3307、标准PSF尾98。没有把生成尾当执行整条尾。
- 6次WARNING：61-PRM c360、17-RRT c422、17-PRM c379、53-PRM c386、53-RRT c52/c415；均原Primary L3 PASS，但最终guard已超过Primary .6s资格界，选择可在.8s内接受的RetainedBackup。没有删除这些时效事件或将其当Primary及时通过。
- 独立核对全部接受epoch、selected/executed、Token/事务与binary32推进，**0角色时限违规、0未决提交、0未验证执行段、0原生重试**。最小实际角色接受余量22.914259ms；混合角色接受最大669.090ms属于Backup，不能误说Primary超.6s。
- Trial61相同PRM路线本轮559提交而旧R557：共同c0–359动作/状态字节一致，首次c360分歧。旧最终guard .539329398s OPEN→Primary；新.600084022s WARNING→Backup（接受.601290265s，合法于Backup .8s界）。旧557结果不改，不能把这2步差异归因路线优化，也不能事后扣除调度/观察器耗时。
- entry→Plant返回包含更多前置成本，不等于原epoch→接受时限。所有耗时原值保留；模型dt=.05仍不是实际20Hz/WCET。

|臂|entry→Plant p50/p95/p99/max ms|最小接受余量ms|最小记录代理净空q|
|---|---|---:|---:|
|61-PRM|394.582 / 496.563 / 784.750 / 1737.223|69.663|0.00659808609|
|61-RRT|368.738 / 519.704 / 1411.735 / 3202.353|45.972|0.00257378245|
|17-RRT|405.428 / 468.746 / 906.999 / 1615.575|22.914|0.0105730093|
|17-PRM|369.392 / 466.281 / 949.965 / 1628.875|58.683|0.00662276810|
|53-PRM|423.851 / 487.668 / 766.861 / 1674.859|51.057|0.0132582125|
|53-RRT|401.474 / 490.551 / 1374.326 / 2772.130|157.530|0.00963523715|

### 数值残差：旧60条保留，新257条实际P0正值不抹零

- 本轮3405个原P0提案中**258个issued32最大行残差>0，其中257个实际作为P0执行**；61-PRM c360正残差提案未选中，不能归到实际后备动作。
- 各臂正值提案/实际P0执行：61-PRM 51/50、61-RRT52/52、17-RRT30/30、17-PRM73/73、53-PRM7/7、53-RRT45/45。最大 **1.3640604618059271e-9**（原归一化CBF行，q/模型秒²）。所有正值动作盒检查通过，不能把正值改成0。
- 补充审计按cycle/state、raw64动作字节、issued32字节唯一关联proposal_events/box/solver：**53-RRT c200 raw64已+9.396509612069615e-12、c201已+1.320514878000445e-13**，所以并非所有本轮正残差都纯由量化产生。c200 issued32变为+1.479489308842119e-10；c201 issued32不正。其余raw64最大残差均<=0。
- 沿用原求解/资格语义，未改solver tolerance、CBF阈值或安全门。共享L2/L3和实际段SAFE并不等价严格QP半空间可行，也不证明这些偏差普遍无害。全逐行矩阵/最大违反Gaussian仍未序列化，只有矩阵哈希与最大值，不能补造。
- 若论文要求“每个issued动作严格满足原P0行”，证据仍不足，应另立量化/数值资格问题；本任务只保留真实局限，不追加修复或试验。历史R557的60次正值仍是原历史分母。

### 预算、复核、勘误与封印

- 实际 **1GPU会话、6Factory、3405尝试/提交、3503求解、46579几何调用、会话3317.445856s（55.29分钟）**。单臂最大673.360656s<900s；无重规划、无原生结果导向重试。父CPU规划694.505813s/2055 FULL只读复用，不算本轮新增；各臂历史规划+新执行的成本相加不是同一次连续端到端测量。
- 3405条实际动作/状态/接受与6810审计hash、全部目标窗口、3405路径进度更新独立复核通过。所有路径进度仅据接受运动更新、无进度冻结；前视目标重算误差0。离散参考段索引可跨极短段，验证的是连续局部弧长/实际运动界，并非“每段必有一个软件采样点”。
- 70保护文件+64来源文件=134锁定物理文件前后不变，三个保护HEAD/工作树保持CLEAN：Candidate33e34a3…、Frozen481c3e5…、Perf b0a6bb…；原默认OFF、算法源码、地图和历史记录未改。算法不commit/push，只有HANDOFF维护。
- **收尾统计错误明确保留：** 主包显存派生表误把nvidia-smi利用率第7列当memory.used第6列，产生19/20MiB错误。原始采样完整正确；不重封主包，独立勘误包修正为各臂设备采样最大1764MiB、进程采样最大1756MiB。5秒采样不是连续峰值；PyTorch峰值allocated129047552B/reserved148897792B也非整个进程峰值。
- 同勘误包补齐主派生残差记录中raw64字段的正确事件路径；主258/257计数未变。主分析/报告/封存16.324076s，勘误只读分析/封存5.599217s；没有新增测试、求解、FULL或GPU。
- **主包224工件manifest SHA：**
  `4036f8d97603d54a4804e350da5d69f9898e5a3678eb1cb3eb9c6c00db3cd1cf`
- **独立勘误8工件manifest SHA：**
  `79857e76127c47ec10ba71509694b01bb56d7fba4b5f00e074e4b67ab44c3c80`
- 两清单现场复验，勘误前后主224清单再次复验；SEAL_RECEIPT均清单外，不自引用。主包错误派生显存字段以勘误包覆盖解释，旧文件不删不改。
- 入口：主FINAL_REPORT.md、results/CASE_RESULTS.csv、PAIRED_RESULTS.json、NATIVE_SCORECARD.json、INDEPENDENT_CROSSCHECK.json、PATH_AND_GOAL_INDEPENDENT.json、PRIOR_SAME_ROUTE_REPLAY_BOUNDARY.json、完整native_pair/raw；勘误REPORT_CLOSEOUT_CORRECTION.md、QP_RESIDUAL_BINDING_COMPLETED.json、GPU_MEMORY_AND_FACTORY_COST_CORRECTED.json、BACKUP_AND_L3_EVENTS.json。

**下一步 NOT_STARTED：** 本轮冻结路线复验已完成，停止追加运行和调参。成熟规划参考均可在这三任务的软件系统中到达，不能据此包装FAS/规划创新；先收束论文主张和严格issued-QP可行性的证据边界，再决定是否另行授权更强优化基线或数值修复。观测支持域、独立物理配准误差、严格GPU数值包络、实际20Hz与普适目标收敛仍未建立，所有SAFE/净空只限当前Gaussian代理地图。

## 以下为历史封存阶段（原文保留，不代表当前运行）

> **当前结论（2026-11-11）：三案例×两种规划器的CPU路径对照已完成；原生六臂因GPU1占用全部未启动。** 六条冻结路径共184闭段通过原FULL复验，不等于可跟踪或到达。历史557条QP中60条量化后正残差已核清，不能声称严格半空间可行。资源门关闭，无自动后继。

## 当前阶段：成熟规划参考匹配对照 V1（2026-11-11）

- **裁决：CPU_PLANNING_COMPLETE_NATIVE_BLOCKED_RESOURCE_CONFLICT**，不是完整闭环对照PASS。用户授权本轮成熟方法审查、适配、有界规划及条件原生比较；没有授权终止/共用其他GPU作业，未绕过资源门。
- 更新者Codex，本Safer-Splat会话；封存UTC **2026-11-11T10:05:14.212500Z**（北京时间18:05:14）。正式GitHub master仅更新HANDOFF。命名检查点 `MATURE_REFERENCE_COMPARE_HANDOFF_BEFORE_V1`，旧blob `fd316f94da73c0507dfbece886604298044286d4` 全文保存在本包inputs/HANDOFF_BEFORE.md。旧R557到达与全部失败记录原样保留。
- 服务器zlab-Super-Server/zlab，经正常zlab-4090；新包：
  `/disk1/zlab/tmp/fas_mature_reference_matched_comparison_v1/run_20261111T094603Z/`
- 原生启动前GPU1物理UUID `GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d` 出现PID806672，进程路径functional3dgs/bin/python，进程显存4424MiB、设备总已用4432MiB。启动器报 `GPU1_RESOURCE_CONFLICT_NO_QUEUE`，位于session_new.py:15、GPU_SESSION_CLAIM创建之前。**本任务GPU会话=0、Factory=0、新QP/PSF求解=0、PlantCommit=0；全部六臂NOT_RUN。** 未终止/共用该进程、未换GPU0、未排队/重试。快照不构成对该作业用途或归属的完整鉴定。
- 当前无本任务运行/等待进程，无自动后继。读取历史残差与新CPU规划不是原生导航；不得给出本轮到达率、H260 Progress、时效或实际运动安全比较。

### 冻结方法、任务与公平边界

- 比较**规划参考**，两种规划器将共享同一 `ACCEPTED_MOTION_LOCAL_ARC_V1`、.02q前视、成熟A、原TieredPSFWitness、CBF-QP、动作/速度约束、1e-12终端/hold和 `FAS_SOFTWARE_ACCEPTANCE_DEADLINE_DEV_V1`。最终task goal不变。原.8s/.2s时限不放宽，原模型dt=.05不解释为20Hz。
- 项目有限Lazy PRM：标准算法的项目实现，**不是官方成熟库**；官方OMPL 2.0.1 RRTConnect：range=.02、seed61、首条精确解，不平滑、不换种子。原C++采样绕过Python计数的问题没有掩盖：本轮不声称内部采样计数受控，改用经过验证的实际状态/运动/FULL和墙钟硬限额。
- 官方出处：[RRTConnect](https://ompl.kavrakilab.org/classompl_1_1geometric_1_1RRTConnect.html)、[MotionValidator](https://ompl.kavrakilab.org/classompl_1_1base_1_1MotionValidator.html)。OMPL二进制SHA `16ccc417ed3432e7e36115712232ea84b4d3ce83643eb50092ae97c8c71a1db2`。搜索核心未重写，仅用共同原FULL替代状态/完整闭段有效性接口。
- Trial61=开发案例；Trial17=已知直线受阻挑战；Trial53=事前固定补充评估案例，**都不是全项目从未见过的holdout**。顺序固定61-PRM→61-RRT→17-RRT→17-PRM→53-PRM→53-RRT。
- 每个规划器/案例300秒、3000 FULL、1024实际运动几何查询、4096状态检查；共享同样float32字节缓存规则，最终路径复验绕过缓存。PRM固定512/k12后至多1024/k24、最多64候选；搜索盒[-.5,-.5,0]–[.5,.5,.3]仅是计算范围，**不是已观测自由空间**。
- 原生预注册最多6Factory、700周期/900秒每臂、5500秒单GPU会话、8400求解/120000几何；这些原生预算本轮均未使用。不能直接运行已封印目录，应另建执行包并重新资源准入。
- 接口探针10项通过，另1项种子顺序检查通过：首探针晚设种子警告保留，正式搜索在任何随机对象构造前设种子。两CPU探针约.998s；原生接线另立1进程/30秒准备预算，合并静态场景检查6组的端点字节/初始参考/错路径拒绝，内部.0353s，含传输准备约4.12s。不是GPU端到端验证。

### 实际CPU规划结果

|任务|项目Lazy PRM 路长q / 段 / 秒 / FULL|官方RRTConnect 路长q / 段 / 秒 / FULL|原生比较|
|---|---|---|---|
|61|.8928281 / 10 / 63.690 / 189|.9807007 / 50 / 206.412 / 614|两臂NOT_RUN|
|17|.9321636 / 11 / 74.788 / 217|.9010830 / 46 / 97.148 / 289|两臂NOT_RUN|
|53|.8974526 / 10 / 28.488 / 78|1.1220001 / 57 / 222.782 / 668|两臂NOT_RUN|

- 全六组规划和最终闭段复验通过；累计**2055 FULL、853运动几何查询、694.506秒规划进程总墙钟**；184条最终路径闭段新鲜复验SAFE。搜索期间374个状态/运动请求UNSAFE全部保留，UNKNOWN请求0。不是374次碰撞/动作，也没有真实执行。
- 各组失败候选、全查询START/RETURN、字节路径与计数守恒独立核查通过。路径几何证据仍是原共享Gaussian代理、没有独立物理真值/观测支持域误差上界；没有运行新的动力学跟踪或闭环。
- RRTConnect是成熟快速首解基线，不是优化型强基线的全集。本轮无平滑/路径优化，不能用PRM三例更快、两例更短宣称优于全部成熟规划方法。Trial17两种路径均存在也不能把历史直线UNSAFE改写为错误。

### 历史60次正QP残差：已确认及缺口

- 从旧R557原始RAW_CYCLES逐条核对控制字节、原始/量化后最大残差、动作盒与L2/L3/执行段记录。**557个raw64最大残差均<=0，60个issued32最大残差>0**；非新增求解或新历史矩阵。
- 正值min6.1697175e-14，中位1.0362429e-10，p95=4.5926832e-10，max8.6105385e-10（c275）。c275 raw64最大残差−1.0662355e-10，issued32转为正；60条动作盒均严格满足，因此正值来自原归一化CBF行。
- 真实符号是 `A u-b>0` 表示线性约束违反，非正安全裕量。双积分器源谓词为 `gᵀu+vᵀHv+6gᵀv+5h>=0`，按梯度范数归一化；残差单位q/模型秒²，不是净空q或barrier q²。
- 源Clarabel 0.10.0仅DefaultSettings+verboseFalse，tol_feas=1e-8；这不是issued32硬保证，不能以“小于solver tolerance”抹零。C0核来源/身份/动作盒，不重新逐行核CBF；L2/L3和执行段FULL是独立的安全义务。60条均历史L2/L3 PASS、执行段SAFE，只说明该记录中后续检查通过，**不证明正残差普遍无害、严格CBF可行或物理安全**。
- 历史仅保存矩阵哈希和最大残差，没有逐行载荷，因此违反行/Gaussian身份仍UNKNOWN；本轮没有新求解补写历史。全部周期和分布见HISTORICAL_QP_RESIDUAL_AUDIT.json/CSV。
- 未改残差、源码、阈值或历史裁决；新比较也只共享原实际数值合同。若主张严格P0可行，需独立量化感知修复版本与重新匹配对照，本轮不声称完成。

### 未运行方法、来源及封印

- 官方SplatNav服务器已有HEAD `e996e229daca4e25703a13243541371290a6f7f8`，现存dirty保持。SplatPlan/Bezier及RRT*真实存在，但SplatPlan Stonehenge默认radius=.01而本任务.015，廊道/碰撞和动力学输出合同需专门适配；**NOT_RUN，未宣称战胜它**。[官方仓库](https://github.com/chengine/splatnav)。
- 已有MPPI是CBFKit MPPI GS软代价CPU H20适配，旧任务73/12/74/66/9/26/79/31，并非本轮Trial61/17/53完整成熟A对照；未伪称pytorch_mppi已集成，软代价不是安全证书。优化型规划/同目标任务型MPC本轮均未挑战。
- 70项保护来源及Candidate/Frozen/Perf三HEAD/dirty无变化；含额外外部工件总95文件后置复核一致。仅独立DEV实验文件、参考旁路接线与文档新增，原代码/default/历史数据不变。
- **166工件封印**，SHA清单现场复验通过；manifest自身SHA：
  `97774c6a52f925b37198575047163be0a952d93858a2a8a2e7cb8e617a472ede`
- 关键文件：FINAL_REPORT.md、PREREGISTRATION.json、NATIVE_ADMISSION_BUDGET_ADDENDUM.json、SOURCE_LOCK.json、DEV_DIFF.patch、results/CASE_RESULTS.csv、results/CPU_PATH_INDEPENDENT_AUDIT.json、results/HISTORICAL_QP_RESIDUAL_AUDIT.json/CSV、results/GPU_RESOURCE_GATE_BLOCK.json、PROTECTED_AFTER.json、ARTIFACT_SHA256.txt。SEAL_RECEIPT.json是封印外回执，不自引用。
- **下一步（未启动）**：资源可用并明确继续后，新执行包复用六条冻结路线、参数和相同安全层，执行原预注册六臂；不重搜、不调参、不把已封印包当可写运行目录。本轮不足以回答谁更能到达、谁更安全或是否存在FAS独有创新。

## 以下为历史封存阶段（原文保留，不代表当前运行）

> **当前结论（2026-11-11）：Trial61 冻结 R 已通过原软件到达判据。** 从冻结初态完整重跑一次，557次实际提交后停止；c547–556连续10次同时满足距离<=.01q、速度<=.005q/模型秒。终距.002207373q、末速.001352092、Progress=.997185134。共同前500步动作/状态与上一轮逐位一致。557代理SAFE、0时效违规、0重试；封存退出，无自动后继。不是严格Terminal、物理安全或泛化证明。

## 当前阶段：Trial61 R 最终到达验证 V1（2026-11-11）

- **裁决：PASS_FROZEN_R_SOFTWARE_ARRIVAL**。只验证一条固定R；本轮D未运行，不是新增D/R配对，也不是新的独立任务样本。
- 更新者：Codex，本Safer-Splat会话；封存UTC **2026-11-11T09:24:51.275417Z**（Asia/Shanghai 17:24:51）。GitHub master仅发布HANDOFF，算法代码不commit/push。命名检查点TRIAL61_FINAL_ARRIVAL_R_BEFORE_V1，旧HANDOFF blob796dc0979022d7e7905dd7e2b7f920989fe18e0f及全文存新包inputs/HANDOFF_BEFORE.md；源检查点NAMED_CHECKPOINT.json。
- 服务器zlab-Super-Server / zlab，经原zlab-4090；GPU1物理UUID GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d→逻辑cuda:0。一次会话、一次Factory，已退出并释放设备；无物理机器人、无安装、无他人进程操作、无自动后继。
- 基线为上一轮run_20261111T084048Z，109工件清单7f1e1ccfabf7eff341c3291b9605ac7d4f538b55d595ee3ed1429571833428b5，完整复验。成熟A、原TieredPSFWitness、QP、PD、初态/最终goal、地图/顺序/坐标、路径/跟踪器、动作/速度界、.015q、dt=.05、1e-12终端/hold均不变。
- 接受合同仍 **FAS_SOFTWARE_ACCEPTANCE_DEADLINE_DEV_V1**，acceptance_plant.py SHA044017f2fb814996e03e3127894b8f5bf7799c21c5973e77b04cf910ee94e773；跟踪器仍 **ACCEPTED_MOTION_LOCAL_ARC_V1**，PATH SHA3650e6085ddb1ff78996942d9006bbd7541c503fa82f7a6de6db48488fdfbbdc。原.8秒guard/.2秒reserve和实际接受门不放宽。
- 本轮仅修改独立DEV运行器的外部时域/看门狗、单R任务列表和日志标签；全部其他算法Python文件与父包哈希一致。70外部来源及Candidate/Frozen/Perf三HEAD/dirty状态前后一致，原代码、默认开关和所有历史记录未改。精确版本见SOURCE_LOCK、IMPLEMENTATION_IDENTITY与DEV_DIFF。

### 为何不接续旧Token

历史末状态、Token观察和路径日志存在，但没有已验证的完整运行态恢复入口。原worker重新build_arm Factory、Reference/streak和cycle0；Token store列出的prepare/validate/activate/consume接口不是恢复证书owner、缓存、协调器/epoch/权限的原子快照协议。故选择**从冻结初态完整运行**，不复用旧Token，不把轨迹拼接当执行资格接续。证据见inputs/RESUME_DECISION_EVIDENCE.json。

### 预注册预算和准入

- 先固定R **最多700周期、900秒单臂、1000秒GPU会话、1400求解、20000几何调用**；一次GPU1/一次Factory、零原生重试。原单周期时限与到达阈值不变，预算不按结果追加。
- 8项静态接线检查通过，含源/goal/初态/路径身份、未改算法哈希、预算位置、fresh cycle0、单会话/拒绝重启及语法。准备含来源校验1.685190s；父包34项CPU回归只复用，不伪称本轮重跑。
- 资源冲突、身份/保护源变化、Oracle UNSAFE/UNKNOWN、未决提交、资格/接受异常或预算即停；合法无动作终止，不调参找赢家。本轮未触发这些停止条件。

### 实际到达过程与结果

|指标|本轮R|
|---|---:|
|实际尝试/提交|557 / 557|
|停止|c556达到连续10提交软件判据|
|首次距离<=.01q|c509|
|首次同时满足距离/速度|c522，仅连续到c525|
|首次合格段中断|c526速度.0052508756>.005，streak归零|
|最终连续窗口|c547–556，10次|
|最终距离q|.002207373202179591|
|最终速度q/模型秒|.0013520923136459196|
|最终Progress|.9971851341881679|
|H260 / H500 Progress|.537202159096277 / .9597591831463638|
|末60步ΔProgress|.046332335352581966|
|near-stall|0完整窗口命中|
|Primary / OPEN|557 / 557|
|PSF尝试 / 支撑提交|19 / 19|
|Backup / Alternative / Terminal实际提交|0 / 0 / 0|
|执行段Oracle SAFE / UNSAFE / UNKNOWN|557 / 0 / 0|
|最小记录proxy净空q|.006598086088473372|
|接受耗时最大ms / 最小余量ms|540.682964 / 59.317036|
|entry→Plant返回p50 / p95 / p99 / max ms|380.971 / 474.529 / 685.512 / 1329.526|

- 最终10次最大距离.002266473611q、最大速度.004763049888，均满足原阈值；不是只看到距离接近就宣布成功。终点附近有小幅往复，速度不为零，所以**软件到达不是1e-12严格Terminal或无限保持保证**。
- 原H500“未到达”结论不改。本轮共同前500条动作/状态逐位无差异，之后57次完成接近、减速与连续判据；这是固定版本的单案例复现，不证明整个GPU环境等价，也不增加独立任务数。
- 路径段0–9依次访问，最终弧长等于.8928280999884619q总长，0进度冻结；557更新绑定实际收据，独立目标重算误差0。没有仅凭前视目标更新实际进度。
- 保留数值局限：60次issued32 QP后验最大行残差为正，最大8.61053849749e-10（c275），见原raw source_qp_calls；未修改阈值或把这些数值改成零。此计数不等同于原资格拒绝，亦不从代理SAFE推出严格GPU数值误差证明。
- 同一新R不是与旧D在H557的公平配对；只能结合上一轮同版本D/R H500结果作案例解释，不能宣称D在扩展时域必不达。单Trial61开发案例，不证明普适导航、跨地图泛化或规划创新。

### 成本、独立核对及封存

- 实际 **1GPU会话、1Factory、557尝试/提交、576求解、7471几何调用**；会话 **532.499252s**，单臂532.037405s；所有上限内。规划0、CPU FULL0、原生重试0，无本轮工程失败或被隐藏重试。
- Factory初始化4.351051s；参考更新累计740.497ms、参考计算865.088ms均计总运行墙钟。分析/报告/封存2.607922s，另记而不伪称GPU计算。PyTorch峰值allocated129047552B/reserved148897792B，不等于整进程显存峰值。
- 557条binary32状态/动作/接受身份、1114条审计行哈希、557条进度和全部到达窗口独立核对；0未决/未验证段/接受违规。入口最大1.33秒仍保留，不扣日志或调度时间；dt=.05不代表20Hz。
- **服务器包：** `/disk1/zlab/tmp/fas_trial61_r_final_arrival_validation_v1/run_20261111T091313Z/`
- **85工件清单SHA256：b1dfea8d465125df486102c31545510f19c4806c5498f3fc4bfa2d628dcefc54**。SEAL_RECEIPT为清单外收据；封存后不改包。
- 入口FINAL_REPORT.md、results/SCORECARD.json、GOAL_TIMELINE.csv、GOAL_INDEPENDENT_AUDIT.json、PARENT_R_NUMERIC_COMPARISON.json、PATH_PROGRESS_INDEPENDENT.json、INDEPENDENT_CROSSCHECK.json、RESOURCE_TOTAL.json；完整raw/R/results保留状态、动作、参考、时效、Oracle、PSF/Token/trace。
- 所有SAFE/净空仅当前共享Gaussian代理地图。观测支持域、独立物理配准误差和严格GPU误差包络仍未知；q不是米，没有物理机器人安全证明。

**下一步 NOT_STARTED：** Trial61这条冻结R的最终软件到达验证可以结案，保留版本和全部历史失败。先整理参考/跟踪/资格层的证据边界；若检验泛化或其他任务，需另行预注册公平对照，不继续对本案例调参刷成功，不自动启动任何后继。

---

## 上一阶段及更早交接（历史结果原样保留）

> **当前结论（2026-11-11）：Trial61 路径进度固定点已修复，新的同版本 D/R 各完成500次提交；R显著持续推进，但两臂均未达到冻结软件终点。** R H260 Progress=0.537202159、H500=0.959759183；末距0.0315562q、速度0.0473236，不能写成到达成功。1000执行段代理SAFE、0接受点违规、0原生重试；已封存退出，无自动后继。以下为当前状态，旧结果原样保留。

## 当前阶段：Trial61 已接受运动路径进度修复 V1（2026-11-11）

- **裁决：PROGRESS_REPAIR_VALIDATED_PAIRED_HORIZON_COMPLETED**。含有限CPU回归、实际D/R、独立复算及封存；不是Goal Success或论文创新PASS。
- 更新者：Codex，本Safer-Splat会话；封存UTC 2026-11-11T08:59:04.889159Z，Asia/Shanghai。正式交接在GitHub master，仅发布HANDOFF。修改前命名检查点TRIAL61_ACCEPTED_PROGRESS_BEFORE_V1；旧HANDOFF blob a9e17dbb51c4598fbc8dcd53ed708a3d08ce64fd及全文已存新包inputs/HANDOFF_BEFORE.md，源/HEAD检查点在NAMED_CHECKPOINT.json。
- 所有测试/实验在zlab-Super-Server、zlab，经原zlab-4090；GPU1物理UUID GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d，逻辑cuda:0。结束无计算进程、GPU1回到6MiB；本任务进程退出，无后台后继、无物理硬件操作。
- 固定成熟A、原TieredPSFWitness、QP、goal/初态、地图/顺序、半径.015q、dt=.05、动作/速度界、1e-12终端、.8/.2与失败语义不变。接受适配合同仍FAS_SOFTWARE_ACCEPTANCE_DEADLINE_DEV_V1，acceptance_plant.py SHA **044017f2fb814996e03e3127894b8f5bf7799c21c5973e77b04cf910ee94e773**，与上一轮完全一致；它仍不是原保护源码原封不动的执行层。
- 同一冻结路线SHA **3650e6085ddb1ff78996942d9006bbd7541c503fa82f7a6de6db48488fdfbbdc**，10边、长度0.8928280999884619q。未重规划、换种子、重跑CPU长跟踪或静态几何；既有全边证据通过父包身份引用，实际执行段另查原Oracle。
- 70个锁定保护/外部文件及Candidate/Frozen/Perf三个HEAD/工作树状态前后一致；HEAD分别33e34a3ac8d710452775ffe688af77393f734fa9、481c3e5e24648d0219e1969f1145648ac99f6943、b0a6bbb96512cef5085feada98a900bf9d8ff15f。父100工件与只读补充包复验通过。原代码、默认开关、旧失败均未覆盖，算法源码不commit/push。

### 固定点及实际修复

旧R只在距当前段终点<=.005q时切段，而.02q前视能跨拐角，形成“旧段不动、目标位于下一段、到达该目标后名义动作趋零”的固定点。上一轮R段2从c115保持到c499，旧证据不改。

新DEV合同 **ACCEPTED_MOTION_LOCAL_ARC_V1**：
1. get只读，不因前视跨角推进索引。原协调器提交、Token/trace与原执行段Oracle和时效复核完成后，才对真实pre/post更新一次；状态/goal/map/cycle/receipt/action绑定，拒绝、UNKNOWN、重复或未接受状态不更新。
2. 单调弧长只在[s,s+2×实际位移]的连续局部路径上投影，不使用全局最近分支；单步运动界来自原dt和速度盒。静止不推进、回退不倒退、终点不外推，精确重复顶点压缩并保留原索引。
3. 0.02q对应管约束投影点及真实运动弦；9个样本加半间距给出实数Lipschitz距离上界，float64实现没有外向舍入证明。偏离则冻结进度。**此管不是安全半径或碰撞证书**，前视仍可能切角；每条实际运动仍须通过原FAS闭段检查。无一般收敛/零切角承诺。
4. 进度更新置于接受关键区间之后、下一周期之前，单独记时；未删除审计、扣耗时或改变原epoch。R更新累计672.157ms/max5.649ms，参考计算累计790.446ms，均计入运行总墙钟。
5. 18路径/接线场景+16接受点/Token故障回归，**34/34**、2进程，脚本计时1.078275s；含SSH与启动的客户端命令总耗时2.014721s，启动未独立服务器计时。无CPU QP/FULL/CUDA。模拟异常不证明掉电或跨重启恰好一次。
6. 新原生R在c167的当前参考记录进入段3，后续依次访问段0–9，无回跳/跳过段/进度冻结；最终弧长0.861317972q。500进度更新均与实际收据绑定，增量<=2×位移，独立目标重算误差0、运动弦界差<=1.74e-18q。最大记录路径偏离0.010454873q。不能将有限验证提升为普适路径跟踪证明。

### 新同版本D→R真实结果

|指标|D直接目标|R冻结绕行+新进度|
|---|---:|---:|
|尝试/提交|500/500|500/500|
|软件到达|H500未到达|H500未到达|
|H260 Progress|0.08541265693212023|0.537202159096277|
|H500 Progress|0.08541368574505083|0.9597591831463638|
|末距goal q|0.717204107095|0.031556211448|
|末速度q/模型秒|2.350715592e-7|0.047323580156|
|末60步ΔProgress|0|0.130167558759|
|首次near-stall|c176–235|无，441完整窗口均阴性|
|Primary / OPEN|500 / 500|500 / 500|
|PSF支撑实际提交|82|0|
|执行段Oracle SAFE/UNSAFE/UNKNOWN|500/0/0|500/0/0|
|最小记录proxy净空q|5.712748631e-8|0.006598086088|
|entry→Plant返回p50/p95/max ms|287.631 / 501.560 / 1280.270|387.807 / 531.061 / 1520.729|
|接受耗时max ms|460.922|516.121|
|最小接受余量ms|139.078|83.879|

- Progress按实际状态到最终goal距离缩减归一化，不是沿路径弧长或累计位移。共同H260 R−D=0.451789502164，即 **+45.178950个百分点**。软件goal仍距离<=.01q、速度<=.005、连续10提交；R距离与速度均未达，不能外推“再几步必到”。
- D仍强名义请求/极小执行动作；R末60步名义范数中位数.038400747、执行.010753222，持续前进而非旧固定点微动。R在500步上限结束，未遇新的资格阻断或near-stall；不自动延长时域。
- 新D与上一轮500条动作/状态逐位一致；新R自c73首次动作及状态分歧。旧R c53超时及随后版本R500固定点失败均保留。与旧R的差异是跟踪器版本诊断，不能把不同时刻耗时变化归因于速度提升。
- 新D/R同安全层/接受层/初态，名义参考不同；方向、幅值、状态历史联合改变，**不是纯方向单因素**。单Trial61开发任务、固定顺序、无重复，不证明泛化、FAS/Gaussian独有优势或新规划方法。
- 1000条binary32状态/动作/接受身份与2000审计行独立复核通过；0未决、0过期已提交、0未验证执行段。代理SAFE不是物理真值，未建立观测自由空间或独立GPU误差包络；近零代理净空不能淡化。dt=.05不代表20Hz，入口max超过1秒不扣除。

### 预算、失败、封存

- 预注册一次GPU会话/两Factory、D→R各500周期或600秒、总1800秒、1000尝试/提交、2000求解/50000几何，原生重试0。
- 实际 **1会话、2Factory、1000尝试/提交、1082求解、11556几何、992.914579s**。D436.792851s，R554.258963s，均在上限内；两臂PyTorch峰值allocated129047552B、reserved148897792B，非nvidia-smi全进程峰值。
- 首次准备因新父目录未建立报FileNotFoundError，测试/GPU均尚未开始；独立目录mkdir修复，失败摘要保留。CPU和原生均首轮通过，无结果导向重试或调参；正式分析/封印首轮完成。
- **权威包：** `/disk1/zlab/tmp/fas_trial61_accepted_motion_progress_repair_v1/run_20261111T084048Z/`
- **109工件清单SHA：7f1e1ccfabf7eff341c3291b9605ac7d4f538b55d595ee3ed1429571833428b5**，清单复验通过，SEAL_RECEIPT为清单外回执。主包封存后不再写入。
- 阅读：FINAL_REPORT.md、results/SCORECARD.json、PATH_PROGRESS_INDEPENDENT.json、INDEPENDENT_CROSSCHECK.json、HISTORICAL_NUMERIC_COMPARISON.json、RESOURCE_TOTAL.json、FINAL_DECISION.json、SOURCE_LINE_INDEX.json；原始native_pair/raw/D|R/results下动作、PATH_PROGRESS、ACCEPTANCE_GATE/TIMING、CYCLE_AUDIT和Oracle。代码差异在DEV_DIFF.patch，预算PREREGISTRATION.json，外部来源SOURCE_LOCK.json。

**下一步 NOT_STARTED：** 旧路径索引固定点可结束修补，保留此次无调参版本。若要证明软件到达，需要另行预注册覆盖终点接近、减速和连续10步判据的有限验证，保持相同参考与安全合同；不能把本次未运行的后续步补成成功，也不因未达而再改安全层或追求新颖性。当前任务到本包封存为止，没有自动续跑。

---

## 上一阶段及更早交接（历史结果，原样保留）

> **当前结论（2026-11-11）：软件接受点修复及新D/R各500提交已完成；两臂均未到达。** R共同H260进展多22.3621个百分点，但末段发现路径索引/前视更新固定点。无接受时效违规、无未决提交；任务已退出。下文当前阶段为最新，旧失败原样保留。

## 当前阶段：Trial61 软件接受点修复与新 D/R 对照（2026-11-11）

- **当前裁决：ACCEPTANCE_REPAIR_VALIDATED_NATIVE_PAIR_COMPLETED**。服务器 CPU 16/16场景首轮通过；新同版本 D/R 各500次真实软件提交，1000/1000代理Oracle SAFE，接受时刻均符合角色时限，0未决、0原生重试。两臂均未软件到达；本裁决不是导航到达PASS。
- 更新者：Codex，本Safer-Splat会话；更新时间2026-11-11 Asia/Shanghai。正式GitHub master，仅发布HANDOFF，不提交实验源码。更新前命名检查点HANDOFF_BEFORE_TRIAL61_ACCEPTANCE_REPAIR_20261111，旧blob 12f1958a9a3c61e634187c9c618f7a02fd93cfd8及全文存主包inputs。
- 实验均在 zlab-Super-Server / zlab，经原 zlab-4090；GPU1 UUID GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d。无物理设备、无安装、无他人进程操作。所有任务已退出，GPU会话释放，无自动后继。
- 核心仍为固定成熟 A、原 TieredPSFWitness、同QP/地图/goal/初态/半径/动作/速度界/终端/Deadline；**执行适配层已变化，不能称原成熟A完全未改**。新合同FAS_SOFTWARE_ACCEPTANCE_DEADLINE_DEV_V1，AcceptancePlant SHA256 044017f2fb814996e03e3127894b8f5bf7799c21c5973e77b04cf910ee94e773；两臂同用。源版本与新差异在SOURCE_LOCK、DEV_DIFF及原生身份文件。旧D不与新R混作单因素对照。
- 70锁定外部来源文件及三保护HEAD/工作树状态前后一致，父包130工件再次全量复验；原代码、默认开关、旧54次失败提交均未改。

### 原缺口与修复的准确范围

1. 原active_cycle.run_cycle在第454行start原epoch；第859行采样FINAL_COMMIT_GUARD。之后仍有仲裁/事务身份构造/Plant身份检查/纯canonical状态计算。原Plant自身没有真正接受前的时效复查。原事务先Plant，再Token prepare/activate或consume，再trace；Token/trace失败保留已提交。
2. 新适配层保留原校验与同canonical数值图，先准备候选后状态和收据，再在单写锁内以真实monotonic采样作软件接受决策。导航elapsed<.8-.2；后备采用上轮实验的<.8接受口径；合法Terminal ANY保持。过期返回committed=False、post_state=None、executed_action_identity=None；原事务Token UNCHANGED，协调器结束该臂，不替换动作或重放。
3. **原Supervisor某些EXPIRED分支仍可选择有效保留Backup**，不能说源码原本一律800ms禁止；新增接受门把上轮实验实际提交判据前移，可能收紧原仲裁动作集合。因此同时重跑D/R，明确新执行合同。
4. 已接受后证据/Token/trace异常不得写成未提交；未知状态保守停止、保留已知收据、不自动重放。CPU场景验证重复拒绝、计算跨时限、异常、原观察器接线与零同步I/O；模拟回调不证明真实掉电或跨重启exactly-once。
5. 软件接受的线性化采样不是硬实时保证：采样后OS可能抢占，返回/Token/trace可晚于deadline。原transition入口检查仍保留，prospective计算结束后才采样接受。不能宣称物理动作、外部可见写入或磁盘在截止前原子完成。
6. 旧R c53 54次提交后超限事实不改；本轮相同前54次数值链逐位一致，但c53接受584.903655ms，未复现旧超限。运行耗时差异不能单归修复，拒绝分支由CPU故障场景验证，不能说本轮原生已观察到过期拒绝。

### 新同版本结果（实际独立D→R）

|指标|D 直接目标|R 冻结绕行|
|---|---:|---:|
|尝试/提交|500/500|500/500|
|软件到达|H500未到达|H500未到达|
|H260 Progress|0.08541265693212023|0.3090334777268925|
|H500 Progress|0.08541368574505083|0.30879213483073725|
|末60步ΔProgress|0|-2.722503600338655e-8|
|首次near-stall窗口|c176–235|c247–306|
|Primary / OPEN|500 / 500|500 / 500|
|PSF支撑实际提交|82|58|
|执行段共享Oracle SAFE|500|500|
|最小记录proxy净空q|5.712748631037788e-8|0.011952441862670596|
|接受耗时max ms|450.297815|584.903655|
|最小接受余量ms|149.702185|15.096345|
|entry→Plant返回p50/p95/max ms|276.538 / 456.837 / 685.810|311.324 / 461.525 / 3167.102|

- 共同H260 R−D=0.22362082079477225，即**+22.362082个百分点**；不能叫到达成功。仅Trial61已知开发任务、固定顺序、无重复样本，不作泛化/显著性或纯性能加速结论。
- D新旧500次、R新旧共同54次动作/状态binary32字节无差异，旧时效失败仍保留。这里只是数值复核，不是新的独立任务。
- 全入口耗时不扣除epoch前开销：R c288 entry→Plant返回3167.102351ms，其中entry→epoch2699.780459ms，epoch→Plant返回467.321892ms。前段包含意图持久化与调度，不能全归fsync；600ms内接受不等于入口600ms完成，更非20Hz。

### 新查明的R末段参考固定点（封存后仅只读算术）

- R末段不同于D：D末60步名义动作范数中位数.141937477、执行约1.096e-13；R名义动作本身仅2.351062399e-8、执行约1.710e-8，不能一概归因“QP压住强PD”。
- path_reference.py:7只在距当前段终点<=.005q时更新段号；第8行截断投影；第10–13行前视.02q可以沿下一段越过拐点。这组规则可产生固定点：越过旧顶点而没进入其.005q切段球时，段号仍旧，前视点却位于下一段.02q处；到该点后PD为零，索引不前进。
- 本轮R自c115进入零基段2，至c499仍在段2；原始投影参数1.250300719>1，截断投影固定旧顶点；距旧顶点.020000046208q>.005q，距返回target仅5.92890872056e-8q。独立按下一段方向构造的.02q固定点与记录target相同；不是新运行跟踪器。
- 这支持末段“参考不再要求推进”的具体机制；不能排除此前QP/动力学历史影响，也不证明修切段即可到达。CPU无QP跟踪曾通过，与该事实不冲突：参考规则对过滤后的轨迹未充分验证。不能据此称FAS/Gaussian独有困难或安全约束错误。
- 单位纠正：会话更新一度口误“5毫米(q)”后立即纠正为**0.005q，非米制**；文档与数据始终使用q。

### 资源、失败记录与封存

- CPU首轮16/16，1测试进程，脚本墙钟0.233633412s（真实单调钟，模拟老化epoch/回调，不是GPU时效证明）；未重规划/CPU路线跟踪或重跑旧结果。
- 原生1会话/2Factory/1000尝试与提交/1140求解/10384几何，817.103455949s；D357.667650s，R在原600s单臂内；总1800s、2000求解/50000几何上限未触及，重试0。1000状态/身份/接受点核验及2000审计记录哈希通过。
- 保留只读定位缺失cycle_coordinator.py（正确路径active_cycle.py）、查询使用未配置python别名、运行前修正result字段名等工程记录。主封存已成功，但外层PowerShell/SSH返回码转义使bash exit收到非数字；工具exit1不等于封存失败。随后只读复验通过，未重复finalize或实验。
- 主包：`/disk1/zlab/tmp/fas_trial61_acceptance_deadline_repair_v1/run_20261111T033642Z/`；100工件，清单SHA **efae2699ddd4dc473e76d7cc5c9c23ee93109c7b7a992b13cc401e02a0fdbd7c**。入口FINAL_REPORT.md、results/SCORECARD.json、INDEPENDENT_CROSSCHECK.json、SOURCE_LINE_INDEX.json、HISTORICAL_NUMERIC_COMPARISON.json、RESOURCE_TOTAL.json、native_pair/raw/D|R/results。
- 独立只读补充包：`/disk1/zlab/tmp/fas_trial61_acceptance_deadline_repair_v1/postseal_readonly_20261111T0355Z/`；清单SHA **1970580acdcecf1e9682c955362d80d716154f42d05870b215979f9ed6e1f9e2**。入口READONLY_SUPPLEMENT_CN.md、REFERENCE_FIXED_POINT_EVIDENCE.json、FULL_COST_WORST_CYCLES.json、CLOSURE_WRAPPER_STATUS.json。补充不改主封印，0新增QP/几何/实验。
- 当前支持域、独立物理配准误差仍未知；SAFE/净空仅共享Gaussian代理。软件到达判据仍.01q、速度<=.005q/模型秒、连续10提交，非1e-12严格Terminal。

**下一步 NOT_STARTED：** 优先修复/验证成熟路径跟踪器的单调路径进度与拐点更新合同，用已冻结R拐点附近状态检查不锁死、不跳过路径段，并保持所有路线/几何/安全门；先有限CPU验证，再另行明确新原生验证范围。不要继续加长500周期、换种子/路线或调整CBF来掩盖参考固定点。本文更新不授权下一轮运行。

---

## 上一阶段及更早交接原文（历史状态；不作为当前授权）

> **当前结论（2026-11-11）：PARTIAL_NATIVE_DIAGNOSTIC_STOPPED。** Trial61 绕障路径与CPU跟踪通过；原生D完成500提交但停滞，R在第54次已提交动作的真实transition入口超原时限约87微秒后停止。没有完整H260配对，不宣称导航改善；全部任务已退出、无自动后继。下文新增阶段为当前状态，旧失败原文保留。

## 当前阶段：Trial61 绕障参考端到端诊断（2026-11-11）

- 当前目标：在固定成熟 A、安全合同与最终 goal 下检验直接参考 D 与绕障参考 R；只评价现有 Gaussian 代理模型，不将搜索盒或无观测区域称为已确认自由空间。用户本轮明确批准了独立 DEV 实现、有限搜索、CPU 跟踪及原生软件对照；这是新范围，不追溯恢复或改判旧 Trial17/53 A0 域门阻断。
- 最后更新：2026-11-11，Asia/Shanghai；更新者：Codex，本 safer-splat 会话。正式交接分支 master；本次仅更新 HANDOFF.md。修改前命名检查点 HANDOFF_BEFORE_TRIAL61_DETOUR_20261111，旧 blob 025ade90ffb6c676b6dd64565cca8483cb4b411d 已保存在新包 inputs/HANDOFF_BEFORE_20261111.md 与 HANDOFF_CHECKPOINT.json。
- 实际环境：zlab-Super-Server / zlab，原 zlab-4090 SSH；实验和测试均在服务器。GPU1 UUID GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d，资源门通过后仅一次会话；未干预他人进程或物理硬件。
- 成熟版本：FAS_MATURE_NATIVE_PSF_RECOVERY_DEV_V1，experiment_arm=A，optional_guard_effectively_enabled=False，原 TieredPSFWitness。沿用封存 Trial23 run_20261106T095437Z 的原生 worker/cycle audit；仅独立 DEV 参考适配和接线改变。固定 task goal、地图/顺序、.015q 半径、dt=.05、动作/速度盒、1e-12 终端、.8s guard/.2s reserve；真实单调钟，不扣除观察器时间。精确版本、源码/地图 SHA 见 SOURCE_LOCK.json 与 native_pair/DEV_DIFF.patch。
- 保护 Candidate 33e34a3ac8d710452775ffe688af77393f734fa9、Frozen 481c3e5e24648d0219e1969f1145648ac99f6943、Perf b0a6bbb96512cef5085feada98a900bf9d8ff15f：三个 HEAD/工作树状态及 81 个保护/外部来源文件前后一致。未修改保护源码、默认开关或旧数据；算法代码没有 commit/push。

### 实际结果与完整分母

|阶段|实际完成|结论边界|
|---|---|---|
|规划接口|确认 OMPL 2.0.1 C++ 采样绕过 Python override、无可用 setStateSamplerAllocator；改用标准有限 Lazy PRM 的最小独立实现|不是官方 OMPL 实现，也不是原创算法；旧失效计数记录保留|
|路线搜索/复验|seed61 PCG64；512样本、6候选；前4顶点UNSAFE、第5完整边UNSAFE、第6接受；10边、长度0.8928280999884618q；新逐边完整复验均SAFE|194 CPU FULL、24 motion checks、65.646672s；没有平滑、换seed或第二采样阶段；不证明观测域/现实安全|
|CPU动力学跟踪|.02q前视/.005q航点切换；429接受步/429段SAFE；Progress 0.9971049685647213；动作与速度盒通过|133.363934s；软件到达 .01q位置/.005速度/连续10周期，非严格Terminal；CPU/GPU不保证逐位等价|
|原生 D|500尝试/500提交；500 Primary/OPEN/Oracle SAFE；418原制动见证、82 PSF见证；H260 Progress .08541265693212023，H500 .08541368574505083|未软件到达；末60步ΔProgress=0，首次near-stall c176–235；582求解/4808几何|
|原生 R|54尝试/54提交；54 Primary/OPEN/Oracle SAFE；54原制动见证、0 PSF；观察终点Progress .06083424396895853|c53实际transition时效超限，已提交后停止；到达为删失，H260不可得，少于60步不能判near-stall；54求解/736几何|

- 本轮不是成功的完整 D/R 对照：R 提前停止，不能比较共同 H260、完整到达率或宣称绕行参考提高 FAS 导航。D 的 H260 与旧记录一致只是复现证据，不增加独立任务。
- D 末速度 2.3507155918288796e-7 q/模型秒，最小记录代理净空 5.712748631037788e-8q；R 终点速度 .043173160520995124，最小记录代理净空 .014371726022039467q。两者样本长度不同，不据此排名安全性。
- entry→Plant返回 ms：D p50/p95/p99/max=276.7874815/453.37884665/489.86475978/631.559337；R=382.5067135/434.61344995/551.18453449/656.293216。入口成本含 epoch 前意图落盘，不能直接以全入口时延代替原授权判据；不是20Hz/WCET证明。

### 实质阻断：R c53 的实际接受时效

- 最终 guard=599.018170964ms，原判 OPEN；Plant入口=599.668920971ms；transition入口=600.087358849ms，超过原600ms资格界约0.087358849ms。guard→transition间隔1.069187885ms。
- 第54次真实软件提交已经发生，随后审计发现异常并停止；不得改为未提交、补签或扣时。该动作原制动L3通过，QP solve 2.47262ms，执行闭段Oracle SAFE；不是已证几何碰撞或PSF拒绝。
- 结果层面为 D 500 次实际transition及时、R 53次及时+1次超限。原 source guard 的54次OPEN与实际transition时刻是不同证据，不以旧摘要的timely计数代替。
- c53 L3_DISCOVERY_ADMISSION约338.432ms，c52约127.907ms；现有分段计时不能把全部差值归因到单一模块。关键间隔包含原调用、检查、调度及内存观察；没有无观察器对照，不能断言是fsync或观察器唯一原因。
- 原事务 COMPLETE、Token APPLIED、trace RECORDED；最终 trace FINALIZED，54条；commit-in-doubt=false，未验证执行段0。SCORECARD 的 trace_finalized 字段来自 arm_execution_evidence_complete=false，不能误读为最终trace未封存，应以 trace_finalization_record.status=FINALIZED 为准。
- 安全时效异常后没有重试、放宽reserve/deadline或继续剩余周期。任务已退出，无自动后继。

### 工程失败、资源和封印

- 保留旧OMPL采样计数失败包 run_20261111T024648Z（manifest 018013f9182633e22a9a863d35f57ca1c6814cb277d532a8c99713be205eed1f）。
- CPU首次跟踪被包级import隔离门阻止，0步/0FULL、1.838679s；改为精确 canonical 源文件加载，新 tracking_attempt2 成功，未修改门。原生准备先后有外部AlexNet SHA索引 KeyError、空目录 FileExistsError/派生 prepare import失败；均发生在GPU/Factory前，保留首次日志及修复版本。
- 候选6中间记录状态遗留CHECKING，已披露，不改历史行；最终PLAN_RESULT、冻结路径和10条新完整证书/独立复核构成接受依据。
- CPU接线8/8通过，1.213898391s；不是额外GPU资格或物理安全证明。独立算术/身份核对554原生状态链、429CPU步及10路线边；不新增QP/几何来补历史。
- 实际累计：原生1会话/2Factory/554尝试与提交/636求解/5544几何API调用，432.763193s；CPU规划194 FULL + 跟踪429 FULL。跨阶段6167几何API计数仅记账，不混同数值域。均在本轮预注册有限预算内；参数和上限见 PREREGISTRATION.json。
- 权威新包：`/disk1/zlab/tmp/fas_trial61_detour_reference_pipeline_v2/run_20261111T025448Z/`。130工件，2026-11-11T03:15:46Z封存；清单复验通过，manifest SHA256 **a995b2f151d66fe9ac25d44c26580454ac15b973f3f2d9a8af71666fe6c12241**。SEAL_RECEIPT.json为清单外回执，封存后不改。
- 阅读入口：FINAL_REPORT.md、results/SCORECARD.json、PER_CYCLE.csv、ACTUAL_TIME_VIOLATIONS.json、INDEPENDENT_CROSSCHECK.json、RESOURCE_TOTAL.json、CANDIDATE_PATH.json、PATH_REVALIDATION.json、native_pair/GPU_SESSION_RESULT.json、PROTECTED_AFTER.json。失败日志、原始receipt/trace/时钟在对应子目录。
- **下一步 NOT_STARTED**：优先审查最终guard至真实接受点的时效覆盖缺口，提出保持原合同的接受点验证方案；需要改核心或再运行时另取明确授权。暂不继续换规划参数、找赢家或重跑R。当前仅可确认代理地图中已有一条全边检查通过且CPU动态可跟踪的路线；完整成熟A执行及参考收益仍未闭合，地图支持域与独立物理误差界仍未知。

---

## 2026-11-07及以前交接原文（历史状态，不作为本轮授权或当前运行状态）

> **先读结论：** 2026-11-07 04:03（Asia/Shanghai）复核：4090原SSH连接成功；独立绕障预算提案12成员与A0执行包15成员清单再次通过。A0已执行核查并因有效域门停止，累计至封存341.287345s，FULL/QP/GPU均0；A1–A3未启动，B/C未授权。早于该A0包的独立绕障累计消耗仍UNKNOWN；2336历史CPU FULL不是绕障消耗。  最新完成Stonehenge观测支持材料的严格只读清点：精确checkpoint/配置/变换与保留ZIP一致；已找到501帧RGBA及关联位姿，但未取得绑定当前地图的真实深度、有效性mask、尺度标定与观测支持域证据。当前域仍UNESTABLISHED，原 **STOPPED_AT_A0_REQUIRED_DOMAIN_GATE** 保留，A1–A3未启动、B/C未授权。本次新增实验/FULL/QP/GPU均0，无新审计工件。用户选择先补观测支持，再研究规划→跟踪→FAS；后续仅方案，不自动续跑。

- 正式维护位置：**https://github.com/kenqiana04/safer-splat/blob/master/HANDOFF.md**；本机文件只是工作副本，阶段更新须同步到 GitHub。
- 最后更新：**2026-11-07 04:03，Asia/Shanghai**（Git 提交记录提供精确发布时间）。
- 更新者：**Codex，本 safer-splat 会话**。
- 本次文档变更：按用户“更新下交接”刷新当前裁决、预算/执行分账、下一步与任务表，消除旧“待确认”段落被误读为当前状态的问题。仅更新HANDOFF；Stonehenge清点沿用已记录证据，本轮未重新清点图像/模型；没有新增实验、预算授权或服务器工件。
- 最近实测阶段：CPU准入`run_20261106T111343Z`，5/6请求实际完成、7FULL，39件封印。最近原生仍是Trial23 `run_20261106T095437Z`的917真实提交；未重跑旧12场景或旧D/L。
- 状态依据：本会话4090服务器实际记录、独立只读复算和封印核验。**今后项目实验、测试及计算默认在4090服务器执行；Windows仅作连接客户端和获授权的文档/Git维护。设备选择和实验资源仍须遵守当轮授权，不是无限GPU授权。**

### Stonehenge观测支持证据只读清点：相机/RGBA存在，有效域仍未建立

- **2026-11-07 / Codex / 本Safer-Splat窗口**：用户选择继续“补齐观测支持范围→规划→跟踪→FAS安全链”的研究路线。随后授权的是一次严格只读清点，不恢复已停止A0–A3、不复用旧预算、不切换为proxy-model-only研究。清点期间原SSH成功，读取、目录清点、归档对照和轻量元数据解析完成；没有文件写入、新审计工件、GitHub更新、规划/训练/渲染/实验/FULL/QP/GPU。**本次另据用户“更新下交接”的明确请求，仅维护HANDOFF。**
- 当前裁决：**OBSERVATION_EVIDENCE_INVENTORIED_DOMAIN_STILL_UNESTABLISHED**。路径仍NOT_EVALUATED，A0域门阻断保留；A1–A3未启动，B/C未授权；Trial17直线FAIL、Trial53直线NOT_RUN及Trial23历史结果不改。此次清点不是导航、安全或新实验PASS。
- 以下来源使用已有数据包相对路径与内容摘要，不新增公开服务器私密绝对路径。检索覆盖已知Stonehenge数据/输出目录、三个保留ZIP的Stonehenge成员，以及相关数据/资产/源码目录的有限深度名称清点；不是全服务器缺失证明。

|材料|实际核验|仍未建立的内容|
|---|---|---|
|精确模型|数据包内 `outputs/stonehenge/splatfacto/2024-09-11_100724/nerfstudio_models/step-000029999.ckpt`；当前磁盘SHA与既有锁定值及原ZIP成员完全一致|未加载模型；文件身份不是几何真实性证明|
|训练配置|同目录 `config.yml` 已按文本读取，未反序列化Python对象YAML；Stonehenge、InstantNGP parser、scene_scale=.3333、fraction=.9；与原ZIP一致|没有原训练环境版本及实际消费帧清单|
|坐标变换|同目录 `dataparser_transforms.json` 为单位旋转、零平移，另列scale=.3333；与原ZIP一致|未确认原坐标的米制含义或独立标定|
|相机位姿|数据包 `data/stonehenge/transforms{,_train,_val,_test}.json` 均解析；train199、val151、test151；501个分组位姿均为有限4×4、齐次底行正确，旋转正交误差约8.3e−8以内|基本结构检查不是位姿精度或图像—地图重投影验证|
|内参|显式水平视场角0.6911112070083618；当前parser结合800×800图像推得fx=fy≈1111.111031px、cx=cy=400，畸变使用缺省0|缺独立标定；默认零畸变不是测量证据|
|图像|数据目录507文件：4 JSON、2辅助Python、501 PNG；所有位姿路径可按parser的.png补全规则解析到文件，头信息均800×800/8-bit/RGBA；各分组render0共3张抽查SHA与原ZIP一致|未全量解码/检查视觉内容；真实采集或合成来源尚未核实；文件名render不足以确定来源|
|真实深度、有效性mask|上述数据目录及ZIP Stonehenge成员中未发现对应文件；所有帧仅有transform_matrix/file_path，未见depth/mask路径字段|RGBA alpha语义未验证，不能充当深度有效性mask；不能据此宣称全服务器没有深度|
|独立场景几何、真实尺度、观测支持域|所查材料未找到绑定当前精确地图的可用证据；无可直接采用的独立mesh/尺度标定/支持域证明|相机视锥、相机或Gaussian bbox、Near/Far及模型渲染深度均不能替代真实已观测自由空间|

**精确来源摘要（当前读取与原ZIP逐字节对照通过）：**

- checkpoint：`ac14f5ced354c93f26cf92404540712eff65bd02554d9e9ed0332508e290382d`。
- config.yml：`cd6ea45ad01553f0ce1531ad08cfaf8359e95041b39c77291d94e75f2d2f2f8e`。
- dataparser_transforms.json：`92a1af2f195be3b32e0422418aff40cbd426c1cf9d8f7d5da87629519f5a0f8e`。
- transforms.json与transforms_train.json字节相同：`b983423062d5bd075438ef06887d01be05fe1fe10a49eedc4fbbd8a031517805`。
- transforms_val.json：`dfe3c08e2e2c3f315317ae5474cd50bce255aa132a56e1b197fab8ed649701d7`。
- transforms_test.json：`fddda8ec77976602c5c442da887d4a4b0232b56391cf6767b58598c4a9fe3a69`。
- ZIP对照是现有磁盘文件与保留归档成员的一致性证据，不是独立官方签名、原训练输入manifest或完整训练过程证明。已有逻辑map identity仍为 `c9eade9ca89b741768a0ca33b3a755b2656402864f121aefdceaed4b0174f7c8`；不将其与checkpoint文件SHA混为一谈。

**坐标、数据接线及划分的核验限制：**

- 当前安装metadata为Nerfstudio **1.1.5**。只读检查 `nerfstudio/data/dataparsers/instant_ngp_dataparser.py`、`data/datamanagers/full_images_datamanager.py`、`data/utils/dataparsers_utils.py`及冻结项目 `splat/gsplat_utils.py`、`ns_utils/nerfstudio_utils.py`，未导入/执行这些运行时模块。
- 配置内部parser保留默认 `data/ours/posterv2`，但当前FullImageDatamanager源码会用外层 `data/stonehenge` 覆盖。该源码解释了配置路径如何对应现有数据；不能仅凭同一场景名称证明2024年训练过程。
- 当前parser读取 `transforms.json` 并按.9 fraction，从199帧推得180训练/19评估；不会直接把val/test目录各151帧当成训练配置实际采用的评估划分。此为当前源码静态推导，**原训练版本、实际划分及消费帧仍未验证**。
- 当前parser将相机平移乘.3333、旋转不变；保存变换为单位刚体变换。现有Gaussian loader直接使用模型坐标。这能解释原相机坐标到训练/地图q坐标的缩放关系，但原坐标单位、相机轴约定与地图配准准确度尚须验证；q不是已确认的米。不能据scale把.015q转换成真实机器人米制半径。
- 元数据Near=1.5/Far=3.5没有独立距离/自由空间含义；当前parser相关路径未把它们作为真实深度证据。相机位姿、RGB及视锥不能独自确定第一可见表面前的可靠空闲区和遮挡后UNKNOWN。

**下一步补证与研究方案（仅建议，未授权执行）：**

1. 补来源链：原训练版本、实际帧清单、采集或合成生成说明、尺度依据；绑定精确checkpoint、相机与RGB身份。
2. 补独立几何：若原场景为合成，寻找原场景几何、生成相机及单位约定；若为真实采集，取得配准传感器深度、有效性mask、内外参及尺度证据。任何新采集、生成或重建工作另定范围与预算；不将被评价Gaussian的渲染深度当独立真值。
3. 验证坐标、重投影、深度定义与误差界；随后以有效观测和保守误差明确FREE/OCCUPIED/UNKNOWN，遮挡后、无效深度、域外保持UNKNOWN。支持域绑定地图/坐标/证据版本；只凭包围盒不得准入。
4. 研究顺序为“支持域→完整路径边验证→跟踪参考→原FAS认证/Deadline/Token/提交链→软件执行与独立评价”。路径需同时满足域与几何条件；跟踪只改变名义参考、最终task goal不变；分别报告路线、可跟踪性、资格链及到达结果，不能把静态PASS升级为动态成功。阶段资源/停止条件须另行明确，不恢复已关闭A0–A3、不默认扩预算。

**当前论文claim边界：**

- 可支持：原有固定Gaussian表示下的软件实验及其原限定范围；Trial23参考收益的案例性证据；直线参考适用性和观测域缺口的分析。
- 不可支持：观测自由空间已建立、通用绕障导航成功、真实物理无碰撞保证或跨场景泛化。新的完整导航claim须有域/几何/跟踪/资格链证据及独立评价。
- 清点任务已结束，无新后台任务；此次清点及本次文档更新未重新检查服务器全局进程，当前全局作业/资源状态UNKNOWN。**没有为只读清点新建封印包或审计工件**；细节证据保留在本会话工具输出和现有源文件，后续不得编造新包位置。

### 已授权A0–A3实际执行：A0有效域门阻断，后续未启动

- **2026-11-06 23:45 Asia/Shanghai**：用户经本窗口交接明确确认仅A0–A3，锁定交接commit `5a1e8e899e1b5971a83c0bce0f6daba41b5d4534`及预算清单 `4720ddd1834a5138166a5fdcdcb253c945e7db7814e344dfe78f27fcd06ddf5d`；总2640s/4096FULL/0QP/0GPU，B/C未授权。原预算提案原件不改，新AUTHORIZATION另存。
- 本窗口原 `ssh zlab4090` 实际成功，主机 `zlab-Super-Server` / UID1000；预算12成员复验通过，未发现重复绕障worker。另一发送端报告的SSH Permission denied原样视为其环境观察，不据此宣称服务器离线；本窗口未换主机/账号/通道/权限配置，也未重试本窗口被拒绝操作。
- **实际裁决：STOPPED_AT_A0_REQUIRED_DOMAIN_GATE**。A0已核查但未通过；A1/A2/A3均NOT_STARTED，B/C NOT_AUTHORIZED。当前17/53 `inputs/FROZEN_CONTRACT.json` 的 `navigation_domain.status=UNRESOLVED`、`bounds=null`、`observed_free_space=null`；原地图合同同样拒绝路线准入。地图资产目录仅config.yml、dataparser_transforms.json、checkpoint；metadata交叉检查未找到绑定本Stonehenge地图的已建立观测支持域。其他ETH3D/TUM/Replica合同不能转用；训练scale/Gaussian bbox不等于观测自由空间。
- 97保护来源及三个HEAD/clean状态一致；17/53准入父包39、选样方案6成员复验通过，原6D初态/最终goal、map/Profile、q单位、.015q/reserve0身份另存锁定。因域门失败，没有伪称完整PRM/跟踪合同已合格。
- A0核查至封存**保守计时341.287345s / 600s**，计时锚点采用服务器15:39:20 UTC，早于首个成功预检时间15:39:28 UTC 8秒，含连接预检、编排和落盘；非CPU性能基准。封存于15:45:01 UTC。15件工件封存前123186B，未触2GiB工件上限；未启动实验worker，合成测试0、采样0、候选边0、FULL0、QP0、GPU0、Factory0、PlantCommit0、旧实验重跑0、进程信号0。后续GitHub交接维护与实验阶段计时分列，不将文件核查冒充实验。
- **路径状态NOT_EVALUATED**：未进入搜索，不能标为预算内未找到路线，更不能声称无路或规划器失败。历史独立绕障消耗仍UNKNOWN，剩余旧直线额度没有使用。本次没有变更为proxy-model-only研究。
- 服务器新包：`/disk1/zlab/tmp/fas_detour_a0_a3_execution_v1/run_20261106T154105Z/`。15成员清单SHA `da0cb62afb43a40b00b29dd4c82140e44abae9588301cdf3079f241901bc65fd`，清单外SEAL_RECEIPT记录通过与墙钟。入口 `FINAL_REPORT.json`、`PHASE_LEDGER.jsonl`、`MAP_DOMAIN_GATE_EVIDENCE.json`、`DOMAIN_METADATA_CROSSCHECK.json`、`INPUT_IDENTITY_LOCK.json`、`STOP_REASON_AND_NEXT_OPTIONS.json`。
- 下一步仅有两类条件选择，均未执行：提供/另行批准建立与map/frame绑定的观测支持域证据（有限域、可复现来源、域外与不确定UNKNOWN）；或者用户另行明确确认仅共享Gaussian代理模型的范围变更，并审阅修订的域/规划合同及明确剩余或新预算，不能自动重置预算。当前任务已按停止条件结束，无自动后继。

### 绕障预算核查与分阶段新提案（历史提案；A阶段后获批并在A0停止）

以下“未授权/等待确认”仅描述2026-11-06 23:32时点；当前以文首及A0执行记录为准。旧提案原件未改，B/C仍未获批，停止后的A阶段不自动续用或重置额度。

- **2026-11-06 23:32 Asia/Shanghai**：按用户“先检查已有交接、任务目录和账本；找不到则提出预算；不要重复实验”的新要求完成服务器资料核查与方案准备。本轮新测试/FULL/求解/GPU/Factory/PlantCommit均0。
- 扩展检索tmp、maintenance_records、v3_repair/execution/diagnostic_records及主项目目录，深度≤5、限定文档/JSON/JSONL元数据；枚举23180路径、命中39相关文档，并追读9个相关包的收据与账本。检索范围和限制落盘，不声称全服务器不存在其他记录。**未找到Trial17/53独立绕障授权或执行账本，既往绕障累计消耗UNKNOWN，不能写0。** 本次直接消费96个封存来源成员与其manifest摘要全部匹配，读取前后内容一致。
- 可核实的相关主线CPU历史FULL小计 **2336**：旧路线预诊断16（13.232599s，首条直线UNKNOWN、规划搜索0）；四任务地图准入65；Trial23无QP跟踪413；Trial23同源QP诊断1835（含资格检查，实际QP920）；17/53直线准入7（4.529989s）。这些属于不同已结束阶段，不是绕障预算或全项目计算总额。
- 另核对旧原生失败包D88：1会话/1Factory/88提交/92solve/1022 geometry、140.217446s；后续成功包D500/L417：1会话/2Factory/917提交/979solve/11075 geometry、702.492992s。两次原生运行应分别保留，共1005历史提交，不能把88次旧失败遗漏，也不能将native geometry API计数与CPU FULL混合。
- 更早其他任务9/12/26/31/66/73/74/79已有CPU参考/MPPI实验：隔离参考1358 FULL另加UNIT 1；MPPI场与rollout共404 FULL；匹配PD/MPPI 624 FULL、373 QP、320软件步。均不属于Trial17/53绕障，已消费，不重跑、不转余额。旧路线文档的12Factory/3120提交/45min仅是未授权、未执行的未来建议。
- **新提案，未授权未启动**：固定17/53、seed0，不换样。A0合同/有效域600s、0FULL；A1仅新增接口测试≤16项/120s、0FULL/0QP；A2有界CPU PRM及完整闭边验证共1800s/4096FULL，每任务900s/2048FULL，≤128采样点/512唯一候选边，选定路径≤8边，单边≤64FULL/90s；A3证书/账本审计120s、0新几何。**建议首先只确认A0–A3：合计2640s（44min）、4096FULL、0QP、0GPU。**
- 进入A2前须冻结有依据的有限有效域、UNKNOWN策略和参考/跟踪合同；缺观测域不能默认拿bbox当自由空间。如只能做代理模型域，先明确收缩主张并再次交用户确认。已完成的端点/失败直连证据只按精确身份复用，不重复跑；规划中UNSAFE/UNKNOWN边排除，预算/身份/数值/账本异常停止。首任务无合格路径则第二任务NOT_RUN；无路结果只能为预算内未找到，不能证明无路。
- **B须路线结果审阅后另行确认**：CPU同源QP直接D/路线R，17-D→17-R→53-R→53-D；资格120s+每臂≤500步/600s，共2520s（42min）、≤2032QP（含32资格）、≤8000FULL（64资格+每臂1984）。失败待推进段不接受；不重规划、不补齐提前停止轨迹。软件Goal仍.01q/.005q每模型秒/连续10步，与严格Terminal分开。
- **C须完整原生准入后另行确认**：GPU1最多1会话/4Factory、每臂≤500周期/600s；总2700s（45min）、2400s后不入新周期、尝试/提交≤2000、solve≤4000、native geometry API≤100000。其他进程占用即不启动；无排队/kill/改设备。该数值是新提案，绝非恢复已关闭四臂授权。
- 所有阶段串行CPU单线程、单worker RSS≤4GiB、工件≤2GiB（接口临时≤16MiB），自动重试0，剩余额度不跨阶段转移；启动、加载、失败和落盘计入墙钟。不可中断调用若超时必须记录实际超限，不能伪称硬时限内完成；无法约束调用/终止则不启动。安全门、源参数、最终goal、物理操作禁令不变。
- 证据与完整机器可读提案：`/disk1/zlab/tmp/fas_detour_budget_reconciliation_plan_v1/run_20261106T152856Z/`，入口 `FINAL_AUDIT_SUMMARY.json`、`HISTORICAL_ACCOUNTING.json`、`SUPPLEMENTAL_EVIDENCE.json`、`PROPOSED_PHASED_BUDGET.json`；12成员清单SHA `4720ddd1834a5138166a5fdcdcb253c945e7db7814e344dfe78f27fcd06ddf5d`。本轮核查/提案已完成，等待用户确认A阶段，无自动后继。

### 本窗口接续核对：绕障预算待核实，未启动新计算

- **2026-11-06 23:22 Asia/Shanghai，BUZHIDAO / Safer-Splat-1 / Safer-Splat 窗口**：收到用户继续绕障实验的交接，正常复用 `ssh zlab4090`，实际主机 `zlab-Super-Server`、UID1000；连接成功，没有权限拒绝。当前用户要求所有实验在服务器执行、保留安全门、不得干预其他进程或实物设备；预算不能核实时停在相关操作前。
- 本次状态为 **BLOCKED_BUDGET_UNVERIFIED_FOR_DETOUR_EXECUTION**，仅完成现状核对与接续合同准备，**绕障实验未完成**。最新直线准入包39、Trial23原生包102、地图准入包50、原规划包6成员共197件全部逐项摘要通过；准入SOURCE_LOCK中的97来源文件与三个保护HEAD/clean状态一致。原Trial23 D500/L417、Trial17直线FAIL、Trial53直线NOT_RUN及四原生臂NOT_STARTED保持原归属。
- 在服务器项目、三个保护工作树及 `/disk1/zlab/tmp` 深度≤3的近期合同/授权/预算/报告/计划文件检查范围内，未找到后续绕障包或独立绕障预算。**这仅是所查范围未发现，绕障后续状态仍UNVERIFIED，不推断全局从未开始。** 所查服务器目录未发现相关AGENTS/SKILL；`/home/zlab/.agents`为空；已读取GitHub AGENTS与HANDOFF。
- 原 `AUTHORIZATION.json` 的132FULL/300s和条件四臂GPU额度属于首非PASS即停的已关闭直线计划，不能作为绕障剩余额度继续消费。地图合同还要求先定义导航支持有效域；当前该条件仍未解决。已在本窗口请求提供绕障预算或记录位置，不重问SSH授权。
- 被动进程快照未发现匹配本任务的运行worker；GPU1 UUID `GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d` 有其他进程PID3317124占4370MiB。仅为检查时快照，未操作该进程、未排队或持续轮询。新增测试/FULL/求解/GPU会话/Factory/PlantCommit均0；哈希审计不计作实验。
- 服务器新包：`/disk1/zlab/tmp/fas_detour_continuation_readonly_audit_v1/run_20261106T152244Z/`；6成员清单SHA `a2411ba0b84ee03467b806e72d8b7b009ecf4ca227c6335498cc8716126e30e9`，清单外SEAL_RECEIPT避免自指。包含 `AUDIT_SUMMARY.json`、`MANIFEST_VERIFICATION.json`、`PROTECTED_VERIFICATION.json`、进程/GPU快照和 `NEXT_STEP_CONTRACT.md`。未覆盖旧封印包或保护源码。
- 下一步：核实独立绕障预算与有限导航有效域，事前冻结任务、规划/跟踪规则、完整闭边验证、FULL/墙钟/候选/重试上限和UNKNOWN处理，再于新DEV推进CPU参考与几何验证；路径通过后才讨论同数值域软件对照。原生GPU须满足其独立预算、资源和完整资格门。上述计算均NOT_STARTED，无自动后继。

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

当前绕障状态：**STOPPED_AT_A0_REQUIRED_DOMAIN_GATE / OBSERVATION_EVIDENCE_INVENTORIED_DOMAIN_STILL_UNESTABLISHED**。独立A0–A3预算已获批，但A0因缺少绑定当前地图的有效观测域而停止；A1–A3未启动，B/C未授权。2026-11-07只读复验预算12成员、执行15成员均通过；A0封存消耗341.287345s、FULL/QP/GPU均0，早前独立绕障消耗仍UNKNOWN。此前直线准入的 **COMPLETED_BOUNDED_ADMISSION_WITH_NEGATIVE_RESULT / APPLICABILITY_LIMIT_STATIC_LINE_REJECTED** 是历史阶段：17直线FAIL、53直线及四GPU臂未启动，不能继承其预算。最新实际原生状态仍是**COMPLETED_BOUNDED_PAIR_WITH_LIMITS**，Trial23 D500/L417，不是本轮新增提交。CPU观察器收尾已补齐，但其证据不等于原生权限；原生资格来自此前新授权与实际链路。以下为保留的较早CPU参考结论，不与新GPU数据混成四组：

`PASS_SAME_SOURCE_CPU_QP_REFERENCE_DIAGNOSIS_WITH_LIMITS`

`REFERENCE_TRACKING_GAIN_SURVIVES_SOURCE_QP_IN_THIS_CPU_CASE`；仅Trial23已知开发任务、固定参数。16项准入检查、两组916个接受模型步、15600项独立复算与968文件封印。新CPU QP920次（含准入4次），FULL1835次（含准入3次）；另1次注入求解失败测试不计真实求解。PSF/Factory/Supervisor/Token/PlantCommit/GPU/A*均0。最终task goal始终不变。

### 推荐下一步——尚未执行

**A0任务已依有效域停止条件结束。本次仅更新交接，未恢复实验。用户已选择先补观测支持证据，再研究规划→跟踪→FAS；下一步是审阅并另定补证任务的范围、分阶段预算及停止条件，NOT_STARTED。** 当前没有获批的新补证/规划预算；不因原A阶段尚有未用额度而自动续跑。代理模型研究仍需明确范围变更与预算确认。 不换17、不补查53、不重复Trial23求好结果，不重跑旧CPU两组，不自动接A*或继续局部LP/PSF筛选。现有证据不足以把直线追踪当作一般导航参考，任何问题定义变化都不能冒称本轮既定复验。

- task goal继续在snapshot；tracking target旁路绑定state/candidate/action，不能擅改Token、半径、Deadline或安全门。
- 参考收益已穿过成熟A，但仅单个已知开发Trial23，D→L固定顺序；无跨地图泛化、无严格实时或物理安全证据。
- 原CPU与新GPU数值域不同，不能直接计算FAS单因素增益；.10q诊断域也不是自由空间/安全管证明。
- 新GPU、Factory或导航任务均须另行授权和现场资源门；默认4090服务器执行不等于持续占用或无限授权。

## 2. 使用版本、分支与工作区状态

### 本次文档维护客户端与远端基点

- 2026-11-07本窗口客户端为Windows Safer-Splat-1；本地master尚无提交，已有未跟踪error.log保持不动。命名元数据检查点`handoff-before-budget-status-refresh-20261107T0403`记录本地状态及原文件摘要；不是未跟踪数据备份。
- GitHub默认分支发布前基点`7c3e616c6459fffaca99289241dbfe5941558b76`，HANDOFF blob `746e2d8ea08616c13327f3b2630560b4e973aa77`。通过GitHub文件API按原blob校验仅更新HANDOFF；不切换本地分支，不改服务器工作树。发布提交号以文件历史为准。
- 本轮原SSH别名`zlab4090`连接至`zlab-Super-Server`成功。没有重新核查三个保护工作树完整状态或GPU/全局进程，不将下述历史快照当作当前状态。

### 较早维护窗口的本机仓库（历史快照，非本次客户端）

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
|Trial17/53绕障A0–A3|A0已核查但未通过，任务停止；A1–A3未启动|封存341.287345s；FULL/QP/GPU0；不自动续用旧额度|
|绕障B/C|NOT_AUTHORIZED_NOT_STARTED|须前置证据与新的明确决定，原直线预算不转入|
|观测支持补证|已完成材料只读清点，有效域仍未建立；后续补证NOT_STARTED|先审阅新范围、预算和停止条件；无后台后继|
|Trial23阶段0/A无QP两组CPU跟踪|已结束并封印|保留旧43工件，不重跑|
|本轮同源QP两参考CPU对照|已结束并封印|两个子进程正常退出，无后台后继任务|
|完整四组参考×FAS对照|跨数值域，不能作严格四组因果比较|前两组CPU已实跑，固定成熟A的D/L已在GPU软件仿真完成；CPU/GPU非逐位等价|
|成熟A相同参考对照|本次D500/L417完成并封印，旧D88失败独立保留|102件；无运行中任务、无自动后继|
|A/G H260 的 `R03_G`、`R04_G`、`R04_A`|历史待办，不在运行或排队|旧续跑曾资源阻断，不自动恢复；先确认用户是否仍要继续此支线|
|服务器其他用户/项目作业|本次未检查GPU/全局进程，当前UNKNOWN|旧原生封存快照仅是历史；SSH可连接不代表GPU空闲|

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

- 2026-11-13：实际Stonehenge任务级规划适配完成，Trial61/17开发＋53已见复用检验，10条CPU模型记录全部软件到达、1943段代理检查覆盖；单次曲率分量反馈主要时间全更慢，53省努力取舍保留，停止此具体构造。保留成熟G/S基线；259工件封印`f1288353…`，路径`fas_task_level_planning_v1/run_20261113T111100Z`，无生产FAS/GPU/自动后继。

- **2026-11-13｜时间—努力结构分解与成熟解结案**：两开发＋四已见复用、201尝试/149轨迹、三努力预算和细化完成。晚切换低努力主要来自更长时间，不是更短路；同路径成熟分配显著快于global。裁决A，采用成熟解并关闭本局部增量；保留事后路径、事件对齐、连续充分准入失败、3旧正超额和高增益敏感性。67工件清单`9ee91914…`，仅HANDOFF发布，无GPU/生产调用或自动后继。

- **2026-11-13｜成熟控制结构与效率检验**：公式级C-CLF-CBF复现、公共兼容域一次修订、2开发/4冻结和3细化完成。最短时间被简单合法交接覆盖；时间—努力前沿仍有取舍，采用成熟名义控制、不新增切换估计器。91完整执行全部到达，144累计轨迹/尝试；旧失败、v1缺链和P2初始FAIL保留。仅HANDOFF发布，服务器独立包`fas_mature_control_efficiency_v1/run_20261113T091600Z`，不启动后继。

- **2026-11-13｜二阶兼容交接验证完成，裁决B。** 2开发＋8冻结，103执行到达＋1未准入；最早/短预测覆盖充分预测，速度影响合法域但未产生新增性能信息，未开发估计器。保留输入不准入、依赖检查失败及全部历史；54文件清单`78af45bd…`。仅CPU，已退出，无自动后继；报告和两张方法表见当前阶段索引。

- **2026-11-13 / Codex / 兼容交接原型**：服务器CPU完成62轨迹及42冻结对照；v1慢方向估计失败后唯一v2修订完成，最佳简单规则对比1胜1负4平。任务强控制全部更快但努力更高；后验闭式驻点＋两候选还原覆盖当前二维模型。66短入口/119408更新、CPU6.602s；287工件ac3305a8…封印。裁决NARROW，不升级当前估计器为已证新方法；仅HANDOFF发布、无GPU或生产调用、无后继。

- **2026-11-13 / Codex / 增量方法设计**：两张兼容路径执行卡＋一张鲁棒信息收益备选；推荐仅做时间代价交接的有限原型，NOT_STARTED。解析例子T=3.100308/2.995732/2.864920，能量有代价；简单积极名义控制T=0.677359构成强反例。已承认原文减速处理及成熟切换优化，先验证便宜强方法是否吸收。三文档服务器封印15912079…；新实验/求解/GPU0；旧A继续关闭，不开发误差包络，不自动扩展。
- **2026-11-13 / Codex / 共有假设独立审查**：P01–P15及6篇直接先例；保留原Excel五表、增六表/120多维项/20差异。H1/H3 NEED_EVIDENCE、H2/H4 ADAPT_ONLY，无新算法立项；H3仅优先取证真实plant年龄与后备窗口。SUPER主文已补、勘误存在但正文和补充理论未核实；safe-dual核至2026 v2。27工件045e7abe…服务器封存，文档校验非科学实验；新GPU/求解/FULL/导航0，A保持关闭，后继未启动。
- **2026-11-13 / Codex / 候选A结构与成本审查结案**：关闭当前拒绝证书＋逆像的独立创新主张；98原制动终端FAIL后同首控PSF PASS保留。243次原分支几何＝196次共享前缀＋47次分支独有；5.148575s/0.944806s仅历史计时包络，不是实测加速。终端早检查/同段复用仅NOT_STARTED工程备选；不启动证明、修复、实验或Gaussian误差开发，不扩B。仅文档发布，旧封印与失败不变；完成交接即结束，新的非等效机制或明确部署需求才可重新讨论授权。
- **2026-11-12 / Codex / 候选A机制可行性审查**：NARROW；固定模式必要约束逆像可跨查询，4例服务器算术与模式反例；原Gaussian数值误差界/总成本优势未立。98原尾终端FAIL→PSF PASS禁止泛化删除首控；Safety Certificates已含碰撞区域。398历史工件/70保护源/三HEAD复验，21件91a74686…封存；新GPU/求解/FULL/执行0，仅更新HANDOFF，无后继。

- **2026-11-11 / Codex / 冻结六路线原生复验完成**：GPU1空闲后1会话6Factory，61/17/53×PRM/RRT六臂均软件到达（559/649/504/597/453/643提交），3405代理SAFE、6次WARNING合法Backup、98 PSF提交、0接受违规/重试/近停滞。3317.446s、3503求解/46579几何，134来源/三HEAD不变；224工件4036f8d9…封存。显存列映射勘误独立8工件79857e76…，原包不改；257实际P0正残差及53-RRT两条raw64正值完整披露。仅HANDOFF发布，无后继，非物理安全/普适优势。

- 2026-11-11：成熟参考对照V1完成61/17/53×PRM/RRT六组CPU规划（2055 FULL、184最终闭段复验），历史60次issued32正QP残差审计完成；GPU1资源冲突导致原生六臂全部NOT_RUN，0 Factory/提交，无排队重试。166工件封印97774c6a52f925b37198575047163be0a952d93858a2a8a2e7cb8e617a472ede。

- **2026-11-11 / Codex / Trial61冻结R最终到达**：从初态完整重跑一次，700步/900秒单臂预算下557提交软件到达；c522–525曾合格4步后速度超限重置，最终c547–556连续10步。前500动作/状态与父R逐位一致；557代理SAFE、19 PSF、0近停滞/接受违规/未决/重试。532.499s、576求解/7471几何；70来源/三HEAD不变，85工件b1dfea8d…封存。仅HANDOFF发布，任务退出，无自动后继；非严格Terminal或物理安全/泛化证明。

- **2026-11-11 / Codex / Trial61已接受运动进度修复**：34/34服务器CPU回归；新D/R各500提交、1000代理SAFE、0接受违规/未决/重试。R越过旧段2固定点至段9，H260 .537202159、H500 .959759183，末距.0315562q且仍运动，未软件到达；D保持.085413686且近停滞。1会话992.914579s、1082求解/11556几何，70来源/三HEAD不变，109工件7f1e1ccf…封存。仅HANDOFF发布，不续跑；有限参考修复不是规划创新或现实安全证明。

- **2026-11-11 / Codex / Trial61接受点修复及新D/R**：新DEV AcceptancePlant在prospective计算与全部检查后执行原时限接受门，16/16 CPU故障场景通过；新D/R各500真实提交、1000Oracle SAFE、0接受违规。H260 .085412657/.309033478，两臂均未到达；R末段被只读定位为段2/前视目标固定点。主100工件efae2699…，只读补充1970580a…；70保护来源/三HEAD及父130工件不变，1GPU会话817.103s、1140求解/10384几何，无重试/后继。外层shell返回码错误与旧超时失败保留，仅发布HANDOFF。

- **2026-11-11 / Codex / Trial61代理绕障端到端诊断**：修复不可靠OMPL计数接口，采用有限Lazy PRM，512样本/6候选得到10边全段SAFE路径；CPU跟踪429步软件到达。原生D500未到达、R54在实际transition超600ms约87微秒后停止，不重试；1会话/2Factory/554提交/636求解/5544原生几何，CPU623FULL。81保护来源及3HEAD不变，130工件封印a995b2f1…，无后继。仅发布HANDOFF，完整对照未完成，不改变任何旧裁决。

- **2026-11-07 04:03 / Codex / 交接与绕障账本状态复核**：原SSH成功；复读独立预算、授权、A0账本/最终报告/封存回执，预算12及执行15成员清单全部通过。A0最终至封存341.287345s（FINAL_REPORT封存前值341.284620s，两者时点不同），FULL/QP/GPU/测试/规划均0；A1–A3未启动、B/C未授权、早前独立绕障累计仍UNKNOWN。保留2336历史主线CPU FULL单列，不挪用直线额度。刷新正文裁决/下一步/任务表并标明旧待确认段落为历史；不重跑实验、不改预算与封印，无新服务器工件、无新后台任务；全局资源未检查。仅发布HANDOFF。

- **2026-11-07 00:08 / Codex / Stonehenge只读观测材料清点后按请求更新交接**：确认501帧RGBA和关联位姿、四JSON及精确checkpoint/配置/变换的归档一致性；当前parser可推导180/19划分和.3333坐标缩放，但原训练消费帧、真实尺度、深度/mask/观测支持域仍未建立。保留A0阻断及17 FAIL/53 NOT_RUN，新增实验0、无新审计包。用户选择先补观测支持再研究规划→跟踪→FAS，仅方案，未恢复旧预算。公开更新仅HANDOFF，不新增私密绝对路径。

- **2026-11-06 23:45 / Codex / 获批A0–A3后有效域门停止**：原SSH成功、预算封印核验；97保护文件/三HEAD及45输入父包成员一致。当前观测域仍UNRESOLVED，A0未通过，A1–A3未启动；未改代理研究范围。A0至封存保守341.287345s、FULL/QP/GPU/测试均0；15件包da0cb62a…，无后继，B/C仍未授权。

- **2026-11-06 23:32 / Codex / 绕障历史预算核查与新提案**：扩展检索与96消费成员核验，未找到17/53独立绕障授权/账本，累计绕障消耗UNKNOWN。列清主线CPU2336FULL、旧D88和新917原生提交及其他任务MPPI消耗，不转旧余额。提交待确认A阶段44min/4096FULL/0GPU方案，B42min与C45min各另议；12件新包4720ddd1…；新增实验0。

- **2026-11-06 23:22 / Codex / Safer-Splat窗口接续审计**：SSH成功；197历史成员、97保护文件和三HEAD复验一致。所查范围未发现后续绕障预算，绕障状态仍UNVERIFIED；原直线计划已关闭，不能回收余额。保存6件只读核对包a2411ba0…与下一步合同；新实验全部0，等待预算位置及导航域门解决，未干预GPU1其他作业。仅更新HANDOFF。

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
