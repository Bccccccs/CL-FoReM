"""Actual Task4 source/config/runtime/official binary identity; rejects Task3 checkpoint namespace."""
from pathlib import Path
from task3_identity import semantic_identity as inherited_identity,tree_digest,_sha_file
ROOT=Path(__file__).resolve().parents[1]
RUNTIME_FILES=('task4_motion_raw.py','task4_history_raw.py','task4_init_survey.py','task4_preflight.py','collect_task4_instances.py','diagnose_task4_init.py','task4_env.py','task4_identity.py','check_task4_localization.py','run_task4_localization.sh','audit_task4_inputs.py','analyze_task4_localization.py','check_task4_sensors.py','task3_env.py','task3_identity.py','task0_proc.py','task4_sac_entry.py','record_task4_quality.py','check_task4_quality.py','evaluate_task4_baseline.py','task4_budget.py','task4_instances.py','task4_formal_entry.py','task4_formal_gate.py','task4_resources.py','task4_budget_watchdog.py','run_task4_formal.sh','task4_formal_resumable.py')
def semantic_identity(root=ROOT,ros_share='/opt/ros/noetic/share'):
 root=Path(root);groups=inherited_identity(root,ros_share)['groups']
 for p in ('src/open_vins','src/forem_localization','config/task4'):
  groups[p]=tree_digest(root/p,skip_files=('execution_freeze.json',)) or 'absent'
 for name in RUNTIME_FILES:
  p=root/'scripts'/name;groups['runtime:'+name]={'files':1,'sha256':_sha_file(p)} if p.is_file() else 'absent'
 for package,relative in (('ov_core','lib/libov_core_lib.so'),('ov_init','lib/libov_init_lib.so'),('ov_msckf','lib/libov_msckf_lib.so'),('ov_msckf','lib/ov_msckf/run_subscribe_msckf'),('ov_msckf','lib/ov_msckf/ros1_serial_msckf')):
  name=package+'/'+relative.split('/')[-1];p=root/'devel/.private'/package/relative
  groups['binary:'+name]={'files':1,'sha256':_sha_file(p)} if p.is_file() else 'absent'
 for p in sorted((root/'devel/.private/modulation_rl/lib/python3/dist-packages').glob('pybindings*.so')):
  groups['inherited_binary:'+p.name]={'files':1,'sha256':_sha_file(p)}
 for package,name in (('modulation_rl','librobots.so'),('modulation_rl','libmygeneral.so'),('modulation_rl','libmyutils.so'),('bio_ik','libbio_ik.so')):
  p=root/'devel/.private'/package/'lib'/name;groups['inherited_binary:'+name]={'files':1,'sha256':_sha_file(p)} if p.is_file() else 'absent'
 return {'schema':4,'namespace':'task4_openvins_stereo_imu','pose_source':'openvins_stereo_imu','groups':groups}
def assert_checkpoint_identity(checkpoint,expected):
 if checkpoint.get('task_namespace')!='task4_openvins_stereo_imu' or checkpoint.get('semantic_identity')!=expected:raise ValueError('Task4 rejects stale/Task3/truth checkpoint identity')

def verify_runtime(root=ROOT):
 import json,yaml
 from audit_task4_inputs import verify_accepted_core
 root=Path(root);errors=verify_accepted_core(root,yaml.safe_load((root/'config/task4/protocol.yaml').read_text()))
 manifest=json.loads((root/'src/open_vins/SOURCE.json').read_text());patches={p['path']:p for p in manifest['patches']}
 if manifest['commit']!='69488123ed9362dd44b6f28e7f4680abbff1442b':errors.append('wrong_VIO_pin')
 for rel,digest in manifest['files'].items():
  if rel in patches:
   patch=patches[rel]
   if patch['old_sha256']!=digest:errors.append('wrong_patch_base:'+rel)
   digest=patch['new_sha256']
  if _sha_file(root/'src/open_vins'/rel)!=digest:errors.append('unrecorded_official_source_change:'+rel)
 identity=semantic_identity(root)
 errors += ['missing_actual_runtime:'+k for k,v in identity['groups'].items() if v=='absent']
 if errors:raise ValueError('Task4 actual runtime source gate: '+repr(errors))
 return identity
