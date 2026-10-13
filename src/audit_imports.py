"""Inventory annotation keys in the original results without modifying them."""
import argparse,json,re,hashlib,time
from pathlib import Path
FIELDS={'requirement_id','case_id','claim_id','event_id','objection_id','safety_requirements','safety_cases','safety_claims','safety_events','objections'}
def scan(v,path=''):
 if isinstance(v,dict):
  for k,x in v.items():
   if k in FIELDS:yield {'pointer':path+'/'+k,'key':k,'value_type':type(x).__name__,'nonempty':bool(x)}
   yield from scan(x,path+'/'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):yield from scan(x,path+'/'+str(i))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('results',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();files=[];hits=[];errors=[];names=[];counts={};started=time.time()
 for p in sorted(a.results.rglob('*')):
  if not p.is_file():continue
  ext=p.suffix.lower();counts[ext]=counts.get(ext,0)+1
  if re.search(r'(requirement|safety.?case|objection|claim|event)',p.name,re.I):names.append(str(p.relative_to(a.results)))
  if ext!='.json':continue
  try:
   data=p.read_bytes();d=json.loads(data);found=list(scan(d));files.append({'path':str(p.relative_to(a.results)),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
   if found:hits.append({'path':str(p.relative_to(a.results)),'matches':found})
  except Exception as e:errors.append({'path':str(p),'error':str(e)})
 report={'source_results':str(a.results.resolve()),'file_counts':counts,'json_files_scanned':len(files),'structured_annotation_matches':hits,'candidate_filenames':names,'read_errors':errors,'json_file_inventory':files,'elapsed_s':time.time()-started,'interpretation':'Structured safety annotations are identified by explicit keys, not inferred from success/failure. Ordinary transitions and contact measurements reside in HDF5; their presence is a separate evidence inventory.'}
 a.output.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='json_file_inventory'},indent=2))
if __name__=='__main__':main()
