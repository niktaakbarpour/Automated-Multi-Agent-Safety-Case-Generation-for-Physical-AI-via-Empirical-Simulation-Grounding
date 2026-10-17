import argparse,collections,csv,hashlib,importlib.metadata,inspect,json,os,random,shutil,subprocess,sys,time,traceback
from pathlib import Path
import numpy as np,torch,h5py,yaml
import xml.etree.ElementTree as ET
from PIL import Image
import recording_base as base
from semantic_scene import semantic_scene
ROOT=Path(__file__).resolve().parent;base.ROOT=ROOT
SOURCE=ROOT/'source'
from oft_adapter import OpenVLAConfig,OpenVLAForActionPrediction,PrismaticImageProcessor,PrismaticProcessor,LlamaTokenizerFast,L1RegressionActionHead,ProprioProjector,load_state,get_vla_action,prepare_observation,process_action,official_globals
from types import SimpleNamespace
from libero.libero import benchmark,get_libero_path
from libero.libero.envs import OffScreenRenderEnv
SUITES=base.SUITES;HORIZONS={'spatial':220,'object':280,'goal':300,'long':520}
dump,write_tree,now=base.dump,base.write_tree,base.now
SCHEMA='4.0';ACTIVE=None
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def identity(d):return hashlib.sha256(json.dumps(d,sort_keys=True,default=base.convert).encode()).hexdigest()[:20]
def lifecycle(p,status,code='pending'):
 p.mkdir(parents=True,exist_ok=True)
 for n,v in [('status.txt',status),('exit_code',code),('runner.pid',os.getpid())]:(p/n).write_text(str(v)+'\n')
 if not (p/'started_at').exists():(p/'started_at').write_text(now()+'\n')
 if status in ['completed','error']:(p/'finished_at').write_text(now()+'\n')
def aggregate(p,rows):
 completed=[r for r in rows if r['pass_fail']!='ERROR'];dump(p/'evaluation.json',rows);dump(p/'errors.json',[r for r in rows if r['pass_fail']=='ERROR']);dump(p/'summary.json',{'updated_at':now(),'completed_episodes':len(completed),'passed':sum(r['success'] for r in completed),'failed':sum(r['pass_fail']=='FAIL' for r in completed),'errors':len(rows)-len(completed),'success_rate':sum(r['success'] for r in completed)/len(completed) if completed else None})
 cols=['global_episode_id','experiment_id','model_configuration_id','task_configuration_id','suite','task_id','episode','seed','success','pass_fail','steps','elapsed_time_s','termination_reason']
 with (p/'metrics.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(rows)
def evaluator_manifest():
 import libero.libero
 paths=list((Path(libero.libero.__file__).parent/'envs').rglob('*.py'));files={str(p):sha(p) for p in paths}
 return {'runtime_library':'hf_libero','runtime_library_version':importlib.metadata.version('hf_libero'),'official_benchmark_commit':subprocess.check_output(['git','-C','/local/home/niktakbr/smolVLA_libero/LIBERO','rev-parse','HEAD'],text=True).strip(),'implementation_files_sha256':files,'evaluator_version':identity(files),'success_signal':'Unmodified OffScreenRenderEnv.check_success and task _check_success'}
class Recorder(base.Recorder):
 def __init__(self,*args):
  super().__init__(*args);self.ids={k:self.base[k] for k in ['experiment_id','model_configuration_id','task_configuration_id','global_episode_id','recorder_schema_version','dataset_schema_version']}
  self.h.attrs.update(self.ids);self.h.attrs['schema_version']=SCHEMA
  (self.path/'exit_code').write_text('pending\n')
 def finish(self,data,error=None):
  r=super().finish(data,error);r.update(self.ids);
  with (self.path/'resources.csv').open() as f:reader=csv.DictReader(f);cols=reader.fieldnames;resource_rows=list(reader)
  with (self.path/'resources.csv').open('w') as f:
   writer=csv.DictWriter(f,fieldnames=cols+list(self.ids));writer.writeheader();writer.writerows(row|self.ids for row in resource_rows)
  dump(self.path/'summary.json',r);dump(self.path/'evaluation.json',r)
  with (self.path/'metrics.csv').open('w') as f:
   cols=[k for k in r if k not in ['resource_peaks','error']];w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerow({k:r[k] for k in cols})
  (self.path/'finished_at').write_text(r['finished_at']+'\n')
  files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in self.path.iterdir() if p.is_file() and p.name not in ['integrity_manifest.json','completion.json']}
  dump(self.path/'integrity_manifest.json',{'algorithm':'sha256','global_episode_id':self.ids['global_episode_id'],'files':files,'excluded':['integrity_manifest.json','completion.json']})
  for n,d in files.items():
   if sha(self.path/n)!=d['sha256']:raise RuntimeError('Integrity mismatch '+n)
  dump(self.path/'completion.json',{'complete':not bool(error),'global_episode_id':self.ids['global_episode_id'],'integrity_manifest_sha256':sha(self.path/'integrity_manifest.json'),'checksums_verified':True,'finished_at':now()});return r
