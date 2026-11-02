"""Bound shell arguments and resume only missing exact members."""
from pathlib import Path
import shlex
from evaluation.r1_v4.provenance import load,write_new
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .plan import HERE,DEST

def main():
 plan=load(HERE/'SOURCE_PLAN.json');missing=[];existing=[]
 for r in plan['files']:
  p=Path(r['restored_path'])
  if p.exists():
   assert p.stat().st_size==r['bytes']
   if r['expected_sha256']:assert sha(p)==r['expected_sha256']
   existing.append(str(p))
  else:missing.append(r)
 groups={};lines=['#!/bin/sh','set -eu']
 for archive in sorted({r['archive'] for r in missing}):
  rows=[r for r in missing if r['archive']==archive];assert all(r['phase']=='batch' for r in rows)
  for start in range(0,len(rows),64):
   key='resume-'+str(len(groups)).zfill(3);names=[r['archive_member'] for r in rows[start:start+64]];groups[key]={'archive':archive,'phase':'batch','members':names}
   emit='printf \'%s\\n%s\\n\' "$TAR_FILENAME" "$TAR_SIZE"; cat'
   remote='tar -x -f '+shlex.quote(archive)+' '+shlex.quote('--to-command='+emit)+' --verbatim-files-from -T -'
   receiver='cd /disk/1/data/niktakbr/trustworthy-phase16 && env PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 -S -m evaluation.r1_v4.rag_evidence_database.multitask_expansion.receive '+shlex.quote(archive)+' batch '+key
   lines.append("printf '%s\\n' "+' '.join(map(shlex.quote,names))+' | ssh -S /tmp/trustworthy-phase5c-fir.sock -o BatchMode=yes alliance-fir '+shlex.quote(remote)+' | ssh -S /tmp/trustworthy-phase5c-hestia.sock -o BatchMode=yes niktakbr@hestia '+shlex.quote(receiver))
 write_new(HERE/'TRANSFER_BATCHES.json',groups);write_new(HERE/'TRANSFER_RESUME.json',{'existing_verified_paths':existing,'missing_files':len(missing),'groups':len(groups),'reason':'Initial per-archive shell command exceeded argument length; resumed bounded member groups; no files overwritten.'})
 p=Path('/disk/1/data/niktakbr/trustworthy-phase5e-working/transport-resume.sh');p.write_text('\n'.join(lines)+'\n');print(len(existing),len(missing),len(groups))
if __name__=='__main__':main()
