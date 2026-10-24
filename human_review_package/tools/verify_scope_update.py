"""Validate scope provenance and blank review templates; never infer physical labels."""
import csv
import json
import re
from pathlib import Path
from jsonschema import Draft202012Validator

F = {'record_id','episode','run_id','object_id','requirement_version','evidence_links','reviewer_copy'}
EXTRA = {'review_start_frame','review_end_frame','evidence_coverage','supporting_frame_references','confidence_uncertainty'}

def validate_scope(scope, schema):
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(scope)

def read_template(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        r = csv.DictReader(f)
        assert F | EXTRA <= set(r.fieldnames), 'Missing scope/coverage fields'
        rows = list(r)
    for row in rows:
        assert all(not v for k,v in row.items() if k not in F), 'Human fields must remain blank in distributed templates'
    return rows

def verify(root):
    scope = json.loads((root/'requirement_scope.v3.json').read_text())
    schema = json.loads((root/'schemas/requirement_scope.v1.schema.json').read_text())
    validate_scope(scope, schema)
    decision = (root/'REQUIREMENT_SCOPE_DECISION.md').read_text()
    for text in [scope['statement'], scope['decision_origin'], scope['decision_id'], scope['requirement_version'], scope['update_date']]:
        assert text in decision
    for key, entry in scope['scope_decisions'].items():
        assert f'{key}. {entry["title"]}' in decision
        assert entry['decision'] in decision and entry['reason'] in decision
    for q in scope['remaining_questions']:
        assert q in decision
    copies = [read_template(root/f'reviewer_{i}/requirement_interpretation.csv') for i in (1,2)]
    expected = set(scope['protected_objects'])
    for rows in copies:
        assert len(rows) == 20
        runs = {r['run_id'] for r in rows}
        assert len(runs) == 4
        for run in runs:
            assert {r['object_id'] for r in rows if r['run_id'] == run} == expected
        assert all(r['requirement_version'] == scope['requirement_version'] for r in rows)
    for a,b in zip(*copies):
        a = dict(a); b = dict(b)
        assert a.pop('reviewer_copy') == 'reviewer_1'
        assert b.pop('reviewer_copy') == 'reviewer_2'
        assert a == b
    with (root/'adjudication/final_labels.csv').open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        assert {'original_review_1_reference','original_review_2_reference','original_review_1_sha256','original_review_2_sha256','original_review_1_answer_verbatim','original_review_2_answer_verbatim','reasoning','remaining_uncertainty','requirement_version','requirement_applicability','requirement_interpretation','evidence_coverage'} <= set(reader.fieldnames)
        assert not list(reader), 'Adjudication is not prefilled'
    for path in [root/'README.md',root/'REQUIREMENT_FOR_REVIEW.md',root/'REVIEW_INSTRUCTIONS.md',root/'reviewer_1/README.md',root/'reviewer_2/README.md',root/'adjudication/README.md']:
        text = path.read_text()
        assert 'REQUIREMENT_SCOPE_DECISION.md' in text
        assert not re.search(r'(?:scope is agreed by all three|team agrees on scope|All three settle requirement scope)', text)
    print('PASS: scope schema, exact decisions/provenance, separate pending statuses, all object/run rows, blank equivalent forms, coverage and preserved-answer adjudication fields.')

if __name__ == '__main__':
    import sys
    verify(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
