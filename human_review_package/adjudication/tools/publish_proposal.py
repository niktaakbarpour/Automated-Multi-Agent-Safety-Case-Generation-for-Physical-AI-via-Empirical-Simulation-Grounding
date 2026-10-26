"""Create/verify a public PROPOSAL snapshot; never approve or freeze labels.

Private evidence and the original proposal are read-only inputs. Publication
redactions are explicit and versioned; no scientific labels/statistics change.
Only the enumerated small text files can be exported. No media is copied.
"""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import re

if not __debug__:
    raise RuntimeError('Do not disable publication validation with Python -O')

COPY_FILES = [
    'alignment_report.csv', 'disagreements.csv', 'evidence_review.csv',
    'adjudication_decisions.csv', 'agreement_statistics.json', 'approval_template.csv',
    'provisional_initial_support.csv', 'provisional_events.csv',
    'provisional_requirement_interpretation.csv', 'provisional_uncertainty_requests.csv',
]
PRIVATE_PATTERN = re.compile(r'/(?:Users|local/home|disk|private|eecs|cs/home)/|[A-Za-z]:\\Users\\',re.I)
SECRET_PATTERN = re.compile(r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16})\b')
PRIVATE_PREFIX = 'adjudication/evidence_'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def readcsv(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))


def writejson(path,data):
    Path(path).write_text(json.dumps(data,sort_keys=True,indent=2,ensure_ascii=False)+'\n')


def scan(text):
    assert not PRIVATE_PATTERN.search(text),'private absolute filesystem path'
    assert not SECRET_PATTERN.search(text),'credential-shaped content'


def verify(package,publication):
    package=Path(package).resolve();publication=Path(publication).resolve()
    assert all(p.is_file() and not p.is_symlink() and p.suffix in ['.csv','.json','.md'] and p.stat().st_size<2*1024**2 for p in publication.iterdir()),'unexpected binary, directory, symlink or oversized public artifact'
    sums=json.loads((publication/'publication_checksums.json').read_text())
    assert set(sums)=={p.name for p in publication.iterdir() if p.is_file() and p.name!='publication_checksums.json'},'public artifact inventory changed'
    for name,expected in sums.items():
        assert Path(name).name==name and (publication/name).is_file(),'invalid public path'
        assert sha(publication/name)==expected,('public checksum mismatch',name)
        scan((publication/name).read_text())
    manifest=json.loads((publication/'dataset_manifest.json').read_text())
    assert manifest['schema_version']=='r1-adjudication-publication-v1'
    assert manifest['status']=='provisional_pending_human_approval_not_frozen'
    assert manifest['adjudicator_identity'] is None and manifest['approval_date'] is None
    assert manifest['finalized_labels_sha256'] is None
    decisions=readcsv(publication/'adjudication_decisions.csv')
    assert len(decisions)==90 and len({r['adjudication_id'] for r in decisions})==90
    assert all(r['human_approval_status']=='pending' and not r['adjudicator_identity'] and not r['approval_date'] for r in decisions)
    assert manifest['decision_counts']['approved']==0 and manifest['decision_counts']['pending']==90
    assert len([r for r in decisions if r['table']=='uncertainty_requests'])==11
    source_rows=collections.defaultdict(list)
    ids={r['adjudication_id'] for r in decisions}
    for row in decisions:
        for side in ['reviewer_1','reviewer_2']:
            source_rows[f'{side}/{row["table"]}.csv'].extend(json.loads(row[f'{side}_original_rows']))
        for ref in json.loads(row['evidence_references']):
            if ref.startswith(PRIVATE_PREFIX):
                assert ref in manifest['private_evidence_references'],'undeclared private evidence'
            else:
                p=(package/ref).resolve()
                assert p.is_relative_to(package) and p.is_file(),('missing public evidence reference',ref)
    for name,expected in manifest['source_file_sha256'].items():
        assert sha(package/name)==expected,('original reviewer source changed',name)
        actual=readcsv(package/name)
        encode=lambda r:json.dumps(r,sort_keys=True,ensure_ascii=False)
        assert collections.Counter(map(encode,actual))==collections.Counter(map(encode,source_rows[name])),('source row lost/changed',name)
    for name,expected in manifest['public_evidence_file_sha256'].items():
        assert sha(package/name)==expected,('public evidence changed',name)
    for table in ['initial_support','events','requirement_interpretation','uncertainty_requests']:
        rows=readcsv(publication/f'provisional_{table}.csv')
        assert {r['adjudication_id'] for r in rows}=={r['adjudication_id'] for r in decisions if r['table']==table}
        assert all(r['human_approval_status']=='pending' for r in rows)
    approvals=readcsv(publication/'approval_template.csv')
    assert {r['adjudication_id'] for r in approvals}==ids
    byid={r['adjudication_id']:r for r in decisions}
    for row in approvals:
        assert row['disposition']=='pending' and not row['adjudicator_identity'] and not row['approval_date'] and not row['reason']
        canonical=json.dumps(byid[row['adjudication_id']],sort_keys=True,ensure_ascii=False,separators=(',',':'))
        assert row['proposal_sha256']==hashlib.sha256(canonical.encode()).hexdigest(),'approval binding changed'
    alignment=readcsv(publication/'alignment_report.csv')
    assert {r['adjudication_id'] for r in alignment}==ids
    differences=readcsv(publication/'disagreements.csv')
    expected={r['adjudication_id'] for r in alignment if not r['classification'].endswith('_agreement') and r['table']!='uncertainty_requests'}
    assert {r['adjudication_id'] for r in differences}==expected and len(differences)==38
    assert {r['adjudication_id'] for r in readcsv(publication/'evidence_review.csv')}==ids
    stats=json.loads((publication/'agreement_statistics.json').read_text())
    assert stats['total_source_rows']==160 and stats['aligned_units']==90
    assert stats['agreements']==41 and stats['paired_comparable_units']==66 and stats['all_difference_units']==38
    assert sha(publication/'agreement_statistics.json')==manifest['original_proposal_artifact_sha256']['agreement_statistics.json'],'statistics changed during publication'
    # Identity and physical-event references remain anchored to the originals.
    scope=json.loads((package/'requirement_scope.v3.json').read_text())
    runs={r['run_id']:r for r in json.loads((package/'evidence_manifest.json').read_text())['runs']}
    event_ids={side:{r['event_id']:(r['run_id'],r['object_id']) for r in readcsv(package/side/'events.csv')} for side in ['reviewer_1','reviewer_2']}
    for row in decisions:
        assert row['run_id'] in runs and row['episode']==runs[row['run_id']]['episode']
        assert row['object_id'] in scope['protected_objects']+['']
        assert row['requirement_version']==scope['requirement_version']
        if row['table']=='requirement_interpretation':
            for side in event_ids:
                for original in json.loads(row[f'{side}_original_rows']):
                    for event in filter(None,original.get('physical_event_id','').split(';')):
                        assert event_ids[side].get(event.strip())==(row['run_id'],row['object_id'])
    return dict(source_rows=160,alignment_units=90,pending_decisions=90,difference_units=38,uncertainty_requests=11,
                private_evidence_included=False,scientific_evidence_revalidated=False)


