"""Simulate a missing final transaction in the independent scratch rebuild only."""
import json,sqlite3
from .channels import WORK
from .build import populate
from .validate import save

def run():
 p=WORK/'independent.sqlite';expected=json.loads((WORK/'INDEPENDENT_BUILD.json').read_text())['logical_digest']
 with sqlite3.connect(p) as c:
  execution=c.execute('select execution from rag_channel_jobs order by execution desc limit 1').fetchone()[0]
  ids=[r[0] for r in c.execute('select id from rag_channel_records where execution=?',(execution,))];assert len(ids)==6
  for id in ids:c.execute('delete from rag_channel_fts where id=?',(id,))
  c.execute('delete from rag_channel_records where execution=?',(execution,));c.execute('delete from rag_channel_jobs where execution=?',(execution,))
 result=populate(p);assert result['inserted']==6 and result['skipped']==431 and result['logical_digest']==expected
 save('PARTIAL_RESUME.json',dict(passed=True,simulated_missing_transaction_execution=execution,restored=result,primary_database_untouched=True))
 print('Partial resume equivalent',result['logical_digest'],flush=True)
if __name__=='__main__':run()
