"""Versioned, atomic P0 checkpoints; simulator state is explicitly not restored."""
import os
import random
from pathlib import Path
import numpy as np
import torch

SEMANTICS = 'p0-action-terminal-v2'


def load_trusted(path, map_location=None):
    """Load a project-produced checkpoint. Torch>=2.6 defaults to weights_only=True,
    which rejects the replay/RNG/config objects stored here; only use on our own files."""
    try:
        return torch.load(str(path), map_location=map_location, weights_only=False)
    except TypeError:  # torch<1.13 has no weights_only argument
        return torch.load(str(path), map_location=map_location)


def capture_rng():
    return dict(python=random.getstate(), numpy=np.random.get_state(), torch=torch.get_rng_state(),
                cuda=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [])


def restore_rng(state):
    random.setstate(state['python'])
    np.random.set_state(state['numpy'])
    torch.set_rng_state(state['torch'].cpu())
    if state['cuda'] and torch.cuda.is_available():
        torch.cuda.set_rng_state_all([s.cpu() for s in state['cuda']])


def save_training(path, agent, memory, counters, config, prior=None):
    names = ['policy', 'critic', 'critic_target', 'policy_optim', 'critic_optim',
             'alpha_optim', 'scheduler_policy_optim', 'scheduler_critic_optim']
    data = dict(version=2, semantics=SEMANTICS, resume_kind='partial_environment_reset',
                agent={n:getattr(agent,n).state_dict() for n in names},
                log_alpha=agent.log_alpha.detach(), alpha=agent.alpha,
                automatic_entropy_tuning=agent.automatic_entropy_tuning,
                prior_beta=agent.prior_beta, agent_config=agent.config,
                replay=dict(buffer=memory.buffer, position=memory.position, capacity=memory.capacity,
                            rng=memory.rng.getstate()),
                counters=dict(counters), config=config, rng=capture_rng(),
                prior=None if prior is None else prior.policy.state_dict())
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    torch.save(data,str(temp))
    os.replace(str(temp),str(path))


def load_training(path, agent, memory, config, prior=None):
    data = load_trusted(path,map_location='cpu')
    if data.get('semantics') != SEMANTICS or data.get('version') != 2:
        raise ValueError('Not a P0 training checkpoint; use explicit warm start')
    if data['config'] != config or data['agent_config'] != agent.config:
        raise ValueError('Resume configuration mismatch')
    if (data['prior'] is None) != (prior is None):
        raise ValueError('Resume prior mismatch')
    for name,state in data['agent'].items():
        getattr(agent,name).load_state_dict(state)
    with torch.no_grad():
        agent.log_alpha.copy_(data['log_alpha'].to(agent.device))
    agent.alpha = torch.as_tensor(data['alpha'],device=agent.device).detach()
    agent.automatic_entropy_tuning = data['automatic_entropy_tuning']
    agent.prior_beta = data['prior_beta']
    replay = data['replay']
    memory.buffer, memory.position, memory.capacity = replay['buffer'], replay['position'], replay['capacity']
    memory.rng.setstate(replay['rng'])
    if prior is not None:
        prior.policy.load_state_dict(data['prior'])
        prior.policy.requires_grad_(False)
        prior.policy.eval()
    restore_rng(data['rng'])
    return data
