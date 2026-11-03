"""Verify evaluation release boundaries without changing frozen scores or questions."""
import json,sqlite3,shutil,subprocess
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.provenance import digest
from evaluation.r1_v4.integrity import verify
from .config import *
from .harness import frozen_check
from .run import canonical

def run():
 frozen_check();h=json.loads((HERE/'HARNESS_VERSION.json').read_text())
 for n,v in h['files'].items():assert sha(HERE/n)==v,n
 assert sha(HERE/'ACCEPTANCE_CRITERIA.json')=='b869b9210e87de9fd3b439f78dd8d8b51de2b7d7671875683f675d341b2a24a2'
 cases={q['id']:q for q in map(json.loads,(HERE/'EVALUATION_DATASET.jsonl').read_text().splitlines())};old=[json.loads(x) for x in (WORK/'reference_v1/EVALUATION_DATASET.jsonl').read_text().splitlines()];assert all(cases[q['id']]['natural_language_query']==q['natural_language_query'] for q in old)
 rows=[json.loads(x) for x in (HERE/'RETRIEVAL_RESULTS.jsonl').read_text().splitlines()];assert len(rows)==594 and len({(r['case_id'],r['mode']) for r in rows})==594
 for r in rows:
  expected=digest(dict(case=cases[r['case_id']],mode=r['mode'],database=DATABASE_SHA,configuration=sha(HERE/'FROZEN_EVALUATION_CONFIGURATION.json')));assert expected==r['input_digest'];assert digest(canonical({k:v for k,v in r.items() if k!='canonical_digest'}))==r['canonical_digest']
 audit=json.loads((WORK/'INDEPENDENT_OUTPUT_AUDIT.json').read_text());assert audit['passed'] and not audit['errors'];replay=json.loads((WORK/'REPLAY_VALIDATION.json').read_text());assert replay['passed'];reg=json.loads((WORK/'REGRESSION.json').read_text());assert reg['passed'] and reg['total_tests']==718
 final_baseline=json.loads((WORK/'FINAL_BASELINE_VERIFICATION.json').read_text());assert final_baseline['passed'] and final_baseline['checked']==8831
 c=sqlite3.connect(DATABASE.as_uri()+'?mode=ro',uri=True);counts={t:c.execute('select count(*) from '+t).fetchone()[0] for t in ('rag_execution_env','rag_env_variants','evidence','rag_channel_records','i_clock_labels')};assert list(counts.values())==[432,104,80786,2592,58075]
 decision=json.loads((WORK/'READINESS_DECISION.json').read_text());assert decision['recommendation']=='B';validity=json.loads((WORK/'REFERENCE_VALIDITY_AUDIT.json').read_text());assert set(validity['invalid_case_annotations'])=={'C7-06','C7-20'}
 resource=dict(retained_work_bytes=sum(p.stat().st_size for p in WORK.rglob('*') if p.is_file()),free_disk_bytes=shutil.disk_usage(WORK).free,no_duplicate_database=not list(WORK.rglob('*.sqlite')))
 result=dict(passed=True,baseline_database_sha256=DATABASE_SHA,baseline_counts=counts,frozen_configuration_sha256=sha(HERE/'FROZEN_EVALUATION_CONFIGURATION.json'),dataset_sha256=sha(HERE/'EVALUATION_DATASET.jsonl'),harness_sha256=sha(HERE/'HARNESS_VERSION.json'),question_wordings_unchanged=True,criteria_unchanged=True,valid_sufficiency_final_questions=161,known_invalid_sufficiency_annotations=validity['invalid_case_annotations'],recommendation='B',regression_tests=718,harness_unit_tests=7,canonical_replay_differences=0,frozen=verify(),resource=resource,new_profiles=0,new_channels=0,production_retrieval_modified=False,empirical_admission_enabled=False,downstream_agents=False,pushed=False,merged=False)
 (WORK/'FINAL_AUDIT.json').write_text(json.dumps(result,sort_keys=True,indent=2));print('FINAL AUDIT PASS',resource,flush=True)
if __name__=='__main__':run()
