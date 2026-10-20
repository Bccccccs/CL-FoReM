# TASK7-FRAMEWORK-DOCS-20261019：写入10-19讨论定下的task7框架并建立准备子任务

- Agent：Claude（claude-opus-5-5，推理强度未知）
- 状态：done（文档交付）；开始2026-10-19 19:03 +0800，完成约19:35。
- 用户要求（原话）：“所以我们要准备，sim，世界模型的训练，前瞻网络的改造，VCM的确定，等等工作，你都开始写文档吧，我同意你的BC，写好文档喊我”。此前同意(a)“候选很多前瞻点，每个点并行优化几条路径，然后每条点选最优的，再选所有点里最优的”。
- 授权边界：只写文档（task7三文档、子任务三文档、SOURCES、DECISIONS、PROGRESS、PLAN、Codex交流文档、本日志）。不派发、不运行、不安装、不改代码与配置、不改参考仓库。
- 协调：task7父文档与SOURCES原由Codex父任务TASK7-SEQUENCE-RESEARCH-20261019声明独占；该任务文件自10:12起无更新、当前无Codex任务进程（仅app-server）。本次按用户直接指令修改，并在[Codex交流文档](20261019-claude-codex-sync.md)说明改动段落与占用的来源编号。SRC-0341–0355保留给Codex补登，不占用。Codex于16:48另登SRC-0357（N2M阅读），本次从SRC-0358起编号，写入前重新核对。
- 已读：根AGENTS、forem/AGENTS、doc/README、PROGRESS、PLAN、DECISIONS、task7三文档、task7.1–7.3 RESULTS与日志、SOURCES SRC-0318/0334–0340/0356/0357；本地`scwm/`源码（见下）。

## 本次依据的只读核查（2026-10-19，Claude）

`scwm/` commit `f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b`：
- 候选航路点：`ss_trainer_ETP.py:264、1941–2040`（U-Net热力图→12扇区取峰值→删占据→合并→top-8，0.1–5 m）；权重`pretrained/cwp_predictor.pth`（`:302`），训练时eval且不可训练（`:1059`）；本地`scwm/pretrained/`仅有`PLACE_HERE.txt`。
- 占据栅格的高度判定：`waypoint_networks/utils.py:377–410`（深度点云按高度阈值分障碍/地面），配置`ss_trainer_ETP.py:1713`（`occupancy_height_thresh: -1.0`，输入27类语义+3类占据、192×192、0.05 m/格）。
- 反馈层：`models/etp/vilmodel_cmt.py:599–611`（world_model三层MLP、feedback_gate、feedback_delta）、`:815–820`（反馈层零初始化）、`:940–967`（对全部候选预测；H_rebuild先detach；e'=e+sigmoid(W_g[e;h])⊙W_d[h;e]）。
- 底层执行：`common/environments.py:386–447`（`single_step_control`先转向再按步前进，tryout碰撞后左右试探）、`:461–490`（瞬移或沿最短路径）。
- 策略训练为模仿学习（`ss_trainer_ETP.py`中`teacher_ghost`等教师动作），不是SAC。
以上登记为SRC-0358。

## 执行记录

- SOURCES：追加SRC-0358（SC²-WM代码补充）、SRC-0359（用户决定）；写入前核对最大编号为SRC-0357（Codex 16:48）。
- DECISIONS：追加TASK7-FRAMEWORK-20261019。
- task7 TASK：更新入口、术语、§2.3、§2.7–§2.9、§3（U1–U6、U10、U16、U20–U22更新，新增U23–U30）、§4–§7、作者说明；保留“先完成task5.5再开始实施”的用户要求。
- task7 PROCEDURE：实施阶段草案按新框架修订；新增准备与设计子任务表与批次。
- task7 RESULTS：追加10-19下午至晚间记录与交接。
- 新建task7.4–task7.12各三文档（27个文件），由暂存目录脚本`gen_task7_children.py`生成，生成前检查目标文件不存在。
- PLAN阶段二、PROGRESS task7行、Codex交流文档（新增第0节）已更新。
- 自检：task7下所有节点恰有三文档、无多余文件；本次改动文件中的本地链接与SOURCES锚点均有效。仍失效的只有task7.1–7.3引用的SRC-0341–0355（待Codex补登）。
- 未执行：任何派发、运行、安装、代码或配置修改。

## 交接

- 已完成：框架写入与准备子任务三文档。
- 待用户：转交Codex交流文档；决定先派发哪些子任务（task7.5(A)只读审计可直接派；task7.6、task7.12运行需授权）；task7.4起草可由Claude与用户开始。
- 风险：task7.1–7.3的部分结论基于旧讨论方案，需按新框架复核；SOURCES由多Agent并发追加，新编号写入前须核对。

## Agent模型与推理强度

- 推荐：Codex GPT6.1sol / Claude Sonnet5.5，medium（跨RL、世界模型、仿真的一致性文档整合）。
- 实际：Claude claude-opus-5-5，推理强度未知。

## 任务归属与委派

- 父任务task7；本次建立task7.4–task7.12三文档（准备与设计子任务），均未派发、未执行。
