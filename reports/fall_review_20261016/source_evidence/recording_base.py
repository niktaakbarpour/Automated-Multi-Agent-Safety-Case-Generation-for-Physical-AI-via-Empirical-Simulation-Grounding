"""Research recording around the upstream FlashVLA synchronous rollout."""
import argparse, contextlib, csv, datetime, hashlib, importlib.metadata, importlib.util, random
import json, os, platform, shutil, subprocess, sys, threading, time, traceback
from pathlib import Path
import h5py, imageio.v2 as imageio, numpy as np, psutil, pynvml, torch
import gymnasium as gym

ROOT = Path('/local/home/niktakbr/pi05-libero')
ACTIVE = None
SUITES = {'spatial':'libero_spatial','object':'libero_object','goal':'libero_goal','long':'libero_10'}
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def convert(x):
    if isinstance(x, torch.Tensor): return x.detach().cpu().float().numpy().tolist() if x.dtype == torch.bfloat16 else x.detach().cpu().numpy().tolist()
    if isinstance(x, np.ndarray): return x.tolist()
    if isinstance(x, np.generic): return x.item()
    if isinstance(x, Path): return str(x)
    return str(x)
def dump(p, x):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp'); tmp.write_text(json.dumps(x,default=convert,indent=2)); tmp.replace(p)
def write_tree(g, data):
    if isinstance(data, dict):
        for k,v in data.items(): write_tree(g.create_group(str(k).replace('/','__')),v)
    elif isinstance(data,(tuple,list)) and any(isinstance(x,(dict,str)) for x in data):
        g.attrs['json']=json.dumps(data,default=convert)
    elif isinstance(data,(torch.Tensor,np.ndarray,list,tuple,int,float,bool,np.generic)):
        if isinstance(data,torch.Tensor):
            g.attrs['torch_dtype']=str(data.dtype)
            data=data.detach().cpu()
            if data.dtype==torch.bfloat16:
                g.attrs['storage_encoding']='bfloat16_bits_uint16';data=data.view(torch.uint16)
            data=data.numpy()
        a=np.asarray(data)
        if a.dtype.kind in 'biufc':
            g.create_dataset('value',data=a,compression='gzip' if a.ndim and a.size>32 else None,compression_opts=1 if a.ndim and a.size>32 else None)
        else: g.attrs['json']=json.dumps(data,default=convert)
    else: g.attrs['json']=json.dumps(data,default=convert)

