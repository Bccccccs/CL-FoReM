"""Explicit data-only snapshots for a committed Task10 decision boundary.

Live environments, callbacks, CUDA graphs and process objects are never pickled.
Mutable scientific state is encoded through a closed class registry. Constructors
supply the robot/kinematics and the collision/renderer references are rebuilt.
"""
from collections import deque
from copy import deepcopy
from pathlib import Path
import numpy as np
import torch

SCHEMA = 'task10-boundary-state-v1'
CORE_REFERENCES = {'kin', 'capsules', 'robot', 'collision', 'renderer'}
ENV_FIELDS = ('observation', 'candidates', 'previous_link', 'last_timing',
              'previous_result', 'previous_candidate', 'previous_result_v1',
              'previous_target_delta_s')
EP_FIELDS = ('map_ids', 'proposal_seeds', 'episode_count', 'totals', 'sensor_config')


def _registry():
    from task7_sim.core import State, Candidate, Transition
    from task7_sim.motion import Route
    from task7_sim.routes import PackedRoute
    from task7_sim.perception import Grid
    from task7_upper.vcm import MemoryEntry
    from task8_sim.primitive_scene import PrimitiveScene
    from task8_sim.routes import PcdTruthPlanner
    return {c.__name__: c for c in (State, Candidate, Transition, Route, PackedRoute,
                                    Grid, MemoryEntry, PrimitiveScene, PcdTruthPlanner)}


def encode(value):
    """CPU tensors retain original device tags; unknown object types fail closed."""
    registry = _registry()
    def visit(item):
        if item is None or type(item) in (str, int, float, bool, bytes):
            return {'kind': 'scalar', 'value': item}
        if isinstance(item, torch.Tensor):
            return {'kind': 'tensor', 'device': str(item.device),
                    'value': item.detach().cpu().clone()}
        if isinstance(item, np.ndarray):
            return {'kind': 'numpy', 'value': item.copy()}
        if isinstance(item, np.generic):
            return {'kind': 'numpy-scalar', 'value': item.copy()}
        if isinstance(item, torch.device):
            return {'kind': 'device', 'value': str(item)}
        if isinstance(item, torch.dtype):
            return {'kind': 'dtype', 'value': str(item).removeprefix('torch.')}
        if isinstance(item, dict):
            return {'kind': 'dict', 'value': [(visit(k), visit(v)) for k, v in item.items()]}
        if isinstance(item, deque):
            return {'kind': 'deque', 'maxlen': item.maxlen, 'value': [visit(v) for v in item]}
        if isinstance(item, (tuple, list)):
            return {'kind': 'tuple' if isinstance(item, tuple) else 'list',
                    'value': [visit(v) for v in item]}
        label = type(item).__name__
        if label not in registry or type(item) is not registry[label]:
            raise ValueError(f'unsupported boundary state object: {type(item).__module__}.{label}')
        fields = dict(vars(item))
        if label == 'PrimitiveScene':
            # A padded query bank is a pure cache; rebuild from exact scene tensors.
            fields['_bank1'] = None
        return {'kind': 'object', 'class': label, 'fields': visit(fields)}
    return dict(schema=SCHEMA, data=visit(value))


def decode(payload, *, device):
    if payload.get('schema') != SCHEMA:
        raise ValueError('boundary state schema/version mismatch')
    registry = _registry()
    def visit(item):
        kind = item['kind']
        if kind == 'scalar': return item['value']
        if kind in ('numpy', 'numpy-scalar'): return item['value'].copy()
        if kind == 'tensor':
            target = device if torch.device(item['device']).type == 'cuda' else item['device']
            return item['value'].to(target).clone()
        if kind == 'device':
            return torch.device(device if torch.device(item['value']).type == 'cuda' else item['value'])
        if kind == 'dtype':
            value = getattr(torch, item['value'], None)
            if not isinstance(value, torch.dtype): raise ValueError('unsupported tensor dtype')
            return value
        if kind == 'dict': return {visit(k): visit(v) for k, v in item['value']}
        if kind == 'tuple': return tuple(visit(v) for v in item['value'])
        if kind == 'list': return [visit(v) for v in item['value']]
        if kind == 'deque': return deque((visit(v) for v in item['value']), maxlen=item['maxlen'])
        if kind == 'object':
            cls = registry.get(item['class'])
            if cls is None: raise ValueError('unsupported boundary state class/version')
            obj = cls.__new__(cls)
            obj.__dict__.update(visit(item['fields']))
            return obj
        raise ValueError(f'unsupported boundary state kind: {kind}')
    return visit(payload['data'])


