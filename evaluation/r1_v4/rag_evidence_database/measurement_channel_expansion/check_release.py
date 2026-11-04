"""Read-only final checksum and release-claims verification."""
import json
from pathlib import Path
from evaluation.r1_v4.evidence_registry_gsn.builder import sha
from .channels import HERE,WORK,BASE,BASE_SHA

def run():
 p=HERE/'ARTIFACT_MANIFEST.json';manifest=json.loads(p.read_text());expected=(HERE/'ARTIFACT_MANIFEST.sha256').read_text().split()[0];assert sha(p)==expected
 for entry in manifest['files']+manifest['external_artifacts']+[manifest['baseline_database']]:
  f=Path(entry['path']);assert f.stat().st_size==entry['bytes'] and sha(f)==entry['sha256'],str(f)
 required=['README.md','CHANNEL_INVENTORY.csv','CHANNEL_COVERAGE_MATRIX.csv','CHANNEL_SELECTION.md','EVIDENCE_CONTRACTS.md','SPATIAL_MAPPING_AUDIT.md','EXTRACTION_VALIDATION.md','RETRIEVAL_EVALUATION.md','SEMANTIC_RETRIEVAL_EVALUATION.md','REGRESSION_RESULTS.md','REPRODUCIBILITY.md','LIMITATIONS.md','ARTIFACT_MANIFEST.json']
 assert all((HERE/n).is_file() for n in required)
 summary=json.loads((HERE/'validation/SUMMARY.json').read_text());assert summary['extraction']['passed'] and summary['extraction']['raw_source_samples_validated']==348450 and summary['extraction']['max_absolute_value_error']==0
 assert summary['regression']['passed'] and summary['regression']['tests']==521 and not summary['regression']['skipped']
 tests=json.loads((HERE/'validation/CHANNEL_TESTS.json').read_text());assert tests['tests_run']==57 and tests['returncode']==0 and tests['skipped']==0
 assert sha(BASE)==BASE_SHA and manifest['counts']['total_records_across_families']==83378 and not manifest['empirical_admission_enabled']
 print(json.dumps(dict(passed=True,manifest_sha256=expected,manifest_entries_verified=len(manifest['files'])+len(manifest['external_artifacts'])+1,regression_tests=578,unexplained_failures=0,database_sha256=sha(WORK/'expanded.sqlite')),sort_keys=True),flush=True)
if __name__=='__main__':run()
