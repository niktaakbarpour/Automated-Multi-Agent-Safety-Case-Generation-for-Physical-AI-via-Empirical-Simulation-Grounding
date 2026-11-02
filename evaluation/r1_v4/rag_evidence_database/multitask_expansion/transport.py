"""Hestia-generated exact storage retrieval command list."""
from pathlib import Path
import shlex,sys
from evaluation.r1_v4.provenance import load
HERE=Path(__file__).resolve().parent

def generate(phase):
 plan=load(HERE/'SOURCE_PLAN.json');rows=[r for r in plan['files'] if r['phase']==phase];lines=['#!/bin/sh','set -eu']
 for archive in sorted({r['archive'] for r in rows}):
  names=[r['archive_member'] for r in rows if r['archive']==archive];emit='printf \'%s\\n%s\\n\' "$TAR_FILENAME" "$TAR_SIZE"; cat'
  remote='tar -x -f '+shlex.quote(archive)+' '+shlex.quote('--to-command='+emit)+' --verbatim-files-from -T -'
  receiver='cd /disk/1/data/niktakbr/trustworthy-phase16 && env PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 -S -m evaluation.r1_v4.rag_evidence_database.multitask_expansion.receive '+shlex.quote(archive)+' '+shlex.quote(phase)
  lines.append("printf '%s\\n' "+' '.join(map(shlex.quote,names))+' | ssh -S /tmp/trustworthy-phase5c-fir.sock -o BatchMode=yes alliance-fir '+shlex.quote(remote)+' | ssh -S /tmp/trustworthy-phase5c-hestia.sock -o BatchMode=yes niktakbr@hestia '+shlex.quote(receiver))
 p=Path('/disk/1/data/niktakbr/trustworthy-phase5e-working')/('transport-'+phase+'.sh');p.write_text('\n'.join(lines)+'\n');print(p)
if __name__=='__main__':generate(sys.argv[1])
