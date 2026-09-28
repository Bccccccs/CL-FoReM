import numpy as np
import torch

from wm.dynamics import CopyModel, MLPDynamics, Normalizer, rollout
from wm.losses import block_mse


def random_policy_checkpoint(tmp_path):
    from model import GaussianPolicy
    from test_sac_updates import spaces
    obs, act = spaces()
    torch.manual_seed(0)
    policy = GaussianPolicy(obs[1], obs[0], 3, [256, 256], act, use_sde=False)
    path = tmp_path / 'policy.pt'
    torch.save({'policy_state_dict': policy.state_dict()}, path)
    return path, policy


def test_encoder_is_frozen_matches_actor_features_and_has_stable_dim(tmp_path):
    from wm.encoder import FixedEncoder
    path, policy = random_policy_checkpoint(tmp_path)
    enc = FixedEncoder(path)
    assert all(not p.requires_grad for p in enc.parameters())
    robot = np.random.default_rng(0).normal(size=(4, 41)).astype(np.float32)
    maps = np.random.default_rng(1).integers(0, 2, size=(4, 120, 120, 1)).astype(np.float32)
    h = enc(robot, maps)
    assert h.shape == (4, enc.dim) and enc.dim == 41 + enc.map_dim and not h.requires_grad
    with torch.no_grad():
        expected = torch.cat([torch.as_tensor(robot), policy.cnn(torch.as_tensor(maps).permute(0, 3, 1, 2))], -1)
    assert torch.allclose(h, expected, atol=1e-6)
    assert np.allclose(enc.encode_numpy(robot, maps, batch=3), h.numpy(), atol=1e-6)


def test_models_start_as_copy_and_action_changes_output_after_training_step():
    torch.manual_seed(0)
    z, a, dt = torch.randn(8, 50), torch.rand(8, 3) * 2 - 1, torch.full((8,), .1)
    m = MLPDynamics(50, use_action=True)
    assert torch.equal(m(z, a, dt), CopyModel()(z, a, dt))
    opt = torch.optim.SGD(m.parameters(), lr=.1)
    block_mse(m(z, a, dt), z + a.sum(1, keepdim=True), robot_dim=41)[0].backward()
    opt.step()
    assert not torch.allclose(m(z, a, dt), m(z, -a, dt))
    no_action = MLPDynamics(50, use_action=False)
    assert torch.equal(no_action(z, a, dt), no_action(z, -a, dt))


def test_save_load_prediction_identical(tmp_path):
    torch.manual_seed(1)
    m = MLPDynamics(50)
    for p in m.parameters():
        torch.nn.init.normal_(p, std=.1)
    torch.save(m.state_dict(), tmp_path / 'm.pt')
    m2 = MLPDynamics(50)
    m2.load_state_dict(torch.load(tmp_path / 'm.pt'))
    z, a, dt = torch.randn(3, 50), torch.randn(3, 3), torch.full((3,), .1)
    assert torch.equal(m(z, a, dt), m2(z, a, dt))


def test_open_loop_rollout_feeds_predictions_not_truth():
    calls = []

    class Recorder(torch.nn.Module):
        def forward(self, z, a, dt):
            calls.append(z.clone())
            return z + 1

    z0 = torch.zeros(2, 4)
    out = rollout(Recorder(), z0, torch.zeros(2, 5, 3), torch.full((2, 5), .1))
    assert out.shape == (2, 5, 4) and torch.equal(out[:, -1], torch.full((2, 4), 5.))
    assert [float(c[0, 0]) for c in calls] == [0, 1, 2, 3, 4]


def test_block_loss_weights_blocks_equally_and_normalizer_roundtrip():
    pred, target = torch.zeros(2, 141), torch.zeros(2, 141)
    target[:, :41] = 1.  # every robot dim wrong by 1, map perfect
    total, robot, maps = block_mse(pred, target)
    assert float(robot) == 1. and float(maps) == 0. and float(total) == 1.
    n = Normalizer(torch.arange(5.), torch.tensor([1., 2., 0., 4., 5.]))
    h = torch.randn(3, 5)
    assert torch.allclose(n.inverse(n(h)), h, atol=1e-5) and float(n.std[2]) == 1.
