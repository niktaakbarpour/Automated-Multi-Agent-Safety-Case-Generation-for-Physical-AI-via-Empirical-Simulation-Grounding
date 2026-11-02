"""Historical metadata discovery, never a replacement for original measurements."""
from evaluation.r1_v4.provenance import load,canonical,strict_loads
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO,sha

def populate_catalog(store,manifest):
 if store.db.execute("SELECT count(*) FROM rag_jobs WHERE status='complete'").fetchone()[0]!=4:raise ValueError('validate four development jobs before catalog expansion')
 if not store.check()['passed']:raise ValueError('development integrity must pass before expansion')
 source=REPO/'data/runs.json';source_hash=sha(source)
 runs={r['run_id']:r for r in load(source)['records']}
 with store.db:
  for row in manifest['executions']:
   run=runs[row['execution_id']];body={**row,'task_instruction':run['task_instruction'],'catalog_source':str(source),'catalog_source_sha256':source_hash,'status':'historical_inventory_metadata','measurement_status':'verified_development_only' if row['measurement_index_eligible'] else 'not_indexed','physical_safety_conclusion':False}
   old=store.db.execute('SELECT body FROM rag_catalog WHERE execution=?',(row['execution_id'],)).fetchone()
   text=run['task_instruction']['text']
   if old is not None and old[0]!=canonical(body).decode():raise ValueError('catalog source changed; versioned rebuild required')
   if old is None:
    store.db.execute('INSERT INTO rag_catalog VALUES(?,?)',(row['execution_id'],canonical(body).decode()))
    store.db.execute('INSERT INTO rag_catalog_fts VALUES(?,?)',(row['execution_id'],str(text)))
 return store.db.execute('SELECT count(*) FROM rag_catalog').fetchone()[0]

def catalog_search(store,execution=None,limit=20,text=None):
 if type(limit)!=int or not 1<=limit<=100:raise ValueError('limit')
 where=[];args=[];join=''
 if execution:where.append('c.execution=?');args.append(execution)
 if text:
  import re
  terms=re.findall(r'\w+',text)
  if not terms:raise ValueError('catalog text')
  join=' JOIN rag_catalog_fts f ON f.execution=c.execution';where.append('rag_catalog_fts MATCH ?');args.append(' AND '.join(chr(34)+t+chr(34) for t in terms))
 args.append(limit)
 rows=store.db.execute('SELECT c.body FROM rag_catalog c'+join+(' WHERE '+' AND '.join(where) if where else '')+' ORDER BY c.execution LIMIT ?',args).fetchall()
 results=[strict_loads(r[0]) for r in rows]
 cache={}
 for r in results:
  job=store.db.execute('SELECT status,records FROM rag_jobs WHERE execution=?',(r['execution_id'],)).fetchone()
  r['measurement_status_is_historical']=True
  r['current_index_job']={'status':job[0],'records':job[1],'source_validation_rechecked_by_catalog':False} if job else {'status':'not_indexed','records':0,'source_validation_rechecked_by_catalog':False}
  if r['catalog_source']!=str(REPO/'data/runs.json'):raise ValueError('unapproved catalog source')
  key=(r['catalog_source'],r['catalog_source_sha256'])
  if key not in cache:
   if sha(key[0])!=key[1]:raise ValueError('catalog source changed')
   cache[key]=True
 return {'results':results,'kind':'historical_inventory_metadata','valid_measurements_implied':False,'physical_safety_conclusion':False}
