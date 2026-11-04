"""Adversarial metadata scopes; reserved/preflight tests use identifiers only."""
from dataclasses import replace,asdict
from evaluation.r1_v4.provenance import load,write_new
from .registry import VariantStore
from .retrieval import VariantQuery,retrieve
from .plan import HERE,WORK

def run():
 db=VariantStore(WORK/'expanded.sqlite');cohort=load(HERE/'COHORT.json');variants=[r[0] for r in db.db.execute('SELECT id FROM rag_env_variants ORDER BY id')];rows=[]
 def check(name,q,expected):
  r=retrieve(db,q);assert r['status']==expected,(name,r);assert not r['matching_count'] and not r['safety_claim_verified'];rows.append({'name':name,'query':asdict(q),'status':r['status'],'returned_records':0})
 for key,task in cohort['tasks'].items():
  wrong=next(t['task']['task_id'] for k,t in cohort['tasks'].items() if k!=key)
  for e in task['executions']:
   b=db.binding(e['execution_id']);q=VariantQuery(execution_id=e['execution_id'],task_id=b['task_id'],variant_id=b['variant_id'],object_id=task['objects'][0],evidence_types=('object_pose',),interval=(0,0));tag=e['execution_id']
   check(tag+':wrong_task',replace(q,task_id=wrong),'invalid_query_scope')
   check(tag+':wrong_execution',replace(q,execution_id='unknown:'+e['execution_id']),'unknown_execution')
   check(tag+':wrong_variant',replace(q,variant_id=next(v for v in variants if v!=b['variant_id'])),'invalid_query_scope')
   check(tag+':unresolved_variant',replace(q,variant_id='xmlenv:unregistered'),'unresolved_variant')
   check(tag+':missing_field',replace(q,field_name='contact_force'),'unsupported_field')
   check(tag+':absent_timestamp',replace(q,field_name='camera_exposure_timestamp'),'unavailable_timestamp')
   check(tag+':unsupported_spatial',replace(q,field_name='raw_eef_world_pose'),'unsupported_spatial_field')
   check(tag+':logical_fixture',replace(q,field_name='logical_main_table_pose'),'unsupported_mapping')
   check(tag+':outside_frames',replace(q,interval=(e['frames'],e['frames'])),'no_matching_indexed_record')
   check(tag+':wrong_field_family',replace(q,field_name='ctrl'),'invalid_query_scope')
   check(tag+':unsupported_clock',replace(q,time_interval=(0.,1.)),'unsupported_temporal_domain')
   check(tag+':uncalibrated_geometry',replace(q,evidence_types=('native_geometry',),capabilities={'geometry_admission':'VERIFIED'}),'invalid_or_insufficient_evidence')
 for status,expected in [('unindexed_profile_pending','unindexed_execution'),('excluded_reserved','excluded_reserved'),('excluded_preflight','excluded_preflight')]:
  execution=db.db.execute('SELECT execution FROM rag_scope_status WHERE status=? ORDER BY execution LIMIT 1',(status,)).fetchone()[0];check(status,VariantQuery(execution_id=execution,evidence_types=('object_pose',)),expected)
 check('implicit_comparison',VariantQuery(evidence_types=('object_pose',)),'invalid_query_scope')
 shared=db.db.execute('SELECT variant_id FROM rag_execution_env GROUP BY variant_id HAVING count(DISTINCT task_id)>1 ORDER BY variant_id LIMIT 1').fetchone()[0];r=retrieve(db,VariantQuery(variant_id=shared,comparative=True,evidence_types=('execution_metadata',)));assert r['status']=='ok' and len(r['groups'])==2 and not r['coverage_composed_across_executions']
 seen=set()
 for g in r['groups']:
  for item in g['result']['results']:assert item['record']['execution_id']==g['execution_id'];seen.add(item['record']['execution_id'])
 assert len(seen)==2
 db.close();result={'passed':True,'negative_queries':len(rows),'invalid_cross_scope_retrievals':0,'distinct_statuses':sorted({r['status'] for r in rows}),'comparative_shared_variant_executions':sorted(seen),'excluded_tests':'One reserved ID and one preflight ID; no source payload or outcomes inspected.','results':rows};write_new(WORK/'NEGATIVE_RETRIEVAL.json',result);return result
if __name__=='__main__':print(run()['negative_queries'])
