"""Filesystem-aware incremental budgets for the pinned, reusable pilot runtime."""
import hashlib,json,os,re,shutil,subprocess,time
from pathlib import Path

GIB=2**30

def path_from(project,value):
    p=Path(value)
    return p if p.is_absolute() else Path(project)/p

def filesystem(path):
    # Resolve existing symlinks, then locate the filesystem for a not-yet-created directory.
    anchor=Path(path).resolve()
    while not anchor.exists():
        if anchor==anchor.parent:raise ValueError('Cannot locate filesystem for '+str(path))
        anchor=anchor.parent
    return {'device':anchor.stat().st_dev,'anchor':str(anchor),'free_bytes':shutil.disk_usage(anchor).free}

def cached_weights(config,project):
    manifest_path=path_from(project,config.get('model_manifest_path','reports/requirement_pilot_queue/model_manifest.json'))
    if not manifest_path.is_file():return 0
    manifest=json.loads(manifest_path.read_text())
    if manifest.get('revision')!=config['revision'] or manifest.get('repo')!=config['model_repo']:return 0
    snapshot=Path(config['snapshot_path']);credited=0;seen=set()
    for name,expected in manifest['files'].items():
        if not name.endswith('.safetensors'):continue
        p=snapshot/name
        if p.is_file() and p.stat().st_size==expected['bytes']:
            key=(p.stat().st_dev,p.stat().st_ino)
            if key not in seen:credited+=p.stat().st_size;seen.add(key)
    return min(config['weight_bytes'],credited)

def storage_plan(config,project,output,probe=filesystem):
    project=Path(project);credit=cached_weights(config,project)
    environment=path_from(project,config['environment_path'])
    environment_exists=(environment/'bin/python').is_file()
    roles=[('model_cache',path_from(project,config['model_cache']),max(0,config['weight_bytes']-credit)),
           ('environment',environment,0 if environment_exists else int(config['environment_budget_gib']*GIB)),
           ('runtime_cache',path_from(project,config['runtime_cache']),int(config.get('runtime_cache_budget_gib',2)*GIB)),
           ('outputs',path_from(project,output),int(config.get('output_budget_gib',1)*GIB)),
           ('runtime_reports',path_from(project,config['runtime_report_dir']),64*1024**2)]
    groups={};reserve=int(config['disk_reserve_gib']*GIB)
    for role,p,budget in roles:
        fs=probe(p);device=str(fs['device'])
        group=groups.setdefault(device,{'device':device,'anchor':fs['anchor'],'free_bytes':fs['free_bytes'],
            'incremental_budget_bytes':0,'reserve_bytes':reserve,'roles':[]})
        group['free_bytes']=min(group['free_bytes'],fs['free_bytes'])
        group['incremental_budget_bytes']+=budget
        group['roles'].append({'role':role,'path':str(p),'incremental_budget_bytes':budget})
    for g in groups.values():
        g['required_free_bytes']=g['incremental_budget_bytes']+reserve
        g['sufficient']=g['free_bytes']>=g['required_free_bytes']
    return {'filesystems':list(groups.values()),'sufficient':all(g['sufficient'] for g in groups.values()),
        'existing_weight_bytes_credited':credit,'existing_environment_credited':environment_exists,
        'cache_credit_qualification':'Sizes credited for budgeting only; all model files must pass pinned SHA-256 verification before load.'}

def verify_existing_runtime(config,project,report_dir):
    project=Path(project);report_dir=Path(report_dir)
    py=path_from(project,config['environment_path'])/'bin/python'
    if not py.is_file():raise RuntimeError('Pinned runtime is missing; no installation or dependency substitution is permitted.')
    baseline=path_from(project,config.get('baseline_package_versions_path','reports/requirement_pilot_queue/package_versions.txt'))
    expected={}
    normalize=lambda n:re.sub(r'[-_.]+','-',n).lower()
    for line in baseline.read_text().splitlines():
        if '==' in line and not line.startswith('#'):
            name,version=line.split('==',1);expected[normalize(name)]=version
    expected.update({'vllm':config['vllm_version'],'transformers':config['transformers_version'],'jsonschema':'4.26.0'})
    code="import importlib.metadata as m,json,re;print(json.dumps({re.sub(r'[-_.]+','-',d.metadata['Name']).lower():d.version for d in m.distributions()}))"
    actual=json.loads(subprocess.check_output([str(py),'-c',code],text=True))
    differences={n:{'expected':v,'actual':actual.get(n)} for n,v in expected.items() if actual.get(n)!=v}
    if differences:raise RuntimeError('Pinned runtime dependency mismatch; no packages changed: '+json.dumps(differences))
    subprocess.run([str(py),'-m','pip','check'],check=True,capture_output=True,text=True)
    report={'verified_at':time.time(),'python':str(py),'baseline':str(baseline),
            'baseline_sha256':hashlib.sha256(baseline.read_bytes()).hexdigest(),'expected_versions_checked':expected,
            'no_dependencies_installed_or_changed':True}
    (report_dir/'runtime_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    freeze=subprocess.check_output([str(py),'-m','pip','freeze'],text=True)
    (report_dir/'package_versions.txt').write_text(freeze)
    return py

def verify_cached_model(config,project,report_dir):
    manifest_path=path_from(project,config.get('model_manifest_path','reports/requirement_pilot_queue/model_manifest.json'))
    manifest=json.loads(manifest_path.read_text());snapshot=Path(config['snapshot_path'])
    if manifest.get('repo')!=config['model_repo'] or manifest.get('revision')!=config['revision'] or snapshot.name!=config['revision']:
        raise RuntimeError('Pinned model identity/revision mismatch')
    verified={}
    for name,expected in manifest['files'].items():
        rel=Path(name)
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('Invalid model manifest path')
        p=snapshot/rel
        if not p.is_file() or p.stat().st_size!=expected['bytes']:raise RuntimeError('Cached model file missing or wrong size: '+name)
        with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        if digest!=expected['sha256']:raise RuntimeError('Pinned model checksum mismatch: '+name)
        verified[name]={'sha256':digest,'bytes':p.stat().st_size}
    if sum(v['bytes'] for n,v in verified.items() if n.endswith('.safetensors'))!=config['weight_bytes']:
        raise RuntimeError('Cached weight byte total differs from pinned configuration')
    index=json.loads((snapshot/'model.safetensors.index.json').read_text())
    if not set(index['weight_map'].values()).issubset(verified):raise RuntimeError('Unverified indexed weight shards')
    result={**manifest,'snapshot':str(snapshot),'files':verified,'verified_at':time.time(),'reused_cached_model':True}
    (Path(report_dir)/'model_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
