"""Second automated pass plus full and partial resume; not independent human replication."""
import json,shutil
from evaluation.r1_v4.provenance import digest
from .config import WORK
from .run import run

def execute():
 first=run('final','final_v1');(WORK/'final_v1_INITIAL_SUMMARY.json').write_text(json.dumps(first,sort_keys=True,indent=2))
 second=run('final','final_v2');assert first['canonical_digest']==second['canonical_digest']
 resumed=run('final','final_v1');assert resumed['resumed']==486 and resumed['canonical_digest']==first['canonical_digest']
 p=WORK/'partial_replay';p.mkdir();files=sorted((WORK/'final_v1').glob('*.json'))
 for f in files[:37]:shutil.copyfile(f,p/f.name)
 partial=run('final','partial_replay');assert partial['resumed']==37 and partial['canonical_digest']==first['canonical_digest']
 differences=[]
 for f in files:
  a=json.loads(f.read_text());b=json.loads((WORK/'final_v2'/f.name).read_text());c=json.loads((p/f.name).read_text())
  if not(a['canonical_digest']==b['canonical_digest']==c['canonical_digest']):differences.append(f.name)
 assert not differences
 result=dict(passed=True,independent_automated_pass=True,independent_human_replication=False,first=first,second=second,full_resume=resumed,partial_resume=partial,canonical_case_differences=differences,canonicalization='Ignore only scratch diagnostic hash/path; every value, identity, rank, status and rubric requirement must match')
 (WORK/'REPLAY_VALIDATION.json').write_text(json.dumps(result,sort_keys=True,indent=2));print('REPLAY VERIFIED',flush=True)
if __name__=='__main__':execute()
