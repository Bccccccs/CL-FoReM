#!/usr/bin/env bash
set -euo pipefail
scale=${1:?100,1000,9600}
run_id=${2:?unique run suffix}
container="mmhusky-p1-check-${scale}-${run_id}"
# Only this new offline container is limited; existing ROS containers stay untouched.
sg docker -c "docker run --name '$container' --init --network none --memory=16g --memory-swap=16g --shm-size=256m --runtime=nvidia -e NVIDIA_VISIBLE_DEVICES=nvidia.com/gpu=0 -e P0_IMAGE_ID=sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430 --mount type=bind,src=/home/ybc/projects/mm_husky_ws,dst=/root/mm_husky_ws mm_husky:node01 python3 -u /root/mm_husky_ws/src/modulation_rl/scripts/wm_resource_check.py --dataset /root/mm_husky_ws/results/p1a-20260923/dataset-v2-10k/dataset.json --encoder-checkpoint /root/mm_husky_ws/results/p1a-20260923/policy-100k.pt --episodes '$scale' --output '/root/mm_husky_ws/results/p1-fix-20260928/check-${scale}-${run_id}'"
