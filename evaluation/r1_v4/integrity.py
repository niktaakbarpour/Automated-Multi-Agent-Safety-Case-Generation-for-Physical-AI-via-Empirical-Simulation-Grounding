"""Read-only Hestia integrity checks against preserved Phase 1.6 hash records."""
from pathlib import Path
import socket
import subprocess
from .configuration import REPO, SPEC
from .provenance import bytes_digest, load
BASE='609ac744b1b2fb899c783de5bb3df3c39943f57e'

def verify():
    if socket.gethostname().lower()!='hestia':
        raise RuntimeError('Frozen integrity checks run on Hestia')
    changes=subprocess.check_output(['git','diff','--name-only',BASE],cwd=REPO,text=True).splitlines()
    if any(not p.startswith('evaluation/r1_v4/') for p in changes):
        raise ValueError('changes_outside_v4_directory')
    audited=load(SPEC/'AUDIT_SOURCE_BINDINGS.json')['files']
    for n,h in audited.items():
        if bytes_digest((REPO/n).read_bytes())!=h:
            raise ValueError('audited_baseline_changed:'+n)
    expected=load(SPEC/'finalization/SPEC_QA_RESULTS.json')['frozen_hestia_checks']
    actual={}
    sealed=0
    for name,entry in expected.items():
        p=Path(name)
        if not str(p).startswith('/disk/1/data/niktakbr/'):
            raise ValueError('unexpected_integrity_path')
        h=bytes_digest(p.read_bytes())
        if h!=entry['sha256']:raise ValueError('frozen_artifact_changed:'+name)
        actual[name]=h
        if p.name.endswith('_SEAL.json'):
            for member,digest in load(p)['files'].items():
                f=p.parent/member
                if not f.resolve().is_relative_to(p.parent.resolve()):raise ValueError('seal_path_escape')
                if bytes_digest(f.read_bytes())!=digest:raise ValueError('seal_member_changed:'+member)
                sealed+=1
    root=Path('/disk/1/data/niktakbr/r1-v3-human-validation-20-20261027')
    freeze=root/'SCORING_FREEZE.json'
    if bytes_digest(freeze.read_bytes())!='6a9b6d2f39422e010ad8a13bf29278ac2255da673473ce8d5a4e8c0301cb23ff':
        raise ValueError('human_scoring_freeze_changed')
    protected=load(freeze)['files']
    for name,h in protected.items():
        p=root/name
        if not p.resolve().is_relative_to(root):raise ValueError('scoring_path_escape')
        if bytes_digest(p.read_bytes())!=h:raise ValueError('human_scoring_guard_changed:'+name)
    return {'passed':True,'audited_sources':len(audited),'live_frozen_hashes':actual,
            'sealed_members_verified':sealed,'human_scoring_protected_files':len(protected),
            'human_freeze_sha256':bytes_digest(freeze.read_bytes()),'baseline':BASE,
            'all_existing_tracked_files_unchanged':True,'new_v4_tracked_files':len(changes)}
