# FLOW-028 项目方向与流程讲解

- Agent：Codex /root
- 开始：2026-09-28T14:43:24.390877+08:00
- 状态：done（文档讲解核查）
- 范围：读取研究目标、系统流程、机制、P0–P5及最新P1报告；仅修改本日志和进度行。
- 已读：AGENTS.md、README、PROGRESS、DECISIONS、RESEARCH_GOAL、SYSTEM_PIPELINE、WM_RESEARCH_DESIGN。
- 长任务：无；不启动容器或训练。

## 进度

- 已发现研究目标文档与D35/D36存在更新时差；讲解以最新进度和决策区分历史、实测与计划。用户本轮提供AGENTS仍写IROS，投稿目标冲突如实注明，不擅自变更研究范围。

## 结论与交接

- 方向：现有Husky/N²M²/SAC中引入前瞻特征修正；最终动作仍由SAC产生。原SAC已有观测反馈。
- 现有执行：目标/EE参考→状态及地图→SAC三维动作→EE推进及底盘速度→BioIK→analytical或Gazebo执行→真实后继观测。
- 拟议P2：编码→SAC预览（不执行）→WM预测→预测变化量→学习特征修正→SAC最终动作→执行一次→新观测重新前瞻。最小版固定WM，修正器与actor head需训练。
- 阶段：P0 analytical已验收；D34索引/有界内存工程修复已验收；D36单seed、1000train/300val一步与五步优于copy和no_action，但独立test/跨seed未验收，P2及后续保持未放行；Gazebo仍review。
- 预测改善以D36报告为准：一步相对copy/no_action为34.07%/3.61%，五步20.86%/3.98%，不是控制成功率改善。
- 下一步（尚未执行）：固定配置跨训练seed验证，冻结未曝光且布局隔离的独立测试，再决定P1出口；本轮未启动实验。

## 改动与验证

- 修改仅doc/PROGRESS.md自己的FLOW-028行及本日志。
- 实际命令：cat读取AGENTS、索引、进度、决策、研究目标/流程/机制、P1/P2/P3/P4、最新重训报告；git status --short；git -C src/modulation_rl rev-parse HEAD，均退出0。
- 主包HEAD：2a1348a87b3b5c45f495fafacad526f7eaee7749；本轮未改源码，未运行容器/算法测试。根仓库既有.gitignore/AGENTS/ENV改动及doc/docker未跟踪内容保留。
- 已核查文档中的历史状态与D34/D36时间差；不把本轮阅读称为复现实验。投稿目标存在AGENTS/IROS与D35/CCF-A或B不一致，本轮不改选会决策。
