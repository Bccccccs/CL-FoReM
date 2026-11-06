"""Frozen deterministic lower actor; task7.20 / SRC-0491.

No optimizer or normalization updates. Checkpoint metadata is mandatory: callers
must supply the expected checkpoint contract, never infer it from tensor shapes.
"""
import hashlib
from pathlib import Path
import torch
from task7_lower.observation import VERSION as OBSERVATION_VERSION, preprocess

ACTION_VERSION='lower-action-l1-d8-v1'


class FrozenLowerPolicy:
    def __init__(self,actor,*,synchronous,checkpoint_version,step,checkpoint_sha256=None):
        self.actor=actor.eval().requires_grad_(False)
        self.synchronous=bool(synchronous)
        self.versions=dict(checkpoint=checkpoint_version,observation=OBSERVATION_VERSION,
                           action=ACTION_VERSION,synchronous=self.synchronous,
                           checkpoint_step=int(step),checkpoint_sha256=checkpoint_sha256)

    @classmethod
    def load(cls,path,*,synchronous,device,checkpoint_version,dtype=torch.float32):
        from task7_lower.networks import Actor
        payload=torch.load(path,map_location=device,weights_only=True)
        expected=dict(checkpoint=checkpoint_version,observation=OBSERVATION_VERSION,
                      action=ACTION_VERSION,synchronous=bool(synchronous))
        if payload.get('versions')!=expected:
            raise ValueError(f'lower checkpoint version mismatch: expected {expected}, got {payload.get("versions")}')
        actor=Actor(74 if synchronous else 75).to(device=device,dtype=dtype)
        actor.load_state_dict(payload['policy'],strict=True)
        return cls(actor,synchronous=synchronous,checkpoint_version=checkpoint_version,
                   step=payload['step'],checkpoint_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())

    @classmethod
    def load_stage_l(cls,path,*,synchronous,device,dtype=torch.float32):
        """Read the authorized local full Stage-L artifact, actor only.

        Full checkpoints contain Python environment/replay/RNG objects, so the
        read happens on CPU with mmap; no optimizer or saved RNG is restored.
        Missing action metadata is an incompatibility, not permission to guess.
        """
        from task7_lower.networks import Actor
        payload=torch.load(path,map_location='cpu',weights_only=False,mmap=True)
        cfg=payload.get('config',{})
        if (payload.get('format')!='task7-lower-full-v1' or
            payload.get('observation_version')!=OBSERVATION_VERSION or
            payload.get('action_version')!=ACTION_VERSION or
            cfg.get('synchronous')!=bool(synchronous)):
            raise ValueError('lower Stage-L checkpoint version mismatch (format/observation/action/variant)')
        actor=Actor(74 if synchronous else 75).to(device=device,dtype=dtype)
        actor.load_state_dict(payload['sac']['policy'],strict=True)
        digest=hashlib.sha256()
        with Path(path).open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
        return cls(actor,synchronous=synchronous,checkpoint_version=payload['format'],
                   step=payload['state']['steps'],checkpoint_sha256=digest.hexdigest())

    @torch.no_grad()
    def __call__(self,observation):
        if not (observation['synchronous']==float(self.synchronous)).all():
            raise ValueError('lower policy variant mismatch')
        m,v=preprocess(observation)
        parameter=next(self.actor.parameters())
        if m.device!=parameter.device or v.device!=parameter.device:
            raise ValueError('lower policy device mismatch')
        raw=self.actor.predict(m.to(parameter.dtype),v.to(parameter.dtype),eval=True)
        if not torch.isfinite(raw).all() or (raw.abs()>1).any():raise ValueError('invalid lower action')
        return raw.to(observation['q'].dtype)
