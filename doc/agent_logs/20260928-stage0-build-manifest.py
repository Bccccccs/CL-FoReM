"""STAGE0-028 R0-2/R0-4: build a wm/data.py-compatible dataset.json from a
20260928-stage0-shard-eval.py output directory (which only copies observation npz files flat
into its output dir plus a summary manifest.json, not the collect_rollouts.py schema that
EpisodeDataset.from_manifest expects). Mirrors collect_rollouts.py's own manifest-building logic
exactly (same fields, same load_episode validation) so both loaders stay interchangeable.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src/modulation_rl/scripts'))
from wm.data import DataError, file_sha256, load_episode  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dir', required=True, help='shard-eval.py output directory')
    p.add_argument('--split', required=True, help='split label written into every episode record')
    a = p.parse_args()
    out = Path(a.dir)
    rows = [json.loads(line) for line in (out / 'episodes.jsonl').read_text().splitlines()]
    episodes = []
    for row in rows:
        seed = row['seed']
        rel = 'episode-%05d-observations.npz' % seed
        rec = dict(split=a.split, seed=seed, path=rel, usable=False,
                   primary_reason=row.get('primary_reason'), exception=row.get('exception'))
        full = out / rel
        if full.exists():
            try:
                ep = load_episode(full, seed)
                rec.update(sha256=file_sha256(full), steps=int(ep['action'].shape[0]),
                           valid_transitions=int(ep['n_valid']), complete=bool(ep['complete']),
                           terminated=bool(ep['terminated']), truncated=bool(ep['truncated']),
                           usable=ep['n_valid'] > 0)
            except DataError as exc:
                rec['validation_error'] = str(exc)
        else:
            rec['exception'] = rec.get('exception') or 'missing observations npz'
        episodes.append(rec)
    manifest = dict(task_id='STAGE0-028', split=a.split, source_dir=str(out), episodes=episodes,
                    counts=dict(planned=len(rows), usable=sum(e['usable'] for e in episodes)))
    (out / 'dataset.json').write_text(json.dumps(manifest, indent=1))
    print(json.dumps(manifest['counts'], indent=2))
    if manifest['counts']['usable'] < manifest['counts']['planned']:
        print('WARNING: %d/%d episodes unusable; see dataset.json for reasons' % (
            manifest['counts']['planned'] - manifest['counts']['usable'], manifest['counts']['planned']))


if __name__ == '__main__':
    main()
