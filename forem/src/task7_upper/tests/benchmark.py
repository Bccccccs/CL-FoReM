"""Bounded concrete network checks: CPU64 vs GPU32, 32 recurrent streams x8.

No environment, rollout, optimizer or training. Observation vector_dim=80 is
an explicit synthetic fixture; adapters choose their actual vector width.
"""
import copy
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import time
import torch
from task7_upper import UpperModel, VCM
from task7_upper.tests.test_full_vcm import sequence, VECTOR_DIM


def measure(job, cuda):
    for _ in range(3): job()
    times, gpu_times = [], []
    for _ in range(20):
        if cuda:
            torch.cuda.synchronize()
            start=torch.cuda.Event(enable_timing=True); end=torch.cuda.Event(enable_timing=True); start.record()
        begin=time.perf_counter(); job()
        if cuda:
            end.record();torch.cuda.synchronize();gpu_times.append(start.elapsed_time(end))
        times.append((time.perf_counter()-begin)*1000)
    result={'samples':20,'wall_ms_median':statistics.median(times),
            'wall_ms_min':min(times),'wall_ms_max':max(times),'wall_ms_samples':times}
    if cuda: result['cuda_event_ms_median']=statistics.median(gpu_times)
    return result


def convert(item, device):
    if isinstance(item,torch.Tensor):
        return item.to(device=device, dtype=torch.float32 if item.is_floating_point() else item.dtype)
    if isinstance(item,dict):return {k:convert(v,device) for k,v in item.items()}
    if isinstance(item,tuple):return tuple(convert(v,device) for v in item)
    return item


def recurrent(m, seq, c, f, mask):
    m.vcm.reset()
    return [m.forward_step(item,c[t],f[t],mask[t]) for t,item in enumerate(seq)]


def vcm_sequence(m, seq):
    m.reset()
    return [m(**item) for item in seq]


