"""PH3-OBSMAP observed-map-v1 (D60): ray casting, occlusion, episode reset, no leakage into the planner
(A* weights and z interpolation), the view running Map methods with self == view, reroute statistics,
CLI plumbing and default-off behaviour."""
import json
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

import modulation.utils  # noqa: F401  (import order workaround for the native extension, see test_robotenv_mismatch.py)
import p0_runner
from modulation.envs import observed_map as om
from modulation.envs.eeplanner import PointToPointPlanner
from modulation.envs.map import Map


# ---- helpers ----------------------------------------------------------------------------------------

def fake_get_inflated_map(data, resolution, width, height, origin_vector, frame_id, inflation_radius, cost_scaling_factor):
    """Stand-in for the pybindings costmap inflation (its C++ calls ros::Time::now(), which needs a ROS node): dilate the
    occupied cells by the radius. What is under test is *which* array is inflated, not the inflation itself."""
    from scipy.ndimage import binary_dilation
    occupied = np.asarray(data).reshape(int(height), int(width)) > 0
    grown = binary_dilation(occupied, iterations=int(round(inflation_radius / resolution))) if occupied.any() else occupied
    return (grown * 100).astype(np.int8).ravel().tolist()


@pytest.fixture(autouse=True)
def _fake_costmap(monkeypatch):
    import modulation.envs.map as map_module
    monkeypatch.setattr(map_module, 'get_inflated_map', fake_get_inflated_map)


def cast(heights, cx, cy, yaw=0.0, radius=1e6, fov_deg=270.0, occ=0.5):
    return om.cast_visible(np.asarray(heights, dtype=np.float32), cx, cy, yaw, radius, np.deg2rad(fov_deg), occ)


def wall_map(h=101, w=101):
    return np.zeros((h, w), dtype=np.float32)


def make_true_map(filled, img=None, res=0.05):
    """A real Map object (real Map methods) without ROS: attributes set by hand."""
    m = object.__new__(Map)
    filled = np.asarray(filled, dtype=np.float32)
    img = filled if img is None else np.asarray(img, dtype=np.float32)
    m._floorplan_img = Image.fromarray(img.copy())
    m._floorplan_img_filled = Image.fromarray(filled.copy())
    m.global_map_resolution = res
    m.local_map_resolution = res
    m.max_map_height = 3.0
    m._world_type = 'sim'
    m.update_from_global_costmap = False
    m.inflation_radius_meter = 0.3
    m.inflated_map = dict()
    m._map_W_meter = res * filled.shape[1]
    m._map_H_meter = res * filled.shape[0]
    m._origin_W_meter, m._origin_H_meter, m._origin_Z_meter = m._map_W_meter / 2, m._map_H_meter / 2, 0
    m._map_frame_rviz = 'base_link'
    return m


# ---- ray casting -------------------------------------------------------------------------------------

def test_empty_map_is_fully_visible_with_a_full_circle_and_huge_radius():
    vis = cast(wall_map(), 50.0, 50.0, fov_deg=360.0)
    assert vis.all()


def test_field_of_view_excludes_what_is_behind_the_chassis():
    vis = cast(wall_map(), 50.0, 50.0, yaw=0.0, fov_deg=270.0, radius=40)
    assert vis[50, 70] and vis[50, 90]            # straight ahead (+x -> larger column)
    assert vis[20, 50] and vis[80, 50]            # both sides (+-90 deg)
    assert not vis[50, 30] and not vis[50, 10]    # straight behind (180 deg) is outside +-135 deg


def test_heading_is_measured_in_the_world_frame_with_y_up():
    # yaw = +90 deg looks north = up in the image = decreasing row index
    vis = cast(wall_map(), 50.0, 50.0, yaw=np.pi / 2, fov_deg=60.0, radius=40)
    assert vis[20, 50] and not vis[80, 50] and not vis[50, 80] and not vis[50, 20]


def test_radius_limits_the_view():
    vis = cast(wall_map(), 50.0, 50.0, fov_deg=360.0, radius=20)
    assert vis[50, 65] and vis[35, 50]
    assert not vis[50, 80] and not vis[10, 50] and not vis[5, 5]
    assert vis.sum() < 1.3 * np.pi * 20 ** 2       # a disc, not the whole map


