"""Score the RQ4 planted-defect repair experiment. CPU only.

    PYTHONPATH=. python3 evaluation/m4_20261127/rq4/experiment/score.py \\
        --stage2-responses STAGE2_RESPONSES.jsonl --out-dir evaluation/m4_20261127/rq4

Primary measure: the blinded human review (rq4/REVIEW/REVIEW_FORM.csv, joined to methods through
experiment/sealed/REVIEW_KEY.json). The method comparison (RQ4_SUMMARY.csv, RQ4_TABLES.md) is written only
when every item has a complete, frozen judgment. With --pre-review, only RQ4_PER_OUTPUT.csv is written, with
the structural and second-Critic facts per output and no human judgments.

Definitions (also in RQ4_PROTOCOL.md):
- Output: one template revision per case, one Qwen revision per case and sample.
- Status: revised; abstained (the method declined); invalid (unparseable or malformed answer, an edit the
  host refused, a revision that failed a validator, or a server reply that did not finish normally);
  missing or no_reply. Only revised outputs are reviewed. The others count as not repaired.
- Correct repair (human): defect fixed "yes", revised claim supported "yes", new problem "no" and scope
  preserved "yes", all four.
- Second Critic (secondary, never decides correctness): the production Critic on the revised argument.
  Target still flagged: a finding on the planted-defect node with a category acceptable for the defect
  type. New objection: any other finding whose (object, node, category) appears in neither the stage 1
  report nor any second review of the original argument.
"""
from collections import defaultdict
from pathlib import Path
import argparse
import csv
import json
import statistics
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as CM  # noqa: E402
import build_review as BR  # noqa: E402

INVALID = ('invalid_unparseable', 'invalid_malformed', 'edit_refused', 'validation_failed', 'invalid_server_reply')
OUTPUT_COLUMNS = ('output_id', 'method', 'case_id', 'sample', 'status', 'stop_reason', 'new_statement',
                  'validators_failed', 'refused_edit_reasons', 'second_reviews', 'second_reviews_target_flagged',
                  'second_reviews_with_new_objection', 'new_objections', 'blind_item_id', 'defect_fixed',
                  'revised_claim_supported_by_evidence', 'new_problem_introduced', 'scope_preserved',
                  'correct_repair')
SUMMARY_COLUMNS = ('method', 'metric', 'numerator', 'denominator', 'rate', 'samples', 'mean_over_samples',
                   'sd_over_samples', 'n_cases', 'n_groups', 'note')


def load_outputs(base):
    out = []
    for state in CM.states():
        t = CM.load_json(base / 'results' / 'template' / f'{state.case_id}.revision_result.json')
        out.append({'output_id': f'{state.case_id}:template', 'method': 'template', 'case_id': state.case_id,
                    'sample': '', 'status': CM.classify_output(t['result']), 'result': t['result'], 'state': state})
    for path in sorted((base / 'results' / 'qwen').glob('*.revision_result.json')):
        q = CM.load_json(path)
        state = next(s for s in CM.states() if s.case_id == q['case_id'])
        out.append({'output_id': q['run_id'], 'method': 'qwen', 'case_id': q['case_id'], 'sample': q['repeat'],
                    'status': q['status'], 'result': q['result'], 'state': state})
    return out


def second_reviews(base, responses):
    """{target_id: [Critic report]} from the stage 2 responses, each rebuilt by critic.review."""
    _, _, requests = CM.RB.load_batch(base / 'batch_stage2')
    attempts = defaultdict(list)
    for line in responses:
        attempts[line['run_id']].append(line)
    reports = defaultdict(list)
    for request in requests:
        replies = [a for a in attempts.get(request['run_id'], []) if a['reply'] is not None]
        if not replies:
            reports[request['target_id']].append(None)
            continue
        critic_request = CM.load_json(base / 'stage2_requests' /
                                      f"{request['target_id'].replace(':', '_')}.critic_request.json")
        reports[request['target_id']].append(CM.replayed_report(critic_request, replies[0]))
    return reports


def keys(report):
    return {(c['object_id'], c['node_id'], c['category']) for c in report['criticisms']}


