# task7 第二轮复核与八项证据核查

- 用户授权：任务A只读复核今日框架并追加交流文档建议；任务B核查八项原始依据、追加SOURCES及建议替换表。禁止代码、安装、训练、评估；不改参考仓库、forem/src、forem/config、task7三文档和DECISIONS。未委派。
- 负责人：Codex；开始：2026-10-19T23:40:47+08:00；状态：A done；B review（核查文档交付，未核事项保留）。
- 推荐：Codex GPT6.1sol / medium，Claude Sonnet5.5 / medium；跨文档因果与原文核查需中等强度。实际模型：未知；实际推理强度：未知（当前会话未提供可独立核实的运行配置）。推荐不等于实际。
- 准备处理：本日志、PROGRESS、SOURCES、agent_logs/task7/20261019-claude-codex-sync.md。共享文件每次写前重读并比较内容，SOURCES从实时最大编号顺延。
- 已读：根AGENTS、forem/AGENTS、doc/README、PROGRESS、ENV、task5.5最终sim评估日志。Git main，工作区已有大量暂存/未暂存/未跟踪变更，全部保留，不暂存不提交。宿主进程可见多Claude会话。
- 并发边界：task5.5日志确认评估使用forem-dev；本次不对该容器执行docker exec，不使用GPU。UR参数优先宿主文件与官方源，必要时只通过宿主docker cp流式读取容器文件（不在容器执行命令）。

## 执行记录

- 开工计划（当时尚未执行）：设计逐项复核、八项证据核查与最终交接。

### 中间核查（2026-10-19 23:46:16 +0800）

- 已完成任务A指定文件与SRC-0358–0381（按用户允许跳过0379/0380技术内容）的阅读；上轮七条已基本写回，仍有后续决定与旧句并存、接口未闭合问题，待写交流文档。
- 已读Christodoulou arXiv:1910.07207v2 §2–3式(4)、(10)–(12)、算法1；SAC-AE arXiv:1910.01741 §4.4–4.5/附录B.2；DrQ arXiv:2004.13649v4附录B.2。
- R2D2 OpenReview原PDF遭验证页/HTTP403（网页工具及宿主urllib均失败）；已核Google DeepMind Acme官方R2D2源码，继续核Google Research SEED RL的显式stop_gradient路径。不冒称已读R2D2论文。
- 宿主只读docker inspect确认forem-dev镜像sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430，容器ID 2456c37db9c9f1f73eb8e651bc83068118441369ddc34a738ff38b0232793314。通过docker cp <容器文件> -在宿主内存解tar读取ur_description，不执行容器内命令。版本1.5.0，apt 1.5.0-1focal.20250520.012707；已核UR5默认参数及关节限位。
- 证据项6已核tasks→simulator_api.sample_circle_goal→eeplanner._calc_6Dplan/_generate_fwd_orientations：终点随机RPY，前向选项只改中段yaw，最后恢复原目标。证据项7已核Python乘dt及C++GMM乘dt分支，常量为m/s，局部变量常实际为单步位移。
- CWP arXiv:2203.02764v1原PDF已通过urllib在内存读取（15835443 bytes，SHA256 40577f1c2079f2d6369b610ca0553bd51564fc2bbbf090a32e2c09f8b61ef639）；pdftotext -layout - -返回0，核PDF页5–6、12。网页工具因大小失败，不等于未取得原文。VLN-3DFF原PDF已核§3.2/§4.1，进一步对照PMLR正式版。
- Robotiq官方20210623手册同样通过urllib内存读取（17017334 bytes），pdftotext返回0，§5.2.3 PDF页127为含耦合件TCP 174 mm；不是CBL本地基座系距离。未把官方TCP或外形最大高度当本地TCP。
- 所有本轮shell/Python均限文本读取、网络取原文、归档解包、静态数值推导与文档写入；未导入/运行项目代码，未评估或使用GPU。一个rg命令曾引用不存在的gmm.cpp而返回2，已更正为gaussian_mixture_model.cpp；错误路径不是证据。

### 最终写入与验证

