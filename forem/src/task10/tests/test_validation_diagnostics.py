"""Choice forks and single-candidate boundaries require different explanations."""
import importlib.util
from pathlib import Path

p=Path(__file__).resolve().parents[3]/'scripts/task10_validation_diagnostics.py'
s=importlib.util.spec_from_file_location('validation_diagnostics',p);d=importlib.util.module_from_spec(s);s.loader.exec_module(d)


def rec(selected,logits):return dict(selected=selected,logits=logits,mask=[True,True])


def test_prefix_logit_comparison_stops_at_first_choice_fork():
    t=[(rec(0,[2,1]),'a'),(rec(1,[1,2]),'b'),(rec(0,[99,0]),'c')]
    i=[(rec(0,[3,1]),'a'),(rec(0,[3,2]),'b'),(rec(1,[0,999]),'c')]
    result=d.compare_prefix(t,i)
    assert not result['identical_selection_sequence']
    assert result['first_selection_difference_index']==1
    assert result['common_state_decisions_compared']==2
    assert result['max_common_state_logit_difference']==2


def test_prefix_does_not_compare_logits_for_mismatched_states():
    result=d.compare_prefix([(rec(0,[2,1]),'a')],[(rec(0,[3,1]),'x')])
    assert result['first_unpaired_state_index']==0
    assert result['common_state_decisions_compared']==0


def test_slot12_preference_excludes_boundaries_without_alternatives():
    single=dict(selected=12,mask=[False]*12+[True])
    options=dict(selected=12,mask=[True]+[False]*11+[True])
    movement=dict(selected=0,mask=options['mask'])
    r=d.summarize_choice_rows([single,options,movement])
    assert r['slot12_count']==2 and r['slot12_fraction']==2/3
    assert r['only_slot12_decisions']==1
    assert r['slot12_with_alternatives']==1 and r['slot12_fraction_with_alternatives']==.5


def test_ik_failure_priority_does_not_double_count_collision_flags():
    def a(status,base,arm,self_collision):return dict(active=True,committed=False,ik_status=status,
        base_collision=base,arm_collision=arm,self_collision=self_collision)
    counts=d.failure_kinds([a(2,True,True,True),a(1,True,True,True),a(0,False,True,True),a(0,False,False,True)])
    assert dict(counts)==dict(ik_rejected=1,base_collision=1,arm_collision=1,self_collision=1)
