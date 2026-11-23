"""Build the blinded review packet for the revised arguments (RQ4). CPU only.

    PYTHONPATH=. python3 evaluation/m4_20261127/rq4/experiment/build_review.py [--check]

Run after build_stage2.py has written results/qwen/. Writes rq4/REVIEW/ (one item per revised argument,
REVIEW_FORM.csv, REVIEW_INSTRUCTIONS.md, REVIEW_MANIFEST.csv) and the key that maps items to methods in
rq4/experiment/sealed/REVIEW_KEY.json. An item shows the original argument for the object, the approved
finding, any other Critic finding (left unchanged), the revised node, and the evidence both methods were
given. It never shows which method wrote the revision, its justification, or a run ID.
"""
from pathlib import Path
import csv
import hashlib
import io
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as CM  # noqa: E402

REVIEW = CM.RQ4 / 'REVIEW'
FORM_COLUMNS = ('blind_item_id', 'reviewer_id', 'review_date', 'prior_exposure_declaration',
                'defect_fixed', 'revised_claim_supported_by_evidence', 'new_problem_introduced',
                'new_problem_description', 'scope_preserved', 'notes', 'review_frozen_timestamp')
ANSWERS = {
    'defect_fixed': ('yes', 'partly', 'no', 'indeterminate'),
    'revised_claim_supported_by_evidence': ('yes', 'no', 'indeterminate'),
    'new_problem_introduced': ('yes', 'no', 'indeterminate'),
    'scope_preserved': ('yes', 'no', 'indeterminate'),
}

INSTRUCTIONS = """# RQ4 blinded review instructions

This is a controlled evaluation of planted-defect repair, not a general measure of Revision Agent effectiveness.

Each item in `items/` shows one revised argument. A defect was planted on purpose in the original argument, a Critic finding about it was approved, and a revision method rewrote the statement the finding is about. Several items can come from the same original argument. Items are in an arbitrary order, and nothing in an item says which method wrote it. Please do not try to find out (for example from `experiment/sealed/` or `experiment/results/`) until your form is complete and frozen.

For every item, fill one row of `REVIEW_FORM.csv`:

- **defect_fixed**: does the revised statement remove the problem the approved finding describes? `yes`, `partly`, `no` or `indeterminate`.
- **revised_claim_supported_by_evidence**: is everything the revised statement asserts supported by the evidence shown in the item (records, retrieval context) or by the argument's own fixed context? A statement that only says something is unresolved or not established counts as supported when that is true of the evidence. `yes`, `no` or `indeterminate`.
- **new_problem_introduced**: does the revision add a new problem: a new unsupported claim, a wrong or invented evidence reference, a contradiction with another node, or a statement that no longer works in the argument? `yes`, `no` or `indeterminate`. If `yes`, describe it in `new_problem_description`.
- **scope_preserved**: does the revised statement keep the original object, node role, requirement and frame interval, without widening or narrowing them? `yes`, `no` or `indeterminate`.
- **notes**: anything that affected your judgment, including uncertainty.

Fill `reviewer_id`, `review_date` and `prior_exposure_declaration` on every row. Say whether you have seen the planted-defect labels, the revision results or the key before reviewing. When the form is complete, put the same `review_frozen_timestamp` on every row and do not change a judgment afterwards.

Your judgments are the primary measure. The second Critic review is reported separately and does not decide whether a repair is correct.

Known limitation: the template method writes fixed wording, so a reader may recognise it across items. Judge each item on its content regardless.
"""


def node_line(node):
    interval = node.get('scope', {}).get('interval') if isinstance(node.get('scope'), dict) else None
    span = f" (frames {interval[0]}-{interval[1]})" if isinstance(interval, list) and len(interval) == 2 else ''
    return f"- **{node['id']}** [{node['type']}]{span}: {node['statement']}"


def graph_of(bundle, object_id):
    return next(g['graph'] for g in bundle['graphs'] if g['object_id'] == object_id)


