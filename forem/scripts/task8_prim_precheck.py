#!/usr/bin/env python3
"""task8.11 X1 precheck: W equivalence (equiv) and I/R reset diagnostics (reset). No training.

* equiv: V3-default path before/after wiring (orig copies in W/orig) must give torch.equal reset results.
* reset: per-seed 256-env initial reset with backend taken from the training config's `map_backend`
  (resolve_map_backend, the wired path); per-episode rows for R; per-seed timing breakdown for I.
Runtime guard (task8_sim.profile_lower.prohibit_training) forbids optimizer construction / backward and
its counters are written into every artifact.
"""
import argparse, collections, copy, gc, hashlib, importlib.util, json, math, os, random, sys, time
from pathlib import Path
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
ORIG = ROOT / 'results/task8/t8-precheck-20261027/W/orig'


def atomic(path, doc):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp'); tmp.write_text(json.dumps(doc, indent=1, allow_nan=False) + '\n'); os.replace(tmp, path)


# ----------------------------------------------------------------------------------- equiv
def deep_equal(a, b, path='', diffs=None):
    diffs = [] if diffs is None else diffs
    if torch.is_tensor(a) and torch.is_tensor(b):
        if a.dtype != b.dtype or a.shape != b.shape or not torch.equal(a, b): diffs.append(path)
    elif isinstance(a, dict) and isinstance(b, dict):
        if a.keys() != b.keys(): diffs.append(path + ':keys')
        else:
            for k in a: deep_equal(a[k], b[k], f'{path}/{k}', diffs)
    elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b): diffs.append(path + ':len')
        else:
            for i, (x, y) in enumerate(zip(a, b)): deep_equal(x, y, f'{path}[{i}]', diffs)
    elif a != b: diffs.append(path)
    return diffs


def snapshot(env):
    from task7_lower.training import choose_candidate
    c = env.core
    snap = dict(map_ids=list(env.map_ids), proposal_seeds=list(env.proposal_seeds), versions=copy.deepcopy(env.versions),
                base=c.state.base.clone(), q=c.state.q.clone(), s=c.state.s.clone(),
                route_xyz=c.route.xyz.clone(), route_quat=c.route.quat.clone(), route_s=c.route.s.clone(),
                grid_observed=c.grid.observed.clone(), grid_height=c.grid.height.clone(), grid_timestamp=c.grid.timestamp.clone(),
                episode_count=env.episode_count.clone())
    choose_candidate(env)
    snap['observation'] = c.current_observation()
    return snap


def load_orig_module(name):
    spec = importlib.util.spec_from_file_location('orig_' + name, ORIG / (name + '.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def equiv(a):
    from task8_lower.evaluation import evaluation_environment, resolve_map_backend
    from task8_sim.env import PcdEpisodeEnv
    guards = prohibit_training()
    cfg = json.loads(Path(a.config).read_text()); device = torch.device(a.device)
    assert resolve_map_backend(cfg) == 'pcd-voxel-v3'
    results = {}
    pool = cfg['pool']
    def mk_train_old():
        # pre-wiring training.py L173 call: no map_backend kwarg
        env = PcdEpisodeEnv(a.envs, seed=cfg['seed'], pool=pool, profile=cfg['profile'], device=device, dtype=torch.float32, split=cfg['train_split'])
        env.kin.dls_cuda_graph = cfg['dls_cuda_graph']; return env
    def mk_train_new():
        env = PcdEpisodeEnv(a.envs, seed=cfg['seed'], pool=pool, profile=cfg['profile'], device=device, dtype=torch.float32, split=cfg['train_split'], map_backend=resolve_map_backend(cfg))
        env.kin.dls_cuda_graph = cfg['dls_cuda_graph']; return env
    def run(factory):
        random.seed(cfg['seed']); np.random.seed(cfg['seed']); torch.manual_seed(cfg['seed'])
        env = factory(); env.reset(); return snapshot(env)
    old, new = run(mk_train_old), run(mk_train_new)
    d = deep_equal(old, new); results['training_env_reset'] = dict(equal=not d, diffs=d, map_ids=old['map_ids'][:a.envs], fields=sorted(old))
    # evaluation_environment: orig module vs current module
    manifest = json.loads(Path(cfg['pool']).read_text())
    entries = [e for e in manifest['maps'] if e['split'] == 'validation'][:a.envs]
    jobs = [dict(map_id=e['id'], seed=100 + i, stream_index=0, role='validation', source_split='validation', episode_index=0, entry=e) for i, e in enumerate(entries)]
    orig_eval = load_orig_module('evaluation')
    def run_eval(mod):
        random.seed(1); np.random.seed(1); torch.manual_seed(1)
        env = mod.evaluation_environment(jobs, cfg, cfg['pool'], device); env.reset(); return snapshot(env)
    old_e, new_e = run_eval(orig_eval), run_eval(sys.modules['task8_lower.evaluation'])
    d = deep_equal(old_e, new_e); results['evaluation_env_reset'] = dict(equal=not d, diffs=d, map_ids=old_e['map_ids'])
    doc = dict(status='pass' if all(r['equal'] for r in results.values()) else 'FAIL', device=str(device), envs=a.envs, config=a.config,
               config_sha256=hashlib.sha256(Path(a.config).read_bytes()).hexdigest(), orig_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ORIG.glob('*.py')},
               current_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in ('src/task8_lower/training.py', 'src/task8_lower/evaluation.py')},
               results=results, guards=guards, scene_cache_env=os.environ.get('TASK8_SCENE_CACHE'))
    atomic(a.output, doc); print(json.dumps(dict(status=doc['status'], results={k: v['equal'] for k, v in results.items()}, guards=guards)))
    return 0 if doc['status'] == 'pass' else 3


