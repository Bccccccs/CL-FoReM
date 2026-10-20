#!/usr/bin/env python3
"""Plain-SAC entry for the migrated Husky core (task3.4). NOT the reference main.py.

Differences from the reference main.py, all deliberate (see doc/tasks/task3/task3.4/RESULTS.md):
  * uses SAC.update_parameters (ordinary SAC update); no prior agent and no frozen-checkpoint loading (the reference main.py's modified update);
  * no hardcoded reference checkpoint paths; checkpoints are written/read only at paths given on the command line and carry a
    contract (obs/action shapes, config + source hashes); a checkpoint without or with a different contract is REFUSED;
  * explicit budgets: --steps and --max-wall-s are mandatory for train; no unbounded itertools.count() loop; no 5,000,001-step default;
  * mode smoke = tiny train + inference->env->replay->update->save->load->deterministic-eval round trip (an interface check,
    never evidence of learning); mode eval = checkpoint-checked deterministic episodes.

The data semantics follow main.py: memory.push(map, rob_state, action, reward, next_map, next_rob_state, mask) with mask = float(not done)
for every done (truncation is NOT bootstrapped); the first `random_warmup_steps` actions are uniform random.
"""
import ray  # noqa: F401  -- must stay first (see task3_env.py)
import torch

import argparse
import copy
import datetime
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
FOREM_ROOT = HERE.parent
CONFIG_DIR = FOREM_ROOT / "config" / "task3"
SCRIPTS_DIR = FOREM_ROOT / "src" / "modulation_rl" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import task3_identity as ID  # noqa: E402  (stdlib only; scripts dir was put on sys.path above)

CONTRACT_SCHEMA = 2                # schema 1 (learning-module hashes only, T3-A01) is refused, never upgraded
CONTRACT_KEYS = ("schema", "obs_robot_dim", "map_shape", "action_dim", "action_low", "action_high", "update_function",
                 "sac_config_sha256", "task_contract_sha256", "source_sha256", "pose_source", "semantic_identity")
STEP_CAP_DEFAULT = 2000          # Task3 is an interface migration: larger budgets need an explicit --step-cap


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_sac_config(path=None):
    path = Path(path) if path else CONFIG_DIR / "sac.yaml"
    cfg = yaml.safe_load(open(path, encoding="utf-8"))
    if cfg.get("schema") != 1:
        raise ValueError("sac config schema must be 1")
    if cfg["algorithm"]["update_function"] != "update_parameters" or cfg["algorithm"].get("prior_agent") not in (None, "none"):
        raise ValueError("this entry only supports the plain update_parameters without a prior agent")
    return cfg, sha256_file(path)


def resolve_device(requested="auto"):
    """Prefer CUDA when available; preserve an explicit device override."""
    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return str(torch.device(requested))


def build_sac_args(cfg, device, batch_size=None):
    """The dict SAC.__init__ reads: gamma, tau, initial_alpha, model.custom_model_config.post_fcnet_hiddens (+ device)."""
    h = cfg["hyper"]
    return dict(gamma=h["gamma"], tau=h["tau"], initial_alpha=h["initial_alpha"], device=device,
                train_batch_size=batch_size or h["batch_size"],
                model=dict(custom_model_config=dict(post_fcnet_hiddens=list(cfg["network"]["fcnet_hiddens"]))))


def make_mask(done, truncated=False):
    """Reference semantics (main.py): mask = float(not done) for EVERY done, including truncation/time-limit-like ends."""
    return float(not done)


def source_hashes(base=None):
    base = Path(base) if base else SCRIPTS_DIR
    files = ["sac.py", "model.py", "replay_memory.py", "utils.py", "modulation/models/mapencoder.py"]
    return {f: sha256_file(base / f) for f in files}


