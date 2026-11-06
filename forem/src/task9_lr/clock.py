"""Trusted host clock and isolated, protocol-bound synthetic epoch service.

Callers never supply an admission time. Fixture generations only translate the
host boot monotonic clock; they cannot slow it, rewind it, or affect real runs.
"""
import datetime as dt
import fcntl
import json
import math
import os
from pathlib import Path
import time
import uuid
from .runtime import sha256


def publish(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with tmp.open('x') as f:
            json.dump(value,f,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
        os.link(tmp,path)
        fd=os.open(path.parent,os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        if tmp.exists():tmp.unlink()
    return dict(path=str(path),sha256=sha256(path))


def finite(x):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x):raise ValueError('invalid clock number')
    return x


def boot():return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def initialize(root, epoch):
    """Low-level fixture setup, prior to freezing its binding in the protocol."""
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=False)
    return publish(root/'00000000.json',dict(format='task9-fixture-clock-v1',generation=0,
        previous=None,boot=boot(),offset=finite(epoch)-time.monotonic()))


def chain(protocol):
    binding=protocol.get('fixture_clock')
    if not binding:return None
    c=protocol.get('continuation',{});workspace=Path(c.get('host_workspace','/'))
    if protocol.get('execution_allowed') is not False or c.get('synthetic_fixture') is not True or not workspace.is_relative_to('/tmp') or workspace.resolve()!=workspace:
        raise ValueError('fixture clock prohibited outside isolated false-execution candidate')
    root=Path(binding['root'])
    if root.resolve()!=root or not root.is_relative_to(workspace) or Path(binding['anchor']['path'])!=root/'00000000.json':
        raise ValueError('fixture clock binding escaped workspace')
    files=sorted(root.glob('*.json'));result=[];previous=None
    for n,path in enumerate(files):
        if path.name!=f'{n:08d}.json':raise ValueError('fixture clock generation missing')
        item=json.loads(path.read_text())
        if n==0 and sha256(path)!=binding['anchor']['sha256']:raise ValueError('fixture clock anchor changed')
        if item.get('format')!='task9-fixture-clock-v1' or item.get('generation')!=n or item.get('previous')!=previous or item.get('boot')!=boot():raise ValueError('fixture clock chain/domain changed')
        offset=finite(item.get('offset'))
        if result and offset<result[-1]['offset']:raise ValueError('fixture clock rewind')
        result.append(item);previous=sha256(path)
    if not result:raise ValueError('fixture clock missing')
    return result


def advance(protocol, seconds):
    seconds=finite(seconds)
    if seconds<=0:raise ValueError('fixture clock must advance')
    root=Path(protocol['fixture_clock']['root'])
    with (root/'clock.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        items=chain(protocol);n=len(items)
        return publish(root/f'{n:08d}.json',dict(format='task9-fixture-clock-v1',generation=n,
            previous=sha256(root/f'{n-1:08d}.json'),boot=boot(),offset=items[-1]['offset']+seconds))


def capture(protocol):
    items=chain(protocol);mono=time.monotonic()
    if items:
        item=items[-1];offset=item['offset'];generation=item['generation']
        domain='fixture:'+protocol['fixture_clock']['anchor']['sha256']
    else:
        # A paired capture bounds the small system-clock/monotonic sampling skew.
        offset=time.time()-mono;generation=None;domain='system:'+boot()
    return dict(epoch=mono+offset,monotonic=mono,offset=offset,generation=generation,domain=domain,boot=boot())


def epoch(protocol):return capture(protocol)['epoch']

def now(protocol):return dt.datetime.fromtimestamp(epoch(protocol),dt.timezone.utc)


def validate_capture(protocol, value):
    if not isinstance(value,dict):raise ValueError('trusted clock capture missing')
    for key in ('epoch','monotonic','offset'):finite(value.get(key))
    if value.get('boot')!=boot() or abs(value['epoch']-value['monotonic']-value['offset'])>1e-5:raise ValueError('clock epoch/monotonic mapping invalid')
    items=chain(protocol)
    if items:
        n=value.get('generation')
        if isinstance(n,bool) or not isinstance(n,int) or not 0<=n<len(items) or value.get('offset')!=items[n]['offset'] or value.get('domain')!='fixture:'+protocol['fixture_clock']['anchor']['sha256']:raise ValueError('unbound fixture clock mapping')
    elif value.get('generation') is not None or value.get('domain')!='system:'+boot():raise ValueError('unbound system clock domain')
    return value


def validate_interval(protocol, start, finish):
    validate_capture(protocol,start);validate_capture(protocol,finish)
    if start['domain']!=finish['domain'] or start['generation']!=finish['generation'] or finish['monotonic']<start['monotonic'] or abs((finish['epoch']-start['epoch'])-(finish['monotonic']-start['monotonic']))>.05:
        raise ValueError('completion clock does not map to actual launch monotonic domain')
