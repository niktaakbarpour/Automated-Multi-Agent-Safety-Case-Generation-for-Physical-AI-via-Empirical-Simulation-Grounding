"""Read-only preservation checks. Prior release manifests remain the trust roots."""
import json,sqlite3,subprocess,os,time
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.readiness_evaluation.check_artifacts import verify
from evaluation.r1_v4.integrity import verify as frozen_verify
from .config import *
def run():
 assert subprocess.check_output(['hostname']).decode().strip().split('.')[0]=='hestia'
 assert subprocess.call(['git','merge-base','--is-ancestor',BASE_COMMIT,'HEAD'])==0
 assert sha(DATABASE)==DATABASE_SHA
 r=verify('375989a36a5c2390987e88a5228701682d51e5127b5de2b275cac2fb7bf16b25');c=__import__('sqlite3').connect(DATABASE.as_uri()+'?mode=ro',uri=True);r['counts']={t:c.execute('select count(*) from '+t).fetchone()[0] for t in ('rag_execution_env','rag_env_variants','evidence','rag_channel_records','i_clock_labels')};assert list(r['counts'].values())==[432,104,80786,2592,58075];c.close();r['frozen_seals_scoring']=frozen_verify();r['database_sha256']=DATABASE_SHA;r['baseline_revision']=BASE_COMMIT;r['corpus_expansion']=False
 f=json.loads((HERE/'FROZEN_IMPLEMENTATION.json').read_text())
 for n,h in f['files'].items():assert sha(HERE/n)==h,n
 assert sha(WORK/'catalogue.sqlite')==f['sidecar_sha256'];r['implementation_manifest_sha256']=sha(HERE/'FROZEN_IMPLEMENTATION.json');r['holdout_dataset_sha256']=sha(HERE/'FROZEN_HOLDOUT_DATASET.jsonl');assert r['holdout_dataset_sha256']==json.loads((HERE/'HOLDOUT_FREEZE.json').read_text())['dataset_sha256'];(WORK/'FINAL_BASELINE_VERIFICATION.json').write_text(json.dumps(r,sort_keys=True,indent=2));print('PRESERVATION VERIFIED',flush=True)
if __name__=='__main__':run()
