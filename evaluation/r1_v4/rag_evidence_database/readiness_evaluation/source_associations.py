"""Freeze existing index source bindings separately from independent factual answers."""
import json,sqlite3
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import *
def run():
 assert sha(DATABASE)==DATABASE_SHA;c=sqlite3.connect(DATABASE.as_uri()+'?mode=ro',uri=True);cases=[json.loads(x) for x in (HERE/'EVALUATION_DATASET.jsonl').read_text().splitlines()];ids={i for q in cases for i in q['expected_source_ids']};executions={q['execution_id'] for q in cases};rows={}
 for e in executions:
  for rid,body in c.execute('select id,body from rag_channel_records where execution=?',(e,)):
   r=json.loads(body);rows[rid]={k:r[k] for k in ('execution_id','task_id','variant_id','source_path','source_sha256')}
 for rid in sorted(ids-set(rows)):
  r=json.loads(c.execute('select body from evidence where id=?',(rid,)).fetchone()[0]);rows[rid]={k:r[k] for k in ('execution_id','task_id','source_path','source_sha256')}
 artifact_hashes={r['source_path']:r['source_sha256'] for r in rows.values()}
 for p,h in artifact_hashes.items():assert sha(__import__('pathlib').Path(p))==h,p
 with (HERE/'SOURCE_ASSOCIATIONS.json').open('x') as f:json.dump(dict(database_sha256=DATABASE_SHA,method='Source link and ID audit against frozen registry, not a factual answer oracle. Numeric/geometry facts remain independent original-source references.',rows=rows,verified_artifacts=artifact_hashes),f,sort_keys=True,indent=2)
 print('SOURCE ASSOCIATIONS',len(rows),len(artifact_hashes),flush=True)
if __name__=='__main__':run()