def test_tall_obstacle_blocks_behind_but_is_seen_itself():
    m = wall_map()
    m[30:71, 60] = 3.0                              # 1-px thin tall wall in front of the robot
    vis = cast(m, 50.0, 50.0, fov_deg=360.0)
    assert vis[50, 60]                              # the blocking cell itself is observed
    assert vis[50, 59] and not vis[50, 61] and not vis[50, 80] and not vis[40, 75]
    assert vis[10, 62]                              # past the end of the wall it is visible again


def test_low_obstacle_can_be_looked_over_but_the_threshold_is_strict():
    m = wall_map()
    m[30:71, 60] = 0.3
    assert cast(m, 50.0, 50.0, fov_deg=360.0)[50, 80]          # 0.3 <= 0.5: not blocking
    m[30:71, 60] = 0.5
    assert cast(m, 50.0, 50.0, fov_deg=360.0)[50, 80]          # exactly the sensor height: not blocking (> H blocks)
    m[30:71, 60] = 0.6
    assert not cast(m, 50.0, 50.0, fov_deg=360.0)[50, 80]      # higher: blocks
    assert cast(m, 50.0, 50.0, fov_deg=360.0, occ=100.0)[50, 80]   # occlusion disabled


def test_full_visibility_setting_sees_every_cell_even_thin_obstacles():
    rng = np.random.default_rng(0)
    m = wall_map(120, 140)
    for _ in range(40):                              # thin (1 px) tall slivers all over the map
        y, x = rng.integers(2, 118), rng.integers(2, 130)
        m[y:y + rng.integers(1, 20), x] = 3.0
    vis = cast(m, 30.3, 60.7, yaw=0.7, radius=1e6, fov_deg=360.0, occ=100.0)
    assert vis.all()


def test_scan_ignores_rays_leaving_the_map():
    vis = cast(wall_map(30, 30), 2.0, 2.0, fov_deg=360.0, radius=1000)   # near the corner, huge radius
    assert vis.all()


# ---- view: methods run with self == view, no leaks ---------------------------------------------------------

def scene():
    """100x100 free map with a 0.3 m high 12x60 block (blocks a 'floor path' and the inflated map)."""
    filled = np.zeros((100, 100), dtype=np.float32)
    filled[20:80, 50:62] = 0.3
    return filled


def test_view_methods_use_the_view_arrays_and_own_inflation_cache():
    true = make_true_map(scene())
    view = om.ObservedMapView(true)
    inflated_true = true.get_inflated_map(ignore_below_height=0.0)
    inflated_view = view.get_inflated_map(ignore_below_height=0.0)
    assert inflated_true.max() > 0 and inflated_view.max() == 0          # nothing observed yet: free
    assert view.inflated_map is not true.inflated_map and len(view.inflated_map) == 1 and len(true.inflated_map) == 1
    assert not np.asarray(view.binary_floorplan(ignore_below_height=0.0)).any()
    assert not view.in_collision(np.array([0.0, 0.0]), use_inflated_map=True)
    # geometry helpers give the same answers as the true map
    p = np.array([[0.4, -0.7]])
    assert np.array_equal(view.meter_to_pixels(p), true.meter_to_pixels(p))
    assert view.global_map_resolution == true.global_map_resolution


def test_observing_makes_the_view_equal_the_truth_and_clears_the_cache():
    true = make_true_map(scene())
    view = om.ObservedMapView(true)
    view.get_inflated_map(ignore_below_height=0.0)
    assert len(view.inflated_map) == 1
    view.set_content(np.asarray(true._floorplan_img), np.asarray(true._floorplan_img_filled))
    assert len(view.inflated_map) == 0                                     # content changed -> cache dropped
    assert np.array_equal(view.get_inflated_map(ignore_below_height=0.0), true.get_inflated_map(ignore_below_height=0.0))
    assert view.update(dt=0.1) is False


def make_planner(map_obj, z_max=0.9):
    p = object.__new__(PointToPointPlanner)
    p._map = map_obj
    p._robot_config = dict(arm_range=0.5, z_max=z_max)
    p.use_fwd_orientation = False
    return p


