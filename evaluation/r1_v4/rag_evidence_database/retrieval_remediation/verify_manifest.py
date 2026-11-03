"""Verify a caller-trusted release manifest and every declared artifact, fail closed."""
import json,argparse,os
from pathlib import Path
from .store import SourceVerifier
from .config import HERE

def verify(expected):
 v=SourceVerifier(namespace='phase5k-release-manifest-verification')
 with v.access(str(HERE/'ARTIFACT_MANIFEST.json'),expected,'strict') as (fd,a):manifest=json.load(fd)
 count=0
 for group in ('internal_artifacts','external_artifacts','trust_roots'):
  for artifact in manifest[group]:
   with v.access(artifact['path'],artifact['sha256'],'strict') as (fd,a):assert os.fstat(fd.fileno()).st_size==artifact['bytes'],artifact['path']
   count+=1
 print(json.dumps(dict(passed=True,manifest_sha256=expected,verified_artifacts=count,policy='descriptor-bound no-follow; trusted hash supplied separately')),flush=True)
 return count
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--sha256',required=True);a=p.parse_args();verify(a.sha256)
