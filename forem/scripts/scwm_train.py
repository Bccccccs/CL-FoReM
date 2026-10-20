#!/usr/bin/env python3
"""FoReM Task4 training entry: plain SAC (task4.8) and, later, frozen-WM feedback SAC (task4.10) under ONE loop.

Semantics follow the reference husky main.py loop: random warm-up actions, then policy actions; update (updates_per_step, once
len(replay) > batch) BEFORE pushing the new transition; mask = float(not done) for every done. Differences are run management only:
explicit budget, full-state checkpoints with resume, per-episode ledger, phase timing, validation-checkpoint evaluation on held-out
scene seeds, physical (independent) success next to the internal one. Never loads a prior agent or old checkpoint.

Run inside forem-dev with a simulation already up (use scripts/scwm_instance.py / run wrapper):
  python3 -u scripts/scwm_train.py --run-id RID --seed 0 --device cuda:0 [--steps N] [--config config/task4_scwm/plain.yaml]
"""
import ray  # noqa: F401  -- first heavy import
import argparse
import hashlib
import json
import os
import random
import signal
import sys
import time
from pathlib import Path

import numpy as np
import torch
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src" / "modulation_rl" / "scripts"))

from scwm_sac import GpuReplay, ScwmSAC, load_replay_npz, save_replay_npz  # noqa: E402

SOURCE_FILES = ["scripts/scwm_train.py", "scripts/scwm_env.py", "scripts/scwm_sac.py", "scripts/scwm_policy.py", "scripts/scwm_feedback.py", "scripts/scwm_wm.py", "scripts/scwm_clock.py", "scripts/task3_env.py",
                "src/modulation_rl/scripts/sac.py", "src/modulation_rl/scripts/model.py", "src/modulation_rl/scripts/modulation/utils.py",
                "src/modulation_rl/scripts/modulation/envs/combined_env.py", "src/modulation_rl/scripts/modulation/envs/robotenv.py",
                "src/modulation_rl/scripts/modulation/envs/eeplanner.py", "src/modulation_rl/src/robot_env.cpp",
                "config/task3/task_contract.yaml", "config/task3/sac.yaml", "src/forem_husky/launch/husky_core.launch"]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def atomic_json(path, obj):
    tmp = str(path) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, default=str)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


class Jsonl:
    def __init__(self, path):
        self.f = open(path, "a", buffering=1)

    def write(self, rec):
        self.f.write(json.dumps(rec, default=str) + "\n")

    def close(self):
        self.f.close()


class Timers:
    """Accumulates wall time per phase and sim-interval samples; flush() returns and clears the window."""

    def __init__(self, profile=False):
        self.profile = profile
        self.t = {}
        self.n = {}
        self.samples = {}
        self.sim = {"think": [], "step": [], "interval": []}
        self.w0 = time.perf_counter()
        self.s0 = None

    def add(self, k, dt):
        self.t[k] = self.t.get(k, 0.0) + dt
        self.n[k] = self.n.get(k, 0) + 1
        if self.profile:
            self.samples.setdefault(k, []).append(dt)

    def flush(self, sim_now):
        wall = time.perf_counter() - self.w0
        out = {"wall_s": wall, "phase_ms_mean": {k: 1e3 * v / max(self.n[k], 1) for k, v in self.t.items()},
               "phase_s_total": dict(self.t), "phase_n": dict(self.n)}
        if self.profile:
            out["phase_latency_ms"] = {k: dict(p50=float(np.percentile(v,50))*1000, p95=float(np.percentile(v,95))*1000, max=float(max(v))*1000) for k,v in self.samples.items() if v}
        for k, v in self.sim.items():
            if v:
                a = np.asarray(v)
                out["sim_" + k + "_s"] = dict(mean=float(a.mean()), p50=float(np.percentile(a, 50)), p95=float(np.percentile(a, 95)), max=float(a.max()))
        if self.s0 is not None and wall > 0:
            out["rtf_window"] = (sim_now - self.s0) / wall
        self.samples = {}
        self.t, self.n, self.sim = {}, {}, {"think": [], "step": [], "interval": []}
        self.w0, self.s0 = time.perf_counter(), sim_now
        return out


