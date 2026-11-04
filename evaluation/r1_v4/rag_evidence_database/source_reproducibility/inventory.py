"""Historical declarations and current byte matches are distinct evidence, not runtime attestations."""
import json,sqlite3,zipfile,hashlib,collections,os
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha,REPO
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier,SourceError
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import owned
from .config import WORK,BASE

def save(name,value):
 with (WORK/name).open('x') as f:json.dump(value,f,sort_keys=True,indent=2)

def run():
 c=sqlite3.connect(BASE.as_uri()+'?mode=ro',uri=True);rows=[];verifier=SourceVerifier();archive=Path('/disk/1/data/niktakbr/hestia-archives/2026-10-12-unused/openvla-oft-libero-gpu0-queue.zip');am=archive.with_suffix('.manifest.json');arc=json.loads(am.read_text());assert sha(archive)==arc['zip_sha256'];out=WORK/'archival_sources';out.mkdir();matches={};archival=[]
 first=c.execute("select json_extract(body,'$.source_path') from evidence where json_extract(body,'$.measurement_type')='execution_metadata' order by execution_id limit 1").fetchone()[0];declared=json.load(open(first))['source_files_sha256']
 with zipfile.ZipFile(archive) as z:
  names=set(z.namelist())
  for relative,expected in sorted(declared.items()):
   member='openvla-oft-libero-gpu0-queue/'+relative
   if member not in names:continue
   info=z.getinfo(member)
   if info.file_size>10*1024**2 or ((info.external_attr>>16)&0o170000)==0o120000:continue
   data=z.read(member);actual=hashlib.sha256(data).hexdigest()
   if actual==expected:
    p=out/(actual+Path(relative).suffix)
    if not p.exists():p.write_bytes(data)
    matches[(relative,expected)]=str(p);archival.append(dict(recorded_relative_path=relative,sha256=expected,current_path=str(p),archive_path=str(archive),archive_sha256=arc['zip_sha256'],archive_manifest_path=str(am),archive_manifest_sha256=sha(am),member=member,classification='RETROSPECTIVE_MATCH_TO_RECORDED_DIGEST',historical_execution_attested=False,date_basis='Archive directory/date and ZIP times are self-reported, not trusted timestamps'))
 historical=collections.Counter();available=collections.Counter()
 for e,body in c.execute('select execution,body from rag_execution_env order by execution'):
  binding=json.loads(body);path=c.execute("select json_extract(body,'$.source_path') from evidence where execution_id=? and json_extract(body,'$.measurement_type')='execution_metadata'",(e,)).fetchone()[0];directory=Path(path).parent;meta=json.load(open(path));integrity=directory/'integrity_manifest.json';completion=directory/'completion.json';im=json.load(integrity.open());co=json.load(completion.open());assert sha(integrity)==co['integrity_manifest_sha256'];assert meta['global_episode_id']==e and sha(path)==im['files']['run_metadata.json']['sha256']
  producer=[]
  for relative,expected in sorted(meta['source_files_sha256'].items()):
   candidates=[REPO/'reports/fall_review_v2_20261016/source_evidence'/relative]
   actual=None
   for p in candidates:
    try:
     with verifier.access(str(p),expected,'verified_session'):actual=str(p)
     break
    except (SourceError,OSError):pass
   if actual is None:actual=matches.get((relative,expected))
   producer.append(dict(relative_path=relative,recorded_sha256=expected,available_matching_path=actual,classification='RECONSTRUCTED_ASSOCIATION' if actual else 'HISTORICAL_RECORD',historical_attestation='RECORDED_DECLARATION_ONLY',current_integrity='VERIFIED_BYTES_MATCH_DECLARATION' if actual else 'UNAVAILABLE',executed_bytes_attested=False));historical[relative]+=1
   if actual:available[relative]+=1
  evaluator=[]
  for original,expected in meta['evaluator']['implementation_files_sha256'].items():
   p=str(owned(original));verifier.verify(p,expected,'verified_session');evaluator.append(dict(recorded_path=original,current_owned_path=p,recorded_sha256=expected,classification='RECONSTRUCTED_ASSOCIATION',integrity='VERIFIED_BYTES_MATCH_DECLARATION',historical_runtime_attested=False))
  rows.append(dict(execution_id=e,task_id=binding['task_id'],variant_id=binding['variant_id'],metadata_path=path,metadata_sha256=sha(path),integrity_manifest_path=str(integrity),integrity_manifest_sha256=sha(integrity),completion_path=str(completion),completion_sha256=sha(completion),recorded_started_at=meta['started_at'],recorded_finished_at=co.get('finished_at'),date_attestation='SELF_REPORTED_HOST_CLOCK; no independent timestamp authority',producer_files=producer,evaluator_files=evaluator,source_commit_declaration=meta['source_commit'],checkout_cleanliness='UNATTESTED',dependency_version_declarations=meta['versions'],python_declaration=meta['python'],platform_declaration=meta['platform'],hardware_backend_declarations={k:meta.get(k) for k in ('gpu','gpu_driver','physical_gpu_index','model_family','checkpoint_revision')},recording_configuration={k:meta.get(k) for k in ('recorder_schema_version','dataset_schema_version','control_frequency_hz','settling_steps','observation_size','seed','inference_configuration','resolved_policy_configuration','recording_notes')},checkpoint_hash_declarations=meta.get('checkpoint_weight_sha256',{}),original_project_root=str(Path(meta['job_plan_file']).parent),container_image_digest=None,historical_binary_attestation='UNATTESTED',original_manifest_inventory={n:dict(sha256=v['sha256'],bytes=v['bytes'],local_available=(directory/n).is_file()) for n,v in im['files'].items()}))
 save('PRODUCER_EVIDENCE.json',dict(executions=len(rows),variants=len({r['variant_id'] for r in rows}),rows=rows,archive_matches=archival,recorded_file_coverage=dict(historical),available_hash_match_coverage=dict(available),historical_binary_attested_executions=0,qualification='Recorded assertions and currently matching bytes are separate. No newly computed hash, version string or commit proves historical runtime/cleanliness.'))
 print('PRODUCER INVENTORY COMPLETE',len(rows),'archival matches',len(archival),flush=True)
if __name__=='__main__':run()
