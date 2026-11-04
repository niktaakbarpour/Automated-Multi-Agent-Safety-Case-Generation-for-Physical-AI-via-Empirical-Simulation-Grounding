"""Read-only prior release, source, count and frozen evaluation verification."""
import json,sqlite3,platform,subprocess
from .config import *
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from evaluation.r1_v4.rag_evidence_database.obligation_preservation.release import verify as k1
from evaluation.r1_v4.rag_evidence_database.retrieval_remediation.verify_manifest import verify as k
from evaluation.r1_v4.rag_evidence_database.readiness_evaluation.check_artifacts import verify as j
from evaluation.r1_v4.integrity import verify

def run():
 assert platform.node().split('.')[0]=='hestia'
 assert subprocess.call(['git','merge-base','--is-ancestor','9de85693fae1323cc2ce12edf59268c8bd0e7c58','HEAD'])==0
 k1('557a93d25d9b2bd4571af14cdfe414fd016ee95d7d1813cebf77b87144c55344')
 out={'k':k('e0006613de605ad14025c91ae23fd16ab373fb5f7acd1bf1449fdf0c626122ee'),'j':j('375989a36a5c2390987e88a5228701682d51e5127b5de2b275cac2fb7bf16b25'),'seals':verify()}
 assert sha(DATABASE)==DATABASE_SHA
 c=sqlite3.connect(DATABASE.as_uri()+'?mode=ro',uri=True)
 out['counts']={t:c.execute('select count(*) from '+t).fetchone()[0] for t in ('rag_execution_env','rag_env_variants','evidence','rag_channel_records','i_clock_labels')};c.close()
 assert list(out['counts'].values())==[432,104,80786,2592,58075]
 out.update(passed=True,database_sha256=sha(DATABASE),k1_verified_artifacts=2118)
 (WORK/'FINAL_PRESERVATION.json').write_text(json.dumps(out,sort_keys=True,indent=2));print('PRESERVATION PASSED',flush=True)
if __name__=='__main__':run()
