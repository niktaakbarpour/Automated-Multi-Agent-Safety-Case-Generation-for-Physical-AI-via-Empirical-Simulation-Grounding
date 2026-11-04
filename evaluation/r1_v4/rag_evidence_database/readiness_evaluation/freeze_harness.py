"""Seal evaluator code after development, before any final target query."""
import json,subprocess
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import *
def run():
 assert not (WORK/'final_v1').exists();dev=json.loads((WORK/'dev_v3_SUMMARY.json').read_text());assert dev['mode_instances']==108
 rows=[json.loads(p.read_text()) for p in (WORK/'dev_v3').glob('*.json')]
 assert all(not r['assessment']['scope_errors'] and not r['assessment']['source_errors'] and not r['assessment']['numeric_errors'] for r in rows)
 test=subprocess.run(['python3','-S','-m','evaluation.r1_v4.rag_evidence_database.readiness_evaluation.test_metrics'],capture_output=True,text=True);(WORK/'harness_tests.log').write_text(test.stdout+test.stderr);assert test.returncode==0
 names=('config.py','harness.py','run.py','assessment.py','metrics.py','EVALUATION_RUBRIC.md','SOURCE_ASSOCIATIONS.json')
 d=dict(version='phase5j-harness-v3',files={n:sha(HERE/n) for n in names},dataset_sha256=sha(HERE/'EVALUATION_DATASET.jsonl'),configuration_sha256=sha(HERE/'FROZEN_EVALUATION_CONFIGURATION.json'),criteria_sha256=sha(HERE/'ACCEPTANCE_CRITERIA.json'),final_queries_run=0,development_instances=108,harness_unit_tests=7,reference_revision='13 case specifications corrected before final; wording and acceptance criteria unchanged; v1/dev outputs retained')
 tmp=HERE/'HARNESS.v3.tmp';tmp.write_text(json.dumps(d,sort_keys=True,indent=2));tmp.replace(HERE/'HARNESS_VERSION.json')
 (HERE/'HARNESS_VERSION.json').chmod(0o444);print('HARNESS FROZEN',sha(HERE/'HARNESS_VERSION.json'),flush=True)
if __name__=='__main__':run()