# ----------------------------------------------------------------------------------- reset
def prohibit_training():
    from task8_sim.profile_lower import prohibit_training as p
    return p()


def wrap_timer(obj, name, label, totals, counts):
    original = getattr(obj, name)
    def call(*args, **kw):
        t = time.monotonic()
        try: return original(*args, **kw)
        finally: totals[label] += time.monotonic() - t; counts[label] += 1
    setattr(obj, name, call)


def reset_diag(a):
    from task8_lower.evaluation import resolve_map_backend
    from task8_sim import episode, scene, primitive_scene, primitive_assets, scene_cache
    from task8_sim.env import PcdEpisodeEnv
    from task8_sim.profile_lower import runtime
    guards = prohibit_training()
    cfg = json.loads(Path(a.config).read_text()); backend = resolve_map_backend(cfg)
    torch.set_num_threads(cfg['threads'])
    device = torch.device('cuda:0')
    totals = collections.defaultdict(float); counts = collections.Counter()
    # Fine-grain wrappers (process-local, nothing on disk changes). Nested labels overlap; see 'note'.
    wrap_timer(episode, 'load_asset', 'v3_load_asset_s', totals, counts)
    orig_from = scene.VoxelScene.from_asset.__func__
    def v3_from(cls, *args, **kw):
        t = time.monotonic()
        try: return orig_from(cls, *args, **kw)
        finally: totals['v3_voxel_scene_from_asset_s'] += time.monotonic() - t; counts['v3_voxel_scene_from_asset_s'] += 1
    scene.VoxelScene.from_asset = classmethod(v3_from)
    wrap_timer(scene_cache.SceneCache, 'load', 'v3_scene_cache_load_s', totals, counts)
    wrap_timer(episode, 'load_backend_scene', 'p_load_backend_scene_s', totals, counts)
    wrap_timer(primitive_scene, 'load_primitive_asset', 'p_load_primitive_asset_s', totals, counts)
    orig_pfrom = primitive_scene.PrimitiveScene.from_asset.__func__
    def p_from(cls, *args, **kw):
        t = time.monotonic()
        try: return orig_pfrom(cls, *args, **kw)
        finally: totals['p_scene_from_asset_s'] += time.monotonic() - t; counts['p_scene_from_asset_s'] += 1
    primitive_scene.PrimitiveScene.from_asset = classmethod(p_from)
    wrap_timer(episode.PcdTruthPlanner, '__init__', 'planner_build_s', totals, counts)
    wrap_timer(episode.PcdTruthPlanner, 'witness_cells', 'witness_cells_s', totals, counts)

    out = Path(a.output); seeds = [int(s) for s in a.seeds.split(',')]
    manifest = json.loads(Path(cfg['pool']).read_text()); by_id = {e['id']: e for e in manifest['maps'] if e['split'] == cfg['train_split']}
    doc = dict(status='running', map_backend=backend, config=a.config, config_sha256=hashlib.sha256(Path(a.config).read_bytes()).hexdigest(),
               config_map_backend=cfg.get('map_backend'), environment_geometry_version=cfg.get('environment_geometry_version'),
               pool=cfg['pool'], split=cfg['train_split'], envs=cfg['environments'] if a.envs is None else a.envs, deadline_s=a.deadline_s, seeds=seeds,
               scene_cache=os.environ.get('TASK8_SCENE_CACHE'), guards=guards, per_seed=[], note='Nested wrapper labels overlap; asset_scene_s is the sampler total; disjoint pieces are in components.')
    envs = doc['envs']
    def flush(status=None):
        if status: doc['status'] = status
        doc['guards'] = guards; doc['runtime'] = runtime(); atomic(out, doc)
    def run_seed(seed):
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
        torch.cuda.reset_peak_memory_stats(); before = {k: totals[k] for k in totals}; cbefore = dict(counts)
        env = PcdEpisodeEnv(envs, seed=seed, pool=cfg['pool'], profile=cfg['profile'], device=device, dtype=torch.float32, split=cfg['train_split'], map_backend=backend)
        env.kin.dls_cuda_graph = cfg['dls_cuda_graph']
        rec = dict(seed=seed, status='running', rows=[], map_backend=env.map_backend, versions=env.versions)
        doc['per_seed'].append(rec)
        sampler = env.sampler; original = sampler.sample; last = dict(stats=copy.deepcopy(sampler.stats), timing=dict(sampler.timing))
        def sample(*args, **kw):
            t = time.monotonic(); e = original(*args, **kw); w = time.monotonic() - t
            st, tm = sampler.stats, sampler.timing
            drej = {k: v - last['stats']['rejections'].get(k, 0) for k, v in st['rejections'].items() if v - last['stats']['rejections'].get(k, 0)}
            base = e.base[0].double().cpu(); goal = e.route.xyz[0, -1].double().cpu(); dxy = goal[:2] - base[:2]
            bearing = math.atan2(float(dxy[1]), float(dxy[0])) - float(base[2]); bearing = (bearing + math.pi) % (2 * math.pi) - math.pi
            ent = by_id[e.map_id]
            rec['rows'].append(dict(index=len(rec['rows']), map_id=e.map_id, difficulty=ent.get('difficulty'), occupied=ent.get('occupied'), proposal_seed=e.seed, wall_s=w,
                proposals=st['proposals'] - last['stats']['proposals'], rejections=drej,
                timing={k: tm[k] - last['timing'][k] for k in tm}, witness_targets=st['witness_targets'] - last['stats']['witness_targets'],
                base_x=float(base[0]), base_y=float(base[1]), yaw=float(base[2]), goal_x=float(goal[0]), goal_y=float(goal[1]), goal_z=float(goal[2]),
                goal_dist_xy=float(dxy.norm()), goal_bearing_rel=bearing, route_length=float(e.route.length[0]),
                witness_base=[float(x) for x in e.witness_base[0].cpu()] if e.witness_base is not None else None))
            last['stats'] = copy.deepcopy(st); last['timing'] = dict(tm)
            if len(rec['rows']) % 32 == 0: flush()
            return e
        sampler.sample = sample
        t0 = time.monotonic(); status = 'pass'; error = None
        try:
            with torch.no_grad(): env.reset(deadline=t0 + a.deadline_s)
        except Exception as exc: status = 'incomplete'; error = repr(exc)
        torch.cuda.synchronize(); elapsed = time.monotonic() - t0
        st, tm = sampler.stats, sampler.timing
        rec.update(status=status, error=error, elapsed_s=elapsed, within_deadline=(status == 'pass' and elapsed <= a.deadline_s), accepted=len(rec['rows']), stats=copy.deepcopy(st), timing=dict(tm),
                   post_sample_reset_s=elapsed - tm['sample_s'],
                   raw={k: totals[k] - before.get(k, 0.) for k in totals}, counts={k: counts[k] - cbefore.get(k, 0) for k in counts},
                   peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(), peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved(),
                   unique_maps=len({r['map_id'] for r in rec['rows']}))
        flush()
        del env, sampler; gc.collect(); torch.cuda.empty_cache()
        return status
    for seed in seeds:
        if run_seed(seed) != 'pass':
            flush('incomplete'); print(json.dumps(dict(status='incomplete', seed=seed, guards=guards))); return 2
    flush('pass')
    print(json.dumps(dict(status='pass', backend=backend, per_seed=[dict(seed=r['seed'], elapsed_s=round(r['elapsed_s'], 2), accepted=r['accepted'], proposals=r['stats']['proposals'], rej=r['stats']['rejections']) for r in doc['per_seed']], guards=guards)))
    return 0


def main():
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest='mode', required=True)
    e = sub.add_parser('equiv'); e.add_argument('--config', required=True); e.add_argument('--output', required=True); e.add_argument('--envs', type=int, default=4); e.add_argument('--device', default='cpu')
    r = sub.add_parser('reset'); r.add_argument('--config', required=True); r.add_argument('--output', required=True); r.add_argument('--seeds', default='4718'); r.add_argument('--envs', type=int, default=None); r.add_argument('--deadline-s', type=float, default=235.)
    a = p.parse_args()
    return equiv(a) if a.mode == 'equiv' else reset_diag(a)


if __name__ == '__main__':
    raise SystemExit(main())
