"""Reproduce Phase 2A CPU-only tests, baseline comparison, frozen checks and demos."""
import argparse
import ast
import datetime
from pathlib import Path
import os
import re
import socket
import subprocess
import sys
import jsonschema
from .configuration import HERE, REPO, SPEC
from .integrity import verify, BASE
from .manifest import builtins
from .provenance import load, write_new, bytes_digest

def run_suite(name,root,tests,output,packages=None):
    env=os.environ.copy()
    env.update(HOME='/tmp',TMPDIR=str(output/'tmp'),PYTHONDONTWRITEBYTECODE='1')
    paths=[str(root/'src'),str(root)]
    switches=[]
    if packages:
        switches=['-S']
        paths += [str(packages),'/usr/lib/python3.12/site-packages','/usr/lib64/python3.12/site-packages']
    env['PYTHONPATH']=os.pathsep.join(paths)
    cmd=[sys.executable,*switches,'-m','unittest','discover','-s',tests,'-v']
    p=subprocess.run(cmd,cwd=root,env=env,capture_output=True,text=True)
    text=p.stdout+p.stderr
    (output/(name+'.log')).write_text(text)
    match=re.search(r'Ran (\d+) tests?',text)
    return {'returncode':p.returncode,'tests_run':int(match.group(1)) if match else None,
            'problem_tests':re.findall(r'^(?:FAIL|ERROR): (.+)$',text,re.M),
            'skipped':len(re.findall(r' \.\.\. skipped ',text)), 'command':cmd,
            'cwd':str(root),'PYTHONPATH':env['PYTHONPATH'],'log_sha256':bytes_digest(text.encode())}

