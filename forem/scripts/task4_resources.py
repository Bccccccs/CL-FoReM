"""Durable campaign WAL. No checkpoint training resume; retries consume one stable ledger."""
import fcntl
import hashlib
import json
import math
import os
import time
from pathlib import Path
from task0_proc import identity, proc_stat

class ResourceExceeded(RuntimeError):
    pass

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def own_alive(owner):
    """PID, kernel start, command and non-zombie state match before any signal."""
    if not owner:
        return False
    found = identity(owner['pid'])
    st = proc_stat(owner['pid'])
    return bool(found == owner and st and st[3] != 'Z')

def atomic_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp-' + str(os.getpid()))
    with temporary.open('w') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)
    fd = os.open(str(path.parent), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

class DiskMeter:
    """Full-tree disk scans at most once per interval per path (task4.5 r2, SRC0153); caps unchanged."""
    def __init__(self, interval_s=30.0, clock=time.monotonic, scanner=None):
        self.interval_s, self.clock, self.scanner, self.cache = interval_s, clock, scanner, {}
    def measure(self, path):
        now = self.clock(); key = str(path); hit = self.cache.get(key)
        if hit is None or now - hit[0] >= self.interval_s:
            hit = (now, (self.scanner or bytes_under)(path)); self.cache[key] = hit
        return hit[1]


def bytes_under(path):
    root = Path(path)
    total = 0
    if root.is_symlink():
        raise ResourceExceeded('resource root must not be symlink')
    for p in root.rglob('*') if root.exists() else ():
        if p.is_file() and not p.is_symlink():
            try:
                total += p.stat().st_size
            except FileNotFoundError:
                pass
    return total

class Ledger:
    def __init__(self, path, cfg, freeze_id, clock=time.time):
        self.path, self.cfg, self.clock = Path(path), cfg, clock
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = open(str(self.path) + '.lock', 'a')
        self.closed = False
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            anchor = Path(str(self.path) + '.campaign-anchor')
            if anchor.exists() and not self.path.exists():
                raise ResourceExceeded('existing campaign ledger missing; never recreate/reset budget')
            if not anchor.exists():
                atomic_write(anchor, {'freeze_id': freeze_id, 'budget_sha256': digest(cfg)})
            if json.loads(anchor.read_text()) != {'freeze_id': freeze_id, 'budget_sha256': digest(cfg)}:
                raise ResourceExceeded('stable campaign anchor/config/freeze mismatch')
            self.data = json.loads(self.path.read_text()) if self.path.exists() else {
                'schema': 2, 'freeze_id': freeze_id, 'budget_sha256': digest(cfg),
                'spent_training_s': 0.0, 'spent_evaluation_s': 0.0,
                'spent_all_s': 0.0, 'jobs': [], 'active': None, 'session': None,
                'selected': {}, 'checkpoints': {}, 'validation': {}, 'test': {},
                'campaign_finalized': False,
            }
            if self.data.get('schema') != 2 or self.data['freeze_id'] != freeze_id or self.data['budget_sha256'] != digest(cfg):
                raise ResourceExceeded('existing global ledger/config/freeze mismatch; never reset or migrate budget')
            active = self.data['active']
            session = self.data.get('session')
            if session and own_alive(session['owner']):
                raise ResourceExceeded('previous actual campaign owner remains alive')
            if active and active.get('suspended'):
                if own_alive(active['owner']):
                    raise ResourceExceeded('previous actual job owner remains alive')
                active = None  # resumable training job (SRC0155); resumed explicitly by resume()
            if active:
                if own_alive(active['owner']):
                    raise ResourceExceeded('previous actual job owner remains alive')
                # Last fsynced lower bound cannot measure crash tail. Charge the cap,
                # retaining observed wall time separately as a measured lower bound.
                self.finish('interrupted_failed', crash=True)
            if session:
                observed = session.get('observed_s', 0.0)
                elapsed_upper = min(self.cfg['all_wall_total_cap_s'], max(0.0, self.clock() - session['started_unix']))
                charged = max(observed, elapsed_upper)
                self.data['spent_all_s'] += charged
                self.data.setdefault('interrupted_sessions', []).append(dict(session, measured_wall_lower_bound_s=observed, charged_wall_s=charged, note='crash tail and downtime conservatively charged; not measured runtime'))
                self.data['session'] = None
            self.save()
        except BaseException:
            self.lock.close()
            self.closed = True
            raise

    def save(self):
        jobs=list(self.data['jobs'])
        if self.data.get('active'):
            jobs[self.data['active']['job_index']]=self.data['active']
        totals={}
        for phase in ('training','evaluation'):
            rows=[j for j in jobs if j['phase']==phase]
            for label,key in (('attempted_steps','attempted_steps'),('completed_steps','steps'),('attempted_updates','attempted_updates'),('completed_updates','updates'),('attempted_resets','attempted_resets')):
                totals[phase+'_'+label]=sum(j.get(key,0) for j in rows)
        self.data['totals']=totals
        atomic_write(self.path, self.data)

    def start_session(self):
        if self.data['campaign_finalized']:
            raise ResourceExceeded('campaign already finalized; test cannot be revisited')
        if self.data.get('session'):
            raise ResourceExceeded('campaign session already active')
        self.assert_wall()
        self.data['session'] = {'owner': identity(os.getpid()), 'started_unix': self.clock(), 'started_monotonic': time.monotonic(), 'observed_s': 0.0}
        self.save()

    def observe_time(self):
        now = self.clock()
        for row in (self.data.get('session'), self.data.get('active')):
            if row:
                row['observed_s'] = max(row['observed_s'], max(0.0, now - row['started_unix']), max(0.0, time.monotonic() - row.get('started_monotonic', time.monotonic())))

    def totals(self):
        self.observe_time()
        active = self.data['active']
        elapsed = active['observed_s'] if active else 0.0
        train = self.data['spent_training_s'] + (elapsed if active and active['phase'] == 'training' else 0.0)
        evaluation = self.data['spent_evaluation_s'] + (elapsed if active and active['phase'] == 'evaluation' else 0.0)
        session = self.data.get('session')
        overall = max(train + evaluation, self.data['spent_all_s'] + (session['observed_s'] if session else 0.0))
        return train, evaluation, overall, elapsed

    def assert_wall(self, phase=None):
        train, evaluation, overall, elapsed = self.totals()
        c = self.cfg
        if overall >= c['all_wall_total_cap_s'] or (phase == 'training' and train >= c['training_wall_total_cap_s']) or (phase == 'evaluation' and evaluation >= c['evaluation_wall_total_cap_s']):
            raise ResourceExceeded('cumulative wall budget exhausted before next operation')
        if train > c['training_wall_total_cap_s'] or evaluation > c['evaluation_wall_total_cap_s']:
            raise ResourceExceeded('cumulative phase budget exceeded')
        if self.data['active'] and elapsed >= self.data['active']['wall_cap_s']:
            raise ResourceExceeded('per-job wall budget exhausted')

    def begin(self, phase, seed, label, wall_cap):
        if self.data['active'] or phase not in ('training', 'evaluation'):
            raise ResourceExceeded('invalid or concurrent budget job')
        self.assert_wall(phase)
        c = self.cfg
        if seed not in c['training_seeds']:
            raise ResourceExceeded('seed outside frozen campaign')
        expected = c['wall_time_cap_per_training_attempt_s'] if phase == 'training' else c['evaluation_wall_per_episode_cap_s']
        if wall_cap != expected:
            raise ResourceExceeded('job wall cap differs from frozen budget')
        # SRC0156: a job that died with the simulator before any interaction/update does not consume a retry.
        prior = [j for j in self.data['jobs'] if j['phase'] == 'training' and j['seed'] == seed and not (j['status'] == 'infrastructure_failed_before_start' and j['attempted_steps'] == 0 and j['attempted_updates'] == 0)]
        if phase == 'training' and (sum(j['attempted_steps'] for j in prior)>0 or sum(j['attempted_updates'] for j in prior)>0):
            raise ResourceExceeded('per-seed cumulative budget consumed: fresh retry cannot complete original full target/schedule')
        if phase == 'training' and (len(prior) >= c['retries_per_seed_cap'] + 1 or sum(j['phase'] == phase and j['status'] != 'infrastructure_failed_before_start' for j in self.data['jobs']) >= c['training_attempts_cap'] or any(j['status'] == 'completed' for j in prior)):
            raise ResourceExceeded('fresh retry/attempt exhausted or training seed already completed')
        row = {'phase': phase, 'seed': seed, 'label': str(label), 'started_unix': self.clock(),
               'observed_s': 0.0, 'started_monotonic': time.monotonic(), 'wall_cap_s': wall_cap, 'owner': identity(os.getpid()),
               'status': 'active', 'steps': 0, 'updates': 0, 'attempted_steps': 0,
               'attempted_updates': 0, 'attempted_resets': 0, 'checkpoints': 0,
               'pending_operation': None, 'resources': {}, 'job_index': len(self.data['jobs']),
               'attempt': len(prior) if phase == 'training' else None}
        self.data['jobs'].append(row)
        self.data['active'] = row
        self.save()
        return row

    def claim_operation(self, operation):
        active = self.data['active']
        if not active or active['pending_operation'] is not None or operation not in ('step', 'update', 'reset', 'checkpoint'):
            raise ResourceExceeded('invalid pending operation')
        self.assert_wall(active['phase'])
        c = self.cfg
        prior=[j for j in self.data['jobs'] if j['phase']=='training' and j['seed']==active['seed'] and j['job_index']!=active['job_index']]
        spent_steps=sum(j['attempted_steps'] for j in prior) if active['phase']=='training' else 0
        spent_updates=sum(j['attempted_updates'] for j in prior) if active['phase']=='training' else 0
        lost_steps = c.get('training_lost_interactions_cap_per_seed', 0) if active['phase'] == 'training' else 0
        lost_updates = c.get('training_lost_updates_cap_per_seed', 0) if active['phase'] == 'training' else 0
        if operation == 'step' and (spent_steps+active['attempted_steps'] >= (c['steps_per_seed'] + lost_steps if active['phase'] == 'training' else c['evaluation_steps_per_episode_cap'])
                                    or (active['phase'] == 'training' and active['steps'] >= c['steps_per_seed'])):
            raise ResourceExceeded('interaction budget exhausted')
        if operation == 'update' and (active['phase'] != 'training' or spent_updates+active['attempted_updates'] >= c['gradient_updates_per_seed_cap'] + lost_updates
                                      or active['updates'] >= c['gradient_updates_per_seed_cap']):
            raise ResourceExceeded('update budget exhausted')
        if operation == 'checkpoint' and (active['phase'] != 'training' or active['checkpoints'] >= c['checkpoints_per_attempt_cap']):
            raise ResourceExceeded('checkpoint budget exhausted')
        key = {'step': 'attempted_steps', 'update': 'attempted_updates', 'reset': 'attempted_resets', 'checkpoint': 'checkpoints'}[operation]
        active[key] += 1
        active['pending_operation'] = operation
        self.observe_time()
        self.save()

    def complete_operation(self, operation):
        active = self.data['active']
        if not active or active['pending_operation'] != operation:
            raise ResourceExceeded('operation completion has no matching claim')
        if operation in ('step', 'update'):
            active['steps' if operation == 'step' else 'updates'] += 1
        active['pending_operation'] = None
        self.observe_time()
        self.save()

    def abandon_operation(self, operation, reason):
        # SRC0155: a training step/update that faulted is never completed; it stays attempted and counts as lost.
        active = self.data['active']
        if not active or active['phase'] != 'training' or active['pending_operation'] != operation or operation not in ('step', 'update'):
            raise ResourceExceeded('abandon has no matching training claim')
        active['pending_operation'] = None
        active.setdefault('abandoned', {}).setdefault(operation, 0)
        active['abandoned'][operation] += 1
        key = 'lost_steps' if operation == 'step' else 'lost_updates'
        active[key] = active.get(key, 0) + 1
        active.setdefault('abandon_reasons', []).append({'operation': operation, 'reason': reason, 'time_unix': self.clock()})
        self.observe_time()
        self.save()

    def register_resume(self, resume):
        active = self.data['active']
        if not active or active['phase'] != 'training' or active['pending_operation'] is not None:
            raise ResourceExceeded('resume state only between training operations')
        if resume['steps'] > active['steps'] or resume['updates'] > active['updates']:
            raise ResourceExceeded('resume state ahead of completed counters')
        active['resume'] = dict(resume, time_unix=self.clock())
        self.save()

    def suspend(self, reason):
        # SRC0155: infrastructure fault; keep the training job resumable instead of failing it.
        active = self.data['active']
        if not active or active['phase'] != 'training' or not active.get('resume'):
            raise ResourceExceeded('only a training job with a registered resume state can be suspended')
        if active['pending_operation'] in ('step', 'update'):
            self.abandon_operation(active['pending_operation'], 'infrastructure:' + reason)
        active['pending_operation'] = None
        self.observe_time()
        active['suspended'] = True
        active.setdefault('suspensions', []).append({'reason': reason, 'time_unix': self.clock(), 'observed_s': active['observed_s']})
        self.data['jobs'][active['job_index']] = active
        self.save()

    def resume(self):
        active = self.data['active']
        if active is None:
            candidates = [j for j in self.data['jobs'] if j.get('suspended') and j['status'] == 'active']
            if len(candidates) != 1:
                raise ResourceExceeded('no unique suspended training job')
            active = self.data['active'] = candidates[0]
        if not active.get('suspended') or not self.data.get('session'):
            raise ResourceExceeded('resume requires a suspended job and an active session')
        r = active['resume']
        active['lost_steps'] = active.get('lost_steps', 0) + active['steps'] - r['steps']
        active['lost_updates'] = active.get('lost_updates', 0) + active['updates'] - r['updates']
        active['steps'], active['updates'] = r['steps'], r['updates']
        active['owner'] = identity(os.getpid())
        active['suspended'] = False
        active.setdefault('resumptions', []).append({'time_unix': self.clock(), 'resume_steps': r['steps'], 'resume_updates': r['updates']})
        c = self.cfg
        if active['lost_steps'] > c.get('training_lost_interactions_cap_per_seed', 0) or active['lost_updates'] > c.get('training_lost_updates_cap_per_seed', 0):
            raise ResourceExceeded('lost interaction/update allowance exhausted')
        self.data['jobs'][active['job_index']] = active
        self.assert_wall('training')
        self.save()
        return active

    def observe(self, **resources):
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in resources.values()):
            raise ResourceExceeded('invalid resource measurement')
        self.observe_time()
        active = self.data['active']
        if active:
            active['resources'].update(resources)
            peaks = active.setdefault('peak_resources', {})
            for key, value in resources.items():
                peaks[key] = max(peaks.get(key, 0), value)
        self.save()
        self.assert_wall(active['phase'] if active else None)
        c = self.cfg
        caps = {'rss_bytes': c['actor_rss_cap_gib'] * 2**30, 'cuda_bytes': c['cuda_memory_cap_gib'] * 2**30,
                'disk_attempt': c['disk_per_training_attempt_cap_gib'] * 2**30, 'disk_all': c['disk_all_cap_gib'] * 2**30,
                'replay_bytes': c['replay_estimated_bytes_cap'], 'replay_length': c['replay_capacity']}
        for key, cap in caps.items():
            if resources.get(key, 0) > cap:
                raise ResourceExceeded('resource exceeded: ' + key)

    def claim_evaluation(self, phase, seed, checkpoint_sha, instance):
        if phase not in ('validation', 'test'):
            raise ResourceExceeded('invalid evaluation phase')
        allowed = self.cfg[phase + '_instance_seeds']
        if seed not in self.cfg['training_seeds'] or instance not in allowed:
            raise ResourceExceeded('evaluation outside complete-instance split')
        key = '%d:%d' % (seed, instance) if phase == 'test' else '%d:%s:%d' % (seed, checkpoint_sha, instance)
        if key in self.data[phase]:
            raise ResourceExceeded('evaluation already claimed; immutable once-only record')
        self.data[phase][key] = {'phase': phase, 'seed': seed, 'instance': instance,
                                'checkpoint_sha256': checkpoint_sha, 'claimed': True,
                                'attempted_episode': False, 'completed': False, 'confirmed_success': False,
                                'return': 0.0, 'status': 'claimed_failed_until_completion'}
        self.save()
        return key

    def finish_evaluation(self, phase, key, result):
        previous = self.data[phase][key]
        if previous['status'] != 'claimed_failed_until_completion':
            raise ResourceExceeded('evaluation record already final')
        self.data[phase][key] = dict(previous, **result)
        self.save()

    def select(self, seed, checkpoint_path):
        key = str(seed)
        if key in self.data['selected']:
            if self.data['selected'][key] != checkpoint_path:
                raise ResourceExceeded('selected checkpoint is immutable; test tuning forbidden')
            return
        if any(v['seed'] == seed for v in self.data['test'].values()):
            raise ResourceExceeded('test already accessed before selection')
        self.data['selected'][key] = checkpoint_path
        self.save()

    def finish(self, status, crash=False):
        active = self.data.get('active')
        if not active:
            return
        if not crash:
            self.observe_time()
        elapsed = active['observed_s']
        charged = max(elapsed, active['wall_cap_s']) if crash else elapsed
        active.update(status=status, measured_wall_lower_bound_s=elapsed, charged_wall_s=charged,
                      crash_tail_charged_full_cap=bool(crash))
        key = 'spent_training_s' if active['phase'] == 'training' else 'spent_evaluation_s'
        self.data[key] += charged
        self.data['jobs'][active['job_index']] = active
        self.data['active'] = None
        self.save()

    def close(self):
        if self.closed:
            return
        try:
            if self.data.get('active') and not self.data['active'].get('suspended'):
                self.finish('interrupted_failed')
            elif self.data.get('active'):
                self.data['active'] = None  # suspended job stays in jobs[] for the next segment
            self.observe_time()
            session = self.data.get('session')
            if session:
                self.data['spent_all_s'] += session['observed_s']
                self.data['session'] = None
            self.save()
        finally:
            fcntl.flock(self.lock, fcntl.LOCK_UN)
            self.lock.close()
            self.closed = True
