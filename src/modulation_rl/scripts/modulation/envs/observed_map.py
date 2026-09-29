"""PH3-OBSMAP `observed-map-v1` (D60): the EE/base *planner* only knows the part of the map the robot has seen.

Everything else (SAC local map, collision, IK, reward, termination) keeps using the true map; only the
map object held by the planner (`planner._map`) is replaced by an `ObservedMapView`.

Semantics (spec: doc/agent_logs/20260929-ph3-obsmap-spec.md section 2.2)
  * The observed map starts empty at every `CombinedEnv.reset`; it is scanned once at the initial pose and
    after every robot step at the new pose.
  * A scan casts rays from the chassis centre over a field of view (`fov_deg`, centred on the chassis
    heading) up to `radius_m`. A ray stops after the first cell whose height is > `occlusion_height`
    (that cell itself is observed); lower obstacles can be looked over (a ~0.5 m high 3D sensor).
  * Observed cells carry their true height, unobserved cells are 0 (free, optimistic planning).
  * The planner sees `_floorplan_img` and `_floorplan_img_filled` multiplied by the observed mask, so the A*
    weights *and* the height interpolation of `_calc_6Dplan` only use observed information.
  * Planner weights are recomputed (same function as at the episode start, from the current chassis pose)
    only when a newly observed cell contains an obstacle.

Implementation choices not fixed by D60 (recorded in the task log): ray/radial sampling density, rounding of
sample points to the nearest cell, observed fraction over the whole grid, weight recomputation start = the
current chassis pose.
"""
import time

import numpy as np
from PIL import Image

from modulation.envs.map import Map

RAY_GAP_PX = 0.5          # max distance between neighbouring rays at the maximum range
RADIAL_STEP_PX = 0.5      # distance between samples along a ray
REROUTE_THRESHOLD_M = 0.3  # D60
REROUTE_WINDOW_STEPS = 20  # D60
_CHUNK_SAMPLES = 400_000   # bounds the transient memory of one scan chunk


# ---------------------------------------------------------------------------------------------- ray casting

def effective_radius_px(radius_px, shape, cx, cy):
    """Radius actually needed: the requested one, but not more than the farthest map corner (+1 px)."""
    h, w = shape
    corner = float(np.hypot(max(cx, w - 1 - cx), max(cy, h - 1 - cy)))
    return min(float(radius_px), corner + 1.0)


