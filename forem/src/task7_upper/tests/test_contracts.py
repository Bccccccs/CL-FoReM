"""Task7.21 contracts. Fixture architectures are NOT project VCM specifications."""
import copy
import os
import pytest
import torch
from torch import nn
from task7_upper import BiasLayer, Heads, WorldModel, CandidateEncoder, UpperModel, VCM


@pytest.fixture(scope='session', autouse=True)
def execution_device():
    if os.environ.get('TASK721_DEVICE') == 'cuda':
        assert torch.cuda.is_available()
        torch.cuda.set_per_process_memory_fraction(3.5 * 1024**3 / torch.cuda.get_device_properties(0).total_memory, 0)
        torch.set_default_device('cuda:0')
        yield
        torch.cuda.synchronize()
        print('GPU peak allocated bytes:', torch.cuda.max_memory_allocated())
        print('GPU peak reserved bytes:', torch.cuda.max_memory_reserved())
        torch.set_default_device('cpu')
    else:
        yield


def inputs(device=None, dtype=torch.float32, b=2, k=13, geometry_dim=6):
    torch.manual_seed(721)
    s = torch.randn(b, 128, device=device, dtype=dtype)
    c = torch.randn(b, k, geometry_dim, device=device, dtype=dtype)
    f = torch.randn(b, k, 19, device=device, dtype=dtype)
    f[..., 8] = 2.
    mask = torch.ones(b, k, device=device, dtype=torch.bool)
    return s, c, f, mask


def encoder(geometry_dim=6):
    # Explicit fixture choices pending specification; no adopted project defaults.
    return CandidateEncoder(geometry_dim=geometry_dim)


def model():
    return UpperModel(encoder(), critic_activation=nn.ReLU)


def has_grad(module):
    return any(p.grad is not None and p.grad.abs().sum() > 0 for p in module.parameters())


def test_zero_equivalence_and_counterexample():
    s, _, _, _ = inputs()
    e, h = torch.randn(2, 13, 128), torch.randn(2, 13, 128)
    a, b, psi = Heads(critic_activation=nn.ReLU), Heads(critic_activation=nn.ReLU), BiasLayer()
    b.copy_from(a)
    assert torch.equal(psi(e, h), e)
    for x, y in zip(a(s, e), b(s, psi(e, h))):
        assert torch.equal(x, y)  # float32 atol=rtol=0
    with torch.no_grad():
        psi.delta.weight.fill_(.02)
        psi.delta.bias.fill_(.4)
    assert not torch.equal(psi(e, h), e)
    assert not torch.equal(a(s, e)[0], b(s, psi(e, h))[0])


@pytest.mark.parametrize('stage', ['1', '2', '3', 'G2', 'G3', 'adapt'])
def test_trainable_sets_and_routes(stage):
    m = model()
    m.set_stage(stage)
    expected = {'1': {'candidate_encoder', 'head_a'}, '2': {'world_model'},
                '3': {'bias', 'head_b', 'world_model'}, 'G2': {'head_b'},
                'G3': {'bias', 'head_b'}, 'adapt': {'candidate_encoder', 'world_model'}}[stage]
    groups = m.trainable_parameters()
    assert set(groups) == expected
    assert {id(p) for v in groups.values() for p in v} == {id(p) for p in m.parameters() if p.requires_grad}
    s, c, f, mask = inputs()
    s.requires_grad_()
    out = m(s, c, f, mask, reachable_radius=1.)
    if stage == '1':
        out['logits'].square().mean().backward(retain_graph=True)
        assert not has_grad(m.candidate_encoder) and s.grad is None
        assert has_grad(m.head_a.actor) and not has_grad(m.head_a.q1)
        m.zero_grad(set_to_none=True)
        out['q1'].square().mean().backward()
        assert has_grad(m.candidate_encoder) and s.grad.abs().sum() > 0
    elif stage in ('3', 'G2', 'G3'):
        (out['logits'].square().mean() + out['q1'].square().mean()).backward(retain_graph=True)
        assert has_grad(m.head_b) and not has_grad(m.candidate_encoder)
        assert not has_grad(m.world_model) and s.grad is None
        if stage != 'G2':
            assert has_grad(m.bias.delta)
            # Gate gradient starts at zero because delta is zero, then becomes nonzero.
            assert not has_grad(m.bias.gate)
            with torch.no_grad(): m.bias.delta.weight.fill_(.01)
            m.zero_grad(set_to_none=True)
            out = m(s, c, f, mask, reachable_radius=1.)
            out['logits'].square().mean().backward(retain_graph=True)
            assert has_grad(m.bias.gate)
    if stage in ('2', '3', 'adapt'):
        m.zero_grad(set_to_none=True)
        out['prediction'].square().mean().backward()
        assert has_grad(m.world_model)
        assert has_grad(m.candidate_encoder) == (stage == 'adapt')
        assert not any(has_grad(x) for x in [m.head_a, m.head_b, m.bias])
        assert s.grad is None


