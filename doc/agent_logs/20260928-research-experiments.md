# RESEARCH-028-EXP — 实验与历史证据审计

- 执行 Agent：Codex `/root/experiments`（主协调 Agent 为 `/root`，只由其维护 PROGRESS 总表）。
- 开始时间：2026-09-28T09:11:13+08:00。
- 状态：review（文档与审计已交付，等待主Agent审查）。
- 目标：只读核实已有 P0/P1 证据、数据划分及真实指标接口；创建 `doc/RESEARCH_EXPERIMENTS.md`，为用户 IROS 2027 研究要求提供可证伪的实验框架。
- 范围：只写本记录与 `doc/RESEARCH_EXPERIMENTS.md`；不启动训练、不修改算法、不加载大型轨迹数组、不写其他 Agent 的共享文档。
- 已读：AGENTS.md、doc/README.md、doc/PROGRESS.md、doc/DECISIONS.md、doc/EVALUATION.md、doc/P1_WORLD_MODEL.md、ENV.md、doc/agent_logs/TEMPLATE.md，以及用户本轮附件全文（路径 `/home/ybc/.codex/attachments/54ea6894-6a03-440e-81cf-2159049941fb/已粘贴的文本.txt`）。
- 技能：读取 using-superpowers；其 SUBAGENT-STOP 明确特定子任务不执行该工作流。本轮是证据与实验文档，不实现功能。
- 版本：主包 `src/modulation_rl` HEAD `2a1348a87b3b5c45f495fafacad526f7eaee7749`，本次检查工作树无输出（干净）；根工作树既有 `.gitignore`、AGENTS.md、ENV.md 修改及未跟踪 doc/、docker/，保留所有其他改动。

## 进度记录

### 2026-09-28T09:11:13+08:00 — 开始

主 Agent 已登记任务。用户强调 WM 闭环研究、实验公平性、负结果、资源约束与论文证据链；本任务将其映射到当前 SAC 状态修正接口，候选轨迹/优化器参数等未存在的接口标明新研究分支，不能包装为既有实现。P1 出口仍遵循 D28：未通过；P1b/P2 暂不放行。

已确认历史 D26/D28 两组测试种子 9000–9099、9100–9199 均已查看。接下来读取 manifest 核查 dataset-v2-10k 的实际种子交叠，并从评测 JSON/代码核实指标与数值，避免仅转抄历史摘要。

## 改动与验证

| 时间 | 文件/命令 | 实际结果/退出码 | 证据 |
|---|---|---|---|
| 09:10–09:11 +08 | `cat` 上述必读文档与用户附件；长输出后分文件重读 DECISIONS、EVALUATION、P1 | 0；原合并输出有截断，已对关键文档补读 | 文档中的 D24–D29；P1 出口与 EVALUATION 统计规范 |
| 09:11 +08 | `date -Iseconds`; `git status --short`; `git -C src/modulation_rl rev-parse HEAD`; `git -C src/modulation_rl status --short` | 0；版本与工作树见上 | 本记录版本栏 |
| 09:11 +08 | `rg --files doc scripts src/modulation_rl/scripts` 过滤 wm/评测文件 | 发现根目录 scripts 不存在，rg 提示错误；有效主包路径为 `src/modulation_rl/scripts` | 后续只查存在目录 |

## 长任务

无。未启动容器/训练/评测，未操作任何运行进程。

## 审查与问题

- 历史 ENV/README/AGENTS 含早期硬件与 P0 状态；本次只以较新的实际记录/产物核实当前证据，不据旧摘要放行阶段。
- 需核查扩充数据是否包含已公开测试种子；“原数据可读取”不能证明实验隔离正确。

## 交接

工作中。最终文档待核查链接与所有引用数值；完成文档仅标 review，不替算法阶段验收。

### 2026-09-28T09:13+08:00 — 用户范围澄清

主 Agent 转达用户最新明确要求：“我们只引入世界模型闭环到husky来，不考虑TopAY和Nmoma了”。本次实验文档只覆盖 Husky 的 WM 前瞻、真实反馈、SAC 最终动作及其必要对照；不列 TopAY/NMoMA 比较，也不把候选轨迹选择或优化器参数自适应当作必做实验。12 Stage 按该闭环主线压缩映射。此澄清优先于附件中泛化系统举例。

### 2026-09-28T09:16+08:00 — manifest 与历史结果核查

本次只读取小型 JSON/源码，未解压轨迹数组。三个 dataset.json 解析、种子集合与 SHA-256 比较均退出 0。确认 dataset-v2-10k 的 train=0–9599，val=9600–9899，test=9900 占位；train 与 dataset-v1 的 train/val/test 分别重复 1000/100/100 条，与 dataset-freshtest test 重复 100 条，且这些交集的分片 SHA-256 **全部相同**。因此不是仅同种子潜在重复，而是 manifest 指向的轨迹内容哈希相同。新扩充训练集内部三个划分互斥，但与历史跨版本 holdout 不互斥。D28 当时模型训练于 dataset-v1，其历史测试结论不被后续采集追溯否定；扩大数据训练的新模型不能再以旧两组 test 作为留出证据。manifest 摘要哈希与数值将写入实验文档。

