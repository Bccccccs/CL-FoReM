import random
import numpy as np
import torch
from test_sac_updates import agent_cpu
from replay_memory import ReplayMemory


def test_checkpoint_restores_optimizer_schedule_temperature_rng_and_replay(monkeypatch, tmp_path):
    from checkpointing import save_training, load_training
    agent = agent_cpu(monkeypatch)
    memory = ReplayMemory(4, 11)
    for i in range(4):
        memory.push(np.full((120,120,1), .1*i), np.full(41,.1*i), np.ones(3)*.1,
                    float(i), np.zeros((120,120,1)), np.zeros(41), 1.)
    agent.update_parameters(memory, 2, 0)
    path = tmp_path/'training.pt'
    save_training(path, agent, memory, {'steps':4,'updates':1}, {'task':'test'})
    expected = (random.random(), np.random.rand(), torch.rand(2), memory.sample(2))
    second = agent_cpu(monkeypatch)
    restored = ReplayMemory(4, 99)
    report = load_training(path, second, restored, {'task':'test'})
    assert report['counters'] == {'steps':4,'updates':1}
    assert report['resume_kind'] == 'partial_environment_reset'
    actual = (random.random(), np.random.rand(), torch.rand(2), restored.sample(2))
    assert expected[:2] == actual[:2] and torch.equal(expected[2],actual[2])
    assert all(np.array_equal(a,b) for a,b in zip(expected[3],actual[3]))
    assert second.scheduler_policy_optim.state_dict() == agent.scheduler_policy_optim.state_dict()
    assert torch.equal(second.log_alpha,agent.log_alpha)
    # Identical next update proves optimizer/target/replay/RNG restoration, beyond weight loading.
    from checkpointing import capture_rng, restore_rng
    rng = capture_rng()
    loss1 = agent.update_parameters(memory,2,1)
    restore_rng(rng)
    loss2 = second.update_parameters(restored,2,1)
    assert np.allclose(loss1, loss2)
    assert all(torch.equal(a,b) for a,b in zip(agent.policy.parameters(),second.policy.parameters()))
