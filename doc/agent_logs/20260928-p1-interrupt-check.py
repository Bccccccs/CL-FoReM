"""Run only after scale probes finish: interrupt an owned 3-epoch short task after its first checkpoint."""
import json
from pathlib import Path
import subprocess
import time

name = 'mmhusky-p1-interrupt-r2'
output = Path('/home/ybc/projects/mm_husky_ws/results/p1-fix-20260928/interrupt-100-r2')
if output.exists():
    raise SystemExit('interrupt output already exists; do not overwrite')
command = ('docker run --name '+name+' --label mm_husky.task=P1-FIX-028 --init --network none '
           '--memory=16g --memory-swap=16g --shm-size=256m --runtime=nvidia '
           '-e NVIDIA_VISIBLE_DEVICES=nvidia.com/gpu=0 '
           '--mount type=bind,src=/home/ybc/projects/mm_husky_ws,dst=/root/mm_husky_ws mm_husky:node01 '
           'python3 -u /root/mm_husky_ws/src/modulation_rl/scripts/wm/train_offline.py '
           '--dataset /root/mm_husky_ws/results/p1-fix-20260928/check-100-r2/dataset.json '
           '--encoder-checkpoint /root/mm_husky_ws/results/p1a-20260923/policy-100k.pt '
           '--cache-dir /root/mm_husky_ws/results/p1-fix-20260928/check-100-r2/cache '
           '--output /root/mm_husky_ws/results/p1-fix-20260928/interrupt-100-r2 '
           '--encode-batch 128 --epochs 3 --hidden 64 --lr 3e-4 --weight-decay 1e-3 --batch 512 --seed 11 --device cuda')
print(json.dumps({'command':command}), flush=True)
proc = subprocess.Popen(['sg','docker','-c',command])
deadline = time.monotonic()+120
sent = False
while proc.poll() is None and time.monotonic()<deadline:
    if (output/'no_action-latest.pt').exists():
        info=json.loads(subprocess.check_output(['sg','docker','-c','docker inspect '+name], text=True))[0]
        assert info['Config']['Labels']['mm_husky.task']=='P1-FIX-028'
        assert '/root/mm_husky_ws/src/modulation_rl/scripts/wm/train_offline.py' in info['Config']['Cmd']
        assert '/root/mm_husky_ws/results/p1-fix-20260928/interrupt-100-r2' in info['Config']['Cmd']
        assert info['State']['Running']
        print(json.dumps({'verified_container':name,'host_pid':info['State']['Pid'],'signal':'SIGINT'}),flush=True)
        subprocess.run(['sg','docker','-c','docker kill --signal=INT '+name],check=True)
        sent=True
        break
    time.sleep(.1)
if not sent:
    raise SystemExit('checkpoint did not become available before completion/deadline; inspect the owned task, no other process stopped')
code=proc.wait(timeout=30)
assert code==130,code
marker=json.loads((output/'interrupted.json').read_text())
assert marker['signal']=='SIGINT'
verify = ('docker exec mmhusky-node01 /usr/local/bin/mm-entrypoint python3 -c '
          '"import torch,json; p=torch.load(\'/root/mm_husky_ws/results/p1-fix-20260928/interrupt-100-r2/no_action-latest.pt\', map_location=\'cpu\', weights_only=False); '
          's=p[\'training_state\']; assert s[\'epoch\']>=1 and s[\'optimizer\'][\'state\'] and s[\'best_state\']; '
          'print(json.dumps(dict(epoch=s[\'epoch\'], completed_train_batches=s[\'completed_train_batches\'], hidden=p[\'hidden\'], normalizer_dims=len(p[\'normalizer\'][\'mean\']))))"')
result=subprocess.check_output(['sg','docker','-c',verify],text=True)
print(json.dumps({'exit_code':code,'marker':marker,'checkpoint':json.loads(result),'result':'passed'}),flush=True)
