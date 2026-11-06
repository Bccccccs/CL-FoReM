"""Small actor-only handoff for task7.20; no lower_policy.py is owned here."""
import torch
from .networks import Actor
from .observation import VERSION,ACTION_VERSION,preprocess

class DeterministicActor:
    def __init__(self,path,device='cuda'):
        s=torch.load(path,map_location=device,weights_only=False)
        if s['format']!='task7-lower-actor-v1' or s['observation_version']!=VERSION or s.get('action_version')!=ACTION_VERSION:raise ValueError('lower actor format mismatch')
        self.synchronous=s['synchronous'];self.steps=s['steps'];self.observation_version=VERSION
        self.policy=Actor(s['vector_dim']).to(device);self.policy.load_state_dict(s['policy']);self.policy.eval()
    @torch.no_grad()
    def __call__(self,observation):
        """Batched Core observation -> deterministic raw Tensor[E,3], same device.
        Caller supplies float32 Core fields on the actor device. Quantization is
        always D20 v1, identical to replay decoding during training.
        """
        m,v=preprocess(observation);return self.policy.predict(m,v,True)