def source_contract():
    """Pin the implementation that interprets every saved field, including assets."""
    from .runtime import sha256
    root = Path(__file__).resolve().parents[2]
    files = []
    for package in ('task10', 'task7_sim', 'task7_lower', 'task7_upper', 'task8_sim'):
        files.extend(sorted((root/'src'/package).glob('*.py')))
    files.extend(sorted((root/'config/task8').glob('*.json')))
    files.extend(sorted((root/'assets').rglob('*.urdf')))
    return {str(p.relative_to(root)): sha256(p) for p in files if p.is_file()}


def runtime_contract():
    return dict(torch=torch.__version__, numpy=np.__version__, threads=torch.get_num_threads(),
        deterministic=torch.are_deterministic_algorithms_enabled(),
        deterministic_warn_only=torch.is_deterministic_algorithms_warn_only_enabled(),
        matmul_tf32=torch.backends.cuda.matmul.allow_tf32,
        cudnn_tf32=torch.backends.cudnn.allow_tf32,
        cudnn_benchmark=torch.backends.cudnn.benchmark,
        cudnn_deterministic=torch.backends.cudnn.deterministic)


def capture_environment(env):
    ep, c = env.episodes, env.episodes.core
    if c is None or env.observation is None or env.candidates is None:
        raise ValueError('initialized decision boundary required')
    if env._pending_result is not None or bool((c.terminated | c.truncated).any()):
        raise ValueError('prepare next and reset all naturally ended rows before saving')
    if not bool(c.done.all()):
        raise ValueError('selected segment still active')
    if env.candidates.get('pending', False):
        raise ValueError('candidate boundary pending')
    if bool(env.candidates['terminal_placeholder'].any()):
        raise ValueError('ended-row candidate placeholder has not been reset')
    if getattr(ep, 'factory', None) is not None:
        raise ValueError('custom mutable sampling factories are not resumable')
    if ep.sampling_cancel is not None:
        raise ValueError('active sampling cancellation callback is not resumable')
    from task8_sim.primitive_scene import PrimitiveSceneBatch
    if type(ep.scenes) is not PrimitiveSceneBatch:
        raise ValueError('decision boundary supports the approved primitive-obb-v1 scene backend')
    core = {k: v for k, v in vars(c).items() if k not in CORE_REFERENCES}
    return encode(dict(core=core, core_keys=sorted(vars(c)),
        scenes=list(ep.scenes.scenes), raycast_backend=ep.scenes.raycast_backend,
        episode={k: getattr(ep, k) for k in EP_FIELDS},
        environment={k: getattr(env, k) for k in ENV_FIELDS},
        sampler=None if ep.sampler is None else dict(planners=ep.sampler.planners,
            stats=ep.sampler.stats, timing=ep.sampler.timing),
        kin_options=dict(dls_cuda_graph=getattr(ep.kin, 'dls_cuda_graph', False))))


def restore_environment(env, payload):
    from task7_sim.core import Core
    from task8_sim.primitive_scene import PrimitiveSceneBatch
    from task8_sim.episode import SceneCollision
    from task8_sim.perception import PcdPanorama
    ep = env.episodes
    if ep.core is not None or env.observation is not None:
        raise ValueError('fresh environment constructor required')
    state = decode(payload, device=ep.device)
    for key, value in state['episode'].items(): setattr(ep, key, value)
    ep.scenes = PrimitiveSceneBatch(state['scenes'], raycast_backend=state['raycast_backend'])
    c = Core.__new__(Core)
    c.__dict__.update(state['core'])
    c.kin, c.capsules, c.robot = ep.kin, ep.robot, ep.robot
    c.collision = SceneCollision(ep.scenes, ep.robot)
    c.renderer = PcdPanorama(ep.scenes, sensor_config=ep.sensor_config)
    if sorted(vars(c)) != state['core_keys']:
        raise ValueError('restored Core field schema differs')
    ep.core = c
    ep.kin.dls_cuda_graph = state['kin_options']['dls_cuda_graph']
    if (ep.sampler is None) != (state['sampler'] is None):
        raise ValueError('sampler presence mismatch')
    if ep.sampler is not None:
        for key, value in state['sampler'].items(): setattr(ep.sampler, key, value)
    for key, value in state['environment'].items(): setattr(env, key, value)
    env._pending_result = None
    return env