def rng_states(rng_np, rng_inst):
    return dict(py=random.getstate(), np=np.random.get_state(), torch=torch.get_rng_state(),
                cuda=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
                rng_np=rng_np.get_state(), rng_inst=rng_inst.get_state())


def set_rng_states(s, rng_np, rng_inst):
    random.setstate(s["py"])
    np.random.set_state(s["np"])
    torch.set_rng_state(s["torch"].cpu())
    if s["cuda"] is not None:
        torch.cuda.set_rng_state_all([x.cpu() for x in s["cuda"]])
    rng_np.set_state(s["rng_np"])
    rng_inst.set_state(s["rng_inst"])


def update_due(completed_env_steps, every):
    if int(every) < 1:
        raise ValueError("update_every_env_steps must be positive")
    return int(completed_env_steps) % int(every) == 0


def run_eval_preserving_rng(env, agent, seeds, max_steps, rng_np, rng_inst):
    state = rng_states(rng_np, rng_inst)
    try:
        episodes = []
        for seed in seeds:
            try:
                episodes += run_eval(env, agent, [seed], max_steps)
            except Exception as exc:
                episodes.append(dict(seed=int(seed), error=repr(exc), done=False, capped=False, internal_success=False, physical_success=None))
        return episodes
    finally:
        set_rng_states(state, rng_np, rng_inst)


