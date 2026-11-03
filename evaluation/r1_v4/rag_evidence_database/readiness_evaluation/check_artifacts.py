"""Verify a caller-pinned evaluation manifest plus the unchanged parent release."""
import json,argparse
from pathlib import Path
from evaluation.r1_v4.rag_evidence_database.physical_semantics_alignment.source_integrity import SourceVerifier,SourceError
from evaluation.r1_v4.rag_evidence_database.source_reproducibility.check_release import verify as parent_verify
from .config import HERE,WORK
from .harness import frozen_check

def verify(expected):
 v=SourceVerifier();p=HERE/'ARTIFACT_MANIFEST.json'
 with v.access(str(p),expected,'strict') as (f,a):manifest=json.load(f)
 checked=0
 for row in manifest['artifacts']:
  with v.access(row['path'],row['sha256'],'strict') as (f,a):
   if __import__('os').fstat(f.fileno()).st_size!=row['bytes']:raise SourceError('evaluation_artifact_size_mismatch')
  checked+=1
 frozen_check();h=json.loads((HERE/'HARNESS_VERSION.json').read_text())
 from evaluation.r1_v4.evidence_registry_gsn.builder import sha
 for n,value in h['files'].items():assert sha(HERE/n)==value,n
 parent=parent_verify(HERE.parent/'source_reproducibility'/'ARTIFACT_MANIFEST.json','d9953192386904e5778050b89770e0f4693c9c86e6cc9ba3b622826e7fe93e93','provenance')
 return dict(passed=True,manifest_sha256=expected,evaluation_artifacts_verified=checked,parent_artifacts_verified=parent['checked'],parent_frozen=parent['frozen'],recommendation='B',known_invalid_sufficiency_cases=['C7-06','C7-20'],rankings_and_acceptance_criteria_unchanged=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--sha256',required=True);a=p.parse_args();print(json.dumps(verify(a.sha256),sort_keys=True))
