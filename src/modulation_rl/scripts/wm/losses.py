"""Block-balanced prediction losses: robot-state block and map-feature block averaged separately, then summed
with equal weight, so the larger map block cannot swamp the robot state (P1-A2)."""
import torch

from wm.data import ROBOT_DIM


def block_mse(pred, target, robot_dim=ROBOT_DIM, reduce=True):
    err = (pred - target) ** 2
    robot = err[..., :robot_dim].mean(-1)
    maps = err[..., robot_dim:].mean(-1)
    if reduce:
        robot, maps = robot.mean(), maps.mean()
    return robot + maps, robot, maps
