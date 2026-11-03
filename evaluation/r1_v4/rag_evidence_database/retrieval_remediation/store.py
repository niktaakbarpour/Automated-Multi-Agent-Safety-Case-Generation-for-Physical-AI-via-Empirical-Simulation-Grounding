"""Unified descriptor-bound readers, including the legacy geometry compatibility path."""
import json,os,contextlib,xml.etree.ElementTree as ET
from pathlib import Path
from evaluation.r1_v4.provenance import digest
from evaluation.r1_v4.rag_evidence_database.source_reproducibility.store import ProvenanceStore
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier,SourceError
from .config import DATABASE,DATABASE_SHA

def canonical_path(path):
 p=Path(path)
 if '..' in p.parts:raise SourceError('path_traversal')
 if str(p).startswith('/local/home/niktakbr/'):
  a=Path('/local/home/niktakbr');b=Path('/disk/0/home/niktakbr')
  if (a.stat().st_dev,a.stat().st_ino)!=(b.stat().st_dev,b.stat().st_ino):raise SourceError('unverified_bind_alias')
  p=b/p.relative_to(a)
 return str(p)
class VerifiedReferences:
 def __init__(self,restore=None,restore_sha256=None):
  self.base=SourceVerifier(namespace='phase5k-descriptor-bound-v1');self.restore=None;self.execution=None;self.variant=None
  if restore is not None:
   with self.base.access(str(restore),restore_sha256,'strict') as (f,a):self.restore=json.load(f)
   if self.restore.get('database_sha256')!=DATABASE_SHA:raise SourceError('restoration_database_identity_mismatch')
   self.restore_root=Path(restore).parent;self.restore_sha=restore_sha256;self.restore_path=str(restore)
 @contextlib.contextmanager
 def access(self,path,expected,mode='strict'):
  original=canonical_path(path);resolved=original
  if self.restore is not None:
   self.base.verify(self.restore_path,self.restore_sha,'strict');entry=self.restore['entries'].get(original+'#'+expected)
   if not entry or self.execution not in entry['executions']:raise SourceError('unmapped_restoration_scope')
   if entry.get('variants') is not None and self.variant not in entry['variants']:raise SourceError('wrong_restoration_variant')
   rel=Path(entry['relative_path'])
   if rel.is_absolute() or '..' in rel.parts:raise SourceError('unsafe_restore_path')
   resolved=str(self.restore_root/rel)
  with self.base.access(resolved,expected,mode) as (f,a):yield f,dict(a,canonical_source_path=original,restoration_verified=self.restore is not None)
 def verify(self,path,expected,mode='strict'):
  with self.access(path,expected,mode) as (f,a):return a
 def __getattr__(self,key):return getattr(self.base,key)
class BundleStore(ProvenanceStore):
 def __init__(self,path=DATABASE,expected_sha256=DATABASE_SHA,restore=None,restore_sha256=None):
  super().__init__(path,expected_sha256=expected_sha256);self.verifier=VerifiedReferences(restore,restore_sha256)
 def set_scope(self,execution,variant):self.verifier.execution=execution;self.verifier.variant=variant
 def read_json(self,p,h,mode='verified_session'):
  with self.verifier.access(p,h,mode) as (f,a):return json.load(f),a
 def check_binding(self,b,mode):
  identity=json.loads(self.db.execute('select body from rag_env_variants where id=?',(b['variant_id'],)).fetchone()[0])
  expected='xmlenv:'+digest(dict(identity_version='1.0.0',xml_sha256=identity['xml_sha256'],asset_content_digest=identity['asset_content_digest']))
  if expected!=b['variant_id'] or digest(identity['assets'])!=b['asset_content_digest']:raise SourceError('variant_identity_mismatch')
  with self.verifier.access(b['xml_path'],b['xml_sha256'],mode) as (f,a):xml=ET.parse(f).getroot()
  assets,_=self.read_json(b['asset_manifest_path'],b['asset_manifest_sha256'],mode);raw,_=self.read_json(b['mapping_path'],b['mapping_sha256'],mode);m=raw.get('mapping',raw)
  if m['source_xml_sha256']!=b['xml_sha256'] or b['execution_id'] not in m['validated_run_ids']:raise SourceError('native_map_scope_mismatch')
  if [g['native_geom_id'] for g in m['geometries']]!=list(range(m['native_geom_count'])):raise SourceError('incomplete_native_map')
  bodies={v.get('name') for v in xml.iter('body')}
  for name,v in b['objects'].items():
   bid=v['body_id'];body=m['body_names'][bid]
   if body!=name+'_main' or body not in bodies:raise SourceError('native_object_identity_mismatch')
   if any(m['geometries'][g]['owner_body_id']!=bid for g in v['collision_geom_ids']):raise SourceError('native_geom_owner_mismatch')
   if raw.get('objects') is not None and any(raw['objects'][name][k]!=v[k] for k in ('body_id','collision_geom_ids')):raise SourceError('profile_object_mismatch')
  for asset in identity['assets']:self.verifier.verify(asset['path'],asset['sha256'],mode)
  if b.get('profile_path'):self.verifier.verify(b['profile_path'],b['profile_sha256'],mode)
  return m
