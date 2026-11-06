"""Schema4 geometry with an explicit ghost sensor detection mask.

Original body indexes, permission tables, zero-pair tables and FK are retained.
Only the two audited velodyne bodies are excluded from self collision checks.
"""
import copy
import torch
from task7_sim.robot import RobotGeometry
from task7_sim.geometry import to_box

SENSOR_BODIES = frozenset(('velodyne1_base_link', 'velodyne2_base_link'))


class GhostRobotGeometry(RobotGeometry):
    sensor_policy = 'ghost-v1'

    def __init__(self, data=None):
        super().__init__(copy.deepcopy(data) if data is not None else None)
        if self.data.get('schema') != 4:
            raise ValueError('ghost-v1 requires audited schema4 robot geometry')
        self._sensor_indices = tuple(i for i, body in enumerate(self.data['body'])
                                     if body['link'] in SENSOR_BODIES)
        if len(self._sensor_indices) != len(SENSOR_BODIES):
            raise ValueError('ghost-v1 requires both audited sensor bodies exactly once')

    def _sphere_collision(self, base, q):
        chunk = 256 if q.is_cuda else 64
        if len(q) > chunk:
            return torch.cat([self._sphere_collision(base[i:i+chunk], q[i:i+chunk])
                              for i in range(0, len(q), chunk)])
        key = ('ghost_sphere_checks', q.device)
        if key not in self._cache:
            groups = torch.tensor([s['group'] for s in self.data['self_spheres']], device=q.device)
            allowed = torch.tensor(self.data['self_body_allowed'], device=q.device, dtype=torch.bool)
            _, zero_body = self._zero_pair_masks(q.device)
            check = ~(allowed[groups] | zero_body)
            check[:, self._sensor_indices] = False
            self._cache[key] = torch.where(check)
        si, bj = self._cache[key]
        sp = self.self_spheres(base, q)
        arm = self._sphere_arm_collision(sp)
        boxes = self.body_boxes(base)[:, bj]
        points = to_box(sp[:, si, :3], boxes)
        body = ((points.abs()-boxes[..., 3:6]).clamp_min(0).square().sum(-1)
                <= sp[:, si, 3].square()).any(-1)
        return arm | body

    def self_contacts(self, base, q, *, masked=False):
        contacts = super().self_contacts(base, q, masked=masked)
        for index in self._sensor_indices:
            k = len(self.data['self_names'])+index
            contacts[:, k, :] = False
            contacts[:, :, k] = False
        return contacts

    def contacts(self, base, caps):
        contacts = super().contacts(base, caps)
        for index in self._sensor_indices:
            k = len(self.data['capsules'])+index
            contacts[:, k, :] = False
            contacts[:, :, k] = False
        return contacts
