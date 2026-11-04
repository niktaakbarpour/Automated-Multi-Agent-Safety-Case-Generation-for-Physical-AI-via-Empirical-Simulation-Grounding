"""Independent process replay, resume, strict-policy subset and deterministic schema assembly."""
import json,os,subprocess
from pathlib import Path
from .config import *
from .evaluate import run,canonical
from evaluation.r1_v4.provenance import digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha

def main():
 first=run('final');assert first['resumed']==448
 fresh=run('fresh');assert fresh['resumed']==0 and fresh['canonical_digest']==first['canonical_digest']
 small=run('partial',limit=37);assert small['executed']==37
 partial=run('partial');assert partial['resumed']==37 and partial['canonical_digest']==first['canonical_digest']
 strict=run('strict_subset',limit=40,verification_mode='strict')
 for p in (WORK/'strict_subset').glob('*.json'):
  a=json.loads(p.read_text());b=json.loads((WORK/'final'/p.name).read_text());assert a['metrics']['status_correct'] and not a['metrics']['errors'];assert a['metrics']['returned_citations']==b['metrics']['returned_citations'];assert a['bundle']['query_id']==b['bundle']['query_id']
 env={k:os.environ[k] for k in ('PATH','PYTHONPATH','PYTHONDONTWRITEBYTECODE','HF_HOME','XDG_CACHE_HOME') if k in os.environ};env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2');log=WORK/'isolated_replay.log'
 with log.open('w') as out:p=subprocess.run(['/usr/bin/python3','-S','-m','evaluation.r1_v4.rag_evidence_database.final_phase5_release.evaluate','--run','isolated'],cwd=str(REPO),env=env,stdout=out,stderr=subprocess.STDOUT)
 assert p.returncode==0,log;isolated=json.loads((WORK/'isolated_SUMMARY.json').read_text());assert isolated['canonical_digest']==first['canonical_digest']
 checked=0;digests={}
 for label in ('final','fresh','partial','isolated'):
  d={}
  for p in (WORK/label).glob('*.json'):
   r=json.loads(p.read_text());assert r['canonical_digest']==digest(canonical({k:v for k,v in r.items() if k!='canonical_digest'}));d[p.name]=r['canonical_digest'];checked+=1
  digests[label]=d
 assert all(d==digests['final'] for d in digests.values())
 from . import schema,capabilities
 assembly=WORK/'independent_assembly';assembly.mkdir();schema.HERE=assembly;schema.write();capabilities.HERE=assembly;capabilities.write()
 for name in ('STRUCTURED_QUERY_SCHEMA.json','EVIDENCE_BUNDLE_SCHEMA.json','CAPABILITY_REGISTRY.json'):assert sha(assembly/name)==sha(HERE/name),name
 result=dict(passed=True,full_resume=first,fresh=fresh,partial=partial,strict_subset=strict,isolated_process=isolated,independently_validated_case_files=checked,citations_stable=True,schemas_registry_byte_rebuild=True,source_database_sha256=sha(DATABASE),catalogue_sha256=sha(CATALOGUE),historical_environment_rebuilt=False,human_replication=False);(WORK/'REPRODUCIBILITY_RESULTS.json').write_text(json.dumps(result,sort_keys=True,indent=2));print('REPRODUCIBILITY PASS',checked,flush=True)
if __name__=='__main__':main()
