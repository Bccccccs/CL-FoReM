"""Import isolation, immutable source identities and scientific configuration gates."""
import hashlib
import json
import math
from numbers import Real
from pathlib import Path
import sys

PACKAGE_ROOT = Path(__file__).resolve().parent
ASSET_ROOT = PACKAGE_ROOT.parents[1]
RUNTIME_ROOT = PACKAGE_ROOT / 'runtime'
GROUP_AXES = {'U20': ('update_every_transfers', 20),
              'E15': ('target_entropy', -1.5), 'R200': ('replay_capacity', 200000)}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def activate():
    """Fail closed on a pre-imported old package, then prefer only isolated copies."""
    source = (RUNTIME_ROOT / 'src').resolve()
    for name, module in tuple(sys.modules.items()):
        if name.split('.')[0] in {'task7_lower', 'task7_sim', 'task8_lower', 'task8_sim'}:
            location = getattr(module, '__file__', None)
            if location and not Path(location).resolve().is_relative_to(source):
                raise RuntimeError('old package already imported: ' + name + ': ' + location)
    sys.path.insert(0, str(source))
    verify_snapshot()
    return source


def verify_snapshot():
    manifest = json.loads((PACKAGE_ROOT / 'origin-manifest.json').read_text())
    for entry in manifest['files']:
        if sha256(PACKAGE_ROOT / 'frozen' / entry['origin']) != entry['sha256']:
            raise RuntimeError('raw frozen dependency changed: ' + entry['origin'])


def artifact_files():
    paths = [p for p in PACKAGE_ROOT.rglob('*') if p.is_file()
             and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts]
    paths += list((ASSET_ROOT / 'scripts').glob('task9_opt_*.py'))
    paths += [p for p in (ASSET_ROOT / 'config/task9/opt').rglob('*') if p.is_file()]
    return {str(p.relative_to(ASSET_ROOT)): sha256(p) for p in sorted(paths)}


def artifact_digest():
    return hashlib.sha256(json.dumps(artifact_files(), sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def source_contract():
    """Full isolated code/config identity replaces the old partial source list."""
    import os
    cache = os.environ.get('TASK8_SCENE_CACHE')
    if cache:
        raise RuntimeError('task9 opt forbids unreviewed runtime scene-cache override')
    verify_snapshot()
    return dict(format='task9-opt-full-contract-v1', files=artifact_files())


def import_manifest():
    result = {}
    for name, module in sorted(sys.modules.items()):
        location = getattr(module, '__file__', None)
        if location and name.split('.')[0] in {'task7_lower', 'task7_sim', 'task8_lower', 'task8_sim', 'task9_opt'}:
            path = Path(location).resolve()
            result[name] = dict(file=str(path), sha256=sha256(path))
    return result


def entropy(config):
    value = config.get('target_entropy', -3)
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError('target_entropy must be a finite real number')
    return float(value)


def scientific_config(config):
    result = dict(config)
    result['target_entropy'] = entropy(config)
    return result


def validate_formal_config(config):
    baseline = json.loads((PACKAGE_ROOT / 'frozen/config/task8/lower_train_B3_prim.json').read_text())
    group = config.get('group')
    if group not in GROUP_AXES or config.get('seed') not in (4718, 4719):
        raise ValueError('unauthorized group or seed')
    axis, value = GROUP_AXES[group]
    expected = dict(baseline, group=group, seed=config['seed'])
    expected[axis] = value
    if config != expected:
        raise ValueError('formal configuration differs outside exact B3 variant matrix')
    entropy(config)