@pytest.mark.parametrize('geometry_dim', [6, 7])
def test_padding_permutation_and_fixed_normalization(geometry_dim):
    m = encoder(geometry_dim).eval()
    s, c, f, mask = inputs(geometry_dim=geometry_dim)
    mask[:, 9:] = False
    ctx, e, u = m(s, c, f, mask, reachable_radius=2.)
    cc, ff = c.clone(), f.clone()
    cc[:, 9:] = float('nan'); ff[:, 9:] = float('nan')
    ctx2, e2, _ = m(s, cc, ff, mask, reachable_radius=2.)
    torch.testing.assert_close(ctx, ctx2, atol=0, rtol=0)
    torch.testing.assert_close(e[:, :9], e2[:, :9], atol=0, rtol=0)
    perm = torch.randperm(13)
    ctx3, e3, _ = m(s, c[:, perm], f[:, perm], mask[:, perm], reachable_radius=2.)
    torch.testing.assert_close(ctx, ctx3, atol=1e-6, rtol=1e-5)
    torch.testing.assert_close(e[:, perm], e3, atol=1e-6, rtol=1e-5)
    ctx4, e4, _ = m(s, c[:, :9], f[:, :9], mask[:, :9], reachable_radius=2.)
    torch.testing.assert_close(ctx, ctx4, atol=1e-6, rtol=1e-5)
    torch.testing.assert_close(e[:, :9], e4, atol=1e-6, rtol=1e-5)
    cg, nf = m.normalize(c, f, 2.)
    torch.testing.assert_close(cg[..., :2], c[..., :2]/3.2)
    torch.testing.assert_close(nf[..., 7], f[..., 7]/f[..., 8])
    torch.testing.assert_close(nf[..., 8], torch.ones_like(f[..., 8]))
    torch.testing.assert_close(nf[..., 12], f[..., 12]/3.2)
    assert not any(isinstance(x, nn.modules.batchnorm._BatchNorm) for x in m.modules())


def test_bias_detaches_h():
    m = BiasLayer()
    with torch.no_grad(): m.delta.weight.normal_()
    e, h = torch.randn(2, 128, requires_grad=True), torch.randn(2, 128, requires_grad=True)
    m(e, h).sum().backward()
    assert h.grad is None and e.grad is not None


def test_world_model_frozen_affine_and_target():
    w = WorldModel(random_frozen=True)
    s, c, _, _ = inputs()
    e, u = torch.randn(2, 13, 128), torch.randn(2, 13, 128)
    h, pred = w(s, e, u)
    assert pred.shape == (2, 13, 128) and not any(p.requires_grad for p in w.parameters())
    before = copy.deepcopy(w.state_dict())
    w.train()
    assert all(torch.equal(v, w.state_dict()[k]) for k, v in before.items())
    scale = torch.linspace(.5, 1.5, 128); shift = torch.linspace(-1., 1., 128)
    w.set_alignment(scale, shift)
    hh, pp = w(s, e, u)
    torch.testing.assert_close(hh, h*scale+shift, atol=0, rtol=0)
    assert not w.alignment_scale.requires_grad and not w.alignment_shift.requires_grad
    # Alignment only affects h sent to psi, not the random prediction head.
    assert torch.equal(pp, pred)
    w.requires_grad_(True)
    assert not any(p.requires_grad for p in w.parameters())
    enc = nn.Linear(3, 128)
    target = WorldModel.encode_target(enc, torch.randn(2, 3, requires_grad=True))
    assert not target.requires_grad


class FixtureEncoder(nn.Module):
    def __init__(self):
        super().__init__(); self.linear = nn.Linear(3, 128)
    def forward(self, x): return self.linear(x)


class FixtureRetrieval(nn.Module):
    def forward(self, v, entries, pose, step):
        return torch.stack([x.feature for x in entries]).mean(0) if entries else torch.zeros_like(v)


class FixtureGate(nn.Linear):
    def forward(self, v, ctx):
        return super().forward(torch.cat((v,ctx), dim=-1))


def vcm():
    # Fixture gate has bias2 per B.2, but its input choice is NOT specified/adopted.
    gate = FixtureGate(256, 128); nn.init.constant_(gate.bias, 2.)
    return VCM(FixtureEncoder(), FixtureRetrieval(), gate, action_result_dim=2)


def test_vcm_fifo_prefix_reset():
    torch.manual_seed(32)
    m = vcm()
    steps = [dict(observation=torch.randn(2, 3), action_result=torch.randn(2, 2),
                  pose=torch.zeros(2, 3), step=torch.full((2,), t), env_ids=[5, 8]) for t in range(7)]
    for x in steps: s = m(**x)
    assert [int(x.step) for x in m.memory[5]] == [3, 4, 5, 6]
    assert all(not x.feature.requires_grad for x in m.memory[5]) is False
    clone = vcm(); clone.load_state_dict(m.state_dict())
    rebuilt = clone.rebuild_prefix(steps)
    assert torch.equal(s, rebuilt) and not rebuilt.requires_grad
    assert not any(x.feature.requires_grad for x in clone.memory[5])
    assert not clone.hidden[5].requires_grad
    m.reset([5])
    assert 5 not in m.memory and 8 in m.memory
    fresh = vcm(); fresh.load_state_dict(m.state_dict())
    last = {k: (v[:1] if torch.is_tensor(v) else [5]) for k, v in steps[-1].items()}
    a = m(**last); b = fresh(**last)
    assert torch.equal(a, b)


