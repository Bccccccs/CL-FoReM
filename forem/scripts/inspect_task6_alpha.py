#!/usr/bin/env python3
"""Read-only: print alpha/log_alpha/update_count/lr of the latest checkpoint of the given task6 runs. usage: inspect_task6_alpha.py RUN_ID..."""
import ray  # noqa: F401
import json, sys
from pathlib import Path
import torch
R = Path("/root/mm_husky_ws/results/task6")
for rid in sys.argv[1:]:
    ck = R / rid / "ckpt"
    try:
        lat = json.load(open(ck / "latest.json"))
        s = torch.load(ck / lat["state"], map_location="cpu", weights_only=False)
        a = s["agent"]
        print(rid, "step", lat["step"], "updates", a["update_count"], "alpha", round(a["alpha"], 4), "log_alpha", float(a["log_alpha"]), "auto_ent", a["automatic_entropy_tuning"],
              "lr(critic,policy,alpha)", [g["lr"] for g in (a["critic_optim"]["param_groups"][0], a["policy_optim"]["param_groups"][0], a["alpha_optim"]["param_groups"][0])], a.get("d14"))
    except Exception as e:
        print(rid, "err", e)