已实读 wm-v1-eval/report.json、wm-v2-eval-freshtest/report.json，确认 D28 数字及出口失败；误探路径 wm-v2-eval/report.json 不存在，实际路径带 -freshtest 后缀。P0 四个 gate JSON passed=true、20 episodes，五项 max_abs_differences 全0；SAC/prior 工程 baseline summary 与验收表一致。这里只核对落盘结果，不是本日重新训练/复测。

代码核查：EpisodeDataset 同时保留逐回合数组并 concatenate 整体数组；train_offline 进一步将完整窗口放 device，训练 epoch 末计算全量 train/val 前向。只修读取器仍可能把内存瓶颈移至 GPU，资源预检需覆盖编码、缓存、窗口索引、训练/验证前向全链路。evaluate_prediction 在内存中计算逐回合误差后只写 report.json 聚合，未落逐回合预测误差；未来统计可重算性需补该产物。收集入口只检查单次三个区间是否重叠，不检查跨版本暴露历史。

实际命令：Python pathlib/json/hashlib 读取三个 manifests 和小型 reports、比对 seed→sha256；sed 读取 wm/data.py、wm/train_offline.py、wm/evaluate_prediction.py、collect_rollouts.py；rg 查 p0_runner.py 指标字段。对不存在的 scripts/p0_metrics.py 的 rg 返回缺文件提示，已定位指标实际在 p0_runner.py，无代码改动。所有成功读取退出0。

### 2026-09-28（09:11–09:20期间） — 数据审计复查证据与沿用原则

用户追加“现有可以沿用的就继续用”。实验文档定位为 EVALUATION/P0–P5 增补，不新建并行实验系统。主 Agent 将跨版本曝光记为 D32。本轮沿用 P0 runner、采集分片、固定编码器、copy/no_action 对照、统计口径与全部负结果；只标缺口和下一步。

三个 manifests 的全部已记录分片路径存在；从 episodes 重加 transitions 与 counts 全相同。各 split 的 episodes.jsonl 有同样数量的逐回合记录，split 内 layout_sha256/initial_observation_sha256 的唯一值数分别等于回合数（不据此声称跨场景类型泛化）。仅实际重算两对小型压缩分片文件哈希，未解压任何数组：seed9000 两文件同为 `0035916dd077927df60d2c6127086bcf7c8e067b911949774b53e73aba8abc7b`，seed9100 两文件同为 `52714b1978dcbe4284a14514c15e382cb46a61ff9932c495efb740de621fa182`，均与各自 manifests 相符。全部200条是manifest哈希比较，不能说全部200条文件已重新读过校验。

| manifest | 本次实算 SHA-256 |
|---|---|
| dataset-v1/dataset.json | 6aec9625f147ba76584a17e5a2d429a6e22c91292a95626af3432dd9a8be4a5d |
| dataset-freshtest/dataset.json | 5062e2450a01f474d4f50b2baeae89419795e6eb206d5b7afeaf44fd313843aa |
| dataset-v2-10k/dataset.json | 405e1c7de36b5c76928ddc1b02e97c38b8fc66e96f05ba69cb24f7ec56d71e00 |
| wm-v2-eval-freshtest/report.json | c0736b8867a1932dd33ce2bbb8f01e5b3bdfcd3d7a50382465a75e580b78631d |

交集可复查命令（本轮已执行等价 Python，退出0；只读 JSON）：

```bash
python3 - <<'PY'
from pathlib import Path
import json
root = Path('results/p1a-20260923')
def read(name):
    return json.loads((root / name / 'dataset.json').read_text())['episodes']
expanded = {r['seed']: r for r in read('dataset-v2-10k') if r['split'] == 'train'}
for name, split in [('dataset-v1', 'train'), ('dataset-v1', 'val'),
                    ('dataset-v1', 'test'), ('dataset-freshtest', 'test')]:
    old = {r['seed']: r for r in read(name) if r['split'] == split}
    overlap = sorted(old.keys() & expanded.keys())
    identical = sum(old[s]['sha256'] == expanded[s]['sha256'] for s in overlap)
    print(name, split, len(overlap), (min(overlap), max(overlap)), identical)
PY
```

实际输出（列：旧版本/划分/交集数/闭区间/同哈希数）：

```text
dataset-v1 train 1000 (0, 999) 1000
dataset-v1 val 100 (8000, 8099) 100
dataset-v1 test 100 (9000, 9099) 100
dataset-freshtest test 100 (9100, 9199) 100
```

代码审查新增：train_offline 在 MLP 构造之后才于 train_model 内 manual_seed，初始化随机源是否可复现需在后续资源修复时单独核验，不在本轮凭静态阅读声称重跑失败。碰撞/IK为累计失败步数；raw MSE 是原始机器人状态/地图**特征尺度**，不是米/弧度的统一物理误差。P0 control_seconds 是动作推理加环境 step；需补 WM/adapter/传输/更新分段计时。

### 2026-09-28T09:20:28+08:00 — 高优先窗口索引缺陷独立核实（D33）