def item_text(state, result):
    request = state.critic_request
    context = request['evaluation_context']
    approved = {d['criticism_id'] for d in state.decisions}
    finding = next(c for c in state.report['criticisms'] if c['criticism_id'] in approved)
    obj = finding['object_id']
    original, revised = graph_of(request['argument_bundle'], obj), graph_of(result['revised_argument_bundle'], obj)
    monitored = context['monitored_interval']
    lines = ['## Context', '',
             f"- Requirement: {context['requirement_id']} {context['requirement_version']}",
             f"- Execution: {context['execution_id']}",
             f"- Object under review: {obj}",
             f"- Monitored interval: {monitored.get('interval')} ({monitored.get('domain')}, {monitored.get('clock')})",
             '', f'## Original argument for {obj}', '']
    lines += [node_line(n) for n in original['nodes']]
    lines += ['', 'Edges: ' + '; '.join(f"{e['source']} {e['type']} {e['target']}" for e in original['edges']), '',
              '## Approved Critic finding', '',
              f"- Node: {finding['node_id']}",
              f"- Category: {finding['category']} {finding['category_name']}",
              f"- Explanation: {finding['explanation']}",
              f"- Suggested action: {finding['suggested_action']}", '',
              '## Other Critic findings on this argument (not approved, left unchanged)', '']
    others = [c for c in state.report['criticisms'] if c['criticism_id'] not in approved]
    lines += ([f"- {c['object_id']} {c['node_id']}: {c['category']} {c['category_name']}. {c['explanation']}"
               for c in others] or ['- None.'])
    changed = [d for d in result['diff']]
    if len(changed) != 1 or (changed[0]['object_id'], changed[0]['node_id']) != (obj, finding['node_id']):
        raise ValueError('a planted-defect revision must change exactly the target node')
    lines += ['', '## Revision', '']
    for d in changed:
        before, after = d.get('before'), d.get('after')
        if isinstance(before, dict) and isinstance(after, dict):
            lines += [f"Node **{d['node_id']}** of {d['object_id']} ({after.get('type')}):", '',
                      f"- Before: {before.get('statement')}", f"- After: {after.get('statement')}", '']
        else:
            raise ValueError(f"unexpected change {d.get('change')!r} in a planted-defect revision")
    lines += ['Every other node and edge of every graph is unchanged.', '',
              '## Revised argument for ' + obj, '']
    lines += [node_line(n) for n in revised['nodes']]
    evidence = state.evidence
    records = [r for r in evidence['evidence'] if r.get('object_id') in (obj, None)]
    lines += ['', '## Evidence given to the revision', '']
    if records:
        for r in records:
            lines.append(f"- **{r['id']}**: {r.get('kind')}, {r.get('measurement_type')}, interval {r.get('interval')}, "
                         f"status {r.get('validation_status')}, capability {r.get('capability')}; "
                         f"limitations: {r.get('limitations')}")
    else:
        lines.append('- No evidence records for this object in the package.')
    rc = evidence['retrieval_context'] or {}
    lines += ['', 'Retrieval context:', '',
              f"- Complete within requested scope: {rc.get('complete_within_requested_scope')}",
              f"- Gaps: {rc.get('gaps')}", '- Limitations:']
    lines += [f'  - {x}' for x in dict.fromkeys(rc.get('limitations') or [])]
    lines.append(f"- Checker assessments admitted: {len([a for a in evidence['checker_assessments'] if a.get('admitted')])}")
    return '\n'.join(lines) + '\n'


def outputs(base=HERE):
    """[(method, output_id, case_id, result)] for every revised argument under base/results."""
    found = []
    for state in CM.states():
        t = CM.load_json(base / 'results' / 'template' / f'{state.case_id}.revision_result.json')
        if t['result']['outcome'] == 'revised':
            found.append(('template', f'{state.case_id}:template', state, t['result']))
    for path in sorted((base / 'results' / 'qwen').glob('*.revision_result.json')):
        q = CM.load_json(path)
        if q['status'] == 'revised':
            state = next(s for s in CM.states() if s.case_id == q['case_id'])
            found.append(('qwen', q['run_id'], state, q['result']))
    return found


def build(base=HERE):
    entries = []
    for method, output_id, state, result in outputs(base):
        body = item_text(state, result)
        entries.append((hashlib.sha256(body.encode('utf-8') + output_id.encode('utf-8')).hexdigest(),
                        method, output_id, state.case_id, body))
    entries.sort()
    files, key, manifest = {}, [], io.StringIO()
    mw = csv.writer(manifest, lineterminator='\n')
    mw.writerow(['blind_item_id', 'item_path', 'sha256'])
    form = io.StringIO()
    fw = csv.DictWriter(form, fieldnames=FORM_COLUMNS, lineterminator='\n')
    fw.writeheader()
    for index, (_, method, output_id, case_id, body) in enumerate(entries, 1):
        bid = f'B{index:02d}'
        text = f'# Review item {bid}\n\n' + body
        files[f'items/{bid}.md'] = text
        mw.writerow([bid, f'items/{bid}.md', CM.sha256_text(text)])
        fw.writerow({c: (bid if c == 'blind_item_id' else '') for c in FORM_COLUMNS})
        key.append({'blind_item_id': bid, 'method': method, 'output_id': output_id, 'case_id': case_id})
    files['REVIEW_FORM.csv'] = form.getvalue()
    files['REVIEW_MANIFEST.csv'] = manifest.getvalue()
    files['REVIEW_INSTRUCTIONS.md'] = INSTRUCTIONS
    return files, {'experiment': CM.EXPERIMENT_VERSION, 'items': key}


def main(argv):
    files, key = build()
    targets = {REVIEW / n: t for n, t in files.items()}
    targets[HERE / 'sealed' / 'REVIEW_KEY.json'] = json.dumps(key, indent=1) + '\n'
    if argv == ['--check']:
        stale = [str(p) for p, t in targets.items()
                 if p.name != 'REVIEW_FORM.csv' and (not p.exists() or p.read_text(encoding='utf-8') != t)]
        print('differs from a fresh build: ' + ', '.join(stale) if stale else
              f"review packet matches a fresh build ({len(key['items'])} items)")
        return 1 if stale else 0
    def answered(path):
        with open(path, encoding='utf-8') as fh:
            return any(any(v for k, v in row.items() if k != 'blind_item_id') for row in csv.DictReader(fh))
    if (REVIEW / 'REVIEW_FORM.csv').exists() and answered(REVIEW / 'REVIEW_FORM.csv'):
        print('REVIEW_FORM.csv already has answers; refusing to overwrite it', file=sys.stderr)
        return 1
    for path, text in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    print(f"wrote {len(key['items'])} review items to {REVIEW.relative_to(CM.ROOT)}", file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
