"""Strict, deterministic B3-5M seed4718 reader (task10 A; SRC-T10-001).

Actor output remains raw [u, omega, v]. Core.motion.actions owns physical
scaling and inplace masking; this adapter never rescales or clips it.
"""
import hashlib
import json
from pathlib import Path
import torch
from task7_lower.networks import Actor
from task7_lower.observation import VERSION, ACTION_VERSION, preprocess

INVENTORY_SHA256 = '4544b053846641106795792cccf458d1462efe8916246575666d899d235ad7bf'
RUN = 'results/task9/t9-stage2-20261029/'
ARTIFACTS = {
    RUN+'B3_5M-seed4718/final.actor.pt': '3db11d9f00317849e35a523d66d0935ebc2e3567d82c519ccc42f3d8de42f7ae',
    RUN+'B3_5M-seed4718/config.json': '52d0d7a33019b73601c0e4997d999d9ca366d5da01750a66a4a35b7a469f7086',
    RUN+'B3_5M-seed4719/final.actor.pt': 'fb9b0054168091e5b4b1953416d8d6e47d03a1834e5a9b0dc4148c85e4574688',
    RUN+'B3_5M-seed4719/config.json': 'a7c5db8a4369de00d13a8217cbc9ac5a51d583c5b045d9bdb8b526de276287de',
    RUN+'B3_5M-seed4720/final.actor.pt': 'c1d7300e6567af18cbd9dde7205e5365f1b681349f4f9de82535955ff0bb330b',
    RUN+'B3_5M-seed4720/config.json': '10f9c7ee281305e0e77f2318172c0705d977a5e72b8e0746b34e0cfeb50d1669',
    'results/task8/t8-pool-20261027/cube-pool-v2/manifest.json': 'a501c76edb29939782a7d7c7ac0e6d34fccc4756ed1fb4c510a2ef41769a0fc4',
    'results/task8/t8-exec-20261026/semantic-pool/index.json': 'a2071c66df7039f64e76ad729f2c0e398f918b9674c220153c0137247055a343',
    'results/task8/t8-pool-20261027/cube-pool-v2/evaluation-seeds.json': '8c7720078023734550c6a15c7f23b74f652adf14fb9120f3bc9639d2fcf4ad76',
}

def _check_hash(path, expected):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    actual=digest.hexdigest()
    if actual != expected:raise ValueError(f'frozen hash mismatch: {path}: {actual} != {expected}')
    return actual


def verify_frozen_manifest(artifact_root, *, source_root=None, inventory_path=None):
    """Check all 69 inventory files, all three actors/configs, and pool manifests.

    artifact_root contains results; source_root contains config/src/scripts.
    Container callers may mount those two roots separately, read-only artifacts.
    """
    root=Path(artifact_root)
    runtime_source=Path(__file__).resolve().parents[2]
    source=Path(source_root) if source_root else (root/'source' if (root/'source').exists() else runtime_source)
    if inventory_path is None:
        inventory_path=root/'logs/task9/t9-opt-design-20261031/parameter-inventory.json'
        if not inventory_path.exists():inventory_path=root/'inventory/parameter-inventory.json'
    _check_hash(inventory_path,INVENTORY_SHA256)
    inventory=json.loads(Path(inventory_path).read_text())
    entries=inventory['source_sha256']
    if len(entries)!=69:raise ValueError('frozen source inventory count mismatch')
    verified={}
    prefix='/home/ybc/projects/CL-FoReM/forem/'
    for original,expected in entries.items():
        if not original.startswith(prefix):raise ValueError('unexpected inventory source path')
        relative=original[len(prefix):]
        verified[relative]=_check_hash(source/relative,expected)
        if relative.startswith(('src/','config/','scripts/')):
            _check_hash(runtime_source/relative,expected)
    artifacts={name:_check_hash(root/name,expected) for name,expected in ARTIFACTS.items()}
    return dict(source_count=len(verified),sources=verified,artifacts=artifacts,inventory_sha256=INVENTORY_SHA256)


def validate_payload(payload):
    expected=dict(checkpoint='task7-lower-actor-v1',observation=VERSION,
                  action=ACTION_VERSION,synchronous=True)
    if not isinstance(payload,dict):raise ValueError('actor payload must be dictionary')
    for key,value in dict(format='task7-lower-actor-v1',observation_version=VERSION,
                          action_version=ACTION_VERSION,synchronous=True,vector_dim=74,
                          steps=5000000,step=5000000,versions=expected).items():
        if payload.get(key)!=value:raise ValueError(f'B3 actor metadata mismatch: {key}')
    if not isinstance(payload.get('policy'),dict):raise ValueError('missing actor policy')
    if any(not isinstance(v,torch.Tensor) or v.dtype!=torch.float32 or not torch.isfinite(v).all()
           for v in payload['policy'].values()):raise ValueError('invalid actor tensor dtype/value')


class FrozenB3:
    synchronous=True
    def __init__(self,device='cpu',artifact_root='/home/ybc/projects/CL-FoReM/forem',
                 *,source_root=None,inventory_path=None):
        self.device=torch.device(device)
        self.hash_report=verify_frozen_manifest(artifact_root,source_root=source_root,inventory_path=inventory_path)
        root=Path(artifact_root)
        self.actor_path=root/(RUN+'B3_5M-seed4718/final.actor.pt')
        self.config=json.loads((root/(RUN+'B3_5M-seed4718/config.json')).read_text())
        self.actor_sha256=ARTIFACTS[RUN+'B3_5M-seed4718/final.actor.pt']
        payload=torch.load(self.actor_path,map_location='cpu',weights_only=True)
        validate_payload(payload)
        # Network initialization consumes CPU RNG; loading a frozen policy must not.
        with torch.random.fork_rng(devices=[]):self.actor=Actor(74)
        self.actor.load_state_dict(payload['policy'],strict=True)
        self.actor.to(device=self.device,dtype=torch.float32).eval().requires_grad_(False)
        self.versions=dict(payload['versions'],checkpoint_step=5000000,checkpoint_sha256=self.actor_sha256)

    @torch.no_grad()
    def select_action(self,observation,deterministic=True):
        if deterministic is not True:raise ValueError('B3 is frozen deterministic only')
        shapes=dict(grid=(128,128,3),q=(6,),tcp=(7,),next_tcp=(7,),route_points=(15,3),
                    subgoal=(5,),synchronous=(1,),previous_action=(3,))
        batch=None
        for key,shape in shapes.items():
            x=observation.get(key)
            if not isinstance(x,torch.Tensor) or x.ndim!=len(shape)+1 or tuple(x.shape[1:])!=shape:
                raise ValueError(f'B3 observation shape: {key}')
            if batch is None:batch=x.shape[0]
            if x.shape[0]!=batch or x.dtype!=torch.float32 or x.device!=next(self.actor.parameters()).device or not torch.isfinite(x).all():
                raise ValueError(f'B3 observation dtype/device/value: {key}')
        if not (observation['synchronous']==1).all():raise ValueError('B3 requires synchronous observation')
        m,v=preprocess(observation)
        raw=self.actor.predict(m,v,eval=True)
        if not torch.isfinite(raw).all() or (raw.abs()>1).any():raise ValueError('invalid B3 action')
        return raw

    def __call__(self,observation):return self.select_action(observation,True)
