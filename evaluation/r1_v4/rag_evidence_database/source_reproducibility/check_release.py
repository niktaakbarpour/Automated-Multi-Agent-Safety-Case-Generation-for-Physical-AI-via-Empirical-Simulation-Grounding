"""Verify a pinned manifest; a newly calculated hash is not a historical attestation."""
import json,argparse
from pathlib import Path
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier,SourceError
from evaluation.r1_v4.rag_evidence_database.measurement_channel_expansion.channels import owned
from .config import HERE

def verify(manifest,expected_sha256,scope='metadata'):
 if scope not in ('metadata','sources','provenance'):raise ValueError('unknown verification scope')
 v=SourceVerifier(roots=('/disk/1/data/niktakbr','/disk/0/home/niktakbr','/usr/bin','/usr/lib','/usr/lib64'))
 with v.access(str(manifest),expected_sha256,'strict') as (f,a):m=json.load(f)
 checked=0
 for row in m['artifacts']:
  if row['required_for']=='provenance' and scope!='provenance':continue
  if row['required_for']=='sources' and scope=='metadata':continue
  p=row['path']
  if p.startswith('/local/'):p=str(owned(p))
  with v.access(p,row['sha256'],'strict') as (f,a):
   if row.get('bytes') is not None and __import__('os').fstat(f.fileno()).st_size!=row['bytes']:raise SourceError('release_size_mismatch')
  checked+=1
 from evaluation.r1_v4.integrity import verify as frozen_verify
 frozen=frozen_verify()
 return dict(passed=True,scope=scope,checked=checked,manifest_sha256=expected_sha256,historical_execution_attested=False,frozen=frozen)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--manifest',default=str(HERE/'ARTIFACT_MANIFEST.json'));p.add_argument('--sha256',required=True);p.add_argument('--scope',choices=['metadata','sources','provenance'],default='metadata');a=p.parse_args();print(json.dumps(verify(Path(a.manifest),a.sha256,a.scope),sort_keys=True))
