#!/usr/bin/env python3
"""Task4 protocol and source permissions gate (no ROS required).
Protocol mode verifies the accepted Task3 baseline and nominal Task4 contracts.
Runtime mode additionally requires REAL Task4 files and rejects known forbidden call sites.
This conservative static gate is not a ROS graph/data-flow proof; 4.3/4.6 must test runtime isolation.
"""
import argparse
import ast
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
DENIED_TOPIC = re.compile(r'ground_truth|p3d|t265|/gazebo/(model_states|get_model_state)|camera[^\s]*odom', re.I)
FORMAL_FIELDS = ('freeze_id', 'training_seeds', 'steps_per_seed', 'gradient_updates_per_seed',
                 'wall_time_cap_s', 'tuning_attempts_cap', 'disk_cap_gib', 'checkpoint_schedule', 'evaluation_seeds_and_episodes')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_protocol(p, s):
    errors = []
    if p.get('schema') != 1 or s.get('schema') != 1:
        errors.append('schema')
    if p.get('estimator', {}).get('name') != 'open_vins' or p.get('pose_source') != 'openvins_stereo_imu':
        errors.append('unique_estimator')
    raw = [s['stereo'][side][key] for side in ('left', 'right') for key in ('topic', 'info_topic')] + [s['imu']['topic']]
    if any(DENIED_TOPIC.search(t) for t in raw) or len(set(raw)) != 5:
        errors.append('forbidden_pose_input')
    if p['permissions']['imu_fields'] != ['header.stamp', 'linear_acceleration', 'angular_velocity'] or s['imu']['absolute_orientation_usage'] != 'forbidden_even_if_plugin_populates_it':
        errors.append('imu_absolute_orientation')
    if any(v != 'estimate_TF' for v in p['permissions']['policy_base_dependencies'].values()):
        errors.append('truth_in_policy')
    if p['frames']['dynamic_publishers'] != ['pose_bridge'] or any(p['frames']['estimator_tf'].values()):
        errors.append('two_pose_publishers')
    init = p['initialization']
    if init['anchor_source'] != 'public_commanded_episode_initial_pose' or init['anchor_readback_from_simulator']:
        errors.append('truth_bootstrap')
    if init['policy_actions_during_bootstrap']:
        errors.append('bootstrap_policy_actions')
    if not p['identity']['reject_Task3_or_truth_checkpoints'] or not p['identity']['fresh_replay_optimizer_training']:
        errors.append('truth_checkpoint')
    if not s['stereo']['physical_two_viewpoints'] or s['stereo']['baseline_m'] <= 0:
        errors.append('fake_stereo')
    if s['stereo']['maximum_pair_skew_s'] != 0 or s['clock'] != 'simulation_time':
        errors.append('clock_or_sync')
    formal = p['budget']['formal']
    if formal['enabled'] and any(formal.get(k) is None for k in FORMAL_FIELDS):
        errors.append('formal_budget_unfrozen')
    return sorted(set(errors))


def verify_accepted_core(root, p):
    a = p['accepted_core']
    freeze = json.loads((root / a['freeze']).read_text())
    acceptance = json.loads((root / a['acceptance']).read_text())
    errors = []
    if not acceptance.get('ok') or acceptance.get('freeze_id') != a['freeze_id'] or freeze.get('freeze_id') != a['freeze_id']:
        errors.append('Task3_not_accepted')
    files = freeze['files']
    if len(files) != a['file_count']:
        errors.append('Task3_file_count')
    # Accepted baseline is immutable archived evidence; actual Task4 inherited tree
    # may differ only at individually hashed, explicitly reviewed paths.
    archive = root / a.get('archive', 'results/task3/freeze-archive/t3.6-core-freeze4/snapshot')
    deltas_path = root / 'config/task4/accepted_core_deltas.json'
    deltas = json.loads(deltas_path.read_text()) if deltas_path.is_file() else {}
    for rel, digest in files.items():
        accepted = archive / rel
        if not accepted.is_file() or sha(accepted) != digest:
            errors.append('Task3_archive_changed:' + rel)
        actual = root / rel
        allowed = deltas.get(rel, {})
        expected = allowed.get('new_sha256', digest)
        if allowed and (allowed.get('old_sha256') != digest or not allowed.get('reason') or not allowed.get('source')):
            errors.append('invalid_allowed_delta:' + rel)
        if not actual.is_file() or sha(actual) != expected:
            errors.append('Task4_undeclared_core_change:' + rel)
    if set(deltas) - set(files):
        errors.append('delta_outside_accepted_core')
    return errors


