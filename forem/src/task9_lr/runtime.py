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
GROUP_AXES = {'C': ('lr_schedule', 'exp_updates'), 'L': ('lr_schedule', 'linear_transfers')}


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
    for entry in manifest.get('runtime_sources',[]):
        if sha256(PACKAGE_ROOT/entry['runtime'])!=entry['runtime_sha256']:
            raise RuntimeError('isolated runtime changed after origin sealing: '+entry['runtime'])


def artifact_files():
    paths = [p for p in PACKAGE_ROOT.rglob('*') if p.is_file()
             and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts]
    paths += list((ASSET_ROOT / 'scripts/task9_11').glob('*.py'))
    paths += [p for p in (ASSET_ROOT / 'config/task9/task9_11').rglob('*') if p.is_file()]
    return {str(p.relative_to(ASSET_ROOT)): sha256(p) for p in sorted(paths)}


def artifact_digest():
    return hashlib.sha256(json.dumps(artifact_files(), sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def source_contract():
    """Full isolated code/config identity replaces the old partial source list."""
    import os
    cache = os.environ.get('TASK8_SCENE_CACHE')
    if cache:
        raise RuntimeError('task9 LR forbids unreviewed runtime scene-cache override')
    verify_snapshot()
    return dict(format='task9-lr-full-contract-v1', files=artifact_files())


def import_manifest():
    result = {}
    for name, module in sorted(sys.modules.items()):
        location = getattr(module, '__file__', None)
        if location and name.split('.')[0] in {'task7_lower', 'task7_sim', 'task8_lower', 'task8_sim', 'task9_lr'}:
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


def validate_formal_config(config, *, smoke=False):
    group = config.get('group')
    seed = config.get('seed')
    if group not in GROUP_AXES or seed not in (4718, 4719):
        raise ValueError('unauthorized task9.11 arm or seed')
    expected = json.loads((ASSET_ROOT / f'config/task9/task9_11/{group}_seed{seed}.json').read_text())
    if smoke:
        expected['total_transfers'] = 1000
    if config != expected:
        raise ValueError('configuration differs outside exact B1-L matrix')
    if config.get('alpha_lr_schedule') != 'exp_updates':
        raise ValueError('explicit common alpha schedule required')
    entropy(config)


def validate_matrix():
    configs = {(a,s): json.loads((ASSET_ROOT / f'config/task9/task9_11/{a}_seed{s}.json').read_text())
               for a in ('C','L') for s in (4718,4719)}
    for (arm,seed), value in configs.items():
        validate_formal_config(value)
        counterpart = configs[('L' if arm=='C' else 'C',seed)]
        if {k for k in value if value[k] != counterpart[k]} != {'group','lr_schedule'}:
            raise ValueError('non-LR scientific difference')
    return configs
