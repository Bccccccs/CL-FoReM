# task7.3：IK失败分类与可借鉴方法调研

- 开始：2026-10-19 10:04 +0800；状态done（晚间父抽查、来源补登与文档静态验收完成）；原负责人Codex子Agent `ik_research`，当前父Codex完成收尾。
- 范围：CBL/N²M²本地IK语义；求解、不可达、奇异、碰撞与连续性；核查有依据的改善方法。
- 边界：仅调研，不改代码、配置、参考仓库与共享文档；只更新所属三文档及本日志。
- 推荐Codex GPT6.1sol / Claude Sonnet5.5 medium；实际配置未核实时记未知。
- 来源条目编号预留：SRC-0351–SRC-0355；登记文本供父Agent统一写SOURCES。

## 执行与来源登记文本

原日志停留在“尚未执行”，没有所称登记正文。旧报告已存在不能代替日志证据；本轮按报告线索重新核查，不伪造原始执行记录。

## 2026-10-19晚 父Codex补全

- 本次实际模型/强度：未知/未知；推荐GPT6.1sol medium / Sonnet5.5 medium（跨IK/坐标/代码核对）。没有运行IK、安装或计时。
- 本地实际抽查：H/F `robot_env.cpp:190–239、411–470、479–515、676–708`、F `robotenv.py:287–302`、BioIK插件`:638–653`、`robot_env.h:203–231`，`validity_fun.cpp:11–30`；`sha256sum`确认H/F robot_env一致（`6fab7246…`），U不同（`a8f7ebb4…`）。源码/配置的commit和未跟踪状态详见task7.5 A.1，不把根HEAD当源码commit。
- 外部实际抽查：ROS-Industrial固定`06d8b9…`解析FK/IK、插件限位/seed排序/回调；Buss/Kim作者稿§2 DLS/SVD；TRACLabs官方概述及HIRO维护分支固定`2e63d6…`README的Speed/Distance行为；Reachability Priors v3的IRM与局限；cuRobo论文§6.2.4/Fig.17/20/附录E.3及legacy v0.7.8批量接口（tag Git对象`d64c4b…`）。
- 工具：`nl/sed/rg/diff/sha256sum/git show/rev-parse/status`；web打开原文/官方文档，`git ls-remote`固定远端引用，`curl -fsSL`只读固定raw。主读取成功退出0，diff差异退出1；ROS生成文档、Buss survey、TRAC作者页有访问失败，分别换官方源码、作者论文稿、官方项目文档，未冒充取到2015 TRAC论文全文。
- 结论：解析多解＋连续分支仍是优先研究建议；旧默认BioIK不等于DLS/解析解，允许近似/软限速需分开验证。碰撞回调实际含已存在world几何（至少地面），随机障碍同步缺口另见SRC-0367；旧失败回退不满足task7整检查点语义。
- 已登记[SRC-0351](../../../SOURCES.md#src-0351)–[SRC-0355](../../../SOURCES.md#src-0355)，每条标实际阅读范围；RESULTS补正H/F行号并追加父抽查与新框架适用性。

## 交接

- 完成：关键本地代码与解析分支父抽查、5条来源、方法限制/版本界限、新框架失败合同对应。证据：[RESULTS](../../../tasks/task7/task7.3/RESULTS.md)、台账、[task7.5 A.1](../../../tasks/task7/task7.5/RESULTS.md#a1-版本与证据约定)、[本次收尾日志](../20261019-codex-research-closeout.md)。
- 未解决：TRAC-IK原论文全文未取得（不影响由官方文档支撑的有限算法描述）；新UR5模型一致性、连续碰撞表示、端到端时延与Blackwell兼容未验证。下一步：task7.5(B)使用适用结论，task7.6计时仍需运行授权。
- 无运行任务/求解器产物；未新增奖励、先验网络、数值阈值或碰撞模型。
