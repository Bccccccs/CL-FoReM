# P1-AUDIT-028-CODE 缓存/数据独立代码审查

- Agent：Codex /root/cache_review
- 开始：2026-09-28T10:48:03+08:00
- 状态：active
- 范围：代码/证据审查，必要有限回归；不改算法、不启动长期训练、不动其他进程。
- 主包HEAD：2a1348a；有P1未提交改动及新cache/test/resource文件，全部保留。
- 主Agent已读当前README/PROGRESS/DECISIONS，开工补读阶段、ENV和交付日志。

## 进度与证据

待记录。

## 长任务

无。

- 2026-09-28 开工复核：已读取AGENTS、README、PROGRESS、D33/D34、ENV、P1_MEMORY_PLAN/P1_WORLD_MODEL与P1-FIX交接；读取requesting-code-review技能作为被派发独立审查员。主包未提交文件与交接吻合，未修改实现。静态审查已覆盖cache.py全文、data.py/encoder.py全文、CNN定义和现有streaming测试；缓存按NPY块/owned batch、统计按观测计数、数据t偏移机制与描述一致。最初查看了错误历史子路径scripts/modulation/wm/cache.py，命令退出1，随后使用实际scripts/wm/cache.py，未造成修改。
- 待验证：用独立合成episode和现有容器做极小CPU参考，检查k=1/5、目标切换/截断/尾帧、跨块LRU与FP64统计、源/缓存损坏。候选风险：编码身份没有直接记录torchvision版本，而CNN调用torchvision.transforms.Resize。尚未将此候选认定成实测特征错配。

## 独立有限验证（2026-09-28 10:51 +08）

命令：

```bash
sg docker -c 'docker exec mmhusky-node01 /usr/local/bin/mm-entrypoint python3 -u /root/mm_husky_ws/doc/agent_logs/20260928-p1-acceptance-cache-probe.py' > doc/agent_logs/20260928-p1-acceptance-cache-probe.log 2>&1
```

退出0，约2秒。实际node01已有容器（ENV入口），CPU合成数据，不加载真实轨迹全集、不训练、不改容器/ROS。源码仍为HEAD2a1348a加未提交P1改动。独立脚本和输出与本日志同目录，临时合成NPZ/NPY由TemporaryDirectory销毁，原结果全部未触碰。

独立参考不调用已有测试fixture：4个回合共18帧，含完整、缺末帧截断、单步和零转移；k=1/5、subgoal排除开关两态、batch3尾批均逐行比较原episode切片，action/dt/h全部精确相等。每块2帧强制跨块；均值/总体标准差对独立dense FP64参考rtol1e-6通过。3个额外reader同进程切换后LRU<=4且owned batch不变；改动一个NPY字节后正式缓存checksum拒绝；关闭后全局pool空。未发现D33时间偏移回归或目标泄漏。

## 审查结论与边界

- 本轮负责范围未发现需要阻断当前node01工程验收的Critical/Important缺陷；没有实现修改建议或内联bug条目。共享训练/预测/资源代码由协调Agent另审，本记录不替代其结论。
- 缓存身份包含源manifest/分片记录、split、encoder SHA、WM及CNN源码、FP32维度/格式、数值后端和编码batch。完整块损坏及不完整正式目录fail-closed，partial不复用；这是最终D34已说明的行为，不将其误写成自动坏块修复/断点续建。
- 有界性质针对实际生产链路：保留O(N)轻量metadata/action/window/permutation索引，地图按单episode（256MiB上限），特征读取按块/当前batch。不是数学意义上任意数据规模O(1)内存；参考API直接EpisodeDataset(episodes)、encode_numpy、gather仍允许调用者显式物化数据，不是正式train/evaluate调用路径。未做超出9600规模或并发线程/worker验证。
- 迁移残余风险（非本环境错算实证、非阻断项）：`scripts/wm/encoder.py:35–43`数值身份未记录torchvision版本，实际CNN `scripts/modulation/models/mapencoder.py:65`调用torchvision.transforms.Resize。后续更换该依赖/预处理实现时应固定配置或补版本身份并做特征参考；本轮未变更环境、未实测跨版本差异，不把潜在差异包装成现存结果错误。
- 没有启动长任务、没有停止他人进程、没有更改算法或共享文档；仅新增本审查脚本/输出并更新本独立日志。研究P1出口/P2仍由当前阶段证据决定，审查通过不等于预测收益。

状态：done（仅独立缓存/数据审查交付）。协调Agent可引用上述范围、命令和实测；不需要从聊天恢复证据。
