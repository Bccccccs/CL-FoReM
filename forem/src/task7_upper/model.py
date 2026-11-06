"""Phase-specific network assembly and gradient boundaries, task7.10 U.4; SRC-0501.

Actor objectives must use actor_q1/actor_q2 (detached); q1/q2 are Critic outputs.
No optimizer/loss/replay/temperature is implemented here. log_alpha belongs to
task7.22. Forward takes the VCM state; an optional VCM is registered for freezing
and trainable parameter enumeration. The default concrete VCM requires an explicit observation vector width.
"""
from torch import nn
from .vcm import VCM
from .candidate_encoder import CandidateEncoder
from .heads import Heads
from .bias import BiasLayer
from .world_model import WorldModel


class UpperModel(nn.Module):
    def __init__(self, candidate_encoder=None, *, critic_activation=nn.ReLU, vcm=None,
                 vector_dim=None, asynchronous=False):
        super().__init__()
        self.vcm = VCM(vector_dim=vector_dim, asynchronous=asynchronous) if vcm is None and vector_dim is not None else vcm
        self.candidate_encoder = CandidateEncoder(geometry_dim=7 if asynchronous else 6) if candidate_encoder is None else candidate_encoder
        self.head_a = Heads(critic_activation=critic_activation)
        self.head_b = Heads(critic_activation=critic_activation)
        self.bias = BiasLayer()
        self.world_model = WorldModel()
        self.random_world_model = WorldModel(random_frozen=True)
        self.copy_head_b_from_a()
        self.set_stage('1')

    def copy_head_b_from_a(self):
        """Call after stage1 checkpoint load and before entering stage3/G2/G3.

        set_stage intentionally does not overwrite already trained head B.
        """
        self.head_b.copy_from(self.head_a)

    def _groups(self):
        return {name: getattr(self, name) for name in
                ('vcm', 'candidate_encoder', 'head_a', 'head_b', 'bias', 'world_model')
                if getattr(self, name) is not None}

    def set_stage(self, stage):
        routes = {'1': {'vcm', 'candidate_encoder', 'head_a'}, '2': {'world_model'},
                  '3': {'bias', 'head_b', 'world_model'}, 'G2': {'head_b'},
                  'G3': {'bias', 'head_b'}, 'adapt': {'candidate_encoder', 'world_model'}}
        stage = str(stage)
        if stage not in routes:
            raise ValueError('Expected stage 1/2/3/G2/G3/adapt')
        self.stage = stage
        self._active_groups = routes[stage]
        for name, module in self._groups().items():
            module.requires_grad_(name in self._active_groups)
        self.random_world_model.requires_grad_(False)
        self.zero_grad(set_to_none=True)
        self.train(self.training)

    def train(self, mode=True):
        super().train(mode)
        if hasattr(self, '_active_groups'):
            for name, module in self._groups().items():
                module.train(mode and name in self._active_groups)
            self.random_world_model.eval()
        return self

    def trainable_parameters(self):
        return {name: tuple(p for p in module.parameters() if p.requires_grad)
                for name, module in self._groups().items() if name in self._active_groups}

    def forward_step(self, vcm_inputs, geometry, features, mask, *, reachable_radius=3.2):
        """One real recurrent decision; caller controls resets/prefix boundaries."""
        if self.vcm is None:
            raise ValueError("Register VCM or supply vector_dim before forward_step")
        state = self.vcm(**vcm_inputs)
        return self(state, geometry, features, mask, reachable_radius=reachable_radius)

    def forward(self, state, geometry, features, mask, *, reachable_radius=3.2):
        if self.stage != '1':
            state = state.detach()
        ctx, e, u = self.candidate_encoder(state, geometry, features, mask,
                                          reachable_radius=reachable_radius)
        h = prediction = None
        if self.stage in ('2', '3', 'adapt', 'G3'):
            wm = self.random_world_model if self.stage == 'G3' else self.world_model
            h, prediction = wm(ctx, e, u)
        corrected = self.bias(e, h) if self.stage in ('3', 'G3', 'adapt') else e
        head = self.head_a if self.stage in ('1', '2') else self.head_b
        # Adaptation uses prediction branch only; no policy gradient to candidates.
        policy_e = corrected.detach() if self.stage == 'adapt' else corrected
        actor_e = policy_e.detach() if self.stage == '1' else policy_e
        logits, q1, q2 = head(state, policy_e, actor_candidates=actor_e)
        return dict(logits=logits.masked_fill(~mask, -float('inf')), q1=q1, q2=q2,
                    actor_q1=q1.detach(), actor_q2=q2.detach(),
                    h=h, prediction=prediction, context=ctx, e=e, u=u,
                    corrected=corrected)