- 本轮实际改动仅四份：`forem/doc/PROGRESS.md`、本日志、`forem/doc/SOURCES.md`（仅新增SRC-0382–0391，后续细化本轮自己的SRC-0386）、`forem/doc/agent_logs/task7/20261019-claude-codex-sync.md`（保留原文前缀，末尾追加第二轮节）。未暂存、未提交、未推送。
- 任务A交付：17项问题，含文件/行号、严重程度与建议；前8项是实现前应澄清的接口合同，后9项涉及表述、来源与G3对照解释。不是17个已发生的代码故障，也不是对方案有效性的实验结论。上轮7条修订已核，当前仍存在后续决定未同步的旧句。
- 任务B交付：八项建议替换表；离散SAC公式SRC-0382；编码器梯度SRC-0383；官方循环回放/预热SRC-0384；UR5实际包/限位/DH SRC-0385；TCP几何与限制SRC-0386；终点姿态与采样SRC-0387；速度单位SRC-0388；VLN-3DFF/CWP原文SRC-0389/0390；本轮静态审查依据SRC-0391。
- TCP补核为只读网格顶点与标准数学推导：二进制STL解析2436三角面，原始x最大0.0444999560713768 m；结合xacro的mimic链，近张开配置的指尖网格轴向最远面约0.1489789957 m，约距CBL虚拟点1.02 mm；θ=0.804 rad时约0.1628589259 m。输入、公式、单位、条件与SHA256均在SRC-0386。这是静态几何证据，未运行模型/接触仿真，不把碰撞网格前缘当抓取TCP或实体标定。
- 原始论文取得限制：OpenReview网页工具和urllib均被验证页/403阻挡；改用Google Research官方SEED RL固定commit af9f769f4c01c602828f1fa806848031dcb52807的compute_loss:354–384，明确预热前缀、stop_gradient和后缀loss。R2D2论文全文仍未核，已如实登记。DrQ固定commit 6d00d0d2e06269ce61de5d1a12d3c74454d44149已核。未执行任何模型代码。
- 网络/文本读取：PDF有的超过网页工具大小限制，改为urllib在宿主内存读取并用`pdftotext -layout - -`提取，返回0；没有落盘到参考仓库。PMLR正式VLN-3DFF路径经标题核对为wang25i，前期猜测的wang25a是无关文章、未采用为证据。一次GitHub请求SSL EOF后顺序重试成功；没有安装依赖。
- 写共享文件方式：每次先重读；SOURCES原最大381，从382开始；持排他咨询锁后比较预期SHA256、再确认内容未变才写入，并读回核对。咨询锁不假定其他Agent配合，因此仍作内容前后比较；本轮未观察到并发写入冲突。
- 文档静态验证命令已返回0：六份受保护审查文件SHA256与读取快照一致；旧SOURCES前缀SHA256仍为387edbb56f01bd787164075417b83b4840d076fb9991fe9ae5ec4dd5f9788855；旧交流文档前缀仍为47d08de281e0a8bb45f873a8c69b06fa137554cd916ce43868c9ca4f25a174f4；10个新来源锚点各出现一次；17项问题、8行替换表、63个本轮本地文件/来源链接存在，无控制字符。TCP补充后在结束前重核同样项目。未运行项目测试或评估。
- 受保护审查快照（完整SHA256）：
  - task7/TASK.md：6b911cf02101e0c15a1b0992e0845f2708f58250eb62541c37649ca16c69ca14
  - task7/task7.4/RESULTS.md：23454698c942216483da309a504233ded88100d98d584888423c98cb6dce7b81
  - task7/task7.5/RESULTS.md：4e5aa62d66f7b2df7957739d134ce299e01419a3b8aa23468912e9afbb304b1e
  - task7/task7.7/RESULTS.md：2bd20aeb4a314d8cbb63cb37f619038226bc8d2681a570f66a1f25be627c6f73
  - task7/task7.8/RESULTS.md：c33eb583fc957a07f9199e5d1256350174e3b9a32461b206483cb4fbeed5ec58
  - DECISIONS.md：294c209ece5eb3769026c0cfe99b61d2b3ecc047a6354f9daff5425eef310403
  - 其余源码身份沿task7.5(A)及本轮各SRC的哈希，没有将根HEAD冒称迁移源码版本。

## 交接

- 目标与授权：仅完成本轮A的设计复核建议、B的八项原始依据核查与替换建议，不实施、不直接修订task7三文档/DECISIONS。负责人Codex；建议由Claude读取交流文档后统一修订，尚未向其他会话发送消息或代派任务。
- 已完成：A复核与17项建议、B八项逐项核查记录/替换文字、SRC-0382–0391、文档完整性验证。A状态done；B状态review（核查交付已完成，以下未核事项保留，不冒称八项全部证明）。
- 证据路径：[第二轮复核](20261019-claude-codex-sync.md#codex第二轮复核2026-10-19)、[SOURCES](../../SOURCES.md#src-0382)、本日志；原代码/安装包/论文精确位置、版本及哈希见各SRC。没有新训练/评估产物。
- 未解决问题：①物理TCP唯一接触点/开合姿态未定义，0.15 m与物理接触TCP等价未证明，已有近张开网格前缘的有限推导；②R2D2原论文全文未取得，技术做法由官方代码支持；③既有SRC记录的用户原话没有在本轮重新取得完整聊天核验；④任务A列出的合同/数值问题仍待Claude/用户在原事项中处理，不能把本轮建议当已授权的新决定。
- 风险：源代码事实不证明新环境已实现、GPU有效、解析IK已数值等价、对照已实际公平或世界模型有效；所有运行类任务依然未执行。保留task5.5评估状态与原会话控制权，未监控/干预其过程，也未进入容器。
- 下一步：Claude按第二轮节处理已定/待定混杂与接口缺口、按八项表替换引用；涉及未定终止/原地同步执行时长、物理TCP定义的选择须回到原E/B/I事项确认。R2D2原论文后续可读时再补论文级证据；不据本交接启动实现、计时、训练或评估。

- 交接时间：2026-10-19T23:54:56+08:00。
