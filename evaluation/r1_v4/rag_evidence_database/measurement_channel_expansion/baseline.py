import sqlite3,json,time
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha,REPO
from evaluation.r1_v4.integrity import verify
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion.final_validation import source_rows
from evaluation.r1_v4.rag_evidence_database.variant_aware_expansion import regressions
root=Path('/disk/1/data/niktakbr/trustworthy-phase5g-working');root.mkdir(exist_ok=True)
def save(n,v):
 with (root/n).open('x') as f:json.dump(v,f,sort_keys=True,indent=2)
here=REPO/'evaluation/r1_v4/rag_evidence_database/variant_aware_expansion'
m=json.loads((here/'ARTIFACT_MANIFEST.json').read_text()); checked=[]
for r in m['files']+m['external_release_artifacts']:
 p=Path(r['path']);p=p if p.is_absolute() else REPO/p
 assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p)
 checked.append(str(p))
for r in json.loads((here/'EXTERNAL_PROFILE_ARTIFACTS.json').read_text())['files']:
 assert sha(r['path'])==r['sha256'];checked.append(r['path'])
for r in source_rows():
 assert sha(r['restored_path'])==(r.get('actual_sha256') or r['sha256']);checked.append(r['restored_path'])
c=sqlite3.connect('file:/disk/1/data/niktakbr/trustworthy-phase5f-working/expanded.sqlite?mode=ro',uri=True)
assert c.execute('PRAGMA integrity_check').fetchall()==[('ok',)]
counts={k:c.execute(q).fetchone()[0] for k,q in {'records':'select count(*) from evidence','executions':'select count(distinct execution_id) from evidence','variants':'select count(*) from rag_env_variants'}.items()}
assert counts==dict(records=80786,executions=432,variants=104),counts
save('BASELINE_VERIFIED.json',dict(passed=True,counts=counts,hashed_paths=checked,schema=c.execute("select name,sql from sqlite_master where sql is not null order by name").fetchall(),frozen=verify(),database_sha256=sha('/disk/1/data/niktakbr/trustworthy-phase5f-working/expanded.sqlite')))
print('Baseline sources and manifests verified',len(checked),flush=True)
regressions.WORK=root/'baseline-regressions';regressions.WORK.mkdir()
regressions.run()
print('BASELINE COMPLETE',flush=True)
