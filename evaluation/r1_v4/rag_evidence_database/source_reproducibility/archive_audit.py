"""Bounded archive environment audit; candidate declarations are not execution attestations."""
import json,zipfile,hashlib,stat,re,tomllib
from pathlib import Path
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier
from .config import WORK

def run():
 a=json.loads((WORK/'PRODUCER_EVIDENCE.json').read_text())['archive_matches'][0];rows=[];binary=[]
 with SourceVerifier().access(a['archive_path'],a['archive_sha256'],'strict') as (f,att):
  with zipfile.ZipFile(f) as z:
   for i in z.infolist():
    name=Path(i.filename).name.lower()
    if i.is_dir() or i.file_size>2*1024*1024:continue
    mode=i.external_attr>>16
    if re.search(r'\.so($|\.)',name) or name in ('python','python3','python3.12'):
     data=z.read(i);binary.append(dict(member=i.filename,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),kind='ZIP_SYMLINK_TARGET_TEXT' if stat.S_ISLNK(mode) else 'UNVERIFIED_BINARY_CANDIDATE',historical_runtime_attested=False))
    if name in ('pyproject.toml','requirements.txt','requirements-dev.txt','uv.lock','poetry.lock','pipfile.lock','dockerfile','environment.yml','environment.yaml','setup.py','setup.cfg') or name.endswith('.lock'):
     data=z.read(i);r=dict(member=i.filename,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),classification='RETROSPECTIVE_ARCHIVE_MEMBER',historical_recording_environment_attested=False,role='PROCESS_COORDINATION_LOCK' if name=='queue.lock' else 'UNBOUND_BUILD_OR_DEPENDENCY_DECLARATION',limitation='No original execution binding to running environment; generic upstream Dockerfile does not identify a used image')
     if name=='pyproject.toml':
      try:
       t=tomllib.loads(data.decode());p=t.get('project',{});r['project_summary']={k:p.get(k) for k in ('name','version','requires-python')};r['declared_dependency_count']=len(p.get('dependencies',[]))
      except (ValueError,UnicodeError):r['toml_parse']='unresolved'
     rows.append(r)
 result=dict(archive_path=a['archive_path'],archive_sha256=a['archive_sha256'],members=rows,binary_candidates=binary,historical_container_digest=None,historical_binary_attestation='UNATTESTED')
 (WORK/'ARCHIVE_ENVIRONMENT_AUDIT.json').write_text(json.dumps(result,sort_keys=True,indent=2));print('ARCHIVE ENVIRONMENT',len(rows),'declarations',len(binary),'binary/path candidates',flush=True)
if __name__=='__main__':run()
