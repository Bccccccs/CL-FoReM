"""Fixed encoder E(o) = [robot_state | actor CNN(map)] taken from a trained SAC policy (P1a, D05).

The feature is exactly the actor's pre-FC concatenation, so P2 can inject corrections at the same interface.
E is frozen (no grad, eval mode) and identified by the checkpoint SHA-256.
"""
import numpy as np
import torch

from wm.data import ROBOT_DIM, MAP_SHAPE, ACTION_DIM, file_sha256


class FixedEncoder(torch.nn.Module):
    def __init__(self, checkpoint, device='cpu'):
        super().__init__()
        # Use the existing training encoder's deterministic backend in every consumer.
        torch.backends.cudnn.deterministic, torch.backends.cudnn.benchmark = True, False
        import gym
        from model import GaussianPolicy
        from checkpointing import load_trusted
        from p0_runner import checkpoint_hidden_sizes
        data = load_trusted(checkpoint, map_location='cpu')
        weights = data['agent']['policy'] if data.get('version') == 2 else data['policy_state_dict']
        map_space = gym.spaces.Box(0., 1., MAP_SHAPE, dtype=np.float32)
        rob_space = gym.spaces.Box(-np.inf, np.inf, (ROBOT_DIM,), dtype=np.float32)
        act_space = gym.spaces.Box(-1., 1., (ACTION_DIM,), dtype=np.float32)
        policy = GaussianPolicy(map_space, rob_space, ACTION_DIM, checkpoint_hidden_sizes(checkpoint), act_space, use_sde=False)
        policy.load_state_dict(weights)
        self.cnn = policy.cnn.to(device).eval()
        self.cnn.requires_grad_(False)
        self.device = torch.device(device)
        self.checkpoint_sha256 = file_sha256(checkpoint)
        self.map_dim = int(self.cnn.output_size)
        self.dim = ROBOT_DIM + self.map_dim
        cuda = self.device.type == 'cuda'
        self.numerical_identity = dict(
            torch_version=str(torch.__version__), numpy_version=np.__version__, device_type=self.device.type,
            torch_threads=torch.get_num_threads(), cuda_version=torch.version.cuda if cuda else None,
            cudnn_version=torch.backends.cudnn.version() if cuda else None,
            gpu_name=torch.cuda.get_device_name(self.device) if cuda else None,
            gpu_capability=list(torch.cuda.get_device_capability(self.device)) if cuda else None,
            cudnn_deterministic=torch.backends.cudnn.deterministic, cudnn_benchmark=torch.backends.cudnn.benchmark,
            cudnn_allow_tf32=torch.backends.cudnn.allow_tf32, matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32,
            matmul_precision=torch.get_float32_matmul_precision())

    @torch.no_grad()
    def forward(self, robot, local_map):
        robot = torch.as_tensor(robot, dtype=torch.float32, device=self.device)
        local_map = torch.as_tensor(local_map, dtype=torch.float32, device=self.device)
        x = local_map.permute(0, 3, 1, 2).contiguous(memory_format=torch.channels_last)
        return torch.cat([robot, self.cnn(x)], dim=-1)

    @torch.no_grad()
    def iter_numpy(self, robot, local_map, batch=128):
        if batch < 1:
            raise ValueError('encoding batch must be positive')
        for i in range(0, len(robot), batch):
            yield self(robot[i:i + batch], local_map[i:i + batch]).cpu().numpy()

    def encode_numpy(self, robot, local_map, batch=128):
        """Small reference API; production writes iter_numpy batches directly to disk."""
        out = np.empty((len(robot), self.dim), dtype=np.float32)
        start = 0
        for block in self.iter_numpy(robot, local_map, batch):
            out[start:start+len(block)] = block
            start += len(block)
        return out
