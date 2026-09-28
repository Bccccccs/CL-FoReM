"""Regression for detached prior actor, broadcasting, and action transformations."""
import gym
import numpy as np
import pytest
import torch
from sac import SAC
from model import GaussianPolicy
from replay_memory import ReplayMemory


def spaces():
    return (gym.spaces.Tuple([gym.spaces.Box(-100, 100, (41,), dtype=np.float32),
                             gym.spaces.Box(-1, 1, (120, 120, 1), dtype=np.float32)]),
            gym.spaces.Box(-1, 1, (3,), dtype=np.float32))


def agent_cpu(monkeypatch):
    obs, act = spaces()
    return SAC(obs, act, 1, dict(device='cpu', gamma=.99, tau=.005, initial_alpha=.2,
               model={'custom_model_config': {'post_fcnet_hiddens': [256, 256]}}), 2000)


@pytest.mark.parametrize('batch', [1, 4])
@pytest.mark.parametrize('prior', [False, True])
def test_updates_actor_critic_but_not_frozen_prior(monkeypatch, batch, prior):
    torch.manual_seed(11)
    agent = agent_cpu(monkeypatch)
    reference = agent_cpu(monkeypatch)
    for p in reference.policy.parameters():
        p.requires_grad_(False)
    frozen = [p.detach().clone() for p in reference.policy.parameters()]
    before = [[p.detach().clone() for p in net.parameters()] for net in [agent.policy, agent.critic]]
    rng = np.random.RandomState(11)
    memory = ReplayMemory(8, 11)
    for _ in range(8):
        memory.push(rng.rand(120,120,1), rng.randn(41), rng.uniform(-.7,.7,3),
                    float(rng.randn()), rng.rand(120,120,1), rng.randn(41), 1.)
    for update in range(2):
        losses = (agent.update_parameters_modified(memory, batch, update, reference) if prior
                  else agent.update_parameters(memory, batch, update))
        assert np.isfinite(losses).all()
    for net, original in zip([agent.policy, agent.critic], before):
        grads = [p.grad for p in net.parameters() if p.grad is not None]
        assert grads and all(torch.isfinite(g).all() for g in grads)
        assert sum(g.abs().sum().item() for g in grads) > 0
        assert any(not torch.equal(p, old) for p, old in zip(net.parameters(), original))
    assert all(p.grad is None and torch.equal(p, old) for p, old in zip(reference.policy.parameters(), frozen))


def test_sample_predict_single_squash_and_scaled_density():
    torch.manual_seed(11)
    obs, _ = spaces()
    act = gym.spaces.Box(np.array([-2., 1., -3.]), np.array([4., 5., 1.]), dtype=np.float32)
    policy = GaussianPolicy(obs[1], obs[0], 3, [256,256], act, use_sde=False)
    maps, robots = torch.zeros(4,120,120,1), torch.zeros(4,41)
    with torch.no_grad():
        policy.mean_linear.bias.fill_(1.)
        policy.log_std_linear.bias.fill_(-2.)
    mean, _, _ = policy(maps, robots)
    expected = torch.tanh(mean) * torch.tensor([3.,2.,2.]) + torch.tensor([1.,3.,-1.])
    assert torch.allclose(policy.predict(maps, robots, True), expected)
    torch.manual_seed(22)
    sampled, logp = policy.sample(maps, robots)
    torch.manual_seed(22)
    assert torch.allclose(sampled, policy.predict(maps, robots, False))
    assert logp.shape == (4,1)
    assert torch.allclose(logp, policy.sample_with_action(maps, robots, sampled), atol=1e-4)
    assert (sampled >= torch.tensor(act.low)).all() and (sampled <= torch.tensor(act.high)).all()
    action = sampled.detach().requires_grad_()
    for p in policy.parameters():
        p.requires_grad_(False)
    grad = torch.autograd.grad(policy.sample_with_action(maps,robots,action).sum(),action)[0]
    assert torch.isfinite(grad).all() and grad.abs().sum() > 0
