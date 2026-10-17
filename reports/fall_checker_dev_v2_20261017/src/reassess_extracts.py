"""Saved-extract reassessment only. No HDF5, images or original robot files opened."""
import argparse,hashlib,json,gzip,re,collections
from pathlib import Path
import numpy as np
from checker import load_config,analyze
from native_geometry_v2 import NativeGeometryIndex
from run_development import allowed_run,build_frame_observations,commit_frame_observations

def reassess(root,old,out):
    out.mkdir(exist_ok=False)
    c=load_config(root/'config.json');split=json.loads((root/'proposed_split.json').read_text())
    index=NativeGeometryIndex.load(root/'corrected_native_geometry_v2.json')
    inventory={r['run_id']:{e['name']:e for e in r['entities']} for r in json.loads((root/'corrected_entity_inventory_v2.json').read_text())['records']}
    previous=json.loads((old/'outputs/summary.json').read_text());priors={d['run_id']:d for d in previous['development']}
    profiles=[('base',c)]+[(p['name'],dict(c,**{k:v for k,v in p.items() if k!='name'})) for p in c['sensitivity_profiles']]
    manifest=json.loads((old/'PACKAGE_MANIFEST.json').read_text())['files'];access=[];results=[];sensitivity=[];persistence_only=[]
    # Ablation: exact prior source, one corrected persistence predicate, no new event logic.
    text=(old/'src/checker.py').read_text();needle='if descending and unsupported else 0'
    assert text.count(needle)==1
    text=text.replace(needle,"if descending and unsupported and previous.get('valid',False) and not previous['direct_support'] and not previous['other_contacts'] and not previous['indirect_candidate'] and not previous['gripper_contacts'] else 0")
    ablation={};exec(compile(text,'prior_checker_persistence_only','exec'),ablation)
    for run in split['development']:
        allowed_run(run,split);prior=priors[run];ep=prior['episode'];rel=f'outputs/episode_{ep:03d}_geometry_contacts.json.gz';path=old/rel
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=manifest[rel]['sha256']:raise ValueError('Saved extract identity mismatch')
        with gzip.open(path,'rt') as f:bundles=json.load(f)
        byframe={b['frame']:b for b in bundles}
        if len(byframe)!=len(bundles):raise ValueError('Duplicate bundle frames')
        index.validate_recording(run,index.record['source_xml_sha256'],index.record['native_geom_count'])
        dest={p:{name:[] for name in c['objects']} for p,_ in profiles};errors=[]
        for fi in range(prior['frames']):
            b=byframe.get(fi)
            if b is None:
                ref={'run_id':run,'frame':fi};err='Missing saved geometry/contact bundle'
                staged={p:{name:dict(ref,valid=False,error=err) for name in c['objects']} for p,_ in profiles};errors.append(dict(ref,error=err))
            else:
                if b['run_id']!=run:raise ValueError('Per-run bundle identity mismatch')
                gp=np.asarray(b['geom_xpos']);gr=np.asarray(b['geom_xmat'])
                if gp.shape!=(161,3) or gr.shape!=(161,3,3) or not np.isfinite(gp).all() or not np.isfinite(gr).all():raise ValueError('Bad saved geometry bundle')
                if b['identity_guard']['physical_or_fall_tolerance'] is not False:raise ValueError('Missing qualified v2 identity guard')
                ref={k:v for k,v in b.items() if k not in ['geom_xpos','geom_xmat','contacts','identity_guard']}
                staged,err=build_frame_observations(ref,index,inventory[run],gp,gr,b['contacts'],profiles,c['objects'])
                if err is not None:errors.append(dict(ref,error=err))
            commit_frame_observations(dest,staged,fi)
        current={k:v for k,v in prior.items() if k!='objects'};current['errors']=errors
        for profile,pc in profiles:
            assert all(len(ss)==prior['frames'] and [s['frame'] for s in ss]==list(range(prior['frames'])) for ss in dest[profile].values())
            assessed={name:analyze(dest[profile][name],pc) for name in c['objects']}
            sensitivity.append({'run_id':run,'profile':profile,'objects':assessed})
            persistence_only.append({'run_id':run,'profile':profile,'objects':{name:ablation['analyze'](dest[profile][name],pc) for name in c['objects']}})
            if profile=='base':current['objects']=assessed
        with gzip.open(out/f'episode_{ep:03d}_observations_all_profiles.json.gz','wt') as f:json.dump(dest,f)
        (out/f'episode_{ep:03d}.json').write_text(json.dumps(current,indent=2));results.append(current)
        access.append({'run_id':run,'saved_extract':str(path),'sha256':digest,'original_recording_opened':False,'frames':len(bundles)})
        print('REASSESSED',ep,flush=True)
    for filename,data in [('summary.json',{'status':'PROVISIONAL_UNVALIDATED','development':results,'held_out':[{'run_id':r,'objects':{n:{'status':'not_processed','human_label':None} for n in c['objects']}} for r in split['held_out']]}),('sensitivity.json',sensitivity),('persistence_only_ablation.json',persistence_only),('access_log.json',access)]:
        (out/filename).write_text(json.dumps(data,indent=2))
    assert len(access)==40 and not set(split['held_out'])&{r['run_id'] for r in access}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--previous-release',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();reassess(a.root,a.previous_release,a.output)
