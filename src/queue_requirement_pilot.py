"""Persistent, GPU-1-only queue. Installation and downloads require sufficient persistent storage."""
import argparse, datetime, fcntl, hashlib, importlib.metadata, json, os, shutil, signal, subprocess, sys, time, traceback, urllib.request
from pathlib import Path
from pilot_storage import path_from, storage_plan, verify_existing_runtime, verify_cached_model
R=Path(__file__).resolve().parents[1]
Q=R/'reports/requirement_pilot_queue'
def read(p): return json.loads(Path(p).read_text())
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(p,v):
    p=Path(p);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(v,indent=2)+'\n');tmp.replace(p)
def status(stage,**kw):
    write(Q/'status.json',{'status':stage,'updated_at':now(),'queue_pid':os.getpid(),'queue_process_start_ticks':proc_identity(os.getpid()),'gpu':1,**kw})
def proc_identity(pid):
    try: return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
    except FileNotFoundError: return None
def jobs():
    output=subprocess.check_output(['nvidia-smi','-i','1','--query-compute-apps=pid,process_name','--format=csv,noheader'],text=True)
    desktop={'/usr/libexec/gnome-remote-desktop-daemon','/usr/bin/ptyxis','/bin/ptyxis','/usr/bin/nautilus'}
    return [line for line in output.splitlines() if line and line.split(',',1)[-1].strip() not in desktop]