def main():
    torch.manual_seed(721);torch.set_num_threads(1)
    # Full fp32 kernels for the float32/float64 comparison (explicit benchmark condition).
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    torch.set_float32_matmul_precision('highest')
    assert torch.cuda.is_available()
    torch.cuda.set_per_process_memory_fraction(3.5*1024**3/torch.cuda.get_device_properties(0).total_memory,0)
    cpu=UpperModel(vector_dim=VECTOR_DIM).double().eval()
    gpu=copy.deepcopy(cpu).float().cuda().eval()
    seq=sequence(batch=32,dtype=torch.float64)
    seq_gpu=[convert(x,'cuda:0') for x in seq]
    c=torch.randn(8,32,13,6,dtype=torch.float64)
    f=torch.randn(8,32,13,19,dtype=torch.float64);f[...,8]=2.
    mask=torch.ones(8,32,13,dtype=torch.bool);mask[...,11:]=False
    cg,fg,mg=convert((c,f,mask),'cuda:0')
    count=lambda m:sum(p.numel() for p in m.parameters())
    report={'batch':32,'sequence_length':8,'K':13,'vector_dim':VECTOR_DIM,
            'input_scope':'synthetic preassembled vectors, decoded grids and f_k; no environment or training timing',
            'tf32_matmul':torch.backends.cuda.matmul.allow_tf32,'tf32_cudnn':torch.backends.cudnn.allow_tf32,
            'torch':torch.__version__,'device':torch.cuda.get_device_name(0),'threads':torch.get_num_threads(),
            'parameter_counts':{n:count(m) for n,m in cpu.named_children()},
            'total_parameters':count(cpu),'vcm_parts':{n:count(m) for n,m in cpu.vcm.named_children()},
            'async_vcm_parameters':count(VCM(vector_dim=VECTOR_DIM+1,asynchronous=True)),
            'parameter_formula':'sync total at vector_dim=D: total80+128*(D-80); async GRU adds384 parameters at same D',
            'numerical_tolerance':{'atol':1e-5,'rtol':1e-4},'numeric':{},'timing':{},'trainable_counts':{},
            'source_sha256':{str(p.relative_to(Path(__file__).parent.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.parent.rglob('*.py')}}
    with torch.no_grad():
        # Record native fastpath drift separately from the strict reference path.
        for fast in (False, True):
            torch.backends.mha.set_fastpath_enabled(fast)
            path='native_fastpath' if fast else 'unfused_reference'
            atol=5e-4 if fast else 1e-5
            report['numeric'][path]={}
            report.setdefault('numeric_conditions',{})[path]={'atol':atol,'rtol':1e-4}
            for stage in ['1','2','3','G2','G3','adapt']:
                cpu.set_stage(stage);gpu.set_stage(stage)
                report['trainable_counts'][stage]={n:sum(p.numel() for p in ps) for n,ps in cpu.trainable_parameters().items()}
                a=recurrent(cpu,seq,c,f,mask);b=recurrent(gpu,seq_gpu,cg,fg,mg)
                errors={}
                for key in ['logits','q1','q2','context','e','u','h','prediction','corrected']:
                    if a[0][key] is None:continue
                    x=torch.stack([o[key] for o in a]);y=torch.stack([o[key].cpu().double() for o in b])
                    assert torch.equal(torch.isfinite(x),torch.isfinite(y))
                    torch.testing.assert_close(x,y,atol=atol,rtol=1e-4)
                    finite=torch.isfinite(x);errors[key]=float((x[finite]-y[finite]).abs().max())
                states=torch.stack([cpu.vcm.hidden[i] for i in range(32)])
                states_gpu=torch.stack([gpu.vcm.hidden[i] for i in range(32)]).cpu().double()
                torch.testing.assert_close(states,states_gpu,atol=atol,rtol=1e-4)
                errors['final_recurrent_state']=float((states-states_gpu).abs().max())
                report['numeric'][path][stage]=errors
                # Clear references to state views before deepcopy/checkpoint operations.
                cpu.vcm.reset();gpu.vcm.reset()
        cpu.set_stage('3');gpu.set_stage('3')
        for label,m,ss,cc,ff,mm in [('cpu64',cpu,seq,c,f,mask),('gpu32',gpu,seq_gpu,cg,fg,mg)]:
            cuda=label=='gpu32'
            outputs=recurrent(m,ss,cc,ff,mm)
            state=torch.stack([m.vcm.hidden[i] for i in range(32)]).repeat(8,1)
            geometry=cc.flatten(0,1);features=ff.flatten(0,1);valid=mm.flatten(0,1)
            ctx,e,u=m.candidate_encoder(state,geometry,features,valid);h,_=m.world_model(ctx,e,u)
            # Per-module batch256 measurements are separate from actual recurrence.
            grids=torch.cat([x['observation'][0] for x in ss]);vec=torch.cat([x['observation'][1] for x in ss])
            vv=m.vcm.f_enc((grids,vec))
            hist=vv[:,None].expand(-1,4,-1);poses=vv.new_zeros(256,4,3)
            steps=torch.arange(4,device=vv.device)[None].expand(256,-1)
            jobs={'f_enc_256':lambda:m.vcm.f_enc((grids,vec)),
                  'retrieval_256':lambda:m.vcm.retrieval.forward_batch(vv,hist,poses,steps,torch.ones_like(steps,dtype=torch.bool),vv.new_zeros(256,3),torch.full((256,),4,device=vv.device)),
                  'gate_256':lambda:m.vcm.gate(vv,vv),
                  'gru_256':lambda:m.vcm.gru(torch.cat((vv,vv.new_zeros(256,23)),-1),vv),
                  'candidate_encoder_256':lambda:m.candidate_encoder(state,geometry,features,valid),
                  'head_a_256':lambda:m.head_a(state,e),'head_b_256':lambda:m.head_b(state,e),
                  'bias_256':lambda:m.bias(e,h),'world_model_256':lambda:m.world_model(ctx,e,u),
                  'random_world_model_256':lambda:m.random_world_model(ctx,e,u),
                  'vcm_recurrent_32x8':lambda:vcm_sequence(m.vcm,ss),
                  'upper_recurrent_32x8':lambda:recurrent(m,ss,cc,ff,mm)}
            report['timing'][label]={n:measure(job,cuda) for n,job in jobs.items()}
    # Also verify and time the actual asynchronous recurrence (extra delta_s input).
    with torch.no_grad():
        acpu=UpperModel(vector_dim=VECTOR_DIM+1,asynchronous=True).double().eval()
        agpu=copy.deepcopy(acpu).float().cuda().eval()
        acpu.set_stage('3');agpu.set_stage('3')
        aseq=sequence(batch=32,dtype=torch.float64,asynchronous=True)
        for item in aseq:
            item['observation']=(item['observation'][0],torch.cat((item['observation'][1],torch.zeros(32,1,dtype=torch.float64)),-1))
        aseq_gpu=[convert(x,'cuda:0') for x in aseq]
        # Async candidates append target progress; rollout f_k progress stays distinct.
        ac=torch.cat((c,torch.full((*c.shape[:-1],1),1.6,dtype=c.dtype)),dim=-1)
        acg=ac.float().cuda()
        aa=recurrent(acpu,aseq,ac,f,mask);ab=recurrent(agpu,aseq_gpu,acg,fg,mg)
        report['async_numeric_stage3']={}
        for key in ('logits','q1','q2','h','prediction'):
            x=torch.stack([o[key] for o in aa]);y=torch.stack([o[key].cpu().double() for o in ab])
            torch.testing.assert_close(x,y,atol=5e-4,rtol=1e-4)
            finite=torch.isfinite(x);report['async_numeric_stage3'][key]=float((x[finite]-y[finite]).abs().max())
        report['async_total_parameters']=count(acpu)
        report['timing']['cpu64']['async_upper_recurrent_32x8']=measure(lambda:recurrent(acpu,aseq,ac,f,mask),False)
        report['timing']['gpu32']['async_upper_recurrent_32x8']=measure(lambda:recurrent(agpu,aseq_gpu,acg,fg,mg),True)
    report['nvidia_smi_compute_snapshot']=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,process_name,used_memory','--format=csv'],text=True)
    report['gpu_peak_allocated_bytes']=torch.cuda.max_memory_allocated();report['gpu_peak_reserved_bytes']=torch.cuda.max_memory_reserved()
    report['parameter_devices']=sorted({str(p.device) for p in gpu.parameters()})
    report['input_devices']=sorted({str(x['observation'][0].device) for x in seq_gpu})
    out=Path('/root/mm_husky_ws/results/task7/t7.21-r4-20261021');out.mkdir(parents=True,exist_ok=True)
    (out/'benchmark.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
