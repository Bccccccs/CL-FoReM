"""Frozen B protocol: finite exact comparison and first-rejection scoring (stdlib)."""
import math

def compare(a,b,path='$'):
 if type(a) is not type(b):return {'path':path,'off':a,'on':b,'cause':'type'}
 if isinstance(a,float) and (not math.isfinite(a) or not math.isfinite(b)):
  return {'path':path,'off':repr(a),'on':repr(b),'cause':'nonfinite'}
 if isinstance(a,dict):
  if a.keys()!=b.keys():return {'path':path,'off':list(a),'on':list(b),'cause':'keys'}
  for k in a:
   d=compare(a[k],b[k],path+'.'+k)
   if d:return d
 elif isinstance(a,list):
  if len(a)!=len(b):return {'path':path,'off':len(a),'on':len(b),'cause':'length'}
  for i,(x,y) in enumerate(zip(a,b)):
   d=compare(x,y,f'{path}[{i}]')
   if d:return d
 elif a!=b:return {'path':path,'off':a,'on':b,'cause':'value'}
 return None

KEY = ('map_id', 'seed', 'stream_index', 'role', 'source_split', 'proposal_seed')
TERMINAL = ('strict_success', 'terminated', 'truncated', 'failures')
FIELDS = {
 'reset': ('case_key', 'state', 'batch_jobs', 'batch_local_index'),
 'begin': ('segment', 'action', 'state', 'target', 'arrived', 'reason',
           'done', 'terminated', 'truncated', 'strict_success', 'failures'),
 'action_start': ('segment', 'action', 'state', 'target', 'raw_action'),
 'substep': ('segment', 'action', 'substep', 'state', 'target', 'raw_action',
             'execution_action', 'pending', 'ik_accepted', 'failed', 'commit',
             'arrived', 'route_end', 'reason', 'done'),
 'action_end': ('segment', 'action', 'state', 'target', 'reason', 'done',
                'terminated', 'truncated', 'strict_success', 'failures',
                'arrived', 'attempted', 'committed'),
 'final': ('state', 'outcome'),
}