class Resources:
    fields=['utc','wall_time_ns','monotonic_ns','suite','task_id','episode','step','source','process_cpu_percent','process_rss_bytes','process_vms_bytes','process_threads','host_cpu_percent','host_ram_used_bytes','host_ram_available_bytes','disk_read_bytes','disk_write_bytes','gpu_index','gpu_util_percent','gpu_memory_util_percent','gpu_used_bytes','gpu_power_w','gpu_temp_c','torch_allocated_bytes','torch_reserved_bytes']
    fields += ['process_tree_rss_bytes','process_tree_cpu_percent','process_tree_processes','process_gpu_used_bytes','gpu_sm_clock_mhz','gpu_memory_clock_mhz','host_load_1m','disk_free_bytes']
    def __init__(self,path,suite,tid,episode):
        self.f=path.open('w'); self.writer=csv.DictWriter(self.f,fieldnames=self.fields); self.writer.writeheader()
        self.p=psutil.Process(); self.p.cpu_percent(); psutil.cpu_percent()
        self.suite,self.tid,self.episode,self.step=suite,tid,episode,-1
        self.lock=threading.Lock(); self.stop=threading.Event(); self.rows=[]; self.childprocs={}
        pynvml.nvmlInit(); self.gpu=int(os.environ.get('CUDA_VISIBLE_DEVICES','1').split(',')[0]); self.handle=pynvml.nvmlDeviceGetHandleByIndex(self.gpu)
        self.thread=threading.Thread(target=self.loop,daemon=True); self.thread.start()
    def sample(self,source):
        with self.lock:
            vm=psutil.virtual_memory(); mem=self.p.memory_info(); io=self.p.io_counters(); u=pynvml.nvmlDeviceGetUtilizationRates(self.handle)
            row=dict(zip(self.fields,[now(),time.time_ns(),time.monotonic_ns(),self.suite,self.tid,self.episode,self.step,source,self.p.cpu_percent(),mem.rss,mem.vms,self.p.num_threads(),psutil.cpu_percent(),vm.used,vm.available,io.read_bytes,io.write_bytes,self.gpu,u.gpu,u.memory,pynvml.nvmlDeviceGetMemoryInfo(self.handle).used,pynvml.nvmlDeviceGetPowerUsage(self.handle)/1000,pynvml.nvmlDeviceGetTemperature(self.handle,0),torch.cuda.memory_allocated(),torch.cuda.memory_reserved()]))
            children=[self.childprocs.setdefault(p.pid,p) for p in self.p.children(recursive=True)]; tree=[self.p]+children
            tree_rss=0; child_cpu=0
            for process in tree:
                try:
                    tree_rss+=process.memory_info().rss
                    if process.pid!=self.p.pid: child_cpu+=process.cpu_percent()
                except (psutil.NoSuchProcess,psutil.AccessDenied): pass
            row.update(process_tree_rss_bytes=tree_rss,process_tree_cpu_percent=row['process_cpu_percent']+child_cpu,process_tree_processes=len(tree),process_gpu_used_bytes=sum(p.usedGpuMemory for p in pynvml.nvmlDeviceGetComputeRunningProcesses(self.handle) if p.pid==os.getpid()),gpu_sm_clock_mhz=pynvml.nvmlDeviceGetClockInfo(self.handle,pynvml.NVML_CLOCK_SM),gpu_memory_clock_mhz=pynvml.nvmlDeviceGetClockInfo(self.handle,pynvml.NVML_CLOCK_MEM),host_load_1m=os.getloadavg()[0],disk_free_bytes=shutil.disk_usage(ROOT/'results').free)
            self.writer.writerow(row); self.f.flush(); self.rows.append(row)
    def loop(self):
        while not self.stop.wait(1): self.sample('periodic_1s')
    def close(self):
        self.stop.set(); self.thread.join(); self.sample('episode_end'); self.f.close()
        return {k:float(max(r[k] for r in self.rows)) for k in ['process_rss_bytes','process_cpu_percent','gpu_used_bytes','gpu_util_percent','torch_allocated_bytes','torch_reserved_bytes','process_tree_rss_bytes']} | {'samples':len(self.rows),'mean_gpu_util_percent':float(np.mean([r['gpu_util_percent'] for r in self.rows])),'mean_cpu_percent':float(np.mean([r['process_cpu_percent'] for r in self.rows])),'mean_gpu_power_w':float(np.mean([r['gpu_power_w'] for r in self.rows]))}

