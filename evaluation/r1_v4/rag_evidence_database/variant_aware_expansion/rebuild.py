"""Independent repeat, resumed jobs and byte-preserving baseline row proof."""
from evaluation.r1_v4.provenance import load,write_new,digest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.store import Store
from .plan import WORK,BASE,BASE_SHA
from .build import populate
from .registry import VariantStore

def run():
 first=load(WORK/'BUILD_MANIFEST.json');resumed=populate(WORK/'expanded.sqlite');assert resumed['build_id']==first['build_id'] and len(resumed['skipped'])==first['new_executions'];write_new(WORK/'RESUME_REPORT.json',resumed)
 repeated=populate(WORK/'independent.sqlite');assert repeated['build_id']==first['build_id'];write_new(WORK/'INDEPENDENT_BUILD.json',repeated)
 a=VariantStore(WORK/'expanded.sqlite');b=VariantStore(WORK/'independent.sqlite');assert digest(a.export())==digest(b.export());b.close();original=Store(BASE);counts={}
 for table,key in [('evidence','id'),('rag_units','id'),('rag_catalog','execution'),('rag_jobs','execution')]:
  expected={r[0]:digest(r) for r in original.db.execute('SELECT '+key+',* FROM '+table)};actual={r[0]:digest(r) for r in a.db.execute('SELECT '+key+',* FROM '+table) if r[0] in expected};assert actual==expected;counts[table]=len(expected)
 original.close();check=a.variant_check();assert check['passed'];write_new(WORK/'DATABASE_INTEGRITY.json',check);a.close();assert sha(BASE)==BASE_SHA
 write_new(WORK/'REBUILD_VALIDATION.json',{'passed':True,'logical_build_id':first['build_id'],'same_record_export':True,'same_variant_relations':True,'baseline_rows_preserved':counts,'completed_jobs_skipped':len(resumed['skipped']),'baseline_sha256':BASE_SHA,'database_sha256':sha(WORK/'expanded.sqlite'),'database_bytes':(WORK/'expanded.sqlite').stat().st_size});print('Rebuild/resume/baseline/integrity passed',counts,flush=True)
if __name__=='__main__':run()
