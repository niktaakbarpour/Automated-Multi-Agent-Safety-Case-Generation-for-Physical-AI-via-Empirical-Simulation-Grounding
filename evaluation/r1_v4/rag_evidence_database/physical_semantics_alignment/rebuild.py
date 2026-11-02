"""Independent copy, full resume and missing-transaction scratch recovery."""
import json,sqlite3
from .config import WORK
from .build import populate
from .audit import save
from .validate import preservation

def run():
 first=json.loads((WORK/'BUILD.json').read_text());r=populate(WORK/'expanded.sqlite');assert r['inserted']==0 and r['skipped']==432 and r['logical_digest']==first['logical_digest'];save(WORK/'RESUME.json',r)
 p=WORK/'independent.sqlite';second=populate(p);assert second['logical_digest']==first['logical_digest'];save(WORK/'INDEPENDENT_BUILD.json',second)
 with sqlite3.connect(p) as c:
  e=c.execute('select execution from h_jobs order by execution desc limit 1').fetchone()[0];c.execute('delete from h_semantics where execution=?',(e,));c.execute('delete from h_execution where execution=?',(e,));c.execute('delete from h_jobs where execution=?',(e,))
 partial=populate(p);assert partial['inserted']==6 and partial['skipped']==431 and partial['logical_digest']==first['logical_digest'];save(WORK/'PARTIAL_RESUME.json',partial)
 save(WORK/'REBUILD_VALIDATION.json',dict(passed=True,logical_digest=first['logical_digest'],full_resume_inserted=0,full_resume_skipped=432,partial_resume_inserted=6,partial_resume_skipped=431,preservation=preservation(p)))
 print('REBUILD COMPLETE',flush=True)
if __name__=='__main__':run()
