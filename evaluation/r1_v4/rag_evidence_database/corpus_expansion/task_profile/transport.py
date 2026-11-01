"""Generate exact storage-only transfer commands, computed on Hestia."""
from pathlib import Path
import shlex,sys
from evaluation.r1_v4.provenance import load
from .plan import HERE

def generate(phase):
 plan=load(HERE/'SOURCE_PLAN.json');lines=['#!/bin/sh','set -eu'];rows=[r for r in plan['files'] if r['phase']==phase]
 for archive in sorted({r['archive'] for r in rows}):
  names=[r['archive_member'] for r in rows if r['archive']==archive]
  emit='printf \'%s\\n%s\\n\' "$TAR_FILENAME" "$TAR_SIZE"; cat'
  remote='tar -x -f '+shlex.quote(archive)+' '+shlex.quote('--to-command='+emit)+' -- '+' '.join(map(shlex.quote,names))
  receive='cd /disk/1/data/niktakbr/trustworthy-phase16 && env PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 -S -m evaluation.r1_v4.rag_evidence_database.corpus_expansion.task_profile.receive '+shlex.quote(archive)+' '+shlex.quote(phase)
  lines.append('ssh -S /tmp/trustworthy-phase5c-fir.sock -o BatchMode=yes alliance-fir '+shlex.quote(remote)+' | ssh -S /tmp/trustworthy-phase5c-hestia.sock -o BatchMode=yes niktakbr@hestia '+shlex.quote(receive))
 output=Path('/disk/1/data/niktakbr/trustworthy-phase5d-working')/('transport-'+phase+'.sh');output.write_text('\n'.join(lines)+'\n');print(output)
if __name__=='__main__':generate(sys.argv[1])