def acceptance_map(output):
    matrix=(SPEC/'V4_TEST_MATRIX.md').read_text()
    ids=re.findall(r'^\| ([A-Z]+\d+[A-Z]*\d*) \|',matrix,re.M)
    tests=[]
    for p in (HERE/'tests').glob('test_*.py'):
        tree=ast.parse(p.read_text())
        for cls in tree.body:
            if isinstance(cls,ast.ClassDef):
                tests += [p.stem+'.'+cls.name+'.'+n.name for n in cls.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
    fallback={
      'F02':['test_A02_F03_raw_contact_or_height_not_a_witness'],
      'F05':['test_raw_contact_has_no_support_exemption'],
      'F07':['test_downward_cannot_precede_departure'],
      'G03':['test_P01_source_tamper','test_R16P02_alias_collision'],
      'G02':['test_G04_units_mismatch','test_G04_clock_mismatch'],
      'S03':['test_R16S02_scope_suffix_blocks_negative'],
      'T03':['test_R16E02_unrelated_invalid_optional_camera','test_dependency_on_missing_camera_blocks_positive'],
      'E01':['test_C00_empty_scope','test_five_object_mixed'],
      'O02':['test_R16E02_unrelated_invalid_optional_camera','test_dependency_on_missing_camera_blocks_positive'],
      'O03':['test_R16E02_invalid_shared_foundation','test_P01_record_tamper_without_source']}
    rows=[]
    for case in ids:
        matches=[t for t in tests if re.search(r'(?:^|_)'+case+r'(?:_|$)',t.split('.')[-1])]
        matches += [t for t in tests if t.split('.')[-1] in fallback.get(case,[])]
        status='analytical_contract_tested' if matches else 'deferred_not_implemented'
        note='Tests declarations/admission/bookkeeping, never physical detection or empirical validity.'
        if case in ('A05','S02','G02','G03','E02'):
            status='deferred_physical_capability' if case!='E02' else 'empirical_validation_pending'
            note={'A05':'Moving/articulated support inference disabled; affected capability IC.',
                  'S02':'Complex handoff/dynamic reassignment not implemented; static unions only.',
                  'G02':'No physical frame/gravity transform solver; metadata contract mismatches tested.',
                  'G03':'Hash/identity binding tested; LIBERO XML/native-geometry importer deferred.',
                  'E02':'No independently labeled reference acquisition, new simulations or accuracy evaluation.'}[case]
        rows.append({'case':case,'status':status,'tests':sorted(set(matches)),'limits':note})
    assert len(rows)==55 and len(set(ids))==55
    write_new(output/'ACCEPTANCE_COVERAGE.json',rows)
    return rows

def main(argv=None):
    assert socket.gethostname().lower()=='hestia','Research validation requires Hestia'
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',required=True,type=Path)
    parser.add_argument('--baseline-root',required=True,type=Path)
    parser.add_argument('--legacy-site-packages',type=Path)
    args=parser.parse_args(argv)
    output=args.output_dir.resolve()
    if not output.is_relative_to('/disk/1/data/niktakbr'):raise ValueError('New results require owned disk1')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=args.baseline_root,text=True).strip()!=BASE:raise ValueError('Wrong baseline')
    output.mkdir(parents=True,exist_ok=False);(output/'tmp').mkdir()
    for p in [SPEC/'R1_V2_CONFIG_SCHEMA.json',HERE/'evidence.schema.json',HERE/'assessment.schema.json']:
        jsonschema.Draft202012Validator.check_schema(load(p))
    suites={
        'phase2a':run_suite('phase2a',REPO,'evaluation/r1_v4/tests',output),
        'frozen_v3':run_suite('frozen_v3',REPO,'evaluation/r1_v3/tests',output,args.legacy_site_packages),
        'existing':run_suite('existing',REPO,'tests',output,args.legacy_site_packages),
        'baseline_existing':run_suite('baseline_existing',args.baseline_root,'tests',output,args.legacy_site_packages)}
    known=suites['existing']['problem_tests']==suites['baseline_existing']['problem_tests']
    known=known and suites['existing']['tests_run']==suites['baseline_existing']['tests_run'] and suites['existing']['skipped']==suites['baseline_existing']['skipped']
    supplemental={}
    for folder in ['r1_reference','r1_v3_generalization','r1_v3_human_validation_20',
                   'r1_v3_ai_only_adjudication_20261030','r1_v3_ai_assisted_human_verification_20261030']:
        entry=run_suite(folder,REPO,'evaluation/'+folder+'/tests',output,args.legacy_site_packages)
        if entry['returncode']:
            baseline=run_suite('baseline_'+folder,args.baseline_root,'evaluation/'+folder+'/tests',output,args.legacy_site_packages)
            entry['baseline']=baseline
            entry['same_baseline_problems']=entry['problem_tests']==baseline['problem_tests'] and entry['tests_run']==baseline['tests_run']
        supplemental[folder]=entry
    write_new(output/'SUPPLEMENTAL_REGRESSIONS.json',supplemental)
    integrity=verify();write_new(output/'FROZEN_INTEGRITY.json',integrity)
    subprocess.run([sys.executable,'-m','evaluation.r1_v4.demonstrate','--output-dir',str(output/'demonstrations')],cwd=REPO,check=True)
    coverage=acceptance_map(output)
    subprocess.run(['git','diff','--check'],cwd=REPO,check=True)
    passed=suites['phase2a']['returncode']==0 and suites['frozen_v3']['returncode']==0 and known
    passed = passed and all(r['returncode']==0 or r.get('same_baseline_problems') for r in supplemental.values())
    report={'phase2a_passed':passed,'supplemental_regressions':supplemental,'entire_existing_suite_passed':suites['existing']['returncode']==0,
        'existing_failures_match_unchanged_baseline':known,'suites':suites,'integrity':integrity,
        'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':socket.gethostname(),
        'baseline_commit':BASE,'branch':subprocess.check_output(['git','branch','--show-current'],cwd=REPO,text=True).strip(),
        'runtime_bindings':builtins(),'acceptance_cases':len(coverage),'exhaustive_outcome_vectors':3906,
        'demonstrations':load(output/'demonstrations/SUMMARY.json'),
        'runtime_file_sha256':{p.name:bytes_digest(p.read_bytes()) for p in sorted(HERE.iterdir()) if p.suffix in ('.py','.json')},
        'empirical_profiles_enabled':False,'new_simulations':False,'empirical_calibration':'BLOCKED_ON_EVIDENCE',
        'independent_empirical_validation':'PENDING','pushed':False,'merged':False}
    write_new(output/'VALIDATION_RESULTS.json',report)
    print('Phase 2A infrastructure:', 'PASS' if passed else 'FAIL')
    print('Existing repository suite:', 'PASS' if report['entire_existing_suite_passed'] else 'BASELINE FAILURES RETAINED')
    if not passed:raise SystemExit(1)
if __name__=='__main__':main()
