"""Direct stdlib checks for sealed collection and JSON-only descriptive audits."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

FOREM=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(FOREM/'src'))

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value

worker=module('entry_worker',FOREM/'scripts/task9_11/worker.py')
audit=module('entry_audit',FOREM/'scripts/task9_11/audit.py')


def static_collection():
    command=worker.g1_test_command();directory=FOREM/'src/task9_lr/tests'
    paths=[Path(x) for x in command if x.endswith('.py')]
    assert paths==[directory/'test_contract.py']
    assert command[command.index('--rootdir')+1]==str(directory)
    assert command[command.index('--confcutdir')+1]==str(directory)
    tests=[]
    tree=ast.parse(paths[0].read_text())
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name.startswith('test_'):
            parameter=None
            for deco in node.decorator_list:
                if isinstance(deco,ast.Call) and isinstance(deco.func,ast.Attribute) and deco.func.attr=='parametrize':
                    parameter=ast.literal_eval(deco.args[1])
            tests.extend([node.name] if parameter is None else [f'{node.name}[{p}]' for p in parameter])
    # Follow every statically named local import without importing scientific code.
    pending=[paths[0],directory/'conftest.py'];seen=set();imports={}
    roots=[FOREM/'src',FOREM/'src/task9_lr/runtime/src']
    while pending:
        path=pending.pop()
        if path in seen:continue
        seen.add(path);names=[]
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.Import):names.extend(n.name for n in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:
                if node.level:
                    root=path.parent
                    for _ in range(node.level-1):root=root.parent
                    relative=root/Path(*node.module.split('.'))
                    for candidate in [relative.with_suffix('.py'),relative/'__init__.py']:
                        if candidate.is_file():pending.append(candidate)
                else:names.append(node.module)
        imports[str(path.relative_to(FOREM))]=sorted(set(names))
        for name in names:
            for root in roots:
                stem=root/Path(*name.split('.'))
                for target in [stem.with_suffix('.py'),stem/'__init__.py']:
                    if target.is_file():pending.append(target)
    assert not any(p.name.startswith('test_') and p!=paths[0] for p in seen)
    return dict(actual_worker_argv=command,collection_targets=[str(p) for p in paths],
                predicted_pytest_node_names=tests,predicted_count=len(tests),
                method='AST of explicit pytest file and local transitive imports; GPU pytest not executed',
                local_transitive_imports=imports,
                stdlib_direct_argv=[sys.executable,'-B',str(directory/'test_supervision_stdlib.py')],
                conftest_scope=str(directory))


class EntryIsolationTests(unittest.TestCase):
    def test_actual_worker_argv_is_explicit_white_list(self):
        value=static_collection()
        self.assertEqual(value['predicted_count'],14)
        self.assertNotIn(str(FOREM/'src/task9_lr/tests'),value['actual_worker_argv'][-1:])
        output=os.environ.get('TASK9_COLLECTION_REPORT')
        if output:Path(output).write_text(json.dumps(value,indent=2)+'\n')

    def test_inherited_pytest_options_cannot_expand_collection(self):
        from unittest.mock import patch
        with patch.dict(os.environ,{'PYTEST_ADDOPTS':'elsewhere','PYTEST_PLUGINS':'bad'}):
            env=worker.g1_test_environment('/temporary-placeholder')
        self.assertNotIn('PYTEST_ADDOPTS',env);self.assertNotIn('PYTEST_PLUGINS',env)
        self.assertEqual(env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'],'1')

    def test_actual_main_uses_sealed_command_and_environment(self):
        tree=ast.parse((FOREM/'scripts/task9_11/worker.py').read_text())
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        calls=[n.func.id for n in ast.walk(main) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
        self.assertIn('g1_test_command',calls);self.assertIn('g1_test_environment',calls)
        self.assertIn('assert_execution_allowed',calls)
        # Keep the original assertion, never skip it under pytest.
        old=ast.parse((FOREM/'src/task9_lr/tests/test_supervision_stdlib.py').read_text())
        test=next(n for n in ast.walk(old) if isinstance(n,ast.FunctionDef) and n.name=='test_no_forbidden_runtime_imports')
        self.assertIn("'pytest'",ast.unparse(test));self.assertIn("'torch'",ast.unparse(test))
        self.assertFalse(any(isinstance(n,ast.Attribute) and n.attr.startswith('skip') for n in ast.walk(test)))

    def test_no_forbidden_imports_in_direct_process(self):
        self.assertFalse({'torch','numpy','pytest','task7_sim','task8_sim','task7_lower','task8_lower'} & {n.split('.')[0] for n in sys.modules})


def expected_jobs(phase):
    result={}
    for domain,(count,role,source) in audit.DOMAIN_CONTRACT[phase].items():
        result[domain]=[dict(map_id=f'{domain}-{i}',seed=10000+i,stream_index=0,role=role,source_split=source) for i in range(count)]
    return result


def evaluation(phase,step=3000000):
    result=dict(complete=True,step=step)
    for domain,jobs in expected_jobs(phase).items():
        rows=[dict(r,proposal_seed=90000+i,strict_success=(i%2==0),original_success=(i%2==0),failures=0,
                   truncated=False,original_finish=True) for i,r in enumerate(jobs)]
        result[domain]=dict(complete=True,episodes=len(rows),expected_episodes=len(rows),rows=rows)
    return result


class JsonAuditTests(unittest.TestCase):
    def freeze(self,root,phase):
        freeze=root/'freeze';freeze.mkdir()
        seed_path=root/'authoritative-seeds.json'
        jobs=expected_jobs(phase)
        seeds=dict(schema_version='task8-eval-seeds-v1')
        for domain,key in [('validation','validation' if phase=='development' else 'test'),('transfer','semantic_transfer')]:
            seeds[key]=[dict(map_id=r['map_id'],episode_seed=r['seed'],stream_index=r['stream_index'],split=r['role']) for r in jobs[domain]]
        seed_path.write_text(json.dumps(seeds))
        digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        inventory=dict(files={},inputs={str(seed_path):digest(seed_path)})
        for arm in ('C','L'):
            for seed in (4718,4719):
                path=freeze/f'{arm}_seed{seed}.json'
                path.write_text(json.dumps(dict(group=arm,seed=seed,evaluation_seeds=str(seed_path))))
                inventory['files']['config/task9/task9_11/'+path.name]=digest(path)
        (freeze/'inventory.json').write_text(json.dumps(inventory))
        if phase=='final':
            manifest=root/'presealed-final-manifest.json'
            manifest.write_text(json.dumps(dict(format='task9-lr-final-manifest-v1',random=jobs['validation'],semantic=jobs['transfer'])))
            releases=root/'releases';releases.mkdir()
            for arm in ('C','L'):
                for seed in (4718,4719):
                    (releases/f'final-test-{arm}-{seed}.json').write_text(json.dumps(dict(test_manifest=dict(path=str(manifest),sha256=digest(manifest)))))

    def test_right_and_left_duplicates_rejected(self):
        rows=evaluation('development')['validation']['rows']
        for a,b in [(rows+rows[:1],rows),(rows,rows+rows[:1])]:
            with self.subTest(left=len(a),right=len(b)),self.assertRaises(ValueError):audit.paired(a,b)

    def test_pair_missing_and_extra_identity_rejected(self):
        rows=evaluation('development')['validation']['rows']
        for other in [rows[:-1],rows[1:]+[dict(rows[0],proposal_seed=-100)]]:
            with self.assertRaises(ValueError):audit.paired(rows,other)

    def test_all_fixed_domains_validate_against_independent_identity_set(self):
        for phase in audit.DOMAIN_CONTRACT:
            expected=expected_jobs(phase);value=evaluation(phase)
            for domain in value.keys()-{'complete','step'}:
                self.assertEqual(audit.validate_domain(value[domain],domain,phase,expected[domain]),value[domain]['rows'])
                corruptions=[]
                for mutation in ['duplicate','missing','extra','wrong_map','wrong_seed','wrong_role','wrong_domain','wrong_stream','denominator','false_complete']:
                    v=copy.deepcopy(value[domain]);rows=v['rows']
                    if mutation=='duplicate':rows[-1]=dict(rows[0])
                    elif mutation=='missing':rows.pop()
                    elif mutation=='extra':rows.append(dict(rows[0],map_id='unexpected'))
                    elif mutation=='wrong_map':rows[0]['map_id']='unexpected'
                    elif mutation=='wrong_seed':rows[0]['seed']=-1
                    elif mutation=='wrong_role':rows[0]['role']='test' if phase=='development' else 'validation'
                    elif mutation=='wrong_domain':rows[0]['source_split']='wrong'
                    elif mutation=='wrong_stream':rows[0]['stream_index']=1
                    elif mutation=='denominator':v['episodes']+=1
                    else:v['complete']=False
                    with self.subTest(phase=phase,domain=domain,mutation=mutation),self.assertRaises(ValueError):
                        audit.validate_domain(v,domain,phase,expected[domain])

    def build(self,root,phase):
        for arm in ('C','L'):
            for seed in (4718,4719):
                folder=root/f'{"formal" if phase=="development" else "test"}-{arm}-seed{seed}';folder.mkdir()
                if phase=='development':
                    for step in range(250000,3000001,250000):
                        (folder/f'validation-{step:07d}.json').write_text(json.dumps(evaluation(phase,step)))
                    (folder/'summary.json').write_text(json.dumps(dict(state=dict(steps=3000000,env_actions=3000000),updates=299975)))
                else:(folder/'final-test.json').write_text(json.dumps(evaluation(phase)))

    def test_normal_full_development_and_final_are_descriptive(self):
        for phase in audit.DOMAIN_CONTRACT:
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);self.build(root,phase)
                self.freeze(root,phase)
                result=audit.audit(root,phase) if phase=='development' else audit.final_audit(root)
                self.assertIs(result['independent_release'],False)
                paired=result['domains']['validation']['paired']['4718'] if phase=='development' else result['paired']['validation']['4718']
                self.assertEqual(sum(paired.values()),100 if phase=='development' else 200)

    def test_tampered_authoritative_inputs_and_configs_rejected(self):
        for tamper in ('seed','config','manifest'):
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);self.freeze(root,'final')
                path=root/({'seed':'authoritative-seeds.json','config':'freeze/C_seed4718.json','manifest':'presealed-final-manifest.json'}[tamper])
                path.write_text(path.read_text()+' ')
                with self.subTest(tamper=tamper),self.assertRaises(ValueError):audit.expected_identities(root,'final')

    def test_swapped_arm_config_cannot_choose_another_file_to_hash(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.freeze(root,'final')
            c=root/'freeze/C_seed4718.json';l=root/'freeze/L_seed4718.json'
            c.write_bytes(l.read_bytes())
            with self.assertRaises(ValueError):audit.expected_identities(root,'final')
            # Even an inventory changed to match those bytes cannot reassign C.
            p=root/'freeze/inventory.json';v=json.loads(p.read_text())
            v['files']['config/task9/task9_11/C_seed4718.json']=hashlib.sha256(c.read_bytes()).hexdigest()
            p.write_text(json.dumps(v))
            with self.assertRaises(ValueError):audit.expected_identities(root,'final')

    def test_nonfinal_checkpoint_corruption_blocks_development_statistics(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.build(root,'development')
            p=root/'formal-L-seed4719/validation-0250000.json';v=json.loads(p.read_text())
            v['transfer']['rows'][-1]=dict(v['transfer']['rows'][0]);p.write_text(json.dumps(v))
            with self.assertRaises(ValueError):audit.audit(root,'development',expected=expected_jobs('development'))

    def test_final_missing_case_blocks_statistics(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.build(root,'final');p=root/'test-C-seed4718/final-test.json'
            v=json.loads(p.read_text());v['transfer']['rows'].pop();p.write_text(json.dumps(v))
            with self.assertRaises(ValueError):audit.final_audit(root,expected=expected_jobs('final'))


if __name__=='__main__':unittest.main(verbosity=2)
