# task8.9.1 r2 固定任务 A

- 负责人 Terra；实际模型 gpt-6.1-terra / low（父指派）。范围：固定清单五条依次执行，原账本累计、GPU0、不得重复 prepare 或修改代码、参数、门；首失败停止。Sol 需复核原件，非独立验收。
- 开始前：main，既有大量工作区改动予以保留；GPU0 无 compute 进程，账本 active=null，已用 81.76879678107798 / 1800 秒。只写本日志及 fixed-execution-r2.json，运行产生清单指定输出与账本。

- 固定任务依次执行：cube b1、b16、b64 均 rc=0、status=pass、warmup=2、steps=20、guard optimizer/backward=0；每条前 GPU0 compute 空、预算充足。
- cube b256 rc=124，status=incomplete，warmup=2、steps=17、guard optimizer/backward=0，wrapper wall=289.6199889937416s。按首失败规则停止；semantic b256 未运行，B 未启动。
- 账本最终累计 505.1480193603784/1800s，active=null；原始 JSON 在 `forem/results/task8/t8-perf-20261027/cube-run-b*.json`，执行汇总 `forem/results/task8/t8-perf-20261027/fixed-execution-r2.json`。须不同 Sol 复核原件；不构成独立验收通过。

## 窗口续测

按父新授权固定清单 `forem/results/task8/t8-perf-20261027/r2-window-jobs.json` 续测，沿原账本、不覆盖原超时结果。cube256 w1/w2 均 rc0、window_complete、预热2+测量10、guard均0，wall分别191.8118801591918s、189.68052812106907s；这两个是重复种子独立窗口，不是连续20步轨迹。

semantic256 w1 rc124、incomplete、预热2+测量8、guard均0，wall 289.7223943127319s；按首失败规则停止，semantic w2 未运行。每次前 GPU0 compute为空且余额充足；最终账本1176.362821953371/1800s，active=null。结果原件 `cube-run-b256-r2-w1.json`、`cube-run-b256-r2-w2.json`、`semantic-run-b256-r2-w1.json`；汇总 `window-execution-r2.json`。需Sol复核与归因，不代表P2验收通过。B后续由父另派执行。

## 最后语义窗口

父批准 `r2-final-window-jobs.json`，沿用1176.3628219533712/1800s账本。semantic w3/w4均 rc0、window_complete、warmup2+6步、optimizer/backward guard均0，wall分别207.63530245888978s和213.58672405034304s。每条前GPU0无其他compute且余额≥296s；三文件前后hash保持父确认值，详 `forem/results/task8/t8-perf-20261027/final-window-execution-r2.json`。最终账本1597.584848462604/1800s、active=null。原w1 rc124/incomplete与8步保留；按Sol已核回滚口径可交Sol合并8+6+6样本，各窗口重复轨迹，不是连续20步。原件 `semantic-run-b256-r2-w3.json`、`semantic-run-b256-r2-w4.json`，须Sol复核、汇总来源和成本；未执行B。
