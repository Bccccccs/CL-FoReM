# 2026-10-21 Claude：task7.18阶段L Codex派发提示

- 作者：Claude（claude-opus-5-5，推理强度未知）；由用户派发，Claude不启动。前提：task7.15、7.16、7.17在PROGRESS为done。推荐Codex GPT6.1sol，high（长训前性能核查与SAC数值健康）。

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7.18-STAGE-L-20261021（阶段L：下层SAC网络与训练）。推荐GPT6.1sol / high；日志写明实际模型与强度，无法核实写“未知”。

【前置】先查forem/doc/PROGRESS.md：task7.15、7.16、7.17必须为done，否则停止并报告。

【授权】用户已授权阶段L训练（SOURCES SRC-0431：同步、不同步两变体各1种子×5M动作转移）。范围、资源、文件归属与启动条件以 forem/doc/tasks/task7/task7.18/TASK.md（含“派发参数”节，SRC-0901）为准。不启停或重建容器、不改阶段一代码与参考仓库、不提交git、不做冻结决定（D10归task7.19）。

【并行】task7.19（GPU3）、task7.20–7.22（GPU0/1）正由其他Codex会话同时执行。开发与性能核查只用GPU2。只改TASK“文件归属”所列文件：新包forem/src/task7_lower/、forem/scripts/task7_lower_train.py及启动/监控脚本、forem/config/task7/lower_train.json；kinematics.py仅限DLS性能改动。不得创建或修改task7.20的lower_policy.py。PROGRESS只改自己的行（写前重读，UTF-8字节定点编辑）；SOURCES只用预留SRC-0470–0479。

【先读】根AGENTS.md（尤其“性能优化共同要求”）；forem/AGENTS.md；forem/doc/README.md、PROGRESS.md；forem/ENV.md；task7.18三文档；规格：task7.13 RESULTS的L.0、L.2、L.3、L.4、L.8、D11、D12、D20；task7.4 N12；参考实现forem/scripts/scwm_sac.py（CBL自写SAC，task5.5用；复制改写并记来源commit与哈希）；task7.14、7.15、7.16、7.17的RESULTS与Claude复核（环境、候选、地图池、回合环境接口与已知性能问题）。

【开工】PROGRESS加一行：TASK7.18-STAGE-L-20261021｜Codex｜active｜日志路径；建日志 forem/doc/agent_logs/task7/task7.18/20261021-codex-stage-l.md，先写开工核查（依赖状态、GPU占用、磁盘、7.17环境吞吐基线）。长任务写PID、supervisor、日志、监控与停止/恢复方式；后台Python用python3 -u。

【要做的事】
1. 实现：下层观测编码（128×128×3局部栅格的新地图编码器＋本体/路线/子目标/变体/上一动作向量，L.2）、Actor与双Q（沿CBL结构，MLP[512,512,256]，log_std截[−20,2]）、SAC更新与capped温度规则（L.8，逐行对照scwm_sac.py并测试一致）、uint8 GPU经验池（D11，在线与训练同一量化→解码路径，D20）、子目标按L.4从task7.15规则候选均匀抽、段/回合mask按L.0与D14。单元测试先行。
2. 有界端到端性能核查（≤4小时容器计算内）：分项测环境步进、reset、候选生成、观测构造、CPU→GPU、SAC update、日志/检查点；E扩展；DLS回退频率与固定成本（一次批量约275 ms与目标数无关）。可行优化须落实并以同输入逐元素比对证明语义不变（DLS改动须接受集合不变）；不得改步长、子步、观测、奖励、终止、超参或“每环境步1次更新”。
3. 有界试训：每变体约5万转移，检查损失、温度、Q值、到达率等数值健康。
4. 按实测推算单次5M墙钟：≤48小时则后台启动两变体正式训练（同步GPU2；不同步在task7.19已结束且GPU3无compute进程时用GPU3，否则与同步共用GPU2并报告吞吐影响；绝不占用GPU0/1）；>48小时则停在正式训练前报告瓶颈与方案。每250k转移存完整状态检查点并在验证集（两档各50张×1回合、确定性动作）评估到达率、各类失败率、超时率、平均用时、G1整帧遮挡比例。
5. 交接接口：RESULTS写明检查点格式、观测预处理/量化版本、确定性取动作函数签名，供task7.20加载。

【遇到规格问题】不发起文档复核轮次。歧义或缺数值只停该部分，日志“待决定”列出位置与可选理解，其余继续；不自行补阈值、新语义或新功能。

【输出】RESULTS按run-id追加：实现与测试（命令/退出码/日志）、性能核查前后对照、试训曲线、墙钟推算、正式训练启动信息与监控方式。正式训练启动后PROGRESS本行写“训练中”并给监控命令；训练结束、评估入账后改为review交Claude复核。做不完或预算用尽如实交接，不标完成。
```
