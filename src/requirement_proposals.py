"""Outcome-free input preparation and review-only candidate generation."""
import argparse, datetime, hashlib, json, time, urllib.request
from pathlib import Path

VERSION = 'requirements-v1'
def digest(data): return hashlib.sha256(data).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text())
def write(p, value):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def prepare(project, task_id=None):
    project = Path(project); tasks = read(project/'data/tasks.json')['records']
    eligible = [t for t in tasks if not t['facts']['task_instruction']['exact_mismatch']
                and t['facts']['task_instruction']['recorded_policy_instruction']
                and t['facts']['task_instruction']['prompt_token_check']['exact_instruction_in_all_decoded_prompts']]
    task = next((t for t in tasks if t['task_id']==task_id), None) if task_id else sorted(eligible, key=lambda t:t['task_id'])[0]
    if task is None: raise ValueError('Unknown task_id')
    i = tasks.index(task); facts = task['facts']; refs = {}; provenance = {}
    task_file_hash=digest((project/'data/tasks.json').read_bytes())
    def take(ref, pointer, value):
        refs[ref] = {'file':'data/tasks.json', 'json_pointer':f'/records/{i}/facts/{pointer}'}
        provenance[ref] = {**refs[ref],'sha256':task_file_hash}; return value
    instruction = facts['task_instruction']
    scene = facts['scene_description']; entities = []
    for kind, key in [('fixture','declared_fixtures'),('object','declared_objects')]:
        for name, category in scene[key].items():
            ref = 'entity:'+name
            entities.append({'entity_id':name,'kind':kind,'category_label':category,
                             'properties':{'material':'unknown','fragility':'unknown'},
                             'source_ref':ref})
            take(ref, 'scene_description/'+key+'/'+name, category)
    for surface in scene['native_surface_geometry']:
        name = surface['native_body_name']
        if not any(e['entity_id']==name for e in entities):
            ref = 'surface:'+name
            entities.append({'entity_id':name,'kind':'native_surface','properties':{'material':'unknown','fragility':'unknown'},'source_ref':ref})
            take(ref,'scene_description/native_surface_geometry/'+str(scene['native_surface_geometry'].index(surface)),surface)
    inventory = facts['available_measurements']; measurements = []
    # Key inventories only. No frame counts, sampled frame IDs, videos, or trajectory values.
    for group, key in [('raw_observation','common_raw_observation_keys'),('simulator','common_simulator_keys')]:
        for name in inventory[key]:
            if 'image' in name: continue
            mid = group+':'+name
            meaning = 'Recorded field; units, frame, and calibration require source review before checking.'
            if name=='contacts': meaning='Control-step contact geometry IDs, distance and position; no per-contact force or continuous substep coverage.'
            if name=='sensordata': meaning='Raw sensor array; named channel offsets, units and calibration are not mapped.'
            if name=='cfrc_ext': meaning='Body external force/torque array; not per-contact force or a damage signal.'
            if name.endswith('_pos'): meaning='Recorded position or relative-position vector; consult source configuration for exact frame and units before checking.'
            if name.endswith('_quat'): meaning='Recorded orientation or relative orientation quaternion; consult source configuration for ordering and frame.'
            if name in ['robot0_joint_pos','robot0_joint_vel','robot0_gripper_qpos','robot0_gripper_qvel']: meaning='Recorded robot joint/gripper position or velocity; no approved safety limits supplied.'
            measurements.append({'measurement_id':mid,'source_field':f'/frames/<frame_id>/{group}/{name}/value (serialized field; contacts use structured children)',
                                 'known_meaning':meaning,'source_ref':'measurement:'+mid})
            take('measurement:'+mid,'available_measurements/'+key+'/'+str(inventory[key].index(name)),name)
    result = {'schema_version':'1.0.0','task_id':task['task_id'],
      'selection':{'reason':'No designated development task found; stable task-ID order among tasks with verified exact instruction match; outcomes not consulted.',
                   'selected_using_outcomes':False},
      'recorded_policy_instruction':take('instruction','task_instruction/recorded_policy_instruction',instruction['recorded_policy_instruction']),
      'environment_bddl_language':take('bddl_language','task_instruction/environment_bddl_language',instruction['environment_bddl_language']),
      'instruction_mismatch':{'exact_mismatch':instruction['exact_mismatch'],
          'meaning_review_status':'needs_review' if instruction['exact_mismatch'] else 'exact_match'},
      'entities':entities,
      'scene':{}, 'intended_interaction':take('intended_interaction','intended_interaction',facts['intended_interaction']),
      'measurement_inventory':measurements,
      'measurement_limitations':take('measurement_limitations','available_measurements/missing_information',inventory['missing_information']),
      'missing_information':take('missing_information','missing_information',facts['missing_information']),
      'unknown_properties':{'human_presence':'unknown','restricted_regions':'unknown','physical_damage':'unknown'},
      'scope':take('scope','scope',facts['scope']), 'source_refs':refs,
      'source_file_sha256':{'data/tasks.json':task_file_hash}}
    for key in ['declared_fixtures','declared_objects','regions','native_surface_geometry','containers_named_by_goal_predicates','initial_predicates','scene_properties']:
        result['scene'][key] = take('scene:'+key,'scene_description/'+key,scene[key])
    # Actual native identity bindings, with all numeric initial pose measurements excluded.
    bindings = [{k:b[k] for k in ['name','kind','root_body_name','body_id','native_ids_scope']}
                for b in facts['objects']['reference_native_bindings']]
    result['native_identity_bindings'] = take('native_identity_bindings','objects/reference_native_bindings',bindings)
    result['native_identity_scope_run_id'] = facts['objects']['reference_run_id']
    bddl = project/'evidence/task_definitions'/f"{task['task_id']}.bddl"
    assert digest(bddl.read_bytes())==task['evidence']['bddl']['sha256']
    refs['bddl_file'] = {'file':str(bddl.relative_to(project)),'sha256':digest(bddl.read_bytes()),
                         'original_source':task['evidence']['bddl']['source_relative_path']}
    provenance['preparation_sources'] = {n:digest((project/n).read_bytes()) for n in ['data/tasks.json','data/runs.json','reports/source_manifest.json']}
    provenance['reference_run_id'] = facts['objects']['reference_run_id']
    provenance['task_evidence'] = task['evidence']
    return result, provenance

