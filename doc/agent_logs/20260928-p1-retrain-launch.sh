#!/usr/bin/env bash
set -euo pipefail
sg docker -c 'docker create --name mmhusky-p1-trainval-1000-r1 --init --network none --memory=16g --memory-swap=16g --shm-size=256m --runtime=nvidia -e NVIDIA_VISIBLE_DEVICES=nvidia.com/gpu=0 -e P0_TASK_ID=P1-RETRAIN-028 -e P0_IMAGE_ID=sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430 --mount type=bind,src=/home/ybc/projects/mm_husky_ws,dst=/root/mm_husky_ws mm_husky:node01 python3 -u /root/mm_husky_ws/doc/agent_logs/20260928-p1-retrain-runner.py'
sg docker -c 'docker inspect mmhusky-p1-trainval-1000-r1' > results/p1-retrain-20260928/diagnostic-r1/container-before.json
python3 - <<'PY'
import json
x=json.load(open('results/p1-retrain-20260928/diagnostic-r1/container-before.json'))[0]
assert x['HostConfig']['Memory']==17179869184
assert x['HostConfig']['MemorySwap']==17179869184
assert x['HostConfig']['NetworkMode']=='none'
assert x['Image']=='sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430'
print('isolation verified before start',flush=True)
PY
set +e
sg docker -c 'docker start -a mmhusky-p1-trainval-1000-r1'
code=$?
sg docker -c 'docker inspect mmhusky-p1-trainval-1000-r1' > results/p1-retrain-20260928/diagnostic-r1/container-after.json
printf '%s\n' "$code" > results/p1-retrain-20260928/diagnostic-r1/launcher-exit-code.txt
exit "$code"
