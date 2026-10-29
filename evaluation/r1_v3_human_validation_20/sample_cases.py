"""Prediction-free, reproducible stratified selection from evidence identities."""
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
OBJECTS=['cream_cheese_1','ketchup_1','orange_juice_1','milk_1','butter_1']

def rank(seed,*parts):return hashlib.sha256('|'.join([seed,*parts]).encode()).hexdigest()

def select(protocol,inputs,evidence):
    source={r['run_id']:r for r in evidence['runs']}
    reserved=set(inputs['reserved_run_ids'])
    groups={'reserved_same_task':[r for r in source.values() if r['run_id'] in reserved],
            'changed_task':[r for r in source.values() if r['run_id'] not in reserved]}
    if len(groups['reserved_same_task'])!=10 or len(groups['changed_task'])!=50:raise ValueError('Expected 10/50 evidence partitions')
    selected=[];seed=protocol['seed']
    for stratum,records in groups.items():
        runs=sorted(records,key=lambda r:rank(seed,'runs',stratum,r['run_id']))[:10]
        objects=sorted(OBJECTS,key=lambda o:rank(seed,'objects',stratum,o))
        for i,r in enumerate(runs):selected.append(dict(r,stratum=stratum,object_id=objects[i%5],run_selection_digest=rank(seed,'runs',stratum,r['run_id'])))
    selected.sort(key=lambda r:rank(seed,'display',r['run_id'],r['object_id']))
    for i,r in enumerate(selected):r['case_id']=f'NV{i+1:02d}'
    return selected

if __name__=='__main__':
    out=HERE/'COORDINATOR_ASSIGNMENTS.json'
    if out.exists():raise FileExistsError(out)
    protocol=json.loads((HERE/'SAMPLING_PROTOCOL.json').read_text())
    parent=HERE.parent/'r1_v3_generalization'
    selected=select(protocol,json.loads((parent/'INPUTS.json').read_text()),json.loads((parent/'blinded_review/evidence_manifest.json').read_text()))
    out.write_text(json.dumps({'sampling_protocol':protocol,'cases':selected,'private_coordinator_only':True},indent=2)+'\n')
    print('\n'.join(f"{r['case_id']} {r['stratum']} episode {r['episode']:03d} {r['object_id']}" for r in selected))
