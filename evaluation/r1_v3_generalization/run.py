"""Independent-input harness around frozen v3. No checker or label changes."""
import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import math
import platform
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()


def save(path,data):
    Path(path).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')


def load_frozen(v3,release):
    freeze=json.loads((HERE/'FREEZE.json').read_text())
    for rel,digest in [('r1_checker.py',freeze['checker_sha256']),('execute.py',freeze['extractor_sha256']),('config.json',freeze['config_sha256'])]:
        if sha(v3/rel)!=digest:raise ValueError('Frozen v3 changed: '+rel)
    sys.path.insert(0,str(v3));sys.path.append(str(release/'src'))
    spec=importlib.util.spec_from_file_location('frozen_v3_execute',v3/'execute.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    from native_geometry_v2 import NativeGeometryIndex
    from run_development import value
    original=json.loads((release/'corrected_native_geometry_v2.json').read_text())
    if original['source_xml_sha256']!='a6177b7383b3b273ed1f41ad1ca342c921aea86584348a6d05a4bdff703e4542':raise ValueError('Wrong measurement mapping')
    return mod,NativeGeometryIndex,value,original


def bind_mapping(original,NativeGeometryIndex,record,xml_sha,native,geom_count):
    if xml_sha!=original['source_xml_sha256'] or native['body_names']!=original['body_names'] or geom_count!=original['native_geom_count']:
        raise ValueError('Frozen mapping does not support recording XML/body/native geometry identity')
    adapted=copy.deepcopy(original);adapted['validated_run_ids']=[record['run_id']]
    index=NativeGeometryIndex(adapted)
    inventory={}
    for entity in record['objects']:
        if entity['body_id']>=len(original['body_names']) or original['body_names'][entity['body_id']]!=entity['root_body_name']:raise ValueError('Entity/body identity mismatch')
        gs=index.geometries_for_body(entity['root_body_name'])
        if not gs:raise ValueError('Unmapped entity')
        inventory[entity['name']]=dict(native_geom_ids=[g['native_geom_id'] for g in gs])
    return index,inventory


def source_receipt(p,expected=None):
    if not p.is_file() or p.is_symlink():raise ValueError('Missing/symlinked input: '+str(p))
    actual=sha(p)
    if expected and actual!=expected:raise ValueError('Checksum mismatch: '+str(p))
    s=p.stat()
    return dict(path=str(p),sha256=actual,size=s.st_size,mtime_ns=s.st_mtime_ns)


def inventory(args):
    import h5py
    mod,NativeGeometryIndex,value,original=load_frozen(args.v3,args.release)
    inputs=json.loads((HERE/'INPUTS.json').read_text());root=Path(inputs['source_results'])
    args.output.mkdir(parents=True,exist_ok=False)
    candidates=inputs['records'];reviewed=[]
    for x in inputs['reviewed_run_ids']:
        reviewed.append(dict(run_id=x['run_id'],task_id='2448c758145ae5ad500f',suite='long',benchmark_task_id=0,episode=int(x['episode'].split('_')[-1]),
                             evidence=dict(trajectory=dict(source_relative_path='long/task_00/'+x['recording_ref'],expected_sha256=x['recording_sha256']),simulator_xml=dict(source_relative_path='long/task_00/'+x['episode']+'/simulator.xml',sha256=x['xml_sha256'])),objects=[]))
    records=[]
    for record in candidates+inputs['cross_scene_preflight_records']+reviewed:
        selected=record in candidates;original_four=record in reviewed
        result=dict(run_id=record['run_id'],task_id=record['task_id'],suite=record['suite'],benchmark_task_id=record['benchmark_task_id'],episode=record['episode'],selected=selected,
                    partition='reviewed_development' if original_four else 'same_task_reserved' if record['run_id'] in inputs['reserved_run_ids'] else 'cross_task_same_scene' if selected else 'cross_scene_preflight',eligible=False)
        try:
            trajectory=root/record['evidence']['trajectory']['source_relative_path'];folder=trajectory.parent
            receipts=[source_receipt(trajectory,record['evidence']['trajectory']['expected_sha256']),source_receipt(root/record['evidence']['simulator_xml']['source_relative_path'],record['evidence']['simulator_xml']['sha256'])]
            meta=json.loads((folder/'metadata.json').read_text());native=json.loads((folder/'simulator_index.json').read_text())
            receipts += [source_receipt(folder/'metadata.json'),source_receipt(folder/'simulator_index.json')]
            for key in ['native_index']:
                if key in record['evidence'] and receipts[-1]['sha256']!=record['evidence'][key]['sha256']:raise ValueError('Native-index manifest mismatch')
            if selected:
                expected=next((f.get('producer_integrity',{}).get('sha256') for f in record.get('execution_files',[]) if f['name']=='metadata.json' and f.get('producer_integrity')),None)
                if expected and expected!=receipts[-2]['sha256']:raise ValueError('Metadata producer hash mismatch')
            if meta['global_episode_id']!=record['run_id'] or meta['task_configuration_id']!=record['task_id'] or meta['checkpoint']!=inputs['expected_checkpoint']:raise ValueError('Metadata identity/checkpoint mismatch')
            model={k:meta.get(k) for k in ['checkpoint','checkpoint_revision','checkpoint_weight_sha256','model_configuration_id','experiment_id','initial_states_sha256','settling_steps','control_frequency_hz']}
            fingerprint=hashlib.sha256();initial=hashlib.sha256();protected=hashlib.sha256()
            with h5py.File(trajectory,'r') as h:
                if str(h.attrs['global_episode_id'])!=record['run_id'] or str(h.attrs['task_configuration_id'])!=record['task_id']:raise ValueError('HDF5 identity mismatch')
                if str(h.attrs['model_configuration_id'])!=meta['model_configuration_id']:raise ValueError('HDF5 model mismatch')
                frames=list(h['frames']);n=len(frames)
                if frames!=[f'{i:06d}' for i in range(n)] or n!=len(h['transitions'])+11 or n<=11:raise ValueError('Missing saved-frame domain')
                if str(h['frames/000010'].attrs['stage'])!='settling' or meta['settling_steps']!=10:raise ValueError('Frame-10 semantics mismatch')
                count=len(value(h['frames/000010'],'simulator/geom_xpos'))
                result.update(frame_count=n,terminal_frame=n-1,native_geom_count=count,body_names=native['body_names'],objects_present=[o['name'] for o in record['objects']],metadata=model,receipts_before=receipts)
                if selected:
                    bind_mapping(original,NativeGeometryIndex,record,receipts[1]['sha256'],native,count)
                    if not set(json.loads((args.v3/'config.json').read_text())['objects'])<={o['name'] for o in record['objects']}:raise ValueError('Protected object set incomplete')
                    result['eligible']=True
                elif not original_four:
                    try:bind_mapping(original,NativeGeometryIndex,record,receipts[1]['sha256'],native,count)
                    except ValueError as exc:result['preflight_blocker']=str(exc)
                    result['scope_missing_objects']=sorted(set(json.loads((args.v3/'config.json').read_text())['objects'])-{o['name'] for o in record['objects']})
                    result['named_table_present']='living_room_table' in native['body_names']
                if selected or original_four:
                    import numpy as np
                    ids=[i for g in original['geometries'] for i in [g['native_geom_id']] if g['owner_body'].split('_main')[0] in json.loads((args.v3/'config.json').read_text())['objects'] and g['collision_capable']]
                    for fi,key in enumerate(frames):
                        f=h['frames'][key];q=np.asarray(value(f,'simulator/qpos'),dtype='<f8')
                        fingerprint.update(q.tobytes())
                        if fi<=10:initial.update(q.tobytes())
                        gp=np.asarray(value(f,'simulator/geom_xpos'),dtype='<f8');gr=np.asarray(value(f,'simulator/geom_xmat'),dtype='<f8')
                        protected.update(gp[ids].tobytes());protected.update(gr[ids].tobytes())
                        if fi>10:fingerprint.update(np.asarray(value(h[f'transitions/{fi-11:06d}'],'executed_action'),dtype='<f8').tobytes())
                    result.update(trajectory_payload_sha256=fingerprint.hexdigest(),protected_geometry_stream_sha256=protected.hexdigest(),setup_qpos_sha256=initial.hexdigest())
            result['receipts_after']=[source_receipt(Path(x['path']),x['sha256']) for x in receipts]
            if result['receipts_before']!=result['receipts_after']:raise ValueError('Input stat/content changed')
        except Exception as exc:
            result.update(eligible=False,error=str(exc))
        records.append(result)
        print('INVENTORIED',result['partition'],record['episode'],result.get('error','OK'),flush=True)
    save(args.output/'inventory.json',dict(records=records,checkpoint_weights_qualification='Recorded metadata attestations compared; weight files are not rehashed and no model is run.'))


def run(args):
    import h5py
    mod,NativeGeometryIndex,value,original=load_frozen(args.v3,args.release)
    config=json.loads((args.v3/'config.json').read_text());physical=json.loads((args.release/'config.json').read_text())
    inputs=json.loads((HERE/'INPUTS.json').read_text());root=Path(inputs['source_results'])
    inventory_records={r['run_id']:r for r in json.loads((args.inventory/'inventory.json').read_text())['records']}
    args.output.mkdir(parents=True,exist_ok=False)
    allpred=[];logs=[]
    for record in inputs['records']:
        inv=inventory_records[record['run_id']];log=dict(run_id=record['run_id'],partition=inv['partition'],errors=[])
        if not inv['eligible']:
            for name in config['objects']:
                allpred.append(dict(run_id=record['run_id'],canonical_object_id=name,requirement_version=config['requirement_version'],applicability='insufficient_information',outcome='insufficient_information',events=[],measurement_frame_intervals=[],applicable_observation_intervals=[],abstention_reason=inv.get('error','Preflight failed'),partition=inv['partition']))
            logs.append(log);continue
        trajectory=root/record['evidence']['trajectory']['source_relative_path'];folder=trajectory.parent
        before=[source_receipt(Path(x['path']),x['sha256']) for x in inv['receipts_after']]
        native=json.loads((folder/'simulator_index.json').read_text())
        index,entities=bind_mapping(original,NativeGeometryIndex,record,inv['receipts_before'][1]['sha256'],native,inv['native_geom_count'])
        frames=[];previous_time=None
        with h5py.File(trajectory,'r') as h:
            for fi in range(inv['frame_count']):
                try:
                    g=h[f'frames/{fi:06d}'];index.validate_recording(record['run_id'],inv['receipts_before'][1]['sha256'],len(value(g,'simulator/geom_xpos')))
                    fact=mod.extract_frame(g,fi,index,entities,physical,config)
                    if not math.isfinite(fact['time']):raise ValueError('Nonfinite time')
                    if previous_time is not None and abs(fact['time']-previous_time-.05)>config['time_arithmetic_allowance_s']:raise ValueError('Timing gap')
                    if fi>10:
                        tr=h[f'transitions/{fi-11:06d}']
                        if int(value(tr,'step'))!=fi-11 or abs(float(value(tr,'simulator_time'))-fact['time'])>config['time_arithmetic_allowance_s']:raise ValueError('Transition timing mismatch')
                    previous_time=fact['time']
                except Exception as exc:
                    log['errors'].append(dict(frame=fi,error=str(exc)));previous_time=None
                    fact=dict(frame=fi,valid=False,contacts_complete=False,mapping_valid=False,objects={},error=str(exc))
                frames.append(fact)
        for name in config['objects']:
            p=mod.evaluate(frames,name,record['run_id'],config)
            p.update(partition=inv['partition'],recording_sha256=inv['receipts_before'][0]['sha256'],frozen_delivery_commit='d6657b8db2f9f91dad4931391b26ab88fee97a90',checker_sha256=sha(args.v3/'r1_checker.py'),configuration_sha256=sha(args.v3/'config.json'),mapping_sha256=sha(args.release/'corrected_native_geometry_v2.json'))
            allpred.append(p)
        with gzip.open(args.output/(record['run_id']+'_facts.json.gz'),'wt') as f:json.dump(frames,f)
        after=[source_receipt(Path(x['path']),x['sha256']) for x in before]
        if after!=before:raise ValueError('Original recording changed during read-only run')
        log.update(receipts_before=before,receipts_after=after,frames=inv['frame_count'],mapping_registration='Identical XML/native count/body names, entity roots/IDs and every-frame transforms checked; only run-ID input registration extended.')
        logs.append(log);print('PREDICTED',inv['partition'],record['episode'],flush=True)
    save(args.output/'predictions.json',allpred);save(args.output/'access_log.json',logs)
    save(args.output/'runtime.json',dict(python=sys.version,platform=platform.platform(),argv=sys.argv,checker_sha256=sha(args.v3/'r1_checker.py'),extractor_sha256=sha(args.v3/'execute.py'),config_sha256=sha(args.v3/'config.json'),harness_sha256=sha(Path(__file__)),reference_answers_loaded=False,simulation_stepped=False))
    save(args.output/'PREDICTION_SEAL.json',dict(files={p.name:sha(p) for p in sorted(args.output.iterdir()) if p.is_file()},reference_answers_loaded=False))
    print('SEALED',len(allpred),sha(args.output/'predictions.json'),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['inventory','run'])
    p.add_argument('--v3',type=Path,required=True);p.add_argument('--release',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--inventory',type=Path)
    a=p.parse_args();inventory(a) if a.command=='inventory' else run(a)
