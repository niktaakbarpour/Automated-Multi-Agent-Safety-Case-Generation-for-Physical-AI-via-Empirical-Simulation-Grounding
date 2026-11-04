"""Bounded development restoration; original recordings never moved or changed."""
import json,contextlib,shutil
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import *
from .store import BundleStore,canonical_path
from .bundle import Retriever,BundleRequest
class Capture:
 def __init__(self,base):self.base=base;self.seen={}
 @contextlib.contextmanager
 def access(self,p,h,mode='strict'):
  with self.base.access(p,h,mode) as value:self.seen[canonical_path(p)]=h;yield value
 def verify(self,p,h,mode='strict'):
  with self.access(p,h,mode) as (f,a):return a
 def __getattr__(self,k):return getattr(self.base,k)
def run():
 build=json.loads((WORK/'BUILD.json').read_text());r=Retriever(WORK/'catalogue.sqlite',build['sha256']);e=json.loads((WORK/'DEVELOPMENT_SELECTION.json').read_text())[0]['execution_id'];c=json.loads(r.catalogue.execute('select body from catalogue where execution=?',(e,)).fetchone()[0]);o=sorted(c['objects'])[0];queries=[f'Collect finger positions, recorded time labels and source hash at frame 20.',f'Which native geometry identifies {o}?','Identify main_table body and geometry.'];capture=Capture(r.store.verifier);r.store.verifier=capture
 for text in queries:assert r.retrieve(BundleRequest(text,e,verification_mode='verified_session'))['completeness_status']=='COMPLETE WITHIN VERIFIED CONTRACT'
 root=WORK/'bounded_restore';root.mkdir(exist_ok=True);(root/'objects').mkdir(exist_ok=True);entries={};bytes_total=0
 for path,h in sorted(capture.seen.items()):
  p=root/'objects'/h
  if not p.exists():
   with capture.base.access(path,h,'strict') as (f,a),p.open('xb') as out:shutil.copyfileobj(f,out)
  assert sha(p)==h;bytes_total+=p.stat().st_size;entries[path+'#'+h]=dict(relative_path='objects/'+h,executions=[e],variants=[c['variant_id']])
 manifest=root/'RESTORE.json';manifest.write_text(json.dumps(dict(version='1',database_sha256=DATABASE_SHA,entries=entries),sort_keys=True,indent=2));store=BundleStore(restore=manifest,restore_sha256=sha(manifest));restored=Retriever(WORK/'catalogue.sqlite',build['sha256'],store=store);outcomes=[]
 try:
  for text in queries:
   out=restored.retrieve(BundleRequest(text,e,verification_mode='verified_session'));assert out['completeness_status']=='COMPLETE WITHIN VERIFIED CONTRACT';outcomes.append(dict(query=text,status=out['completeness_status']))
 finally:restored.close();r.close()
 result=dict(passed=True,executions=1,variants=1,mapped_artifacts=len(entries),unique_contents=len({v['relative_path'] for v in entries.values()}),mapped_bytes=bytes_total,manifest_path=str(manifest),manifest_sha256=sha(manifest),outcomes=outcomes,database_copied=False,required_prerequisites=['separately pinned original database','pinned K catalogue'],historical_binary_attestation=False);(WORK/'RESTORATION_RESULTS.json').write_text(json.dumps(result,sort_keys=True,indent=2));print(result,flush=True)
if __name__=='__main__':run()
