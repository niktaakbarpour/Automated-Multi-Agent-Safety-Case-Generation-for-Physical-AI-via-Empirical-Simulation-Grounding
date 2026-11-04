"""Freeze implementation, schemas, capability bounds and zero-error criteria before evaluation."""
import json,datetime,platform,sqlite3
from importlib.metadata import version
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import *
def run():
 assert not (HERE/'FROZEN_RELEASE_CONFIGURATION.json').exists()
 assert (WORK/'BASELINE_TESTS.json').exists()
 files={p.name:sha(p) for p in HERE.glob('*.py') if p.name in ('config.py','api.py','completeness.py','reference.py','evaluate.py','faults.py','experimental.py')}
 for name in ('STRUCTURED_QUERY_SCHEMA.json','EVIDENCE_BUNDLE_SCHEMA.json','CAPABILITY_REGISTRY.json'):files[name]=sha(HERE/name)
 out=dict(version=VERSION,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),baseline_revision=BASE_COMMIT,baseline_manifest_sha256=BASE_MANIFEST_SHA,database_path=str(DATABASE),database_sha256=DATABASE_SHA,catalogue_path=str(CATALOGUE),catalogue_sha256=CATALOGUE_SHA,files=files,runtime=dict(python=platform.python_version(),sqlite=sqlite3.sqlite_version,packages={p:version(p) for p in ('numpy','h5py','jsonschema','torch','transformers')}),production_route='Explicit structured obligations only; no NLP call or automatic promotion',production_default_verification='strict',evaluation_verification='verified_session with independent strict subset replay',planned_cases=448,planned_executions=16,categories=28,acceptance=dict(exact_status_correct=1.0,source_value_errors=0,source_attribution_errors=0,scope_or_temporal_errors=0,false_complete=0,invalid_assurance_acceptance=0,critical_rejections=1.0,missing_obligation_reporting=1.0,mandatory_family_completeness=1.0,stable_citations=True,exact_independent_replay=True,all_regressions_pass=True),exclusions='No post-result exclusions/label edits/threshold changes; no reserved/preflight/candidate payloads',metric_scope='Repeated structured source-scope instances, not linguistic cases or physical-safety accuracy',decision='A only if structured acceptance and preservation pass; B if implemented but critical release criteria fail; C if source identity/measurement integrity cannot support contract',experimental_policy='K.1 historical shortcomings remain; experimental output never qualifies as production completeness',historical_attestation=False,empirical_admission=False,downstream_agents=False)
 (HERE/'FROZEN_IMPLEMENTATION_CONFIGURATION.json').write_text(json.dumps(out,sort_keys=True,indent=2));print('IMPLEMENTATION/ACCEPTANCE FROZEN',sha(HERE/'FROZEN_IMPLEMENTATION_CONFIGURATION.json'),flush=True)
if __name__=='__main__':run()