def make_contract(obs_space, action_space, sac_cfg_sha, pose_source="gazebo_reference", root=None, ros_share=None):
    """`root` is the FoReM tree the contract is computed from (default: this checkout); tests pass a modified copy. The contract carries, besides
    the shapes/configs, the semantic identity of the ACTUAL environment/task/control/model/config files (task3_identity, T3-A01)."""
    robot_space, map_space = obs_space[0], obs_space[1]
    root = Path(root) if root else FOREM_ROOT
    return dict(schema=CONTRACT_SCHEMA, obs_robot_dim=int(robot_space.shape[0]), map_shape=[int(x) for x in map_space.shape],
                action_dim=int(action_space.shape[0]), action_low=[float(x) for x in action_space.low],
                action_high=[float(x) for x in action_space.high], update_function="update_parameters",
                sac_config_sha256=sac_cfg_sha, task_contract_sha256=sha256_file(root / "config" / "task3" / "task_contract.yaml"),
                source_sha256=source_hashes(root / "src" / "modulation_rl" / "scripts"), pose_source=pose_source,
                semantic_identity=ID.semantic_identity(root, ros_share or ID.ROS_SHARE))


def save_checkpoint_with_contract(agent, path, contract, meta=None):
    """Original SAC.save_checkpoint file (policy/critic/critic_target/optimizers) + an extra `contract` entry (primitives only)."""
    path = str(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    agent.save_checkpoint("task3", ckpt_path=path)               # reference function, unchanged
    ck = torch.load(path)                                        # weights_only=True default: tensors + primitives
    ck["contract"] = dict(contract)
    ck["meta"] = dict(meta or {}, created=datetime.datetime.now().astimezone().isoformat(), torch=str(torch.__version__))
    torch.save(ck, path)
    return path


def check_contract(found, expected):
    diffs = [k for k in CONTRACT_KEYS if found.get(k) != expected.get(k)]
    if "semantic_identity" in diffs:
        diffs.remove("semantic_identity")
        diffs += ["semantic_identity[" + ",".join(ID.identity_diffs(found.get("semantic_identity"), expected.get("semantic_identity"))) + "]"]
    return diffs


def load_checkpoint_checked(agent, path, expected_contract, evaluate=False):
    """Refuses (ValueError) a checkpoint with no contract or a different obs/action/config/source contract; otherwise delegates to
    SAC.load_checkpoint (reference function)."""
    ck = torch.load(str(path))
    c = ck.get("contract")
    if not isinstance(c, dict):
        raise ValueError("checkpoint has no task3 contract (legacy/foreign checkpoints are not loaded)")
    if c.get("schema") != CONTRACT_SCHEMA or not isinstance(c.get("semantic_identity"), dict):
        raise ValueError("checkpoint contract lacks the full semantic identity (schema %r, need %d): refused, legacy contracts are not upgraded"
                         % (c.get("schema"), CONTRACT_SCHEMA))
    diffs = check_contract(c, expected_contract)
    if diffs:
        raise ValueError("checkpoint contract mismatch: " + ", ".join(diffs))
    agent.load_checkpoint(str(path), evaluate=evaluate)
    return ck.get("meta", {})


def finite_transition(state, action, reward, next_state, mask):
    return (all(np.all(np.isfinite(x)) for x in (state[0], state[1], action, next_state[0], next_state[1]))
            and math.isfinite(reward) and mask in (0.0, 1.0))


class Budget:
    def __init__(self, steps, max_wall_s):
        if steps is None or max_wall_s is None or steps <= 0 or max_wall_s <= 0:
            raise ValueError("train requires explicit positive --steps and --max-wall-s")
        self.steps, self.max_wall_s, self.t0 = int(steps), float(max_wall_s), time.time()

    def exhausted(self, n):
        return n >= self.steps or (time.time() - self.t0) >= self.max_wall_s


def policy_delta(a, b):
    return float(sum((x - y).pow(2).sum().item() for x, y in zip(a.parameters(), b)) ** 0.5)


def run_train(env, agent, memory, cfg, budget, rng, log, batch_size):
    """Collect + plain updates under an explicit budget. Returns counters. Mirrors the reference loop structure (random warmup, then
    policy actions; one update per step once the buffer exceeds the batch size), without evaluation/checkpoint side effects."""
    warm = int(cfg["smoke_budget"]["random_warmup_steps"])
    n = updates = episodes = 0
    losses = []
    state = env.reset(seed=int(rng.randint(1 << 30)))
    ep_steps = 0
    while not budget.exhausted(n):
        action = rng.uniform(-1, 1, size=env.action_space.shape).astype(np.float32) if n < warm else agent.select_action(state)
        next_state, reward, done, info = env.step(action)
        mask = make_mask(done, info.get("truncated", False))
        if not finite_transition(state, action, reward, next_state, mask):
            raise RuntimeError("non-finite or malformed transition")
        memory.push(state[1], state[0], action, reward, next_state[1], next_state[0], mask)
        log.append(dict(step=n, done=bool(done), terminated=info["terminated"], truncated=info["truncated"], mask=mask, reward=float(reward)))
        n += 1
        ep_steps += 1
        if len(memory) > batch_size:
            l1, l2, lp, la, alpha = agent.update_parameters(memory, batch_size, updates)
            losses.append([l1, l2, lp, la, alpha])
            updates += 1
        state = next_state
        if done:
            episodes += 1
            state = env.reset(seed=int(rng.randint(1 << 30)))
            ep_steps = 0
    return dict(steps=n, updates=updates, episodes_finished=episodes, losses=losses)


def run_eval(env, agent, episodes, max_steps, seed):
    out = []
    for ep in range(episodes):
        state = env.reset(seed=seed + ep)
        done, n, ret, info = False, 0, 0.0, {}
        while not done and n < max_steps:
            action = agent.select_action(state, eval=True)
            state, r, done, info = env.step(action)
            ret += r
            n += 1
        out.append(dict(episode=ep, steps=n, done=bool(done), return_=ret, success=info.get("success"), truncated=info.get("truncated"),
                        ee_done=info.get("ee_done"), nr_kin_failures=info.get("nr_kin_failures"), nr_base_collisions=info.get("nr_base_collisions")))
    return out


def main():
    from replay_memory import ReplayMemory
    from sac import SAC
    import task3_env as T

    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["smoke", "train", "eval"])
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="auto", help="auto: use CUDA when available, otherwise CPU; explicit cpu/cuda[:index] overrides")
    ap.add_argument("--config", default=None)
    ap.add_argument("--steps", type=int, default=None, help="train: environment steps (mandatory)")
    ap.add_argument("--max-wall-s", type=float, default=None, help="train: wall-clock cap in seconds (mandatory)")
    ap.add_argument("--step-cap", type=int, default=STEP_CAP_DEFAULT, help="refuse train budgets above this (Task3 is an interface migration)")
    ap.add_argument("--batch-size", type=int, default=None)
    ap.add_argument("--checkpoint", default=None, help="eval: checkpoint to load; train: where to save at the end")
    ap.add_argument("--episodes", type=int, default=1)
    ap.add_argument("--max-steps-per-episode", type=int, default=60)
    a = ap.parse_args()
    requested_device = a.device
    a.device = resolve_device(requested_device)
    res_dir = Path(os.environ.get("FOREM_RES_DIR", Path("results/task3") / a.run_id))
    res_dir.mkdir(parents=True, exist_ok=True)
    cfg, cfg_sha = load_sac_config(a.config)
    batch = a.batch_size or int(cfg["smoke_budget"]["batch_size"] if a.mode == "smoke" else cfg["hyper"]["batch_size"])
    rng = np.random.RandomState(a.seed)
    torch.manual_seed(a.seed)
    np.random.seed(a.seed)

    env = T.Task3Env(seed=a.seed)
    contract = make_contract(env.observation_space, env.action_space, cfg_sha)
    sac_args = build_sac_args(cfg, a.device, batch)
    num_steps = int(cfg["smoke_budget"]["num_steps_lr_horizon"])
    summary = dict(run_id=a.run_id, mode=a.mode, device=a.device, requested_device=requested_device, seed=a.seed, batch_size=batch, config_sha256=cfg_sha, contract=contract,
                   update_function="update_parameters", verdicts={})
    V = summary["verdicts"]

    if a.mode == "eval":
        if not a.checkpoint:
            raise SystemExit("eval needs --checkpoint")
        agent = SAC(env.observation_space, env.action_space, int(cfg["hyper"]["target_update_interval"]), sac_args, num_steps)
        meta = load_checkpoint_checked(agent, a.checkpoint, contract, evaluate=True)
        devs = sorted({str(p.device) for m in (agent.policy, agent.critic, agent.critic_target) for p in m.parameters()})
        summary["tensor_devices"] = devs
        V["networks_on_requested_device"] = all(torch.device(d).type == torch.device(a.device).type for d in devs)
        eps = run_eval(env, agent, a.episodes, a.max_steps_per_episode, a.seed)
        summary.update(episodes=eps, checkpoint_meta=meta)
        V["eval_ran"] = len(eps) == a.episodes
    else:
        if a.mode == "train":
            if a.steps and a.steps > a.step_cap:
                raise SystemExit(f"refused: --steps {a.steps} exceeds --step-cap {a.step_cap}")
            budget = Budget(a.steps, a.max_wall_s)
        else:
            budget = Budget(int(cfg["smoke_budget"]["random_warmup_steps"]) + 12, 900)
        memory = ReplayMemory(int(cfg["replay"]["capacity"]), a.seed)
        agent = SAC(env.observation_space, env.action_space, int(cfg["hyper"]["target_update_interval"]), sac_args, num_steps)
        before = [p.detach().clone() for p in agent.policy.parameters()]
        tgt_before = [p.detach().clone() for p in agent.critic_target.parameters()]
        log = []
        t0 = time.time()
        c = run_train(env, agent, memory, cfg, budget, rng, log, batch)
        summary.update(collect_and_update=dict(steps=c["steps"], updates=c["updates"], episodes_finished=c["episodes_finished"],
                                               wall_s=time.time() - t0, buffer=len(memory)))
        L = np.array(c["losses"]) if c["losses"] else np.zeros((0, 5))
        summary["losses"] = dict(first=L[0].tolist() if len(L) else None, last=L[-1].tolist() if len(L) else None)
        V["transitions_collected"] = c["steps"] >= 1 and len(memory) == c["steps"]
        V["plain_updates_ran"] = c["updates"] >= 1
        V["losses_finite"] = bool(len(L)) and bool(np.all(np.isfinite(L)))
        devs = sorted({str(p.device) for m in (agent.policy, agent.critic, agent.critic_target) for p in m.parameters()})
        summary["tensor_devices"] = devs                      # the ACTUAL device of every network tensor, not the requested string
        V["networks_on_requested_device"] = all(torch.device(d).type == torch.device(a.device).type for d in devs)
        V["policy_params_changed"] = policy_delta(agent.policy, before) > 0.0
        V["critic_target_soft_updated"] = policy_delta(agent.critic_target, tgt_before) > 0.0
        V["mask_matches_reference_for_every_done"] = all(r["mask"] == float(not r["done"]) for r in log)
        summary["done_flags"] = dict(n_done=sum(r["done"] for r in log), n_truncated=sum(r["truncated"] for r in log), n_terminated=sum(r["terminated"] for r in log))
        if a.mode == "train" and a.checkpoint:
            save_checkpoint_with_contract(agent, a.checkpoint, contract, meta=dict(steps=c["steps"], updates=c["updates"], seed=a.seed))
        if a.mode == "smoke":
            ckpt = res_dir / "checkpoints" / "smoke_ckpt.pt"
            save_checkpoint_with_contract(agent, ckpt, contract, meta=dict(steps=c["steps"], updates=c["updates"], seed=a.seed))
            summary["checkpoint"] = dict(path=str(ckpt), sha256=sha256_file(ckpt), bytes=ckpt.stat().st_size)
            agent2 = SAC(env.observation_space, env.action_space, int(cfg["hyper"]["target_update_interval"]), sac_args, num_steps)
            load_checkpoint_checked(agent2, ckpt, contract, evaluate=True)
            devs2 = sorted({str(p.device) for p in agent2.policy.parameters()})
            summary["loaded_agent_policy_devices"] = devs2
            V["loaded_policy_on_requested_device"] = all(torch.device(d).type == torch.device(a.device).type for d in devs2)
            agent.policy.eval()
            idx = [0, len(memory) // 2, len(memory) - 1]
            diffs = []
            for i in idx:
                st = (memory.buffer[i][1], memory.buffer[i][0])
                a1, a2 = agent.select_action(st, eval=True), agent2.select_action(st, eval=True)
                diffs.append(float(np.abs(a1 - a2).max()))
            V["checkpoint_roundtrip_deterministic_action"] = max(diffs) <= 1e-6
            summary["roundtrip_max_action_diff"] = max(diffs)
            # wrong contracts are refused
            bad = {}
            for name, mut in dict(obs_dim=dict(obs_robot_dim=40), action_dim=dict(action_dim=2), map_shape=dict(map_shape=[64, 64, 1]),
                                  sac_config=dict(sac_config_sha256="0" * 64), task=dict(task_contract_sha256="0" * 64),
                                  update_fn=dict(update_function="other_update"), pose=dict(pose_source="estimator")).items():
                try:
                    load_checkpoint_checked(agent2, ckpt, dict(contract, **mut))
                    bad[name] = "accepted"
                except ValueError:
                    bad[name] = "refused"
            # one changed semantic-identity group (environment/task/control, robot model, task3 config, system model package) is refused
            for g in [g for g, v in contract["semantic_identity"]["groups"].items() if v != "absent"]:
                ident = copy.deepcopy(contract["semantic_identity"])
                ident["groups"][g] = dict(ident["groups"][g], sha256="0" * 64)
                try:
                    load_checkpoint_checked(agent2, ckpt, dict(contract, semantic_identity=ident))
                    bad["identity:" + g] = "accepted"
                except ValueError:
                    bad["identity:" + g] = "refused"
            ck = torch.load(str(ckpt))
            ck.pop("contract")
            nc = res_dir / "checkpoints" / "no_contract.pt"
            torch.save(ck, nc)
            try:
                load_checkpoint_checked(agent2, nc, contract)
                bad["no_contract"] = "accepted"
            except ValueError:
                bad["no_contract"] = "refused"
            # a legacy schema-1 contract (learning-module hashes only, no semantic identity) is refused, not upgraded
            ck["contract"] = {k: v for k, v in contract.items() if k != "semantic_identity"}
            ck["contract"]["schema"] = 1
            lc = res_dir / "checkpoints" / "legacy_schema1.pt"
            torch.save(ck, lc)
            try:
                load_checkpoint_checked(agent2, lc, contract)
                bad["legacy_schema1_contract"] = "accepted"
            except ValueError:
                bad["legacy_schema1_contract"] = "refused"
            summary["contract_mismatch_results"] = bad
            V["wrong_or_missing_contract_refused"] = all(v == "refused" for v in bad.values())
            # eval path through the env with the loaded agent (deterministic policy, 1 short episode)
            eps = run_eval(env, agent2, 1, 25, a.seed + 1000)
            summary["eval_episode"] = eps
            V["loaded_policy_drives_env"] = len(eps) == 1 and eps[0]["steps"] >= 1
        summary["no_prior_used"] = True
    env.close()
    summary["ok"] = all(V.values())
    with open(res_dir / "sac_summary.json", "w") as f:
        json.dump(summary, f, indent=1, default=str)
    for k, v in V.items():
        print(("PASS " if v else "FAIL ") + k)
    print("OK" if summary["ok"] else "NOT OK", "->", res_dir / "sac_summary.json")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