def run_eval(env, agent, seeds, max_steps):
    """Deterministic policy on held-out scene seeds; no replay, no update. Returns per-episode dicts."""
    out = []
    for s in seeds:
        w0 = time.time()
        state = env.reset(seed=int(s))
        done, n, ret, info = False, 0, 0.0, {}
        while not done and n < max_steps:
            a = agent.select_action(state, eval=True)
            state, r, done, info, _ = env.step(a)
            ret += r
            n += 1
        phys = info.get("physical") if done else None
        out.append(dict(seed=int(s), steps=n, done=bool(done), capped=bool(not done), return_=float(ret), internal_success=info.get("success"),
                        ee_done=info.get("ee_done"), nr_kin_failures=info.get("nr_kin_failures"), nr_base_collisions=info.get("nr_base_collisions"),
                        truncated=info.get("truncated"), physical=phys, physical_success=(phys or {}).get("success", False),
                        episode_hash=env.episode_spec["hash"], wall_s=time.time() - w0))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--world", choices=["sim", "gazebo"], default="gazebo")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--config", default=str(ROOT / "config" / "task4_scwm" / "plain.yaml"))
    ap.add_argument("--steps", type=int, default=None, help="override budget.total_env_steps (pilots)")
    ap.add_argument("--max-wall-s", type=float, default=None)
    ap.add_argument("--val-every", type=int, default=None)
    ap.add_argument("--ckpt-every", type=int, default=None)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--no-val-final", action="store_true", help="pilots: skip the validation pass at the end")
    ap.add_argument("--cudnn-benchmark", action="store_true")
    ap.add_argument("--method", choices=["plain", "feedback"], default="plain")
    ap.add_argument("--wm", default=None, help="feedback: task4.9 model file (frozen world model + reference encoder)")
    ap.add_argument("--fork-ckpt-dir", default=None, help="feedback, fresh start: plain-run checkpoint dir to fork from")
    ap.add_argument("--fork-step", type=int, default=None)
    ap.add_argument("--pin-ckpt-steps", default="", help="comma list: checkpoints at exactly these steps are never deleted (fork points)")
    ap.add_argument("--window-s", type=float, default=None, help="fixed sim window per decision (scwm_clock); default: reference real-time stepping")
    ap.add_argument("--no-unthrottle", action="store_true", help="with --window-s: keep the wall-clock pacing of the physics loop")
    a = ap.parse_args()

    cfg = yaml.safe_load(open(a.config))
    B = cfg["budget"]
    total = int(a.steps or B["total_env_steps"])
    val_every = int(a.val_every or cfg["validation"]["every_env_steps"])
    ckpt_every = int(a.ckpt_every or cfg["checkpoint"]["every_env_steps"])
    log_every = int(cfg["logging"]["progress_every_env_steps"])
    warm, batch = int(B["random_warmup_steps"]), int(B["batch_size"])
    update_every = int(B.get("update_every_env_steps", 1))
    if update_every < 1:
        raise ValueError("update_every_env_steps must be positive")
    screening = cfg.get("screening")
    logdir = Path(os.environ.get("FOREM_LOG_DIR", ROOT / "logs" / "task4" / a.run_id))
    resdir = Path(os.environ.get("FOREM_RES_DIR", ROOT / "results" / "task4" / a.run_id))
    ckdir = resdir / "ckpt"
    for d in (logdir, resdir, ckdir):
        d.mkdir(parents=True, exist_ok=True)
    torch.backends.cudnn.benchmark = bool(a.cudnn_benchmark)

    if a.method == "feedback" and not (a.wm and (a.resume or (a.fork_ckpt_dir and a.fork_step))):
        raise SystemExit("feedback needs --wm and, on a fresh start, --fork-ckpt-dir/--fork-step")
    fork_files = {}
    if a.method == "feedback":
        fork_files["wm_sha256"] = sha256_file(a.wm)
        if a.fork_ckpt_dir:
            tg = "%08d" % a.fork_step
            fork_files["fork_state_sha256"] = sha256_file(Path(a.fork_ckpt_dir) / ("state_%s.pt" % tg))
            fork_files["fork_replay_sha256"] = sha256_file(Path(a.fork_ckpt_dir) / ("replay_%s.npz" % tg))
    manifest = dict(run_id=a.run_id, method=a.method, fork=dict(dir=a.fork_ckpt_dir, step=a.fork_step, **fork_files) if a.method == "feedback" else None, seed=a.seed, device=a.device, config=cfg, config_sha256=sha256_file(a.config), total_steps=total, window_s=a.window_s, unthrottle=bool(a.window_s and not a.no_unthrottle),
                    sources={f: sha256_file(ROOT / f) for f in SOURCE_FILES}, torch=str(torch.__version__),
                    gpu=torch.cuda.get_device_name(torch.device(a.device)) if a.device.startswith("cuda") else None,
                    ros_master=os.environ.get("ROS_MASTER_URI"), started=time.strftime("%F %T %z"))
    if a.world == "sim":
        manifest["world"] = "sim"
        manifest["force_rectangle_obstacles"] = True
        manifest["sources"]["src/modulation_rl/scripts/modulation/envs/map.py"] = sha256_file(ROOT / "src/modulation_rl/scripts/modulation/envs/map.py")
    mpath = resdir / "run_manifest.json"
    if mpath.exists():
        old = json.load(open(mpath))
        if not a.resume:
            raise SystemExit("refused: run-id already has a manifest; use --resume or a new run-id")
        diffs = [k for k in ("seed", "config_sha256", "sources", "window_s", "method", "world") if old.get(k) != manifest.get(k)]
        if diffs:
            raise SystemExit("refused: resume with changed %s" % diffs)
        manifest["started"] = old["started"]
        manifest["resumed"] = old.get("resumed", []) + [time.strftime("%F %T %z")]
    atomic_json(mpath, manifest)

    random.seed(a.seed)
    np.random.seed(a.seed)
    torch.manual_seed(a.seed)
    rng_np = np.random.RandomState(a.seed)                       # warm-up actions
    rng_inst = np.random.RandomState(a.seed * 7919 + 13)         # training scene seeds

    from scwm_env import ScwmEnv
    if os.environ.get("SCWM_FAKE_ENV"):                      # unit tests only: no simulation
        from scwm_fake_env import FakeEnv
        env = FakeEnv(seed=a.seed)
    else:
        env = ScwmEnv(seed=a.seed, window_s=a.window_s, unthrottle=not a.no_unthrottle, **({"world": "sim", "max_close_steps": cfg.get("max_close_steps", 500)} if a.world == "sim" else {}))
    sac_args = dict(gamma=0.99, tau=0.001, initial_alpha=1.0, device=a.device, train_batch_size=batch,
                    model=dict(custom_model_config=dict(post_fcnet_hiddens=[512, 512, 256])))
    policy_factory = None
    if a.method == "feedback":
        import functools
        import scwm_wm as WMM
        from scwm_feedback import FeedbackGaussianPolicy
        from scwm_policy import FixedGaussianPolicy
        skel = FixedGaussianPolicy(env.observation_space[1], env.observation_space[0], 3, [512, 512, 256], env.action_space, False)
        ref_enc, wmodel, _wmck = WMM.load_wm(a.wm, a.device, skel)
        policy_factory = functools.partial(FeedbackGaussianPolicy, ref_encoder=ref_enc, world_model=wmodel)
        manifest["ref_encoder_sha256"] = ref_enc.sha256()
        atomic_json(mpath, manifest)
    agent = ScwmSAC(env.observation_space, env.action_space, 1, sac_args, int(B["lr_horizon_updates"]), **({"policy_factory": policy_factory} if policy_factory else {}), alpha_rule=B.get("alpha_rule", "capped"), lr_schedule=B.get("lr_schedule", "exp_updates"))
    replay = GpuReplay(int(B["replay_capacity"]), a.seed, a.device)
    ledger, progress, events = Jsonl(logdir / "episodes.jsonl"), Jsonl(logdir / "progress.jsonl"), Jsonl(logdir / "events.jsonl")

    steps = updates = episodes = 0
    next_val = val_every
    next_ckpt = ckpt_every
    if a.method == "feedback" and not a.resume:
        tg = "%08d" % a.fork_step
        S = torch.load(Path(a.fork_ckpt_dir) / ("state_%s.pt" % tg), weights_only=False, map_location=a.device)
        agent.load_fork_state(S["agent"])
        load_replay_npz(replay, Path(a.fork_ckpt_dir) / ("replay_%s.npz" % tg), S["replay_rng"])
        set_rng_states(S["rng"], rng_np, rng_inst)
        steps, updates, episodes = S["steps"], S["updates"], S["episodes"]
        env.epoch, env.episode_id = S["env_epoch"], S["env_episode_id"]
        next_val, next_ckpt = S["next_val"], S["next_ckpt"]
        events.write(dict(ev="fork", from_step=steps, fork=manifest["fork"], time=time.strftime("%F %T %z")))
    if a.resume:
        ptr = ckdir / "latest.json"
        if not ptr.exists():
            raise SystemExit("refused: --resume but no checkpoint")
        P = json.load(open(ptr))
        S = torch.load(ckdir / P["state"], weights_only=False, map_location=a.device)
        agent.load_full_state_dict(S["agent"])
        load_replay_npz(replay, ckdir / P["replay"], S["replay_rng"])
        set_rng_states(S["rng"], rng_np, rng_inst)
        steps, updates, episodes = S["steps"], S["updates"], S["episodes"]
        env.epoch, env.episode_id = S["env_epoch"], S["env_episode_id"]
        next_val, next_ckpt = S["next_val"], S["next_ckpt"]
        events.write(dict(ev="resume", from_step=steps, time=time.strftime("%F %T %z")))
    events.write(dict(ev="start", steps=steps, total=total, time=time.strftime("%F %T %z"), device=a.device))

    stop = {"flag": None}
    for sg in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sg, lambda s, f: stop.__setitem__("flag", signal.Signals(s).name))

    def save_ckpt():
        checkpoint_t0 = time.perf_counter()
        tag = "%08d" % steps
        st = dict(agent=agent.full_state_dict(), rng=rng_states(rng_np, rng_inst), steps=steps, updates=updates, episodes=episodes,
                  env_epoch=env.epoch, env_episode_id=env.episode_id, next_val=next_val, next_ckpt=next_ckpt, replay_rng=replay.rng.getstate())
        if screening:
            st["next_screen"] = next_screen
        torch.save(st, ckdir / ("state_%s.pt.tmp" % tag))
        os.replace(ckdir / ("state_%s.pt.tmp" % tag), ckdir / ("state_%s.pt" % tag))
        replay_t0 = time.perf_counter()
        save_replay_npz(replay, ckdir / ("replay_%s.npz" % tag))
        if a.world == "sim":
            tm.add("replay_disk", time.perf_counter()-replay_t0)
        atomic_json(ckdir / "latest.json", dict(step=steps, state="state_%s.pt" % tag, replay="replay_%s.npz" % tag))
        pins = {int(x) for x in a.pin_ckpt_steps.split(",") if x}
        olds = [p for p in sorted(ckdir.glob("state_*.pt"))[:-int(cfg["checkpoint"]["keep_last"])] if int(p.stem.split("_")[1]) not in pins]
        for p in olds:
            p.unlink()
            (ckdir / p.name.replace("state_", "replay_").replace(".pt", ".npz")).unlink(missing_ok=True)
        events.write(dict(ev="checkpoint", step=steps, time=time.strftime("%F %T %z"), **({"wall_s":time.perf_counter()-checkpoint_t0} if a.world=="sim" else {})))
        if a.world == "sim":
            tm.add("checkpoint", time.perf_counter()-checkpoint_t0)

    def validate():
        t0 = time.time()
        eps = run_eval(env, agent, cfg["instances"]["validation_seeds"], int(cfg["validation"]["max_steps_per_episode"]))
        torch.save(agent.policy.state_dict(), ckdir / ("policy_step%08d.pt" % steps))
        rec = dict(step=steps, episodes=eps, wall_s=time.time() - t0,
                   physical_successes=sum(bool(e["physical_success"]) for e in eps), n=len(eps),
                   internal_successes=sum(bool(e["internal_success"]) for e in eps))
        atomic_json(resdir / ("validation_step%08d.json" % steps), rec)
        events.write(dict(ev="validation", step=steps, physical_successes=rec["physical_successes"], internal_successes=rec["internal_successes"], n=rec["n"], wall_s=rec["wall_s"]))
        if a.world == "sim":
            tm.add("validation", time.time()-t0)
        return rec

    next_screen = int(S.get("next_screen", screening["every_env_steps"])) if screening and (a.resume or (a.method == "feedback" and a.fork_step)) else (int(screening["every_env_steps"]) if screening else None)

    def screen():
        t0 = time.time()
        eps = run_eval_preserving_rng(env, agent, screening["seeds"], int(cfg["validation"]["max_steps_per_episode"]), rng_np, rng_inst)
        torch.save(agent.policy.state_dict(), ckdir / ("screen_policy_step%08d.pt" % steps))
        rec = dict(step=steps, scheduled_step=next_screen, episodes=eps, wall_s=time.time()-t0, n=len(eps), internal_successes=sum(bool(e.get("internal_success")) for e in eps))
        atomic_json(resdir / ("screening_step%08d.json" % next_screen), rec)
        events.write(dict(ev="screening", step=steps, scheduled_step=next_screen, n=rec["n"], internal_successes=rec["internal_successes"], wall_s=rec["wall_s"]))
        tm.add("screening", time.time()-t0)

    tm = Timers(profile=a.world == "sim")
    window = dict(ep=0, succ=0, phys=0, ret=0.0)
    t_run0 = time.time()
    last_log_step = steps
    state = None
    ep_state = None
    try:
        while steps < total and not stop["flag"]:
            inst_seed = int(rng_inst.randint(*cfg["instances"]["train_seed_range"]))
            w0 = time.perf_counter()
            state = env.reset(seed=inst_seed)
            tm.add("reset", time.perf_counter() - w0)
            tm.s0 = tm.s0 if tm.s0 is not None else env.sim_time()
            ep_ret, ep_n, ep_w0, ep_s0 = 0.0, 0, time.time(), env.sim_time()
            ep_start_step = steps
            done = False
            info = {}
            while not done and steps < total and not stop["flag"]:
                w0 = time.perf_counter()
                action = rng_np.uniform(-1, 1, size=3).astype(np.float32) if steps < warm else agent.select_action(state)
                w1 = time.perf_counter()
                next_state, reward, done, info, meta = env.step(action)
                w2 = time.perf_counter()
                if len(replay) > batch and update_due(steps + 1, update_every):
                    for _ in range(int(B["updates_per_step"])):
                        agent.set_env_steps(steps + 1)
                        agent.update_parameters(replay, batch, updates)
                        updates += 1
                w3 = time.perf_counter()
                replay.push(state[1], state[0], action, reward, next_state[1], next_state[0], float(not done), meta=meta)
                w4 = time.perf_counter()
                tm.add("select", w1 - w0); tm.add("env_step", w2 - w1); tm.add("update", w3 - w2); tm.add("push", w4 - w3)
                s = info["scwm"]
                tm.sim["think"].append(s["t_cmd"] - s["t_obs"]); tm.sim["step"].append(s["t_next"] - s["t_cmd"]); tm.sim["interval"].append(s["t_next"] - s["t_obs"])
                state = next_state
                steps += 1
                ep_n += 1
                ep_ret += reward
                if steps - last_log_step >= log_every:
                    rec = tm.flush(env.sim_time())
                    rec.update(step=steps, updates=updates, episodes=episodes, window_episodes=window["ep"], window_internal_success=window["succ"],
                               window_physical_success=window["phys"], window_return_sum=window["ret"], elapsed_s=time.time() - t_run0,
                               steps_per_s_window=(steps - last_log_step) / max(rec["wall_s"], 1e-9))
                    progress.write(rec)
                    window = dict(ep=0, succ=0, phys=0, ret=0.0)
                    last_log_step = steps
                if steps >= next_ckpt:
                    next_ckpt += ckpt_every
                    save_ckpt()
                if a.max_wall_s and time.time() - t_run0 > a.max_wall_s:
                    stop["flag"] = "max_wall"
            if done:
                episodes += 1
                ph = info.get("physical", {})
                window["ep"] += 1; window["succ"] += int(bool(info.get("success"))); window["phys"] += int(bool(ph.get("success"))); window["ret"] += ep_ret
                ledger.write(dict(kind="train", episode=episodes, episode_id=env.episode_id, epoch=env.epoch, inst_seed=inst_seed, hash=env.episode_spec["hash"],
                                  step_start=ep_start_step, step_end=steps, n=ep_n, ret=float(ep_ret), internal_success=info.get("success"),
                                  ee_done=info.get("ee_done"), nr_kin_failures=info.get("nr_kin_failures"), nr_base_collisions=info.get("nr_base_collisions"),
                                  truncated=info.get("truncated"), terminated=info.get("terminated"), physical=ph, physical_success=ph.get("success"),
                                  sim_s=env.sim_time() - ep_s0, wall_s=time.time() - ep_w0))
            elif ep_n > 0:       # budget end / stop signal inside an episode: keep the steps in the ledger (fixed denominators)
                ledger.write(dict(kind="train_partial", episode=episodes + 1, episode_id=env.episode_id, epoch=env.epoch, inst_seed=inst_seed,
                                  hash=env.episode_spec["hash"], step_start=ep_start_step, step_end=steps, n=ep_n, ret=float(ep_ret), stop=stop["flag"]))
            if screening and not stop["flag"]:
                while steps >= next_screen:
                    screen()
                    next_screen += int(screening["every_env_steps"] if next_screen < 300000 else screening.get("after_300k_every", screening["every_env_steps"]))
            if steps >= next_val and not stop["flag"]:
                next_val += val_every
                validate()
        if not stop["flag"] and steps >= total and not a.no_val_final:
            validate()
    finally:
        events.write(dict(ev="exit", step=steps, stop=stop["flag"], time=time.strftime("%F %T %z")))
        if steps > 0:
            save_ckpt()
        env.close()
    atomic_json(resdir / "train_summary.json", dict(run_id=a.run_id, steps=steps, updates=updates, episodes=episodes, stop=stop["flag"], wall_s=time.time() - t_run0))
    print("DONE steps=%d updates=%d episodes=%d stop=%s" % (steps, updates, episodes, stop["flag"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
