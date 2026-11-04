"""Measured strict versus verified-session overhead; no verification relaxation."""
import json,time,statistics,sys,sqlite3,os,subprocess,platform
from dataclasses import replace
import h5py,numpy,torch,transformers
from .config import *
from .bundle import Retriever,BundleRequest
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
def main():
 cases=[json.loads(l) for l in (HERE/'FROZEN_HOLDOUT_DATASET.jsonl').read_text().splitlines()];cases=[q for q in cases if q['category']=='C1'][:8];build=json.loads((WORK/'BUILD.json').read_text());r=Retriever(WORK/'catalogue.sqlite',build['sha256']);rows=[]
 try:
  for mode in ('strict','verified_session'):
   for repeat in range(2):
    for q in cases:
     b=BundleRequest(q['query'],**q['request']);b=replace(b,verification_mode=mode);start=time.perf_counter();o=r.retrieve(b);elapsed=time.perf_counter()-start;assert o['completeness_status']=='COMPLETE WITHIN VERIFIED CONTRACT';rows.append(dict(case_id=q['id'],mode=mode,repeat=repeat,seconds=elapsed))
 finally:r.close()
 summary={m:dict(queries=len([x for x in rows if x['mode']==m]),median=statistics.median(x['seconds'] for x in rows if x['mode']==m),max=max(x['seconds'] for x in rows if x['mode']==m)) for m in ('strict','verified_session')};(WORK/'BENCHMARK.json').write_text(json.dumps(dict(rows=rows,summary=summary,mode_difference='Session verification reuses cryptographically verified identities only while descriptor/file identity signatures remain stable; strict hashes on every access'),sort_keys=True,indent=2))
 env=dict(host=platform.node(),python=sys.version,sqlite=sqlite3.sqlite_version,h5py=h5py.__version__,numpy=numpy.__version__,torch=torch.__version__,transformers=transformers.__version__,platform=platform.platform(),memory_status=[l.strip() for l in open('/proc/self/status') if l.startswith(('VmPeak:','VmHWM:','VmRSS:'))],free_disk_bytes=os.statvfs(WORK).f_bavail*os.statvfs(WORK).f_frsize,work_bytes=int(subprocess.check_output(['du','-sb',str(WORK)]).split()[0]));(WORK/'ENVIRONMENT_AND_RESOURCES.json').write_text(json.dumps(env,sort_keys=True,indent=2));print(summary,flush=True)
if __name__=='__main__':main()
