"""Task7.18.3 component checks; these do NOT replace the long-trajectory gate."""
import copy
import pytest
import torch
from task7_lower.sac import LowerSAC, soft_update
from task7_lower.speedup_candidates import CandidateSAC


def test_candidate_is_explicit_and_cuda_only():
    s=CandidateSAC(74,'cpu')
    assert s.update_backend=='eager'
    with pytest.raises(ValueError,match='unknown'):s.set_update_backend('unknown')
    with pytest.raises(ValueError,match='CUDA'):s.set_update_backend('async_checks')
    # Production LowerSAC exposes no candidate selection mechanism.
    assert not hasattr(LowerSAC,'set_update_backend')


@pytest.mark.skipif(not torch.cuda.is_available(),reason='requires allocated CUDA device')
def test_async_validation_preserves_sample_and_rng_1000():
    torch.manual_seed(7183)
    s=CandidateSAC(74,'cuda');s.set_update_backend('async_checks')
    # Actual batch256, same weights and varied fixed inputs. This isolates
    # validation from nondeterministic convolution BACKWARD accumulation.
    m=torch.rand(256,128,128,3,device='cuda');v=torch.rand(256,74,device='cuda')
    with torch.no_grad():
        for _ in range(1000):
            state=torch.cuda.get_rng_state()
            a=s.policy.sample(m,v);after=torch.cuda.get_rng_state()
            torch.cuda.set_rng_state(state);b=s._sample_update(m,v)
            assert all(torch.equal(x,y) for x,y in zip(a,b))
            assert torch.equal(after,torch.cuda.get_rng_state())


@pytest.mark.skipif(not torch.cuda.is_available(),reason='requires allocated CUDA device')
def test_target_graph_preserves_elementwise_formula_1000_and_state_load():
    torch.manual_seed(7183)
    s=CandidateSAC(74,'cuda');s.set_update_backend('async_checks_target_graph')
    target=copy.deepcopy(s.critic_target)
    with torch.no_grad():
        for i in range(1000):
            for p in s.critic.parameters():p.add_((i%3-1)*1e-7)
            soft_update(target,s.critic,s.tau);s._update_target()
            assert all(torch.equal(x,y) for x,y in zip(target.parameters(),s.critic_target.parameters()))
        # Loading updates the same parameter storage; graph must observe new
        # source/target values without retaining stale numerical state.
        saved=copy.deepcopy(s.full_state_dict());s.load_full_state_dict(saved)
        target.load_state_dict(saved['critic_target'])
        soft_update(target,s.critic,s.tau);s._update_target()
        assert all(torch.equal(x,y) for x,y in zip(target.parameters(),s.critic_target.parameters()))
