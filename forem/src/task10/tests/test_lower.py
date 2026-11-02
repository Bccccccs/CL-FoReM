"""Frozen real-artifact contract checks; no training or environment stepping."""
import os
from pathlib import Path
import pytest
import torch
from task7_lower.observation import preprocess
from task8_lower.sac import LowerSAC

ROOT = Path(os.environ.get('TASK10_ARTIFACT_ROOT', '/home/ybc/projects/CL-FoReM/forem'))

def observation(device='cpu'):
    gen = torch.Generator().manual_seed(17)
    result = {k: torch.randn(shape, generator=gen).to(device) for k, shape in {
        'q': (3,6), 'tcp': (3,7), 'next_tcp': (3,7),
        'route_points': (3,15,3), 'subgoal': (3,5),
        'previous_action': (3,3)}.items()}
    result['grid'] = torch.zeros(3,128,128,3,device=device)
    result['grid'][...,0] = 1
    result['grid'][...,1] = torch.tensor([.014,.015,3.],device=device)[:,None,None]
    result['grid'][...,2] = 1
    result['synchronous'] = torch.ones(3,1,device=device)
    return result

def test_all_frozen_hashes_and_geometry():
    from task10.lower import verify_frozen_manifest
    report = verify_frozen_manifest(ROOT)
    assert report['source_count'] == 69
    assert len(report['artifacts']) == 9

@pytest.mark.parametrize('device', ['cpu', pytest.param('cuda:0', marks=pytest.mark.skipif(not torch.cuda.is_available(), reason='CUDA unavailable'))])
def test_real_actor_matches_original_sac_and_freezes(device):
    from task10.lower import FrozenB3
    rng = torch.random.get_rng_state().clone()
    frozen = FrozenB3(device=device, artifact_root=ROOT)
    assert torch.equal(rng, torch.random.get_rng_state())
    original = LowerSAC(74, device, frozen.config)
    original.policy.load_state_dict(frozen.actor.state_dict())
    original.policy.eval()
    obs = observation(device)
    inputs = []
    hook = frozen.actor.mlp.register_forward_pre_hook(lambda _, x: inputs.append(x[0].detach().clone()))
    actual = frozen(obs)
    hook.remove()
    reference_inputs = []
    hook = original.policy.mlp.register_forward_pre_hook(lambda _, x: reference_inputs.append(x[0].detach().clone()))
    expected = original.select_action(obs, True)
    hook.remove()
    torch.testing.assert_close(actual, expected, atol=0, rtol=0)
    torch.testing.assert_close(inputs[0], reference_inputs[0], atol=0, rtol=0)
    assert actual.dtype == torch.float32 and actual.device == torch.device(device)
    assert not frozen.actor.training and not actual.requires_grad
    assert all(not p.requires_grad and p.grad is None for p in frozen.actor.parameters())
    m,v=preprocess(obs)
    assert m.shape == (3,128,128,3) and v.shape == (3,74)
    torch.testing.assert_close(m[:,0,0,1],torch.tensor([.01,.02,2.55],device=device),atol=0,rtol=0)
    print({'device':str(actual.device),'dtype':str(actual.dtype),'input_max_abs':float((inputs[0]-reference_inputs[0]).abs().max()),'output_max_abs':float((actual-expected).abs().max())})

@pytest.mark.parametrize('field,value', [('format','wrong'),('observation_version','wrong'),('action_version','wrong'),('synchronous',False),('vector_dim',75),('steps',3000000),('step',3000000),('versions',{})])
def test_metadata_mismatch_rejected(field,value):
    from task10.lower import FrozenB3, validate_payload
    frozen = FrozenB3(device='cpu',artifact_root=ROOT)
    payload=torch.load(frozen.actor_path,map_location='cpu',weights_only=True)
    payload[field]=value
    with pytest.raises(ValueError): validate_payload(payload)

def test_invalid_inputs_rejected_and_no_stochastic_path():
    from task10.lower import FrozenB3
    frozen=FrozenB3(device='cpu',artifact_root=ROOT)
    with pytest.raises(ValueError):frozen.select_action(observation(),False)
    for mutate in (lambda o:o.update(synchronous=torch.zeros(3,1)),
                   lambda o:o.update(q=o['q'].double()),
                   lambda o:o['grid'].fill_(float('nan')),
                   lambda o:o.update(route_points=torch.zeros(3,14,3))):
        obs=observation();mutate(obs)
        with pytest.raises(ValueError):frozen(obs)

def test_physical_action_order_and_inplace():
    from task7_sim.motion import actions
    raw=torch.tensor([[-1.,.5,-1.],[1.,-.7,1.]])
    u,w,v=actions(raw,True,torch.tensor([False,True]))
    torch.testing.assert_close(u,torch.tensor([.01,.3]))
    torch.testing.assert_close(w,torch.tensor([.5,0.]))
    torch.testing.assert_close(v,torch.tensor([-.3,0.]))


def test_hash_mismatch_stops(tmp_path):
    from task10.lower import _check_hash
    path=tmp_path/'changed';path.write_bytes(b'altered')
    with pytest.raises(ValueError,match='frozen hash mismatch'):
        _check_hash(path,'0'*64)