def simulator_assets(xml):
 tree=ET.fromstring(xml);assets=[];compiler=tree.find('compiler')
 for e in tree.findall('./asset/*'):
  name=e.get('file')
  if not name:continue
  p=Path(name)
  if not p.is_absolute():
   directory=compiler.get('meshdir' if e.tag=='mesh' else 'texturedir','') if compiler is not None else '';p=Path(directory)/p
  p=p.resolve();assert p.is_file(),str(p)
  assets.append({'kind':e.tag,'name':e.get('name'),'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
 return {'algorithm':'sha256','assets':assets,'source':'Actual simulator XML mesh and texture file references; computed before control.'}

class Facade:
 def __init__(self,env,suite,horizon,seed):self._env=env;self.suite_name=suite;self._max_episode_steps=horizon;self.episode_seed=seed
def main():
 global ACTIVE
 ap=argparse.ArgumentParser();ap.add_argument('--suite',choices=SUITES,required=True);ap.add_argument('--episodes',type=int,default=50);ap.add_argument('--smoke',action='store_true');ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 plan=json.loads((ROOT/'experiment_plan.json').read_text());assert a.suite in plan['suite_labels']
 model_dir=ROOT/'model';model_manifest=json.loads((ROOT/'model_manifest.json').read_text());checkpoint_id=model_manifest['repo']
 assert model_manifest['passed'] and checkpoint_id==plan['model'] and model_manifest['revision']==plan['revision']
 for name,entry in model_manifest['files'].items():assert sha(model_dir/name)==entry['sha256'],name
 out=a.output;lifecycle(out,'initializing');dump(out/'launch.json',{'argv':sys.argv,'cwd':os.getcwd(),'environment':{k:os.environ.get(k) for k in ['CUDA_VISIBLE_DEVICES','MUJOCO_GL','MUJOCO_EGL_DEVICE_ID','LIBERO_CONFIG_PATH','HF_HOME','OMP_NUM_THREADS','TF_ENABLE_ONEDNN_OPTS']}})
 random.seed(1000);np.random.seed(1000);torch.manual_seed(1000);torch.cuda.manual_seed_all(1000)
 torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False
 cfg=OpenVLAConfig.from_pretrained(model_dir,local_files_only=True)
 policy=OpenVLAForActionPrediction.from_pretrained(model_dir,config=cfg,attn_implementation='sdpa',torch_dtype=torch.bfloat16,low_cpu_mem_usage=True,local_files_only=True).to('cuda').eval()
 policy.vision_backbone.set_num_images_in_input(2)
 policy.norm_stats=json.loads((model_dir/'dataset_statistics.json').read_text())
 unnorm_key=SUITES[a.suite] if SUITES[a.suite] in policy.norm_stats else SUITES[a.suite]+'_no_noops'
 assert unnorm_key in policy.norm_stats
 oft_cfg=SimpleNamespace(use_l1_regression=True,use_diffusion=False,use_film=False,num_images_in_input=2,use_proprio=True,center_crop=True,num_open_loop_steps=8,unnorm_key=unnorm_key,model_family='openvla')
 head_paths=list(model_dir.glob('action_head--*.pt'));proprio_paths=list(model_dir.glob('proprio_projector--*.pt'));assert len(head_paths)==len(proprio_paths)==1
 action_head=L1RegressionActionHead(input_dim=policy.llm_dim,hidden_dim=policy.llm_dim,action_dim=7).to(torch.bfloat16).to('cuda').eval()
 action_head.load_state_dict(load_state(head_paths[0]),strict=True)
 proprio_projector=ProprioProjector(llm_dim=policy.llm_dim,proprio_dim=8).to(torch.bfloat16).to('cuda').eval()
 proprio_projector.load_state_dict(load_state(proprio_paths[0]),strict=True)
 processor=PrismaticProcessor(image_processor=PrismaticImageProcessor.from_pretrained(model_dir,local_files_only=True),tokenizer=LlamaTokenizerFast.from_pretrained(model_dir,local_files_only=True))
 evaluator=evaluator_manifest();weights=model_manifest['files']
 inference={'mode':'synchronous official OpenVLA-OFT L1 action-head prediction','asynchronous':False,'inference_overlap_steps':0,'chunk_size':8,'executed_actions_per_prediction':8,'do_sample':False,'temperature':None,'temperature_applicability':'Continuous L1 regression, not sampled action tokens','diffusion_steps':None,'precision':'bfloat16','quantization':False,'compile_model':False,'attention_implementation':'sdpa','attention_note':'Official fork SDPA path provides bidirectional parallel action decoding. No compilation or backend/fusion override.','control_frequency_hz':20,'observation_resolution':[256,256],'model_image_resolution':[224,224],'model_cameras':['agentview_image','robot0_eye_in_hand_image'],'use_proprio':True,'proprio_dimension':8,'action_head':'L1RegressionActionHead','use_diffusion':False,'use_film':False,'recorded_cameras':['agentview_image','robot0_eye_in_hand_image'],'center_crop':True,'crop_area_scale':0.9,'image_orientation':'180 degree rotation, official JPEG roundtrip and TF Lanczos3 resize, then official center crop','unnorm_key':unnorm_key,'normalization_statistics':policy.norm_stats[unnorm_key],'gripper_mapping':'official binarize 2*x-1 then invert sign','cuda_matmul_allow_tf32':torch.backends.cuda.matmul.allow_tf32,'cudnn_allow_tf32':torch.backends.cudnn.allow_tf32}
 source_files={str(p.relative_to(ROOT)):sha(p) for p in SOURCE.rglob('*.py')}
 source_files.update({p.name:sha(p) for p in [Path(__file__),ROOT/'recording_base.py',ROOT/'semantic_scene.py',ROOT/'oft_adapter.py']})
 mid=identity({'checkpoint':weights,'inference':inference,'sources':source_files});eid=plan['experiment_id']+('_smoke' if a.smoke else '')
 meta={'experiment_id':eid,'evaluation_group_id':'openvla-oft-libero-gpu0','model_configuration_id':mid,'recorder_schema_version':SCHEMA,'dataset_schema_version':SCHEMA,'schema_compatibility':'4.0 records native 8-action chunks, control-step offsets and normalized proprio; common raw/state/semantic/resource layout retained','model_family':'OpenVLA-OFT 7B','checkpoint':checkpoint_id,'checkpoint_revision':model_manifest['revision'],'checkpoint_weight_sha256':{k:v['sha256'] for k,v in weights.items() if k.endswith(('.safetensors','.pt')) and not k.startswith('lora_adapter/')},'downloaded_checkpoint_files':weights,'checkpoint_files':{k:v for k,v in weights.items() if not k.startswith('lora_adapter/') and k not in ['README.md','.gitattributes','modeling_prismatic.py','configuration_prismatic.py','processing_prismatic.py']},'model_url':plan['original_model_url'],'base_model':'openvla/openvla-7b','benchmark':'LIBERO','suite':SUITES[a.suite],'inference_configuration':inference,'resolved_policy_configuration':cfg.to_dict(),'evaluator':evaluator,'source_files_sha256':source_files,'source_commit':subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip(),'versions':{name:importlib.metadata.version(name) for name in {d.metadata['Name'] for d in importlib.metadata.distributions()}},'python':sys.version,'platform':sys.platform,'gpu':torch.cuda.get_device_name(),'gpu_driver':subprocess.check_output(['nvidia-smi','--query-gpu=driver_version','--format=csv,noheader'],text=True).splitlines()[2],'physical_gpu_index':int(os.environ['CUDA_VISIBLE_DEVICES']),'episodes_per_task':a.episodes,'seed_start':1000,'smoke':a.smoke}
 meta['oft_configuration']=vars(oft_cfg);meta['loaded_component_files']=[str(head_paths[0].relative_to(model_dir)),str(proprio_paths[0].relative_to(model_dir))];meta['transformers_fork']={'repo':'https://github.com/moojink/transformers-openvla-oft','commit':'bc339d9ad707454c0c115970db43c260067c61ab','loaded_llama_implementation':inspect.getsourcefile(type(policy.language_model)),'loaded_llama_sha256':sha(inspect.getsourcefile(type(policy.language_model)))}
 meta['job_plan_file']=str(ROOT/'experiment_plan.json')
 meta['recording_notes']={'protocol_adapter':'Official OpenVLA-OFT preprocessing, native predict_action/action head and gripper mapping; native 8-action open-loop chunks. Official per-trial initial states and horizon; per-episode seeds 1000-1049 replace author single run seed 7. Settling action [0,0,0,0,0,0,-1], 10 steps. No autoreset.','videos':'20 FPS, display rotated 180 degrees; raw lossless frames unchanged. Full control-step coverage including initial, settling and terminal; no intermediate physics video.','timing':'Includes recording and synchronization overhead; native bidirectional parallel decoding through pinned official Transformers fork, native SDPA attention, no FlashAttention.','resources':'Device GPU and host metrics shared; process CPU/RAM/GPU memory separate; sample-weighted means; 1s and every control step.','unavailable':'No hidden activations or internal autoregressive action tokens; public predict_action result retained. Internal reset sampler draws unavailable. Scalar multi-target/predicate-only fields null with named mappings. Both cameras and 8D proprioception are model inputs. Public returned action chunks retained; public auxiliary hidden-state output intentionally omitted.'}
 dump(out/'run_metadata.json',meta);dump(out/'evaluator_manifest.json',evaluator)
 (out/'model_info.txt').write_text('Model: '+checkpoint_id+'\nURL: '+meta['model_url']+'\nLoaded weights: '+str(model_dir/'model.safetensors.index.json')+'\nSuite: '+SUITES[a.suite]+'; episodes/task: '+str(a.episodes)+'; GPU: '+os.environ['CUDA_VISIBLE_DEVICES']+'\nEffective configuration and provenance:\n'+json.dumps(meta,default=base.convert,indent=2)+'\n');(out/'experiment.txt').write_text((out/'model_info.txt').read_text());(out/'RECORDING_GUIDE.txt').write_text(json.dumps(meta['recording_notes'],indent=2))
 original_predict=policy.predict_action
 def predict(*args,**kwargs):
  g=ACTIVE.h.require_group('inference_calls').create_group(f'{ACTIVE.chunk:06d}');g.attrs.update(step=ACTIVE.step,utc=now(),chunk_id=ACTIVE.chunk)
  write_tree(g.create_group('processed_inputs'),{k:v for k,v in kwargs.items() if not isinstance(v,torch.nn.Module)});write_tree(g.create_group('rng_before_inference'),{'torch_cpu':torch.get_rng_state(),'torch_cuda':torch.cuda.get_rng_state()})
  torch.cuda.synchronize();start=time.perf_counter();result=original_predict(*args,**kwargs);torch.cuda.synchronize();g.attrs['inference_elapsed_s']=time.perf_counter()-start
  write_tree(g.create_group('public_action_chunk'),result[0]);ACTIVE.chunk+=1;return result
 policy.predict_action=predict
 class RecordingProcessor:
  def __call__(self,prompt,image):
   parent=ACTIVE.h.require_group('preprocessing').require_group(f'{ACTIVE.chunk:06d}');g=parent.create_group(f'image_{len(parent):02d}')
   write_tree(g,{'prompt':prompt,'preprocessed_pil_rgb':np.asarray(image),'step':ACTIVE.step})
   return processor(prompt,image)
 recorded_processor=RecordingProcessor()
 suite=benchmark.get_benchmark_dict()[SUITES[a.suite]]();rows=[];lifecycle(out,'running');dump(out/'task_plan.json',{'suite':SUITES[a.suite],'task_count':suite.n_tasks,'episodes_per_task':50,'planned_episodes':suite.n_tasks*50,'tasks':[suite.get_task(i).name for i in range(suite.n_tasks)],'selected_task_ids':[0] if a.smoke else list(range(suite.n_tasks)),'selected_episodes_per_task':a.episodes,'selected_episode_count':a.episodes*(1 if a.smoke else suite.n_tasks)})
 for tid in ([0] if a.smoke else range(suite.n_tasks)):
  task=suite.get_task(tid);td=out/f'task_{tid:02d}';lifecycle(td,'running');bddl=Path(get_libero_path('bddl_files'))/task.problem_folder/task.bddl_file;init=Path(get_libero_path('init_states'))/task.problem_folder/task.init_states_file;states=suite.get_task_init_states(tid)
  tc={'task_suite':SUITES[a.suite],'suite_label':a.suite,'task_id':tid,'task_name':task.name,'instruction':task.language,'bddl_sha256':sha(bddl),'initial_states_sha256':sha(init),'task_horizon':HORIZONS[a.suite],'observation_size':[256,256],'control_frequency_hz':20,'settling_steps':10,'initial_state_protocol':'episode index modulo official archive length','randomization':'no added domain randomization','evaluator_version':evaluator['evaluator_version']}
  tm=meta|tc|{'task_configuration_id':identity(tc)};dump(td/'run_metadata.json',tm);shutil.copy2(bddl,td/'task.bddl');shutil.copy2(init,td/'benchmark_initial_states.init');shutil.copy2(out/'launch.json',td/'launch.json')
  env=OffScreenRenderEnv(bddl_file_name=str(bddl),camera_heights=256,camera_widths=256)
  try:
   for ep in range(a.episodes):
    if shutil.disk_usage(out).free<250*1024**3:raise RuntimeError('Disk reserve below 250 GiB; current episode not started')
    seed=1000+ep;random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed);gid=f'libero_{a.suite}_openvla_oft_task{tid:02d}_seed{seed}_trial{ep:03d}_{eid[-12:]}' + ('_smoke' if a.smoke else '')
    em=tm|{'global_episode_id':gid,'initial_state_index':ep%len(states),'episode':ep,'seed':seed,'simulator_asset_manifest':'simulator_asset_manifest.json'};path=td/f'episode_{ep:03d}';ACTIVE=Recorder(path,a.suite,tid,ep,seed,em);facade=Facade(env,SUITES[a.suite],HORIZONS[a.suite],seed);data=None;error=None;oldout,olderr=os.dup(1),os.dup(2)
    with (path/'simulator.log').open('w',buffering=1) as log:
     try:
      sys.stdout.flush();sys.stderr.flush();os.dup2(log.fileno(),1);os.dup2(log.fileno(),2);env.seed(seed);env.reset();raw=env.set_init_state(states[ep%len(states)]);write_tree(ACTIVE.h.create_group('benchmark_initial_state'),states[ep%len(states)])
      ACTIVE.snapshot(raw,facade,'before_settling');phases={'before_settling':semantic_scene(facade,raw,'before_settling')}
      for settle in range(10):
       raw,r,d,info=env.step(np.array([0,0,0,0,0,0,-1],dtype=np.float32));ACTIVE.snapshot(raw,facade,'settling');write_tree(ACTIVE.h.require_group('settling_actions').create_group(f'{settle:03d}'),{'executed_action':np.array([0,0,0,0,0,0,-1]),'reward':r,'done':d,'info':info})
      phases['before_first_action']=semantic_scene(facade,raw,'before_first_action');dump(path/'semantic_initial_conditions.json',{'global_episode_id':gid,'recorder_schema_version':SCHEMA,'phases':phases});(path/'simulator.xml').write_text(env.sim.model.get_xml());dump(path/'simulator_asset_manifest.json',simulator_assets(env.sim.model.get_xml()));m=env.sim.model;dump(path/'simulator_index.json',{k:getattr(m,k) for k in ['body_names','joint_names','geom_names','site_names','camera_names','jnt_qposadr','jnt_dofadr'] if hasattr(m,k)})
      fn=env.env._check_success;source=inspect.getsource(fn);dump(path/'evaluator_version.json',evaluator|{'task_success_callable':fn.__module__+'.'+fn.__qualname__,'task_success_source_sha256':sha(inspect.getsourcefile(fn)),'success_method_source_sha256':hashlib.sha256(source.encode()).hexdigest(),'goal_predicates':env.env.parsed_problem.get('goal_state')});(path/'success_condition_source.py.txt').write_text(source);write_tree(ACTIVE.h.create_group('language_inputs'),{'instruction':task.language,'note':'Exact prompt, token IDs/mask, normalized proprio and two-camera pixels saved at each inference.'})
      action_queue=collections.deque(maxlen=8);acts=[];rewards=[];successes=[];dones=[];latencies=[];start=time.perf_counter()
      with torch.inference_mode():
       for step in range(HORIZONS[a.suite]):
        triggered=not action_queue;t=time.perf_counter()
        g=ACTIVE.h.require_group('policy_steps').create_group(f'{step:06d}')
        if triggered:
         observation,img=prepare_observation(raw,224)
         write_tree(g.create_group('prepared_observation'),{k:v.copy() if isinstance(v,np.ndarray) else v for k,v in observation.items()})
         cid=ACTIVE.chunk
         public_chunk=np.asarray(get_vla_action(oft_cfg,policy,recorded_processor,observation,task.language,action_head=action_head,proprio_projector=proprio_projector,use_film=False))
         assert public_chunk.shape==(8,7) and np.isfinite(public_chunk).all()
         action_queue.extend((cid,offset,row.copy()) for offset,row in enumerate(public_chunk))
        cid,offset,selected=action_queue.popleft()
        g.attrs.update(step=step,utc=now(),chunk_id=cid,chunk_offset=offset,triggered_inference=triggered)
        write_tree(g.create_group('public_action'),selected.copy())
        action=process_action(selected.copy(),'openvla')
        latencies.append((time.perf_counter()-t)*1000)
        write_tree(g.create_group('postprocessed_action_chunk'),action.reshape(1,1,7))
        if not np.isfinite(action).all():raise RuntimeError('Nonfinite model action')
        write_tree(g.create_group('executed_action'),action);raw,reward,done,info=env.step(action);success=bool(env.check_success());terminated=bool(done or success);truncated=step+1>=HORIZONS[a.suite] and not terminated
        ACTIVE.snapshot(raw,facade,'terminal' if terminated or truncated else 'control');event={'step':step,'utc':now(),'wall_time_ns':time.time_ns(),'monotonic_ns':time.monotonic_ns(),'simulator_time':float(env.sim.data.time),'reward':float(reward),'terminated':terminated,'truncated':truncated,'is_success':success,'info':info};write_tree(ACTIVE.h.require_group('transitions').create_group(f'{step:06d}'),event|{'executed_action':action});ACTIVE.events.append(event);ACTIVE.res.step=step;ACTIVE.res.sample('control_step');ACTIVE.step+=1;ACTIVE.h.flush()
        acts.append(torch.tensor(action).unsqueeze(0));rewards.append(torch.tensor([reward]));successes.append(torch.tensor([success]));dones.append(torch.tensor([terminated or truncated]))
        if terminated or truncated:break
      data={'action':torch.stack(acts,dim=1),'reward':torch.stack(rewards,dim=1),'success':torch.stack(successes,dim=1),'done':torch.stack(dones,dim=1),'step_latencies_ms':latencies,'rollout_walltime_s':time.perf_counter()-start}
     except Exception:error=traceback.format_exc();print(error,flush=True)
     finally:
      sys.stdout.flush();sys.stderr.flush();os.dup2(oldout,1);os.dup2(olderr,2);os.close(oldout);os.close(olderr)
    r=ACTIVE.finish(data,error);ACTIVE=None;rows.append(r);aggregate(td,[x for x in rows if x['task_id']==tid]);aggregate(out,rows);print(json.dumps(r,default=base.convert),flush=True)
    if error:raise RuntimeError(error)
  finally:env.close()
  lifecycle(td,'completed',0)
 lifecycle(out,'completed',0)
if __name__=='__main__':
 try:main()
 except BaseException:
  traceback.print_exc()
  if '--output' in sys.argv:
   failed_out=Path(sys.argv[sys.argv.index('--output')+1]);lifecycle(failed_out,'error',1)
   for task_status in failed_out.glob('task_*/status.txt'):
    if task_status.read_text().strip() in ['running','initializing']:lifecycle(task_status.parent,'error',1)
  sys.exit(1)