主 Agent 要求独立验证 `wm/train_offline.py:29–35`：`window_tensors` 读取了 `e,t=w[:,0],w[:,1]`，但 observation/action 索引都漏加 `t`。本Agent确认，`encode_split/window_tensors`被训练、val_probe和evaluate_prediction共同使用，因此不是只影响未来内存优化。训练与1/5步评测把同一回合不同t重复映射到该回合前1/5步。dataset原始分片和EpisodeDataset.gather的正确索引不受本项直接影响；旧模型/曲线/报告受影响，须保留但不能作为全轨迹预测的有效证据。

首次宿主 `python3` probe 退出1：`ModuleNotFoundError: numpy`。未安装依赖。读取 `sg docker -c 'docker ps --format "{{.Names}} {{.Status}}"'` 退出0，确认现有 `mmhusky-node01` 运行；随后在该容器 `/opt/python310/bin/python3` 做只用NumPy的5窗口CPU probe（未import Torch，未占GPU，未碰真实轨迹）。NumPy1.23.5，退出0。没有启动训练、重启/停止容器或其他进程。

实际执行命令及输出：

```bash
sg docker -c 'docker exec -i mmhusky-node01 /opt/python310/bin/python3 -' <<'PY'
import numpy as np
obs_offset=np.array([0,5]);act_offset=np.array([0,4])
w=np.array([[0,0],[0,1],[0,2],[1,0],[1,1]])
e,t=w[:,0],w[:,1];k=1
o_current=obs_offset[e][:,None]+np.arange(k+1)
a_current=act_offset[e][:,None]+np.arange(k)
o_expected=(obs_offset[e]+t)[:,None]+np.arange(k+1)
a_expected=(act_offset[e]+t)[:,None]+np.arange(k)
print('current_obs',o_current.tolist());print('expected_obs',o_expected.tolist())
print('current_action',a_current.tolist());print('expected_action',a_expected.tolist())
assert np.array_equal(o_current[0],o_current[1])
assert not np.array_equal(o_current,o_expected)
PY
```

```text
current_obs [[0, 1], [0, 1], [0, 1], [5, 6], [5, 6]]
expected_obs [[0, 1], [1, 2], [2, 3], [5, 6], [6, 7]]
current_action [[0], [0], [0], [4], [4]]
expected_action [[0], [1], [2], [4], [5]]
```

测试覆盖检查：`rg -n 'window_tensors|encode_split' scripts/tests scripts/wm`（以主包路径执行等价搜索）没有tests命中；`test_wm_data.py`确实测试`EpisodeDataset.gather`的非零t，但train_offline绕过它；`test_wm_prediction.py`测试独立rollout，不覆盖窗口组装。旧43项通过不能证明真实训练/评测窗口正确。

处置：只修文档可信级别，不改算法。D26–D28原数值是历史产物，但不是已验证的全轨迹动作条件预测优劣结论；P1仍未过出口的原因改为“受缺陷影响，必须先修正确性并重训重测”，不能将“增加数据”作为优先因果解释。根Agent将记D33；实验文档即刻同步，资源方案由主Agent另写P1_MEMORY_PLAN.md。

时间戳核对：本轮系统 `date -Iseconds` 实测为2026-09-28T09:20:28+08:00；高优先发现记录使用该实测时刻，未单独取时的上一条以本轮时间段表示，避免估算分钟被误认为精确运行时间。

### 2026-09-28T09:23:01+08:00 — 文档交付与验证

已创建 `doc/RESEARCH_EXPERIMENTS.md`（185行）：沿用EVALUATION/P0–P5，覆盖已有证据、数据隔离、指标状态、SAC匹配对照、闭环频率消融、鲁棒性/泛化/资源矩阵、统计和claim证据、下一步有限顺序。最新用户范围已贯彻，未加入外部系统比较/候选轨迹必做接口。D33优先级高于扩数据，旧P1结果在文档所有结论入口标为受影响历史。

验证（本轮实际执行，均退出0）：

- Python解析Markdown本地链接：20个引用，缺失0；含主Agent新建P1_MEMORY_PLAN链接。
- 从真实wm-v2-eval-freshtest/report.json逐项断言表中1/5步三模型MSE、两组配对差均值及CI、窗口数：全部一致；窗口数同时明确为错误索引生成的名义行数。
- 三个dataset.json的各split转移数、压缩字节数与正文逐项比对：全部一致；数据分片存在性、交集与SHA证据见上文。
- 断言D33/“不是有效全轨迹测试”/“尚未执行”/SAC最终动作约束均存在，外部系统名称不在实验矩阵正文。
- 两文档逐行检查无尾部空白、末尾换行、代码围栏成对；主包git status无输出，本任务没有算法改动。`git diff --check`亦无输出，但doc属于根仓库未跟踪内容，不能单靠该命令替代上述逐文件验证。

交接：状态review，仅交付本日志与实验增补；主Agent维护总表并审查。首要后续是D33正确性修复及覆盖非零t的窗口回归，再实施有界内存方案与正确重训；D32要求新测试前登记全历史曝光。没有启动新训练、没有新模型收益结论、没有调整P0–P5 gate；原始结果/分片/容器进程保留。
