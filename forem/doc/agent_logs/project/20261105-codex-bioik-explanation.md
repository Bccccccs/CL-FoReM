# BioIK用途与本项目选择解释

- 任务：PROJECT-BIOIK-20261105；负责人Codex；开始/完成时间：2026-11-05T17:18:39+08:00；状态done。
- 用户要求：解释bioik是什么、为什么我们不用。授权仅资料/源码核查及说明，不改实现、不运行实验、不新增功能。
- 已读README、PROGRESS、task7.3 RESULTS、task7.5相关复用/IK合同、SOURCES相关条目；分支codex/task9-sac-opt-20261031，根HEAD121cb36，工作区有大量既有修改，保留。只读查看进程，未启停任务。
- 核查：旧Husky配置仍为BioIK；新task7_sim/kinematics.py::solve_tcp_in_arm先解析分支/FK回检，再对无精确解调用DLS。现代码还可按base/robot参数作碰撞分支选择，因此不能把早期设计中IK完全不看碰撞的文字当全部现实现。
- 结论与边界：BioIK将目标末端位姿转为关节配置，可组合软目标；旧CBL复现使用，新独立批量环境选择解析+DLS。批量架构适配是工程理由，未做本次BioIK对新求解器配对性能/成功率测试，不能称新求解器更优或两环境等价。来源见[SRC-BIOIK-20261105](../../SOURCES.md#src-bioik-20261105)、既有SRC-0351/0352/0366/0417。
- 方法：只读配置/源码及官方README（Disclaimer、Basic Usage、Advanced Usage），无安装、训练、测试。下一步/剩余事项：无；交付聊天解释，若研究性能优劣需另行授权具体对照。
- 选模/委派：推荐Codex GPT6.1sol low、Claude Sonnet5.5 low，普通资料解释无特殊推理要求；允许范围内按难度选模/强度及独立或委派，本轮独立完成，实际模型/强度无法核实，记未知。
