"""Concrete SRC-0903 VCM: recurrence, reference math, and complete gradient paths."""
import copy
import math
import pytest
import torch
from torch import nn
from task7_upper import VCM, UpperModel, MemoryRetrieval
from task7_upper.tests.test_contracts import has_grad, inputs, execution_device

# Explicit synthetic observation layout; no environment adapter is asserted here.
VECTOR_DIM = 80


def sequence(batch=2, length=8, device=None, dtype=torch.float32, asynchronous=False):
    ids = list(range(batch))
    return [dict(observation=(torch.randn(batch, 3, 128, 128, device=device, dtype=dtype),
                              torch.randn(batch, VECTOR_DIM, device=device, dtype=dtype)),
                 action_result=torch.randn(batch, 24 if asynchronous else 23, device=device, dtype=dtype),
                 pose=torch.randn(batch, 3, device=device, dtype=dtype),
                 step=torch.full((batch,), t, device=device, dtype=torch.long), env_ids=ids)
            for t in range(length)]


@pytest.mark.parametrize('asynchronous', [False, True])
def test_real_vcm_fifo_prefix_reset_and_gru(asynchronous):
    torch.manual_seed(722)
    m = VCM(vector_dim=VECTOR_DIM, asynchronous=asynchronous)
    seq = sequence(asynchronous=asynchronous)
    for x in seq:
        previous = torch.stack([m.hidden.get(i, torch.zeros(128)) for i in x['env_ids']])
        s = m(**x)
        calibrated = torch.stack([m.memory[i][-1].feature for i in x['env_ids']])
        assert torch.equal(s, m.gru(torch.cat((calibrated, x['action_result']), -1), previous))
    assert [int(x.step) for x in m.memory[0]] == [4, 5, 6, 7]
    clone = VCM(vector_dim=VECTOR_DIM, asynchronous=asynchronous)
    clone.load_state_dict(m.state_dict())
    rebuilt = clone.rebuild_prefix(seq)
    assert torch.equal(s, rebuilt) and not rebuilt.requires_grad
    assert not clone.hidden[0].requires_grad
    assert all(not entry.feature.requires_grad for entry in clone.memory[0])
    m.reset([0]); assert 0 not in m.memory and 1 in m.memory
    fresh = VCM(vector_dim=VECTOR_DIM, asynchronous=asynchronous); fresh.load_state_dict(m.state_dict())
    item = dict(seq[-1]); item['env_ids'] = [0]
    item['observation'] = tuple(v[:1] for v in item['observation'])
    for key in ('action_result', 'pose', 'step'): item[key] = item[key][:1]
    assert torch.equal(m(**item), fresh(**item))
    # Empty history bypasses retrieval and gate, as in original SC²-WM.
    assert torch.equal(m.memory[0][-1].feature, m.f_enc(item['observation'])[0])
    m.reset(); assert not m.memory and not m.hidden


def test_retrieval_math_geometry_defaults_and_clamping():
    r = MemoryRetrieval()
    assert float(r.logit_scale) == pytest.approx(math.log(10))
    assert float(r.time_decay) == pytest.approx(.1)
    assert torch.count_nonzero(r.geometry[0].weight) == 0
    assert torch.count_nonzero(r.geometry[0].bias) == 0
    assert torch.count_nonzero(r.steps.weight) == 0
    current = torch.tensor([[1., 2., math.pi/2]])
    old = torch.tensor([[[1., 3., math.pi]]])
    g = r.relative_geometry(old, current)
    torch.testing.assert_close(g, torch.tensor([[[1., 0., 1., 0., 1.]]]), atol=1e-6, rtol=0)
    v, f = torch.randn(1, 128), torch.randn(1, 3, 128)
    poses = torch.randn(1, 3, 3); valid = torch.tensor([[True, True, False]])
    steps, now = torch.tensor([[-100, 10, -50]]), torch.tensor([3])
    delta = torch.tensor([[4, 0, 4]])
    encoded = f + r.geometry(r.relative_geometry(poses, current)) + r.steps(delta)
    scores = (r.q_proj(v)[:, None]*r.k_proj(encoded)).sum(-1)/math.sqrt(128)*r.logit_scale.exp() - r.time_decay.abs()*delta
    scores[:, 2] = -float('inf')
    x = r.attn_norm(v+(scores.softmax(-1)[..., None]*r.v_proj(encoded)).sum(1))
    expected = r.ffn_norm(x+r.ffn(x))
    actual = r.forward_batch(v,f,poses,steps,valid,current,now)
    torch.testing.assert_close(actual, expected, atol=0, rtol=0)
    # Nonzero geometry/time embeddings make wrong-frame or wrong-clamp implementations observable.
    with torch.no_grad():
        r.geometry[0].weight.normal_(std=.1); r.steps.weight.normal_(std=.1)
    assert not torch.equal(actual, r.forward_batch(v,f,poses,steps,valid,current,now))
    m = VCM(vector_dim=VECTOR_DIM)
    assert m.gru.input_size == 151
    assert torch.equal(m.gate.bias, torch.full_like(m.gate.bias, 2.))
    assert .00008 < float(m.gate.weight.std()) < .00012
    result = torch.arange(19.).reshape(1,19)
    prev = old[:,0]
    extra = VCM.previous_features(prev,current,result)
    torch.testing.assert_close(extra[:,:4], g[:,0,:4], atol=0,rtol=0)
    assert torch.equal(extra[:,4:], result)
    async_extra = VCM.previous_features(prev,current,result,torch.tensor([.6]))
    assert torch.equal(async_extra[:,4], torch.tensor([.6]))
    assert torch.equal(async_extra[:,5:], result)