def validate(document, task_input, schema):
    from jsonschema import Draft202012Validator
    errors = [f'{"/".join(map(str,e.path))}: {e.message}' for e in Draft202012Validator(schema).iter_errors(document)]
    if errors: return errors
    if document['task_id']!=task_input['task_id']: errors.append('Incorrect task_id')
    if not document['candidate_requirements'] and not document['missing_information']:
        errors.append('Zero candidates require missing information or a reason')
    entities = {e['entity_id'] for e in task_input['entities']}
    inventory = {m['measurement_id'] for m in task_input['measurement_inventory']}
    refs = set(task_input['source_refs']); seen = set()
    for r in document['candidate_requirements']:
        if r['requirement_id'] is not None:
            if r['requirement_id'] in seen: errors.append('Duplicate requirement_id')
            seen.add(r['requirement_id'])
        if set(r['entities'])-entities: errors.append('Unknown entities: '+str(set(r['entities'])-entities))
        if set(r['supporting_input_refs'])-refs: errors.append('Unknown supporting_input_refs')
        missing = False
        for m in r['required_measurements']:
            if m['availability']=='present' and m['measurement_id'] not in inventory: errors.append('Measurement absent from inventory: '+str(m['measurement_id']))
            if m['availability']=='missing':
                missing=True
                if m['measurement_id'] is not None: errors.append('Missing measurement must have null measurement_id')
        if missing and r['checkability']=='potentially_checkable': errors.append('Missing measurements incompatible with potentially_checkable')
    if task_input['instruction_mismatch']['meaning_review_status']=='needs_review' and document['candidate_requirements']:
        errors.append('Task instruction mismatch needs review before proposals')
    return errors

