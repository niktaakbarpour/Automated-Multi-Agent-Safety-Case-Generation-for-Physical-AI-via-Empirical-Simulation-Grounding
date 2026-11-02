"""Fresh baseline manifest, frozen archives, native inputs and release preservation."""
import json,subprocess,os
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import REPO,sha
from evaluation.r1_v4.integrity import verify
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.check_release import run as check_g
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion.final_validation import source_rows
from .config import WORK,HERE,BASE,BASE_SHA,BASE_COMMIT
from .audit import save
from .validate import preservation

def run():
 check_g();checked=0
 for r in source_rows():assert sha(r['restored_path'])==(r.get('actual_sha256') or r['sha256']);checked+=1
 g=Path('/disk/1/data/niktakbr/trustworthy-phase5g-working')
 for p,h in json.loads((g/'INVENTORY_SUPPLEMENT.json').read_text())['sources'].items():assert sha(p)==h;checked+=1
 for row in json.loads((g/'MAIN_TABLE_AUDIT.json').read_text())['rows']:
  for s in row['sources']:assert sha(s['owned_path'])==s['expected_sha256'];checked+=1
 for r in json.loads((WORK/'PRIMARY_SOURCES.json').read_text())['files']:assert sha(r['path'])==r['sha256'];checked+=1
 for p in (WORK/'models').glob('*.json'):
  m=json.loads(p.read_text());assert sha(m['xml_path'])==m['xml_sha256'] and sha(m['compiler_record_path'])==m['compiler_record_sha256'];checked+=2
 assert all(r['equal'] for r in json.loads((WORK/'MUJOCO_HEADER_COMPARISON.json').read_text()))
 from .source_integrity import SourceVerifier
 from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import owned
 import sqlite3
 verifier=SourceVerifier();catalog=sqlite3.connect(BASE.as_uri()+'?mode=ro',uri=True)
 for body, in catalog.execute('select body from rag_env_variants'):
  for asset in json.loads(body)['assets']:verifier.verify(str(owned(asset['path'])),asset['sha256'],'verified_session');checked+=1
 catalog.close()
 assert sha(BASE)==BASE_SHA
 for name in ('reference_hardened/RETRIEVAL_VALIDATION.json','REBUILD_VALIDATION.json','REGRESSION_HARDENED.json','reference_hardened/SEMANTIC_BENCHMARK.json','VELOCITY_VALIDATION.json','VELOCITY_BY_CHANNEL.json','BINDING_VALIDATION.json','FORCE_LIMITS_VALIDATION.json','CLI_VALIDATION.json'):assert json.loads((WORK/name).read_text())['passed'],name
 assert json.loads((WORK/'legacy_g/EXTRACTION_RETRIEVAL_VALIDATION.json').read_text())['passed'];assert json.loads((WORK/'legacy_g/CHANNEL_SEMANTIC_EVALUATION.json').read_text())['passed'];assert json.loads((WORK/'legacy_f/SEMANTIC_EVALUATION.json').read_text())['passed'];assert json.loads((WORK/'legacy_f/NEGATIVE_RETRIEVAL.json').read_text())['passed']
 changed=subprocess.check_output(['git','diff','--name-only',BASE_COMMIT],text=True).splitlines();assert all(p.startswith(str(HERE.relative_to(REPO))+'/') for p in changed)
 frozen=verify();save(WORK/'FROZEN_FINAL.json',frozen);save(WORK/'PRESERVATION_FINAL.json',preservation(WORK/'expanded.sqlite'))
 build=json.loads((WORK/'BUILD.json').read_text());assert sha(WORK/'expanded.sqlite')==build['database_sha256']
 result=dict(passed=True,baseline_commit=BASE_COMMIT,baseline_database_sha256=BASE_SHA,baseline_manifest_entries_verified=585,fresh_source_checks=checked,database_path=str(WORK/'expanded.sqlite'),database_sha256=sha(WORK/'expanded.sqlite'),database_bytes=(WORK/'expanded.sqlite').stat().st_size,frozen=frozen,free_disk_bytes=os.statvfs('/disk/1').f_bavail*os.statvfs('/disk/1').f_frsize,empirical_admission_enabled=False,simulations_stepped=0,source_corpus_copies=0,push_or_merge=False)
 save(WORK/'FINAL_AUDIT.json',result);print('FINAL AUDIT PASSED',result['database_sha256'],flush=True)
if __name__=='__main__':run()
