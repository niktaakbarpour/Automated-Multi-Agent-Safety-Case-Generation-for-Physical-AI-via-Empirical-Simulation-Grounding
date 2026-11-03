"""Independent read-only prior release/source/seal verification, with new outputs only."""
import json,sqlite3,subprocess,os,platform
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.verify_manifest import verify as verify_k
from evaluation.r1_v4.rag_evidence_database.readiness_evaluation.check_artifacts import verify as verify_j
from evaluation.r1_v4.integrity import verify as verify_frozen
from .config import *
def run():
 assert platform.node().split('.')[0]=='hestia';assert subprocess.call(['git','merge-base','--is-ancestor',BASE_COMMIT,'HEAD'])==0
 k_count=verify_k(BASE_MANIFEST_SHA);j=verify_j('375989a36a5c2390987e88a5228701682d51e5127b5de2b275cac2fb7bf16b25');assert sha(DATABASE)==DATABASE_SHA and sha(CATALOGUE)==CATALOGUE_SHA;c=sqlite3.connect(DATABASE.as_uri()+'?mode=ro',uri=True);counts={t:c.execute('select count(*) from '+t).fetchone()[0] for t in ('rag_execution_env','rag_env_variants','evidence','rag_channel_records','i_clock_labels')};assert list(counts.values())==[432,104,80786,2592,58075];c.close();out=dict(passed=True,host=platform.node(),baseline_revision=BASE_COMMIT,baseline_k_verified_artifacts=k_count,parent_j_and_i=j,frozen_seals_and_scoring=verify_frozen(),database_sha256=DATABASE_SHA,catalogue_sha256=CATALOGUE_SHA,counts=counts,work_bytes=sum(p.stat().st_size for p in WORK.rglob('*') if p.is_file()),free_disk_bytes=os.statvfs(WORK).f_bavail*os.statvfs(WORK).f_frsize,no_corpus_expansion=True,no_new_channels=True);(WORK/'FINAL_PRESERVATION.json').write_text(json.dumps(out,sort_keys=True,indent=2));print('ALL PRIOR RELEASES/SOURCES/SEALS VERIFIED',flush=True)
if __name__=='__main__':run()