def assign_ids(document, pilot_id, generation):
    for index, r in enumerate(document['candidate_requirements']):
        r['requirement_id']='proposal-'+digest(f"{pilot_id}:{generation}:{index}".encode())[:20]
    return document

def review_file(document):
    return {'task_id':document['task_id'],'scientific_review_status':'pending',
      'reviews':[{'requirement_id':r['requirement_id'],'decision':'pending','reviewer':'',
          'reviewer_comments':'','revised_requirement_text':'','reason_for_changes':''}
          for r in document['candidate_requirements']]}

def request_json(url, payload=None):
    data=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(url,data=data,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=1800) as f: return json.load(f)

def complete(config, messages, seed, tokenizer):
    settings=config['generation']
    template={'enable_thinking':settings['thinking'],'preserve_thinking':False,'reasoning_effort':settings['reasoning_effort']}
    rendered=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,**template)
    ids=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,**template)
    if len(ids)+settings['max_tokens']>settings['context_limit']: raise ValueError('Input plus output budget exceeds context; input was not truncated')
    payload={'model':config['model_repo'],'messages':messages,'temperature':settings['temperature'],
      'top_p':settings['top_p'],'top_k':settings['top_k'],'min_p':settings['min_p'],
      'presence_penalty':settings['presence_penalty'],'repetition_penalty':settings['repetition_penalty'],
      'max_tokens':settings['max_tokens'],'seed':seed,'reasoning_effort':settings['reasoning_effort'],
      'chat_template_kwargs':template,'return_prompt_text':True}
    start=time.monotonic(); raw=request_json(config['base_url']+'/chat/completions',payload)
    return raw, {'request':payload,'rendered_chat_template':rendered,'input_tokens':len(ids),
                 'template_matches':raw.get('prompt_text')==rendered,
                 'elapsed_seconds':time.monotonic()-start,'timestamp':now()}

def final_response(raw):
    choice=raw['choices'][0]; message=choice['message']
    if choice['finish_reason']!='stop': raise ValueError('Incomplete response: finish_reason='+str(choice['finish_reason']))
    text=message.get('content');reason=message.get('reasoning_content',message.get('reasoning'))
    if not isinstance(text,str) or not text.strip(): raise ValueError('Missing final response')
    if '<think>' in text or '</think>' in text: raise ValueError('Backend did not separate reasoning from final answer')
    return text, reason

