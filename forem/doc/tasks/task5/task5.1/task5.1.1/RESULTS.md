# task5.1.1 监督结果

> **当前状态（2026-10-19核对）：结束（监控对象A训练与评估已结束，不再运行）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：active（派发准备2026-10-11T22:52:46.766949+08:00；子Agent尚未核查）。父部署的A训练已运行，监督新验收尚未执行。
推荐/派发Codex gpt-6.1-sol/low；Claude替代Sonnet5.5/low或默认，明确监控步骤；实际运行由接手Agent记录。
目标授权：只监督A及已部署后处理，不新增运行、不改配置/源码/参数、不停止其他任务。证据/风险/剩余事项待子Agent实际记录。

## 接手核查 2026-10-11T22:53:47.610552+08:00

实际派发gpt-6.1-sol/low（父派发可核实）；推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认，明确监控步骤。只监控A，不重启/修改/启动B/停止进程。依据[ SRC0219 ](../../../../SOURCES.md#src-0219)。

```json
{
  "time": "2026-10-11T22:53:47.610552+08:00",
  "monitor_pid": 2140918,
  "monitor_alive": true,
  "posttrain_pid": 2203635,
  "posttrain_alive": true,
  "train_pid": 34861,
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-11T22:53:43.530137+08:00",
    "host_cpu_cores": 4.0936412924253345,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 186,
  "cpu_max": 17.351935250212577,
  "progress_path": "forem/results/task5/t5.1-train-s40/ray/pr2_acceleration_penalty:0.05_learn_torso:T_learn_vel_norm:0.1_training_intensity:0.1_transition_noise_base:0.04_mindispl1.0,0.0,1.0/SACTrainerCustom_modulation_rl_env_6525c_00000_0_2026-10-11_14-38-16/progress.csv",
  "progress_latest": {
    "timesteps_total": "18000",
    "episodes_total": "226",
    "time_total_s": "905.1393439769745",
    "training_iteration": "18"
  },
  "latest_evaluation": null,
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

已完成接手核查；剩余训练与§4–6仍执行中/待执行，不作为独立验收。风险：长训/后处理后续失败尚不能排除。下一步每30分钟核查记录，异常立即交父。监控路径results/task5/t5.1-train-s40/host_cpu_5s.jsonl、monitor_30min.jsonl、posttrain_status.json；不执行停止/恢复。

## R7/D11监控规则更新 2026-10-11T23:04:45.241541+08:00

用户最新规则由父Agent通知：连续5分钟主机CPU时间加权均值>56核仅告警，任何情况下不得因CPU自动停止训练。撤销旧两次5秒样本SIGINT说明，旧记录保留为历史。已只读核查monitor_D11_change.json和当前monitor_task5_train.py：旧PID2140918由父停止，新PID2238780生效23:04:04+08，脚本已无训练信号路径，A PID34861未重启。posttrain CPU告警blocked检查父正在修改，本子Agent未改源码/进程。证据results/task5/t5.1-train-s40/monitor_D11_change.json；来源由父登记，不写共享SOURCES。模型推荐/实际派发仍GPT6.1sol/gpt-6.1-sol low；Claude Sonnet5.5 low/默认。

## 30分钟核查 2026-10-11T23:24:03.850032+08:00

```json
{
  "time": "2026-10-11T23:24:03.850032+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "cpu_latest": {
    "time": "2026-10-11T23:24:00.918272+08:00",
    "host_cpu_cores": 5.385809939957876,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 549,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 2.9,
  "progress_latest": {
    "timesteps_total": "52000",
    "episodes_total": "613",
    "time_total_s": "2701.9143607616425",
    "training_iteration": "52"
  },
  "latest_evaluation": null,
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。已核查posttrain脚本无CPU告警失败门，当前PID2243657。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-11T23:57:12.276443+08:00

```json
{
  "time": "2026-10-11T23:57:12.276443+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-11T23:57:07.936258+08:00",
    "host_cpu_cores": 5.372387567176844,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 946,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 4.4,
  "progress_latest": {
    "timesteps_total": "87000",
    "episodes_total": "966",
    "time_total_s": "4687.679025173187",
    "training_iteration": "87"
  },
  "latest_evaluation": {
    "steps": 75000,
    "metrics": {
      "episode_reward_max": -3.6521449788367035,
      "episode_reward_min": -47.41568113921456,
      "episode_reward_mean": -14.449659739314242,
      "episode_len_mean": 114.38,
      "episode_media": {},
      "episodes_this_iter": 50,
      "policy_reward_min": {},
      "policy_reward_max": {},
      "policy_reward_mean": {},
      "custom_metrics": {
        "goal_reached_mean": 0.12,
        "goal_reached_min": "False",
        "goal_reached_max": "True",
        "ik_fails_mean": 17.06,
        "ik_fails_min": 0,
        "ik_fails_max": 20,
        "ik_zero_fail_mean": 0.14,
        "ik_zero_fail_min": "False",
        "ik_zero_fail_max": "True",
        "ik_b100_mean": 1.0,
        "ik_b100_min": "True",
        "ik_b100_max": "True",
        "base_collisions_mean": 0.54,
        "base_collisions_min": 0,
        "base_collisions_max": 20,
        "success_mean": 0.1,
        "success_min": "False",
        "success_max": "True",
        "vel_normed_avg_deviation_mean": 0.033540555346756575,
        "vel_normed_avg_deviation_min": 0.014240028180056449,
        "vel_normed_avg_deviation_max": 0.056090774450348886,
        "steps_above_joint_vel_limit_mean": 0.02,
        "steps_above_joint_vel_limit_min": 0,
        "steps_above_joint_vel_limit_max": 1,
        "steps_above_3x_joint_vel_limit_mean": 0.0,
        "steps_above_3x_joint_vel_limit_min": 0,
        "steps_above_3x_joint_vel_limit_max": 0,
        "dist_to_desired_mean": 0.049468442747012585,
        "dist_to_desired_min": 0.008650405468946583,
        "dist_to_desired_max": 0.10346721207330589,
        "rot_dist_to_desired_mean": 0.0020687838030300286,
        "rot_dist_to_desired_min": 9.704532135000117e-07,
        "rot_dist_to_desired_max": 0.020546748255148604,
        "success_nojumps_mean": 0.08,
        "success_nojumps_min": "False",
        "success_nojumps_max": "True",
        "success_nojumps3x_mean": 0.1,
        "success_nojumps3x_min": "False",
        "success_nojumps3x_max": "True",
        "max_close_steps_reached_mean": 0.02,
        "max_close_steps_reached_min": 0.0,
        "max_close_steps_reached_max": 1.0,
        "vel_norm_mean": 0.09434394725392328,
        "vel_norm_min": 0.07471307288402709,
        "vel_norm_max": 0.1084414974626686,
        "episode_disc_return_mean": -6.296224568727722,
        "episode_disc_return_min": -13.902892799796001,
        "episode_disc_return_max": -2.1777648615438165
      },
      "hist_stats": {
        "episode_reward": [
          -14.482221059323559,
          -11.288525480127179,
          -17.25935021898782,
          -5.787917922221524,
          -17.991775071911558,
          -9.415373130899068,
          -9.601082555190349,
          -12.283426550077404,
          -12.325842906471859,
          -11.623301981991402,
          -10.911356262861856,
          -12.411759197699118,
          -45.92368692728085,
          -16.88600861150348,
          -8.951941803511602,
          -10.21678675516283,
          -3.6521449788367035,
          -10.031618137272014,
          -10.353065830974089,
          -14.02903047341922,
          -9.598277177266052,
          -24.27673973576146,
          -11.732761375318255,
          -11.515012890801685,
          -19.57599387958051,
          -15.06381303711716,
          -13.552207348540852,
          -14.771772736069446,
          -18.330485697917496,
          -13.105617543965977,
          -23.77470750944159,
          -47.41568113921456,
          -6.885856169000837,
          -18.2636739573558,
          -5.217632687582843,
          -20.141146356340506,
          -15.072423700109738,
          -40.817628018042335,
          -15.198260369678591,
          -10.329880593282013,
          -9.100392889532138,
          -11.687228190312256,
          -11.821040908658698,
          -9.191929023017567,
          -8.969622097517343,
          -10.349822957652036,
          -11.979792878077333,
          -4.410839560590242,
          -11.169334363110318,
          -13.737196319132927
        ],
        "episode_lengths": [
          93,
          118,
          88,
          82,
          63,
          38,
          98,
          52,
          122,
          63,
          86,
          37,
          273,
          207,
          175,
          91,
          121,
          68,
          62,
          118,
          65,
          210,
          94,
          47,
          176,
          111,
          170,
          156,
          203,
          136,
          77,
          428,
          110,
          112,
          105,
          84,
          190,
          125,
          112,
          85,
          54,
          54,
          96,
          72,
          74,
          71,
          92,
          139,
          59,
          157
        ]
      },
      "sampler_perf": {
        "mean_raw_obs_processing_ms": 3.195662806917737,
        "mean_inference_ms": 1.5138537316889198,
        "mean_action_processing_ms": 0.07565546702671716,
        "mean_env_wait_ms": 10.353821974534256,
        "mean_env_render_ms": 0.0
      },
      "off_policy_estimator": {}
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T00:20:56.211302+08:00

```json
{
  "time": "2026-10-12T00:20:56.211302+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T00:20:54.398356+08:00",
    "host_cpu_cores": 5.503127062446966,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 1231,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 1.9,
  "progress_latest": {
    "timesteps_total": "112000",
    "episodes_total": "1166",
    "time_total_s": "6094.641946077347",
    "training_iteration": "112"
  },
  "latest_evaluation": {
    "steps": 75000,
    "metrics": {
      "episode_reward_max": -3.6521449788367035,
      "episode_reward_min": -47.41568113921456,
      "episode_reward_mean": -14.449659739314242,
      "episode_len_mean": 114.38,
      "episode_media": {},
      "episodes_this_iter": 50,
      "policy_reward_min": {},
      "policy_reward_max": {},
      "policy_reward_mean": {},
      "custom_metrics": {
        "goal_reached_mean": 0.12,
        "goal_reached_min": "False",
        "goal_reached_max": "True",
        "ik_fails_mean": 17.06,
        "ik_fails_min": 0,
        "ik_fails_max": 20,
        "ik_zero_fail_mean": 0.14,
        "ik_zero_fail_min": "False",
        "ik_zero_fail_max": "True",
        "ik_b100_mean": 1.0,
        "ik_b100_min": "True",
        "ik_b100_max": "True",
        "base_collisions_mean": 0.54,
        "base_collisions_min": 0,
        "base_collisions_max": 20,
        "success_mean": 0.1,
        "success_min": "False",
        "success_max": "True",
        "vel_normed_avg_deviation_mean": 0.033540555346756575,
        "vel_normed_avg_deviation_min": 0.014240028180056449,
        "vel_normed_avg_deviation_max": 0.056090774450348886,
        "steps_above_joint_vel_limit_mean": 0.02,
        "steps_above_joint_vel_limit_min": 0,
        "steps_above_joint_vel_limit_max": 1,
        "steps_above_3x_joint_vel_limit_mean": 0.0,
        "steps_above_3x_joint_vel_limit_min": 0,
        "steps_above_3x_joint_vel_limit_max": 0,
        "dist_to_desired_mean": 0.049468442747012585,
        "dist_to_desired_min": 0.008650405468946583,
        "dist_to_desired_max": 0.10346721207330589,
        "rot_dist_to_desired_mean": 0.0020687838030300286,
        "rot_dist_to_desired_min": 9.704532135000117e-07,
        "rot_dist_to_desired_max": 0.020546748255148604,
        "success_nojumps_mean": 0.08,
        "success_nojumps_min": "False",
        "success_nojumps_max": "True",
        "success_nojumps3x_mean": 0.1,
        "success_nojumps3x_min": "False",
        "success_nojumps3x_max": "True",
        "max_close_steps_reached_mean": 0.02,
        "max_close_steps_reached_min": 0.0,
        "max_close_steps_reached_max": 1.0,
        "vel_norm_mean": 0.09434394725392328,
        "vel_norm_min": 0.07471307288402709,
        "vel_norm_max": 0.1084414974626686,
        "episode_disc_return_mean": -6.296224568727722,
        "episode_disc_return_min": -13.902892799796001,
        "episode_disc_return_max": -2.1777648615438165
      },
      "hist_stats": {
        "episode_reward": [
          -14.482221059323559,
          -11.288525480127179,
          -17.25935021898782,
          -5.787917922221524,
          -17.991775071911558,
          -9.415373130899068,
          -9.601082555190349,
          -12.283426550077404,
          -12.325842906471859,
          -11.623301981991402,
          -10.911356262861856,
          -12.411759197699118,
          -45.92368692728085,
          -16.88600861150348,
          -8.951941803511602,
          -10.21678675516283,
          -3.6521449788367035,
          -10.031618137272014,
          -10.353065830974089,
          -14.02903047341922,
          -9.598277177266052,
          -24.27673973576146,
          -11.732761375318255,
          -11.515012890801685,
          -19.57599387958051,
          -15.06381303711716,
          -13.552207348540852,
          -14.771772736069446,
          -18.330485697917496,
          -13.105617543965977,
          -23.77470750944159,
          -47.41568113921456,
          -6.885856169000837,
          -18.2636739573558,
          -5.217632687582843,
          -20.141146356340506,
          -15.072423700109738,
          -40.817628018042335,
          -15.198260369678591,
          -10.329880593282013,
          -9.100392889532138,
          -11.687228190312256,
          -11.821040908658698,
          -9.191929023017567,
          -8.969622097517343,
          -10.349822957652036,
          -11.979792878077333,
          -4.410839560590242,
          -11.169334363110318,
          -13.737196319132927
        ],
        "episode_lengths": [
          93,
          118,
          88,
          82,
          63,
          38,
          98,
          52,
          122,
          63,
          86,
          37,
          273,
          207,
          175,
          91,
          121,
          68,
          62,
          118,
          65,
          210,
          94,
          47,
          176,
          111,
          170,
          156,
          203,
          136,
          77,
          428,
          110,
          112,
          105,
          84,
          190,
          125,
          112,
          85,
          54,
          54,
          96,
          72,
          74,
          71,
          92,
          139,
          59,
          157
        ]
      },
      "sampler_perf": {
        "mean_raw_obs_processing_ms": 3.195662806917737,
        "mean_inference_ms": 1.5138537316889198,
        "mean_action_processing_ms": 0.07565546702671716,
        "mean_env_wait_ms": 10.353821974534256,
        "mean_env_render_ms": 0.0
      },
      "off_policy_estimator": {}
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T00:45:49.719037+08:00

```json
{
  "time": "2026-10-12T00:45:49.719037+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T00:45:45.943982+08:00",
    "host_cpu_cores": 5.332160030170653,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 1529,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 3.9,
  "progress_latest": {
    "timesteps_total": "139000",
    "episodes_total": "1323",
    "time_total_s": "7598.459347724915",
    "training_iteration": "139"
  },
  "latest_evaluation": {
    "steps": 75000,
    "metrics": {
      "goal_reached_mean": 0.12,
      "ik_fails_mean": 17.06,
      "ik_zero_fail_mean": 0.14,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.54,
      "success_mean": 0.1,
      "vel_normed_avg_deviation_mean": 0.033540555346756575,
      "steps_above_joint_vel_limit_mean": 0.02,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.049468442747012585,
      "rot_dist_to_desired_mean": 0.0020687838030300286,
      "success_nojumps_mean": 0.08,
      "success_nojumps3x_mean": 0.1,
      "max_close_steps_reached_mean": 0.02,
      "vel_norm_mean": 0.09434394725392328,
      "episode_disc_return_mean": -6.296224568727722
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T01:10:56.416205+08:00

```json
{
  "time": "2026-10-12T01:10:56.416205+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T01:10:52.529123+08:00",
    "host_cpu_cores": 5.353114980826051,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 1830,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 4.0,
  "progress_latest": {
    "timesteps_total": "163000",
    "episodes_total": "1430",
    "time_total_s": "9101.064842700958",
    "training_iteration": "163"
  },
  "latest_evaluation": {
    "steps": 150000,
    "metrics": {
      "goal_reached_mean": 0.48,
      "ik_fails_mean": 8.32,
      "ik_zero_fail_mean": 0.54,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 3.02,
      "success_mean": 0.44,
      "vel_normed_avg_deviation_mean": 0.024884695726124288,
      "steps_above_joint_vel_limit_mean": 0.02,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.027066687246495663,
      "rot_dist_to_desired_mean": 0.002067453344133603,
      "success_nojumps_mean": 0.44,
      "success_nojumps3x_mean": 0.44,
      "max_close_steps_reached_mean": 0.02,
      "vel_norm_mean": 0.08427030201917006,
      "episode_disc_return_mean": -4.412864586579294
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T01:35:44.172872+08:00

```json
{
  "time": "2026-10-12T01:35:44.172872+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T01:35:44.124428+08:00",
    "host_cpu_cores": 6.0076050406963954,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 2128,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 0.2,
  "progress_latest": {
    "timesteps_total": "190000",
    "episodes_total": "1516",
    "time_total_s": "10582.94049501419",
    "training_iteration": "190"
  },
  "latest_evaluation": {
    "steps": 150000,
    "metrics": {
      "goal_reached_mean": 0.48,
      "ik_fails_mean": 8.32,
      "ik_zero_fail_mean": 0.54,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 3.02,
      "success_mean": 0.44,
      "vel_normed_avg_deviation_mean": 0.024884695726124288,
      "steps_above_joint_vel_limit_mean": 0.02,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.027066687246495663,
      "rot_dist_to_desired_mean": 0.002067453344133603,
      "success_nojumps_mean": 0.44,
      "success_nojumps3x_mean": 0.44,
      "max_close_steps_reached_mean": 0.02,
      "vel_norm_mean": 0.08427030201917006,
      "episode_disc_return_mean": -4.412864586579294
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T02:00:19.879479+08:00

```json
{
  "time": "2026-10-12T02:00:19.879479+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T02:00:15.638214+08:00",
    "host_cpu_cores": 5.360993242181361,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 2422,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 4.4,
  "progress_latest": {
    "timesteps_total": "217000",
    "episodes_total": "1583",
    "time_total_s": "12057.262030601501",
    "training_iteration": "217"
  },
  "latest_evaluation": {
    "steps": 150000,
    "metrics": {
      "goal_reached_mean": 0.48,
      "ik_fails_mean": 8.32,
      "ik_zero_fail_mean": 0.54,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 3.02,
      "success_mean": 0.44,
      "vel_normed_avg_deviation_mean": 0.024884695726124288,
      "steps_above_joint_vel_limit_mean": 0.02,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.027066687246495663,
      "rot_dist_to_desired_mean": 0.002067453344133603,
      "success_nojumps_mean": 0.44,
      "success_nojumps3x_mean": 0.44,
      "max_close_steps_reached_mean": 0.02,
      "vel_norm_mean": 0.08427030201917006,
      "episode_disc_return_mean": -4.412864586579294
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T02:24:56.419929+08:00

```json
{
  "time": "2026-10-12T02:24:56.419929+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T02:24:52.183175+08:00",
    "host_cpu_cores": 5.299990575225409,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 2717,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 4.3,
  "progress_latest": {
    "timesteps_total": "240000",
    "episodes_total": "1650",
    "time_total_s": "13524.263050079346",
    "training_iteration": "240"
  },
  "latest_evaluation": {
    "steps": 225000,
    "metrics": {
      "goal_reached_mean": 0.72,
      "ik_fails_mean": 4.48,
      "ik_zero_fail_mean": 0.76,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.16,
      "success_mean": 0.68,
      "vel_normed_avg_deviation_mean": 0.02435225940611539,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.011880063054388254,
      "rot_dist_to_desired_mean": 0.0013887404195431921,
      "success_nojumps_mean": 0.68,
      "success_nojumps3x_mean": 0.68,
      "max_close_steps_reached_mean": 0.08,
      "vel_norm_mean": 0.08228130083933113,
      "episode_disc_return_mean": -3.3115080634645904
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T02:50:01.195318+08:00

```json
{
  "time": "2026-10-12T02:50:01.195318+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T02:49:58.828713+08:00",
    "host_cpu_cores": 6.783641907396348,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 3018,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 2.5,
  "progress_latest": {
    "timesteps_total": "268000",
    "episodes_total": "1717",
    "time_total_s": "15053.223274946213",
    "training_iteration": "268"
  },
  "latest_evaluation": {
    "steps": 225000,
    "metrics": {
      "goal_reached_mean": 0.72,
      "ik_fails_mean": 4.48,
      "ik_zero_fail_mean": 0.76,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.16,
      "success_mean": 0.68,
      "vel_normed_avg_deviation_mean": 0.02435225940611539,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.011880063054388254,
      "rot_dist_to_desired_mean": 0.0013887404195431921,
      "success_nojumps_mean": 0.68,
      "success_nojumps3x_mean": 0.68,
      "max_close_steps_reached_mean": 0.08,
      "vel_norm_mean": 0.08228130083933113,
      "episode_disc_return_mean": -3.3115080634645904
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T03:14:42.264064+08:00

```json
{
  "time": "2026-10-12T03:14:42.264064+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T03:14:40.363934+08:00",
    "host_cpu_cores": 5.220221824237282,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 3314,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 2.0,
  "progress_latest": {
    "timesteps_total": "295000",
    "episodes_total": "1779",
    "time_total_s": "16524.63499355316",
    "training_iteration": "295"
  },
  "latest_evaluation": {
    "steps": 225000,
    "metrics": {
      "goal_reached_mean": 0.72,
      "ik_fails_mean": 4.48,
      "ik_zero_fail_mean": 0.76,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.16,
      "success_mean": 0.68,
      "vel_normed_avg_deviation_mean": 0.02435225940611539,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.011880063054388254,
      "rot_dist_to_desired_mean": 0.0013887404195431921,
      "success_nojumps_mean": 0.68,
      "success_nojumps3x_mean": 0.68,
      "max_close_steps_reached_mean": 0.08,
      "vel_norm_mean": 0.08228130083933113,
      "episode_disc_return_mean": -3.3115080634645904
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T03:39:42.821710+08:00

```json
{
  "time": "2026-10-12T03:39:42.821710+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T03:39:41.991171+08:00",
    "host_cpu_cores": 5.200603318250377,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 3614,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 0.9,
  "progress_latest": {
    "timesteps_total": "318000",
    "episodes_total": "1832",
    "time_total_s": "18007.577374219894",
    "training_iteration": "318"
  },
  "latest_evaluation": {
    "steps": 300000,
    "metrics": {
      "goal_reached_mean": 0.8,
      "ik_fails_mean": 2.28,
      "ik_zero_fail_mean": 0.88,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.42,
      "success_mean": 0.78,
      "vel_normed_avg_deviation_mean": 0.021311442956341176,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.008367605202007395,
      "rot_dist_to_desired_mean": 0.0008036682460191211,
      "success_nojumps_mean": 0.78,
      "success_nojumps3x_mean": 0.78,
      "max_close_steps_reached_mean": 0.08,
      "vel_norm_mean": 0.07669220315584542,
      "episode_disc_return_mean": -3.4532105644176876
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T04:04:56.016669+08:00

```json
{
  "time": "2026-10-12T04:04:56.016669+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T04:04:53.599919+08:00",
    "host_cpu_cores": 5.837559304992617,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 3916,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 2.5,
  "progress_latest": {
    "timesteps_total": "346000",
    "episodes_total": "1884",
    "time_total_s": "19538.385365009308",
    "training_iteration": "346"
  },
  "latest_evaluation": {
    "steps": 300000,
    "metrics": {
      "goal_reached_mean": 0.8,
      "ik_fails_mean": 2.28,
      "ik_zero_fail_mean": 0.88,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.42,
      "success_mean": 0.78,
      "vel_normed_avg_deviation_mean": 0.021311442956341176,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.008367605202007395,
      "rot_dist_to_desired_mean": 0.0008036682460191211,
      "success_nojumps_mean": 0.78,
      "success_nojumps3x_mean": 0.78,
      "max_close_steps_reached_mean": 0.08,
      "vel_norm_mean": 0.07669220315584542,
      "episode_disc_return_mean": -3.4532105644176876
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T04:29:48.846015+08:00

```json
{
  "time": "2026-10-12T04:29:48.846015+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T04:29:45.147882+08:00",
    "host_cpu_cores": 5.313723641620314,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 4214,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 3.8,
  "progress_latest": {
    "timesteps_total": "373000",
    "episodes_total": "1940",
    "time_total_s": "21024.025899410248",
    "training_iteration": "373"
  },
  "latest_evaluation": {
    "steps": 300000,
    "metrics": {
      "goal_reached_mean": 0.8,
      "ik_fails_mean": 2.28,
      "ik_zero_fail_mean": 0.88,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.42,
      "success_mean": 0.78,
      "vel_normed_avg_deviation_mean": 0.021311442956341176,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.008367605202007395,
      "rot_dist_to_desired_mean": 0.0008036682460191211,
      "success_nojumps_mean": 0.78,
      "success_nojumps3x_mean": 0.78,
      "max_close_steps_reached_mean": 0.08,
      "vel_norm_mean": 0.07669220315584542,
      "episode_disc_return_mean": -3.4532105644176876
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T04:54:06.400134+08:00

```json
{
  "time": "2026-10-12T04:54:06.400134+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T04:54:01.743228+08:00",
    "host_cpu_cores": 5.344056295551646,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 4505,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 4.8,
  "progress_latest": {
    "timesteps_total": "395000",
    "episodes_total": "1984",
    "time_total_s": "22475.761342525482",
    "training_iteration": "395"
  },
  "latest_evaluation": {
    "steps": 375000,
    "metrics": {
      "goal_reached_mean": 0.82,
      "ik_fails_mean": 2.78,
      "ik_zero_fail_mean": 0.86,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.06,
      "success_mean": 0.82,
      "vel_normed_avg_deviation_mean": 0.024080390383689972,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.008292705831835943,
      "rot_dist_to_desired_mean": 0.0009618834172853973,
      "success_nojumps_mean": 0.82,
      "success_nojumps3x_mean": 0.82,
      "max_close_steps_reached_mean": 0.06,
      "vel_norm_mean": 0.07797499038972037,
      "episode_disc_return_mean": -3.3599704318020738
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T05:18:16.942101+08:00

```json
{
  "time": "2026-10-12T05:18:16.942101+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T05:18:13.346530+08:00",
    "host_cpu_cores": 5.797334674377671,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 4795,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 3.7,
  "progress_latest": {
    "timesteps_total": "421000",
    "episodes_total": "2036",
    "time_total_s": "23913.974814414978",
    "training_iteration": "421"
  },
  "latest_evaluation": {
    "steps": 375000,
    "metrics": {
      "goal_reached_mean": 0.82,
      "ik_fails_mean": 2.78,
      "ik_zero_fail_mean": 0.86,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.06,
      "success_mean": 0.82,
      "vel_normed_avg_deviation_mean": 0.024080390383689972,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.008292705831835943,
      "rot_dist_to_desired_mean": 0.0009618834172853973,
      "success_nojumps_mean": 0.82,
      "success_nojumps3x_mean": 0.82,
      "max_close_steps_reached_mean": 0.06,
      "vel_norm_mean": 0.07797499038972037,
      "episode_disc_return_mean": -3.3599704318020738
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T05:42:36.118581+08:00

```json
{
  "time": "2026-10-12T05:42:36.118581+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T05:42:34.969758+08:00",
    "host_cpu_cores": 5.2140542920952475,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 5087,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 1.3,
  "progress_latest": {
    "timesteps_total": "448000",
    "episodes_total": "2084",
    "time_total_s": "25418.660576581955",
    "training_iteration": "448"
  },
  "latest_evaluation": {
    "steps": 375000,
    "metrics": {
      "goal_reached_mean": 0.82,
      "ik_fails_mean": 2.78,
      "ik_zero_fail_mean": 0.86,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.06,
      "success_mean": 0.82,
      "vel_normed_avg_deviation_mean": 0.024080390383689972,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.008292705831835943,
      "rot_dist_to_desired_mean": 0.0009618834172853973,
      "success_nojumps_mean": 0.82,
      "success_nojumps3x_mean": 0.82,
      "max_close_steps_reached_mean": 0.06,
      "vel_norm_mean": 0.07797499038972037,
      "episode_disc_return_mean": -3.3599704318020738
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T06:06:54.540054+08:00

```json
{
  "time": "2026-10-12T06:06:54.540054+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T06:06:51.548738+08:00",
    "host_cpu_cores": 5.269831296534824,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 5378,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 3.1,
  "progress_latest": {
    "timesteps_total": "469000",
    "episodes_total": "2127",
    "time_total_s": "26862.546402931213",
    "training_iteration": "469"
  },
  "latest_evaluation": {
    "steps": 450000,
    "metrics": {
      "goal_reached_mean": 0.8,
      "ik_fails_mean": 1.88,
      "ik_zero_fail_mean": 0.9,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.4,
      "success_mean": 0.8,
      "vel_normed_avg_deviation_mean": 0.025122022084969036,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.007120283859273197,
      "rot_dist_to_desired_mean": 0.0007090366689552507,
      "success_nojumps_mean": 0.8,
      "success_nojumps3x_mean": 0.8,
      "max_close_steps_reached_mean": 0.1,
      "vel_norm_mean": 0.06943413446841039,
      "episode_disc_return_mean": -3.7760719961667224
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T06:31:21.490172+08:00

```json
{
  "time": "2026-10-12T06:31:21.490172+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T06:31:18.015341+08:00",
    "host_cpu_cores": 5.2245718774548315,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 5671,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 3.6,
  "progress_latest": {
    "timesteps_total": "495000",
    "episodes_total": "2163",
    "time_total_s": "28317.41223716736",
    "training_iteration": "495"
  },
  "latest_evaluation": {
    "steps": 450000,
    "metrics": {
      "goal_reached_mean": 0.8,
      "ik_fails_mean": 1.88,
      "ik_zero_fail_mean": 0.9,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.4,
      "success_mean": 0.8,
      "vel_normed_avg_deviation_mean": 0.025122022084969036,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.007120283859273197,
      "rot_dist_to_desired_mean": 0.0007090366689552507,
      "success_nojumps_mean": 0.8,
      "success_nojumps3x_mean": 0.8,
      "max_close_steps_reached_mean": 0.1,
      "vel_norm_mean": 0.06943413446841039,
      "episode_disc_return_mean": -3.7760719961667224
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T06:55:40.799841+08:00

```json
{
  "time": "2026-10-12T06:55:40.799841+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T06:55:39.635173+08:00",
    "host_cpu_cores": 5.042631397065754,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 5963,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 1.3,
  "progress_latest": {
    "timesteps_total": "521000",
    "episodes_total": "2211",
    "time_total_s": "29772.646283626556",
    "training_iteration": "521"
  },
  "latest_evaluation": {
    "steps": 450000,
    "metrics": {
      "goal_reached_mean": 0.8,
      "ik_fails_mean": 1.88,
      "ik_zero_fail_mean": 0.9,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.4,
      "success_mean": 0.8,
      "vel_normed_avg_deviation_mean": 0.025122022084969036,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.007120283859273197,
      "rot_dist_to_desired_mean": 0.0007090366689552507,
      "success_nojumps_mean": 0.8,
      "success_nojumps3x_mean": 0.8,
      "max_close_steps_reached_mean": 0.1,
      "vel_norm_mean": 0.06943413446841039,
      "episode_disc_return_mean": -3.7760719961667224
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T07:20:04.157030+08:00

```json
{
  "time": "2026-10-12T07:20:04.157030+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T07:20:01.249068+08:00",
    "host_cpu_cores": 5.692733215991954,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 6255,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 3.0,
  "progress_latest": {
    "timesteps_total": "543000",
    "episodes_total": "2246",
    "time_total_s": "31257.756860256195",
    "training_iteration": "543"
  },
  "latest_evaluation": {
    "steps": 525000,
    "metrics": {
      "goal_reached_mean": 0.82,
      "ik_fails_mean": 1.6,
      "ik_zero_fail_mean": 0.92,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.0,
      "success_mean": 0.82,
      "vel_normed_avg_deviation_mean": 0.028203769993331646,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.007636553498463191,
      "rot_dist_to_desired_mean": 0.0008955188909505768,
      "success_nojumps_mean": 0.82,
      "success_nojumps3x_mean": 0.82,
      "max_close_steps_reached_mean": 0.1,
      "vel_norm_mean": 0.06948916807769252,
      "episode_disc_return_mean": -3.8018897364187705
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T07:44:28.868058+08:00

```json
{
  "time": "2026-10-12T07:44:28.868058+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T07:44:27.842278+08:00",
    "host_cpu_cores": 5.273686855993969,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 6548,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 1.1,
  "progress_latest": {
    "timesteps_total": "569000",
    "episodes_total": "2293",
    "time_total_s": "32707.704085588455",
    "training_iteration": "569"
  },
  "latest_evaluation": {
    "steps": 525000,
    "metrics": {
      "goal_reached_mean": 0.82,
      "ik_fails_mean": 1.6,
      "ik_zero_fail_mean": 0.92,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.0,
      "success_mean": 0.82,
      "vel_normed_avg_deviation_mean": 0.028203769993331646,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.007636553498463191,
      "rot_dist_to_desired_mean": 0.0008955188909505768,
      "success_nojumps_mean": 0.82,
      "success_nojumps3x_mean": 0.82,
      "max_close_steps_reached_mean": 0.1,
      "vel_norm_mean": 0.06948916807769252,
      "episode_disc_return_mean": -3.8018897364187705
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T08:08:53.572472+08:00

```json
{
  "time": "2026-10-12T08:08:53.572472+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T08:08:49.460694+08:00",
    "host_cpu_cores": 5.108897199786291,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 6840,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 4.2,
  "progress_latest": {
    "timesteps_total": "595000",
    "episodes_total": "2346",
    "time_total_s": "34167.385675907135",
    "training_iteration": "595"
  },
  "latest_evaluation": {
    "steps": 525000,
    "metrics": {
      "goal_reached_mean": 0.82,
      "ik_fails_mean": 1.6,
      "ik_zero_fail_mean": 0.92,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.0,
      "success_mean": 0.82,
      "vel_normed_avg_deviation_mean": 0.028203769993331646,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.007636553498463191,
      "rot_dist_to_desired_mean": 0.0008955188909505768,
      "success_nojumps_mean": 0.82,
      "success_nojumps3x_mean": 0.82,
      "max_close_steps_reached_mean": 0.1,
      "vel_norm_mean": 0.06948916807769252,
      "episode_disc_return_mean": -3.8018897364187705
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T08:33:56.074763+08:00

```json
{
  "time": "2026-10-12T08:33:56.074763+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T08:33:55.956198+08:00",
    "host_cpu_cores": 5.45267127592709,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 7141,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 0.2,
  "progress_latest": {
    "timesteps_total": "618000",
    "episodes_total": "2397",
    "time_total_s": "35683.612397909164",
    "training_iteration": "618"
  },
  "latest_evaluation": {
    "steps": 600000,
    "metrics": {
      "goal_reached_mean": 0.78,
      "ik_fails_mean": 1.64,
      "ik_zero_fail_mean": 0.9,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.06,
      "success_mean": 0.74,
      "vel_normed_avg_deviation_mean": 0.030402060967602788,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.009150503134068674,
      "rot_dist_to_desired_mean": 0.001280285810897703,
      "success_nojumps_mean": 0.74,
      "success_nojumps3x_mean": 0.74,
      "max_close_steps_reached_mean": 0.16,
      "vel_norm_mean": 0.07918512619357254,
      "episode_disc_return_mean": -3.431294879109511
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T08:59:46.261456+08:00

```json
{
  "time": "2026-10-12T08:59:46.261456+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T08:59:42.655727+08:00",
    "host_cpu_cores": 5.034409007988929,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 7450,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 3.7,
  "progress_latest": {
    "timesteps_total": "645000",
    "episodes_total": "2456",
    "time_total_s": "37199.99521327019",
    "training_iteration": "645"
  },
  "latest_evaluation": {
    "steps": 600000,
    "metrics": {
      "goal_reached_mean": 0.78,
      "ik_fails_mean": 1.64,
      "ik_zero_fail_mean": 0.9,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.06,
      "success_mean": 0.74,
      "vel_normed_avg_deviation_mean": 0.030402060967602788,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.009150503134068674,
      "rot_dist_to_desired_mean": 0.001280285810897703,
      "success_nojumps_mean": 0.74,
      "success_nojumps3x_mean": 0.74,
      "max_close_steps_reached_mean": 0.16,
      "vel_norm_mean": 0.07918512619357254,
      "episode_disc_return_mean": -3.431294879109511
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T09:25:51.569351+08:00

```json
{
  "time": "2026-10-12T09:25:51.569351+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T09:25:49.431085+08:00",
    "host_cpu_cores": 10.108759238874036,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 7763,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 2.3,
  "progress_latest": {
    "timesteps_total": "673000",
    "episodes_total": "2508",
    "time_total_s": "38779.263722896576",
    "training_iteration": "673"
  },
  "latest_evaluation": {
    "steps": 600000,
    "metrics": {
      "goal_reached_mean": 0.78,
      "ik_fails_mean": 1.64,
      "ik_zero_fail_mean": 0.9,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.06,
      "success_mean": 0.74,
      "vel_normed_avg_deviation_mean": 0.030402060967602788,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.009150503134068674,
      "rot_dist_to_desired_mean": 0.001280285810897703,
      "success_nojumps_mean": 0.74,
      "success_nojumps3x_mean": 0.74,
      "max_close_steps_reached_mean": 0.16,
      "vel_norm_mean": 0.07918512619357254,
      "episode_disc_return_mean": -3.431294879109511
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T09:50:53.252594+08:00

```json
{
  "time": "2026-10-12T09:50:53.252594+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T09:50:51.104873+08:00",
    "host_cpu_cores": 5.483816174388978,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 8063,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 2.3,
  "progress_latest": {
    "timesteps_total": "696000",
    "episodes_total": "2555",
    "time_total_s": "40269.10205101967",
    "training_iteration": "696"
  },
  "latest_evaluation": {
    "steps": 675000,
    "metrics": {
      "goal_reached_mean": 0.84,
      "ik_fails_mean": 2.04,
      "ik_zero_fail_mean": 0.86,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.02,
      "success_mean": 0.82,
      "vel_normed_avg_deviation_mean": 0.035623145322584156,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.007339885397919272,
      "rot_dist_to_desired_mean": 0.001288230810931694,
      "success_nojumps_mean": 0.82,
      "success_nojumps3x_mean": 0.82,
      "max_close_steps_reached_mean": 0.06,
      "vel_norm_mean": 0.09361099400217718,
      "episode_disc_return_mean": -2.735401537774041
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T10:16:30.023955+08:00

```json
{
  "time": "2026-10-12T10:16:30.023955+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T10:16:27.879169+08:00",
    "host_cpu_cores": 5.582178653344645,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 8370,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 2.3,
  "progress_latest": {
    "timesteps_total": "723000",
    "episodes_total": "2629",
    "time_total_s": "41793.40927577019",
    "training_iteration": "723"
  },
  "latest_evaluation": {
    "steps": 675000,
    "metrics": {
      "goal_reached_mean": 0.84,
      "ik_fails_mean": 2.04,
      "ik_zero_fail_mean": 0.86,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.02,
      "success_mean": 0.82,
      "vel_normed_avg_deviation_mean": 0.035623145322584156,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.007339885397919272,
      "rot_dist_to_desired_mean": 0.001288230810931694,
      "success_nojumps_mean": 0.82,
      "success_nojumps3x_mean": 0.82,
      "max_close_steps_reached_mean": 0.06,
      "vel_norm_mean": 0.09361099400217718,
      "episode_disc_return_mean": -2.735401537774041
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。

## 30分钟核查 2026-10-12T10:41:52.161176+08:00

```json
{
  "time": "2026-10-12T10:41:52.161176+08:00",
  "status": "active",
  "rule": "D11 CPU仅告警",
  "pids": {
    "monitor": 2238780,
    "posttrain": 2243657,
    "train": 34861
  },
  "host_pids_alive": {
    "monitor": true,
    "posttrain": true
  },
  "train_ps": "    PID COMMAND\n  34861 /opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env pr2 --total_steps 1000000\n",
  "cpu_latest": {
    "time": "2026-10-12T10:41:49.590143+08:00",
    "host_cpu_cores": 5.953067571388182,
    "interval_s": 5,
    "host_logical_cpus": 64
  },
  "cpu_samples": 8674,
  "cpu_max": 17.351935250212577,
  "cpu_age_s": 2.7,
  "progress_latest": {
    "timesteps_total": "749000",
    "episodes_total": "2691",
    "time_total_s": "43266.831818819046",
    "training_iteration": "749"
  },
  "latest_evaluation": {
    "steps": 675000,
    "metrics": {
      "goal_reached_mean": 0.84,
      "ik_fails_mean": 2.04,
      "ik_zero_fail_mean": 0.86,
      "ik_b100_mean": 1.0,
      "base_collisions_mean": 0.02,
      "success_mean": 0.82,
      "vel_normed_avg_deviation_mean": 0.035623145322584156,
      "steps_above_joint_vel_limit_mean": 0.0,
      "steps_above_3x_joint_vel_limit_mean": 0.0,
      "dist_to_desired_mean": 0.007339885397919272,
      "rot_dist_to_desired_mean": 0.001288230810931694,
      "success_nojumps_mean": 0.82,
      "success_nojumps3x_mean": 0.82,
      "max_close_steps_reached_mean": 0.06,
      "vel_norm_mean": 0.09361099400217718,
      "episode_disc_return_mean": -2.735401537774041
    }
  },
  "exit_code": null,
  "alert": false,
  "posttrain_status": null
}
```

来源[SRC0219](../../../../SOURCES.md#src-0219)及父D11变更证据monitor_D11_change.json。训练与后处理未完成；继续只读监督，CPU告警不停止。推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认；实际派发gpt-6.1-sol/low。
