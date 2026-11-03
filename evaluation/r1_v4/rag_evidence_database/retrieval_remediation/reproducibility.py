"""Fresh process replay and independently rebuilt catalogue, without source duplication."""
import json,sqlite3
from pathlib import Path
from .config import *
from .run_eval import run
from .build import populate
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
def main():
 frozen=json.loads((HERE/'FROZEN_IMPLEMENTATION.json').read_text())
 for n,h in frozen['files'].items():assert sha(HERE/n)==h,n
 a=run(HERE/'FROZEN_HOLDOUT_DATASET.jsonl','holdout_guard_v2');assert a['resumed']==1296
 b=run(HERE/'FROZEN_HOLDOUT_DATASET.jsonl','holdout_guard_independent');assert a['canonical_digest']==b['canonical_digest'],(a,b)
 p=run(HERE/'FROZEN_HOLDOUT_DATASET.jsonl','holdout_guard_partial',limit=37);assert p['mode_instances']==37
 c=run(HERE/'FROZEN_HOLDOUT_DATASET.jsonl','holdout_guard_partial');assert c['resumed']==37 and a['canonical_digest']==c['canonical_digest']
 original=json.loads((WORK/'BUILD.json').read_text());fresh=populate(WORK/'catalogue_guard_independent.sqlite');full=populate(WORK/'catalogue.sqlite');assert fresh['logical_digest']==original['logical_digest']==full['logical_digest'] and full['resumed']==432
 partial=WORK/'catalogue_guard_partial.sqlite'
 if not partial.exists():
  src=sqlite3.connect((WORK/'catalogue.sqlite').as_uri()+'?mode=ro',uri=True);dst=sqlite3.connect(partial)
  for sql, in src.execute("select sql from sqlite_master where type='table' order by name"):dst.execute(sql)
  for t in ('meta','catalogue','jobs'):
   rows=src.execute('select * from '+t+' order by 1'+(' limit 37' if t!='meta' else '')).fetchall();dst.executemany('insert into '+t+' values('+','.join('?' for _ in rows[0])+')',rows)
  dst.commit();dst.close();src.close()
 pr=populate(partial);assert pr['resumed']==37 and pr['logical_digest']==original['logical_digest']
 result=dict(passed=True,full_resume=a,independent_replay=b,partial_replay=c,sidecar_fresh=fresh,sidecar_full_resume=full,sidecar_partial_resume=pr,automated_not_independent_human_replication=True);(WORK/'REPRODUCIBILITY_RESULTS.json').write_text(json.dumps(result,sort_keys=True,indent=2));print('REPRODUCIBILITY PASS',flush=True)
if __name__=='__main__':main()
