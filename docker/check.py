"""Fail on broken project imports, compiled bindings or actual CUDA execution."""
import importlib
import json
import platform
import subprocess

import torch

subprocess.run(["python3", "-m", "pip", "check"], check=True)
modules = ["gym", "ray", "wandb", "OpenSSL", "pettingzoo", "pyastar",
           "rospy", "pybindings", "pybindings_robots", "model", "sac",
           "modulation.utils", "modulation.myray.ray_utils", "stable_baselines3",
           "vit_pytorch", "skimage", "imageio", "PIL", "pytest", "gpustat"]
module_paths = {}
for name in modules:
    module_paths[name] = importlib.import_module(name).__file__
assert module_paths["stable_baselines3"].startswith(
    "/root/mm_husky_ws/src/modulation_rl/scripts/stable_baselines3/"), module_paths
from pybindings_robots import RobotHusky

assert torch.cuda.is_available(), "CUDA is unavailable to a fresh process"
x = torch.randn(16, 16, device="cuda", requires_grad=True)
(x @ x.T).square().mean().backward()
torch.cuda.synchronize()
assert torch.isfinite(x.grad).all().item()
for package in ["modulation_rl", "husky_ur5", "bio_ik", "gazebo_ros",
                "ur_description", "velodyne_description", "lms1xx"]:
    subprocess.run(["rospack", "find", package], check=True)
print(json.dumps({"python": platform.python_version(), "torch": torch.__version__,
                  "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0),
                  "module_paths": module_paths, "cuda_forward_backward": "PASS"}, indent=2))
