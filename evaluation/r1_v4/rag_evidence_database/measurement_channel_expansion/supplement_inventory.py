"""Add full JSON leaf/container and HDF5 attribute coverage to the census CSVs."""
import json,csv,collections
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .channels import WORK,HERE

def run():
 marker=WORK/'INVENTORY_SUPPLEMENT.json'
 if marker.exists():raise ValueError('supplement already generated; use new report directory')
 rows=[json.loads(p.read_text()) for p in sorted((WORK/'inventory').glob('*.json'))];assert len(rows)==432
 agg={};matrix=[];sources={}
 for r in rows:
  for k,v in r['attributes'].items():matrix.append([r['execution_id'],r['task_id'],r['variant_id'],'hdf5:'+k,r['source_path'],r['source_sha256'],v['example'],v['count'],len(r['frames']) if '/frames/' in k else '',json.dumps(v['types']),'saved_in_source_not_independently_searchable'])
  for key,v in r['json_fields'].items():
   path,selector=key.split('#',1);canonical=Path(path).name+'#'+selector
   if path not in sources:sources[path]=sha(path)
   a=agg.setdefault(canonical,dict(paths=set(),tasks=set(),variants=set(),executions=set(),types=collections.Counter()));a['paths'].add(path);a['tasks'].add(r['task_id']);a['variants'].add(r['variant_id']);a['executions'].add(r['execution_id']);a['types'][v['type']]+=1
   matrix.append([r['execution_id'],r['task_id'],r['variant_id'],'json:'+canonical,path,sources[path],selector,1,'',json.dumps(v,sort_keys=True),'saved_in_metadata_document_not_independently_searchable'])
 with (HERE/'CHANNEL_INVENTORY.csv').open('a') as f:
  w=csv.writer(f)
  for k,a in sorted(agg.items()):w.writerow(['json:'+k,'JSON',k,sorted(a['paths'])[0]+'#'+k.split('#',1)[1],json.dumps(a['types'],sort_keys=True),'artifact snapshot/event metadata; no uniform frequency','unverified/not_applicable','unverified/not_applicable','exact metadata key only',';'.join(sorted(a['tasks'])),';'.join(sorted(a['variants'])),len(a['executions']),432-len(a['executions']),len(a['executions']),'saved_in_metadata_document_not_independently_searchable','requires key-specific contract before physical use','exact source hash, key and documented producer semantics','A key name or numeric value alone does not establish units, timebase or frame'])
 with (HERE/'CHANNEL_COVERAGE_MATRIX.csv').open('a') as f:csv.writer(f).writerows(matrix)
 report=dict(json_channel_ids=len(agg),supplemental_coverage_rows=len(matrix),json_sources_hashed=len(sources),sources=sources,local_video_files=sum(f['suffix'] in ('.mp4','.avi') for r in rows for f in r['files']),local_resource_csv_files=sum(Path(f['path']).name=='resources.csv' for r in rows for f in r['files']),scope='Only 432 admitted execution directories. HDF5 full tree and JSON keys inspected; unavailable video/resource payloads are not claimed absent in original archives.')
 with marker.open('x') as f:json.dump(report,f,sort_keys=True,indent=2)
 print({k:v for k,v in report.items() if k!='sources'},flush=True)
if __name__=='__main__':run()
