"""Supplementary isolated integrity probes; no production source files are modified."""
import json,tempfile,shutil
from pathlib import Path
from evaluation.r1_v4.rag_evidence_database.source_reproducibility.store import ProvenanceStore
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier,SourceError
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion.retrieval import guard
from .config import *
def run():
 db=ProvenanceStore(DATABASE,expected_sha256=DATABASE_SHA);case=json.loads((HERE/'EVALUATION_DATASET.jsonl').read_text().splitlines()[0]);b=db.binding(case['execution_id']);rows=[]
 with tempfile.TemporaryDirectory(dir=WORK,prefix='integrity-component-') as tmp:
  root=Path(tmp);p=root/'model.xml';shutil.copyfile(b['xml_path'],p);alias=root/'alias.xml';alias.symlink_to(p);scoped=dict(b,xml_path=str(alias))
  try:guard(db,scoped,{});legacy_result='accepted_hash_matching_symlink'
  except Exception as e:legacy_result='rejected:'+type(e).__name__+':'+str(e)
  try:SourceVerifier().verify(str(alias),b['xml_sha256'],'strict');strict_result='accepted'
  except SourceError:strict_result='rejected_symlink'
  rows.append(dict(probe='XML source primitive differential',legacy=legacy_result,strict_phase5i=strict_result,scope='Component-level verified-binding fixture, not an end-to-end compromised-release exploit',source_bytes_identical=True))
  actual=root/'bytes';actual.write_bytes(b'original');import hashlib,os
  h=hashlib.sha256(b'original').hexdigest();v=SourceVerifier();v.verify(str(actual),h,'verified_session');stat=actual.stat();actual.write_bytes(b'modified');os.utime(actual,ns=(stat.st_atime_ns,stat.st_mtime_ns))
  try:v.verify(str(actual),h,'verified_session');stale='accepted_modified'
  except SourceError:stale='rejected_modified'
  rows.append(dict(probe='Stale cache with preserved mtime',result=stale));actual.write_bytes(b'original');recovered=v.verify(str(actual),h,'verified_session');rows.append(dict(probe='Recovered byte-identical source',result=recovered['status']))
 db.close();(WORK/'ADVERSARIAL_COMPONENT_RESULTS.json').write_text(json.dumps(dict(rows=rows,production_artifacts_modified=False,source_text_instruction_policy='Source bytes are never eval/exec input; instruction-note mutation is tested as a hash mismatch, not as an LLM prompt-injection benchmark'),sort_keys=True,indent=2));print(rows,flush=True)
if __name__=='__main__':run()