@pytest.mark.parametrize('stage', ['1', '2', '3', 'G2', 'G3', 'adapt'])
@pytest.mark.parametrize('asynchronous', [False, True])
def test_full_recurrent_model_gradient_routes(stage, asynchronous):
    torch.manual_seed(723)
    m = UpperModel(vector_dim=VECTOR_DIM, asynchronous=asynchronous)
    m.set_stage(stage)
    expected = {'1': {'vcm','candidate_encoder','head_a'}, '2': {'world_model'},
                '3': {'bias','head_b','world_model'}, 'G2': {'head_b'},
                'G3': {'bias','head_b'}, 'adapt': {'candidate_encoder','world_model'}}[stage]
    assert set(m.trainable_parameters()) == expected
    seq = sequence(asynchronous=asynchronous)
    # T9: 4 steps no-gradient warmup, 4 steps with real recurrent graph.
    m.vcm.rebuild_prefix(seq[:4])
    assert not m.vcm.hidden[0].requires_grad
    _, c, f, mask = inputs(geometry_dim=7 if asynchronous else 6)
    outputs = [m.forward_step(item,c,f,mask) for item in seq[4:]]
    out = outputs[-1]
    if stage in ('1', '3', 'G2', 'G3'):
        losses=[]
        for o in outputs:
            lp=o['logits'].log_softmax(-1)
            losses.append((lp.exp()*(.35*lp-torch.minimum(o['actor_q1'],o['actor_q2']))).sum(-1).mean())
        sum(losses).backward(retain_graph=True)
        head = m.head_a if stage=='1' else m.head_b
        assert has_grad(head.actor) and not has_grad(head.q1) and not has_grad(head.q2)
        assert not has_grad(m.vcm) and not has_grad(m.candidate_encoder) and not has_grad(m.world_model)
        if stage in ('3','G3'): assert has_grad(m.bias.delta)
        m.zero_grad(set_to_none=True)
        sum(o['q1'].square().mean()+o['q2'].square().mean() for o in outputs).backward(retain_graph=True)
        assert has_grad(head.q1) and has_grad(head.q2) and not has_grad(head.actor)
        assert has_grad(m.vcm) == (stage=='1')
        assert has_grad(m.candidate_encoder) == (stage=='1')
        if stage=='1':
            for module in (m.vcm.f_enc.cnn, m.vcm.f_enc.fusion, m.vcm.retrieval.q_proj,
                           m.vcm.retrieval.k_proj, m.vcm.retrieval.v_proj, m.vcm.retrieval.ffn,
                           m.vcm.retrieval.geometry, m.vcm.retrieval.steps, m.vcm.gate, m.vcm.gru):
                assert has_grad(module)
            assert m.vcm.retrieval.time_decay.grad.abs() > 0
            assert m.vcm.retrieval.logit_scale.grad.abs() > 0
        assert not has_grad(m.world_model) and not has_grad(m.random_world_model)
    if stage in ('2','3','adapt'):
        m.zero_grad(set_to_none=True)
        target = m.world_model.encode_target(m.vcm.f_enc,seq[-1]['observation'])
        assert not target.requires_grad
        loss = (1-torch.nn.functional.cosine_similarity(out['prediction'][:,0],target,dim=-1)).mean()
        loss.backward()
        assert has_grad(m.world_model)
        assert has_grad(m.candidate_encoder) == (stage=='adapt')
        assert not any(has_grad(x) for x in (m.vcm,m.head_a,m.head_b,m.bias,m.random_world_model))


@pytest.mark.parametrize('asynchronous', [False, True])
def test_full_model_zero_switch_equivalence(asynchronous):
    m = UpperModel(vector_dim=VECTOR_DIM, asynchronous=asynchronous).eval()
    seq = sequence(asynchronous=asynchronous)
    _,c,f,mask=inputs(geometry_dim=7 if asynchronous else 6)
    with torch.no_grad():
        state=m.vcm.rebuild_prefix(seq)
        m.set_stage('1'); a=m(state,c,f,mask)
        m.copy_head_b_from_a();m.set_stage('3'); b=m(state,c,f,mask)
        errors = {}
        for key in ('logits','q1','q2'):
            errors[key] = float((a[key]-b[key]).abs().max())
            torch.testing.assert_close(a[key], b[key], atol=1e-6, rtol=1e-6)
        print('full-stage-switch float32 max_abs:', errors)
        # Isolate the identity invariant from a separately recomputed Transformer.
        assert torch.equal(m.bias(a['e'], b['h']), a['e'])
        for x,y in zip(m.head_a(state,a['e']),m.head_b(state,m.bias(a['e'],b['h']))):
            assert torch.equal(x,y)
        m.bias.delta.bias.fill_(.5)
        b=m(state,c,f,mask)
        assert not torch.equal(a['logits'],b['logits'])