def cast_visible(heights, cx, cy, yaw, radius_px, fov_rad, occlusion_height):
    """Boolean HxW mask of the cells visible from pixel position (cx, cy) (column, row; rows grow downwards).

    heights          HxW array of obstacle heights (m); a cell with height > occlusion_height blocks the view
                     behind it (the blocking cell is visible itself).
    yaw              chassis heading in the world frame (y axis up); in pixel space the direction is (cos, -sin).
    fov_rad          field of view centred on the heading; >= 2*pi means all around.
    Samples outside the map end the ray and are never marked.
    """
    h, w = heights.shape
    visible = np.zeros((h, w), dtype=bool)
    r = effective_radius_px(radius_px, (h, w), cx, cy)
    if r <= 0:
        return visible
    full = fov_rad >= 2 * np.pi - 1e-9
    fov = 2 * np.pi if full else float(fov_rad)
    n_rays = int(np.ceil(fov / (RAY_GAP_PX / max(r, 1.0)))) + (0 if full else 1)
    n_rays = max(n_rays, 1)
    if full:
        angles = yaw + np.arange(n_rays) * (2 * np.pi / n_rays)
    elif n_rays == 1:
        angles = np.array([yaw])
    else:
        angles = yaw - fov / 2 + np.arange(n_rays) * (fov / (n_rays - 1))
    s = np.arange(0.0, r + 1e-9, RADIAL_STEP_PX)
    per_chunk = max(1, _CHUNK_SAMPLES // len(s))
    for i in range(0, n_rays, per_chunk):
        a = angles[i:i + per_chunk]
        px = cx + np.cos(a)[:, None] * s[None, :]
        py = cy - np.sin(a)[:, None] * s[None, :]
        ix = np.rint(px).astype(np.int32)
        iy = np.rint(py).astype(np.int32)
        inside = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
        hit = heights[np.clip(iy, 0, h - 1), np.clip(ix, 0, w - 1)] > occlusion_height
        block = hit | ~inside
        before = np.cumsum(block, axis=1, dtype=np.int32) - block   # blockers strictly before a sample
        seen = (before == 0) & inside
        visible[iy[seen], ix[seen]] = True
    return visible


def directed_path_deviation(new_xy, old_xy):
    """max over the points of the new path of the distance to the nearest point of the old path (metres).
    ~0 when the route did not change (the new path is then a piece of the old one)."""
    new = np.asarray(new_xy, dtype=np.float64)[:, :2]
    old = np.asarray(old_xy, dtype=np.float64)[:, :2]
    d2 = ((new[:, None, :] - old[None, :, :]) ** 2).sum(-1)
    return float(np.sqrt(d2.min(axis=1).max()))


# ---------------------------------------------------------------------------------------------- planner view

class ObservedMapView:
    """What the planner sees instead of the true `Map`.

    NOT a plain `__getattr__` proxy: `Map.get_inflated_map`, `binary_floorplan` and `in_collision` read
    `self._floorplan_img(_filled)` and the `self.inflated_map` cache, so they are bound to *this* object (own
    masked images, own cache) instead of forwarding to the true map's bound methods. Only immutable
    geometry/config attributes (resolution, origin, world type, ...) are forwarded.
    """
    # methods that read the map arrays or the inflation cache -> must run with self == view
    get_inflated_map = Map.get_inflated_map
    binary_floorplan = Map.binary_floorplan
    in_collision = Map.in_collision
    meter_to_pixels = Map.meter_to_pixels
    pixels_to_meter = Map.pixels_to_meter
    _build_occgrid_msg = Map._build_occgrid_msg

    def __init__(self, true_map):
        self._true = true_map
        self.inflated_map = dict()
        zeros = np.zeros(np.asarray(true_map._floorplan_img).shape, dtype=np.float32)
        self.set_content(zeros, zeros)

    def __getattr__(self, name):
        if name == '_true':
            raise AttributeError(name)
        return getattr(self._true, name)

    def set_content(self, img_array, filled_array):
        self._floorplan_img = Image.fromarray(np.ascontiguousarray(img_array, dtype=np.float32))
        self._floorplan_img_filled = Image.fromarray(np.ascontiguousarray(filled_array, dtype=np.float32))
        self.inflated_map.clear()

    def update(self, dt):
        """The planner calls this at reset; the view only changes through the manager's scans."""
        return False


# ---------------------------------------------------------------------------------------------- manager

class ObservedMapManager:
    """Per-env owner of the observed map, the planner hooks and the reroute statistics.

    observe=True  : observed-map-v1 (planner map replaced, weights recomputed on new obstacle content).
    observe=False : `--obsmap-log-reroutes` only: statistics on the untouched planner (nominal reference).
    stats=False   : skip the reroute bookkeeping (training).
    """

    def __init__(self, radius_m=0.0, fov_deg=270.0, occlusion_height=0.5, observe=True, stats=True):
        self.stats = bool(stats)   # False while training: no per-step reroute bookkeeping
        self.radius_m = float(radius_m)
        self.fov_rad = float(np.deg2rad(fov_deg))
        self.occlusion_height = float(occlusion_height)
        self.observe = bool(observe)
        self.view = None
        self._mask = None
        self._true_img = None
        self._true_filled = None
        self.new_episode()

    # -- episode state
    def new_episode(self):
        self.view = None
        self._mask = None
        self._true_img = self._true_filled = None
        self.step = 0
        self.weight_updates = 0
        self.seconds = []
        self._prev_plan = None
        self.reroute_steps = []
        self.reroute_dists = []
        self.kin_flags = []
        self.col_flags = []

    # -- scanning
    def _scan(self, base_tf, true_map):
        """Scan at `base_tf`; returns True when a newly observed cell contains an obstacle."""
        from modulation.envs.env_utils import quaternion_to_yaw
        if self._mask is None:
            self._true_img = np.asarray(true_map._floorplan_img, dtype=np.float32).copy()
            self._true_filled = np.asarray(true_map._floorplan_img_filled, dtype=np.float32).copy()
            self._mask = np.zeros(self._true_filled.shape, dtype=bool)
        cx, cy = true_map.meter_to_pixels(np.array(base_tf[:2], dtype=np.float64), round=False)
        radius_px = self.radius_m / true_map.global_map_resolution
        visible = cast_visible(self._true_filled, float(cx), float(cy), quaternion_to_yaw(base_tf[3:]),
                               radius_px, self.fov_rad, self.occlusion_height)
        new = visible & ~self._mask
        changed = bool(((self._true_filled[new] > 0) | (self._true_img[new] > 0)).any())
        self._mask |= visible
        return changed

    def _refresh_view(self):
        m = self._mask
        self.view.set_content(np.where(m, self._true_img, 0.0), np.where(m, self._true_filled, 0.0))

    @property
    def observed_fraction(self):
        return None if self._mask is None else float(self._mask.mean())

    # -- hooks called by CombinedEnv
    def on_planner_set(self, planner, base_tf, true_map):
        """Before `planner.reset()`: (re)scan at the current pose and hand the planner the observed view."""
        if not self.observe:
            return
        if not hasattr(planner, 'generate_base_feasible_eeweights'):
            raise NotImplementedError('observed-map-v1 needs a PointToPointPlanner (simpleobstacle task)')
        changed = self._scan(base_tf, true_map)
        if self.view is None:
            self.view = ObservedMapView(true_map)
            changed = True
        if changed:
            self._refresh_view()
        planner._map = self.view

    def on_plan(self, planner):
        """After a plan was generated (initial reset or a step): reroute statistics."""
        if not self.stats:
            return
        path = getattr(planner, '_last_global_plan_meters', None)
        if path is None:
            return
        xy = np.asarray(path, dtype=np.float64)[:, :2].copy()
        if self._prev_plan is not None and self.step > 0:
            d = directed_path_deviation(xy, self._prev_plan)
            if d > REROUTE_THRESHOLD_M:
                self.reroute_steps.append(self.step)
                self.reroute_dists.append(d)
        self._prev_plan = xy

    def on_step_robot(self, planner, base_tf):
        """After `robot.step`, before `generate_obs_step`: scan at the new pose, recompute weights if needed."""
        self.step += 1
        if not self.observe:
            return
        t0 = time.perf_counter()
        changed = self._scan(base_tf, planner._map._true)
        if changed:
            self._refresh_view()
            planner._weights = planner.generate_base_feasible_eeweights(
                base_tf=base_tf, gripper_goal_wrist=planner.gripper_goal_wrist)
            self.weight_updates += 1
        self.seconds.append(time.perf_counter() - t0)

    def on_step_end(self, robot_info):
        if not self.stats:
            return
        self.kin_flags.append(bool(robot_info.get('kin_failure', False)))
        self.col_flags.append(bool(robot_info.get('base_collision', False)))

    # -- episode summary (goes into episodes.jsonl)
    def summary(self):
        window = REROUTE_WINDOW_STEPS
        ik_hits = col_hits = 0
        for s in self.reroute_steps:      # step s produced the new route; look at steps s+1 .. s+window
            ik_hits += any(self.kin_flags[s:s + window])
            col_hits += any(self.col_flags[s:s + window])
        n = len(self.reroute_steps)
        return dict(obsmap_reroute_count=n,
                    obsmap_reroute_steps=list(self.reroute_steps),
                    obsmap_reroute_dists=[round(d, 4) for d in self.reroute_dists],
                    obsmap_weight_updates=self.weight_updates,
                    obsmap_post_reroute_ik_rate=(ik_hits / n) if n else None,
                    obsmap_post_reroute_collision_rate=(col_hits / n) if n else None,
                    obsmap_observed_fraction_final=self.observed_fraction,
                    obsmap_seconds_mean=float(np.mean(self.seconds)) if self.seconds else 0.0)