def test_a_unobserved_obstacle_does_not_reach_the_astar_weights_and_appears_once_observed():
    true = make_true_map(np.pad(np.full((60, 12), 3.0, dtype=np.float32), ((20, 20), (50, 38))))
    base_tf, goal = [-2.0, 0.0, 0, 0, 0, 0, 1], [2.0, 0.0, 0.5, 0, 0, 0, 1]
    free = make_true_map(np.zeros((100, 100), dtype=np.float32))
    w_true = make_planner(true).generate_base_feasible_eeweights(base_tf=base_tf, gripper_goal_wrist=goal)
    w_free = make_planner(free).generate_base_feasible_eeweights(base_tf=base_tf, gripper_goal_wrist=goal)
    view = om.ObservedMapView(true)
    w_view = make_planner(view).generate_base_feasible_eeweights(base_tf=base_tf, gripper_goal_wrist=goal)
    assert not np.array_equal(w_true, w_free)
    assert np.array_equal(w_view, w_free)                                  # nothing leaked
    view.set_content(np.asarray(true._floorplan_img), np.asarray(true._floorplan_img_filled))
    assert np.array_equal(make_planner(view).generate_base_feasible_eeweights(base_tf=base_tf, gripper_goal_wrist=goal), w_true)


def test_height_interpolation_reads_the_observed_map_too():
    wall = np.zeros((100, 100), dtype=np.float32)
    wall[:, 48:54] = 0.3                                                   # low wall across the whole map: cannot be avoided
    true = make_true_map(wall)
    view = om.ObservedMapView(true)
    goal = [2.0, 0.0, 0.5, 0, 0, 0, 1]

    def z_profile(map_obj):
        p = make_planner(map_obj)
        p._weights = np.ones((100, 100), dtype=np.float32)                 # straight line path
        p._prev_plan = SimpleNamespace(next_gripper_tf=[-2.0, 0.0, 0.5, 0, 0, 0, 1])
        p.gripper_goal_wrist = goal
        return p._calc_6Dplan(goal, None)[:, 2]

    z_true, z_view = z_profile(true), z_profile(view)
    assert z_true.max() > 0.52                                             # the EE lifts over the (true) 0.3 m wall (+0.25 inflation)
    assert np.allclose(z_view, 0.5)                                        # the unobserved wall is not known
    view.set_content(np.asarray(true._floorplan_img), np.asarray(true._floorplan_img_filled))
    assert np.allclose(z_profile(view), z_true)


# ---- manager: episode state, weights recomputation ------------------------------------------------------------

class FakePlanner:
    def __init__(self, true):
        self._map = true
        self._weights = 'initial'
        self.gripper_goal_wrist = [2.0, 0.0, 0.5, 0, 0, 0, 1]
        self.calls = []
        self._last_global_plan_meters = None

    def generate_base_feasible_eeweights(self, base_tf, gripper_goal_wrist):
        self.calls.append(tuple(base_tf[:2]))
        return 'weights-%d' % len(self.calls)


def tf(x, y, yaw=0.0):
    return [x, y, 0.0, 0.0, 0.0, np.sin(yaw / 2), np.cos(yaw / 2)]


def obstacle_scene():
    filled = np.zeros((200, 200), dtype=np.float32)
    filled[95:105, 150:160] = 3.0        # tall block at x = +2.5..2.9 m (res 0.05, origin at the centre)
    return make_true_map(filled)


def test_weights_are_recomputed_only_when_an_obstacle_becomes_observed():
    true = obstacle_scene()
    mgr = om.ObservedMapManager(radius_m=2.0, fov_deg=270.0, occlusion_height=0.5)
    planner = FakePlanner(true)
    mgr.on_planner_set(planner, tf(-3.0, 0.0), true)                       # far from the block: nothing seen
    assert planner._map is mgr.view and not np.asarray(planner._map._floorplan_img_filled).any()
    mgr.on_step_robot(planner, tf(-2.9, 0.0))                              # more free space seen: no recompute
    assert planner.calls == [] and mgr.weight_updates == 0
    mgr.on_step_robot(planner, tf(1.0, 0.0))                               # block now within 2 m
    assert planner.calls == [(1.0, 0.0)] and planner._weights == 'weights-1' and mgr.weight_updates == 1
    assert np.asarray(planner._map._floorplan_img_filled).max() == 3.0
    mgr.on_step_robot(planner, tf(1.1, 0.0))                               # nothing new
    assert mgr.weight_updates == 1
    assert np.asarray(true._floorplan_img_filled).max() == 3.0             # the true map is untouched
    assert 0.0 < mgr.observed_fraction < 1.0


