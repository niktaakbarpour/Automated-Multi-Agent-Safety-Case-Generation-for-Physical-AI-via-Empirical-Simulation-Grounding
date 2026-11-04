"""Bounded development-source restoration with explicit maps and no original fallback."""
import json,shutil
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.restoration import Capture
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.store import BundleStore
from .config import *
from .api import StructuredRetriever
from .fixtures import request,first

def run():
 engine=StructuredRetriever(verification_mode='verified_session');c=first(engine);q=request(c);capture=Capture(engine.store.verifier);engine.store.verifier=capture;baseline=engine.retrieve(q);assert baseline['completeness_status']=='COMPLETE WITHIN VERIFIED CONTRACT';engine.close();root=WORK/'bounded_restore';root.mkdir(exist_ok=True);(root/'objects').mkdir(exist_ok=True);entries={}
 for p,h in sorted(capture.seen.items()):
  target=root/'objects'/h
  if not target.exists():
   with capture.base.access(p,h,'strict') as (fd,a),target.open('xb') as out:shutil.copyfileobj(fd,out)
  assert sha(target)==h;entries[p+'#'+h]=dict(relative_path='objects/'+h,executions=[c['execution_id']],variants=[c['variant_id']])
 manifest=root/'RESTORE.json';manifest.write_text(json.dumps(dict(database_sha256=DATABASE_SHA,entries=entries),sort_keys=True,indent=2));store=BundleStore(restore=manifest,restore_sha256=sha(manifest));restored=StructuredRetriever(store=store,verification_mode='verified_session')
 try:
  result=restored.retrieve(q);assert result['completeness_status']=='COMPLETE WITHIN VERIFIED CONTRACT';assert [i['citation_id'] for g in baseline['groups'] for i in g['items']]==[i['citation_id'] for g in result['groups'] for i in g['items']]
 finally:restored.close()
 incomplete=root/'INCOMPLETE.json';raw=c['source_path']+'#'+c['source_sha256'];assert raw in entries;incomplete.write_text(json.dumps(dict(database_sha256=DATABASE_SHA,entries={k:v for k,v in entries.items() if k!=raw}),sort_keys=True));engine=StructuredRetriever(store=BundleStore(restore=incomplete,restore_sha256=sha(incomplete)),verification_mode='verified_session')
 try:bad=engine.retrieve(q);assert bad['completeness_status']=='UNAVAILABLE' and not any(g['items'] for g in bad['groups'])
 finally:engine.close()
 result=dict(passed=True,executions=1,variants=1,mappings=len(entries),unique_contents=len({v['relative_path'] for v in entries.values()}),bytes=sum(p.stat().st_size for p in (root/'objects').iterdir()),manifest_path=str(manifest),manifest_sha256=sha(manifest),citation_identity_preserved=True,incomplete_mapping_rejected_without_fallback=True,prerequisites='Separately pinned original database and catalogue; these were not copied',historical_environment_reproduced=False);(WORK/'RESTORATION_RESULTS.json').write_text(json.dumps(result,sort_keys=True,indent=2));print(result,flush=True)
if __name__=='__main__':run()