def build(package,proposal,out):
    import importlib.util
    package=Path(package).resolve();proposal=Path(proposal).resolve();out=Path(out).resolve()
    assert not out.exists(),'new publication version required; never overwrite a package'
    spec=importlib.util.spec_from_file_location('private_adjudication',Path(__file__).with_name('adjudicate.py'))
    core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    private,decisions=core.verify(package,proposal)
    assert len(decisions)==90 and all(r['human_approval_status']=='pending' for r in decisions)
    # Validate the entire private input first; public reference checks do not imply
    # that absent evidence was re-inspected by a reader of the public repository.
    originals={p.name:sha(p) for p in proposal.iterdir() if p.is_file()}
    out.mkdir(parents=True)
    for name in COPY_FILES:
        content=(proposal/name).read_bytes();scan(content.decode())
        (out/name).write_bytes(content)
    public_refs={name:h for name,h in private['evidence_file_sha256'].items() if not name.startswith(PRIVATE_PREFIX)}
    private_refs={name:h for name,h in private['evidence_file_sha256'].items() if name.startswith(PRIVATE_PREFIX)}
    recording_refs={ep:dict(recording_ref=f'recording://{ep}/trajectory.h5',
                           trajectory_sha256=data['trajectory_sha256'],trajectory_bytes=data['trajectory_bytes'],
                           source_stat_unchanged=data['source_stat_unchanged'])
                    for ep,data in private['recording_provenance'].items()}
    manifest=dict(schema_version='r1-adjudication-publication-v1',status='provisional_pending_human_approval_not_frozen',
                  source_base_commit=private['source_base_commit'],requirement_version=private['requirement_version'],
                  annotation_schema=private['annotation_schema'],requirement_scope_sha256=private['requirement_scope_sha256'],
                  reviewer_provenance=private['reviewer_provenance'],source_file_sha256=private['source_file_sha256'],
                  public_evidence_file_sha256=public_refs,private_evidence_references=private_refs,
                  runs=private['runs'],protected_objects=private['protected_objects'],recording_provenance=recording_refs,
                  decision_counts=private['decision_counts'],adjudicator_identity=None,approval_date=None,finalized_labels_sha256=None,
                  source_proposal_manifest_sha256=sha(proposal/'dataset_manifest.json'),original_proposal_artifact_sha256=originals,
                  script_sha256={p.name:sha(p) for p in sorted(Path(__file__).parent.glob('*.py'))},
                  evidence_access='Private excerpts/contact sheets are excluded. Hashes and logical references only; public verification cannot revalidate their scientific contents.',
                  finalization='Use the unchanged private proposal with restored authorized evidence and explicit human approval. This publication snapshot is deliberately not accepted by the finalizer.')
    writejson(out/'dataset_manifest.json',manifest)
    redactions=dict(schema_version='r1-publication-redactions-v1',source_manifest_sha256=manifest['source_proposal_manifest_sha256'],
                    unchanged_scientific_artifacts=COPY_FILES,
                    changes=[dict(field='recording_provenance.*.source_directory',action='Replace private absolute locations with episode-scoped recording:// logical references; recording hashes retained.'),
                             dict(field='native_mapping',action='Exclude detailed evidence-derived inventory; original XML hashes and public native_geometry.csv references retained.'),
                             dict(field='recording_provenance.*.supporting_source_hashes_and_csv_schemas',action='Exclude private extraction metadata; original recording/XML hashes retained.'),
                             dict(field='evidence_file_sha256',action='Separate public hashes from unavailable private evidence references; no payloads copied.'),
                             dict(field='proposal_checksums.json',action='Retain original checksum as provenance hash; generate separate checksums for this publication version.'),
                             dict(field='README.md, adjudication_report.md',action='Add publication access limitations and prevent confusing publication approval with adjudication approval.')],
                    statistics_unchanged=True,decisions_unchanged=True,original_submissions_unchanged=True)
    writejson(out/'redaction_map.json',redactions)
    notice=('> **Public provisional snapshot.** All 90 decisions remain pending Nikta’s approval; no dataset is frozen. '
            'Private evidence excerpts and contact sheets are intentionally excluded. References to them are provenance identifiers, not publicly accessible files. '
            'The reviewer-source comparison and hashes can be checked publicly; scientific re-inspection and authoritative finalization require authorized access to the original private evidence. '
            'See `redaction_map.json` for the explicit publication transformation.\n\n')
    report=(proposal/'adjudication_report.md').read_text()
    report=report.replace('Raw excerpts, contact sheets and all generated outputs remain uncommitted under the latest instruction.',
                          'Raw excerpts and contact sheets remain excluded; publication of this provisional snapshot does not approve adjudication labels.')
    report=report.replace('Separately approve a publication allowlist.','Publication is authorized for the reviewed safe allowlist only.')
    (out/'adjudication_report.md').write_text(notice+report)
    (out/'README.md').write_text('''# Public R1 proposed adjudication

All **90 decisions are pending**; no human-reference dataset is frozen. Original reviewer CSVs remain unchanged. Statistics and scientific decision ledgers are byte-identical to the private proposal. See adjudication_report.md, agreement_statistics.json, evidence_review.csv and adjudication_decisions.csv.

Private raw JSON/CSV excerpts and twelve contact sheets are excluded. The manifest lists their hashes and logical references, clearly marked unavailable in the public snapshot. It contains no private absolute recording locations or raw native-object inventory. redaction_map.json documents the transformation; original private proposal hashes are retained without its private paths. Existing authorized reviewer submissions and previously published evidence references are not re-added or modified by this change.

From the repository root:

```sh
python3 human_review_package/adjudication/tools/publish_proposal.py verify --publication human_review_package/adjudication/publication_20261026
python3 -m unittest discover -s human_review_package/adjudication/tests -v
```

The public verifier checks source-file hashes, lossless annotation representation, approval bindings, run/object/event references, unchanged statistics, pending status, checksum inventory and publication safety. It does **not** independently validate excluded scientific evidence. Private-evidence integration tests run when authorized excerpts are present; otherwise they explicitly skip. Portable source-comparison/publication tests remain available.

Approval_template.csv is still pending. Proposed labels and references are prefilled for review, not signed off. Nikta must explicitly approve, correct or preserve uncertainty, with attributable identity/date/rationale. The episode-014 cream-cheese interpretation remains conditional on her support/carrying confirmation. All eleven uncertainty requests and sampling/visibility/causation limitations remain.

Do not finalize from this redacted snapshot. It deliberately lacks the private finalizer’s proposal format and approval context. With authorized evidence restored, a coordinator first verifies the original private proposal and applies actual human decisions to a copied approval ledger. Only after approval, run from the repository root:

```sh
python3 human_review_package/adjudication/tools/adjudicate.py finalize --proposal human_review_package/adjudication/proposed_20261026 --approvals nikta_reviewed_approvals.csv --output-root versioned-reference
```

That command has **not** been executed on the real dataset. Synthetic approval/export tests use temporary directories only. Original source annotations are never overwritten; unresolved cases stay explicit. Adjudicated consensus is not independent inter-rater reliability, and neither these selected executions nor the reference labels establish detector accuracy or real-world safety.

To reproduce this publication transformation, use the unchanged authorized private proposal and a NEW output directory:

```sh
python3 human_review_package/adjudication/tools/publish_proposal.py build --proposal human_review_package/adjudication/proposed_20261026 --out publication-reproduction
```
''')
    writejson(out/'publication_checksums.json',{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()})
    assert originals=={p.name:sha(p) for p in proposal.iterdir() if p.is_file()},'private proposal changed'
    return verify(package,out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package',type=Path,default=Path(__file__).resolve().parents[2])
    sub=p.add_subparsers(dest='cmd',required=True)
    b=sub.add_parser('build');b.add_argument('--proposal',type=Path,required=True);b.add_argument('--out',type=Path,required=True)
    v=sub.add_parser('verify');v.add_argument('--publication',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(build(a.package,a.proposal,a.out) if a.cmd=='build' else verify(a.package,a.publication),indent=2))
