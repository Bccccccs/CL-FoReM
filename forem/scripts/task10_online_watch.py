#!/usr/bin/env python3
"""Parent's read-only trial watcher, with durable monitoring/30-minute handoff."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import time
from zoneinfo import ZoneInfo
from task10_online_report import report


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);args=p.parse_args()
    run=args.run.resolve();forem=Path(__file__).resolve().parents[1]
    log=forem/'doc/agent_logs/task10/20261102-codex-online-trial.md'
    progress=forem/'doc/PROGRESS.md'
    last_handoff=time.monotonic()
    with (run/'monitor.jsonl').open('a') as stream:
        while True:
            value=report(run)
            compact={k:value[k] for k in ('status','completed_real_decisions','reserved_real_decisions','in_flight',
                'online_update_ledger','uniform_warmup_rows_in_execution_journal','last_completed_replay_count','completed_batches',
                'supervisor_wall_seconds','remaining_training_seconds')}
            compact.update(epoch=time.time(),watcher_pid=os.getpid())
            encoded=json.dumps(compact,allow_nan=False)
            stream.write(encoded+'\n');stream.flush();os.fsync(stream.fileno())
            print(encoded,flush=True)
            if time.monotonic()-last_handoff>=1800:
                stamp=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
                text=(f'\n{stamp} · 自动监控快照（父统一watcher，非新运行）：'
                    f'reserved/completed={value["reserved_real_decisions"]}/{value["completed_real_decisions"]}，'
                    f'inflight={value["in_flight"]}，在线updates={value["online_update_ledger"]}，'
                    f'已完成replay边界={value["last_completed_replay_count"]}，'
                    f'elapsed={value["supervisor_wall_seconds"]:.3f}s。'
                    '原截止不变，journal/账本/monitor.jsonl为原件，未恢复/重启/配对；[运行证据](../../SOURCES.md#src-t10-023)。\n')
                with log.open('a') as f:f.write(text)
                old=progress.read_text()
                progress.write_text(old.replace('# 当前进度\n','# 当前进度\n\n'+stamp+
                    f' **T10-ONLINE-TRIAL-20261102 · Codex · active监控**：真实完成{value["completed_real_decisions"]}/1200，'
                    f'在线更新{value["online_update_ledger"]}/200，inflight{value["in_flight"]}；'
                    '原7h截止不变，唯一运行继续，不重启。[原件/日志](agent_logs/task10/20261102-codex-online-trial.md) · [来源](SOURCES.md#src-t10-023)。\n',1))
                last_handoff=time.monotonic()
            if value['launch'].get('status')=='process_exited' or value['final_summary'] is not None:
                break
            time.sleep(30)
if __name__=='__main__':main()
