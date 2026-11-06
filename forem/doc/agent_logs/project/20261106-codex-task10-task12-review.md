# task10 task12 联合审核

开始 2026-11-06T09:11:29.356170+08:00。用户要求审核task10/12。负责人Codex，实际模型/强度未知；推荐GPT6.1sol/medium、Sonnet5.5/medium，训练/评估/隔离合同跨模块核查。可自主选模/先建档委派，本轮独立。范围：读取两工作区最新记录、已完成原件和实际进程，必要定向复算并追加审核依据/结果；不新增训练/评估，不干预其他进程。

主分支codex/task9-sac-opt-20261031、task10树codex/task10-upper-wm，多处既有脏改动保留。task10执行者正在单独补10k CPU报告（PID2479978），不重复启动或覆盖其输出。task12 r8 GPU3制数中，只读分组/计数/新代码，不提前查看封存收益。

## task10 JSON原件独立复算

标准库读取三检查点episodes/decisions.jsonl，核36唯一回合、60唯一决策、计数、初态哈希跨检查点相等、合法槽且选择最高logit；退出码0。完整终态/权重审计复用执行者报告，不重复全量哈希或模拟评估。
```json
{
  "2000": {
    "completed": 12,
    "success": 10,
    "inplace": 0,
    "decisions": 18,
    "reasons": {
      "failure_limit": 2,
      "strict_success": 10
    },
    "failed_maps": [
      "sparse_validation_00004",
      "standard_validation_00000"
    ],
    "inplace_rows": [],
    "stall_max": 0
  },
  "5000": {
    "completed": 12,
    "success": 9,
    "inplace": 1,
    "decisions": 20,
    "reasons": {
      "failure_limit": 2,
      "strict_success": 9,
      "completion_with_failures": 1
    },
    "failed_maps": [
      "sparse_validation_00004",
      "standard_validation_00000",
      "standard_validation_00001"
    ],
    "inplace_rows": [
      {
        "map": "standard_validation_00001__trained",
        "index": 0,
        "stalls": 0,
        "delta_s": [
          0.25
        ]
      }
    ],
    "stall_max": 1
  },
  "10000": {
    "completed": 12,
    "success": 9,
    "inplace": 1,
    "decisions": 22,
    "reasons": {
      "failure_limit": 2,
      "strict_success": 9,
      "completion_with_failures": 1
    },
    "failed_maps": [
      "sparse_validation_00004",
      "standard_validation_00000",
      "standard_validation_00001"
    ],
    "inplace_rows": [
      {
        "map": "standard_validation_00001__trained",
        "index": 0,
        "stalls": 0,
        "delta_s": [
          0.25
        ]
      }
    ],
    "stall_max": 2
  }
}
```

## task12阶段核查及结束

2026-11-06T09:14:15.029017+08:00：234/256完整、5616/6144完整状态标签、0更新；核160/32/64和256唯一地图、与旧65无交集、标签前冻结、15项已有测试通过；静态核训练装配跳过sealed、训练集权重、五键选模/200epoch/4600更、封存哈希锁与统计门。未读sealed标签或收益；不重跑测试。task10补CPU报告PID2479978仍执行，未重复启动。修改两树SOURCES、各自RESULTS/PROGRESS及task10 DECISIONS，保留其他执行者记录；无代码/运行产物修改、无新训练/评估。结论仅阶段审核；当前执行者继续报告补证及持久制数。
