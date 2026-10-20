# PROJECT-GPU-TRAINING-SIZE-20261009

用户问训练规模/显存，15:29只读GPU与实际CUDA训练进程、配置/回放代码。三seed各1M，70k/73k/72k，GPU各3740MiB/97887MiB。回放map两份2.682GiB推导，规模与同时驻留内存分开；reset/CPU限制沿既有Task4.8实测。不改模型或扩batch，不为了显存满扩大范围。来源[SRC-0194](../../SOURCES.md#src-0194)。

Codex /root实际未知，推荐GPT6.1sol/Sonnet5.5 low/default（常规快照与明确字节计算）。状态done；没有新测试/训练或操作他人进程。