def test_new_episode_clears_the_observed_map():
    true = obstacle_scene()
    mgr = om.ObservedMapManager(radius_m=10.0, fov_deg=360.0, occlusion_height=0.5)
    planner = FakePlanner(true)
    mgr.on_planner_set(planner, tf(1.0, 0.0), true)
    assert mgr.observed_fraction > 0.5
    mgr.on_step_robot(planner, tf(1.0, 0.0))
    mgr.new_episode()
    assert mgr.view is None and mgr.observed_fraction is None and mgr.step == 0 and mgr.weight_updates == 0
    planner2 = FakePlanner(true)
    mgr.on_planner_set(planner2, tf(-4.0, -4.0), true)                     # radius 10 m still sees it: it is a fresh scan
    assert planner2._map is mgr.view and planner2._map is not planner._map


def test_set_ee_planner_in_the_middle_of_an_episode_keeps_the_observed_map():
    true = obstacle_scene()
    mgr = om.ObservedMapManager(radius_m=2.0, fov_deg=360.0, occlusion_height=0.5)
    p1 = FakePlanner(true)
    mgr.on_planner_set(p1, tf(1.0, 0.0), true)
    seen = mgr.observed_fraction
    p2 = FakePlanner(true)
    mgr.on_planner_set(p2, tf(-3.0, 3.0), true)
    assert p2._map is p1._map and mgr.observed_fraction > seen
    assert np.asarray(p2._map._floorplan_img_filled).max() == 3.0          # earlier observations kept


def test_log_only_mode_leaves_the_planner_untouched():
    true = obstacle_scene()
    mgr = om.ObservedMapManager(observe=False)
    planner = FakePlanner(true)
    mgr.on_planner_set(planner, tf(0.0, 0.0), true)
    mgr.on_step_robot(planner, tf(0.1, 0.0))
    assert planner._map is true and planner._weights == 'initial' and planner.calls == []
    assert mgr.observed_fraction is None and mgr.summary()['obsmap_observed_fraction_final'] is None


# ---- reroute statistics -----------------------------------------------------------------------------------

def line(x0, x1, y=0.0, n=40):
    return np.stack([np.linspace(x0, x1, n), np.full(n, y)], axis=1)


def test_directed_path_deviation():
    old = line(0, 4, n=81)                                                 # 0.05 m spacing like the A* path
    assert om.directed_path_deviation(old, old) < 1e-9
    assert om.directed_path_deviation(old[20:], old) < 1e-9                # a suffix of the old route: no reroute
    assert om.directed_path_deviation(line(1.01, 4, n=60), old) < 0.05     # slightly shifted samples stay far below 0.3 m
    assert om.directed_path_deviation(line(0, 4, y=0.5, n=81), old) == pytest.approx(0.5, abs=1e-6)
    detour = np.concatenate([line(0, 2, n=41), line(2.05, 4, y=1.0, n=40)])
    assert om.directed_path_deviation(detour, old) == pytest.approx(1.0, abs=1e-6)
    assert om.directed_path_deviation(old, detour) < 1.5                   # directed: the two directions differ


