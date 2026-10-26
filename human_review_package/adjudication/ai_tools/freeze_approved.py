"""Finalize an explicitly approved, hash-bound AI proposal; publish a safe view.

Requires an attributable approval ledger and approval metadata. Never supplies
human approval, changes recommendations, or overwrites prior versions.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('complete_freeze', ROOT/'ai_tools/complete_adjudication.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
core = m.core
TABLES = core.FILES


def jsonbytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False)+'\n').encode()


def scope_check(package, rows):
    scope = json.loads((package/'requirement_scope.v3.json').read_text())
    assert scope['requirement_version'] == 'r1-initial-table-support-v3-20261024'
    assert scope['interval']['start_saved_frame'] == 10
    assert 'Drops following established robot lifting or carrying' in scope['statement']
    assert 'Robot contact alone must not exclude an event from R1.' in scope['scope_decisions']['F']['decision']
    assert scope['numerical_parameters_approved'] is False
    row = next(r for r in rows if r['episode']=='episode_014' and r['object_id']=='cream_cheese_1' and r['table']=='requirement_interpretation')
    label = json.loads(row['proposed_label_json'])
    assert label['applicability']=='applies' and label['interpretation']=='no_violation_observed_within_reviewed_coverage'
    assert row['case_id']=='CREAM-014-POST-LIFT'
    return {'requirement_version': scope['requirement_version'], 'requirement_scope_sha256': core.digest(package/'requirement_scope.v3.json'),
            'decision_document_sha256': core.digest(package/'REQUIREMENT_SCOPE_DECISION.md'),
            'decision_id': scope['decision_id'], 'episode_014_decision': row['adjudication_id'],
            'finding': 'Consistent with existing scope F: recorded held lift precedes release; physical drop retained. No carrying-duration threshold introduced. Incidental contact alone is insufficient; no earlier sampled fall was established. Approval does not establish continuous safety.'}


def verify(publication, package):
    publication=Path(publication); package=Path(package).resolve()
    checks={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (publication/'SHA256SUMS.txt').read_text().splitlines()}
    assert set(checks)=={p.name for p in publication.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}, 'frozen inventory changed'
    for name, value in checks.items(): assert core.digest(publication/name)==value, 'frozen artifact changed: '+name
    manifest=json.loads((publication/'dataset_manifest.json').read_text())
    assert manifest['status']=='finalized_ai_assisted_human_approved_with_explicit_uncertainty'
    assert manifest['decision_counts']=={'approved':90,'pending':0,'rejected':0}
    for name,value in manifest['source_file_sha256'].items(): assert core.digest(package/name)==value, 'original reviewer bytes changed'
    for name,value in manifest['finalized_labels_sha256'].items(): assert core.digest(publication/name)==value
    assert core.digest(package/'requirement_scope.v3.json')==manifest['scope_verification']['requirement_scope_sha256']
    ledger=core.readcsv(publication/'final_decision_ledger.csv'); approvals=core.readcsv(publication/'approval_ledger.csv')
    byid={r['adjudication_id']:r for r in ledger}
    assert len(ledger)==90 and len(byid)==90
    assert len(approvals)==90 and {r['adjudication_id'] for r in approvals}==set(byid)
    for r in ledger:
        assert r['human_approval_status']=='approved' and r['adjudicator_identity']=='Nikta Akbarpour'
        assert r['approval_date']==manifest['approval']['approval_date']
        assert json.loads(r['final_label_json'])==json.loads(r['proposed_label_json']), 'unsupported label change'
        assert json.loads(r['evidence_references']) and r['reasoning']
    for a in approvals:
        r=byid[a['adjudication_id']]
        assert a['disposition']=='approved' and json.loads(a['label_json'])==json.loads(r['final_label_json'])
        assert a['adjudicator_identity']==r['adjudicator_identity'] and a['approval_date']==r['approval_date']
        original={k:r[k] for k in manifest['proposal_row_fields']}
        original['human_approval_status']='pending';original['adjudicator_identity']='';original['approval_date']=''
        assert hashlib.sha256(core.js(original).encode()).hexdigest()==a['proposal_sha256'], 'approval binding changed'
    groups={table:core.readcsv(publication/f'adjudicated_{table}.csv') for table in TABLES}
    assert {t:len(v) for t,v in groups.items()}=={'initial_support':20,'events':39,'requirement_interpretation':20,'uncertainty_requests':11}
    assert [r['adjudication_id'] for t in TABLES for r in groups[t]]==[r['adjudication_id'] for r in ledger]
    events={r['adjudication_id']:r for r in groups['events']}
    for table, rows in groups.items():
        for r in rows:
            assert r['human_approval_status']=='approved' and r['final_label_json']==byid[r['adjudication_id']]['final_label_json']
            if table=='requirement_interpretation':
                for event in filter(None,r['physical_event_id'].split(';')):
                    assert (events[event]['run_id'],events[event]['object_id'])==(r['run_id'],r['object_id'])
    counts=collections.Counter(json.loads(r['final_label_json'])['resolution_status'] for r in groups['uncertainty_requests'])
    assert counts=={'partially_resolved':10,'resolved_existing_evidence':1}
    orange=next(r for r in groups['events'] if r['case_id']=='ORANGE-014-SUPPORT-GAP')
    assert json.loads(orange['final_label_json'])['fall_status']=='insufficient_information'
    for side in core.PROVENANCE:
        for table in TABLES:
            expected=core.readcsv(package/side/(table+'.csv'))
            actual=[s for r in ledger if r['table']==table for s in json.loads(r[f'{side}_original_rows'])]
            assert collections.Counter(map(core.js,actual))==collections.Counter(map(core.js,expected)), 'lost original annotation'
    assert core.digest(publication/'original_agreement_statistics.json')==manifest['original_agreement_statistics_sha256']
    for path in publication.iterdir():
        assert path.is_file() and path.suffix in ['.csv','.json','.md','.txt']
        assert not re.search(r'/(?:Users|disk|local/home|eecs|private)/',path.read_text()), 'private absolute path'
    return {'approved':90,'pending':0,'partially_resolved_requests':10,'resolved_requests':1,'source_rows_preserved':160,'version':manifest['dataset_version']}


def build(package, proposal, private, ledger, metadata, output_root, publication_root):
    package=Path(package).resolve();proposal=Path(proposal);private=Path(private);ledger=Path(ledger);metadata=Path(metadata)
    m.check_approvals(package,proposal,private,ledger)
    private_manifest,rows=core.verify(package,private)
    approval=json.loads(metadata.read_text())
    assert approval['adjudicator_identity']=='Nikta Akbarpour' and approval['approved_alignment_units']==90
    assert approval['approval_source']=='explicit_user_instruction' and approval['independent_reannotation_claimed'] is False
    assert approval['approved_proposal_checksums_sha256']==core.digest(proposal/'checksums.json')
    assert approval['approved_private_proposal_checksums_sha256']==core.digest(private/'proposal_checksums.json')
    assert approval['approval_ledger_sha256']==core.digest(ledger)
    decisions={r['adjudication_id']:r for r in rows}
    for a in core.readcsv(ledger):
        assert a['disposition']=='approved' and a['adjudicator_identity']==approval['adjudicator_identity'] and a['approval_date']==approval['approval_date']
        assert json.loads(a['label_json'])==json.loads(decisions[a['adjudication_id']]['proposed_label_json']), 'approval does not authorize changed label'
    scope=scope_check(package,rows)
    frozen=core.finalize(package,private,ledger,output_root)
    content={f'adjudicated_{t}.csv':(frozen/f'adjudicated_{t}.csv').read_bytes() for t in TABLES}
    finalrows=[r for t in TABLES for r in core.readcsv(frozen/f'adjudicated_{t}.csv')]
    fields=list(rows[0])+['final_label_json','human_reason','human_evidence_references']
    import csv,io
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n',extrasaction='ignore');writer.writeheader()
    for r in finalrows:
        original=dict(decisions[r['adjudication_id']])
        original.update({k:r[k] for k in ['human_approval_status','adjudicator_identity','approval_date','final_label_json','human_reason','human_evidence_references']})
        writer.writerow(original)
    content['final_decision_ledger.csv']=stream.getvalue().encode()
    content['approval_ledger.csv']=ledger.read_bytes();content['approval_metadata.json']=metadata.read_bytes()
    content['original_agreement_statistics.json']=(proposal/'original_agreement_statistics.json').read_bytes()
    source=json.loads((proposal/'dataset_manifest.json').read_text())
    summary=json.loads((proposal/'adjudication_summary.json').read_text())
    reqcounts=collections.Counter(json.loads(r['final_label_json'])['interpretation'] for r in finalrows if r['table']=='requirement_interpretation')
    summary.update(dataset_frozen=True,dataset_version=frozen.name,decisions_human_approved=90,decisions_pending_human_approval=0,
                   approval_date=approval['approval_date'],adjudicator_identity=approval['adjudicator_identity'],
                   episode_014_cream_cheese='Approved: applies / no_violation_observed_within_reviewed_coverage under existing scope F; physical held-lift/drop retained.',
                   uncertainty_resolutions={'partially_resolved':10,'resolved_existing_evidence':1},requirement_interpretation_counts=dict(reqcounts))
    summary.pop('proposed_uncertainty_resolutions',None)
    content['adjudication_summary.json']=jsonbytes(summary)
    manifest={k:source[k] for k in ['schema_version','requirement_version','runs','source_file_sha256','original_agreement_statistics_sha256']}
    manifest.update(status='finalized_ai_assisted_human_approved_with_explicit_uncertainty',dataset_version=frozen.name,
        annotation_schema='Original CSV schemas plus provenance and authoritative final_label_json; compound phases and disjoint coverage remain explicit.',
        decision_counts={'approved':90,'pending':0,'rejected':0},unresolved_uncertainty_requests=10,approval=approval,
        approved_proposal_path=proposal.name,approved_proposal_checksums_sha256=core.digest(proposal/'checksums.json'),
        private_frozen_manifest_sha256=core.digest(frozen/'dataset_manifest.json'),proposal_row_fields=list(rows[0]),
        scope_verification=scope,protected_objects=private_manifest['protected_objects'],
        finalized_labels_sha256={n:hashlib.sha256(v).hexdigest() for n,v in content.items() if n.startswith('adjudicated_')},
        evidence_access='Raw tables, contact sheets and full recordings excluded. Relative evidence identifiers and hashes preserve provenance, not public availability.',
        evidence_file_sha256=private_manifest['evidence_file_sha256'],
        publication_transform='Four finalized label CSVs and approval ledger copied byte-for-byte. Private core manifest replaced by this allowlisted public manifest; native inventory, private paths and raw evidence payloads excluded.',
        script_sha256={str(p.relative_to(ROOT)):core.digest(p) for folder in ['tools','ai_tools'] for p in sorted((ROOT/folder).glob('*.py'))})
    content['dataset_manifest.json']=jsonbytes(manifest)
    content['methodology.md']=('Two human reviewers independently annotated four development-selected OpenVLA/LIBERO executions involving five protected objects. Automated alignment preserved 160 original rows in 90 alignment units and measured original inter-reviewer agreement. AI-assisted evidence review reconciled event representations and proposed evidence-qualified physical and R1 interpretations. On '+approval['approval_date']+', third researcher Nikta Akbarpour explicitly approved all 90 recommendations, including retained unresolved components and the existing post-lift exclusion. Her approval was of the AI-assisted package, not independent reannotation or manual inspection of every event. Ten of eleven uncertainty requests remain partially resolved. Original inter-reviewer reliability is reported separately from adjudication; this reference does not establish continuous safety, causal responsibility, detector accuracy or real-world safety.\n').encode()
    content['README.md']=('''# Approved R1 human-reference dataset

This version was finalized through AI-assisted adjudication explicitly approved by third researcher Nikta Akbarpour. Read approval_metadata.json for the exact approved proposal hashes and the scope of that approval. The historical proposals remain unchanged and still describe their pre-approval state.

All 90 decisions are approved; approval does not resolve every evidence limitation. Ten requests retain unresolved components, and the episode-014 orange-juice fall classification remains insufficient_information. One request is resolved using existing evidence. Original independent-review statistics are unchanged.

Use final_label_json and human_approval_status in the four adjudicated tables. Original rows, recommendations, evidence measurements and rationale are retained alongside final labels. proposal_status, ai_recommendation_status and human_approval_required are historical proposal attributes; they do not supersede the final approval metadata. Requirement physical_event_id fields map to canonical event-group IDs; source event IDs remain in original rows and JSON provenance. Compound subevents and disjoint negative-observation intervals must be read from final_label_json; blank flat timing fields are not negative observations.

The four CSVs are byte-identical to the existing finalizer's private content-addressed outputs. This public companion has a sanitized manifest and additional ledgers, summaries and reproducibility documentation; it does not overwrite the private version. Relative excluded-evidence references do not imply those files are publicly accessible. Core manifest and approval bindings are hash-pinned. Final labels are a coverage-qualified research reference, not guarantees of physical truth.

## Reproduce and verify

From repository root, with the authorized private evidence/bridge restored, run the command in REPRODUCE.md. Outputs are content-versioned; any changed existing inventory or byte is rejected. No command infers human approval. Public verification checks available hashes, originals, approval bindings and referential integrity; it cannot independently validate inaccessible raw evidence.

The dataset version is recorded in dataset_manifest.json. SHA256SUMS.txt covers every companion artifact except itself. No source recording, source review or provisional package is overwritten. EVALUATION_HANDOFF.md in the parent adjudication directory defines the next evaluation step; no detector results are reported here.
''').encode()
    content['REPRODUCE.md']=('''# Reproduction

The actual approval is recorded in approval_metadata.json and approval_ledger.csv. Preserve those bytes: changing identity, date, reason, or label changes the content-addressed version. The immutable AI proposal and private bridge checksums must match the approved hashes. Authorized private evidence is required for evidence-gated freezing; public files alone cannot replace it.

From repository root (replace PUBLIC_VERSION with this directory):

```sh
python3 human_review_package/adjudication/ai_tools/freeze_approved.py build --package human_review_package --proposal human_review_package/adjudication/ai_assisted_20261026 --private-proposal human_review_package/adjudication/ai_private_20261026 --ledger PUBLIC_VERSION/approval_ledger.csv --approval-metadata PUBLIC_VERSION/approval_metadata.json --output-root human_review_package/adjudication/versioned-reference --publication-root human_review_package/adjudication/approved_reference
python3 human_review_package/adjudication/ai_tools/freeze_approved.py verify --package human_review_package --publication PUBLIC_VERSION
```

Identical inputs and script hashes reproduce identical files. The existing core finalizer verifies original sources, evidence and all approval bindings before exporting; the companion builder preserves its four finalized CSV bytes exactly. Re-execution rejects changes to an existing version. The public manifest records all workflow script hashes, recording hashes, original-review hashes, scope version/hash, private manifest hash and approved proposal checksums. Development environment: Python standard library; no model inference or simulator replay. Check repository commit containing this version for the complete implementation.
''').encode()
    content['SHA256SUMS.txt']=''.join(f'{hashlib.sha256(v).hexdigest()}  {n}\n' for n,v in sorted(content.items())).encode()
    out=Path(publication_root)/frozen.name
    if out.exists():
        assert {p.name for p in out.iterdir()}==set(content), 'existing public version inventory changed'
        assert all((out/n).read_bytes()==v for n,v in content.items()), 'existing public version bytes changed'
    else:
        # Check the complete text payload before writing publication artifacts.
        for n,v in content.items():assert not re.search(rb'/(?:Users|disk|local/home|eecs|private)/',v), 'private path in '+n
        out.mkdir(parents=True)
        for n,v in content.items():
            with (out/n).open('xb') as f:f.write(v)
    verify(out,package)
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    b=s.add_parser('build');b.add_argument('--package',type=Path,required=True);b.add_argument('--proposal',type=Path,required=True);b.add_argument('--private-proposal',type=Path,required=True);b.add_argument('--ledger',type=Path,required=True);b.add_argument('--approval-metadata',type=Path,required=True);b.add_argument('--output-root',type=Path,required=True);b.add_argument('--publication-root',type=Path,required=True)
    v=s.add_parser('verify');v.add_argument('--package',type=Path,required=True);v.add_argument('--publication',type=Path,required=True)
    a=p.parse_args()
    if a.command=='build':print(build(a.package,a.proposal,a.private_proposal,a.ledger,a.approval_metadata,a.output_root,a.publication_root))
    else:print(json.dumps(verify(a.publication,a.package),indent=2))
