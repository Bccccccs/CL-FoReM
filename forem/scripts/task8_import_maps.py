#!/usr/bin/env python3
"""Offline task8 mapgen importer; exit 1 preserves all per-map errors."""
import argparse
import json
from task8_sim.import_mapgen import import_pool


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    report = import_pool(args.source, args.output)
    print(json.dumps({'ok':report['ok'], 'map_count':len(report['maps']),
                      'validated_count':sum(m['status']=='validated' for m in report['maps']),
                      'output':args.output}))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