def test_reroute_threshold_counts_and_post_reroute_window():
    mgr = om.ObservedMapManager(observe=False)
    planner = FakePlanner(None)

    def plan(path):
        planner._last_global_plan_meters = np.hstack([path, np.zeros((len(path), 5))])
        mgr.on_plan(planner)

    plan(line(0, 4))                                                       # initial plan (step 0): nothing to compare
    fail_at = {8: (True, False), 40: (False, True)}
    for step in range(1, 61):
        mgr.on_step_robot(planner, tf(0, 0))
        if step == 5:
            plan(line(0.5, 4, y=0.31))                                     # 0.31 > 0.3 m -> reroute at step 5
        elif step == 30:
            plan(line(0.5, 4, y=0.66))                                     # a further 0.35 m -> second reroute
        elif step == 31:
            plan(line(0.5, 4, y=0.86))                                     # only 0.2 m from the previous route: no reroute
        else:
            plan(line(0.5, 4, y=mgr._prev_plan[0, 1]))                     # same route
        ik, col = fail_at.get(step, (False, False))
        mgr.on_step_end(dict(kin_failure=ik, base_collision=col))
    s = mgr.summary()
    assert s['obsmap_reroute_steps'] == [5, 30] and s['obsmap_reroute_count'] == 2
    # reroute at 5: IK failure at step 8 is inside steps 6..25 -> hit; reroute at 30: a collision at step 40 is inside 31..50
    assert s['obsmap_post_reroute_ik_rate'] == 0.5 and s['obsmap_post_reroute_collision_rate'] == 0.5
    assert s['obsmap_weight_updates'] == 0 and s['obsmap_seconds_mean'] == 0.0


def test_no_reroute_gives_none_rates():
    mgr = om.ObservedMapManager(observe=False)
    s = mgr.summary()
    assert s['obsmap_reroute_count'] == 0 and s['obsmap_post_reroute_ik_rate'] is None


# ---- CLI plumbing / default off ---------------------------------------------------------------------------

def base_args(**extra):
    return SimpleNamespace(checkpoint='c.pt', task='simpleobstacle', world_type='sim', device='cpu', seed=11, max_episode_steps=2000,
                           ik_mode='fixed', ik_iterations=100, policy_mode='deterministic', **extra)


def test_default_worker_command_has_no_obsmap_flags_and_they_forward_when_set(tmp_path):
    plain = p0_runner.episode_command(base_args(), tmp_path, 10000)
    assert not any(a.startswith('--obsmap') for a in plain)
    assert p0_runner.obsmap_flags(base_args()) == []
    assert p0_runner.obsmap_flags(base_args(obsmap_radius=0.0, obsmap_fov_deg=270.0, obsmap_occlusion_height=0.5,
                                            obsmap_log_reroutes=False)) == []
    cmd = p0_runner.episode_command(base_args(obsmap_radius=5.0, obsmap_fov_deg=200.0, obsmap_occlusion_height=0.4,
                                              obsmap_log_reroutes=False), tmp_path, 10000)
    assert cmd[cmd.index('--obsmap-radius') + 1] == '5.0' and cmd[cmd.index('--obsmap-fov-deg') + 1] == '200.0'
    assert cmd[cmd.index('--obsmap-occlusion-height') + 1] == '0.4' and '--obsmap-log-reroutes' not in cmd
    cmd = p0_runner.episode_command(base_args(obsmap_radius=0.0, obsmap_fov_deg=270.0, obsmap_occlusion_height=0.5,
                                              obsmap_log_reroutes=True), tmp_path, 10000)
    assert '--obsmap-log-reroutes' in cmd and '--obsmap-radius' not in cmd


def test_argparse_rejects_bad_obsmap_combinations(monkeypatch, tmp_path):
    def run(*argv):
        monkeypatch.setattr('sys.argv', ['p0_runner.py', *argv, '--output', str(tmp_path / 'o')])
        with pytest.raises(SystemExit):
            p0_runner.main()
    ev = ['eval', '--checkpoint', 'x', '--seeds', 'y']
    run('train', '--obsmap-log-reroutes')                                          # reroute logging is eval only
    run(*ev, '--obsmap-radius', '-1')
    run(*ev, '--obsmap-radius', '5', '--obsmap-fov-deg', '0')
    run(*ev, '--obsmap-radius', '5', '--obsmap-fov-deg', '400')
    run(*ev, '--obsmap-radius', '5', '--obsmap-occlusion-height', '-0.1')
    run(*ev, '--obsmap-radius', '5', '--task', 'dynObstacle')
    run(*ev, '--obsmap-log-reroutes', '--task', 'dynObstacle')
    run('train', '--obsmap-radius', '5', '--task', 'dynObstacle')
    run(*ev, '--obsmap-radius', '5', '--shield-config', 'z')
    run(*ev, '--obsmap-log-reroutes', '--latency-wm-comp', 'z')
    run(*ev, '--obsmap-radius', '5', '--dyn-freeze')
    run(*ev, '--obsmap-fov-deg', '200')                                            # parameters without the switch
    assert not (tmp_path / 'o').exists()