def coverage(events, row):
 """Validate a complete episode against its independent ORIGINAL evaluate row.

 Exact OFF/ON agreement is separate: two equally truncated logs are incomplete.
 Errors are evidence gaps; callers must never convert them to non-recovery.
 """
 errors = []
 counts = dict(events=0, reset=0, begin=0, action_start=0, substep=0,
               action_end=0, final=0, attempted=0, committed=0, rejections=0,
               expected_actions=row.get('transfers') if isinstance(row, dict) else None)
 def fail(message):
  errors.append(message)
 def result():
  return dict(complete=not errors, errors=errors, counts=counts)
 def number(x):
  return type(x) in (int, float) and (type(x) is int or math.isfinite(x))
 def vector(x, n):
  return isinstance(x, list) and len(x) == n and all(number(v) for v in x)
 def equal(a, b, where):
  difference = compare(a, b)
  if difference:
   fail(where + ': ' + str(difference))
 if not isinstance(row, dict):
  fail('missing independent evaluation row'); return result()
 for k in KEY + ('transfers', 'time_s', 'difficulty', 'first_Q',
                 'discounted_MC_return', 'Q_minus_MC') + TERMINAL:
  if k not in row: fail('row missing ' + k)
 if compare(row, row): fail('row contains nonfinite value')
 for k in ('time_s', 'discounted_MC_return'):
  if not number(row.get(k)): fail('invalid row.' + k)
 if type(row.get('transfers')) is not int or row['transfers'] < 0:
  fail('row.transfers must be nonnegative integer')
 for k in TERMINAL:
  if k in row and (type(row[k]) is not (int if k == 'failures' else bool)):
   fail('invalid row.' + k)
 if row.get('terminated') is not True and row.get('truncated') is not True:
  fail('independent evaluation row is not terminal')
 if not isinstance(events, (list, tuple)):
  fail('events must be a sequence'); return result()
 normalized = []
 for i, record in enumerate(events):
  where = 'event[%d]' % i
  if not isinstance(record, dict):
   fail(where + ' is not an object'); continue
  if compare(record, record): fail(where + ' contains nonfinite value')
  e = record.get('comparison', record)
  if not isinstance(e, dict):
   fail(where + ' comparison is not an object'); continue
  normalized.append(e); counts['events'] += 1
  kind = e.get('event')
  if kind not in FIELDS:
   fail(where + ' unknown event'); continue
  counts[kind] += 1
  for k in ('case_no', 'training_seed') + FIELDS[kind]:
   if k not in e: fail(where + ' missing ' + k)
  for k in ('case_no', 'training_seed', 'segment', 'action', 'substep', 'reason',
            'attempted', 'committed', 'failures', 'batch_local_index'):
   if k in e and type(e[k]) is not int: fail(where + ' invalid integer ' + k)
  for k in ('pending', 'ik_accepted', 'failed', 'commit', 'arrived', 'route_end',
            'done', 'terminated', 'truncated', 'strict_success'):
   if k in e and type(e[k]) is not bool: fail(where + ' invalid boolean ' + k)
  state = e.get('state')
  if not (isinstance(state, dict) and vector(state.get('base'), 3)
          and vector(state.get('q'), 6) and number(state.get('s'))):
   fail(where + ' invalid committed state')
  if 'target' in FIELDS[kind]:
   t = e.get('target')
   if not (isinstance(t, dict) and vector(t.get('pose'), 3)
           and type(t.get('inplace')) is bool and number(t.get('cap'))):
    fail(where + ' invalid target')
  for k, n in (('raw_action', 3), ('execution_action', 3)):
   if k in FIELDS[kind] and not vector(e.get(k), n): fail(where + ' invalid ' + k)
 if errors: return result()
 if not normalized or counts['reset'] != 1 or normalized[0]['event'] != 'reset':
  fail('exactly one initial reset required')
 if not normalized or counts['final'] != 1 or normalized[-1]['event'] != 'final':
  fail('exactly one terminal final required')
 if errors: return result()
 reset = normalized[0]; final = normalized[-1]
 for e in normalized:
  for k in ('case_no', 'training_seed'):
   if e[k] != reset[k]: fail('unstable ' + k)
   if k in row and str(e[k]) != str(row[k]): fail('row identity mismatch ' + k)
 case_key = reset['case_key']
 if not isinstance(case_key, dict) or any(k not in case_key for k in KEY):
  fail('reset missing full case_key')
 else:
  for k in KEY:
   if str(case_key[k]) != str(row[k]): fail('reset/row identity mismatch ' + k)
 jobs = reset['batch_jobs']; local = reset['batch_local_index']
 if not isinstance(jobs, list) or local < 0 or local >= len(jobs) or not isinstance(jobs[local], dict):
  fail('invalid reset batch identity')
 else:
  for k in KEY[:-1]:
   if k not in jobs[local] or str(jobs[local][k]) != str(row[k]):
    fail('batch/row identity mismatch ' + k)
 equal(final['outcome'], row, 'final outcome differs from original row')
 state = reset['state']; segment = 0; action = 0; opened = None; target = None
 steps = []; terminal_snapshot = None; episode_terminal = False; segment_done = True
 for i, e in enumerate(normalized[1:-1], 1):
  kind = e['event']; where = 'event[%d]' % i
  if episode_terminal: fail(where + ' event after episode termination')
  if kind == 'begin':
   if not segment_done: fail(where + ' begin before previous segment finished')
   segment_done = e['done']
   if opened is not None: fail(where + ' begin inside action')
   if e['segment'] != segment + 1 or e['action'] != action:
    fail(where + ' noncontiguous segment or begin action')
   equal(e['state'], state, where + ' begin changed committed state')
   segment = e['segment']; target = e['target']; terminal_snapshot = e
   episode_terminal = e['terminated'] or e['truncated']
  elif kind == 'action_start':
   if segment_done: fail(where + ' action_start without new begin after finished segment')
   if opened is not None: fail(where + ' action_start before action_end')
   if segment < 1 or e['segment'] != segment or e['action'] != action + 1:
    fail(where + ' noncontiguous action or missing begin')
   equal(e['state'], state, where + ' action_start state')
   equal(e['target'], target, where + ' target changed without begin')
   action = e['action']; opened = e; steps = []
  elif kind == 'substep':
   if opened is None:
    fail(where + ' substep outside action'); continue
   if e['segment'] != segment or e['action'] != action:
    fail(where + ' substep identity mismatch')
   if e['substep'] != len(steps) or e['substep'] not in (0, 1):
    fail(where + ' duplicate, missing or unordered substep')
   if not e['pending']: fail(where + ' recorded substep is not pending')
   if e['commit'] == e['failed'] or (e['commit'] and not e['ik_accepted']):
    fail(where + ' inconsistent commit/failure/IK masks')
   if steps and (steps[-1]['done'] or steps[-1]['failed']):
    fail(where + ' substep after stopped action')
   equal(e['raw_action'], opened['raw_action'], where + ' raw action changed')
   equal(e['target'], target, where + ' target changed without begin')
   if not e['commit']: equal(e['state'], state, where + ' rejected state was committed')
   else: state = e['state']
   steps.append(e)
   counts['rejections'] += int(e['pending'] and e['failed'])
  elif kind == 'action_end':
   if opened is None:
    fail(where + ' action_end without action_start'); continue
   if e['segment'] != segment or e['action'] != action:
    fail(where + ' action_end identity mismatch')
   if not steps or e['attempted'] != len(steps) or e['attempted'] not in (1, 2):
    fail(where + ' original attempted does not match pending substeps')
   if len(steps) == 1 and not (steps[0]['failed'] or steps[0]['done']):
    fail(where + ' missing second pending substep without original early stop')
   commits = sum(s['commit'] for s in steps)
   if e['committed'] != commits: fail(where + ' original committed does not match substeps')
   if any(s['done'] for s in steps) and not e['done']:
    fail(where + ' original substep done lost at action_end')
   segment_done = e['done']
   counts['attempted'] += e['attempted']; counts['committed'] += e['committed']
   equal(e['state'], state, where + ' action_end committed state')
   equal(e['target'], target, where + ' target changed without begin')
   opened = None; terminal_snapshot = e
   episode_terminal = e['terminated'] or e['truncated']
  else:
   fail(where + ' unexpected reset/final inside episode')
 if opened is not None: fail('missing action_end')
 for kind in ('action_start', 'action_end'):
  if counts[kind] != row['transfers']: fail(kind + ' count differs from original transfers')
 if action != row['transfers']: fail('global action sequence differs from original transfers')
 equal(final['state'], state, 'final state differs from last committed state')
 # begin can terminate a zero-length segment via Core._finish without an
 # action; its original terminal snapshot is therefore also authoritative.
 if terminal_snapshot is None:
  fail('missing independently recorded terminal snapshot')
 else:
  for k in TERMINAL:
   equal(terminal_snapshot[k], row[k], 'terminal ' + k)
  if not terminal_snapshot['done']: fail('last terminal snapshot is not done')
 return result()