def scan_source(text, role):
    """Actual statements/launch wiring, not comments or a parallel mocked implementation."""
    errors = []
    if role in ('policy_python', 'imu_python'):
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Original evaluation helpers are inventoried; calling them from policy is forbidden below.
                if node.name in ('evaluation_truth', 'gazebo_model_names'):
                    continue
                body = ast.Module(body=node.body, type_ignores=[])
                for n in ast.walk(body):
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ('evaluation_truth', 'get_model_state'):
                        errors.append('truth_in_policy')
                    if isinstance(n, ast.Constant) and isinstance(n.value, str) and DENIED_TOPIC.search(n.value) and n.value.startswith('/'):
                        errors.append('forbidden_pose_input')
                    if role == 'imu_python' and isinstance(n, ast.Attribute) and n.attr.startswith('orientation'):
                        errors.append('imu_absolute_orientation')
        for n in ast.walk(tree):
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'POSE_SOURCE' for t in n.targets):
                if isinstance(n.value, ast.Constant) and n.value.value == 'gazebo_reference':
                    errors.append('truth_source_identity')
    elif role == 'imu_cpp':
        code = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
        if re.search(r'\bmsg\s*->\s*orientation\b', code):
            errors.append('imu_absolute_orientation')
        if 'initialize_with_gt(' in code or DENIED_TOPIC.search(code):
            errors.append('truth_in_estimator')
    elif role == 'launch_xml':
        root = ET.fromstring(text)
        nodes = list(root.iter('node'))
        bridges = [n for n in nodes if n.get('type') in ('pose_bridge.py', 'pose_adapter.py')]
        if len(bridges) != 1:
            errors.append('two_pose_publishers')
        for n in root.iter():
            if n.tag in ('arg', 'param', 'remap'):
                value = n.get('default', n.get('value', n.get('to', '')))
                name = n.get('name', n.get('from', ''))
                if name in ('pose_topic', 'input_topic') and DENIED_TOPIC.search(value):
                    errors.append('forbidden_pose_input')
                if name == 'pose_source' and value == 'gazebo_reference':
                    errors.append('truth_source_identity')
                if name in ('publish_global_to_imu_tf', 'publish_calibration_tf') and value.lower() not in ('false', '0'):
                    errors.append('two_pose_publishers')
    else:
        raise ValueError('unknown source role: ' + role)
    return sorted(set(errors))


def baseline_inventory(root):
    """Line-qualified migration obligations from current accepted source, not a claim that replacement exists."""
    points = {
      'scripts/task3_env.py': ['POSE_SOURCE =', 'def evaluation_truth', 'def gazebo_model_names', 'def _capture_spec'],
      'scripts/task3_identity.py': ['SRC_PACKAGES =', 'RUNTIME_FILES =', 'config:task3'],
      'scripts/task3_sac_entry.py': ['pose_source', 'Task3Env', 'task3'],
      'src/forem_husky/launch/husky_core.launch': ['pose_topic', 'pose_source', 'pose_bridge'],
      'src/modulation_rl/src/worlds.cpp': ['waitForTransform(', 'lookupTransform("map"', 'setModelState'],
      'src/modulation_rl/src/robot_env.cpp': ['world_->awaitTfs()', 'world_->getBaseTransformWorld()', 'desired_base_tf'],
      'src/modulation_rl/scripts/modulation/envs/combined_env.py': ['set_base_tf([30.0', 'draw_startpose_and_goal', 'get_local_map(robot_obs.base_tf', 'world_to_relative_tf(robot_obs.base_tf'],
      'src/modulation_rl/scripts/modulation/envs/map.py': ['_get_local_map_gt', '_get_local_map_from_costmap', 'draw_startpose_and_goal'],
    }
    out = []
    for rel, needles in points.items():
        path = root / rel
        for line, text in enumerate(path.read_text().splitlines(), 1):
            if any(n in text for n in needles):
                out.append({'path': rel, 'line': line, 'sha256': sha(path), 'statement': text.strip()})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage', choices=['protocol', 'runtime'], default='protocol')
    ap.add_argument('--root', type=Path, default=ROOT)
    ap.add_argument('--output', type=Path)
    ap.add_argument('--source', action='append', default=[], help='ROLE:actual/relative/file; runtime additionally requires all three roles')
    a = ap.parse_args()
    root = a.root.resolve()
    p = yaml.safe_load((root / 'config/task4/protocol.yaml').read_text())
    s = yaml.safe_load((root / 'config/task4/sensors.yaml').read_text())
    errors = validate_protocol(p, s) + verify_accepted_core(root, p)
    checks = []
    sources = list(a.source)
    if a.stage == 'protocol':
        sources.append('imu_cpp:' + p['estimator']['reference_callback'])
    else:
        roles = {v.split(':', 1)[0] for v in sources}
        if not {'policy_python', 'imu_cpp', 'launch_xml'} <= roles:
            errors.append('runtime_sources_incomplete')
    for value in sources:
        role, rel = value.split(':', 1)
        path = root / rel
        if not path.is_file():
            errors.append('source_missing:' + rel)
            continue
        found = scan_source(path.read_text(), role)
        checks.append({'path': rel, 'role': role, 'sha256': sha(path), 'errors': found})
        errors.extend(found)
    report = {'schema': 1, 'stage': a.stage, 'ok': not errors, 'errors': sorted(set(errors)),
              'protocol_hash': sha(root / 'config/task4/protocol.yaml'), 'sensor_hash': sha(root / 'config/task4/sensors.yaml'),
              'accepted_core_freeze': p['accepted_core']['freeze_id'], 'checked_sources': checks,
              'runtime_ready': False, 'runtime_ready_note': '4.1 does not prove live ROS graph, estimator build, isolation or accuracy',
              'baseline_migration_inventory': baseline_inventory(root)}
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(text + '\n')
    print(text)
    return 0 if report['ok'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
