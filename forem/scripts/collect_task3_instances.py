#!/usr/bin/env python3
"""task3.5: record the FULL episode instances (start pose, goal, every obstacle) of a fixed seed list, twice, and check that both
passes agree (seed => identical episode). The file is hashed into the execution freeze; evaluation/Task4 must use these seeds."""
import ray  # noqa: F401,E402
import torch  # noqa: F401,E402
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import task3_env as T  # noqa: E402

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=list(range(101, 111)))
    a = ap.parse_args()
    res = os.environ.get("FOREM_RES_DIR", "results/task3/instances")
    os.makedirs(res, exist_ok=True)
    env = T.Task3Env(seed=0)
    passes = []
    for _ in range(2):
        specs = {}
        for s in a.seeds:
            env.reset(seed=s)
            specs[str(s)] = env.episode_spec
        passes.append(specs)
    env.close()
    same = all(passes[0][k]["hash"] == passes[1][k]["hash"] for k in passes[0])
    distinct = len({v["hash"] for v in passes[0].values()}) == len(a.seeds)
    json.dump(dict(seeds=a.seeds, episodes=passes[0], second_pass_hashes={k: v["hash"] for k, v in passes[1].items()},
                   identical_on_repeat=same, all_distinct=distinct), open(os.path.join(res, "episode_instances.json"), "w"), indent=1)
    print("PASS identical_on_repeat" if same else "FAIL identical_on_repeat")
    print("PASS all_distinct" if distinct else "FAIL all_distinct")
    return 0 if same and distinct else 1

if __name__ == "__main__":
    sys.exit(main())
