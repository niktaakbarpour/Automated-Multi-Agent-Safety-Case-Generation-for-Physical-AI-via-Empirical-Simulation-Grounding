"""Recompute frozen v3 core outputs from sealed derived facts, without labels."""
import argparse
import gzip
import json
from pathlib import Path
from execute import HERE,sha,save
from r1_checker import evaluate


def replay(execution,output):
    if output.exists():raise FileExistsError(output)
    freeze=json.loads((HERE/'FREEZE.json').read_text())
    for name,digest in freeze['implementation_files'].items():
        if sha(HERE/name)!=digest:raise ValueError('Frozen implementation changed: '+name)
    seal=json.loads((execution/'PREDICTION_SEAL.json').read_text())
    for name,digest in seal['files'].items():
        if Path(name).name!=name or sha(execution/name)!=digest:raise ValueError('Evidence missing or changed: '+name)
    config=json.loads((HERE/'config.json').read_text())
    manifest=json.loads((HERE.parent/'r1_reference/recordings.json').read_text())
    predictions=json.loads((execution/'predictions.json').read_text())
    records=[]
    for run in manifest['runs']:
        with gzip.open(execution/(run['episode']+'_facts.json.gz'),'rt') as f:facts=json.load(f)
        for p in predictions:
            if p['run_id']!=run['run_id']:continue
            again=evaluate(facts,p['canonical_object_id'],p['run_id'],config)
            if not all(p[k]==v for k,v in again.items()):raise ValueError('Replay mismatch')
            records.append(dict(run_id=p['run_id'],object_id=p['canonical_object_id'],core_output_identical=True))
    if len(records)!=20:raise ValueError('Missing replay units')
    save(output,dict(facts_and_all_artifact_hashes_verified=True,replayed_units=len(records),all_core_outputs_identical=True,units=records,reference_answers_loaded=False))
    print('Verified and reproduced',len(records),'sealed core predictions; no reference inputs.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execution',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();replay(a.execution,a.output)
