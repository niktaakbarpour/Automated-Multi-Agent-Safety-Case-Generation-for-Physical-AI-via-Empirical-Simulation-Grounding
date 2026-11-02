"""Current dependency bytes, RECORD consistency and ABI facts; never historical binary attestation."""
import importlib.metadata as md,importlib,json,sys,os,hashlib,base64,stat,platform,datetime
from pathlib import Path
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier,SourceError
from .config import WORK
from .inventory import save

def collect(environment):
 roots=('/disk/0/home/niktakbr','/disk/1/data/niktakbr','/usr/bin','/usr/lib','/usr/lib64');v=SourceVerifier(roots=roots,namespace='hestia-current-'+environment);packages=[];artifacts={};skipped=[];total=0
 names=('numpy','h5py','torch','transformers','tokenizers','safetensors','jsonschema') if environment=='retrieval' else ('numpy','mujoco','robosuite','hf_libero')
 def capture(path,kind,expected=None):
  nonlocal total
  path=Path(os.path.normpath(str(path)))
  if str(path) in artifacts:return artifacts[str(path)]
  try:
   fd=v.open_fd(path)
   with os.fdopen(fd,'rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest();size=os.fstat(f.fileno()).st_size
  except (SourceError,OSError):return None
  total+=size;record=dict(path=str(path),sha256=actual,bytes=size,kind=kind,classification='RETROSPECTIVE_ARTIFACT',historical_binary_attestation='UNATTESTED',record_digest_matches=None if expected is None else actual==expected)
  artifacts[str(path)]=record;return record
 for name in names:
  try:dist=md.distribution(name)
  except md.PackageNotFoundError:packages.append(dict(name=name,status='NOT_INSTALLED_CURRENT'));continue
  refs=[];consistency=0;mismatches=[];missing=[];other=0
  for item in dist.files or []:
   text=str(item);kind='ELF_BINARY' if '.so' in Path(text).name else 'SOURCE_CODE' if text.endswith('.py') else 'PACKAGE_METADATA' if any(text.endswith(x) for x in ('/METADATA','/WHEEL','/RECORD','/direct_url.json','/INSTALLER','/entry_points.txt')) else None
   if kind is None:other+=1;continue
   expected=None
   if item.hash and item.hash.mode=='sha256':expected=base64.urlsafe_b64decode(item.hash.value+'='*((4-len(item.hash.value)%4)%4)).hex()
   p=dist.locate_file(item);r=capture(p,kind,expected)
   if r is None:missing.append(str(p));continue
   refs.append(r['path'])
   if expected:
    consistency+=1
    if r['sha256']!=expected:mismatches.append(dict(path=r['path'],record_sha256=expected,actual_sha256=r['sha256']))
  packages.append(dict(name=name,version=dist.version,classification='RETROSPECTIVE_ARTIFACT',recording_time_identity='UNATTESTED',metadata_location=str(getattr(dist,'_path','')),artifact_paths=refs,record_hashes_checked=consistency,record_mismatches=mismatches,unavailable_or_redirected_files=missing,other_distribution_payloads_not_hashed=other,requires_dist=dist.metadata.get_all('Requires-Dist') or [],completeness='Selected executable Python, ELF and metadata files; not a hermetic environment or proof of pristine historical installation'))
 # Load only the decoder/native libraries needed to identify current mapped ABI files.
 for module in (('numpy','h5py','sqlite3','_sqlite3') if environment=='retrieval' else ('mujoco','numpy')):
  try:importlib.import_module(module)
  except ImportError:pass
 maps=[]
 with open('/proc/self/maps') as f:
  for line in f:
   p=line.rstrip().split()[-1]
   if p.startswith(('/usr/lib/','/usr/lib64/','/disk/0/home/niktakbr/')) and '.so' in p and p not in maps:maps.append(p)
 for p in maps:capture(p,'MAPPED_CURRENT_ABI_LIBRARY')
 executable=Path(sys.executable)
 if executable.is_symlink():executable=executable.parent/os.readlink(executable)
 capture(executable,'CURRENT_PYTHON_BINARY')
 result=dict(environment=environment,classification='RETROSPECTIVE_ARTIFACT',historical_runtime_attested=False,collected_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),collection_date_basis='Current host clock, not a historical timestamp authority',runtime=dict(executable=str(executable),python=sys.version,abi=sys.implementation.cache_tag,byteorder=sys.byteorder,machine=platform.machine(),libc=platform.libc_ver()),packages=packages,artifacts=list(artifacts.values()),bytes_hashed=total,scope='Current code/binary identity and installed RECORD consistency only. Historical dependency version declarations are inventoried separately.')
 save('DEPENDENCIES_'+environment+'.json',result);print('DEPENDENCIES',environment,len(artifacts),total,'RECORD mismatches',sum(len(p.get('record_mismatches',[])) for p in packages),flush=True)
if __name__=='__main__':collect(sys.argv[1])
