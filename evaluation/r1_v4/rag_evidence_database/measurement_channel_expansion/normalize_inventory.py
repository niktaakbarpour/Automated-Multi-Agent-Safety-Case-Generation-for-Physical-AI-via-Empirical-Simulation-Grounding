"""Normalize repeated source/variant/key strings without losing inventory detail."""
import csv,json
from pathlib import Path
from .channels import WORK,HERE
from evaluation.r1_v4.evidence_registry_gsn.builder import sha

def run():
 original=HERE/'CHANNEL_COVERAGE_MATRIX.csv';archived=WORK/'FULL_CHANNEL_COVERAGE_MATRIX.csv'
 if archived.exists():raise ValueError('already normalized')
 original.rename(archived)
 inventory=HERE/'CHANNEL_INVENTORY.csv';old=WORK/'FULL_CHANNEL_INVENTORY.csv';inventory.rename(old)
 with old.open() as f:rows=list(csv.DictReader(f))
 channelkeys={r['canonical_channel_id']:f'C{i:04d}' for i,r in enumerate(rows)}
 assert len(channelkeys)==len(rows)
 with inventory.open('x') as f:
  w=csv.DictWriter(f,fieldnames=['channel_key']+list(rows[0]));w.writeheader();w.writerows(dict(channel_key=channelkeys[r['canonical_channel_id']],**r) for r in rows)
 executions={};sources={};profiles={}
 with archived.open() as source,original.open('x') as dest:
  reader=csv.DictReader(source);w=csv.writer(dest);w.writerow(['execution_key','channel_key','source_key','recorded_occurrences','saved_frame_denominator','value_profile_key'])
  for r in reader:
   e=r['execution_id'];executions.setdefault(e,'E'+str(len(executions)).zfill(3));source=(e,r['task_id'],r['variant_id'],r['source_path'],r['source_sha256']);sources.setdefault(source,'S'+str(len(sources)).zfill(4));profile=(r['dtype_shape_counts'],r['phase5f_representation']);profiles.setdefault(profile,'P'+str(len(profiles)).zfill(3))
   w.writerow([executions[e],channelkeys[r['channel_id']],sources[source],r['recorded_occurrences'],r['saved_frames_denominator'],profiles[profile]])
 with (HERE/'EXECUTION_SOURCE_BINDINGS.csv').open('x') as f:
  w=csv.writer(f);w.writerow(['source_key','execution_key','execution_id','task_id','variant_id','source_path','source_sha256'])
  for (e,t,v,p,h),key in sorted(sources.items(),key=lambda x:x[1]):w.writerow([key,executions[e],e,t,v,p,h])
 with (HERE/'VALUE_PROFILES.json').open('x') as f:json.dump({key:dict(dtype_shape_counts=shape,phase5f_representation=status) for (shape,status),key in profiles.items()},f,sort_keys=True,indent=2)
 report=dict(matrix_rows=sum(1 for _ in archived.open())-1,normalized_matrix_sha256=sha(original),full_external_matrix_path=str(archived),full_external_matrix_sha256=sha(archived),channel_keys=len(channelkeys),source_bindings=len(sources),execution_keys=len(executions),value_profiles=len(profiles),join='CHANNEL_COVERAGE_MATRIX channel_key -> CHANNEL_INVENTORY; source_key -> EXECUTION_SOURCE_BINDINGS; value_profile_key -> VALUE_PROFILES.json. Exact paths/task/variant/hash retained once per source. Full original expanded matrix retained externally.')
 with (WORK/'NORMALIZED_INVENTORY.json').open('x') as f:json.dump(report,f,indent=2)
 print(report,flush=True)
if __name__=='__main__':run()