class FakeObsEnv:
    """Exposes what p0_runner.evaluate touches, plus the obsmap summary hook."""
    def __init__(self):
        self.map = SimpleNamespace(_floorplan_img=np.zeros((4, 4), dtype=np.float32))
        self.action_space = SimpleNamespace(seed=lambda s: None)
        self.unwrapped = SimpleNamespace(_ee_planner=SimpleNamespace(gripper_goal_wrist=[0., 0., 0.]),
                                         obsmap_summary=lambda: dict(obsmap_reroute_count=2))
        self.current_goal, self.goals, self.t = 0, [1], 0

    def seed(self, s): pass
    def get_robot_obs(self): return SimpleNamespace(base_tf=[0., 0., 0.])
    def reset(self):
        self.t = 0
        return [np.zeros(41, dtype=np.float32), np.zeros((120, 120, 1), dtype=np.float32)]

    def step(self, action):
        self.t += 1
        done = self.t >= 3
        info = dict(nr_base_collisions=0, nr_kin_failures=0, ee_done=done)
        return [np.zeros(41, dtype=np.float32), np.zeros((120, 120, 1), dtype=np.float32)], 0.0, done, info


class FakeAgent:
    def __init__(self):
        self.policy = SimpleNamespace(eval=lambda: None)

    def select_action(self, state, eval=False):
        return np.array([0.5, 0.25, -0.5], dtype=np.float32)


def run_evaluate(tmp_path, **flags):
    seeds = tmp_path / 'seeds.json'
    seeds.write_text('[10000, 10001]')
    ckpt = tmp_path / 'c.pt'
    ckpt.write_bytes(b'x')
    args = SimpleNamespace(seeds=str(seeds), episodes=2, save_observations=False, world_type='sim', task='simpleobstacle',
                           checkpoint=str(ckpt), max_episode_steps=50, policy_mode='deterministic', save_step_info=False,
                           shield_config=None, latency_wm_comp=None, **flags)
    out = tmp_path / 'out'; out.mkdir()
    p0_runner.evaluate(args, FakeAgent(), FakeObsEnv(), out, dict(ik_fail_thresh=10, time_step=.1))
    return [json.loads(l) for l in (out / 'episodes.jsonl').read_text().splitlines()]


def test_default_off_evaluate_adds_no_obsmap_field(tmp_path):
    rows = run_evaluate(tmp_path)
    assert rows and all(not any(k.startswith('obsmap') for k in r) for r in rows)


def test_evaluate_adds_the_summary_only_when_the_switch_is_on(tmp_path):
    (tmp_path / 'a').mkdir(); (tmp_path / 'b').mkdir(); (tmp_path / 'c').mkdir()
    rows = run_evaluate(tmp_path / 'a', obsmap_radius=3.0, obsmap_log_reroutes=False)
    assert all(r['obsmap_reroute_count'] == 2 for r in rows)
    rows = run_evaluate(tmp_path / 'b', obsmap_radius=0.0, obsmap_log_reroutes=True)
    assert all(r['obsmap_reroute_count'] == 2 for r in rows)
    rows = run_evaluate(tmp_path / 'c', obsmap_radius=0.0, obsmap_log_reroutes=False)
    assert all('obsmap_reroute_count' not in r for r in rows)


def test_training_mode_manager_skips_the_reroute_bookkeeping_but_still_observes():
    true = obstacle_scene()
    mgr = om.ObservedMapManager(radius_m=2.0, fov_deg=270.0, occlusion_height=0.5, stats=False)
    planner = FakePlanner(true)
    mgr.on_planner_set(planner, tf(0.0, 0.0), true)
    planner._last_global_plan_meters = np.hstack([line(0, 4), np.zeros((40, 5))])
    mgr.on_plan(planner)
    mgr.on_step_robot(planner, tf(1.0, 0.0))
    mgr.on_step_end(dict(kin_failure=True, base_collision=True))
    assert mgr._prev_plan is None and mgr.kin_flags == [] and mgr.col_flags == []
    assert mgr.weight_updates == 1 and planner._map is mgr.view                    # the planner still sees only the observed map
