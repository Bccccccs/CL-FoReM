# task12.6 新图最终审核

开始：2026-11-05T20:29:38.190179+08:00。用户要求“审核”；范围为 r7 原件/统计及结论验收，只更新审核文档，不启动新实验、不改科学合同、不干预其他运行。负责人 Codex，实际模型/强度无法独立核实。推荐 GPT6.1sol/medium、Sonnet5.5/medium，因需核对点级与状态级口径；执行者可按根 AGENTS 自主选模及先建档委派，本轮独立完成。

已读根 AGENTS、README、PROGRESS、task12.6 三文档和父结果；工作区有大量既有改动，全部保留。审核原件：forem/results/task12/t12-newmaps-20261105-r7。

## 原件独立复算

以标准库从 states/*/{labels,selection,row}.json 关联 candidate_id；独立复算标签公式、允许扇区最高分/最近选择与点/状态计数，不调用原统计模块。退出码 0。原始 FK 数值沿用已验证提取路径，本轮未重复计算物理 FK。

```json
{
  "counts": {
    "labels": 768,
    "positive_sectors": 107,
    "covered_states": 21,
    "network_points": 96,
    "network_states": 17,
    "network_arrival_states": 6,
    "nearest_points": 74,
    "nearest_states": 18,
    "nearest_arrival_states": 12,
    "point_same_states": 21,
    "point_gain_states": 8,
    "point_loss_states": 3
  },
  "state_pairs": {
    "both": 15,
    "gain": 2,
    "neither": 12,
    "loss": 3
  },
  "gain_states": [
    "state-03",
    "state-06"
  ],
  "loss_states": [
    "state-11",
    "state-23",
    "state-24"
  ],
  "label_formula_and_selection_checks": "passed on all 768 JSON records; FK values reused, not re-evaluated",
  "driver": {
    "run_id": "t12-newmaps-20261105-r7",
    "status": "returned",
    "started": "2026-11-05T15:44:49.959565+08:00",
    "driver_pid": 1892068,
    "docker_client_pid": 1892078,
    "container": "forem-task12-newmaps-r7",
    "gpu": {
      "index": 2,
      "uuid": "GPU-656ca5c1-681f-48a2-7d1f-a00824723f68",
      "baseline_memory_mib": 14
    },
    "argv": [
      "sg",
      "docker",
      "-c",
      "docker run --rm --name forem-task12-newmaps-r7 --gpus device=GPU-656ca5c1-681f-48a2-7d1f-a00824723f68 --network none --user 1004:1004 --cpuset-cpus 10-11 --shm-size 1g -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/run/code:/original/frozen-source/src -e OMP_NUM_THREADS=2 -e OPENBLAS_NUM_THREADS=2 -e CUDA_VISIBLE_DEVICES=0 -e PYTORCH_KERNEL_CACHE_PATH=/tmp/torch-kernels -e CUBLAS_WORKSPACE_CONFIG=:4096:8 -v /home/ybc/projects/CL-FoReM/forem:/workspace:ro -v /home/ybc/projects/CL-FoReM/forem/results/task12/t12-abc-20261104-r1:/original:ro -v /home/ybc/projects/CL-FoReM/forem/results/task12/t12-newmaps-20261105-r7:/run --entrypoint /opt/python310/bin/python3 mm_husky:node01 -u /run/code/task12_newmaps.py --run /run"
    ],
    "engineering_estimate_s": 14400,
    "network_updates": 0,
    "last_attempt": {
      "attempt": 1,
      "event": "end",
      "started": "2026-11-05T15:44:49.959565+08:00",
      "started_epoch": 1793864689.9595797,
      "driver_pid": 1892068,
      "gpu": {
        "index": 2,
        "uuid": "GPU-656ca5c1-681f-48a2-7d1f-a00824723f68",
        "baseline_memory_mib": 14
      },
      "argv": [
        "sg",
        "docker",
        "-c",
        "docker run --rm --name forem-task12-newmaps-r7 --gpus device=GPU-656ca5c1-681f-48a2-7d1f-a00824723f68 --network none --user 1004:1004 --cpuset-cpus 10-11 --shm-size 1g -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/run/code:/original/frozen-source/src -e OMP_NUM_THREADS=2 -e OPENBLAS_NUM_THREADS=2 -e CUDA_VISIBLE_DEVICES=0 -e PYTORCH_KERNEL_CACHE_PATH=/tmp/torch-kernels -e CUBLAS_WORKSPACE_CONFIG=:4096:8 -v /home/ybc/projects/CL-FoReM/forem:/workspace:ro -v /home/ybc/projects/CL-FoReM/forem/results/task12/t12-abc-20261104-r1:/original:ro -v /home/ybc/projects/CL-FoReM/forem/results/task12/t12-newmaps-20261105-r7:/run --entrypoint /opt/python310/bin/python3 mm_husky:node01 -u /run/code/task12_newmaps.py --run /run"
      ],
      "ended": "2026-11-05T17:43:29.792054+08:00",
      "wall_s": 7119.832531532273,
      "returncode": 0
    },
    "device_verified": true,
    "estimate_adjustments": [
      {
        "at": "2026-11-05T15:51:20.856931+08:00",
        "completed": 1,
        "estimate_s": 10872.63963724114,
        "reason": "same32 workload actual throughput; no scale/scientific changes"
      }
    ],
    "returncode": 0,
    "sampled_device_peak_mib": 3392,
    "ended": "2026-11-05T17:43:29.792054+08:00"
  }
}
```

完成：2026-11-05T20:31:38.696088+08:00。已核三次状态退化state-11/23/24均为唯一允许安全到点正例漏选；详见SRC-T12-023。修改SOURCES、PROGRESS、DECISIONS、task12父RESULTS、task12.6 TASK/RESULTS及本日志。task12.6 done、task12整体仍待泛化与系统验证。无代码/实验产物修改，无新制数/训练，未干预其他进程。
