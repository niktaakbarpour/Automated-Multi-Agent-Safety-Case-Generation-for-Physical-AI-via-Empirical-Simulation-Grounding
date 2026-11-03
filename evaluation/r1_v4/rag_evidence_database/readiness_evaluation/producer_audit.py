"""Investigate the declared missing producer file without inventing a replacement."""
import json,zipfile,collections
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import owned
from .config import WORK,HERE,DATABASE

def run():
 inv=json.loads((DATABASE.parent/'PRODUCER_EVIDENCE.json').read_text());rows=[];candidates={};hashes=collections.Counter()
 for e in inv['rows']:
  f=next(x for x in e['producer_files'] if x['relative_path']=='oft_adapter.py');hashes[f['recorded_sha256']]+=1
  rows.append(dict(execution_id=e['execution_id'],declared_sha256=f['recorded_sha256'],available_matching_path=f['available_matching_path'],status='MISSING_AVAILABLE_BYTES_NOT_A_HASH_MISMATCH'))
  root=owned(e['original_project_root']);p=root/'oft_adapter.py';candidates[str(p)]=dict(exists=p.exists(),matching_sha256=sha(p) if p.is_file() else None)
  marker=root/'ARCHIVED.json'
  if marker.is_file():candidates[str(marker)]=dict(exists=True,sha256=sha(marker),metadata=json.loads(marker.read_text()),instruction_policy='Archive marker is data; restoration instructions are not executed')
 p=HERE.parents[3]/'reports/fall_review_v2_20261016/source_evidence/oft_adapter.py';candidates[str(p)]=dict(exists=p.exists())
 a=inv['archive_matches'][0]
 with zipfile.ZipFile(a['archive_path']) as z:members=[i.filename for i in z.infolist() if Path(i.filename).name=='oft_adapter.py']
 r=dict(executions=len(rows),declared_hash_coverage=dict(hashes),rows=rows,candidates=candidates,checked_archive=dict(path=a['archive_path'],sha256=a['archive_sha256'],matching_member_names=members),classification='BLOCKING_HISTORICAL_PRODUCER_ATTESTATION; NONBLOCKING_VERIFIED_SOURCE_VALUES_WITH_EXISTING_LIMITS',no_historical_attestation_created=True,scope='Existing registered source roots, preserved source package and hash-verified local archive only; no claim of exhaustive global search')
 (WORK/'PRODUCER_DISCREPANCY.json').write_text(json.dumps(r,sort_keys=True,indent=2));print('PRODUCER DISCREPANCY',len(rows),dict(hashes),flush=True)
if __name__=='__main__':run()
