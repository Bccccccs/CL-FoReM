#!/usr/bin/env bash
# PLANNED ONLY: next 1000-episode train/val diagnostic; not run by P1-FIX-028.
set -euo pipefail
run_id=${1:?supply a fresh run id, e.g. r1}
[[ "$run_id" =~ ^[a-zA-Z0-9_-]+$ ]] || exit 2
# Confirm >=32GiB host headroom, free GPU0, output absent, and frozen protocol hashes first.
sg docker -c "docker run --name 'mmhusky-p1-trainval-1000-${run_id}' --init --network none --memory=16g --memory-swap=16g --shm-size=256m --runtime=nvidia -e NVIDIA_VISIBLE_DEVICES=nvidia.com/gpu=0 --mount type=bind,src=/home/ybc/projects/mm_husky_ws,dst=/root/mm_husky_ws mm_husky:node01 python3 -u /root/mm_husky_ws/src/modulation_rl/scripts/wm/train_offline.py --dataset /root/mm_husky_ws/results/p1-retrain-20260928/protocol-1000/dataset.json --encoder-checkpoint /root/mm_husky_ws/results/p1a-20260923/policy-100k.pt --cache-dir /root/mm_husky_ws/results/p1-retrain-20260928/feature-cache --encode-batch 128 --output '/root/mm_husky_ws/results/p1-retrain-20260928/trainval-1000-${run_id}' --hidden 64 --lr 3e-4 --weight-decay 1e-3 --batch 512 --epochs 200 --patience 20 --seed 11 --device cuda"
