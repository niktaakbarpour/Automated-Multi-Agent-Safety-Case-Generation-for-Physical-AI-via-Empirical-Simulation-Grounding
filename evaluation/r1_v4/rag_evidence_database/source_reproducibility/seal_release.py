"""Create a current-byte release inventory, without claiming historical attestation."""
import json,sqlite3
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import owned
from .config import HERE,WORK,BASE,BASE_SHA,BASE_COMMIT,VERSION

def generate():
 rows={}
 def add(p,h=None,role='metadata',basis='release-generated current artifact'):
  p=Path(p);key=str(p);row=dict(path=key,sha256=h or sha(p),bytes=p.stat().st_size,required_for=role,basis=basis)
  if key in rows:
   if rows[key]['sha256']!=row['sha256']:raise ValueError('conflicting source identity '+key)
   priority={'metadata':0,'sources':1,'provenance':2}
   if priority[rows[key]['required_for']]<=priority[role]:return
  rows[key]=row
 for p in sorted(HERE.rglob('*')):
  if p.is_file() and p.name not in ('ARTIFACT_MANIFEST.json','ARTIFACT_MANIFEST.sha256','RELEASE_VERIFICATION_RESULT.json') and '__pycache__' not in p.parts:add(p)
 for p in sorted(WORK.rglob('*')):
  if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts:add(p)
 add(BASE,BASE_SHA,basis='independently verified Phase5H baseline')
 for a in json.loads((WORK/'PRODUCER_EVIDENCE.json').read_text())['archive_matches']:
  add(a['archive_path'],a['archive_sha256'],'provenance','retrospective source restoration archive; no historical runtime assertion')
  add(a['archive_manifest_path'],a['archive_manifest_sha256'],'provenance','archive integrity declaration, not timestamp authority')
 prior=HERE.parent/'physical_semantics_alignment'/'ARTIFACT_MANIFEST.json'
 add(prior,basis='pinned prior release manifest')
 def inherited(value):
  if isinstance(value,dict):
   if value.get('path') and value.get('sha256'):add(value['path'],value['sha256'],basis='inherited validated release integrity record')
   for x in value.values():inherited(x)
  elif isinstance(value,list):
   for x in value:inherited(x)
 inherited(json.loads(prior.read_text()))
 frozen=json.loads((WORK/'REGRESSION.json').read_text())['frozen']
 for p,h in frozen.get('live_frozen_hashes',{}).items():add(p,h,basis='frozen evaluation artifact/seal identity')
 c=sqlite3.connect('file:'+str(WORK/'expanded.sqlite')+'?mode=ro',uri=True)
 deps={r[0] for r in c.execute("select target from i_edges where relation='current_artifact'")}
 for id,p,h in c.execute('select id,path,sha256 from i_artifacts'):
  if p.startswith('/local/'):p=str(owned(p))
  add(p,h,'provenance' if id in deps else 'sources','preserved source or retrospective dependency binding; not historical execution attestation')
 result=dict(version=VERSION,branch='feat/rag-evidence-database-release-provenance',baseline_commit=BASE_COMMIT,baseline_database_sha256=BASE_SHA,classification='RETROSPECTIVE_RELEASE_INTEGRITY',historical_execution_attested=False,signature_or_timestamp_authority=None,self_exclusions={'ARTIFACT_MANIFEST.json':'manifest cannot hash itself','ARTIFACT_MANIFEST.sha256':'external checksum of manifest','RELEASE_VERIFICATION_RESULT.json':'records this manifest hash; verification is independently repeatable and Git commit anchors this result'},artifacts=sorted(rows.values(),key=lambda r:r['path']))
 p=HERE/'ARTIFACT_MANIFEST.json';p.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');(HERE/'ARTIFACT_MANIFEST.sha256').write_text(sha(p)+'  ARTIFACT_MANIFEST.json\n');print('MANIFEST',len(rows),sha(p),flush=True);return sha(p)
if __name__=='__main__':generate()
