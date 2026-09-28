#!/usr/bin/env bash
# STAGE0-028 R0-1: WM 补种子22。仿 20260928-p1-retrain-launch.sh，仅改容器名/GPU索引/R0_SEED。
set -euo pipefail
OUT=results/p1-retrain-20260928/diagnostic-s22
sg docker -c 'docker create --name mmhusky-r0-wm-s22 --init --network none --memory=16g --memory-swap=16g --shm-size=256m --runtime=nvidia -e NVIDIA_VISIBLE_DEVICES=nvidia.com/gpu=1 -e P0_TASK_ID=STAGE0-028-R0-1 -e P0_IMAGE_ID=sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430 -e R0_SEED=22 --mount type=bind,src=/home/ybc/projects/CL-FoReM,dst=/root/mm_husky_ws mm_husky:node01 python3 -u /root/mm_husky_ws/doc/agent_logs/20260928-stage0-r01-runner.py'
sg docker -c 'docker inspect mmhusky-r0-wm-s22' > "$OUT/container-before.json"
python3 - "$OUT/container-before.json" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))[0]
assert x['HostConfig']['Memory']==17179869184
assert x['HostConfig']['MemorySwap']==17179869184
assert x['HostConfig']['NetworkMode']=='none'
assert x['Image']=='sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430'
print('isolation verified before start',flush=True)
PY
set +e
sg docker -c 'docker start -a mmhusky-r0-wm-s22' > "$OUT/container-stdout.log" 2>&1
code=$?
sg docker -c 'docker inspect mmhusky-r0-wm-s22' > "$OUT/container-after.json"
printf '%s\n' "$code" > "$OUT/launcher-exit-code.txt"
exit "$code"
