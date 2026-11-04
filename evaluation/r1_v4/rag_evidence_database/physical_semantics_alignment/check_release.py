"""Read-only artifact closure and published-count verification."""
import json
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .config import HERE,WORK

def run():
 path=HERE/'ARTIFACT_MANIFEST.json';manifest=json.loads(path.read_text());assert sha(path)==(HERE/'ARTIFACT_MANIFEST.sha256').read_text().split()[0]
 entries=manifest['files']+manifest['external_artifacts']+manifest['original_databases']+[manifest['release_database'],manifest['baseline_manifest']]
 for r in entries:
  p=Path(r['path']);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p)
 required=('README.md','MEASUREMENT_SEMANTICS_AUDIT.md','SEMANTIC_CONTRACTS.csv','PRIMARY_SOURCE_TRACEABILITY.md','TEMPORAL_ALIGNMENT.md','COORDINATE_FRAME_AUDIT.md','GEOMETRY_BINDINGS.csv','SOURCE_INTEGRITY_POLICY.md','SOURCE_TAMPERING_TESTS.md','VALIDATION_RESULTS.md','RETRIEVAL_EVALUATION.md','REGRESSION_RESULTS.md','COVERAGE_AND_LIMITATIONS.md','REPRODUCIBILITY.md','ARTIFACT_MANIFEST.json')
 assert all((HERE/p).is_file() for p in required)
 reg=json.loads((HERE/'validation/REGRESSION_RESULTS.json').read_text());assert reg['passed'] and reg['baseline_tests']==578 and reg['new_tests']==87 and reg['tests']==665 and reg['skipped']==0
 final=json.loads((HERE/'validation/FINAL_AUDIT.json').read_text());assert final['passed'] and final['database_sha256']==manifest['release_database']['sha256']
 print(json.dumps(dict(passed=True,entries_verified=len(entries),database_sha256=manifest['release_database']['sha256'],manifest_sha256=sha(path),regression_tests=665,scope='Database infrastructure; no physical-safety or empirical R1 admission')),flush=True)
if __name__=='__main__':run()
