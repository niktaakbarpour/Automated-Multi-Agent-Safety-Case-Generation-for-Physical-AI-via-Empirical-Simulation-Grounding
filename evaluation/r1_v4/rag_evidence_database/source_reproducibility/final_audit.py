"""Aggregate exact results and assert release invariants without changing old data."""
import json,sqlite3,subprocess
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.integrity import verify
from .config import WORK,BASE,BASE_SHA

def run():
 def load(n):return json.loads((WORK/n).read_text())
 build=load('BUILD.json');assert sha(WORK/'expanded.sqlite')==build['database_sha256'];assert sha(BASE)==BASE_SHA
 for n in ('ASSURANCE_VALIDATION.json','RESTORATION.json','REBUILD_RESUME.json','PRESERVATION.json','CLAIM_VALIDATION.json','SEMANTIC_EQUIVALENCE.json','GRAPH_RELEASE_VALIDATION.json'):assert load(n)['passed'],n
 assert load('REGRESSION.json')['total_tests']==718
 h=load('legacy_h/RETRIEVAL_VALIDATION.json');g=load('legacy_g/EXTRACTION_RETRIEVAL_VALIDATION.json');f=load('legacy_f/RETRIEVAL_METRICS.json')
 for r in (h,g,f):assert r['precision_at_1']==r['recall_at_20']==r['MRR']==1.
 sf=load('legacy_f/SEMANTIC_EVALUATION.json');assert sf['passed'] and sf['invalid_cross_scope_retrievals']==0 and sf['unique_linguistic_probes']==12;assert sf['aggregate']['semantic']['precision_at_1']==0.935374149659864
 assert load('legacy_g/CHANNEL_SEMANTIC_EVALUATION.json')['cross_scope_leakage']==0
 c=sqlite3.connect('file:'+str(WORK/'expanded.sqlite')+'?mode=ro',uri=True);counts={t:c.execute('select count(*) from '+t).fetchone()[0] for t in ('rag_execution_env','rag_env_variants','evidence','rag_channel_records','h_semantics','i_clock_labels')};assert list(counts.values())==[432,104,80786,2592,2592,58075]
 result=dict(passed=True,counts=counts,build=build,baseline_sha256=BASE_SHA,regression_tests=718,frozen=verify(),exact_benchmarks=dict(phase5f_queries=len(load('legacy_f/QUERY_FIXTURES.json')),phase5f_negatives=load('legacy_f/NEGATIVE_RETRIEVAL.json')['negative_queries'],phase5g_queries=g['source_target_queries'],phase5g_negatives=g['negative_controls'],phase5h_queries=h['queries'],phase5h_negatives=h['negative_controls']),phase5i_assurance=load('ASSURANCE_VALIDATION.json'),new_executions=0,new_measurement_channels=0,empirical_admission_enabled=False,downstream_agents_implemented=False,push_or_merge_performed=False)
 (WORK/'FINAL_AUDIT.json').write_text(json.dumps(result,sort_keys=True,indent=2));print('FINAL AUDIT PASS',flush=True)
if __name__=='__main__':run()
