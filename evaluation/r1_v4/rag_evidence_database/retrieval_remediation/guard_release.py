"""New freeze and fresh scopes after a mandatory assurance guard; no ranking changes."""
import json,datetime
from .config import *
from .reference import scopes,make
from .holdout import BANK
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
def run():
 assert (HERE/'evaluation_v1/ARCHIVE.json').exists()
 f=json.loads((HERE/'evaluation_v1/FROZEN_IMPLEMENTATION.json').read_text());f.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),evaluation_version=2,implementation_version=VERSION+'-assurance-guard-1',security_correction='Only metadata-only typed-measurement guard; no intent/ranking rules changed',prior_evaluation_manifest_sha256=sha(HERE/'evaluation_v1/FROZEN_IMPLEMENTATION.json'));f['files']={n:sha(HERE/n) for n in f['files']};(HERE/'FROZEN_IMPLEMENTATION.json').write_text(json.dumps(f,sort_keys=True,indent=2))
 a=json.loads((HERE/'evaluation_v1/FROZEN_ACCEPTANCE_CRITERIA.json').read_text());a.update(created_utc=f['created_utc'],implementation_manifest_sha256=sha(HERE/'FROZEN_IMPLEMENTATION.json'),evaluation_version=2,additional_critical_cases='Nine metadata-only typed requirements replace formerly positive C7 scope instances; they must abstain. Thresholds unchanged.',previous_results_not_release_evidence=True);(HERE/'FROZEN_ACCEPTANCE_CRITERIA.json').write_text(json.dumps(a,sort_keys=True,indent=2))
 j=HERE.parent/'readiness_evaluation';excluded={r['execution'] for r in json.loads((j/'EVALUATION_SELECTION.json').read_text())};excluded|={r['execution_id'] for r in json.loads((WORK/'DEVELOPMENT_SELECTION.json').read_text())};excluded|={r['execution_id'] for r in json.loads((WORK/'HOLDOUT_SELECTION.json').read_text())};selected=scopes(dict(goal=6,long=6,object=6,spatial=6),excluded);rows=[]
 for i,s in enumerate(selected):
  other=next(x['binding']['variant_id'] for x in selected if x['binding']['variant_id']!=s['binding']['variant_id'])
  for category,bank in BANK.items():
   k=i%8;text,families,kind=bank[k];guard=category=='C7' and k in (0,4,6)
   if guard:families=[];kind='unsupported'
   q=make(s,category,text,families,kind,i,other);q.update(id=f'KH2-{category}-{i:02d}',split='holdout',template_id=category+'-'+str(k),template=text)
   if guard:q['request'].update({0:dict(units='kg'),4:dict(required_properties=['sensor_clock_synchronized']),6:dict(assurance='verified_physical_interpretation')}[k]);q['reference_limitation']='No measurement family requested; typed physical/unit/property requirements cannot be satisfied by metadata.'
   if category=='C9':q['narrow_value_claim']=dict(component=0,expected_equal=i%2==0,rule='Exact source component, no safety judgment')
   rows.append(q)
 p=HERE/'FROZEN_HOLDOUT_DATASET.jsonl';p.write_text(''.join(json.dumps(q,sort_keys=True,allow_nan=False)+'\n' for q in rows));(WORK/'HOLDOUT_SELECTION_V2.json').write_text(json.dumps(selected,sort_keys=True,indent=2));r=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),evaluation_version=2,dataset_sha256=sha(p),implementation_sha256=sha(HERE/'FROZEN_IMPLEMENTATION.json'),acceptance_sha256=sha(HERE/'FROZEN_ACCEPTANCE_CRITERIA.json'),questions=216,templates=72,executions=24,variants=len({s['binding']['variant_id'] for s in selected}),excluded_scopes=len(excluded),critical_abstentions=sum(q['critical_abstention'] for q in rows),ranking_eligible=sum(q['ranking_eligible'] for q in rows),fresh_execution_scopes=True,linguistic_holdout=False,known_template_overlap='Same frozen 72-template bank; V1 results exposed; no ranking or vocabulary correction made',human_evaluation=False);(HERE/'HOLDOUT_FREEZE.json').write_text(json.dumps(r,sort_keys=True,indent=2));print(r,flush=True)
if __name__=='__main__':run()
