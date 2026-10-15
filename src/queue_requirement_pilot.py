"""Persistent, GPU-1-only queue. Installation and downloads require sufficient persistent storage."""
import datetime, fcntl, hashlib, importlib.metadata, json, os, shutil, signal, subprocess, sys, time, traceback, urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[1]
Q=R/'reports/requirement_pilot_queue'
def read(p): return json.loads(Path(p).read_text())
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(p,v):
    p=Path(p);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(v,indent=2)+'\n');tmp.replace(p)
def status(stage,**kw):
    write(Q/'status.json',{'status':stage,'updated_at':now(),'queue_pid':os.getpid(),'gpu':1,**kw})
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
    env=os.environ.copy();base=Path('/local/home/niktakbr/.cache')
    vals={'HF_HOME':config['model_cache'],'PIP_CACHE_DIR':str(base/'pip'),
      'XDG_CACHE_HOME':str(base),'UV_CACHE_DIR':str(base/'uv'),'UV_PYTHON_INSTALL_DIR':str(base/'uv/python'),
      'TMPDIR':str(base/'tmp'),'TORCH_HOME':str(base/'torch'),'CUDA_CACHE_PATH':str(base/'cuda'),
      'MPLCONFIGDIR':str(base/'matplotlib'),'NUMBA_CACHE_DIR':str(base/'numba'),
      'CUDA_VISIBLE_DEVICES':'1','OMP_NUM_THREADS':'4','TOKENIZERS_PARALLELISM':'false',
      'HF_HUB_DISABLE_PROGRESS_BARS':'1','PYTHONDONTWRITEBYTECODE':'1'}
    for key,value in vals.items():
        if key.endswith('_DIR') or key.endswith('_HOME') or key in ['TMPDIR','MPLCONFIGDIR','NUMBA_CACHE_DIR']:Path(value).mkdir(parents=True,exist_ok=True)
    env.update(vals);write(Q/'effective_environment.json',vals);return env
def setup_model(config,env,py):
    # Pin all files to the already-resolved official repository revision; no substitutions.
    script='''
from huggingface_hub import HfApi,snapshot_download
import json,hashlib
from pathlib import Path
config=json.loads(Path('config/requirement_generation.json').read_text())
info=HfApi().model_info(config['model_repo'],revision=config['revision'],files_metadata=True)
assert info.sha==config['revision']
snapshot=Path(snapshot_download(config['model_repo'],revision=config['revision'],allow_patterns=['*.json','*.safetensors','*.jinja','*.txt','*.model','README.md'],max_workers=2))
manifest={}
for p in sorted(snapshot.rglob('*')):
 if p.is_file():
  with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
  manifest[str(p.relative_to(snapshot))]={'sha256':h,'bytes':p.stat().st_size}
for sibling in info.siblings:
 if sibling.rfilename in manifest and sibling.lfs:
  assert manifest[sibling.rfilename]['sha256']==sibling.lfs.sha256,sibling.rfilename
assert any(n.endswith('.safetensors') for n in manifest)
config['snapshot_path']=str(snapshot)
Path('reports/requirement_pilot_queue/resolved_config.json').write_text(json.dumps(config,indent=2))
Path('reports/requirement_pilot_queue/model_manifest.json').write_text(json.dumps({'repo':config['model_repo'],'revision':info.sha,'snapshot':str(snapshot),'files':manifest},indent=2))
'''
    file=Q/'download_model.py';file.write_text(script)
    cmd=[str(py),str(file)]
    with (Q/'setup.log').open('a') as log:
        log.write('\nCOMMAND '+json.dumps(cmd)+'\n');log.flush()
        download=subprocess.Popen(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        paused=False
        try:
            while download.poll() is None:
                free=shutil.disk_usage(R).free/2**30
                if free<config['disk_reserve_gib']+10 and not paused:
                    os.killpg(download.pid,signal.SIGSTOP);paused=True
                    status('download_paused_for_storage',free_gib=round(free,2),download_pid=download.pid)
                elif paused and free>config['disk_reserve_gib']+config['weight_bytes']/2**30+20:
                    os.killpg(download.pid,signal.SIGCONT);paused=False;status('downloading_pinned_model')
                time.sleep(2)
            if download.returncode:raise RuntimeError('Pinned download failed; see setup.log')
        finally:
            if download.poll() is None:
                if paused:os.killpg(download.pid,signal.SIGCONT)
                os.killpg(download.pid,signal.SIGTERM);download.wait(timeout=30)
def main():
    Q.mkdir(parents=True,exist_ok=True);lock=(Q/'queue.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert subprocess.check_output(['hostname'],text=True).strip().lower()=='hestia'
    config=read(R/'config/requirement_generation.json');assert config['physical_gpu']==1
    server=None
    try:
        while jobs():status('queued_waiting_for_gpu1',compute_jobs=jobs());time.sleep(30)
        required=config['disk_reserve_gib']+config['environment_budget_gib']+config['weight_bytes']/2**30
        while shutil.disk_usage(R).free/2**30<required:
            status('queued_waiting_for_storage',required_free_gib=round(required,2),free_gib=round(shutil.disk_usage(R).free/2**30,2));time.sleep(30)
        env=cache_env(config);venv=R/'.venv-requirements';py=venv/'bin/python'
        if not py.exists():run([sys.executable,'-m','venv',str(venv)],'setup.log',env)
        status('installing_isolated_backend')
        run([str(py),'-m','pip','install','vllm=='+config['vllm_version'],'transformers=='+config['transformers_version'],'jsonschema==4.26.0'],'setup.log',env)
        run([str(py),'-m','pip','check'],'setup.log',env)
        with (Q/'package_versions.txt').open('w') as f:subprocess.run([str(py),'-m','pip','freeze'],stdout=f,check=True)
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
        auditfile=Q/'audit_backend.py';auditfile.write_text(audit);run([str(py),str(auditfile)],'setup.log',env)
        status('downloading_pinned_model');setup_model(config,env,py);config=read(Q/'resolved_config.json')
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
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        out=R/'data/requirement_pilots'/stamp;status('smoke_then_three_generations',output=str(out),server_pid=server.pid)
        run([str(py),str(R/'src/requirement_proposals.py'),'--project',str(R),'pilot','--config',str(Q/'resolved_config.json'),'--output',str(out)],'pilot.log',env)
        status('completed_pending_human_review',output=str(out),generations=3)
    except BaseException:
        status('blocked_error',error=traceback.format_exc());raise
    finally:
        # Stop only this queue's own server, never an existing GPU job.
        if server is not None and server.poll() is None:
            os.killpg(server.pid,signal.SIGTERM)
            try:server.wait(timeout=30)
            except subprocess.TimeoutExpired:os.killpg(server.pid,signal.SIGKILL);server.wait()
if __name__=='__main__':main()