def remaining(e):
 state=e['state'];target=e['target']
 if target['inplace']:r=max(float(target['cap'])-float(state['s']),0.)
 else:r=math.hypot(float(state['base'][0])-float(target['pose'][0]),float(state['base'][1])-float(target['pose'][1]))
 if not math.isfinite(r):raise ValueError('nonfinite remaining')
 return r


def score(events, row):
 """Frozen first-rejection score, gated by independent coverage validation."""
 checked = coverage(events, row)
 if not checked['complete']:
  return dict(classification='U', reason='incomplete trace', missing_reasons=checked['errors'], coverage=checked)
 events = [e.get('comparison', e) for e in events]
 first = next((i for i, e in enumerate(events)
               if e['event'] == 'substep' and e['pending'] and e['failed']), None)
 if first is None:
  return dict(classification='no_rejection', reason='no actual rejection recorded', coverage=checked)
 f = events[first]
 out = dict(first_rejection=f, classification='N', rejection_count=checked['counts']['rejections'],
            coverage=checked, first_segment=f['segment'], max_reduction_m=0., max_yaw_change_rad=0.)
 try:
  baseline = remaining(f); out['baseline_remaining_m'] = baseline
  last = f
  for e in events[first + 1:]:
   if e['event'] == 'begin':
    out['end_cause'] = 'target_changed'; break
   if e['event'] not in ('substep', 'action_end'): continue
   if e['segment'] != f['segment']:
    out['end_cause'] = 'target_changed'; break
   last = e
   if e['event'] == 'substep' and e['commit']:
    reduction = baseline - remaining(e)
    out['max_reduction_m'] = max(out['max_reduction_m'], reduction)
    yaw = float(e['state']['base'][2]) - float(f['state']['base'][2])
    out['max_yaw_change_rad'] = max(out['max_yaw_change_rad'], abs(math.atan2(math.sin(yaw), math.cos(yaw))))
    if reduction > 1e-6:
     out.update(classification='R', recovery_event=e, recovery_cause='committed_remaining_decrease'); return out
   if e['arrived']:
    out.update(classification='R', recovery_event=e, recovery_cause='explicit_same_segment_arrived'); return out
  out.setdefault('end_cause', 'episode_ended')
  out['last_same_segment_event'] = last
 except (KeyError, ValueError, TypeError, IndexError, OverflowError) as ex:
  out.update(classification='U', unknown_reason=repr(ex))
 return out