class Recorder:
    def __init__(self,path,suite,tid,ep,seed,base):
        self.path=path; path.mkdir(parents=True,exist_ok=False); self.started=time.perf_counter(); self.started_at=now(); self.step=0; self.frame=0; self.chunk=0; self.stage='reset'; self.events=[]
        self.h=h5py.File(path/'trajectory.h5','w'); self.h.attrs.update(suite=suite,task_id=tid,episode=ep,seed=seed,schema_version=1)
        write_tree(self.h.create_group('rng_before_reset'),{'python':repr(random.getstate()),'numpy':np.random.get_state(),'torch_cpu':torch.get_rng_state(),'torch_cuda':torch.cuda.get_rng_state()})
        self.res=Resources(path/'resources.csv',suite,tid,ep); self.writers={}
        self.base=base; self.seed=seed; self.ep=ep; self.suite=suite; self.tid=tid
        (path/'status.txt').write_text('running\n'); (path/'started_at').write_text(self.started_at+'\n'); (path/'runner.pid').write_text(str(os.getpid())+'\n')
        dump(path/'launch.json',{'argv':sys.argv,'pid':os.getpid()}); dump(path/'run_metadata.json',base | {'episode':ep,'seed':seed,'started_at':self.started_at}); dump(path/'metadata.json',base | {'episode':ep,'seed':seed,'initial_state_index':base['initial_state_index'],'started_at':self.started_at})
    def snapshot(self,raw,env,label):
        g=self.h.require_group('frames').create_group(f'{self.frame:06d}'); g.attrs.update(stage=label,control_step=self.step,utc=now(),wall_time_ns=time.time_ns(),monotonic_ns=time.monotonic_ns())
        write_tree(g.create_group('raw_observation'),raw)
        sim=env._env.sim; d=sim.data
        state={'flattened':sim.get_state().flatten(),'time':float(d.time),'qpos':d.qpos.copy(),'qvel':d.qvel.copy(),'ctrl':d.ctrl.copy(),'body_xpos':d.body_xpos.copy(),'body_xquat':d.body_xquat.copy(),'site_xpos':d.site_xpos.copy(),'ncon':int(d.ncon)}
        contacts=[]
        for i in range(d.ncon):
            c=d.contact[i]; contacts.append({'geom1':int(c.geom1),'geom2':int(c.geom2),'dist':float(c.dist),'pos':c.pos.copy()})
        state['contacts']=contacts
        for name in ['qacc','act','sensordata','actuator_force','cfrc_ext','cvel','geom_xpos','geom_xmat','site_xmat']:
            if hasattr(d,name): state[name]=np.asarray(getattr(d,name)).copy()
        write_tree(g.create_group('simulator'),state)
        for cam in ['agentview_image','robot0_eye_in_hand_image']:
            if cam not in self.writers:
                self.writers[cam]=imageio.get_writer(self.path/(cam+'.mp4'),fps=20,codec='libx264',quality=8,macro_block_size=1)
            self.writers[cam].append_data(np.ascontiguousarray(raw[cam][::-1,::-1]))
        self.frame+=1
        return self.frame-1
    def finish(self,data,error=None):
        for w in self.writers.values(): w.close()
        resources=self.res.close(); self.h.flush(); self.h.close()
        success=bool(data['success'].any()) if data else False
        steps=int(data['action'].shape[1]) if data else self.step
        last=self.events[-1] if self.events else {}
        reason='exception' if error else 'success' if success else 'environment_terminated' if last.get('terminated') else 'time_limit'
        result={'suite':self.suite,'task_id':self.tid,'episode':self.ep,'seed':self.seed,'success':success,'pass_fail':'PASS' if success else 'ERROR' if error else 'FAIL','steps':steps,'elapsed_time_s':time.perf_counter()-self.started,'started_at':self.started_at,'finished_at':now(),'termination_reason':reason,'sum_reward':float(data['reward'].sum()) if data else None,'max_reward':float(data['reward'].max()) if data else None,'resource_peaks':resources,'error':error,'frames_including_settling_and_terminal':self.frame}
        result.update(max_process_rss_bytes=resources['process_rss_bytes'],max_gpu_used_bytes=resources['gpu_used_bytes'],peak_gpu_util_percent=resources['gpu_util_percent'],peak_cpu_percent=resources['process_cpu_percent'],peak_process_tree_rss_bytes=resources['process_tree_rss_bytes'],mean_gpu_util_percent=resources['mean_gpu_util_percent'],mean_cpu_percent=resources['mean_cpu_percent'],mean_gpu_power_w=resources['mean_gpu_power_w']); dump(self.path/'evaluation.json',result); dump(self.path/'summary.json',result)
        if data:
            with h5py.File(self.path/'trajectory.h5','a') as h: write_tree(h.create_group('upstream_rollout'),data)
        with (self.path/'metrics.csv').open('w') as f:
            cols=[k for k in result if k not in ['resource_peaks','error']]; w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerow({k:result[k] for k in cols})
        (self.path/'status.txt').write_text('error\n' if error else 'completed\n'); (self.path/'exit_code').write_text('1\n' if error else '0\n')
        return result

