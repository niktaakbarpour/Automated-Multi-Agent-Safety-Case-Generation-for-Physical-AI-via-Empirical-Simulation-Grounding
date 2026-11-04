"""Final source/seal preservation, old semantic compatibility and new sidecar checks."""
import os,time
from pathlib import Path
from collections import defaultdict
from evaluation.r1_v4.provenance import load,write_new,canonical,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha,REPO
from evaluation.r1_v4.integrity import verify
from .plan import HERE,WORK,BASE,BASE_SHA

def source_rows():
 rows=load(HERE.parent/'multitask_expansion/RESTORED_SOURCES.json')['files']+load(HERE.parent/'corpus_expansion/task_profile/RESTORED_SOURCES.json')['files']+load(HERE.parent/'expansion/VALIDATED_SOURCE_PROFILE.json')['source_bindings'];rows += [{'restored_path':r['path'],'sha256':r['sha256']} for r in load(HERE.parents[1]/'evidence_review_readiness/SOURCE_BINDINGS.json')['original_files']]
 for r in load(HERE/'COHORT.json')['files']:
  expected=r['expected_sha256'] or load(Path(r['restored_path']).parent/'episode_001/run_metadata.json')['initial_states_sha256'];rows.append({'restored_path':r['restored_path'],'sha256':expected})
 return rows

def run():
 assert sha(BASE)==BASE_SHA;assert load(WORK/'REGRESSION_RESULTS.json')['passed'];assert load(WORK/'REBUILD_VALIDATION.json')['passed'];assert load(WORK/'NEGATIVE_RETRIEVAL.json')['passed'];assert load(WORK/'SEMANTIC_EVALUATION.json')['passed']
 source=source_rows()
 for r in source:assert sha(r['restored_path'])==(r.get('actual_sha256') or r['sha256'])
 files=load(HERE/'EXTERNAL_PROFILE_ARTIFACTS.json')['files']
 for r in files:assert Path(r['path']).stat().st_size==r['bytes'] and sha(r['path'])==r['sha256']
 old=load(HERE.parent/'multitask_expansion/ARTIFACT_SHA256.json')['files'];amendments=[]
 import subprocess
 for path,expected in old.items():
  current=sha(REPO/path)
  if current!=expected:
   assert path=='evaluation/r1_v4/libero_measurement_reader/reader.py';prior=subprocess.check_output(['git','show','114f1f6540a6ba182606a2a921af131ad6b0f7d3:'+path],cwd=REPO)
   from evaluation.r1_v4.provenance import bytes_digest
   assert bytes_digest(prior)==expected;amendments.append({'path':path,'baseline_sha256':expected,'phase5f_sha256':current,'reason':'Add only the closed variant-v1 reader dispatch; all Phase5E file contents retained in baseline commit.'})
 write_new(WORK/'FROZEN_FINAL.json',verify())
 sem=load(WORK/'SEMANTIC_EVALUATION.json');by=defaultdict(list)
 for row in sem['results']:by[row['variant_id']].append(row)
 import statistics
 metrics={v:{m:{'instances':sum(r['method']==m for r in rows),'precision_at_1':statistics.mean(r['precision_at_1'] for r in rows if r['method']==m),'recall_at_20':statistics.mean(r['recall_at_20'] for r in rows if r['method']==m),'MRR':statistics.mean(r['reciprocal_rank'] for r in rows if r['method']==m)} for m in ('fts5','semantic')} for v,rows in by.items()};write_new(WORK/'SEMANTIC_VARIANT_METRICS.json',metrics)
 report={'passed':True,'original_source_paths_freshly_hashed':len(source),'external_profile_artifacts_hashed':len(files),'phase5e_baseline_sha256':BASE_SHA,'phase5e_files_unchanged_except_versioned_reader_dispatch':True,'intentional_code_amendments':amendments,'database_path':str(WORK/'expanded.sqlite'),'database_sha256':sha(WORK/'expanded.sqlite'),'database_bytes':(WORK/'expanded.sqlite').stat().st_size,'semantic_sha256':sha(WORK/'semantic.sqlite'),'semantic_bytes':(WORK/'semantic.sqlite').stat().st_size,'disk1_available_bytes':os.statvfs('/disk/1').f_bavail*os.statvfs('/disk/1').f_frsize,'empirical_admission_enabled':False,'simulations_run':0,'push_or_merge':False};write_new(WORK/'FINAL_VALIDATION.json',report);print(report,flush=True)
if __name__=='__main__':run()
