# P1-AUDIT-028 P1修复交付独立验收

- Agent：Codex /root
- 开始：2026-09-28T10:48:03+08:00
- 状态：done（工程交付审查）
- 范围：代码/证据审查，必要有限回归；不改算法、不启动长期训练、不动其他进程。
- 主包HEAD：2a1348a；有P1未提交改动及新cache/test/resource文件，全部保留。
- 主Agent已读当前README/PROGRESS/DECISIONS，开工补读阶段、ENV和交付日志。

## 进度与证据

待记录。

## 长任务

无。

## 开工及当前验证

- 已读AGENTS、ENV、P1_MEMORY_PLAN、P1_WORLD_MODEL及实施日志D34。当前主包未提交改动为data/cache/encoder/train/evaluate/val_probe/resource/test；没有改SAC/环境语义文件。
- 使用requesting-code-review技能委派缓存/数据独立审查（P1-AUDIT-028-CODE），已先登记表与日志；主Agent检查训练/评测及资源证据。
- 实际命令：`sg docker -c 'docker exec mmhusky-node01 /usr/local/bin/mm-entrypoint python3 -m pytest /root/mm_husky_ws/src/modulation_rl/scripts/tests -q'`，退出0，65 passed/351继承warnings/16.98s；输出20260928-p1-acceptance-tests.log。没有安装依赖、运行环境rollout或研究训练。
- 逐文件SHA与source-version-r2及三规模summary的代码身份一致。重新计算各原始resources.jsonl的RSS/USS峰值、任务swap峰值，并检查两模型各1epoch/8batch曲线、train/val无test，全部一致。证据20260928-p1-acceptance-evidence.json。
- 已核查下一轮protocol-1000确实train0–999、val9600–9899、无test，SHA与交接一致；布局隔离仍未完成，不能将其作为新最终测试。
- NVIDIA查询当前无compute进程后启动一次有限验证集重评（已有100-r2的8batch模型，全300val，输出新目录results/p1-audit-20260928/prediction-val）。该命令复用0.399GiB既有缓存，不重建9600数据、不使用test、不训练；完整命令见工具调用，输出20260928-p1-acceptance-prediction.log；结果待返回。

## 最终审查结论（2026-09-28T10:52:15+08:00）

**当前P1-FIX-028工程修复及有限资源交付可验收，未发现阻断项；不代表P1研究出口。**

1. 当前源码10个交付文件与最终r2冻结指纹一致，关键生产链路已消除全量地图/全量窗口device物化。WindowSource按episode+t取窗、batch训练验证、episode预测聚合及模型hidden/normalizer加载与目标一致。
2. root独立复跑全套65测试通过；cache_review独立合成4episode/18帧探针通过，覆盖k1/5、目标切换、截断、零转移、跨块/尾batch、统计、共享LRU和损坏拒绝。审查范围及非阻断风险见20260928-p1-acceptance-cache.md。
3. root新目录重跑真实300回合val，一步79593/五步78393窗口，退出0。全部horizons字典（含逐episode误差、各模型均值与paired CI）与check-100-r2旧报告精确相同；证据prediction.log与results/p1-audit-20260928/prediction-val/report.json。未使用test或进行模型更新。
4. 100/1000/9600资源产物已逐项核查源码、原始监控及curve；9600 RSS2.2496GiB、USS2.2171GiB、cgroup11.1539GiB，task swap0。这是先前三级实测的独立证据复核，本轮未重建9600缓存。各模型仅8batch训练，随后完整train诊断/val覆盖；不能视作完整epoch/长期200epoch训练通过。
5. 下一轮协议确为train0–999/val9600–9899、无test，SHA47b63b591355ab21702b1cd5fda694b5ee8ae309a2ba392b3b401aace3f82a18；启动脚本仍是待执行的研究重训入口。本轮没有运行它。

## 非阻断限制及下一步

- 可以进入已冻结1000回合train/val重训诊断；先登记新任务、核对资源与输出目录，依据新结果决定下一步。P1研究可信出口/未曝光最终测试仍未达成，P2继续blocked。
- 缓存数值身份未显式含torchvision版本；固定本次镜像/依赖下未观察错误，未来迁移或升级该预处理依赖时应补身份/固定配置并重新做特征参考，不能直接承诺缓存跨环境可复用。
- 有界内存以当前9600规模/无worker配置成立，仍有O(N)轻量索引；没有宣称任意规模常数内存。无精确resume CLI；损坏或partial缓存拒绝而非自动续建，均已在交接说明。
- 本轮不改任何实现、原结果、checkpoint、数据或环境配置，不提交/推送、不启动长期训练。短测试与验证均退出，无后台作业。

## 可接手证据

- 20260928-p1-acceptance-tests.log：本轮65测试。
- 20260928-p1-acceptance-evidence.json：原始资源/源码/协议核对及新验证比较。
- 20260928-p1-acceptance-prediction.log：本轮真实val重评。
- 20260928-p1-acceptance-cache.md及probe.py/log：独立审查与合成CPU探针。
