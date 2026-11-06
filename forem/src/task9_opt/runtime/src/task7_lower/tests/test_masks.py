"""D14 integration uses the read-only Core; trainer stores terminal obs unchanged."""
import torch
from task7_sim.env import EpisodeEnv
from task7_sim.tests.test_env import factory,target
from task7_lower.replay import Replay
from task7_lower.observation import preprocess


def test_terminal_mask_and_old_subgoal_observation_before_reset():
    env=EpisodeEnv(1,factory,seed=47);env.reset();env.begin(target(env.core,.0075))
    tr=env.step(torch.zeros(1,3,dtype=torch.float64)).transition
    assert tr.done.item() and tr.mask.item()==0
    # Convert fixture dtype only; production environment/replay uses float32.
    o={k:v.float() for k,v in tr.observation.items()};n={k:v.float() for k,v in tr.next_observation.items()}
    r=Replay(2,75,47,'cpu');r.push(o,tr.raw_action.float(),tr.reward.float(),n,tr.mask.float())
    assert torch.equal(r.gather([0])[4],preprocess(n)[0]) and torch.equal(r.gather([0])[5],preprocess(n)[1])
    assert r.mask[0]==0