def run(cmd,log,env):
    with (Q/log).open('a') as f:
        f.write('\nCOMMAND '+json.dumps(cmd)+'\n');f.flush()
        subprocess.run(cmd,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
def cache_env(config):
    env = os.environ.copy()
    base = path_from(R, config['runtime_cache'])
    vals={'HF_HOME':config['model_cache'],'PIP_CACHE_DIR':str(base/'pip'),
      'XDG_CACHE_HOME':str(base),'UV_CACHE_DIR':str(base/'uv'),'UV_PYTHON_INSTALL_DIR':str(base/'uv/python'),
      'TMPDIR':str(base/'tmp'),'TORCH_HOME':str(base/'torch'),'CUDA_CACHE_PATH':str(base/'cuda'),
      'MPLCONFIGDIR':str(base/'matplotlib'),'NUMBA_CACHE_DIR':str(base/'numba'),
      'CUDA_VISIBLE_DEVICES':'1','OMP_NUM_THREADS':'4','TOKENIZERS_PARALLELISM':'false',
      'HF_HUB_DISABLE_PROGRESS_BARS':'1','PYTHONDONTWRITEBYTECODE':'1',
      'XDG_CONFIG_HOME':str(base/'config'),'VLLM_CONFIG_ROOT':str(base/'config/vllm'),
      'FLASHINFER_WORKSPACE_BASE':str(base/'flashinfer-home'),
      'VLLM_NO_USAGE_STATS':'1','VLLM_CACHE_ROOT':str(base/'vllm'),'TRITON_CACHE_DIR':str(base/'triton'),
      'TORCHINDUCTOR_CACHE_DIR':str(base/'torchinductor'),'TORCH_EXTENSIONS_DIR':str(base/'torch-extensions')}
    for key,value in vals.items():
        if key.endswith('_DIR') or key.endswith('_HOME') or key in ['TMPDIR','MPLCONFIGDIR','NUMBA_CACHE_DIR']:Path(value).mkdir(parents=True,exist_ok=True)
    env.update(vals);write(Q/'effective_environment.json',vals);return env
def main(config_path, output=None):
    global Q
    config=read(config_path)
    configured=Path(config.get('runtime_report_dir','reports/requirement_pilot_queue'))
    Q=configured if configured.is_absolute() else R/configured
    if Q.resolve()==(R/'reports/requirement_pilot_queue').resolve() and config.get('prompt_version')=='requirements-v2':
        raise ValueError('Version 2 must use a separate runtime report directory')
    Q.mkdir(parents=True,exist_ok=True);lock=(Q/'queue.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert subprocess.check_output(['hostname'],text=True).strip().lower()=='hestia'
    assert config['physical_gpu']==1
    write(Q/'launch_config.json',config)
    server=None
    try:
        while jobs():status('queued_waiting_for_gpu1',compute_jobs=jobs());time.sleep(30)
        out=Path(output) if output else R/'data/requirement_pilots'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        if not out.is_absolute():out=R/out
        if out.exists():raise ValueError('Pilot output directory already exists; refusing overwrite')
        plan=storage_plan(config,R,out);write(Q/'storage_plan.json',plan)
        while not plan['sufficient']:
            status('queued_waiting_for_storage',storage=plan);time.sleep(30)
            plan=storage_plan(config,R,out);write(Q/'storage_plan.json',plan)
        env=cache_env(config);venv=Path(config['environment_path'])
        status('verifying_existing_pinned_runtime')
        py=verify_existing_runtime(config,R,Q)
        # Save installed backend's handling of requested settings for verification, without environment/secrets.
        audit="""import inspect,json,pathlib,vllm,transformers,torch
from vllm.entrypoints.openai.chat_completion.protocol import ChatCompletionRequest
fields=ChatCompletionRequest.model_fields
required=['reasoning_effort','chat_template_kwargs','temperature','top_p','top_k','min_p','repetition_penalty','presence_penalty','max_tokens','seed']
assert all(k in fields for k in required),str(set(required)-set(fields))
config=json.loads(pathlib.Path('config/requirement_generation.json').read_text());s=config['generation']
sampling={k:s[k] for k in ['temperature','top_p','top_k','min_p','presence_penalty','repetition_penalty']}
request=ChatCompletionRequest(model=config['model_repo'],messages=[{'role':'user','content':'smoke'}],**sampling,max_tokens=s['max_tokens'],seed=1000,reasoning_effort=s['reasoning_effort'],chat_template_kwargs={'enable_thinking':s['thinking'],'preserve_thinking':False})
params=request.to_sampling_params(s['max_tokens'],{})
for k,v in sampling.items():assert getattr(params,k)==v,(k,getattr(params,k),v)
assert params.seed==1000 and params.max_tokens==s['max_tokens']
chat=request.build_chat_params(None,'auto')
assert chat.chat_template_kwargs['reasoning_effort']==s['reasoning_effort']
assert chat.chat_template_kwargs['enable_thinking']==s['thinking']
assert chat.chat_template_kwargs['preserve_thinking']==False
assert torch.version.cuda is not None
root=pathlib.Path(vllm.__file__).parent
matches={}
for p in root.rglob('*.py'):
 text=p.read_text()
 if 'reasoning_effort' in text and ('chat_template_kwargs' in text or 'SamplingParams' in text):matches[str(p.relative_to(root))]=text
pathlib.Path('reports/requirement_pilot_queue/backend_settings_audit.json').write_text(json.dumps({'vllm':vllm.__version__,'transformers':transformers.__version__,'torch':torch.__version__,'cuda':torch.version.cuda,'fields':required,'sampling_and_template_settings_verified':True,'handling_sources':matches},indent=2))
"""
        audit=audit.replace("pathlib.Path('config/requirement_generation.json')",f"pathlib.Path({str(Q/'launch_config.json')!r})").replace('reports/requirement_pilot_queue/',str(Q)+'/')
        auditfile=Q/'audit_backend.py';auditfile.write_text(audit);run([str(py),str(auditfile)],'setup.log',env)
        status('verifying_cached_pinned_model');verify_cached_model(config,R,Q)
        write(Q/'resolved_config.json',config)
        plan=storage_plan(config,R,out);write(Q/'storage_plan_verified.json',plan)
        if not plan['sufficient']:raise RuntimeError('Storage changed during verification; refusing model load')
        if jobs():raise RuntimeError('GPU 1 acquired another compute job during setup; refusing model load')
        cmd=[str(venv/'bin/vllm'),'serve',config['snapshot_path'],'--served-model-name',config['model_repo'],
             '--revision',config['revision'],'--tokenizer-revision',config['revision'],
             '--host','127.0.0.1','--port','8027','--dtype','bfloat16','--cpu-offload-gb',str(config['cpu_offload_gib']),
             '--max-model-len',str(config['generation']['context_limit']),'--max-num-seqs','1',
             '--gpu-memory-utilization','0.90','--enforce-eager','--reasoning-parser','qwen3','--language-model-only']
        write(Q/'server_command.json',{'argv':cmd,'cwd':str(R),'timestamp':now()})
        logfile=(Q/'server.log').open('a');server=subprocess.Popen(cmd,cwd=R,env=env,stdout=logfile,stderr=subprocess.STDOUT,start_new_session=True)
        status('loading_model',server_pid=server.pid);deadline=time.monotonic()+1800
        while True:
            if server.poll() is not None:raise RuntimeError('Server exited; inspect server.log. No alternative precision/model was selected.')
            try:
                with urllib.request.urlopen('http://127.0.0.1:8027/health',timeout=3) as f:assert f.status==200
                break
            except Exception:
                if time.monotonic()>deadline:raise RuntimeError('Server startup timeout')
                time.sleep(5)
        status('smoke_then_configured_generations',output=str(out),server_pid=server.pid)
        run([str(py),str(R/'src/requirement_proposals.py'),'--project',str(R),'pilot','--config',str(Q/'resolved_config.json'),'--output',str(out)],'pilot.log',env)
        status('completed_pending_human_review',output=str(out),generations=len(config['generation']['seeds']))
    except BaseException:
        status('blocked_error',error=traceback.format_exc());raise
    finally:
        # Stop only this queue's own server, never an existing GPU job.
        if server is not None and server.poll() is None:
            os.killpg(server.pid,signal.SIGTERM)
            try:server.wait(timeout=30)
            except subprocess.TimeoutExpired:os.killpg(server.pid,signal.SIGKILL);server.wait()
def inspect_status(path):
    s=read(path)
    terminal={'completed_pending_human_review','blocked_error','stopped_before_launch_for_review'}
    if s.get('status') not in terminal:
        start=s.get('queue_process_start_ticks')
        if start is None or proc_identity(s.get('queue_pid',-1))!=start:
            return {**s,'reported_status':s.get('status'),'status':'stale_process_not_verified'}
    return s

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--config',type=Path,default=R/'config/requirement_generation.json')
    ap.add_argument('--output',type=Path)
    ap.add_argument('--launch-reviewed-pilot',action='store_true',help='Launch only after researcher review; otherwise print the plan without starting jobs.')
    ap.add_argument('--status',type=Path)
    a=ap.parse_args()
    if a.status:print(json.dumps(inspect_status(a.status),indent=2))
    elif not a.launch_reviewed_pilot:
        print(json.dumps({'status':'stopped_before_launch_for_review','config_path':str(a.config),'config':read(a.config),'output':str(a.output) if a.output else None},indent=2))
    else:main(a.config.resolve(),a.output)