def pilot(project, config_path, output):
    from transformers import AutoTokenizer
    project=Path(project);config=read(config_path);out=Path(output);out.mkdir(parents=True,exist_ok=False)
    source=project/'data/requirement_inputs/development.json';task_input=read(source)
    tokenizer=AutoTokenizer.from_pretrained(config['snapshot_path'],local_files_only=True,trust_remote_code=False)
    prompt=(project/'prompts/requirements-v1.txt').read_text();schema=read(project/'schemas/candidate_requirements.schema.json')
    input_hash=digest(source.read_bytes());pilot_id='requirements-'+digest((input_hash+str(out)+config['revision']).encode())[:20]
    write(out/'task_input.json',task_input);write(out/'config.json',config)
    (out/'prompt.txt').write_text(prompt);write(out/'schema.json',schema)
    write(out/'metadata.json',{'pilot_id':pilot_id,'input_sha256':input_hash,'prompt_version':VERSION,
       'prompt_sha256':digest(prompt.encode()),'schema_sha256':digest(json.dumps(schema,sort_keys=True).encode()),
       'created_at':now(),'scope':'candidate proposals only; no safety assessment or execution','source_provenance':read(source.with_name('provenance.json'))})
    for name in ['model_manifest.json','package_versions.txt','backend_settings_audit.json','server_command.json']:
        (out/name).write_bytes((project/'reports/requirement_pilot_queue'/name).read_bytes())
    smoke_messages=[{'role':'user','content':'Return the complete final JSON object {"smoke":"ok"}. No additional final-answer text.'}]
    raw,meta=complete(config,smoke_messages,900,tokenizer);write(out/'smoke_raw.json',raw);write(out/'smoke_request.json',meta)
    assert meta['template_matches'],'Backend did not apply the exact pinned chat template/settings'
    text,reason=final_response(raw);assert json.loads(text)=={'smoke':'ok'}
    assert raw.get('usage',{}).get('prompt_tokens')==meta['input_tokens'],'Backend template/token count differs from pinned local template'
    if config['generation']['thinking']: assert isinstance(reason,str) and reason.strip(),'Missing separated reasoning content'
    write(out/'smoke_validation.json',{'passed':True,'complete_final_response':True,'official_template_prompt_tokens_match':True,
       'settings_verification':'API request accepted; pinned local template token count matched; see backend implementation audit and server startup logs. Sampling effectiveness cannot be inferred from one output.'})
    base=[{'role':'system','content':prompt+'\nJSON schema:\n'+json.dumps(schema)},
          {'role':'user','content':json.dumps(task_input,ensure_ascii=False)}]
    results=[]
    for generation,seed in enumerate(config['generation']['seeds'],1):
        folder=out/f'generation_{generation:02d}';folder.mkdir();messages=list(base);valid=False
        for attempt in range(2):
            try: raw,meta=complete(config,messages,seed,tokenizer)
            except Exception as error:
                write(folder/f'attempt_{attempt+1}_transport_error.json',{'error':str(error),'timestamp':now(),'retry':bool(attempt)})
                break
            write(folder/f'attempt_{attempt+1}_raw.json',raw)
            meta.update(retry=bool(attempt),seed=seed);write(folder/f'attempt_{attempt+1}_metadata.json',meta)
            document=None;errors=[]
            try:
                if not meta['template_matches']: raise ValueError('Backend template/settings mismatch')
                text,reason=final_response(raw);(folder/f'attempt_{attempt+1}_final.txt').write_text(text)
                document=json.loads(text);errors=validate(document,task_input,schema)
            except (ValueError,KeyError,TypeError) as e: errors=[str(e)]
            write(folder/f'attempt_{attempt+1}_validation.json',{'structurally_valid':not errors,'errors':errors,
                'scientific_review':'pending','truncated':raw['choices'][0]['finish_reason']=='length','retry':bool(attempt)})
            if not errors:
                # Null allocation is allowed in the wire schema; content is never rewritten.
                original=json.loads(json.dumps(document));write(folder/'parsed_original.json',original)
                document=assign_ids(document,pilot_id,generation);assert not validate(document,task_input,schema)
                write(folder/'candidates.json',document);write(folder/'human_review.json',review_file(document));valid=True;break
            # One fresh, independent format-correction conversation. Preserve both attempts.
            messages=base+[{'role':'user','content':'One format/reference correction retry. Preserve your proposal meaning; do not approve it. Specific validation errors: '+json.dumps(errors)+'\nPrevious final response: '+str(raw['choices'][0]['message'].get('content',''))}]
        results.append({'generation':generation,'valid':valid,'path':str(folder)})
    write(out/'pilot_summary.json',{'pilot_id':pilot_id,'task_id':task_input['task_id'],'generations':results,'scientific_review':'pending'})
    if not all(r['valid'] for r in results): raise ValueError('Pilot finished with validation failures; all attempts preserved')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True)
    sub=ap.add_subparsers(dest='command',required=True);p=sub.add_parser('prepare');p.add_argument('--task-id')
    p=sub.add_parser('pilot');p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    if a.command=='prepare':
        value,provenance=prepare(a.project,a.task_id);p=a.project/'data/requirement_inputs';p.mkdir(exist_ok=False)
        write(p/'development.json',value);write(p/'provenance.json',provenance);print(value['task_id'])
    else: pilot(a.project,a.config,a.output)
if __name__=='__main__': main()
