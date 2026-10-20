"""Pure helpers shared by the Task3 checks and their unit tests (no ROS/torch imports)."""
import math

ALLOWED_TF_AUTHORS = frozenset({"/pose_bridge", "/robot_state_publisher"})
POLICY_EDGE = ("odom", "base_footprint")


def yaw_of(q):
    """Yaw of quaternion (x, y, z, w)."""
    return math.atan2(2.0 * (q[3] * q[2] + q[0] * q[1]), 1.0 - 2.0 * (q[1] ** 2 + q[2] ** 2))


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def tf_authority(callers):
    """callers: {node_name: iterable of (parent, child) edges it published on /tf}.

    Returns dict(odom_base_authors=[...], unique=bool, allowed=bool). The policy-facing base pose edge odom->base_footprint
    must have exactly one publisher (the pose bridge), and /tf may only be published by the allowed nodes."""
    authors = sorted(c for c, edges in callers.items() if POLICY_EDGE in set(edges))
    return dict(odom_base_authors=authors, unique=authors == ["/pose_bridge"], allowed=set(callers) <= ALLOWED_TF_AUTHORS)