def main():
    global ACTIVE
    ap=argparse.ArgumentParser(); ap.add_argument('--suite',choices=SUITES,required=True); ap.add_argument('--episodes',type=int,default=50); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--smoke',action='store_true'); ap.add_argument('--seed',type=int,default=1000); args=ap.parse_args()
    out=args.output; out.mkdir(parents=True,exist_ok=True); (out/'runner.pid').write_text(str(os.getpid())+'\n'); (out/'started_at').write_text(now()+'\n'); (out/'status.txt').write_text('initializing\n'); (out/'exit_code').write_text('pending\n')
    dump(out/'launch.json',{'argv':sys.argv,'cwd':os.getcwd(),'env':{k:v for k,v in os.environ.items() if k in ['CUDA_VISIBLE_DEVICES','MUJOCO_GL','OMP_NUM_THREADS','HF_HOME','PIP_CACHE_DIR','LIBERO_CONFIG_PATH']}})
    from lerobot.envs.libero import LiberoEnv as BaseEnv
    from lerobot.envs.configs import LiberoEnv as EnvConfig
    from libero.libero import benchmark, get_libero_path
    from lerobot.configs.policies import PreTrainedConfig
    from flashvla.policies.factory import make_policy,make_pre_post_processors
    from lerobot.envs.factory import make_env_pre_post_processors
    from lerobot.utils.random_utils import set_seed
    spec=importlib.util.spec_from_file_location('upstream_eval',ROOT/'flashvla/sim_eval/libero/eval.py'); mod=importlib.util.module_from_spec(spec); sys.modules[spec.name]=mod; spec.loader.exec_module(mod)
    OriginalManager=mod.AsyncStreamingActionManager
    class RecordedManager(OriginalManager):
        def _launch_inference(self,obs):
            t=time.perf_counter(); result=super()._launch_inference(obs)
            if ACTIVE:
                g=ACTIVE.h.require_group('inference_calls').create_group(f'{ACTIVE.chunk:06d}'); g.attrs.update(step=ACTIVE.step,utc=now(),inference_dispatch_s=time.perf_counter()-t)
                write_tree(g.create_group('processed_inputs'),obs); write_tree(g.create_group('returned_action_chunk'),result); ACTIVE.chunk+=1
            return result
        def act(self,obs):
            t=time.perf_counter(); result=super().act(obs)
            if ACTIVE:
                g=ACTIVE.h.require_group('policy_steps').create_group(f'{ACTIVE.step:06d}'); g.attrs.update(utc=now(),act_elapsed_s=time.perf_counter()-t)
                write_tree(g.create_group('processed_observation'),obs); write_tree(g.create_group('manager_action'),result)
            return result
    mod.AsyncStreamingActionManager=RecordedManager
    class RecordedEnv(BaseEnv):
        def _make_envs_task(self,*a,**k):
            env=super()._make_envs_task(*a,**k); original=env.step
            def tapped(action):
                raw,reward,done,info=original(action)
                if ACTIVE:
                    ACTIVE.snapshot(raw,self,ACTIVE.stage)
                    if ACTIVE.stage=='settling':
                        g=ACTIVE.h.require_group('settling_actions').create_group(f'{ACTIVE.frame:06d}'); write_tree(g,{'action':action,'reward':reward,'done':done,'info':info})
                return raw,reward,done,info
            env.step=tapped
            return env
        def reset(self,*a,**k):
            if ACTIVE:
                ACTIVE.stage='settling'; i=self.init_state_id % len(self._init_states)
                write_tree(ACTIVE.h.create_group('benchmark_initial_state'),self._init_states[i])
                (ACTIVE.path/'simulator.xml').write_text(self._env.sim.model.get_xml())
                model=self._env.sim.model
                dump(ACTIVE.path/'simulator_index.json',{k:getattr(model,k) for k in ['body_names','joint_names','geom_names','site_names','camera_names','jnt_qposadr','jnt_dofadr'] if hasattr(model,k)})
            obs,info=super().reset(*a,**k)
            if ACTIVE:
                ACTIVE.stage='control'; ACTIVE.snapshot(self._env.env._get_observations(),self,'model_initial_observation')
            return obs,info
        def step(self,action):
            raw,reward,done,info=self._env.step(action); success=bool(self._env.check_success()); terminated=bool(done or success)
            info.update(task=self.task,task_id=self.task_id,done=done,is_success=success)
            if terminated: info['final_info']={'task':self.task,'task_id':self.task_id,'done':bool(done),'is_success':success}
            if ACTIVE:
                event={'step':ACTIVE.step,'utc':now(),'wall_time_ns':time.time_ns(),'monotonic_ns':time.monotonic_ns(),'simulator_time':float(self._env.sim.data.time),'reward':float(reward),'terminated':terminated,'truncated':False,'is_success':success,'info':info}
                write_tree(ACTIVE.h.require_group('transitions').create_group(f'{ACTIVE.step:06d}'),event | {'applied_action':action})
                ACTIVE.events.append(event); ACTIVE.res.step=ACTIVE.step; ACTIVE.res.sample('control_step'); ACTIVE.h.flush(); ACTIVE.step+=1
            return self._format_raw_obs(raw),reward,terminated,False,info
    suite_name=SUITES[args.suite]; suite=benchmark.get_benchmark_dict()[suite_name](); cfg=EnvConfig(task=suite_name,observation_height=256,observation_width=256)
    set_seed(args.seed); torch.backends.cudnn.benchmark=True; torch.backends.cuda.matmul.allow_tf32=True
    # Register FlashVLA config types before parsing the checkpoint.
    from flashvla.policies.pi05.configuration_pi05 import PI05FlashVLAConfig
    PreTrainedConfig._choice_registry["pi05-flashvla"]=PI05FlashVLAConfig
    pc=PreTrainedConfig.from_pretrained(str(ROOT/'flashvla-pi05-libero')); pc.pretrained_path=ROOT/'flashvla-pi05-libero'; pc.device='cuda'; pc.compile_model=False; pc.fuse_qkv=False; pc.fuse_gate_up=False
    policy=make_policy(pc,env_cfg=cfg); policy.eval()
    pre,post=make_pre_post_processors(pc,pc.pretrained_path,preprocessor_overrides={'device_processor':{'device':'cuda'},'rename_observations_processor':{'rename_map':{}},'tokenizer_processor':{'tokenizer_name':str(ROOT/'tokenizer')}})
    envpre,envpost=make_env_pre_post_processors(env_cfg=cfg,policy_cfg=pc)
    versions={d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
    manifest=json.loads((ROOT/'model-manifest.json').read_text())
    metadata={'model_family':'π0.5','checkpoint':'z-lab/flashvla-pi05-libero','checkpoint_revision':manifest['sha'],'base_model':'lerobot/pi05_base','model_url':'https://huggingface.co/z-lab/flashvla-pi05-libero','benchmark':'LIBERO','suite':suite_name,'inference_mode':'FlashVLA synchronous (d=0)','inference_overlap_steps':0,'episodes_per_task':args.episodes,'seed_start':args.seed,'policy_config':pc.to_dict() if hasattr(pc,'to_dict') else str(pc),'versions':versions,'python':sys.version,'platform':platform.platform(),'gpu':torch.cuda.get_device_name(),'flashvla_git_commit':subprocess.check_output(['git','-C',str(ROOT/'flashvla'),'rev-parse','HEAD'],text=True).strip(),'official_libero_git_commit':subprocess.check_output(['git','-C',str(ROOT/'LIBERO'),'rev-parse','HEAD'],text=True).strip(),'runtime_libero_module':__import__('libero').__file__,'recording_notes':{'terminal_autoreset':'Disabled after termination to retain terminal state; control, rewards and success checks follow upstream LiberoEnv.','videos':'Both camera images flipped for viewing; exact original uint8 images are stored losslessly in HDF5. 20 FPS = simulator control frequency.','time':'Wall times include recording overhead; not an uninstrumented latency benchmark.','resources':'GPU metrics are device-wide, process CPU/RAM metrics are runner-specific. Periodic 1s plus every control step.','model_outputs':'Public action chunk outputs and manager actions; no hidden activations or denoising instrumentation.','failure_reason':'Only observed termination reason is assigned automatically; causal failure taxonomy is left for analysis.'}}
    metadata['tokenizer_provenance']=json.loads((ROOT/'tokenizer/provenance.json').read_text()); metadata['runner_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(); metadata['runtime_source_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__import__('libero').__file__),Path(sys.modules[BaseEnv.__module__].__file__),ROOT/'flashvla/sim_eval/libero/eval.py']}; dump(out/'run_metadata.json',metadata); dump(out/'packages.json',versions); shutil.copy2(ROOT/'model-manifest.json',out/'model-manifest.json'); shutil.copy2(__file__,out/'research_runner.py')
    metrics=[]; task_ids=[0] if args.smoke else range(suite.n_tasks)
    for tid in task_ids:
        task=suite.get_task(tid); taskout=out/f'task_{tid:02d}'; taskout.mkdir(exist_ok=True)
        bddl=Path(get_libero_path('bddl_files'))/task.problem_folder/task.bddl_file; init=Path(get_libero_path('init_states'))/task.problem_folder/task.init_states_file
        shutil.copy2(bddl,taskout/'task.bddl'); shutil.copy2(init,taskout/'benchmark_initial_states.init')
        base=metadata | {'task_id':tid,'task_name':task.name,'instruction':task.language,'bddl_sha256':hashlib.sha256(bddl.read_bytes()).hexdigest(),'initial_states_sha256':hashlib.sha256(init.read_bytes()).hexdigest()}
        dump(taskout/'run_metadata.json',base); dump(taskout/'launch.json',json.loads((out/'launch.json').read_text())); (taskout/'status.txt').write_text('running\n'); (taskout/'runner.pid').write_text(str(os.getpid())+'\n'); (taskout/'started_at').write_text(now()+'\n')
        vec=gym.vector.SyncVectorEnv([lambda:RecordedEnv(suite,tid,suite_name,obs_type='pixels_agent_pos',observation_width=256,observation_height=256)],autoreset_mode=gym.vector.AutoresetMode.DISABLED)
        if tid==0:
            obs,_=vec.reset(seed=[args.seed]); obs=mod.preprocess_observation(obs); obs=mod.add_envs_task(vec,obs); obs=pre(envpre(obs))
            with torch.no_grad(): OriginalManager(policy,overlap_steps=0).warmup(obs)
            vec.envs[0].init_state_id=0
        try:
            for ep in range(args.episodes):
                epout=taskout/f'episode_{ep:03d}'; seed=args.seed+ep
                if (epout/'evaluation.json').exists():
                    prev=json.loads((epout/'evaluation.json').read_text())
                    if prev['pass_fail']!='ERROR': metrics.append(prev); continue
                    raise RuntimeError(f'Existing errored episode needs review: {epout}')
                vec.envs[0].init_state_id=ep
                ACTIVE=Recorder(epout,args.suite,tid,ep,seed,base|{'initial_state_index':ep % len(vec.envs[0]._init_states)})
                data=None; error=None
                # Keep task/episode stderr and stdout in an individual simulator log.
                with (epout/'simulator.log').open('w',buffering=1) as log:
                    oldout,olderr=os.dup(1),os.dup(2)
                    try:
                        sys.stdout.flush(); sys.stderr.flush(); os.dup2(log.fileno(),1); os.dup2(log.fileno(),2)
                        with torch.no_grad(): data=mod.rollout(vec,policy,envpre,envpost,pre,post,inference_overlap_steps=0,seeds=[seed],return_observations=False)
                    except Exception:
                        error=traceback.format_exc(); print(error,flush=True)
                    finally:
                        sys.stdout.flush(); sys.stderr.flush(); os.dup2(oldout,1); os.dup2(olderr,2); os.close(oldout); os.close(olderr)
                result=ACTIVE.finish(data,error); ACTIVE=None; metrics.append(result)
                summary={'completed_episodes':len(metrics),'successes':sum(x['success'] for x in metrics),'failures':sum(x['pass_fail']=='FAIL' for x in metrics),'errors':sum(x['pass_fail']=='ERROR' for x in metrics),'success_rate':sum(x['success'] for x in metrics)/len(metrics)}
                dump(out/'summary.json',summary); dump(out/'evaluation.json',metrics)
                for target,rows in [(out,metrics),(taskout,[x for x in metrics if x['task_id']==tid])]:
                    dump(target/'evaluation.json',rows)
                    with (target/'metrics.csv').open('w') as f:
                        cols=['suite','task_id','episode','seed','success','pass_fail','steps','elapsed_time_s','sum_reward','max_reward','termination_reason','started_at','finished_at','max_process_rss_bytes','max_gpu_used_bytes','peak_gpu_util_percent','peak_cpu_percent','peak_process_tree_rss_bytes','mean_gpu_util_percent','mean_cpu_percent','mean_gpu_power_w']; w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
                    dump(target/'summary.json',{'episodes':len(rows),'successes':sum(x['success'] for x in rows),'success_rate':sum(x['success'] for x in rows)/len(rows)}) if target==taskout else None
                print(json.dumps(result,default=convert),flush=True)
                if error: raise RuntimeError(error)
        finally: vec.close()
        (taskout/'status.txt').write_text('completed\n'); (taskout/'exit_code').write_text('0\n')
    (out/'status.txt').write_text('completed\n'); (out/'exit_code').write_text('0\n')
if __name__=='__main__':
    try: main()
    except BaseException:
        traceback.print_exc()
        if '--output' in sys.argv:
            p=Path(sys.argv[sys.argv.index('--output')+1]); p.mkdir(parents=True,exist_ok=True); (p/'status.txt').write_text('error\n'); (p/'exit_code').write_text('1\n')
        sys.exit(1)
