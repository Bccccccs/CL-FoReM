import argparse,importlib.util,json
from pathlib import Path

spec=importlib.util.spec_from_file_location('wd',Path(__file__).resolve().parents[3]/'scripts/task7_lower_watchdog.py')
wd=importlib.util.module_from_spec(spec);spec.loader.exec_module(wd)
ARGS=argparse.Namespace(window=50000,base_step=500000,ratio=3.,share=.5,min_episodes=10,share_min_step=0)

def make(tmp,rate_fn,end_fn=None,validations=(),upto=1000000):
    run=Path(tmp);seg=0;ep=dict(fail_limit=0,other_terminated=0,truncated=0);lines=[]
    for s in range(1000,upto+1,1000):
        seg+=rate_fn(s)
        if end_fn:
            for k,v in end_fn(s).items():ep[k]+=v
        lines.append(json.dumps(dict(step=s,segments=seg,episode_end=dict(ep))))
    (run/'learning.jsonl').write_text('\n'.join(lines)+'\n{"step": 99')   # partial last line tolerated
    for v in validations:(run/f'validation-{v:07d}.json').write_text('{}')
    return run

def test_rule_b_triggers_only_after_base_plus_window(tmp_path):
    rate=lambda s:8 if s<=700000 else 30
    run=make(tmp_path,rate,upto=560000)
    assert wd.evaluate_run(run,ARGS)[0] is None
    run=make(tmp_path,rate,upto=1000000)
    trig,info=wd.evaluate_run(run,ARGS)
    assert trig and trig['rule']=='b' and info['seg_per_1000_at_base']==8.0

def test_rule_b_not_triggered_by_mild_growth_or_before_500k(tmp_path):
    assert wd.evaluate_run(make(tmp_path,lambda s:8 if s<=500000 else 20,upto=1000000),ARGS)[0] is None
    assert wd.evaluate_run(make(tmp_path,lambda s:200,upto=400000),ARGS)[0] is None

def test_rule_a_two_consecutive_validations_over_half(tmp_path):
    end=lambda s:dict(fail_limit=1,other_terminated=0,truncated=0) if s%100==0 else {}
    # 10 episodes per 1000 steps, all fail-limit -> share 1.0
    run=make(tmp_path,lambda s:1,end,validations=(250000,500000),upto=500000)
    trig,_=wd.evaluate_run(run,ARGS);assert trig and trig['rule']=='a'
    one=make(tmp_path,lambda s:1,end,validations=(250000,),upto=250000)
    for p in Path(tmp_path).glob('validation-0500000.json'):p.unlink()
    assert wd.evaluate_run(one,ARGS)[0] is None   # only one validation so far

def test_rule_a_needs_both_intervals_and_minimum_episodes(tmp_path):
    def end(s):
        frac_bad=s>250000
        return dict(fail_limit=1 if frac_bad else 0,other_terminated=0 if frac_bad else 1,truncated=0) if s%100==0 else {}
    run=make(tmp_path,lambda s:1,end,validations=(250000,500000),upto=500000)
    assert wd.evaluate_run(run,ARGS)[0] is None   # first interval share 0
    sparse=lambda s:dict(fail_limit=1) if s%50000==0 else {}   # 5 episodes per interval < min_episodes
    run=make(tmp_path,lambda s:1,sparse,validations=(250000,500000),upto=500000)
    assert wd.evaluate_run(run,ARGS)[0] is None

def test_finished_detection(tmp_path):
    assert not wd.finished(tmp_path)
    (tmp_path/'STOP').touch();assert wd.finished(tmp_path)

def test_rule_a_share_min_step_ignores_early_intervals(tmp_path):
    end=lambda s:dict(fail_limit=1,other_terminated=0,truncated=0) if s%100==0 else {}
    late=argparse.Namespace(**{**vars(ARGS),'share_min_step':1000000})
    run=make(tmp_path,lambda s:1,end,validations=(250000,500000),upto=500000)
    assert wd.evaluate_run(run,late)[0] is None                      # both intervals end before 1M -> not judged
    run=make(tmp_path,lambda s:1,end,validations=(250000,500000,750000,1000000,1250000),upto=1250000)
    trig,_=wd.evaluate_run(run,late)
    assert trig and trig['rule']=='a' and '@1000000' in trig['detail'] and '@1250000' in trig['detail']