def read_review(path, key_path):
    """({output_id: judgment row}, complete?) from the review form and the sealed key."""
    if not Path(path).exists():
        return {}, False
    with open(path, encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    key = {k['blind_item_id']: k for k in CM.load_json(key_path)['items']}
    complete = bool(rows) and {r['blind_item_id'] for r in rows} == set(key) and all(
        r[c] in allowed for r in rows for c, allowed in BR.ANSWERS.items()) and all(
        r['reviewer_id'].strip() and r['review_frozen_timestamp'].strip() for r in rows)
    return {key[r['blind_item_id']]['output_id']: r for r in rows if r['blind_item_id'] in key}, complete


def per_output(base, stage2, review):
    rows = []
    for o in load_outputs(base):
        state, result = o['state'], o['result']
        label = state.label['expected_location']
        acceptable = set(state.label['acceptable_model_categories'])
        row = {c: '' for c in OUTPUT_COLUMNS}
        row.update(output_id=o['output_id'], method=o['method'], case_id=o['case_id'], sample=o['sample'],
                   status=o['status'])
        if result is not None:
            row['stop_reason'] = result['stop_reason'] or ''
            row['validators_failed'] = ';'.join(v['name'] for v in result['validators'] if v['issues'])
            row['refused_edit_reasons'] = ';'.join(r for x in result['rejected_edits'] for r in x['reasons'])
            if result['outcome'] == 'revised':
                row['new_statement'] = next(d['after']['statement'] for d in result['diff'])
        if stage2 is not None and o['status'] == 'revised':
            target = o['output_id'] if o['method'] == 'qwen' else f"{o['case_id']}:template"
            original = keys(state.report) | {k for r in stage2.get(f"{o['case_id']}:original", []) if r for k in keys(r)}
            reviews = [r for r in stage2.get(target, []) if r is not None]
            flagged = [any(c['object_id'] == label['object_id'] and c['node_id'] == label['node_id']
                           and c['category'] in acceptable for c in r['criticisms']) for r in reviews]
            reflag = {(label['object_id'], label['node_id'], c) for c in acceptable}
            new = [sorted(keys(r) - original - reflag) for r in reviews]
            row.update(second_reviews=len(reviews), second_reviews_target_flagged=sum(flagged),
                       second_reviews_with_new_objection=sum(bool(n) for n in new),
                       new_objections=';'.join(sorted({f'{a} {b} {c}' for n in new for a, b, c in n})))
        judgment = review.get(o['output_id'])
        if judgment is not None:
            row['blind_item_id'] = judgment['blind_item_id']
            for c in BR.ANSWERS:
                row[c] = judgment[c]
            row['correct_repair'] = int(judgment['defect_fixed'] == 'yes'
                                        and judgment['revised_claim_supported_by_evidence'] == 'yes'
                                        and judgment['new_problem_introduced'] == 'no'
                                        and judgment['scope_preserved'] == 'yes')
        elif o['status'] != 'revised':
            row['correct_repair'] = 0
        rows.append(row)
    return rows


def summary_row(method, metric, rows, value, weight=lambda r: 1, note=''):
    num, den = sum(value(r) for r in rows), sum(weight(r) for r in rows)
    by = defaultdict(lambda: [0, 0])
    for r in rows:
        if r['sample'] != '':
            by[r['sample']][0] += value(r)
            by[r['sample']][1] += weight(r)
    rates = [a / b for _, (a, b) in sorted(by.items()) if b]
    return {'method': method, 'metric': metric, 'numerator': num, 'denominator': den,
            'rate': round(num / den, 4) if den else '', 'samples': len(rates),
            'mean_over_samples': round(statistics.mean(rates), 4) if rates else '',
            'sd_over_samples': round(statistics.stdev(rates), 4) if len(rates) >= 2 else '',
            'n_cases': len({r['case_id'] for r in rows}),
            'n_groups': len({s.label['parent_group_id'] for s in CM.states() if s.case_id in {r['case_id'] for r in rows}}),
            'note': note or ('deterministic: one output per case' if method == 'template' else '')}


def summarize(rows):
    out = []
    for method in ('template', 'qwen'):
        m = [r for r in rows if r['method'] == method]
        revised = [r for r in m if r['status'] == 'revised']
        out += [summary_row(method, 'revised', m, lambda r: int(r['status'] == 'revised')),
                summary_row(method, 'abstained', m, lambda r: int(r['status'] == 'abstained')),
                summary_row(method, 'invalid', m, lambda r: int(r['status'] in INVALID)),
                summary_row(method, 'missing_or_no_reply', m, lambda r: int(r['status'] in ('missing', 'no_reply'))),
                summary_row(method, 'correct_repair', m, lambda r: int(r['correct_repair'] == 1),
                            note='all outputs; a non-revised output is not a repair'),
                summary_row(method, 'correct_repair_of_revised', revised, lambda r: int(r['correct_repair'] == 1))]
        for column, answer in (('defect_fixed', 'yes'), ('revised_claim_supported_by_evidence', 'yes'),
                               ('new_problem_introduced', 'yes'), ('scope_preserved', 'yes')):
            out.append(summary_row(method, f'{column}={answer}', revised, lambda r, c=column, a=answer: int(r[c] == a),
                                   note='revised outputs, human review'))
        reviewed = [r for r in revised if r['second_reviews'] != '']
        if reviewed:
            out.append(summary_row(method, 'second_critic_target_still_flagged', reviewed,
                                   lambda r: r['second_reviews_target_flagged'], weight=lambda r: r['second_reviews'],
                                   note='secondary; per second review'))
            out.append(summary_row(method, 'second_critic_new_objection', reviewed,
                                   lambda r: r['second_reviews_with_new_objection'], weight=lambda r: r['second_reviews'],
                                   note='secondary; per second review'))
    return out


def tables(rows, summary):
    index = {(r['method'], r['metric']): r for r in summary}

    def cell(method, metric):
        r = index.get((method, metric))
        if r is None or r['denominator'] == 0:
            return 'n/a'
        text = f"{r['numerator']}/{r['denominator']}"
        if r['mean_over_samples'] != '' and r['sd_over_samples'] != '':
            text += f" (mean {float(r['mean_over_samples']):.2f}, SD {float(r['sd_over_samples']):.2f})"
        return text
    metrics = ('revised', 'abstained', 'invalid', 'missing_or_no_reply', 'correct_repair', 'correct_repair_of_revised',
               'defect_fixed=yes', 'revised_claim_supported_by_evidence=yes', 'new_problem_introduced=yes',
               'scope_preserved=yes', 'second_critic_target_still_flagged', 'second_critic_new_objection')
    lines = ['# RQ4 tables', '', 'Generated by `experiment/score.py`. A controlled evaluation of planted-defect repair: '
             '3 planted unsupported-guarantee defects from 2 source executions (0 independent cases). Not a general '
             'measure of Revision Agent effectiveness.', '', '| Metric | Template | Qwen |', '|---|---|---|']
    lines += [f"| {m.replace('_', ' ')} | {cell('template', m)} | {cell('qwen', m)} |" for m in metrics]
    lines += ['', '## Per output', '', '| Output | Status | Fixed | Supported | New problem | Scope | Correct |',
              '|---|---|---|---|---|---|---|']
    lines += [f"| {r['output_id']} | {r['status']} | {r['defect_fixed']} | {r['revised_claim_supported_by_evidence']} | "
              f"{r['new_problem_introduced']} | {r['scope_preserved']} | {r['correct_repair']} |" for r in rows]
    return '\n'.join(lines) + '\n'


def write(path, columns, rows):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=columns, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def main(argv=None):
    p = argparse.ArgumentParser(prog='score.py')
    p.add_argument('--base', default=str(HERE), help='experiment folder holding results/ and the batches')
    p.add_argument('--stage2-responses', nargs='+', default=None)
    p.add_argument('--review-form', default=str(BR.REVIEW / 'REVIEW_FORM.csv'))
    p.add_argument('--key', default=str(HERE / 'sealed' / 'REVIEW_KEY.json'))
    p.add_argument('--out-dir', required=True)
    p.add_argument('--pre-review', action='store_true', help='write only per-output facts, no human judgments')
    args = p.parse_args(argv)
    base, out = Path(args.base), Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stage2 = None
    if args.stage2_responses:
        stage2 = second_reviews(base, [l for path in args.stage2_responses for l in CM.RB.read_jsonl(path)])
    if args.pre_review:
        write(out / 'RQ4_PER_OUTPUT.csv', OUTPUT_COLUMNS, per_output(base, stage2, {}))
        print('pre-review: per-output facts only; no human judgments and no method comparison', file=sys.stderr)
        return 0
    review, complete = read_review(args.review_form, args.key)
    if not complete:
        print('the blinded review is not complete and frozen; the method comparison is not written '
              '(use --pre-review for per-output facts)', file=sys.stderr)
        return 1
    rows = per_output(base, stage2, review)
    summary = summarize(rows)
    write(out / 'RQ4_PER_OUTPUT.csv', OUTPUT_COLUMNS, rows)
    write(out / 'RQ4_SUMMARY.csv', SUMMARY_COLUMNS, summary)
    (out / 'RQ4_TABLES.md').write_text(tables(rows, summary), encoding='utf-8')
    print(f'{len(rows)} outputs scored', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
