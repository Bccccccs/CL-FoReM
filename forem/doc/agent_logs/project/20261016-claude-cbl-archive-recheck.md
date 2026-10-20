# 2026-10-16 Claude：cbl原始训练记录独立复核

- 用户要求：“这个对话核查cbl的原始训练记录”。对象是同日[archive首次核查](20261016-claude-cbl-archive-audit.md)所述的`/home/ybc/projects/CL-FoReM/archive`。
- 边界：只读，不改archive，不进入正在运行的容器，不评估/训练。宿主上的解析脚本（自写的TFRecord CRC32C解析、zip testzip、熵扫描）位于会话scratchpad，不作为长期证据。执行：Claude（claude-opus-5-5，实际推理强度未知）；推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low（只读核对，无特殊推理要求）。

## 逐项复核结果

|首次核查主张|复核方法|结果|
|---|---|---|
|`main.py/sac.py/model.py`源码缺失，仅有`__pycache__/sac、model.cpython-37.pyc`|`find`全archive（除runtime）|一致。唯一的`sac.py`是`scripts/stable_baselines3/sac/sac.py`（SB3库，不是cbl自写的SAC）|
|26个检查点中5个损坏（`checkpoints/`3000、5000；`checkpoints_pnp/`全部3个），其余完好|`zipfile.testzip`逐个检查|一致：21个完好，5个`BadZipFile`|
|损坏的5个在`mm_husky_runtime`中有完好的同名副本，字节数相同|stat大小+testzip；`pnp_plus/4000`做SHA256|一致：5个副本zip完好，大小逐字节数相同；`pnp_plus/4000`两份SHA256相同（前缀`5e19a6b4472e0c7e`）|
|7个TB文件只有前40或60 MiB有效，之后全为乱码|自写TFRecord解析，逐条校验长度CRC与数据CRC；按1 MiB分块扫描全文件熵|一致：在41942986–62914559字节处中断（即40/60 MiB边界前），之后压缩比约0.97（有效段约0.25–0.27）。抽样时曾见到疑似低熵点，全文件分块扫描确认低熵只在0–59 MiB，60 MiB之后没有可读区段|
|可读部分的成功率表（7个run）|从有效记录解析`metrics/perfect_success`与`eval/perfect_success`|7行的起点/最高/末值、episode范围、eval数值全部与首次核查一致|
|RLlib picknplace run：picknplace/sim/1 worker/batch 256/intensity 25.6/buffer 1e5/learning_starts 0/seed 173/ik_fail_thresh 20；991次迭代、1,000,151步；训练success 0→0.67；最后eval（984,059步）success 0.70、goal_reached 0.74|读`params.json`、`progress.csv`、`result.json`|全部一致；另有goal_reached训练末值0.82；检查点10个（000100…000900、000991），不是逐迭代保存|

路径更正：RLlib副本在`archive/mm_husky_ws/modulation_rl(复件)/`（与`src/`同级），首次核查记录写法正确，引用时不要误补成`src/modulation_rl(复件)`。

## 结论

- 首次核查的事实部分经独立复核成立，未发现数值错误。
- 仍未知（与首次核查相同）：cbl `main.py`各run的任务、配置和最终成功率；TB文件60 MiB之后的内容需要原文件重拷才能恢复。
- 补充事实：`__pycache__`里留有`sac/model.cpython-37.pyc`，理论上可反编译出近似源码。是否做、是否向cbl补要原文件需用户决定，本次不执行。