def test_vcm_critic_actor_routing():
    m = UpperModel(encoder(), critic_activation=nn.ReLU, vcm=vcm())
    m.set_stage('1')
    s = m.vcm(torch.randn(2, 3), torch.randn(2, 2), torch.zeros(2, 3), torch.zeros(2), [0,1])
    _, c, f, mask = inputs()
    out = m(s, c, f, mask, reachable_radius=1.)
    out['logits'].square().mean().backward(retain_graph=True)
    assert not has_grad(m.vcm)
    out['q1'].square().mean().backward()
    assert has_grad(m.vcm)


@pytest.mark.parametrize('stage', ['1', '2', '3', 'G2', 'G3', 'adapt'])
def test_vcm_freeze_by_phase(stage):
    m = UpperModel(encoder(), critic_activation=nn.ReLU, vcm=vcm())
    m.set_stage(stage)
    assert all(p.requires_grad == (stage == '1') for p in m.vcm.parameters())
    if stage == '1': return
    state = m.vcm(torch.randn(2,3), torch.randn(2,2), torch.zeros(2,3), torch.zeros(2), [0,1])
    _, c, f, mask = inputs()
    out = m(state, c, f, mask, reachable_radius=1.)
    if stage in ('2', 'adapt'):
        out['prediction'].square().mean().backward()
    else:
        out['logits'].square().mean().backward()
    assert not has_grad(m.vcm)


def test_frozen_random_no_weight_update_and_serialization():
    m = model(); m.set_stage('G3')
    before = copy.deepcopy(m.random_world_model.state_dict())
    # Synthetic one-step optimizer verification, not model training.
    optim = torch.optim.SGD([p for group in m.trainable_parameters().values() for p in group], lr=.01)
    s,c,f,mask=inputs()
    m(s,c,f,mask,reachable_radius=1.)['logits'].square().mean().backward()
    optim.step()
    assert all(torch.equal(v,m.random_world_model.state_dict()[k]) for k,v in before.items())
    other=model(); other.load_state_dict(m.state_dict())
    for k,v in m.state_dict().items(): assert torch.equal(v,other.state_dict()[k])


def test_reject_empty_mask_and_bad_normalization():
    m=encoder()
    s,c,f,mask=inputs()
    with pytest.raises(ValueError): m(s,c,f,torch.zeros_like(mask),reachable_radius=1.)
    with pytest.raises(ValueError): m(s,c,f,mask,reachable_radius=0.)
    f[...,8]=0.
    with pytest.raises(ValueError): m(s,c,f,mask,reachable_radius=1.)


@pytest.mark.parametrize('stage', ['1', '3', 'G2', 'G3'])
def test_discrete_sac_actor_objective(stage):
    m = model(); m.set_stage(stage)
    s, c, f, mask = inputs(); s.requires_grad_()
    out=m(s,c,f,mask,reachable_radius=1.)
    log_pi=out['logits'].log_softmax(-1)
    pi=log_pi.exp()
    # U.3 exact discrete expectation. Actor values must not carry the Q graph.
    q=torch.minimum(out['actor_q1'],out['actor_q2'])
    loss=(pi*(.35*log_pi-q)).sum(-1).mean()
    loss.backward()
    head=m.head_a if stage=='1' else m.head_b
    assert has_grad(head.actor)
    assert not has_grad(head.q1) and not has_grad(head.q2)
    assert not has_grad(m.candidate_encoder) and not has_grad(m.world_model)
    assert s.grad is None
    if stage in ('3','G3'): assert has_grad(m.bias.delta)


@pytest.mark.parametrize('asynchronous', [False, True])
def test_variant_geometry_and_target_progress(asynchronous):
    # Catch missing target progress, wrong distance scale, or wrong variant width.
    width = 7 if asynchronous else 6
    m = UpperModel(asynchronous=asynchronous).eval()
    s, c, f, mask = inputs(geometry_dim=width)
    assert m.candidate_encoder.geometry[0].in_features == width
    c[..., :6] = torch.tensor([3.2, -1.6, .6, .8, 6.4, 1.])
    if asynchronous:
        c[..., 6] = 1.6  # target, deliberately different from rollout progress
        f[..., 12] = .32
    g, normalized_f = m.candidate_encoder.normalize(c, f, reachable_radius=1.)
    expected = [1., -.5, .6, .8, 2., 1.] + ([.5] if asynchronous else [])
    torch.testing.assert_close(g, torch.tensor(expected).expand_as(g))
    if asynchronous:
        torch.testing.assert_close(normalized_f[..., 12], torch.full_like(f[..., 12], .1))
        changed = c.clone(); changed[..., 6] = 0.
        with torch.no_grad():
            original = m(s,c,f,mask)
            other = m(s,changed,f,mask)
        assert not torch.equal(original['u'], other['u'])
    wrong = torch.zeros(*c.shape[:-1], 6 if asynchronous else 7)
    with pytest.raises(ValueError):
        m(s,wrong,f,mask)
